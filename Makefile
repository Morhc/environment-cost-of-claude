PANDOC_FLAGS = --pdf-engine=xelatex

MAIN_FIGS = figures/fig1_claude_energy_vs_tokens.png \
            figures/fig2_cross_provider.png \
            figures/fig3_token_scaling.png \
            figures/fig4_datacenters.png \
            figures/fig5_training.png
# figures/fig_s2_usage_alltime.png is NOT a make target: it is built from your own Claude Code
# transcripts via `measure_usage.py --plot`, which no other reader can reproduce.

.PHONY: all dashboard app icon figures provenance clean

all: figures

# Local dashboard: your own usage, four tabs, refresh button
dashboard:
	python3 dashboard.py

# macOS: a double-clickable app on the Desktop. Sets DASHBOARD_AUTOQUIT=1, so the server exits
# once no browser tab is watching it. Embeds this checkout's path -- rerun after moving the repo.
app:
	python3 make_app.py

# Regenerate the tab icon and re-inline it into dashboard.html as a data URI
icon:
	python3 make_favicon.py

figures: $(MAIN_FIGS)

$(MAIN_FIGS): make_figures.py data/sourced_data.json
	python3 make_figures.py

# Optional: PROVENANCE.md as a PDF for citation. Needs pandoc + xelatex + DejaVu fonts.
provenance: PROVENANCE.pdf
PROVENANCE.pdf: PROVENANCE.md $(MAIN_FIGS)
	pandoc $< -o $@ $(PANDOC_FLAGS) -V geometry:margin=2.6cm -V mainfont="DejaVu Sans" \
	  -V fontsize=11pt -V linkcolor=blue --toc

clean:
	rm -f PROVENANCE.pdf
