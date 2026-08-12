# Handoff — state of the work as of August 11, 2026

This project was built in a Claude cloud session and moved to local. Everything below is current;
`CLAUDE.md` holds the working rules, this file holds the state and the open threads.

## What exists

| File | What it is |
|:---|:---|
| `report.md` → `claude-environmental-impact-report.pdf` | Main report, 23 pp, 5 figures, 5 tables, ~80 sources |
| `researcher_brief.md` → `opus-researcher-footprint-brief.pdf` | Companion brief, 11 pp, 1 figure, for researchers estimating their own use |
| `data/sourced_data.json` | Every plotted value with its source, method, and credibility flag |
| `make_figures.py` | Figures 1–5 of the main report |
| `make_scenario_figure.py` | The brief's three-panel session figure |
| `scenario_calc.py` | The session arithmetic — prints all scenario permutations |
| `CLAUDE.md` | Project conventions (strictness rule, honesty rule, source hierarchy, palette) |

## The central finding

**Anthropic has published no first-party environmental data of any kind** — no sustainability
report, no Scope 1/2/3 inventory, no per-query energy/water/carbon figure, no PUE/WUE, no
training-run disclosure for any Claude model. Verified directly (`anthropic.com/sustainability`
404s; the Transparency Hub has no environmental content) and corroborated by SINK Project (31/100,
42nd of 43 SaaS companies), Stanford FMTI, MIT Tech Review, and Heatmap. Every Claude-specific
number in both documents is therefore third-party, and the credibility of each is assessed
individually.

## Key quantitative anchors

- **Per request (Claude):** 0.836 / 2.781 / 5.518 Wh (short/medium/long) for Claude 3.7 Sonnet;
  3.49 / 5.68 / 17.05 Wh with extended thinking. Jegham et al. arXiv:2505.09598 **v6** — note v6
  dropped the Claude 3.5 rows earlier versions carried. Method is contested and likely biased high.
- **Calibration from competitors:** Google's measured Gemini median = 0.24 Wh full boundary /
  0.10 Wh chip-only (the 2.4× ratio is the single most useful number in the literature);
  Epoch ~0.3 Wh; Microsoft/Oviedo median 0.31 Wh (IQR 0.16–0.60).
- **Per token (Opus 4.5):** 390 / 1,950 / 39 Wh per million fresh-input / output / cached-read
  tokens (Couch, Jan 2026).
- **Token scaling:** ~linear in output tokens; near-flat then supra-linear in input tokens
  (~0.3 Wh typical → ~2.5 Wh at 10k → ~40 Wh at 100k input, Epoch modeled).
- **Grids:** eGRID 2023 — RFCW (Indiana PJM) 413, ERCT 333, NYUP 110, US avg 348 gCO₂/kWh
  (all four verified against EPA's summary data, Aug 2026; US avg = 767.209 lb/MWh).
  Short-run marginal runs 1.24–1.86× higher; long-run marginal can run ~0.8× lower.
- **AVERT 2023 marginal ("uniform EE", flat 24/7 profile), region-matched to the sites:**
  Mid-Atlantic (New Carlisle) 618, Texas 587, New York 475, US national 648 gCO₂/kWh.
  **The fleet's ~3.8× average-accounting spread collapses to ~1.3× at the margin** — the most
  consequential number added since the first draft, and it weakens the clean-grid siting story.
- **The researcher session** (25 prompts, 800k window, caching on): 1.31 kWh → 456 g CO₂e
  (US avg) → 4.4 L water total / 0.24 L on-site. Full band across grid conventions: 375–834 g.

## Decisions already made (don't relitigate without reason)

1. **Strict sourcing in the main report; labeled derivation in the brief.** The user chose this
   explicitly when offered three options.
2. **The Fable 5 panel stays empty.** It is a finding, not an omission.
3. **Jegham v6, not v5 or the dashboard.** Two research agents returned conflicting numbers; v6 was
   fetched directly and is authoritative here.
4. **Marginal emissions presented two-sided.** An earlier draft offered a one-sided "we're
   conservative" framing; the Gagnon & Cole LRMER literature made that dishonest. Fixed.
5. **The "48% more carbon-intensive" figure is a siting effect, not a marginal-emissions argument.**
   Checked against the source (arXiv 2411.09786) — it uses attributional average factors. Our usage
   in the main report is correct as written; don't repurpose it.

## Closed since the first draft (August 11, 2026, local session)

- **AVERT regional marginal factors — done.** Retrieved, extracted (`extract_avert.py`, needs
  `openpyxl`), archived at `data/avert_emission_rates_2023.xlsx`, and written into
  `data/sourced_data.json` under `avert_2023`. The brief's Section 4 table now carries three
  region-matched rows instead of national stand-ins; the main report's siting section and both
  its summaries carry the marginal-vs-average qualification. Caveats recorded in the JSON:
  AVERT regions ≠ eGRID subregions (the NY comparison is the worst affected, since AVERT's NY is
  all of NYISO and eGRID's NYUP is upstate only), Indiana is split 21/79 Mid-Atlantic/Midwest
  (New Carlisle assigned to Mid-Atlantic because I&M is a PJM member), the rates are T&D-adjusted
  for retail loads, and EPA explicitly cautions against using AVERT for emissions accounting.
- **PJM emission reports — resolved, negatively.** There is no edition after 2018–2022. PJM's
  Reports & Notices library lists emissions reports for data years 2019, 2020, 2021 and 2022 only;
  the series was discontinued in favour of Data Miner and an interactive Emissions page. The
  2018–2022 numbers were verified by reading the PDF directly (2022 marginal 1,041 on-peak /
  976 off-peak vs 811 system average, lb/MWh), which confirms the 1.24× flat-load ratio the brief
  already printed. Two errors were fixed while there: the brief had cited AVERT at 1,405 lb/MWh
  against eGRID's 823 lb/MWh — mixed vintages giving 1.71×. On consistent 2023 vintages it is
  1,429 against 767, i.e. **1.86×**.
- **Note the unresolved disagreement:** AVERT's Mid-Atlantic marginal rate (618 gCO₂/kWh) and
  PJM's own flat-weighted 2022 marginal rate (457) differ by a third for roughly the same
  footprint. Both are printed rather than reconciled.

## Open threads / what I'd do next

- **A bottom-up bounding analysis** for the undisclosed models (Trainium2/TPU power draw, assumed
  utilization, PUE) was offered and not taken up. It would give defensible upper/lower bounds where
  the strict rule currently leaves blanks.
- **No measured long-context energy curve exists for any Claude model** — the 200k–1M context window
  is the signature feature and the biggest unmeasured term. Worth flagging to anyone with API access
  and a power meter.
- **Prompt caching's real energy effect is unquantified in the literature.** Couch prices it at ~1/10
  fresh input; nobody has measured it. It's the largest single lever in the session calculation.
- **No marginal *water*-intensity factors were found.** The off-site water figure inherits the same
  dispatch logic as carbon (a marginal gas unit evaporates cooling water; wind and solar do not),
  but nothing published quantifies it. Flagged in the brief, unquantified.

## Rebuilding

See `README.md`. Short version: `make` — needs pandoc, xelatex + lmodern, and matplotlib.
The repo is now under git (initialised locally, August 11, 2026; no remote configured).
PDFs are gitignored as build products — run `make` to regenerate them.

On macOS the documents' DejaVu fonts are not present by default and xelatex fails with a fontspec
error; `brew install --cask font-dejavu` fixes it and keeps the typography identical to the
Ubuntu-built originals.
