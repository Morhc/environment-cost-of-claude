# Handoff — state of the work as of August 14, 2026

**The repo is a tool now, not a report.** `dashboard.py` measures your own Claude Code usage across
every machine you work on and costs it in energy, CO₂ and water; `PROVENANCE.md` documents where
every rate and factor comes from. The 28-page report and 16-page brief were retired on 14 August
once the dashboard replaced their hypothetical session with real measurement. Their sourcing lives
on in `PROVENANCE.md`; the claims audit, aggregate-consumption literature and section-by-section
review of the academic record were dropped and remain in git history at `3d7008a`.

Published at **github.com/Morhc/environment-cost-of-claude** (public, MIT + CC BY 4.0).
`CLAUDE.md` holds the working rules; this file holds state and open threads.

## What exists

| File | What it is |
|:---|:---|
| `PROVENANCE.md` | Where every number comes from, how far to trust it, what is unknown. 9 sections. |
| `dashboard.py` / `dashboard.html` | Local dashboard, four tabs, Refresh button. Stdlib only, loopback only, whitelisted routes. Threaded, so a slow SSH refresh cannot starve anything else. |
| `make_app.py` | Builds the macOS double-click app: icon, and a launcher that sets `DASHBOARD_AUTOQUIT=1`. Embeds this checkout's absolute path, so the bundle is built, never committed. |
| `make_favicon.py` | The leaf mark. `svg()` is the single source for both the tab favicon and the app icon. |
| `measure_usage.py` | Transcripts → tokens → energy/CO₂/water. `--raw`, `--merge`, `--by`, `--plot`, `--list-projects`. |
| `collect_usage.sh` | Local + SSH hosts, merged. |
| `data/sourced_data.json` | Every value with source, method, credibility flag. Includes equivalences. |
| `extract_avert.py` / `extract_cambium.py` | Short-run and long-run marginal grid factors from EPA / NREL. |
| `training_bounds.py` | Derived training-energy bounds behind PROVENANCE §7. |
| `make_figures.py` | The five sourced figures. |
| `sources.json` | **Untracked.** Your machines and label globs. `sources.example.json` is the template. |
| `data/usage_cache.json` | **Untracked.** Collected usage; holds every directory you have worked in. |

## Current measured totals (14 August 2026, both machines)

892.5 kWh · 311 kg CO₂e (US average) · 2,965 L water of which 161 L on-site · 103 sessions ·
54,700 messages · 60 days. Cluster holds ~62%. Band across the fifteen conventions: 245–1,732
driving miles. **Any total is a snapshot that includes the work of producing it.**

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
  Short-run marginal runs 1.24–1.86× higher; long-run marginal runs 0.34–1.13× of the average
  depending on region.
- **Three region-matched grid conventions** (gCO₂/kWh), the spine of the siting argument:

  | Site | eGRID avg | AVERT short-run | Cambium long-run (20 yr) |
  |:---|---:|---:|---:|
  | New Carlisle, IN | 413 | 618 | 166 |
  | W Texas | 333 | 587 | 114 |
  | Lake Mariner, NY | 110 | 475 | 124 |
  | *spread* | *3.75×* | *1.30×* | *1.46×* |

  **The siting spread compresses under both marginal conventions, and the ranking inverts on the
  20-year one** — the most consequential finding added since the first draft.
- **The researcher session** (25 prompts, 800k window, caching on, measured f = 0.20): 0.94 kWh
  → 326 g CO₂e (US avg) → 3.11 L water total / 0.17 L on-site. Full band across grid conventions:
  103–607 g (5.9×).

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

- **Bottom-up training bounds — done**, now PROVENANCE §7, at the user's explicit
  direction (offered four placements; they chose the labeled appendix). `training_bounds.py`
  calibrates Wh/FLOP against Llama 3.1 405B's disclosed 3.8e25 FLOP + 30.84M H100-hours rather
  than stacking hardware guesses, then applies it to Epoch's Claude FLOP estimates. Claude 3 Opus
  ≈ **10.4 GWh** central (7.2–14.3 across the MFU band), 3.5 Sonnet ≈ 17.5, 3.7 Sonnet ≈ 22.0.
  Validation: Meta's disclosed 8,930 tCO₂e ÷ our 21.6 GWh backs out 414 gCO₂/kWh, a real US grid
  factor. The honest width is the Epoch FLOP uncertainty, not the conversion — 3.7 Sonnet spans
  4.9–89.6 GWh on Epoch's own stated FLOP range. CLAUDE.md now records this as exception #2.

- **Long-run marginal rates retrieved (NREL Cambium 2023) — the siting finding now rests on the
  right convention.** The earlier AVERT-only version over-claimed: it quantified the fleet's
  spread as collapsing 3.8× → 1.3× on short-run marginal rates, when AVERT's own docs disclaim
  horizons beyond 5 years and these are 20-year assets. Cambium's 20-year levelized LRMERs (its
  published defaults: 2025 start, 20 yr, 3% real, mid-case) are region-matched: **PJM_West 166,
  ERCOT 114, NYISO 124 gCO₂/kWh**. The finding survives and is *stronger* — the spread compresses
  under both marginal conventions, which are biased in opposite directions on level (1.30× short-run,
  1.46× long-run). And the ranking inverts: Texas is cleanest on a 20-year basis, not upstate NY,
  because ERCOT/PJM_West induce build far cleaner than their current mix (0.34×, 0.40× of average)
  while NY induces build no cleaner than its existing hydro and nuclear (1.13×).
- **The output share is measured, and the old assumption was 1.4× too high.** `measure_usage.py`
  reads token counters from local Claude Code transcripts (counters only, never content) and now
  carries them through to CO₂ and water across all 15 grid conventions. Over 56 sessions /
  24,956 assistant messages / 47 days for one heavy user: cache hit rate **98.1%**, main-thread
  output share **19–24%** (against an assumed 0.5), cached reads **72% of energy**, distribution
  median 89 Wh / p90 21.8 kWh / max 84.1 kWh (mean/median 62), total **306.9 kWh → 107 kg CO₂e →
  267 driving miles** at the US average (85–595 miles across conventions). The brief's headline
  moved from 1.31 kWh / 456 g / 4.4 L to **0.94 kWh / 326 g / 3.11 L**. Caveat recorded in
  Section 5: Claude Code's input is mostly tool results, a different workload from the
  paper-reading scenario modelled.
- **Usage measurement is now multi-source and operational** (`collect_usage.sh`). It runs
  `measure_usage.py --raw` locally and pipes the same script over SSH to named hosts (remote needs
  only python3; `--raw` reads no data files), then merges. For this user: laptop **308 kWh** +
  the cluster **492 kWh** = **800 kWh / 279 kg CO₂e / ~700 driving miles** over 58 days, 104 sessions.
  **62% of the total was on the cluster**, so every laptop-only figure quoted earlier was a 2.6×
  undercount. On the cluster the roots are `/home/$USER/.claude/projects` and
  `/scratch/$USER/.claude/projects`; `collect_usage.sh` discovers both and scopes them to
  `$USER`. The account name is deliberately not recorded here — it lives in the maintainer's
  own notes, so this repo stays user-agnostic.
- **Scope remote discovery to `$USER`.** A first version globbed `/scratch/*/.claude/projects`,
  which matched another user's group-readable directory on the shared cluster and silently added
  ~2.7 kWh of someone else's usage. Fixed to `/scratch/$USER`. On a shared cluster, wildcards over home-like
  paths are both wrong and not yours to read.
- **Three path-layout traps, all found the hard way, all now handled in `scan()`:** nested
  subagent/workflow transcripts (22% of laptop energy), the older *flat* `projects/<session>.jsonl`
  layout (all of the cluster scratch), and file mtime as a proxy for history span (29 days vs a true
  47). Each one silently undercounted, and each undercount flattered the result.
- **Watch the nesting.** Subagent and workflow transcripts live at
  `<project>/<session>/subagents/[workflows/<wf>/]agent-*.jsonl`. A first version of the tool
  globbed only `*/*.jsonl` and so **undercounted energy by 22%**. Any per-user accounting that
  ignores agentic side-contexts will understate by roughly that much. Also do not use file mtime
  for the history span — it moves when a session is resumed and gave 29 days against a true 47;
  read the in-file `timestamp` field instead.

## Traps that cost time (all fixed, do not reintroduce)

1. **Transcripts nest.** Subagent/workflow files live at `<project>/<session>/subagents/...` —
   missing them undercounted by 22%.
2. **Two path layouts.** `<project>/<session>.jsonl` and a flat `<session>.jsonl`; the flat one is
   all of the cluster's scratch.
3. **Project directory names are lossy.** `/`, `.` and `_` all map to `-`, so decoding them turns
   `nucrate_viewer` into `nucrate/viewer`. Use the `cwd` field from the records.
4. **cwd changes mid-session.** 14 of 37 home-directory sessions moved; attributing a whole session
   to its first cwd made `/Users/<me>` look like a 103 kWh project. Tokens follow the cwd per message.
5. **Never use file mtime for the history span.** It moves on resume; gave 29 days against a true 47.
6. **Scope remote discovery to `$USER`.** A `/scratch/*` wildcard matched a colleague's readable
   directory and added their usage to the total.
7. **Do not serve the repo directory over HTTP.** `SimpleHTTPRequestHandler` + `chdir` published
   `sources.json` and `usage_cache.json`. The dashboard whitelists its routes and checks `Host`.
8. **Do not detect a closed tab by asking the tab.** The first version of the app's auto-quit used a
   heartbeat plus `sendBeacon` on `pagehide`. `sendBeacon` is best-effort by specification, and
   background tabs get their timers throttled to roughly one a minute, which forces the fallback
   timeout up to minutes — so a missed beacon looks exactly like a broken feature. The tab now holds
   an event-stream connection open and the server watches the socket. Detect closure with `select()`
   on the peer, not by writing: the first write to a closed peer succeeds into the send buffer and
   only the second raises, so a write-based check lags by a whole keepalive interval.
9. **`qlmanage` flattens SVGs onto opaque white.** It is the only SVG rasteriser macOS ships, so the
   app icon is rendered twice — over white and over black — and the discarded alpha solved back out.
   Downscale icons with `BOX`, not `LANCZOS`, whose ringing leaves a halo at 16 px.
10. **Never name a shell loop variable `path` in zsh.** It is tied to `$PATH`; a `read sha path` in
    the privacy audit wiped the shell's PATH and every later command in that script failed.

## Open threads / what I'd do next
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
`make app` additionally needs numpy/Pillow and macOS's own `qlmanage` and `iconutil`.

The repo is under git (initialised locally, August 11, 2026) and published at
`github.com/Morhc/environment-cost-of-claude`, **public**. Two files must never be committed:
`sources.json` (machine names, and label globs that can name colleagues' paths) and
`data/usage_cache.json` (every working directory you have ever used). Both are gitignored, and a
full-history audit on August 14 confirmed neither has ever been committed, that no username,
hostname or absolute path appears in any blob on any branch, and that the retired report PDFs still
reachable in history contain none either. Re-run that audit before adding anything generated from
transcripts — deleted files survive in git history, so genericising the working tree is not enough.
PDFs are gitignored as build products — run `make` to regenerate them.

On macOS the documents' DejaVu fonts are not present by default and xelatex fails with a fontspec
error; `brew install --cask font-dejavu` fixes it and keeps the typography identical to the
Ubuntu-built originals.
