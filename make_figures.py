"""Generate figures for the Claude environmental-impact report.
All plotted values are published third-party estimates/disclosures — see data/sourced_data.json.
Palette: dataviz reference palette (light mode)."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ---- palette (dataviz reference, light mode) ----
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.family": "DejaVu Sans",
    "text.color": INK, "axes.edgecolor": BASE, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9, "axes.titlesize": 10, "figure.dpi": 200,
})

D = json.load(open("data/sourced_data.json"))
FIG = "figures/"

# =========================================================================
# FIGURE 1 — Energy per request vs tokens, one panel per Claude model family
# =========================================================================
fig, axes = plt.subplots(2, 2, figsize=(9.2, 7.0), sharex=True, sharey=True)
fig.subplots_adjust(hspace=0.34, wspace=0.10, top=0.82, bottom=0.10, left=0.075, right=0.98)

XLIM = (2e2, 2e6); YLIM = (0.08, 200)

def panel_setup(ax, title, subtitle):
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_title(title, loc="left", fontweight="bold", color=INK, pad=14)
    ax.text(0, 1.035, subtitle, transform=ax.transAxes, fontsize=7.5, color=MUTED)
    ax.grid(True, which="both", alpha=0.5)

def gemini_ref(ax):
    ax.axhline(0.24, color=BASE, lw=1.0, ls=(0, (4, 3)))

# Panel 1: Claude 3.7 Sonnet (Jegham v6)
ax = axes[0, 0]
panel_setup(ax, "Claude 3.7 Sonnet", "Jegham et al. 2025 — black-box API benchmark")
jt = D["jegham_v6"]; cats = jt["prompt_categories"]
tok = [cats[c]["input_tokens"] + cats[c]["output_tokens"] for c in ("short", "medium", "long")]
for key, col, lbl in (("claude_3_7_sonnet", BLUE, "standard"),
                      ("claude_3_7_sonnet_et", ORANGE, "extended thinking")):
    vals = [jt["energy_wh"][key][c] for c in ("short", "medium", "long")]
    y = [v[0] for v in vals]; err = [v[1] for v in vals]
    ax.errorbar(tok, y, yerr=err, color=col, marker="o", ms=6, lw=2,
                capsize=3, mfc=col, mec=SURFACE, mew=1.2, label=lbl)
ax.legend(frameon=False, fontsize=8, loc="upper left", handlelength=1.4)
gemini_ref(ax)
ax.text(1.7e6, 0.26, "Gemini median prompt 0.24 Wh (measured, Google 2025)",
        fontsize=6.6, color=MUTED, ha="right", va="bottom")

# Panel 2: Claude Opus 4.5 / Sonnet 4.5 (Couch)
ax = axes[0, 1]
panel_setup(ax, "Claude Opus 4.5 / Sonnet 4.5 (agentic use)",
            "Couch 2026 — scaled from Epoch's GPT-4o anchor")
c = D["couch_2026"]
t = np.logspace(np.log10(XLIM[0]), np.log10(XLIM[1]), 100)
cache = t * c["wh_per_million_cached_read_tokens"] / 1e6   # cached-read bound
fresh = t * c["wh_per_million_input_tokens"] / 1e6         # fresh-input bound
out = t * c["wh_per_million_output_tokens"] / 1e6          # all-output bound
ax.fill_between(t, cache, out, color=BLUE, alpha=0.13, lw=0)
ax.plot(t, out, color=BLUE, lw=1.6)
ax.plot(t, fresh, color=BLUE, lw=1.2, ls=(0, (4, 2)))
ax.plot(t, cache, color=BLUE, lw=1.2, ls=(0, (1, 2)))
ms = c["median_session"]
ax.plot(ms["input_tokens"] + ms["output_tokens"], ms["wh"], "o", ms=7,
        color=ORANGE, mec=SURFACE, mew=1.2, zorder=5)
ax.annotate("median Claude Code session\n(~590k tokens, ~41 Wh —\nmost input is cached reads)",
            xy=(5.9e5, 41), xytext=(6e3, 30), fontsize=7.2, color=INK2,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.text(4.5e2, 4.5e2 * 1950 / 1e6 * 1.7, "output tokens: 1.95 Wh / k", fontsize=6.8,
        color=BLUE, rotation=32, rotation_mode="anchor")
ax.text(6e3, 6e3 * 390 / 1e6 * 0.52, "fresh input: 0.39 Wh / k", fontsize=6.8,
        color=BLUE, rotation=32, rotation_mode="anchor")
ax.text(4.5e4, 4.5e4 * 39 / 1e6 * 0.5, "cached input: 0.039 Wh / k", fontsize=6.8,
        color=BLUE, rotation=32, rotation_mode="anchor")
gemini_ref(ax)

# Panel 3: Claude Opus 4.7 (Digital Applied)
ax = axes[1, 0]
panel_setup(ax, "Claude Opus 4.7", "Digital Applied 2026 — blog synthesis, ±2–3×")
da = D["digital_applied_2026"]["claude_opus_4_7"]
x47 = [da["chat_tokens_approx"], da["long_context_tokens"]]
y47 = [da["chat_wh"], da["long_context_wh"]]
yerr = np.array([[y - y / 3 for y in y47], [y * 3 - y for y in y47]])
ax.errorbar(x47, y47, yerr=yerr, fmt="o", ms=7, color=AQUA, mfc=SURFACE,
            mec=AQUA, mew=1.8, capsize=3, lw=1.2, ls="none")
ax.annotate("standard chat\n0.78 Wh", xy=(x47[0], y47[0]), xytext=(1.8e3, 0.25),
            fontsize=7.2, color=INK2)
ax.annotate("800k-token context\n14.1 Wh", xy=(x47[1], y47[1]), xytext=(3.5e4, 18),
            fontsize=7.2, color=INK2)
ax.text(0.03, 0.05, "Hollow markers: lower-credibility source\n(methodology not fully public)",
        transform=ax.transAxes, fontsize=6.8, color=MUTED)
gemini_ref(ax)

# Panel 4: Claude Fable 5 — no data
ax = axes[1, 1]
panel_setup(ax, "Claude Fable 5 / Claude 5 generation", "Released 2026")
ax.text(0.5, 0.55, "No published data", ha="center", va="center",
        transform=ax.transAxes, fontsize=13, color=INK2, fontweight="bold")
ax.text(0.5, 0.40, "Neither Anthropic nor any third party has published\n"
        "an energy estimate for this model generation\n(as of Aug 11, 2026)",
        ha="center", va="center", transform=ax.transAxes, fontsize=8, color=MUTED)
gemini_ref(ax)

for ax in axes[1]:
    ax.set_xlabel("Tokens per request (input + output)", fontsize=8.5)
for ax in axes[:, 0]:
    ax.set_ylabel("Energy per request (Wh)", fontsize=8.5)

fig.suptitle("Energy per request vs. tokens — Claude models, all published estimates (none from Anthropic)",
             x=0.075, y=0.975, ha="left", fontsize=12, fontweight="bold", color=INK)
fig.text(0.075, 0.935, "Panels use different third-party methodologies and are not directly comparable; "
         "every point carries method-level uncertainty of roughly 2–4×. Log–log scales.",
         fontsize=8, color=INK2)
fig.savefig(FIG + "fig1_claude_energy_vs_tokens.png", bbox_inches="tight")
plt.close(fig)

# =========================================================================
# FIGURE 2 — Per-query estimates across providers/methods (dot plot, log x)
# =========================================================================
rows = [
    # (label, center, lo, hi, group)
    ("Gemini apps median — narrow boundary (chips only)", 0.10, None, None, 0),
    ("Gemini apps median — full boundary, incl. idle + PUE", 0.24, None, None, 0),
    ("Frontier model, median query (Oviedo/Microsoft sim.)", 0.31, 0.16, 0.60, 1),
    ("Frontier model, long/reasoning query (Oviedo sim.)", 3.91, 2.15, 7.05, 1),
    ("GPT-4o typical query (Epoch AI, first-principles)", 0.30, None, None, 2),
    ("ChatGPT average query (Altman claim, no methodology)", 0.34, None, None, 2),
    ("GPT-4.1 nano — long prompt (Jegham)", 0.454, 0.454 - 0.208, 0.454 + 0.208, 3),
    ("GPT-4o — long prompt (Jegham)", 1.788, 1.788 - 0.363, 1.788 + 0.363, 3),
    ("Claude 3.7 Sonnet — long prompt (Jegham)", 5.518, 5.518 - 0.751, 5.518 + 0.751, 3),
    ("Claude 3.7 Sonnet ext. thinking — long (Jegham)", 17.045, 17.045 - 4.4, 17.045 + 4.4, 3),
    ("DeepSeek-R1 — long prompt (Jegham)", 33.634, 33.634 - 3.798, 33.634 + 3.798, 3),
    ("OpenAI o3 — long prompt (Jegham)", 39.223, 39.223 - 20.317, 39.223 + 20.317, 3),
]
gcolors = {0: BLUE, 1: AQUA, 2: ORANGE, 3: YELLOW}
gnames = {0: "Measured in production (Google, Aug 2025)",
          1: "Production-grounded simulation (Joule, 2026)",
          2: "First-principles / company claim",
          3: "Black-box API benchmark, long prompts (arXiv:2505.09598v6)"}

fig, ax = plt.subplots(figsize=(9.2, 5.6))
fig.subplots_adjust(left=0.42, right=0.97, top=0.86, bottom=0.10)
ypos = []
y = 0
last_g = None
for label, cen, lo, hi, g in rows:
    if g != last_g and last_g is not None:
        y -= 0.55
    last_g = g
    ypos.append(y)
    y -= 1
for (label, cen, lo, hi, g), yy in zip(rows, ypos):
    col = gcolors[g]
    if lo is not None:
        ax.plot([lo, hi], [yy, yy], color=col, lw=2.4, solid_capstyle="round", alpha=0.55)
    ax.plot(cen, yy, "o", ms=7.5, color=col, mec=SURFACE, mew=1.2, zorder=5)
    ax.text(cen, yy + 0.34, f"{cen:g}", ha="center", fontsize=7, color=INK2)
ax.set_yticks(ypos)
ax.set_yticklabels([r[0] for r in rows], fontsize=8, color=INK)
ax.set_xscale("log")
ax.set_xlim(0.05, 90)
ax.set_ylim(min(ypos) - 0.8, max(ypos) + 0.9)
ax.grid(axis="x", which="both", alpha=0.5); ax.grid(axis="y", alpha=0)
ax.set_xlabel("Energy per request (Wh) — log scale", fontsize=9)
handles = [Line2D([], [], marker="o", ls="none", ms=7, color=gcolors[k],
                  mec=SURFACE, label=gnames[k]) for k in gnames]
ax.legend(handles=handles, frameon=False, fontsize=7.6, loc="upper right", handletextpad=0.4)
ax.set_title("Published per-request energy estimates span two orders of magnitude —\nmostly due to method and boundary, not model physics",
             loc="left", fontweight="bold", fontsize=11.5, pad=12)
fig.savefig(FIG + "fig2_cross_provider.png", bbox_inches="tight")
plt.close(fig)

# =========================================================================
# FIGURE 3 — Token scaling: decode (output) vs prefill (input context)
# =========================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.2))
fig.subplots_adjust(wspace=0.28, top=0.80, bottom=0.14, left=0.08, right=0.98)

# (a) energy vs OUTPUT tokens — measured open models + frontier estimates
ax1.set_xscale("log"); ax1.set_yscale("log")
t = np.logspace(2, 4.2, 50)
# Llama 3.1 8B: 0.12 J/token (ML.Energy, H100, batch 64, Dec 2025)
ax1.plot(t, t * 0.12 / 3600, color=BLUE, lw=2)
ax1.text(9e2, 9e2 * 0.12 / 3600 * 0.55, "Llama 3.1 8B — 0.12 J/tok (measured)", fontsize=7,
         color=BLUE, rotation=33, rotation_mode="anchor")
# Qwen3-32B measured response-level points
q = D["ml_energy"]["qwen3_32b"]
qx = [q["chat"]["mean_output_tokens"], q["reasoning"]["mean_output_tokens"]]
qy = [q["chat"]["j_per_response"] / 3600, q["reasoning"]["j_per_response"] / 3600]
ax1.plot(qx, qy, "o-", color=ORANGE, lw=2, ms=6.5, mec=SURFACE, mew=1.1)
ax1.text(1.05e3, 0.075, "Qwen3-32B (chat → reasoning):\n~10× tokens → ~23× energy", fontsize=7,
         color=ORANGE, rotation=38, rotation_mode="anchor")
# Frontier full-boundary (Oviedo): 0.31 Wh @ ~500 out; 3.91 Wh @ ~7.5k out
ax1.plot([500, 7500], [0.31, 3.91], "s-", color=AQUA, lw=2, ms=6, mec=SURFACE, mew=1.1)
ax1.text(6.2e2, 0.62, "Frontier >200B, full boundary\n(Oviedo 2026: 15× tokens → 13× energy)", fontsize=7,
         color="#0f7a54", rotation=27, rotation_mode="anchor")
ax1.set_xlim(1e2, 2e4); ax1.set_ylim(2e-3, 30)
ax1.set_xlabel("Output tokens", fontsize=8.5)
ax1.set_ylabel("Energy per request (Wh)", fontsize=8.5)
ax1.set_title("a. Decode: energy grows ~linearly with output tokens", loc="left",
              fontweight="bold", fontsize=9.5)
ax1.grid(True, which="both", alpha=0.5)

# (b) energy vs INPUT context — modeled (Epoch) + Jegham Claude points
ax2.set_xscale("log"); ax2.set_yscale("log")
ex = [500, 10000, 100000]; ey = [0.3, 2.5, 40]
ax2.plot(ex, ey, "o--", color=BLUE, lw=1.8, ms=6.5, mec=SURFACE, mew=1.1)
ax2.annotate("GPT-4o, modeled (Epoch AI 2025):\nprefill becomes supra-linear\nat long context", xy=(1e5, 40),
             xytext=(2.5e3, 55), fontsize=7, color=INK2,
             arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
jx = [100, 1000, 10000]
jy = [jt["energy_wh"]["claude_3_7_sonnet"][cc][0] for cc in ("short", "medium", "long")]
ax2.plot(jx, jy, "o-", color=ORANGE, lw=2, ms=6.5, mec=SURFACE, mew=1.1)
ax2.text(1.5e2, 1.6, "Claude 3.7 Sonnet (Jegham)\noutput also rises 300→1.5k tok", fontsize=7,
         color=ORANGE, va="bottom")
ax2.set_xlim(50, 3e5); ax2.set_ylim(0.1, 150)
ax2.set_xlabel("Input (context) tokens", fontsize=8.5)
ax2.set_title("b. Prefill: long context becomes the dominant cost", loc="left",
              fontweight="bold", fontsize=9.5)
ax2.grid(True, which="both", alpha=0.5)

fig.suptitle("How energy scales with tokens (published measurements and models; log–log)",
             x=0.08, ha="left", fontsize=11.5, fontweight="bold", color=INK)
fig.text(0.08, 0.875, "Dashed = modeled, solid = measured. Peer-reviewed finding (ACL 2025): decode energy scales linearly with output length "
         "and dominates typical requests; prefill energy is negligible at short context.", fontsize=7.6, color=INK2)
fig.savefig(FIG + "fig3_token_scaling.png", bbox_inches="tight")
plt.close(fig)

# =========================================================================
# FIGURE 4 — Anthropic-linked data center capacity + grid carbon intensity
# =========================================================================
sites = [
    # label, firm MW, additional planned MW, grid annotation
    ("New Carlisle, IN — AWS Project Rainier\n(~1M Trainium2; also PA & MS sites, MW n/d)", 910, 2250 - 910,
     "PJM / RFCW · 413 gCO₂/kWh"),
    ("Google Cloud TPUs — locations undisclosed\n(up to 1M TPUs, '>1 GW in 2026')", 0, 1000,
     "grid unknown · n/d"),
    ("Lake Mariner, NY — TeraWulf/Fluidstack*\n(liquid-cooled; former coal site)", 520, 750 - 520,
     "NYISO upstate / NYUP · 110 gCO₂/kWh"),
    ("Hawesville, KY — TeraWulf, 20-yr lease\n(online H2 2027)", 0, 401,
     "MISO via Big Rivers · subregion n/d"),
    ("West Texas — Cipher/Fluidstack sites*\n(Barber Lake + Abernathy)", 375, 0,
     "ERCOT / ERCT · 333 gCO₂/kWh"),
    ("Memphis, TN — 'Colossus 1' (all compute)\n(~220k GPUs)", 300, 0,
     "on-site gas turbines (reported) · n/d"),
]
fig, ax = plt.subplots(figsize=(9.2, 4.8))
fig.subplots_adjust(left=0.34, right=0.80, top=0.80, bottom=0.12)
ypos = np.arange(len(sites))[::-1]
for yy, (label, firm, planned, grid) in zip(ypos, sites):
    if firm:
        ax.barh(yy, firm, height=0.58, color=BLUE, edgecolor=SURFACE, linewidth=0.8)
    if planned:
        ax.barh(yy, planned, left=firm, height=0.58, color=BLUE, alpha=0.28,
                edgecolor=SURFACE, linewidth=0.8)
    total = firm + planned
    ax.text(total + 25, yy, grid, va="center", fontsize=7.4, color=INK2, clip_on=False)
    ax.text(total + 25, yy - 0.27, "", va="center")
ax.set_yticks(ypos)
ax.set_yticklabels([s[0] for s in sites], fontsize=7.8, color=INK)
ax.set_xlim(0, 2400)
ax.set_xlabel("Capacity (MW) — solid: operating/leased as reported; light: announced/planned", fontsize=8.5)
ax.grid(axis="x", alpha=0.5); ax.grid(axis="y", alpha=0)
fig.text(0.03, 0.955, "Where Claude physically runs: Anthropic-linked compute capacity and local grid carbon intensity",
         fontweight="bold", fontsize=11.5, color=INK)
fig.text(0.03, 0.905, "*Site attribution reported by trade press, never confirmed by Anthropic. Grid intensities: EPA eGRID 2023 (Rev 2, Jun 2025). "
         "Capacity ≠ average draw.", fontsize=7.6, color=INK2)
fig.savefig(FIG + "fig4_datacenters.png", bbox_inches="tight")
plt.close(fig)

# =========================================================================
# FIGURE 5 — Disclosed / published training footprints (Claude: none)
# =========================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.3))
fig.subplots_adjust(wspace=0.30, top=0.78, bottom=0.22, left=0.09, right=0.97)

# (a) training energy
te = [("BLOOM 176B\nmeasured, 2022", 433, BLUE, 1.0),
      ("GPT-3 175B\nestimated, 2021", 1287, BLUE, 1.0),
      ("Llama 3.1 405B\nderived*", 21600, BLUE, 0.45)]
x = np.arange(len(te) + 1)
for i, (lbl, v, col, alpha) in enumerate(te):
    ax1.bar(i, v, color=col, alpha=alpha, width=0.6, edgecolor=SURFACE)
    ax1.text(i, v * 1.15, f"{v:,.0f}", ha="center", fontsize=7.6, color=INK2)
ax1.text(3, 900, "any Claude model:\nno disclosure,\nno credible estimate", ha="center",
         fontsize=7.6, color=INK2, style="italic")
ax1.bar(3, 0, color=MUTED)
ax1.set_yscale("log"); ax1.set_ylim(100, 8e4)
ax1.set_xticks(x)
ax1.set_xticklabels([t[0] for t in te] + ["Claude\n(all versions)"], fontsize=7.4)
ax1.set_ylabel("Training energy (MWh, log)", fontsize=8.5)
ax1.set_title("a. Training energy", loc="left", fontweight="bold", fontsize=9.5)
ax1.grid(axis="y", which="both", alpha=0.5); ax1.grid(axis="x", alpha=0)

# (b) training carbon
tc = [("BLOOM\nmeasured,\nnuclear grid", 50.5, BLUE, 1.0, ""),
      ("GPT-3\nestimated", 552, BLUE, 1.0, ""),
      ("Claude 4 run\nexternal est.,\nlow credibility", 5000, AQUA, 0.35, "//"),
      ("Llama 3.1\n405B\ndisclosed", 8930, BLUE, 1.0, ""),
      ("Mistral\nLarge 2\nLCA†", 20400, BLUE, 0.45, "")]
for i, (lbl, v, col, alpha, hatch) in enumerate(tc):
    ax2.bar(i, v, color=col, alpha=alpha, width=0.6, edgecolor=SURFACE, hatch=hatch)
    ax2.text(i, v * 1.15, f"{v:g}", ha="center", fontsize=7.6, color=INK2)
ax2.set_yscale("log"); ax2.set_ylim(10, 1.5e5)
ax2.set_xticks(range(len(tc)))
ax2.set_xticklabels([t[0] for t in tc], fontsize=6.8)
ax2.set_ylabel("tCO₂e (log)", fontsize=8.5)
ax2.set_title("b. Training carbon", loc="left", fontweight="bold", fontsize=9.5)
ax2.grid(axis="y", which="both", alpha=0.5); ax2.grid(axis="x", alpha=0)

fig.suptitle("Published training footprints — the Claude column is the finding",
             x=0.09, ha="left", fontsize=11.5, fontweight="bold", color=INK)
fig.text(0.09, 0.845, "Grid choice dominates carbon: BLOOM used 1/3 of GPT-3's energy but emitted ~1/11 of its CO₂e (French nuclear grid, 57 gCO₂/kWh). "
         "Hatched/light bars: derived or lower-credibility values.", fontsize=7.6, color=INK2)
fig.text(0.09, 0.015, "*Llama 3.1 405B energy derived from Meta's disclosed 30.84M H100 GPU-hours × 700 W TDP (no PUE).  "
         "†Mistral LCA value covers training + 18 months of usage, incl. embodied emissions.", fontsize=7.0, color=MUTED)
fig.savefig(FIG + "fig5_training.png", bbox_inches="tight")
plt.close(fig)

print("figures done")
