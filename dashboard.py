"""Local dashboard for your own Claude Code environmental cost.

    python3 dashboard.py            # serves http://localhost:8765 and opens a browser
    make dashboard                  # same
    ./Dashboard.command             # double-click on macOS

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
    Globs, not exact strings: a cluster's login node changes between sessions (tri-login01,
    tri-login04, ...) and laptop hostnames follow whatever network they are on, so exact
    matching would fragment one machine into several rows. Longest pattern wins, so a specific
    rule beats a general one."""
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
    cfg = load_config()
    raws, errors = collect()
    data = build(raws, errors, cfg.get("labels"))
    os.makedirs("data", exist_ok=True)
    json.dump(data, open(CACHE, "w"), indent=1)
    return data


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            self.path = "/dashboard.html"
            return super().do_GET()
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
            return self._send(load_config())
        return super().do_GET()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        cfg = load_config().get("remote", [])
        print(f"Environment Cost of Claude — dashboard on {url}")
        print(f"  sources: local" + (f" + {', '.join(map(str, cfg))}" if cfg else
                                     "  (add remote hosts in sources.json)"))
        if not os.path.exists(CACHE):
            print("  no cached data yet — press Refresh in the browser, or wait for first load")
        print("  Ctrl-C to stop")
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
