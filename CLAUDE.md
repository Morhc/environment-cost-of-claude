# Project conventions — Claude environmental impact analysis

Read this before touching anything. These rules were set by the user and are load-bearing.

## The strictness rule (non-negotiable)

**Only published, sourced values appear in the main report's tables and figures.** No fillers, no
placeholder numbers, no plausible-sounding extrapolations. Where no published estimate exists —
notably the Claude Fable 5 / Claude 5 generation — the gap is *displayed as a finding*
("No published data"), not papered over.

There are exactly two deliberate exceptions, both quarantined and both labeled:

1. The companion brief (`researcher_brief.md`) exists to do scenario arithmetic the reader can't
   avoid. Everything there is explicitly labeled **derived**, every input rate is sourced, and
   Section 4 audits the direction of every excluded term.
2. **Appendix C of the main report** (bottom-up training bounds, added 2026-08-11 at the user's
   explicit direction after being offered the alternatives). It is confined to the appendix and
   must stay out of the body, the tables, and Figure 2 — the training panel stays empty. Every
   number carries a "derived, not published" marker, the width is presented as the finding, and
   the direction of each excluded term is signed. Reproducible via `training_bounds.py`.

If a third exception is ever proposed, it needs the same treatment: quarantined location, labeled
values, signed error directions, and a script that regenerates it.

**Measured data is not an exception** — it outranks everything. Section 5 of the brief reports token
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

- Section 0 of the brief says the ± is a *parameter sweep only*, not total uncertainty.
- Section 4 presents marginal-vs-average grid accounting as **two-sided** (short-run marginal runs
  1.24–1.86× *above* the average; long-run marginal runs 0.34–0.40× *below* it at the Indiana and
  Texas sites, and 1.13× above at the New York one), not as a one-sided "we're conservative" claim.
- Every excluded term carries an explicit ↑/↓ direction.

## Source hierarchy

1. Primary corporate disclosures and regulatory filings
2. Peer-reviewed measurements
3. Credible preprints with published methodology (Epoch AI, ML.ENERGY, Microsoft/Oviedo)
4. Trade press for verifiable facts only (capacity, leases, grid interconnections)
5. Transparent independent estimates (Couch)
6. Blog syntheses — used only when flagged as such (Digital Applied is marked medium-low, drawn
   with hollow markers in Figure 4)

Untraceable figures that circulate widely (e.g. "Claude 3 Opus = 4.05 Wh/query") are documented in
the claims audit and **excluded from all figures**. See the master table in Appendix A.

## Figure conventions

Figures use the `dataviz` skill's reference palette (light mode). Key hexes are defined at the top
of `make_figures.py`: surface `#fcfcfb`, ink `#0b0b0b`/`#52514e`, muted `#898781`, grid `#e1e0d9`,
series blue `#2a78d6`, orange `#eb6834`, aqua `#1baf7a`, yellow `#eda100`. Keep them.

- Log–log where the data spans orders of magnitude (it usually does).
- Lower-credibility sources get hollow markers or hatched bars, always with a caption note.
- Rotated inline labels beat legends where a line's identity is obvious.
- Panels using different methodologies must be captioned as not directly comparable.

## Writing conventions

Prose over bullets in the reports themselves. Tables for anything comparative. Every number in the
running text traceable to `data/sourced_data.json` or an inline citation. Avoid the word
"comprehensive" about our own work — the whole point is that comprehensiveness is impossible here.

## Gotchas that cost time

- Pandoc caption-ID syntax (`{#tbl:foo}`) renders **literally** in PDF output with this template.
  Don't use it; strip it if it reappears.
- `lmodern.sty` is missing on a bare Ubuntu texlive install → `apt-get install -y lmodern`.
- Python scripts use relative paths (`data/`, `figures/`) — **run them from the project root**.
- Matplotlib must use the `Agg` backend (already set in both scripts).
- Figure cross-references in the text are manual. If you add or reorder a figure, grep for
  "Figure N" and fix by hand.
