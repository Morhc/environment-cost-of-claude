---
title: "What Does Your Opus Session Cost? Water and Carbon for a Heavy Research Use-Case"
subtitle: "A companion brief to *The Environmental Footprint of Claude* — derived estimates, stated assumptions, honest error bars"
author: "Prepared for Josh Issa"
date: "August 11, 2026"
geometry: margin=2.6cm
fontsize: 11pt
mainfont: "DejaVu Sans"
linkcolor: "blue"
urlcolor: "blue"
numbersections: true
header-includes:
  - \usepackage{float}
  - \floatplacement{figure}{H}
  - \usepackage{caption}
  - \captionsetup{font=small,labelfont=bf}
---

\setcounter{section}{-1}

# The bottom line

For the impatient reader: one heavy Opus research session as defined below (20–30 prompts accruing 80% of a 1M-token window) costs, under the central estimate with its parameter-sweep uncertainty:

| | Per session |
|:---|:---|
| **CO~2~** | **330 ± 40 g CO~2~e** (US-average grid) |
| **Water** | **3,100 ± 380 mL** total (of which **170 ± 20 mL** is on-site cooling water) |
| *underlying energy* | *0.94 ± 0.11 kWh* |

**Read the ± narrowly.** It spans only the swept scenario parameters (prompt count 20–30, measured output share 19–24%) at the central rate-set with caching on. It is *not* a total uncertainty. Three larger shifts sit outside it: the grid serving the request, together with the accounting convention applied to it, moves CO~2~ across a band of roughly **103–607 g** — a factor of 5.9, from upstate New York on annual averages or ERCOT on long-run marginal rates at the low end, to AVERT's national short-run rate at the high end (Section 4); defeating prompt caching raises everything ~4.2×, to roughly 1.5 kg CO~2~e and 14 L; and the optimistic alternative rate-set sits ~15× below the central values. Section 4 audits which direction each remaining assumption is likely to be wrong in.

Everything here is derived rather than measured — with one exception, new in this revision. The output share was previously an unmeasured assumption centred at 50%; it is now measured at **19–24%** from 56 real sessions belonging to one heavy user (Section 5). That single correction lowers the headline by a factor of 1.4, and it is the largest single error this brief has carried.

## In relation to what?

A number without a denominator is an invitation to misread it, so here is the central estimate against everyday personal quantities (US reference values):

| One session equals… | CO~2~: 330 g | Water: 3.1 L (170 mL on-site) |
|:---|:---|:---|
| …of your daily life | **~3.3%** of an average household's *electricity* emissions for one day (~29 kWh → ~10 kg CO~2~e); **~0.9%** of the average American's *total* daily carbon footprint (~38 kg) | **~1.0%** of one person's daily indoor water use (~310 L); about **half of one toilet flush** (6 L) |
| …in a familiar unit | driving an average US gasoline car **~0.8 miles / 1.3 km** (EPA: 400 g/mile) | **~6 standard 500 mL bottles** at the full (power-plant-inclusive) boundary; **about a third of a bottle** counting only data-center cooling |

Read across the row that matches the question being asked. If the question is "should *I* feel bad about this session?", the honest answer from these denominators is that it is a rounding error on a day's personal footprint — you emit the session's CO~2~ roughly every 12 minutes just by being an average American, and flush more water before breakfast. If the question is "does this scale?", invert it: a researcher who runs one such session every working day accrues ~85 kg CO~2~e and ~810 L per year, and a 10,000-person user base doing the same reaches ~0.85 ktCO~2~e/yr — at which point the grid factors and disclosure gaps of the main report, not personal restraint, are the operative variables. Both readings are correct; they answer different questions. (Reference values: EIA household electricity ~10,800 kWh/yr; Global Carbon Budget US per-capita ~14 t/yr; EPA fleet-average 400 g/mile; EPA WaterSense ~82 gal/person/day indoor; US federal standard 1.6 gal/flush. The caching-off case scales every "session" entry ~4.2×.)

# Purpose and honest framing

This brief answers a practical question for researchers: *if I use an Opus-class Claude model the way researchers actually do — long conversations, big contexts, papers pasted in — how much electricity, water, and CO~2~ does that represent?* It is a companion to the full report, which established the evidence base; this document applies that base to one concrete scenario.

One framing rule matters more than any number below. **Anthropic has published no measured energy, water, or carbon figures, so every *rate* here is a third-party estimate.** Unlike the main report's figures — which plot only published values — this brief exists precisely to do the arithmetic a researcher can't avoid doing. Two of the scenario's inputs are, however, now measured directly from local session transcripts (Section 5): the prompt-cache hit rate and the output share. Those measurements constrain how the published rates are applied; they do not make the underlying rates any less estimated. Every assumption is stated, every rate is sourced, and the result is presented as a range whose width is honest: about **two orders of magnitude between the most optimistic and most pessimistic defensible readings**, with a central estimate we consider most plausible. If a reader takes away one number, it should be the central estimate; if they take away two, the second should be the width of the range.

# The scenario

The use-case, per the project brief: a researcher working through a substantial problem sends **20–30 prompts** in one conversation and accrues **80% of a 1-million-token context window (800,000 tokens)** with an Opus-class model. Naively, each prompt contributes an equal share of the window. We take N = 25 prompts as the central case, so each turn adds ~32,000 tokens (a chunk of a paper, a long reply, a data excerpt) and the model's context grows linearly from 32k to 800k tokens over the session.

Two mechanical facts drive everything. First, in an accumulating conversation the model re-reads the entire history on every turn, so the *processed* token count is far larger than the window: with equal steps, total history re-read is 800k × (N−1)/2 ≈ **9.6 million tokens** for N = 25, on top of the 800k of new content. Second, whether those re-read tokens are cheap or expensive depends on **prompt caching**: Anthropic's serving stack caches conversation prefixes, and the one published Claude rate-set that distinguishes these prices caching at roughly one-tenth the energy of fresh input. Caching state is therefore the single largest lever in the result. It used to be an unverifiable assumption; it is now measured at a 98.3% hit rate (Section 5), so the caching-on case is the real one and the caching-off column below is a bound that ordinary use does not approach.

Because the model must be one for which published rates exist, the calculation uses **Opus 4.5-generation rates** (and an Opus 4.7 alternative). Under the strict rule of the main report there is no published basis for the Fable/Claude 5 generation; a reader using newer models should treat these numbers as the best available proxy, biased in an unknown direction, though the industry's measured trend (33× per-prompt energy reduction in one year at Google; ~40% per-token annual software gains in ML.ENERGY data) suggests newer serving stacks are more efficient per token, while newer models may think longer.

## Rates and assumptions

Table: Inputs. Rates are published third-party estimates; scenario parameters are this brief's assumptions.

| Quantity | Value | Source / status |
|:---|:---|:---|
| Fresh input energy | 390 Wh / M tokens | Couch (Jan 2026), Opus 4.5 via price-ratio scaling of Epoch's GPT-4o anchor |
| Output energy | 1,950 Wh / M tokens | same |
| Cached-read energy | 39 Wh / M tokens | same |
| Alternative per-request rates | 0.78 Wh (short chat) → 14.1 Wh (800k context) | Digital Applied (Apr 2026), Opus 4.7, ±3× self-declared |
| On-site water | 0.18 L / kWh | AWS multiplier used by Jegham et al. v6 |
| Off-site (power-plant) water | 3.142 L / kWh | same |
| Grid carbon intensity | 110–413 gCO~2~/kWh | EPA eGRID 2023: NYUP, ERCT (333), US avg (348), RFCW |
| Prompts per session (N) | 20–30, central 25 | scenario assumption |
| Window accrued | 800k tokens (80% of 1M) | scenario assumption |
| Output share of window (f) | 0.19–0.24, central 0.20 | **measured** — 56 real sessions, one heavy user (Section 5) |
| Caching | on | **measured** — 98.3% hit rate over 16,240 messages (Section 5) |

The output-share parameter used to carry a warning here that no one had measured the input/output mix of research conversations, so this brief swept 20–80% and centred at 50%. That is no longer true: it is measured at 19–24% (Section 5), and since output tokens cost ~5× fresh input per token, the correction matters — the previous central case was a factor of 1.4 too high. The two figures bracket a genuine ambiguity in attribution rather than sampling noise: an assistant turn's output is written back into the cache as history on the following turn, so the counters cannot cleanly separate "output" from "new input" at the boundary. A user whose work is more output-heavy — drafting rather than reading — would sit above this band.

# Results

![Session totals. Panel (a): the full defensible energy range spans ~50 Wh to ~5.1 kWh; the central estimate is ~0.94 kWh. Panels (b) and (c) apply grid factors and water factors to the central rate-set. The output share driving these is measured, not assumed (Section 5); every other input is derived.](figures/fig_s1_session.png)

Table: Session totals (central case: N = 25, f = 0.20, caching on; ranges span N = 20–30 and the measured f = 0.19–0.24). Derived from published rates and a measured output share.

| Metric | Central | Range (caching on) | Caching off | Optimistic alt. (Opus 4.7 interp.) |
|:---|---:|---:|---:|---:|
| Energy / session | **0.94 kWh** | 0.85–1.06 kWh | 3.5–5.1 kWh | 0.05–0.69 kWh (central 0.19) |
| Energy / prompt | 37 Wh | 28–53 Wh | 176–257 Wh | 3–23 Wh |
| CO~2~e / session, US-avg grid | **326 g** | 294–370 g | 1.2–1.8 kg | 18–240 g |
| CO~2~e / session, Indiana PJM | 387 g | 349–439 g | 1.5–2.1 kg | 21–285 g |
| CO~2~e / session, upstate NY | 103 g | 93–117 g | 0.4–0.6 kg | 6–76 g |
| Water / session, on-site only | **0.17 L** | 0.15–0.19 L | 0.6–0.9 L | 0.01–0.12 L |
| Water / session, incl. off-site | **3.11 L** | 2.81–3.53 L | 11.7–17.1 L | 0.2–2.3 L |
| Water / prompt, incl. off-site | 124 mL | 94–177 mL | 0.5–0.7 L | 9–76 mL |

## What these numbers mean

**Energy.** The central estimate — **~0.94 kWh for the whole session** — is about a dishwasher cycle, ~3% of an average US household's daily electricity, or the energy to drive a typical EV about 5.5 km. It is also roughly **3,900 median Gemini prompts**: a vivid illustration of the main report's point that heavy long-context use, not the median chat, is where individual footprints live. Per prompt, the central ~37 Wh is ~45× the Jegham short-prompt figure for Claude 3.7 Sonnet and ~156× Google's measured median — driven almost entirely by the accumulated context, not by anything exotic about the questions asked.

**Carbon.** At the US-average grid factor the central session is **~0.33 kg CO~2~e — about 0.8 miles of driving in an average US gasoline car**. Where the request is actually served changes this by ~3.8× on annual-average accounting: ~0.10 kg on upstate New York's hydro-heavy grid versus ~0.39 kg on the Indiana PJM grid hosting Anthropic's largest campus — and which grid serves *your* request is not disclosed or controllable. That siting spread narrows to ~1.3–1.5× if the same sites are costed at marginal rates — short-run or long-run, the compression holds either way (Section 4) — so siting is a much weaker lever than the average-basis figures suggest, and on a 20-year view upstate New York is no longer the cleanest of the three. Annualized, a researcher running one such session every working day at the central estimate emits **~85 kg CO~2~e/yr** (US-avg grid) — well under a tenth of one transatlantic round-trip flight per economy seat, or roughly one tank of gasoline burned. Training amortization, embodied hardware, and idle capacity are *not* included; no published basis exists for adding them for Claude.

**Water.** The central session evaporates **~0.17 L on-site** (a small glass) and **~3.1 L including power-plant water** (about six 500 mL bottles). The viral-era claim of "a bottle of water per prompt" is, for this deliberately heavy scenario, roughly right *per four prompts* at the total boundary — and roughly 74× too high at the on-site boundary that corporate figures use. Both statements are true; they use different boundaries, which is the entire water-numbers controversy in miniature.

**The spread is the finding.** The optimistic reading (Opus 4.7 blog rates, interpolated) puts the session under 0.2 kWh; the pessimistic one (no caching, output-heavy, 30 prompts) approaches 5.1 kWh. That ~27× spread between defensible constructions — before grid choice and accounting convention move carbon by another ~2.3× (Section 4) — is the direct, practical cost of Anthropic's non-disclosure documented in the main report.

# Which way are we wrong?

Presenting a central estimate obliges us to say which direction it is likely to be off in. Two things need separating: a *grid-accounting* choice we made that has a defensible alternative in each direction, and a set of *boundary exclusions* that are almost all one-directional.

## Marginal vs. average grid intensity

The table above converts electricity to CO~2~ using eGRID **annual average** factors — the emissions intensity of everything on that grid over a year. But adding a data center's load does not draw down "the average"; grid operators dispatch generators in merit order, and the unit that actually responds to incremental demand is usually gas or coal, not the must-run nuclear and renewables that pull the average down. The technically correct factor for an *incremental* load is a marginal one, and there are two of those, pointing opposite ways.

**Short-run marginal** (SRMER) asks which existing plant ramps up tonight, and is consistently *higher* than the average. PJM's own published rates put its 2022 marginal at 976 lb/MWh off-peak and 1,041 on-peak against an 811 lb/MWh system average; weighting those by the hours a flat 24/7 load actually occupies (on-peak is 80 of 168 hours per week) gives 1,007 lb/MWh, or **1.24×** the system average. EPA's AVERT, run for data year 2023, puts the national flat-profile ("uniform EE") marginal rate at 1,429 lb/MWh against eGRID 2023's 767 lb/MWh US average — **1.86×**, the largest ratio in this literature. Holland et al. (PNAS 2022) find **1.51×** nationally — and, pointedly, that while average US emissions fell 28% over 2010–2019, *marginal* emissions rose 7%.

**Long-run marginal** (LRMER) asks what gets *built* because sustained new demand exists, and runs *lower* than the average across most of the US: Gagnon & Cole (PNAS 2022) argue short-run rates "neglect the impacts of any structural change," and for US vehicle electrification found LRMERs of 286–336 gCO~2~/kWh against short-run rates of 591–631 — a factor-of-two disagreement in the opposite direction, because new load in most US markets induces disproportionately renewable build.

**Which of the two applies here is not a matter of taste.** NREL advises applying an LRMER to any intervention persisting five years or longer, and EPA's AVERT documentation states the opposite bound — that its short-run rates "should not be used to examine the emission impacts of changes that extend more than 5 years into the future." A data-center campus is a multi-decade asset; Anthropic's Hawesville lease alone runs 20 years. On the literature's own guidance, **the long-run rate is the horizon-appropriate one for the siting question**, and the short-run rate answers a narrower question: what happens on the grid tonight while this session runs.

Both are available region-matched. NREL's Cambium 2023 dataset publishes LRMERs by region, levelized on the workbook's published defaults — 2025 start, **20-year evaluation period**, 3% real discount, mid-case scenario, in kg CO~2~/MWh at the point of end-use. Setting the three conventions side by side for the grids that actually host Anthropic's compute:

Table: The same three sites under three accounting conventions, each region-matched. Sources: EPA eGRID 2023; EPA AVERT 2023 ("uniform EE"); NREL Cambium 2023 (20-year levelized, mid-case).

| Site | eGRID annual average | AVERT short-run marginal | Cambium long-run marginal |
|:---|---:|---:|---:|
| New Carlisle, IN | 413 (RFCW) | 618 (Mid-Atlantic) | **166** (PJM_West) |
| Barber Lake / Abernathy, TX | 333 (ERCT) | 587 (Texas) | **114** (ERCOT) |
| Lake Mariner, NY | 110 (NYUP) | 475 (New York) | **124** (NYISO) |
| *spread across the three* | *3.75×* | *1.30×* | *1.46×* |

Two things follow, and the first is robust precisely because the two marginal conventions are biased in *opposite* directions on level. **The siting spread compresses under both.** A factor of 3.75 on annual averages becomes 1.3× short-run and 1.5× long-run. Whatever else is uncertain, the attributional picture overstates how much emissions clean-grid siting actually avoids for incremental load — and it overstates it under the pessimistic marginal convention and the optimistic one alike.

Second, and more surprising: **the ranking inverts.** On annual averages upstate New York is the cleanest site by a factor of three. On a 20-year long-run marginal basis it is no longer the cleanest — Texas is, at 114 gCO~2~/kWh, and New York's 124 sits closer to Indiana's 166 than to its own 110 annual average. The mechanism is visible in the ratios: adding sustained load in ERCOT or PJM_West induces build that is *much* cleaner than what those grids run today (LRMER is 0.34× and 0.40× of their averages respectively), whereas in New York the induced build is no cleaner than the hydro and nuclear already there (LRMER is 1.13× the average). A clean grid is not the same thing as a grid with clean headroom, and for incremental load it is the headroom that matters.

Cautions, all pushing toward reading the cross-convention ratios as indicative rather than exact. Neither AVERT's regions nor Cambium's GEA regions are coextensive with eGRID's subregions, so every marginal-versus-average ratio crosses a geographic boundary; the New York case is worst, because both marginal datasets span all of NYISO including gas-heavy downstate while eGRID's NYUP is upstate only. (The comparison *across* the three sites within a single convention — the spreads in the last row — does not suffer this, since each column is internally consistent.) Indiana is split 21% Mid-Atlantic / 79% Midwest in EPA's apportionment, and New Carlisle is assigned to the PJM side because its utility, Indiana Michigan Power, is a PJM member. AVERT's rates are T&D-adjusted and Cambium's are quoted at end-use, so both include distribution losses and run modestly high for a transmission-connected campus. Cambium's values are scenario-dependent — mid-case here, out of eight. And AVERT's rates assume a **0.5% displacement of regional demand**, which a multi-gigawatt campus badly violates; that is the single largest stretch in this section.

Two further caveats belong to the sources themselves. EPA states that AVERT "is a marginal emissions assessment tool and not a tool for emissions accounting," and cautions against its use in corporate greenhouse-gas reporting — consistent with the use here, as a sensitivity on an attributional headline rather than a replacement for it. And AVERT's Mid-Atlantic short-run rate (618 gCO~2~/kWh) and PJM's own flat-weighted 2022 short-run rate (457) differ by a third for substantially the same footprint, on different methods and data years. That disagreement is not resolved here; it is carried through the table below as a genuine error bar, because two authoritative sources disagreeing by a third *is* the state of public knowledge.

Table: The central session (0.94 kWh) costed under each grid-accounting convention. Derived; conventions answer different questions and are not interchangeable. Rows matched to a grid that actually hosts Anthropic compute are marked †.

| Convention | Factor (gCO~2~/kWh) | Session CO~2~ | Source |
|:---|---:|---:|:---|
| eGRID average, upstate NY † | 110 | **103 g** | EPA eGRID 2023 |
| Long-run marginal, ERCOT † | 114 | 107 g | NREL Cambium 2023, 20-yr levelized |
| Long-run marginal, NYISO † | 124 | 116 g | NREL Cambium 2023 |
| Long-run marginal, PJM_West † | 166 | 156 g | NREL Cambium 2023 |
| Long-run marginal, US EV study | 286–336 | 268–314 g | Gagnon & Cole, PNAS 2022 (direction, not a data-center factor) |
| eGRID average, ERCOT † | 333 | 312 g | EPA eGRID 2023 |
| eGRID average, US | 348 | 326 g | EPA eGRID 2023 (this brief's headline) |
| eGRID average, Indiana PJM (RFCW) † | 413 | 387 g | EPA eGRID 2023 |
| Short-run marginal, PJM published (2022) † | 457 | 427 g | PJM 2018–2022 Emission Rates report, flat-weighted |
| Short-run marginal, AVERT New York (2023) † | 475 | 445 g | EPA AVERT |
| Short-run marginal, AVERT Texas (2023) † | 587 | 549 g | EPA AVERT |
| Short-run marginal, AVERT Mid-Atlantic (2023) † | 618 | 579 g | EPA AVERT |
| Short-run marginal, US national | 648 | **607 g** | EPA AVERT 2023 |

So the defensible band for the same session is roughly **103–607 g CO~2~e — a factor of 5.9**, on top of everything else, and far wider than the ±11% printed in Section 0. That width is not sloppiness; it is three legitimate accounting conventions answering three different questions about the same kilowatt-hours. If the question is "what is this session's share of the grid it ran on," use the eGRID rows. If it is "what did the grid burn tonight because of it," use the short-run rows. If it is "what will be built because demand like this persists" — the right question for a 20-year campus — use the long-run rows, which are the lowest in the table. Our headline sits in the middle of the band and is the attributional convention, which we think is the right default for a single user's session: LRMER's optimism rests on new load inducing clean build, and for AI data centers specifically the documented 2025–26 responses have included coal-retirement deferrals, multi-year gas-turbine backlogs, and on-site gas generation, which is not what that assumption describes. But a reader who wants the incremental-emissions number rather than the attributional one should use the short-run rows, and they are higher than what we printed. The same dispatch logic governs the off-site water: a marginal gas or coal unit evaporates cooling water, wind and solar do not, so the 2.94 L off-site figure inherits this uncertainty too — we found no published marginal water-intensity factors to quantify it.

## Direction of the excluded terms

Table: Every term we left out or approximated, and which way it moves the answer.

| Term | Status | Direction | Magnitude if known |
|:---|:---|:---|:---|
| Idle capacity, host CPU/DRAM, PUE | likely outside the Couch/Epoch boundary | **↑ understates** | up to ~2.4× (Google: 0.10 → 0.24 Wh chip-only vs full boundary) |
| Training, amortized per prompt | excluded | **↑** | unknown for Claude; Google's historical ML split was ~60/40 inference/training |
| Embodied carbon (chips, buildings) | excluded | **↑** | only Mistral has quantified it for any frontier model |
| Chip-fabrication water | excluded | **↑** | ~2,200 gal ultra-pure water per chip (Ren) |
| Extended thinking / reasoning modes | excluded | **↑** if you use them | 3–4× on affected requests (Jegham) |
| Short-run marginal grid intensity | we used annual average | **↑** | 1.24–1.86× (1.5× at the AVERT region serving New Carlisle) |
| Price-as-energy-proxy in the Couch rates | assumption | **↓ overstates** if Opus pricing carries margin above marginal compute | unquantified |
| Model/serving vintage (Opus 4.5-era rates) | proxy for newer models | **↓** | industry trend is fast: 33× per-prompt in 12 months at Google; ~40%/yr per-token from software alone |
| Long-run marginal grid intensity | we used annual average | **↓** | 0.34–0.40× at the Indiana and Texas sites; 1.13× at the New York one (Cambium 2023) |
| Equal-prompt-size, caching behaviour, output share | simplifications | ambiguous | inside the printed ± |

We cannot sign the net error, and we are not going to pretend otherwise. What can be said cleanly is that the *boundary* exclusions are systematically one-directional — every physical thing we left out of the accounting adds emissions and water rather than removing them — while the terms that plausibly push down are about *method vintage and pricing assumptions* rather than about physical processes we ignored. A reader who wants a single defensible sentence: the central estimate is more likely to be too low than too high on boundary grounds, and the honest total uncertainty is roughly an order of magnitude, not the ±11% printed in Section 0.

# What real usage looks like

Every number above this section is derived from published rates applied to a hypothetical session. This section is different: it is the only *measured* content in either document, and it exists because two of the scenario's inputs turned out to be checkable after all.

Claude Code writes a local transcript for every session, and each assistant message carries the token counters the serving stack returned: fresh input, cache writes, cache reads, and output. Those are exactly the four categories the Couch rate-set prices separately. Aggregating them over **56 sessions and 16,240 assistant messages** belonging to one heavy user — a working researcher, across scientific-computing, data-analysis, and writing projects — gives the following. Only the counters were read; no message content was examined.

Table: Measured token and energy mix, 56 sessions, one heavy user. Token counts are measured; the energy column applies the Couch rates and is therefore derived.

| | Tokens | Share of tokens | Energy at Couch rates | Share of energy |
|:---|---:|---:|---:|---:|
| Fresh input (incl. cache writes) | 78.1 M | 1.7% | 30.4 kWh | 12.8% |
| Cached reads | 4,386.9 M | 97.8% | 171.1 kWh | **72.0%** |
| Output | 18.5 M | 0.4% | 36.0 kWh | 15.2% |
| **Total** | **4,483.5 M** | | **237.5 kWh** | |

Three findings, in descending order of consequence for this brief.

**Caching is not a lever, it is a constant.** The measured cache hit rate is **98.3%**. Section 2 treated caching as the single largest uncertainty and showed both an on and an off case; the off case is a bound that ordinary use does not approach. This is a property of the serving stack rather than of the workload, so it generalises better than anything else in this section.

**The output share is 19–24%, not 50%.** This brief previously swept 20–80% and centred on 50% because nobody had measured it. Measured, output is 19.1% of non-cached tokens, or 23.7% if cache-writes are attributed to new content instead. Since output tokens carry ~5× the per-token energy of fresh input, that correction alone lowers every headline figure by a factor of **1.4** — and it is the reason the numbers in this revision are lower than in the previous one.

**The distribution is violently heavy-tailed — mean/median = 48.** Median session 89 Wh; ninetieth percentile 18.0 kWh; largest single session 51.6 kWh. The main report argues from the literature that per-request energy distributions are heavy-tailed and that medians therefore mislead; this is that claim measured directly, at the session level, and the tail is heavier than the literature's per-request figures suggest. Note where the modelled scenario falls: the 0.94 kWh "heavy research session" of Section 3 is roughly **ten times the median real session but nearly twenty times below the ninetieth percentile.** The hypothetical this brief was built around is not an extreme case. It is a moderately busy one.

For scale, the 237.5 kWh total across these 56 sessions is **~83 kg CO~2~e** at the US-average grid factor — comparable to driving about 210 miles, accrued over months of daily professional use.

**What this does and does not license.** These are Claude Code sessions, and their "input" is dominated by tool results — files read, commands run, searches returned — rather than by material a person pasted in. That is a genuinely different workload from the paper-reading researcher the scenario models, even though both are input-heavy, and it is why the output share is presented as a range rather than a point. It is also one user: n = 1, no claim of representativeness, and it excludes Desktop and web usage entirely. What it grounds well is the *mechanism* — an accumulating context, re-read under near-total caching, with cached reads dominating the energy — which is the structural claim the whole brief rests on, and which the measurement confirms.

*Reproducible on any machine with Claude Code history: `measure_usage.py`.*

# How a researcher can actually reduce this

The scaling structure behind these numbers implies concrete, high-leverage habits, in descending order of effect. **Start new conversations rather than extending old ones** when the history no longer matters: the re-read history is the largest single line item — measured, cached reads are 72% of session energy despite costing a tenth as much per token (Section 5) — and a fresh thread resets it (this is also why the caching-off column is ~4.2× worse — if you use an interface or API pattern that defeats caching, the history dominates everything). **Trim what you paste**: attaching only the relevant sections of papers rather than full PDFs attacks the supra-linear prefill term documented in the main report (~0.3 Wh at short context versus ~40 Wh modeled at 100k input tokens). **Prefer concise outputs** where possible: output tokens carry ~5× the per-token cost of fresh input under these rates, so asking for a targeted answer rather than an exhaustive rewrite matters more than shortening your question. **Match the model to the task**: routing summarization or extraction to a smaller model and reserving Opus-class reasoning for the hard steps tracks the 10–30× per-token spread between model classes in the measured open-model literature. And for perspective, keep the denominator honest in both directions: one heavy session is a dishwasher cycle, not a catastrophe — but a lab of twenty researchers doing this daily is ~4.9 MWh/yr, the scale at which grid siting, disclosure, and procurement (the main report's Sections 3 and 8) become the real environmental questions.

# Caveats register

Everything above is **derived, not measured**. The Couch rates rest on an untested assumption (API price tracks marginal compute energy) anchored to a GPT-4o estimate on assumed NVIDIA hardware, while Claude actually serves substantially on Trainium and TPUs with unpublished power characteristics. The caching-on column is now measured rather than assumed (98.3% hit rate, Section 5); the equal-prompt-size assumption is the user's stated simplification (front-loaded contexts — pasting everything in turn one — would shift cost from history re-reads toward a single large prefill and lower totals modestly under cached rates); the output share is measured but from a different workload than the one modelled (Section 5); extended-thinking modes are *excluded* (Jegham's measurements suggest 3–4× multipliers on affected requests); and no training, embodied-hardware, idle-capacity, or chip-fabrication water is included anywhere. The grid factors are 2023 annual averages, not marginal or hourly intensities — Section 4 quantifies that choice rather than merely flagging it. Where these caveats resolve — if Anthropic publishes measured per-token distributions, fleet PUE/WUE, and site attribution — this entire brief reduces to one row of a disclosed table. Until then, cite these numbers with their ranges attached.

# Sources

Rates and factors: Couch, *Electricity use of AI coding agents* (simonpcouch.com, Jan 2026) · Digital Applied, *AI Model Sustainability Report 2026* (Apr 2026) · Jegham et al., arXiv:2505.09598 v6 (AWS PUE/WUE/CIF multipliers) · EPA eGRID 2023 Rev 2 · Google, arXiv:2508.15734 (Gemini median, efficiency trend) · Epoch AI gradient update (context scaling) · ML.ENERGY leaderboard & longitudinal data (model-class spreads, caching-era software gains). Marginal-emissions sensitivity (Section 4): PJM, *2018–2022 CO~2~, SO~2~ and NO~X~ Emission Rates* (Apr 2023), Table 2, values read from the report directly — this remains the most recent edition, as PJM discontinued the annual PDF thereafter in favour of Data Miner and its interactive Emissions page · EPA, *Emission Rates from AVERT* (Apr 2024 release, data year 2023), national and regional "uniform EE" avoided CO~2~ rates, extracted by `extract_avert.py` · NREL, *Long-Run Marginal Emission Rates for Electricity — Workbooks for 2023 Cambium Data* (Feb 2024), GEA-region LRMERs on the workbook's published levelization (2025 start, 20-year period, 3% real discount, mid-case), extracted by `extract_cambium.py` · Holland, Kotchen et al., "Why marginal CO~2~ emissions are not decreasing for US electricity," *PNAS* 2022 · Gagnon & Cole, "Short-run marginal emission rates omit important impacts of electric-sector interventions," *PNAS* 2022 · Siler-Evans, Azevedo & Morgan, *Environ. Sci. Technol.* 2012. Everyday reference values (Section 0): EIA, average US residential electricity consumption (~10,800 kWh/household/yr) · Global Carbon Project / Our World in Data, US per-capita CO~2~ (~14 t/yr) · EPA, average passenger-vehicle emissions (400 g CO~2~/mile) · EPA WaterSense, indoor water use (~82 gal/person/day) · US Energy Policy Act 1992 toilet standard (1.6 gal/flush). Full source list and credibility assessments: *The Environmental Footprint of Claude* (companion report, Appendix B), and `sourced_data.json` for machine-readable values. Scenario arithmetic: `scenario_calc.py`. Measured usage (Section 5): `measure_usage.py`, run against local Claude Code transcripts. Both reproducible.
