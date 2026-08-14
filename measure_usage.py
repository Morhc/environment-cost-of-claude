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
ap.add_argument("--plot", metavar="PNG", help="write an all-time figure: daily energy and "
                "cumulative CO2, each with its uncertainty band")
ap.add_argument("--event", action="append", metavar="DATE=LABEL", default=[],
                help="annotate a date on the plot, e.g. --event 2026-07-24='Pro -> Max'. "
                     "Repeatable.")
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
            cwd = None
            for line in open(path, errors="replace"):
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                # The directory name encodes the working directory but is lossy: "/", "." and "_"
                # all become "-", so it cannot be inverted. The records carry the real path.
                if cwd is None and d.get("cwd"):
                    cwd = d["cwd"]
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
                               dict(project=project, root=root, cwd=cwd, fresh=0, cached=0,
                                    out=0, msgs=0, subagents=0, first=first, last=last))
            s["fresh"] += f; s["cached"] += c; s["out"] += o; s["msgs"] += m
            s["subagents"] += len(parts) > 2
            s["cwd"] = s.get("cwd") or cwd
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
    host = platform.node()
    for sd in sessions:
        sd["source"] = host
    print(json.dumps({
        "source": host, "roots": [os.path.expanduser(r) for r in
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

if a.plot and hourly:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    # Palette: the dataviz reference instance, light mode — same hexes as make_figures.py.
    # Validated with scripts/validate_palette.js (all six checks pass).
    SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
    MUTED, GRIDC, BLUE, ORANGE = "#898781", "#e1e0d9", "#2a78d6", "#eb6834"
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans", "text.color": INK, "axes.edgecolor": "#c3c2b7",
        "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.grid": True, "grid.color": GRIDC, "grid.linewidth": 0.7, "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False, "font.size": 9, "figure.dpi": 200,
    })

    if a.tz:
        from zoneinfo import ZoneInfo
        ptz = ZoneInfo(a.tz)
    else:
        ptz = datetime.datetime.now().astimezone().tzinfo
    zlabel = a.tz or datetime.datetime.now().astimezone().strftime("%Z")

    daily = {}
    for k, (bf, bc, bo) in hourly.items():
        loc = (datetime.datetime.strptime(k, "%Y-%m-%dT%H")
               .replace(tzinfo=datetime.timezone.utc).astimezone(ptz))
        daily[loc.date()] = daily.get(loc.date(), 0.0) + (bf*R_IN + bc*R_CACHE + bo*R_OUT) / 1000
    d0, d1 = min(daily), max(daily)
    days = [d0 + datetime.timedelta(days=n) for n in range((d1 - d0).days + 1)]
    kwh = [daily.get(d, 0.0) for d in days]            # zero days kept: the gaps are signal
    cum = [sum(kwh[:i+1]) for i in range(len(kwh))]

    g_lo, g_hi = min(GRIDS.values()), max(GRIDS.values())
    lo_name = min(GRIDS, key=GRIDS.get).replace("_", " ")
    hi_name = max(GRIDS, key=GRIDS.get).replace("_", " ")

    BLUE_D, BLUE_L = "#184f95", "#86b6ef"   # blue ramp steps 600 / 250
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9.2, 8.8), sharex=True)
    fig.subplots_adjust(left=0.085, right=0.955, top=0.895, bottom=0.07, hspace=0.30)

    # (a) daily energy. Band = the low end of the rate's stated 2-4x method uncertainty.
    ax1.fill_between(days, [v/2 for v in kwh], [v*2 for v in kwh], color=BLUE, alpha=0.13, lw=0)
    ax1.plot(days, kwh, color=BLUE, lw=2, solid_capstyle="round")
    ax1.set_ylabel("kWh per day", fontsize=8.5)
    ax1.set_title("a. Daily energy — band is the ×/÷2 method uncertainty on the per-token rates",
                  loc="left", fontweight="bold", fontsize=9.5)
    pk = max(range(len(kwh)), key=lambda i: kwh[i])
    ax1.annotate(f"{kwh[pk]:.0f} kWh", (days[pk], kwh[pk]), textcoords="offset points",
                 xytext=(0, 7), ha="center", fontsize=7.5, color=INK2)
    ax1.yaxis.set_major_locator(MaxNLocator(5))

    # (b) cumulative CO2. Band = the sourced spread across grid accounting conventions.
    ax2.fill_between(days, [c*g_lo/1000 for c in cum], [c*g_hi/1000 for c in cum],
                     color=ORANGE, alpha=0.13, lw=0)
    ax2.plot(days, [c*g/1000 for c in cum], color=ORANGE, lw=2, solid_capstyle="round")
    ax2.set_ylabel("cumulative kg CO$_2$", fontsize=8.5)
    ax2.set_title(f"b. Cumulative CO$_2$ — line is {a.grid.replace('_',' ')}; band spans every "
                  f"grid convention ({lo_name} → {hi_name})",
                  loc="left", fontweight="bold", fontsize=9.5)
    for val, name, off in ((g_hi, hi_name, 4), (g, a.grid.replace("_", " "), 0),
                           (g_lo, lo_name, -10)):
        ax2.annotate(f"{cum[-1]*val/1000:.0f} kg", (days[-1], cum[-1]*val/1000),
                     textcoords="offset points", xytext=(6, off), fontsize=7.5,
                     color=INK2 if val == g else MUTED, va="center")
    ax2.yaxis.set_major_locator(MaxNLocator(5))

    # (c) cumulative water, stacked. On-site cooling and power-plant evaporation are two parts of
    # one quantity, not two categories, so they take two steps of a single sequential blue ramp
    # (steps 600 and 250; validated with --ordinal: monotone L, visible gap, light end 2.06:1).
    # The split IS the finding -- it is the boundary that makes published water figures disagree.
    on = [c*WUE_ON for c in cum]
    tot = [c*(WUE_ON+WUE_OFF) for c in cum]
    ax3.fill_between(days, 0, on, color=BLUE_D, lw=0, label="on-site cooling")
    ax3.fill_between(days, on, tot, color=BLUE_L, lw=0, label="power-plant evaporation")
    ax3.plot(days, tot, color=BLUE_D, lw=1.4, solid_capstyle="round")
    ax3.set_ylabel("cumulative litres", fontsize=8.5)
    ax3.set_title("c. Cumulative water — the split is the measurement boundary, not an error bar",
                  loc="left", fontweight="bold", fontsize=9.5)
    ax3.legend(loc="upper left", frameon=False, fontsize=8, handlelength=1.4,
               labelcolor=INK2, borderpad=0.2)
    ax3.annotate(f"{tot[-1]:,.0f} L  total", (days[-1], tot[-1]), textcoords="offset points",
                 xytext=(6, 2), fontsize=7.5, color=INK2, va="center")
    ax3.annotate(f"{on[-1]:,.0f} L  on-site", (days[-1], on[-1]), textcoords="offset points",
                 xytext=(6, -2), fontsize=7.5, color=MUTED, va="center")
    ax3.yaxis.set_major_locator(MaxNLocator(5))

    for spec in a.event:
        ds, _, lab = spec.partition("=")
        try:
            ed = datetime.date.fromisoformat(ds.strip())
        except ValueError:
            continue
        for ax in (ax1, ax2, ax3):
            ax.axvline(ed, color=INK2, lw=1.1, ls=(0, (4, 3)), alpha=0.75, zorder=1)
        ax1.annotate(lab.strip() or ds.strip(), (ed, ax1.get_ylim()[1]),
                     textcoords="offset points", xytext=(5, -10), fontsize=8,
                     color=INK2, fontweight="bold")
        before = [v for d, v in zip(days, kwh) if d < ed]
        after = [v for d, v in zip(days, kwh) if d >= ed]
        if before and after:
            ax1.annotate(f"mean/day  {sum(before)/len(before):.1f} → "
                         f"{sum(after)/len(after):.1f} kWh",
                         (ed, ax1.get_ylim()[1]), textcoords="offset points", xytext=(5, -24),
                         fontsize=7.5, color=MUTED)

    ax3.set_xlabel(f"date ({zlabel})", fontsize=8.5)
    fig.autofmt_xdate(rotation=0, ha="center")
    nsrc = len(sources or [1])
    fig.suptitle(f"Claude Code usage, {d0} to {d1} — {len(sessions)} sessions across "
                 f"{nsrc} machine{'s' if nsrc != 1 else ''}\n"
                 f"{kwh and sum(kwh):.0f} kWh measured in tokens, costed with published rates",
                 x=0.085, y=0.985, ha="left", fontsize=11.5, fontweight="bold", color=INK)
    fig.savefig(a.plot, bbox_inches="tight")
    print(f"\nwrote {a.plot}  ({len(days)} days, {sum(kwh):.1f} kWh)")

print("\nToken counts are measured; energy, CO2 and water are derived from third-party rates "
      "with 2-4x method uncertainty.")
print("Still uncounted: cloud sessions (server-side, never on local disk), Claude Desktop, "
      "claude.ai, and any machine not merged in.")
