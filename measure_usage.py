"""Claude Code transcripts -> tokens -> energy -> CO2 and water.

Reads ONLY the usage counters on assistant messages in ~/.claude/projects, including the
nested subagent and workflow transcripts (22% of energy on this machine).
No message content is opened, and nothing leaves the machine.

    python3 measure_usage.py                 # everything, US-average grid
    python3 measure_usage.py --days 30       # last 30 days only
    python3 measure_usage.py --grid PJM_West # cost it against a specific convention
    python3 measure_usage.py --list-grids    # show every available convention

Energy is DERIVED: measured token counts times Couch's (Jan 2026) per-token estimates for
Opus 4.5 / Sonnet 4.5, which carry the 2-4x method uncertainty documented in the main report.
The token counts are measured; everything downstream of them is not. Grid and water factors
come from data/sourced_data.json, so run this from the project root.
"""
import argparse
import datetime
import glob
import json
import os
import statistics as st
import time

D = json.load(open("data/sourced_data.json"))
c = D["couch_2026"]
R_IN, R_OUT, R_CACHE = (c["wh_per_million_input_tokens"] / 1e6,
                        c["wh_per_million_output_tokens"] / 1e6,
                        c["wh_per_million_cached_read_tokens"] / 1e6)
WUE_ON, WUE_OFF = 0.18, 3.142          # L/kWh, AWS multipliers used by Jegham et al. v6
MILE_G = 400                           # EPA average passenger vehicle, gCO2/mile

# Every grid convention the project carries, cheapest first. Three different questions:
# attributional (eGRID), short-run marginal (AVERT/PJM), long-run marginal (Cambium).
GRIDS = {f"eGRID_{k}": v for k, v in D["egrid_2023"]["gco2_per_kwh"].items()}
GRIDS |= {f"AVERT_{k.replace(' ', '_')}": v for k, v in D["avert_2023"]["gco2_per_kwh"].items()}
GRIDS |= {f"Cambium_{k}": v for k, v in D["cambium_2023_lrmer"]["gco2_per_kwh"].items()}
GRIDS["PJM_2022_shortrun"] = D["pjm_emissions_2022"]["flat_load_marginal_gco2_per_kwh_derived"]

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--days", type=float, help="only sessions active in the last N days")
ap.add_argument("--grid", default="eGRID_US_avg", help="convention for the headline (default US average)")
ap.add_argument("--project", help="substring filter on the project directory name")
ap.add_argument("--list-grids", action="store_true", help="print all conventions and exit")
a = ap.parse_args()

if a.list_grids:
    for k, v in sorted(GRIDS.items(), key=lambda kv: kv[1]):
        print(f"  {k:<34} {v:6.1f} gCO2/kWh")
    raise SystemExit
if a.grid not in GRIDS:
    raise SystemExit(f"unknown grid {a.grid!r}; try --list-grids")

# Transcripts nest: <project>/<session>.jsonl is the main thread, and
# <project>/<session>/subagents/[workflows/<wf>/]agent-*.jsonl are the subagents it spawned.
# Those subagent files carry real token spend and must be rolled into their parent session --
# missing them undercounted this machine's total by 22%.
ROOT = os.path.expanduser("~/.claude/projects")
agg = {}
for path in glob.glob(f"{ROOT}/**/*.jsonl", recursive=True):
    parts = os.path.relpath(path, ROOT).split(os.sep)
    if len(parts) < 2:
        continue
    project, session = parts[0], parts[1].removesuffix(".jsonl")
    if a.project and a.project not in project:
        continue
    fresh = cached = out = msgs = 0
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
        fresh += (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        cached += u.get("cache_read_input_tokens") or 0
        out += u.get("output_tokens") or 0
        msgs += 1
    if not msgs:
        continue
    s = agg.setdefault((project, session),
                       dict(project=project, msgs=0, fresh=0, cached=0, out=0,
                            subagents=0, first=first, last=last))
    s["msgs"] += msgs; s["fresh"] += fresh; s["cached"] += cached; s["out"] += out
    s["subagents"] += len(parts) > 2
    if first: s["first"] = min(s["first"] or first, first)
    if last: s["last"] = max(s["last"] or last, last)

sessions = list(agg.values())
for s in sessions:
    s["wh"] = s["fresh"] * R_IN + s["cached"] * R_CACHE + s["out"] * R_OUT

# --days filters on the session's own last activity, read from the transcript rather than from
# file mtime (mtime moves when a session is resumed and understates how far back history runs).
if a.days:
    cutoff = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - a.days * 86400))
    sessions = [s for s in sessions if (s["last"] or "") >= cutoff]

if not sessions:
    raise SystemExit("no sessions matched")

sessions.sort(key=lambda s: -s["wh"])
tot = lambda k: sum(s[k] for s in sessions)
F, C, O, WH = tot("fresh"), tot("cached"), tot("out"), tot("wh")
kwh = WH / 1000
stamps = [t for s in sessions for t in (s["first"], s["last"]) if t]
span = ""
if stamps:
    d0, d1 = min(stamps)[:10], max(stamps)[:10]
    days = (datetime.date.fromisoformat(d1) - datetime.date.fromisoformat(d0)).days
    span = f" | {d0} .. {d1} ({days} days)"

print(f"{len(sessions)} sessions ({tot('subagents')} with subagent transcripts) | "
      f"{tot('msgs'):,} assistant messages{span}")

print("\n=== Tokens (measured) ===")
for lbl, v in (("fresh input (incl. cache writes)", F), ("cached reads", C), ("output", O)):
    print(f"  {lbl:<34} {v/1e6:10.1f} M  ({v/(F+C+O):5.1%})")
print(f"  cache hit rate {C/(F+C):.1%} | output share of non-cached tokens {O/(F+O):.1%}")

print(f"\n=== Energy (derived, Couch rates) ===")
for lbl, v in (("fresh input", F*R_IN), ("cached reads", C*R_CACHE), ("output", O*R_OUT)):
    print(f"  {lbl:<34} {v/1000:8.2f} kWh  ({v/WH:5.1%} of energy)")
print(f"  {'TOTAL':<34} {kwh:8.2f} kWh")

g = GRIDS[a.grid]
co2 = kwh * g / 1000
print(f"\n=== CO2 and water at {a.grid} ({g:.1f} gCO2/kWh) ===")
print(f"  CO2            {co2:8.1f} kg   = {co2*1000/MILE_G:,.0f} miles / "
      f"{co2*1000/MILE_G*1.609:,.0f} km driving")
print(f"  water on-site  {kwh*WUE_ON:8.1f} L")
print(f"  water total    {kwh*(WUE_ON+WUE_OFF):8.1f} L    = {kwh*(WUE_ON+WUE_OFF)/0.5:,.0f} "
      f"x 500 mL bottles")

print(f"\n=== CO2 across every convention (kg / driving miles) ===")
for k, v in sorted(GRIDS.items(), key=lambda kv: kv[1]):
    kg = kwh * v / 1000
    mark = " <-" if k == a.grid else ""
    print(f"  {k:<34} {v:6.1f} g/kWh {kg:8.1f} kg {kg*1000/MILE_G:7.0f} mi{mark}")
lo, hi = min(GRIDS.values()), max(GRIDS.values())
print(f"  band: {kwh*lo/1000*1000/MILE_G:.0f}-{kwh*hi/1000*1000/MILE_G:.0f} miles "
      f"({hi/lo:.1f}x, purely from the accounting convention)")

wh = sorted(s["wh"] for s in sessions)
q = lambda p: wh[min(int(p * len(wh)), len(wh) - 1)]
print(f"\n=== Per-session distribution (Wh) ===")
print(f"  median {q(0.5):.0f} | p90 {q(0.9):,.0f} | max {wh[-1]:,.0f} | mean {st.mean(wh):,.0f}"
      f"  (mean/median = {st.mean(wh)/q(0.5):.0f}x)")

print(f"\n=== Heaviest sessions ===")
print(f"  {'Wh':>8} {'kg CO2':>7} {'msgs':>6}  project")
for s in sessions[:8]:
    print(f"  {s['wh']:8.0f} {s['wh']/1000*g/1000:7.2f} {s['msgs']:6d}  {s['project'][:52]}")

print("\nToken counts are measured; energy, CO2 and water are derived from third-party rates "
      "with 2-4x method uncertainty.\nClaude Code only — Desktop and web usage are not counted.")
