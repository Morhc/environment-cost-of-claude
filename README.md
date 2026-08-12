# Environmental footprint of Claude — analysis, figures, and reports

Two documents and everything needed to rebuild them:

- **`claude-environmental-impact-report.pdf`** (23 pp) — source-critical analysis of what can be
  quantified about Claude's environmental footprint from Anthropic's disclosures, the academic
  literature, and third-party estimates.
- **`opus-researcher-footprint-brief.pdf`** (11 pp) — companion brief costing one heavy Opus
  research session in CO₂ and water, with a signed audit of every excluded term.

Start with `HANDOFF.md` for project state and open threads, and `CLAUDE.md` for the working rules.

## Rebuild

```bash
make            # both PDFs
make report     # main report only
make brief      # companion brief only
make figures    # regenerate all PNGs from sourced_data.json
make clean      # remove generated PDFs (figures are kept)
```

Scripts use paths relative to the project root — **run everything from here**, not from `figures/`.

## Dependencies

**Python** (3.9+): `matplotlib` for the figures. `extract_avert.py` additionally needs `openpyxl`,
but only if you want to re-derive the EPA AVERT marginal-emissions rates — the extracted values are
already in `data/sourced_data.json`, so nothing in `make` depends on it.

```bash
pip install matplotlib
python3 -m venv .venv && .venv/bin/pip install openpyxl   # only for extract_avert.py
```

**PDF toolchain**: pandoc with a XeLaTeX engine.

```bash
# Debian / Ubuntu
sudo apt-get install -y pandoc texlive-xetex texlive-latex-recommended \
                        texlive-fonts-recommended lmodern

# macOS (Homebrew)
brew install pandoc
brew install --cask mactex-no-gui     # or basictex + `sudo tlmgr install lmodern`
```

`lmodern` is the one that bites — pandoc's default template requires it and a minimal texlive
install omits it. The documents set DejaVu Sans as the main font; substitute in the YAML front
matter if you don't have it.

## Layout

```
├── report.md                    # main report source
├── researcher_brief.md          # companion brief source
├── data/sourced_data.json       # every plotted value + its source and credibility flag
├── data/avert_emission_rates_2023.xlsx   # EPA primary source, archived (sources move)
├── make_figures.py              # figures 1–5 (main report)
├── make_scenario_figure.py      # session figure (brief)
├── scenario_calc.py             # session arithmetic; prints all permutations
├── extract_avert.py             # re-derives AVERT marginal rates from the EPA workbook
├── training_bounds.py           # derived training-energy bounds behind Appendix C
├── extract_cambium.py           # re-derives NREL Cambium long-run marginal rates
├── measure_usage.py             # your own Claude Code usage -> tokens, energy, CO2, water
├── figures/*.png                # generated
├── CLAUDE.md                    # project conventions
└── HANDOFF.md                   # state, decisions, open threads
```

## Changing the scenario

`scenario_calc.py` is the fastest way to re-cost the researcher session under different assumptions
— prompt count, output share, caching on/off, grid factor. Edit the constants at the top and run:

```bash
python3 scenario_calc.py
```

It prints every permutation plus carbon and water at four grid intensities. If you change the
central case, update the numbers in `researcher_brief.md` Sections 0, 3, and 4 (they are written
inline, not templated) and re-run `make brief`.

## Costing your own usage

`measure_usage.py` reads the token counters Claude Code writes to `~/.claude/projects/*/*.jsonl`
and carries them through to CO2 and water. It opens only the usage counters, never message
content, and nothing leaves the machine.

```bash
python3 measure_usage.py                  # everything, US-average grid
python3 measure_usage.py --days 30        # last 30 days
python3 measure_usage.py --grid Cambium_PJM_West   # a specific accounting convention
python3 measure_usage.py --list-grids     # all 15 conventions, cheapest first
```

The token counts are measured. Everything downstream — energy, CO2, water — is derived from
third-party rates carrying 2–4× method uncertainty, and the spread across accounting conventions
alone is ~7×. The tool prints all of them rather than one number, for the reasons in Section 4 of
the brief.

**It sees one machine.** Claude Code keeps transcripts per-machine with no central ledger, so a
full personal total means running it everywhere and adding up:

```bash
python3 measure_usage.py --json > usage-$(hostname -s).json     # on each machine
jq -s '{kwh: (map(.kwh)|add)}' usage-*.json                     # then together
```

Four things stay uncounted even then: Claude Code on remote hosts (transcripts live on the host you
ran it on), cloud sessions (server-side, never written to local disk), Claude Desktop, and
claude.ai. There is no way to recover those from the filesystem.

## A note on the numbers

Anthropic publishes no environmental data, so nothing here about Claude is measured — it is all
third-party estimation with method-level uncertainty of roughly 2–4× per point, and up to an order
of magnitude in total for the session scenario. Both documents are written to make that explicit
rather than to hide it. Please preserve that when editing; see the honesty rule in `CLAUDE.md`.
