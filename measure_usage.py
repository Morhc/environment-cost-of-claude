"""Claude Code transcripts -> tokens -> energy -> CO2 and water.

Reads ONLY the usage counters on assistant messages. No message content is opened.

    python3 measure_usage.py                      # this machine, US-average grid
    python3 measure_usage.py --days 30            # last 30 days
    python3 measure_usage.py --grid Cambium_PJM_West
    python3 measure_usage.py --list-grids

Claude Code stores transcripts per-machine with no central ledger, so one run is a LOWER BOUND.
For a real personal total, collect from every machine and merge:

    ./collect_usage.sh trillium                   # does all of the below for you

    # or by hand:
    python3 measure_usage.py --raw > local.json
    ssh HOST 'python3 - --raw --root /home/USER/.claude/projects' < measure_usage.py > host.json
    python3 measure_usage.py --merge local.json host.json

`--raw` emits token counts with no rates applied and reads no data files, so it is safe to pipe to
any host with a python3 and nothing else installed.

Energy, CO2 and water are DERIVED: measured token counts times Couch's (Jan 2026) per-token
estimates for Opus 4.5 / Sonnet 4.5, which carry 2-4x method uncertainty. The token counts are
measured; nothing downstream of them is. Rates and grid factors come from data/sourced_data.json,
so any mode except --raw must run from the project root.
"""
import argparse
import datetime
import glob
import json
import os
import statistics as st
import time

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--root", action="append", help="transcript root (repeatable); "
                "default ~/.claude/projects")
ap.add_argument("--days", type=float, help="only sessions active in the last N days")
ap.add_argument("--grid", default="eGRID_US_avg", help="convention for the headline")
ap.add_argument("--project", help="substring filter on the project directory name")
ap.add_argument("--raw", action="store_true", help="emit token counts as JSON; applies no rates "
                "and reads no data files, so it can be piped to a remote host")
ap.add_argument("--merge", nargs="+", metavar="FILE", help="combine --raw JSON files and report")
ap.add_argument("--list-grids", action="store_true", help="print all conventions and exit")
ap.add_argument("--by", choices=["day", "week", "month", "hour", "dow"],
                help="also print a time series: calendar bins, or hour-of-day / day-of-week "
                     "profiles")
ap.add_argument("--tz", help="timezone for --by, e.g. America/Vancouver or America/Toronto. "
                "Transcripts are stored in UTC, so this only changes how bins are drawn. "
                "Default: this machine's local zone.")
a = ap.parse_args()


def scan(roots, project_filter=None):
    """Walk transcript roots and aggregate token counters per session.

    Two path layouts exist and both must be handled -- missing either silently undercounts:
      <project>/<session>.jsonl                      current layout
      <session>.jsonl                                older flat layout (seen on Trillium scratch)
    and subagent/workflow transcripts nest one or more levels deeper under
      <project>/<session>/subagents/[workflows/<wf>/]agent-*.jsonl
    Those carry real token spend and roll into their parent session.
    """
    agg = {}
    # Token counts bucketed by UTC hour. Transcripts timestamp every record in UTC ("...Z")
    # regardless of the host's own timezone, so a laptop on PST and a cluster on EST are already
    # on one clock -- the timezone is only ever a display choice, applied at report time.
    hourly = {}
    for root in roots:
        root = os.path.expanduser(root)
        if not os.path.isdir(root):
            continue
        for path in glob.glob(f"{root}/**/*.jsonl", recursive=True):
            parts = os.path.relpath(path, root).split(os.sep)
            if len(parts) == 1:
                project, session = "(flat)", parts[0].removesuffix(".jsonl")
            else:
                project, session = parts[0], parts[1].removesuffix(".jsonl")
            if project_filter and project_filter not in project:
                continue
            f = c = o = m = 0
            first = last = None
            for line in open(path, errors="replace"):
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if ts := d.get("timestamp"):
                    first = min(first or ts, ts)
                    last = max(last or ts, ts)
                if d.get("type") != "assistant":
                    continue
                u = (d.get("message") or {}).get("usage")
                if not isinstance(u, dict):
                    continue
                # top-level counters only; the `iterations` array restates the same numbers
                mf = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
                mc = u.get("cache_read_input_tokens") or 0
                mo = u.get("output_tokens") or 0
                f += mf; c += mc; o += mo; m += 1
                if ts:
                    h = hourly.setdefault(ts[:13], [0, 0, 0])   # "YYYY-MM-DDTHH" in UTC
                    h[0] += mf; h[1] += mc; h[2] += mo
            if not m:
                continue
            s = agg.setdefault((root, project, session),
                               dict(project=project, fresh=0, cached=0, out=0, msgs=0,
                                    subagents=0, first=first, last=last))
            s["fresh"] += f; s["cached"] += c; s["out"] += o; s["msgs"] += m
            s["subagents"] += len(parts) > 2
            if first: s["first"] = min(s["first"] or first, first)
            if last: s["last"] = max(s["last"] or last, last)
    return list(agg.values()), hourly


def rates_and_grids():
    """Loaded lazily so --raw needs no data files and can run on a bare remote host."""
    D = json.load(open("data/sourced_data.json"))
    c = D["couch_2026"]
    R = (c["wh_per_million_input_tokens"] / 1e6, c["wh_per_million_cached_read_tokens"] / 1e6,
         c["wh_per_million_output_tokens"] / 1e6)
    G = {f"eGRID_{k}": v for k, v in D["egrid_2023"]["gco2_per_kwh"].items()}
    G |= {f"AVERT_{k.replace(' ', '_')}": v for k, v in D["avert_2023"]["gco2_per_kwh"].items()}
    G |= {f"Cambium_{k}": v for k, v in D["cambium_2023_lrmer"]["gco2_per_kwh"].items()}
    G["PJM_2022_shortrun"] = D["pjm_emissions_2022"]["flat_load_marginal_gco2_per_kwh_derived"]
    return R, G


WUE_ON, WUE_OFF = 0.18, 3.142      # L/kWh, AWS multipliers used by Jegham et al. v6
MILE_G = 400                       # EPA average passenger vehicle, gCO2/mile

if a.list_grids:
    _, G = rates_and_grids()
    for k, v in sorted(G.items(), key=lambda kv: kv[1]):
        print(f"  {k:<34} {v:6.1f} gCO2/kWh")
    raise SystemExit

# ---- gather -------------------------------------------------------------------------------
if a.merge:
    sources, sessions, hourly = [], [], {}
    for fn in a.merge:
        d = json.load(open(fn))
        sources.append(d)
        sessions += d["sessions_detail"]
        for k, v in (d.get("hourly") or {}).items():
            h = hourly.setdefault(k, [0, 0, 0])
            for i in range(3): h[i] += v[i]
else:
    sessions, hourly = scan(a.root or ["~/.claude/projects"], a.project)
    if a.days:
        cut = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - a.days * 86400))
        sessions = [s for s in sessions if (s["last"] or "") >= cut]
    sources = None

if not sessions:
    raise SystemExit("no sessions matched")

tot = lambda k: sum(s[k] for s in sessions)
F, C, O = tot("fresh"), tot("cached"), tot("out")
stamps = [t for s in sessions for t in (s["first"], s["last"]) if t]

if a.raw:
    import platform
    print(json.dumps({
        "source": platform.node(), "roots": [os.path.expanduser(r) for r in
                                             (a.root or ["~/.claude/projects"])],
        "sessions": len(sessions), "messages": tot("msgs"),
        "first": min(stamps) if stamps else None, "last": max(stamps) if stamps else None,
        "tokens": {"fresh": F, "cached": C, "output": O},
        "hourly": hourly,
        "sessions_detail": sessions,
    }, indent=1))
    raise SystemExit

# ---- report -------------------------------------------------------------------------------
(R_IN, R_CACHE, R_OUT), GRIDS = rates_and_grids()
if a.grid not in GRIDS:
    raise SystemExit(f"unknown grid {a.grid!r}; try --list-grids")
for s in sessions:
    s["wh"] = s["fresh"] * R_IN + s["cached"] * R_CACHE + s["out"] * R_OUT
sessions.sort(key=lambda s: -s["wh"])
WH = sum(s["wh"] for s in sessions)
kwh = WH / 1000

span = ""
if stamps:
    d0, d1 = min(stamps)[:10], max(stamps)[:10]
    span = (f" | {d0} .. {d1} "
            f"({(datetime.date.fromisoformat(d1) - datetime.date.fromisoformat(d0)).days} days)")
print(f"{len(sessions)} sessions | {tot('msgs'):,} assistant messages{span}")
if sources:
    print("\n=== Sources merged ===")
    for d in sources:
        swh = sum(s["fresh"]*R_IN + s["cached"]*R_CACHE + s["out"]*R_OUT
                  for s in d["sessions_detail"]) / 1000
        print(f"  {d['source']:<28} {d['sessions']:3d} sessions  {swh:8.2f} kWh  "
              f"({swh/kwh:5.1%})  {', '.join(d['roots'])}")

print("\n=== Tokens (measured) ===")
for lbl, v in (("fresh input (incl. cache writes)", F), ("cached reads", C), ("output", O)):
    print(f"  {lbl:<34} {v/1e6:10.1f} M  ({v/(F+C+O):5.1%})")
print(f"  cache hit rate {C/(F+C):.1%} | output share of non-cached tokens {O/(F+O):.1%}")

print("\n=== Energy (derived, Couch rates) ===")
for lbl, v in (("fresh input", F*R_IN), ("cached reads", C*R_CACHE), ("output", O*R_OUT)):
    print(f"  {lbl:<34} {v/1000:8.2f} kWh  ({v/WH:5.1%} of energy)")
print(f"  {'TOTAL':<34} {kwh:8.2f} kWh")

g = GRIDS[a.grid]
co2 = kwh * g / 1000
print(f"\n=== CO2 and water at {a.grid} ({g:.1f} gCO2/kWh) ===")
print(f"  CO2            {co2:8.1f} kg   = {co2*1000/MILE_G:,.0f} miles / "
      f"{co2*1000/MILE_G*1.609:,.0f} km driving")
print(f"  water on-site  {kwh*WUE_ON:8.1f} L")
print(f"  water total    {kwh*(WUE_ON+WUE_OFF):8.1f} L    = "
      f"{kwh*(WUE_ON+WUE_OFF)/0.5:,.0f} x 500 mL bottles")

print("\n=== CO2 across every convention (kg / driving miles) ===")
for k, v in sorted(GRIDS.items(), key=lambda kv: kv[1]):
    kg = kwh * v / 1000
    print(f"  {k:<34} {v:6.1f} g/kWh {kg:8.1f} kg {kg*1000/MILE_G:7.0f} mi"
          f"{' <-' if k == a.grid else ''}")
lo, hi = min(GRIDS.values()), max(GRIDS.values())
print(f"  band: {kwh*lo/1000*1000/MILE_G:.0f}-{kwh*hi/1000*1000/MILE_G:.0f} miles "
      f"({hi/lo:.1f}x, purely from the accounting convention)")

wh = sorted(s["wh"] for s in sessions)
q = lambda p: wh[min(int(p * len(wh)), len(wh) - 1)]
print("\n=== Per-session distribution (Wh) ===")
print(f"  median {q(0.5):.0f} | p90 {q(0.9):,.0f} | max {wh[-1]:,.0f} | mean {st.mean(wh):,.0f}"
      f"  (mean/median = {st.mean(wh)/q(0.5):.0f}x)")

print("\n=== Heaviest sessions ===")
print(f"  {'Wh':>8} {'kg CO2':>7} {'msgs':>6}  project")
for s in sessions[:8]:
    print(f"  {s['wh']:8.0f} {s['wh']/1000*g/1000:7.2f} {s['msgs']:6d}  {s['project'][:52]}")

if a.by and hourly:
    if a.tz:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(a.tz)
    else:
        tz = datetime.datetime.now().astimezone().tzinfo
    UTC = datetime.timezone.utc
    LABEL = {"day": "%Y-%m-%d", "week": "%G-W%V", "month": "%Y-%m"}
    DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    bins = {}
    for k, (bf, bc, bo) in hourly.items():
        # "YYYY-MM-DDTHH" is UTC; move it into the display zone before bucketing
        local = datetime.datetime.strptime(k, "%Y-%m-%dT%H").replace(tzinfo=UTC).astimezone(tz)
        key = (f"{local.hour:02d}:00" if a.by == "hour" else
               DOW[local.weekday()] if a.by == "dow" else local.strftime(LABEL[a.by]))
        bins[key] = bins.get(key, 0.0) + (bf * R_IN + bc * R_CACHE + bo * R_OUT) / 1000

    if a.by == "day":       # keep calendar gaps visible rather than silently closing them
        d0, d1 = (datetime.date.fromisoformat(x) for x in (min(bins), max(bins)))
        for n in range((d1 - d0).days + 1):
            bins.setdefault(str(d0 + datetime.timedelta(days=n)), 0.0)
    order = (DOW if a.by == "dow" else
             [f"{h:02d}:00" for h in range(24)] if a.by == "hour" else sorted(bins))
    order = [k for k in order if k in bins]

    zname = a.tz or datetime.datetime.now().astimezone().strftime("%Z")
    unit = "hour of day" if a.by == "hour" else "day of week" if a.by == "dow" else a.by
    print(f"\n=== Energy by {unit} ({zname}) — kWh, and {a.grid} miles ===")
    peak = max(bins.values()) or 1
    for k in order:
        v = bins[k]
        bar = "█" * round(40 * v / peak)
        print(f"  {k:<11} {v:7.2f} kWh {v*g/1000*1000/MILE_G:6.0f} mi  {bar}")
    nz = [v for v in bins.values() if v > 0]
    print(f"  {len(nz)} active {unit} bins | busiest {max(bins, key=bins.get)} at "
          f"{peak:.2f} kWh | mean over active bins {sum(nz)/len(nz):.2f} kWh")

print("\nToken counts are measured; energy, CO2 and water are derived from third-party rates "
      "with 2-4x method uncertainty.")
print("Still uncounted: cloud sessions (server-side, never on local disk), Claude Desktop, "
      "claude.ai, and any machine not merged in.")
