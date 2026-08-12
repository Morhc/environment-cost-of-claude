PANDOC_FLAGS = --pdf-engine=xelatex

MAIN_FIGS = figures/fig1_claude_energy_vs_tokens.png \
            figures/fig2_cross_provider.png \
            figures/fig3_token_scaling.png \
            figures/fig4_datacenters.png \
            figures/fig5_training.png
BRIEF_FIG = figures/fig_s1_session.png
# figures/fig_s2_usage_alltime.png is NOT a make target: it is built from the author's own
# Claude Code transcripts via `measure_usage.py --plot`, which no other reader can reproduce.
# It is committed as a static asset.

.PHONY: all report brief figures scenario clean

all: report brief

report: claude-environmental-impact-report.pdf
brief: opus-researcher-footprint-brief.pdf
figures: $(MAIN_FIGS) $(BRIEF_FIG)

claude-environmental-impact-report.pdf: report.md $(MAIN_FIGS)
	pandoc $< -o $@ $(PANDOC_FLAGS)

opus-researcher-footprint-brief.pdf: researcher_brief.md $(BRIEF_FIG)
	pandoc $< -o $@ $(PANDOC_FLAGS)

$(MAIN_FIGS): make_figures.py data/sourced_data.json
	python3 make_figures.py

$(BRIEF_FIG): make_scenario_figure.py data/sourced_data.json
	python3 make_scenario_figure.py

# Print every scenario permutation (energy, carbon at 4 grids, water)
scenario:
	python3 scenario_calc.py

# Note: both PDFs are committed to the repo (they are the deliverable). `make clean`
# removes them locally; `git checkout` restores the committed copies.
clean:
	rm -f claude-environmental-impact-report.pdf opus-researcher-footprint-brief.pdf
