"""Bottom-up bounds on Claude training energy and carbon.

EVERYTHING THIS PRINTS IS DERIVED, NOT PUBLISHED. It is the deliberate exception to the
strictness rule, confined to Appendix C of the main report. See CLAUDE.md.

Method. Rather than stack assumptions about hardware, utilization and PUE from scratch, the
primary route calibrates energy-per-FLOP against the one modern training run for which both
compute and GPU-hours are disclosed by the developer -- Llama 3.1 405B -- and applies that
intensity to Epoch AI's FLOP estimates for Claude. A first-principles route is run alongside as
a consistency check, with model FLOP utilization (MFU) swept over the range the literature
supports.

The dominant uncertainty is the FLOP estimate, not the energy conversion: Epoch flags its Claude
figures as low-precision, and for Claude 3.7 Sonnet publishes a range spanning a factor of 9.
Run from the project root."""
import json

D = json.load(open("data/sourced_data.json"))

# --- Anchors (all published) -------------------------------------------------------------
# Meta, Llama 3 Herd of Models (arXiv:2407.21783) + Llama 3.1 model card:
LLAMA_FLOP = 3.8e25                                   # disclosed in the paper
LLAMA_GPU_H = D["training_disclosed"]["llama31_405b"]["gpu_hours"]   # 30.84M H100-hours
H100_TDP_W = 700                                      # NVIDIA H100 SXM TDP
H100_BF16_DENSE = 989.5e12                            # FLOP/s, dense (1,979 TFLOP/s w/ sparsity)
PUE = 1.14                                            # AWS multiplier used by Jegham et al. v6
MFU_RANGE = (0.25, 0.50)                              # published large-run MFU spread

FLOP = D["epoch_training_flop"]["estimates_flop"]
CLAUDE = {"Claude 3 Opus": FLOP["claude_3_opus"],
          "Claude 3.5 Sonnet": FLOP["claude_35_sonnet"],
          "Claude 3.7 Sonnet": FLOP["claude_37_sonnet"]}
SONNET37_RANGE = (1.1e25, 1.0e26)                     # Epoch's own stated range

GRIDS = {"NYUP (upstate NY)": 110, "US average": 348, "RFCW (Indiana PJM)": 413,
         "AVERT Mid-Atlantic marginal": D["avert_2023"]["gco2_per_kwh"]["Mid-Atlantic"]}

# --- Route 1: calibrate against Llama 3.1 -------------------------------------------------
llama_wh = LLAMA_GPU_H * H100_TDP_W                   # 21.6 GWh, chip-only, TDP basis, no PUE
wh_per_flop = llama_wh / LLAMA_FLOP
implied_mfu = LLAMA_FLOP / (LLAMA_GPU_H * 3600 * H100_BF16_DENSE)

print("=== Calibration anchor: Llama 3.1 405B (developer-disclosed) ===")
print(f"  {LLAMA_GPU_H/1e6:.2f}M H100-hours x {H100_TDP_W} W = {llama_wh/1e9:.1f} GWh "
      f"(chip-only, TDP basis, no PUE)")
print(f"  {LLAMA_FLOP:.1e} FLOP  ->  {wh_per_flop:.3e} Wh/FLOP  "
      f"({wh_per_flop*1e25/1e9:.2f} GWh per 1e25 FLOP)")
print(f"  implied MFU = {implied_mfu:.1%}  (sanity: sits inside the published {MFU_RANGE[0]:.0%}-"
      f"{MFU_RANGE[1]:.0%} band)")

# Independent validation: Meta also disclosed location-based tCO2e for the same run. Dividing
# that by the energy derived above backs out the grid factor Meta's own accounting implies --
# if the TDP-based energy were badly wrong, this would land nowhere near a real US grid.
llama_tco2 = D["training_disclosed"]["llama31_405b"]["tco2e_location"]
implied_grid = llama_tco2 * 1e6 / (llama_wh / 1000)
print(f"  cross-check: Meta's disclosed {llama_tco2:,} tCO2e / {llama_wh/1e9:.1f} GWh implies a "
      f"{implied_grid:.0f} gCO2/kWh grid,")
print(f"  which is a plausible US industrial grid factor (cf. eGRID RFCW 413, US avg 348) -- so "
      f"the TDP basis is not wildly off.")

# --- Route 2: first principles, MFU swept -------------------------------------------------
def wh_per_flop_fp(mfu):
    """Accelerator-seconds needed per FLOP, times power."""
    return H100_TDP_W / (H100_BF16_DENSE * mfu) / 3600

print("\n=== Consistency check: first-principles Wh/FLOP across the MFU band ===")
for mfu in (MFU_RANGE[0], implied_mfu, MFU_RANGE[1]):
    print(f"  MFU {mfu:5.1%}: {wh_per_flop_fp(mfu):.3e} Wh/FLOP "
          f"({wh_per_flop_fp(mfu)*1e25/1e9:.2f} GWh per 1e25 FLOP)")
lo_int, hi_int = wh_per_flop_fp(MFU_RANGE[1]), wh_per_flop_fp(MFU_RANGE[0])
print(f"  -> conversion uncertainty alone is {hi_int/lo_int:.1f}x; the Llama calibration "
      f"sits within it")

# --- Bounds per model ---------------------------------------------------------------------
def band(flop):
    """(low, central, high) GWh at the wall, i.e. including PUE."""
    return (flop * lo_int * PUE / 1e9, flop * wh_per_flop * PUE / 1e9,
            flop * hi_int * PUE / 1e9)

print(f"\n=== Derived training energy, GWh at the wall (PUE {PUE}) ===")
print(f"{'Model':<20} {'FLOP':>9}   {'low':>6} {'central':>8} {'high':>6}")
for name, flop in CLAUDE.items():
    lo, ce, hi = band(flop)
    print(f"{name:<20} {flop:>9.1e}   {lo:6.1f} {ce:8.1f} {hi:6.1f}")
lo_s, _, hi_s = band(SONNET37_RANGE[0])[0], None, band(SONNET37_RANGE[1])[2]
print(f"{'  (3.7 Sonnet, using':<20}")
print(f"{'   Epoch FLOP range)':<20} {SONNET37_RANGE[0]:.1e}-{SONNET37_RANGE[1]:.1e}"
      f"   {lo_s:6.1f} {'':8} {hi_s:6.1f}   <- the honest width")

print(f"\n=== Derived training carbon, tCO2, central conversion ===")
print(f"{'Model':<20} " + " ".join(f"{g:>14}" for g in GRIDS))
for name, flop in CLAUDE.items():
    _, ce, _ = band(flop)
    print(f"{name:<20} " + " ".join(f"{ce*1e6*ci/1e6:>14,.0f}" for ci in GRIDS.values()))

# --- Context -------------------------------------------------------------------------------
bloom = D["training_disclosed"]["bloom"]["energy_mwh"] / 1000
gpt3 = D["training_disclosed"]["gpt3"]["energy_mwh"] / 1000
sink = D["training_disclosed"]["claude_any"]["external_estimate"]["value_tco2e"]
_, opus_ce, _ = band(CLAUDE["Claude 3 Opus"])
_, s37_ce, _ = band(CLAUDE["Claude 3.7 Sonnet"])
print(f"\n=== Context ===")
print(f"  BLOOM 176B (measured):        {bloom:6.2f} GWh")
print(f"  GPT-3 (Patterson estimate):   {gpt3:6.2f} GWh")
print(f"  Llama 3.1 405B (disclosed):   {llama_wh/1e9:6.2f} GWh (chip-only, no PUE)")
print(f"  Claude 3 Opus (derived here): {opus_ce:6.2f} GWh")
# Denominators that make a GWh legible.
session_wh = 936                                      # central researcher session, scenario_calc.py
gemini_wh = D["google_2025"]["median_text_prompt"]["wh"]
rainier_mw = D["datacenters"]["new_carlisle_in"]["mw_observed_2026_03"]
print(f"\n  In other units, the Claude 3 Opus central figure ({opus_ce:.1f} GWh) is:")
print(f"    ~{opus_ce*1e9/session_wh/1e6:.1f}M heavy researcher sessions (at {session_wh} Wh each)")
print(f"    ~{opus_ce*1e9/gemini_wh/1e9:.0f}B median Gemini prompts (at {gemini_wh} Wh each)")
print(f"    ~{opus_ce*1e9/(rainier_mw*1e6):.0f} hours of the New Carlisle campus at its observed "
      f"{rainier_mw} MW draw")
print(f"  -- i.e. one frontier training run of this scale is roughly HALF A DAY of one campus,")
print(f"  which is why the literature expects lifetime inference to dominate training.")

print(f"\n  SINK's external estimate for 'a Claude 4 training run' is {sink:,} tCO2e.")
print(f"  Our Claude 3.7 Sonnet central lands at "
      f"{s37_ce*1e6*GRIDS['US average']/1e6:,.0f} tCO2 (US avg grid) -- i.e. SINK's figure for a")
print(f"  LATER model sits below our estimate for an EARLIER one, which is a reason to")
print(f"  distrust it rather than a corroboration.")
