"""Figure for the researcher-session companion report. Derived from published rates."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; MUTED = "#898781"
GRID = "#e1e0d9"; BASE = "#c3c2b7"
BLUE = "#2a78d6"; ORANGE = "#eb6834"; AQUA = "#1baf7a"; YELLOW = "#eda100"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "text.color": INK, "axes.edgecolor": BASE,
    "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 9, "figure.dpi": 200,
})

W = 800_000
R_IN, R_OUT, R_CACHE = 390 / 1e6, 1950 / 1e6, 39 / 1e6

def session(N, f, cached=True):
    step = W / N
    hist = step * N * (N - 1) / 2
    fresh, out = (1 - f) * W, f * W
    return (fresh * R_IN + out * R_OUT + hist * R_CACHE) if cached else ((fresh + hist) * R_IN + out * R_OUT)

def session_da(N):
    step = W / N
    return sum(0.78 + (14.1 - 0.78) * (k * step) / 800_000 for k in range(1, N + 1))

# ranges across N=20..30, f_out=0.2..0.8
couch_on = [session(N, f, True) for N in (20, 25, 30) for f in (0.2, 0.5, 0.8)]
couch_off = [session(N, f, False) for N in (20, 25, 30) for f in (0.2, 0.5, 0.8)]
E_ON = (min(couch_on), session(25, 0.5, True), max(couch_on))
E_OFF = (min(couch_off), session(25, 0.5, False), max(couch_off))
E_DA = (session_da(20) / 3, session_da(25), session_da(30) * 3)

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8.6, 7.6),
                                    gridspec_kw={"height_ratios": [1.1, 1.25, 0.95]})
fig.subplots_adjust(left=0.36, right=0.97, top=0.90, bottom=0.07, hspace=0.75)

# (a) energy per session
rows = [("Opus 4.7 blog rates, interpolated\n(Digital Applied, ±3×)", E_DA, AQUA),
        ("Opus 4.5 per-token rates, caching ON\n(Couch; f_out 0.2–0.8, N 20–30)", E_ON, BLUE),
        ("Opus 4.5 rates, caching OFF\n(full context re-read each turn)", E_OFF, ORANGE)]
for i, (lbl, (lo, c, hi), col) in enumerate(rows):
    y = len(rows) - 1 - i
    ax1.plot([lo, hi], [y, y], color=col, lw=3, alpha=0.5, solid_capstyle="round")
    ax1.plot(c, y, "o", ms=8, color=col, mec=SURFACE, mew=1.2, zorder=5)
    ax1.text(c, y + 0.3, f"{c:,.0f}", ha="center", fontsize=7.5, color=INK2)
ax1.set_yticks(range(len(rows)))
ax1.set_yticklabels([r[0] for r in rows][::-1], fontsize=7.6)
ax1.set_xscale("log"); ax1.set_xlim(40, 10000)
ax1.set_ylim(-0.6, len(rows) - 0.4 + 0.3)
ax1.grid(axis="y", alpha=0)
ax1.set_xlabel("Energy per session (Wh, log scale)", fontsize=8)
ax1.set_title("a. Session energy under the two published Claude rate-sets", loc="left",
              fontweight="bold", fontsize=9.5)

# (b) carbon, central frame (caching on), whiskers = its N/f range
grids = [("NY upstate (NYUP, 110 g/kWh)", 110), ("ERCOT (ERCT, 333 g/kWh)", 333),
         ("US average (348 g/kWh)", 348), ("Indiana PJM (RFCW, 413 g/kWh)", 413)]
for i, (lbl, ci) in enumerate(grids):
    y = len(grids) - 1 - i
    lo, c, hi = (E_ON[0] / 1000 * ci, E_ON[1] / 1000 * ci, E_ON[2] / 1000 * ci)
    ax2.plot([lo, hi], [y, y], color=BLUE, lw=3, alpha=0.5, solid_capstyle="round")
    ax2.plot(c, y, "o", ms=8, color=BLUE, mec=SURFACE, mew=1.2, zorder=5)
    ax2.text(hi + 18, y, f"{c:.0f} g", va="center", fontsize=7.5, color=INK2)
ax2.set_yticks(range(len(grids)))
ax2.set_yticklabels([g[0] for g in grids][::-1], fontsize=7.6)
ax2.set_xlim(0, 850); ax2.grid(axis="y", alpha=0)
ax2.set_xlabel("g CO$_2$e per session — central rate-set, caching on (uncached ≈ 3.6× higher)", fontsize=8)
ax2.set_title("b. Carbon depends on which grid serves the request (undisclosed)", loc="left",
              fontweight="bold", fontsize=9.5)

# (c) water, central frame
wrows = [("On-site (cooling, WUE 0.18 L/kWh)", 0.18, BLUE),
         ("Off-site (power plants, 3.14 L/kWh)", 3.142, ORANGE)]
for i, (lbl, wue, col) in enumerate(wrows):
    y = len(wrows) - 1 - i
    lo, c, hi = (E_ON[0] / 1000 * wue, E_ON[1] / 1000 * wue, E_ON[2] / 1000 * wue)
    ax3.plot([lo, hi], [y, y], color=col, lw=3, alpha=0.5, solid_capstyle="round")
    ax3.plot(c, y, "o", ms=8, color=col, mec=SURFACE, mew=1.2, zorder=5)
    ax3.text(hi + 0.12, y, f"{c:.2f} L", va="center", fontsize=7.5, color=INK2)
ax3.set_yticks(range(len(wrows)))
ax3.set_yticklabels([w[0] for w in wrows][::-1], fontsize=7.6)
ax3.set_xlim(0, 6.5); ax3.grid(axis="y", alpha=0)
ax3.set_xlabel("Litres per session — central rate-set, caching on (AWS multipliers, Jegham v6)", fontsize=8)
ax3.set_title("c. Water: the off-site (power-plant) share dominates", loc="left",
              fontweight="bold", fontsize=9.5)

fig.suptitle("A heavy Opus research session (20–30 prompts, 80% of a 1M-token window):\nderived energy, carbon, and water", x=0.03, y=0.985, ha="left", fontsize=11.5, fontweight="bold", color=INK)
fig.savefig("figures/fig_s1_session.png", bbox_inches="tight")
print({k: [round(v) for v in vals] for k, vals in {"DA": E_DA, "ON": E_ON, "OFF": E_OFF}.items()})
