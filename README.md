# Environment Cost of Claude

What can actually be quantified about the environmental footprint of using Anthropic's Claude
models, from published sources — plus a tool that measures your own usage and costs it in CO₂ and
water.

## Measure your own usage first

Claude Code writes a transcript for every session, and each assistant message carries the token
counters the serving stack returned. That is real measurement, not an estimate. This repo turns it
into energy, CO₂ and water:

```bash
python3 measure_usage.py                    # this machine
./collect_usage.sh trillium other-host      # every machine you use, merged
```

**One machine is almost always an undercount.** There is no central ledger — transcripts live on
whichever machine ran them, and for this author a laptop-only run missed 62% of the total, which was
sitting on an HPC login node. `collect_usage.sh` pipes the same script over SSH to hosts you name
(they need only `python3`), discovers transcript roots scoped to `$USER`, and merges the results.
Only token counts come back; no message content is ever read, and nothing leaves your machines.

```bash
python3 measure_usage.py --list-grids       # 15 accounting conventions, cheapest first
python3 measure_usage.py --grid Cambium_PJM_West --days 30
python3 measure_usage.py --by hour --tz America/Vancouver
python3 measure_usage.py --plot usage.png --event 2026-07-24='Plan limit raised'
```

Full options and caveats in [Costing your own usage](#costing-your-own-usage) below. The headline
number depends enormously on which accounting convention you pick — across the fifteen the tool
carries, the same electricity spans a factor of seven — which is the point of the report.

## The documents

- **`claude-environmental-impact-report.pdf`** (28 pp) — source-critical analysis of what can be
  quantified about Claude's environmental footprint from Anthropic's disclosures, the academic
  literature, and third-party estimates. Appendix C carries bottom-up training bounds.
- **`opus-researcher-footprint-brief.pdf`** (16 pp) — companion brief costing one heavy Opus
  research session in CO₂ and water, with a signed audit of every excluded term. Section 5 reports
  one user's measured usage, the only measured content in either document.

The central finding is an absence: **Anthropic has published no first-party environmental data of
any kind.** Every Claude-specific number in both documents is therefore third-party, and the
credibility of each is assessed individually.

Start with `HANDOFF.md` for project state and open threads, and `CLAUDE.md` for the working rules.

## License

Software is MIT. The written work, figures and data are CC BY 4.0. Use any of it for any purpose,
with attribution. See `LICENSE`.

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
├── collect_usage.sh             # merges usage across machines (local + ssh hosts)
├── figures/*.png                # generated (fig_s2_usage_alltime.png needs the author's
│                                #   own transcripts — `make` cannot rebuild it)
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
<a id="costing-your-own-usage"></a>

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

**One run sees one machine, and that is usually a large undercount.** Claude Code keeps
transcripts per-machine with no central ledger. For this author, a laptop-only run missed 62% of
the total, which lived on an HPC login node. Use the collector:

```bash
./collect_usage.sh                    # this machine only
./collect_usage.sh trillium           # this machine + a remote host
./collect_usage.sh trillium other-box # ...and more
```

Remote hosts need nothing but `python3` — the script is piped over stdin and run with `--raw`,
which applies no rates and reads no data files. Only token counts come back, never message
content. Remote roots are auto-discovered and **scoped to `$USER`**: a wildcard like
`/scratch/*/.claude/projects` matches other people's directories on a shared cluster, which both
inflates your total and reads what isn't yours.

Two things stay uncounted regardless: cloud sessions (server-side, never written to local disk)
and Claude Desktop / claude.ai. There is no way to recover those from a filesystem.

### Cost over time

Transcripts timestamp every record in **UTC**, whatever timezone the host runs in, so a laptop on
Pacific and a cluster on Eastern are already on one clock. The timezone is purely a display choice,
applied when the bins are drawn:

```bash
python3 measure_usage.py --by day  --tz America/Vancouver   # calendar days, gaps preserved
python3 measure_usage.py --by hour --tz America/Vancouver   # hour-of-day profile
python3 measure_usage.py --by dow                           # day-of-week profile
python3 measure_usage.py --by week   # or --by month
```

`--by` works with `--merge` too, so multi-machine history bins on a single wall clock.

For an all-time figure — daily energy and cumulative CO2, each with its uncertainty band, plus
annotated events:

```bash
python3 measure_usage.py --plot figures/usage.png --tz America/Vancouver \
        --event 2026-07-24='Pro -> Max'
```

The daily band is the ×/÷2 method uncertainty on the per-token rates; the cumulative band spans
every grid convention in `sourced_data.json`. `--event` is repeatable and prints the mean-per-day
on either side of each marker.

## A note on the numbers

Anthropic publishes no environmental data, so nothing here about Claude is measured — it is all
third-party estimation with method-level uncertainty of roughly 2–4× per point, and up to an order
of magnitude in total for the session scenario. Both documents are written to make that explicit
rather than to hide it. Please preserve that when editing; see the honesty rule in `CLAUDE.md`.
