"""Aggregate token statistics from local Claude Code transcripts.
Reads ONLY the usage counters on assistant messages; no message content is touched.
"""
import json, os, glob, statistics as st

ROOT = os.path.expanduser("~/.claude/projects")
R_IN, R_OUT, R_CACHE = 390/1e6, 1950/1e6, 39/1e6      # Wh/token, Couch 2026

sessions = []
for path in glob.glob(os.path.join(ROOT, "*", "*.jsonl")):
    fresh = cached = out = 0; msgs = 0
    for line in open(path, errors="replace"):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") != "assistant": continue
        u = (d.get("message") or {}).get("usage")
        if not isinstance(u, dict): continue
        # top-level only; `iterations` restates the same numbers
        fresh  += (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        cached += u.get("cache_read_input_tokens") or 0
        out    += u.get("output_tokens") or 0
        msgs   += 1
    if msgs:
        sessions.append(dict(project=os.path.basename(os.path.dirname(path)),
                             msgs=msgs, fresh=fresh, cached=cached, out=out,
                             wh=fresh*R_IN + cached*R_CACHE + out*R_OUT))

sessions.sort(key=lambda s: -s["wh"])
tot = lambda k: sum(s[k] for s in sessions)
F, C, O, W = tot("fresh"), tot("cached"), tot("out"), tot("wh")

print(f"{len(sessions)} sessions with usage data, {tot('msgs'):,} assistant messages\n")
print("=== Aggregate token mix ===")
print(f"  fresh input (incl. cache writes) : {F/1e6:10.1f} M  ({F/(F+C+O):5.1%} of all tokens)")
print(f"  cached reads                     : {C/1e6:10.1f} M  ({C/(F+C+O):5.1%})")
print(f"  output                           : {O/1e6:10.1f} M  ({O/(F+C+O):5.1%})")
print(f"\n  cache hit rate (cached / (fresh+cached)) : {C/(F+C):6.1%}")
print(f"  output share of NON-cached tokens        : {O/(F+O):6.1%}   <- brief's f, measured")
print(f"  output share of ALL processed tokens     : {O/(F+C+O):6.1%}")

print("\n=== Energy split at Couch rates ===")
for lbl, v in (("fresh input", F*R_IN), ("cached reads", C*R_CACHE), ("output", O*R_OUT)):
    print(f"  {lbl:14s}: {v/1000:8.2f} kWh  ({v/W:5.1%} of energy)")
print(f"  {'TOTAL':14s}: {W/1000:8.2f} kWh")

wh = sorted(s["wh"] for s in sessions)
print("\n=== Per-session energy (Wh) ===")
for q, lbl in ((0.5,"median"),(0.9,"p90"),(1.0,"max")):
    print(f"  {lbl:7s}: {wh[min(int(q*len(wh)), len(wh)-1)]:9.1f}")
print(f"  mean   : {st.mean(wh):9.1f}   (mean/median = {st.mean(wh)/wh[len(wh)//2]:.1f}x -> heavy tail)")

print("\n=== Ten largest sessions ===")
print(f"  {'Wh':>8} {'msgs':>6} {'out%':>6} {'cache%':>7}  project")
for s in sessions[:10]:
    f_share = s["out"]/(s["fresh"]+s["out"]) if s["fresh"]+s["out"] else 0
    c_share = s["cached"]/(s["fresh"]+s["cached"]) if s["fresh"]+s["cached"] else 0
    print(f"  {s['wh']:8.1f} {s['msgs']:6d} {f_share:6.1%} {c_share:7.1%}  {s['project'][:58]}")
