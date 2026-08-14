# Project conventions — Claude environmental impact analysis

Read this before touching anything. These rules were set by the user and are load-bearing.

## The strictness rule (non-negotiable)

**Only published, sourced values appear in `PROVENANCE.md` and the dashboard.** No fillers, no
placeholder numbers, no plausible-sounding extrapolations. Where no published estimate exists —
notably the Claude Fable 5 / Claude 5 generation — the gap is *displayed as a finding*
("No published data"), not papered over.

The one deliberate exception is the **training-bounds section of `PROVENANCE.md`** (§7), which
converts Epoch's FLOP estimates into energy. It is confined to that section, every value is marked
derived, its width is presented as the finding, and it is reproducible via `training_bounds.py`.

If a second exception is ever proposed it needs the same treatment: a quarantined location,
labeled values, signed error directions, and a script that regenerates it.

**Measured data is not an exception** — it outranks everything. The dashboard reports token
counters read from local Claude Code transcripts (`measure_usage.py`). Where a measurement exists it
replaces the corresponding assumption outright, and the assumption's former value is stated so the
correction is visible. Read only the usage counters, never message content.

## Grid accounting

Three conventions, three different questions, all three printed:

- **eGRID annual average** — attributional; the right basis for an inventory and this project's headline.
- **AVERT short-run marginal** — what the grid burns tonight because of this load. Note EPA's own
  caution that AVERT is "not a tool for emissions accounting", and its 0.5% displacement assumption,
  which a gigawatt-scale campus violates.
- **NREL Cambium long-run marginal** — what gets *built* because the load persists. This is the
  horizon-appropriate one for multi-decade campuses (AVERT explicitly disclaims >5 years), and it is
  what the siting argument must rest on.

Never present a marginal number as if it were attributional, or vice versa. Where two authoritative
sources for the same quantity disagree — AVERT's Mid-Atlantic 618 vs PJM's own 457 gCO2/kWh — print
both as an error bar rather than picking a winner. That is a standing instruction from the user.

## The honesty rule

When presenting an estimate, state which direction it is likely to be wrong in. If the error can't
be signed, say so explicitly rather than implying the printed ± is a total uncertainty. The user's
instruction was literally "We should do things honestly" — applied, this meant:

- The dashboard draws the ×/÷2 rate band on both the daily and cumulative curves, because the
  uncertainty is multiplicative and compounds into the total rather than averaging out.
- Grid accounting is presented as **two-sided** (short-run marginal runs 1.24–1.86× *above* the
  average; long-run marginal runs 0.34–0.40× *below* it at the Indiana and Texas sites, and 1.13×
  above at the New York one), never as a one-sided "we're conservative" claim.
- Where two authoritative sources disagree — AVERT's 618 gCO₂/kWh against PJM's own 457 — print
  both as an error bar rather than picking a winner. Standing instruction from the user.

## Source hierarchy

1. Primary corporate disclosures and regulatory filings
2. Peer-reviewed measurements
3. Credible preprints with published methodology (Epoch AI, ML.ENERGY, Microsoft/Oviedo)
4. Trade press for verifiable facts only (capacity, leases, grid interconnections)
5. Transparent independent estimates (Couch)
6. Blog syntheses — used only when flagged as such (Digital Applied is marked medium-low, drawn with hollow markers)

Untraceable figures that circulate widely (e.g. "Claude 3 Opus = 4.05 Wh/query") are **excluded
from all figures and from the dashboard**.

## Figure conventions

Figures use the `dataviz` skill's reference palette (light mode). Key hexes are defined at the top
of `make_figures.py`: surface `#fcfcfb`, ink `#0b0b0b`/`#52514e`, muted `#898781`, grid `#e1e0d9`,
series blue `#2a78d6`, orange `#eb6834`, aqua `#1baf7a`, yellow `#eda100`. Keep them.

- Log–log where the data spans orders of magnitude (it usually does).
- Lower-credibility sources get hollow markers or hatched bars, always with a caption note.
- Rotated inline labels beat legends where a line's identity is obvious.
- Panels using different methodologies must be captioned as not directly comparable.

## Writing conventions

Prose over bullets in `PROVENANCE.md`. Tables for anything comparative. Every number in the
running text traceable to `data/sourced_data.json` or an inline citation. Avoid the word
"comprehensive" about our own work — the whole point is that comprehensiveness is impossible here.

## Privacy (the repo is public)

`sources.json` and `data/usage_cache.json` are gitignored and must stay that way: the first names
machines and can carry label globs matching colleagues' paths, the second records every working
directory the user has ever been in. No tracked file may contain a real username, hostname or
absolute path — use `$USER`, `/scratch/$USER`, `<you>` in examples.

Deleted files survive in git history, so scan history and not just the working tree before
publishing anything derived from transcripts. Grep is not sufficient on its own: check figures and
any PDFs too, since neither is searchable as text.

## Gotchas that cost time

- Pandoc caption-ID syntax (`{#tbl:foo}`) renders **literally** in PDF output with this template.
  Don't use it; strip it if it reappears.
- `lmodern.sty` is missing on a bare Ubuntu texlive install → `apt-get install -y lmodern`.
- Python scripts use relative paths (`data/`, `figures/`) — **run them from the project root**.
- Matplotlib must use the `Agg` backend (already set in both scripts).
- Figure cross-references in the text are manual. If you add or reorder a figure, grep for
  "Figure N" and fix by hand.
- The app's auto-quit must not be reimplemented on `sendBeacon`/`pagehide` or a polling heartbeat.
  Both are best-effort, and background tabs are timer-throttled, so the fallback timeout has to be
  minutes — a missed beacon then looks identical to a broken feature. Liveness is a held-open
  connection the server watches; presence is the whole signal.
- `qlmanage` is the only SVG rasteriser macOS ships and it flattens onto opaque white. `make_app.py`
  renders over white and over black and solves for the discarded alpha. Icons downscale with `BOX`;
  `LANCZOS` rings and halos at 16 px.
- Icons are judged at 16 px, not in the preview. Designs that read at 48 px and dissolve at 16 have
  been rejected twice now — render a contact sheet at true size on both light and dark and look.
- In zsh, never name a loop variable `path` — it is tied to `$PATH` and assigning it breaks every
  subsequent command in the script.
