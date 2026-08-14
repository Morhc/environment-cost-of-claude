"""Local dashboard for your own Claude Code environmental cost.

    python3 dashboard.py            # serves http://localhost:8765 and opens a browser
    make dashboard                  # same
    make app                        # build a double-clickable macOS app (see make_app.py)
    ./Dashboard.command             # double-click, but leaves a Terminal window behind

With DASHBOARD_AUTOQUIT=1 (which the macOS app sets) the server shuts itself down once no browser
tab is watching it, so double-clicking the app and closing the tab leaves nothing running.

Stdlib only. Reads token counters from Claude Code transcripts (never message content), costs
them with the published rates in data/sourced_data.json, and serves three views: the totals, the
split across the machines you work on, and the projects that dominate.

Which machines to collect from lives in sources.json (see sources.example.json). Local is always
included. Refresh re-runs the collection, including over SSH for remote hosts.

Every number below the token counts is DERIVED and carries the uncertainty documented in the
report: 2-4x on the per-token rates, and a factor of ~7 across grid accounting conventions.
"""
import http.server
import json
import os
import fnmatch
import select
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
PORT = int(os.environ.get("DASHBOARD_PORT", "8765"))
CACHE = "data/usage_cache.json"
CONFIG = "sources.json"

# --- Auto-quit, for the double-clickable app --------------------------------------------------
# The page holds one open connection (/api/live) for as long as it is on screen, and this server
# exits once no connection remains. The tab does not have to report anything: closing it tears the
# socket down, and an open socket is self-evident in a way a message is not.
#
# The first version did ask the tab to report -- a heartbeat while open, a sendBeacon on pagehide.
# Both are best-effort. sendBeacon is not guaranteed to be delivered, and timers in background tabs
# are throttled to about one per minute, which forces the idle timeout up to a couple of minutes.
# When the beacon went missing the server sat there for the whole timeout, which reads as broken.
#
# GRACE covers reload and ordinary navigation, where the connection drops and comes back. It has to
# clear the client's reconnect delay, which the stream sets to 1 s (`retry:`), so 5 leaves room for
# a slow reload without making a real close feel sluggish.
#
# NEVER_CONNECTED is the separate case where no browser ever arrived -- no default browser, or the
# page failed to load. Nothing will ever close a connection that was never opened, so that needs
# its own timeout or the app would linger invisibly forever.
AUTOQUIT = os.environ.get("DASHBOARD_AUTOQUIT") == "1"
GRACE, NEVER_CONNECTED = 5.0, 90.0
LIVE = {"n": 0, "empty_since": None, "ever": False}
LIVE_LOCK = threading.Lock()
REFRESH_LOCK = threading.Lock()


def load_config():
    if os.path.exists(CONFIG):
        return json.load(open(CONFIG))
    return {"remote": []}


def collect():
    """Run measure_usage.py --raw locally and over SSH for each configured host."""
    out, errors = [], []
    try:
        r = subprocess.run([sys.executable, "measure_usage.py", "--raw"],
                           capture_output=True, text=True, timeout=900)
        if r.returncode == 0 and r.stdout.strip():
            out.append(json.loads(r.stdout))
        else:
            errors.append(f"local: {(r.stderr or 'no output').strip().splitlines()[-1][:200]}")
    except Exception as e:
        errors.append(f"local: {e}")

    for host in load_config().get("remote", []):
        name = host if isinstance(host, str) else host.get("host")
        roots = [] if isinstance(host, str) else host.get("roots", [])
        try:
            # Discover roots on the remote if none were configured. Scoped to $USER: a wildcard
            # over /scratch/* matches other people's directories on a shared cluster.
            if not roots:
                d = subprocess.run(
                    ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", name,
                     'for d in "$HOME"/.claude/projects /scratch/"$USER"/.claude/projects '
                     '/project/*/"$USER"/.claude/projects; do [ -d "$d" ] && echo "$d"; done'],
                    capture_output=True, text=True, timeout=120)
                roots = [x for x in d.stdout.split() if x]
            if not roots:
                errors.append(f"{name}: no transcript roots found")
                continue
            args = []
            for x in roots:
                args += ["--root", x]
            r = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", name,
                 "python3 - --raw " + " ".join(f"--root {x}" for x in roots)],
                stdin=open("measure_usage.py"), capture_output=True, text=True, timeout=1800)
            if r.returncode == 0 and r.stdout.strip():
                out.append(json.loads(r.stdout))
            else:
                tail = (r.stderr or "no output").strip().splitlines()
                errors.append(f"{name}: {tail[-1][:200] if tail else 'failed'}")
        except Exception as e:
            errors.append(f"{name}: {e}")
    return out, errors


def label_for(value, labels, fallback=None):
    """Map a hostname or path onto a human name using glob patterns from sources.json.
    Globs, not exact strings: a cluster's login node changes between sessions (the login node
    rotates) and laptop hostnames follow whatever network they are on, so exact
    matching would fragment one machine into several rows (login01, login04, login06 have all
    appeared for one cluster in a week). Longest pattern wins, so a specific rule beats a
    general one."""
    best = None
    for pat, name in (labels or {}).items():
        if fnmatch.fnmatch(value, pat) and (best is None or len(pat) > len(best[0])):
            best = (pat, name)
    return best[1] if best else (fallback if fallback is not None else value)


def pretty_project(name, cwd):
    """Prefer the real working directory recorded in the transcript. The project DIRECTORY name
    is a lossy encoding -- Claude Code maps "/", "." and "_" all onto "-", so decoding it turns
    'nucrate_viewer' into 'nucrate/viewer' and '25.12.1' into '25/12/1'. Only fall back to that
    when a transcript carried no cwd at all."""
    if cwd:
        return cwd
    if name == "(flat)":
        return "(no project directory)"
    return name


def build(raws, errors, labels=None):
    """Turn raw per-host token counts into everything the three tabs need."""
    D = json.load(open("data/sourced_data.json"))
    c = D["couch_2026"]
    R_IN = c["wh_per_million_input_tokens"] / 1e6
    R_CACHE = c["wh_per_million_cached_read_tokens"] / 1e6
    R_OUT = c["wh_per_million_output_tokens"] / 1e6
    grids = {f"eGRID_{k}": v for k, v in D["egrid_2023"]["gco2_per_kwh"].items()}
    grids |= {f"AVERT_{k.replace(' ', '_')}": v for k, v in D["avert_2023"]["gco2_per_kwh"].items()}
    grids |= {f"Cambium_{k}": v for k, v in D["cambium_2023_lrmer"]["gco2_per_kwh"].items()}
    grids["PJM_2022_shortrun"] = D["pjm_emissions_2022"]["flat_load_marginal_gco2_per_kwh_derived"]
    WUE_ON, WUE_OFF = 0.18, 3.142

    wh = lambda s: s["fresh"] * R_IN + s["cached"] * R_CACHE + s["out"] * R_OUT
    sessions, per_source, stamps = [], {}, []
    hourly = {}
    for d in raws:
        for k, v in (d.get("hourly") or {}).items():
            h = hourly.setdefault(k, [0, 0, 0])
            for i in range(3):
                h[i] += v[i]
        src = d.get("source") or "unknown"
        b = per_source.setdefault(src, dict(source=label_for(src, labels), host=src,
                                            roots=d.get("roots", []), wh=0.0,
                                            sessions=0, messages=0, fresh=0, cached=0, out=0))
        for s in d.get("sessions_detail", []):
            s = dict(s)
            s["source"] = s.get("source") or src
            s["wh"] = wh(s)
            sessions.append(s)
            b["wh"] += s["wh"]; b["sessions"] += 1; b["messages"] += s["msgs"]
            for k in ("fresh", "cached", "out"):
                b[k] += s[k]
            for t in (s.get("first"), s.get("last")):
                if t:
                    stamps.append(t)

    total_wh = sum(s["wh"] for s in sessions) or 1e-9

    # Projects are keyed on the working directory in effect at each message, not on the session's
    # first cwd: 14 of 37 home-directory sessions here changed directory partway through, which
    # made "/Users/<me>" look like one huge project when it was really a launch point for many.
    per_project, compactions = {}, []
    for s in sessions:
        for c in (s.get("compactions") or []):
            compactions.append(dict(c, source=s["source"]))
        buckets = s.get("by_cwd") or {(s.get("cwd") or s["project"]): [s["fresh"], s["cached"],
                                                                      s["out"], s["msgs"]]}
        for path, v in buckets.items():
            name = label_for(path, labels, path)
            p = per_project.setdefault(name, dict(project=name, path=path, source=s["source"],
                                                  wh=0.0, sessions=0, messages=0, paths=set()))
            p["wh"] += v[0] * R_IN + v[1] * R_CACHE + v[2] * R_OUT
            p["messages"] += v[3]
            p["sessions"] += 1
            p["paths"].add(path)
    for p in per_project.values():
        paths = sorted(p.pop("paths"))
        p["path"] = paths[0] if len(paths) == 1 else f"{paths[0]}  (+{len(paths) - 1} more)"

    projects = sorted(per_project.values(), key=lambda p: -p["wh"])
    for p in projects:
        p["share"] = p["wh"] / total_wh
    sources = sorted(per_source.values(), key=lambda b: -b["wh"])
    for b in sources:
        b["share"] = b["wh"] / total_wh

    return {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "errors": errors,
        "totals": {
            "kwh": total_wh / 1000,
            "sessions": len(sessions),
            "messages": sum(s["msgs"] for s in sessions),
            "first": min(stamps) if stamps else None,
            "last": max(stamps) if stamps else None,
            "tokens": {k: sum(s[k] for s in sessions) for k in ("fresh", "cached", "out")},
        },
        "hourly": hourly,
        "rates_wh_per_token": {"fresh": R_IN, "cached": R_CACHE, "out": R_OUT},
        "grids": grids,
        "water": {"on_site_l_per_kwh": WUE_ON, "total_l_per_kwh": WUE_ON + WUE_OFF},
        "equivalences": D["equivalences"],
        "sources": sources,
        "projects": projects,
        "compactions": sorted(compactions, key=lambda c: c.get("at") or ""),
        "session_list": [{"wh": s["wh"], "msgs": s["msgs"], "first": s.get("first"),
                          "last": s.get("last"), "source": s["source"],
                          "project": label_for(s.get("cwd") or s["project"], labels,
                                               s.get("cwd") or s["project"])}
                         for s in sessions],
        "threshold": 0.05,
    }


def refresh():
    # Serialised: the server is threaded so heartbeats keep arriving during a long SSH collection,
    # which also means two Refresh clicks could otherwise write the cache file at once.
    with REFRESH_LOCK:
        cfg = load_config()
        raws, errors = collect()
        data = build(raws, errors, cfg.get("labels"))
        os.makedirs("data", exist_ok=True)
        json.dump(data, open(CACHE, "w"), indent=1)
        return data


class Handler(http.server.BaseHTTPRequestHandler):
    """Serves exactly three things and nothing else.

    An earlier version subclassed SimpleHTTPRequestHandler after chdir'ing into the repo, which
    quietly published every file in it -- sources.json (machine names, colleagues' paths) and
    data/usage_cache.json (every directory you have worked in) included. Loopback-only, but there
    is no reason for those to be reachable over HTTP at all, so this whitelists instead.
    """

    ALLOWED = {"/", "/index.html", "/api/data", "/api/refresh", "/api/config", "/api/live"}

    def log_message(self, *args):
        pass

    def _local_only(self):
        """Reject anything not addressed to loopback. The socket is already bound to 127.0.0.1;
        this additionally blocks DNS-rebinding, where a hostile page resolves its own domain to
        127.0.0.1 and talks to this server from inside your browser."""
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        return host in ("localhost", "127.0.0.1", "::1", "")

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self):
        body = open("dashboard.html", "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _stream(self):
        """Hold an event-stream open for as long as the tab is. Presence is the whole payload.

        Closure is detected by watching the socket for readability rather than by writing to it:
        the first write to a closed peer usually succeeds into the send buffer and only the second
        one raises, so a write-based check would not notice until the next keepalive. select() sees
        the peer's FIN as a readable socket with nothing on it, which is immediate."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with LIVE_LOCK:
            LIVE["n"] += 1
            LIVE["ever"] = True
            LIVE["empty_since"] = None
        try:
            self.wfile.write(b"retry: 1000\n\ndata: open\n\n")
            self.wfile.flush()
            last = time.time()
            while True:
                r, _, _ = select.select([self.connection], [], [], 1.0)
                if r and not self.connection.recv(1, socket.MSG_PEEK):
                    break                                    # peer closed: the tab is gone
                if time.time() - last > 20:
                    self.wfile.write(b": keepalive\n\n")      # also catches a peer that vanished
                    self.wfile.flush()                       # without sending a FIN
                    last = time.time()
        except (OSError, ValueError):
            pass
        finally:
            with LIVE_LOCK:
                LIVE["n"] = max(0, LIVE["n"] - 1)
                if LIVE["n"] == 0:
                    LIVE["empty_since"] = time.time()

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if not self._local_only():
            self.send_error(403, "local requests only")
            return
        if path not in self.ALLOWED:
            self.send_error(404, "not found")
            return
        if path == "/api/live":
            return self._stream()
        if path in ("/", "/index.html"):
            return self._send_html()
        if path == "/api/data":
            if os.path.exists(CACHE):
                return self._send(json.load(open(CACHE)))
            return self._send(refresh())
        if path == "/api/refresh":
            try:
                return self._send(refresh())
            except Exception as e:
                return self._send({"error": str(e)}, 500)
        if path == "/api/config":
            # config without the machine list: the browser only needs the labels
            return self._send({"labels": load_config().get("labels", {})})


class Server(socketserver.ThreadingTCPServer):
    """Threaded so that a refresh -- which can take minutes when it collects over SSH -- does not
    block the heartbeat. On the single-threaded server the watchdog below would see a stale
    heartbeat during a long refresh and shut down mid-collection."""
    allow_reuse_address = True
    daemon_threads = True


def watchdog(httpd, started):
    """Exit once no tab is watching. Runs only under DASHBOARD_AUTOQUIT=1."""
    while True:
        time.sleep(0.5)
        now = time.time()
        with LIVE_LOCK:
            n, empty_since, ever = LIVE["n"], LIVE["empty_since"], LIVE["ever"]
        if n > 0:
            continue
        if ever and empty_since and now - empty_since > GRACE:
            why = "browser tab closed"
        elif not ever and now - started > NEVER_CONNECTED:
            why = f"no browser connected within {NEVER_CONNECTED:.0f}s"
        else:
            continue
        print(f"  quitting: {why}")
        threading.Thread(target=httpd.shutdown, daemon=True).start()
        return


if __name__ == "__main__":
    url = f"http://localhost:{PORT}"
    try:
        httpd = Server(("127.0.0.1", PORT), Handler)
    except OSError:
        # Already running -- most likely the app was double-clicked twice. Surfacing the open
        # dashboard is what was wanted either way; starting a second copy is not.
        print(f"already serving on {url} — opening it")
        webbrowser.open(url)
        raise SystemExit(0)

    with httpd:
        cfg = load_config().get("remote", [])
        print(f"Environment Cost of Claude — dashboard on {url}")
        print(f"  sources: local" + (f" + {', '.join(map(str, cfg))}" if cfg else
                                     "  (add remote hosts in sources.json)"))
        if not os.path.exists(CACHE):
            print("  no cached data yet — press Refresh in the browser, or wait for first load")
        print("  quits when you close the tab" if AUTOQUIT else "  Ctrl-C to stop")
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        if AUTOQUIT:
            threading.Thread(target=watchdog, args=(httpd, time.time()), daemon=True).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
