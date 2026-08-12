"""Researcher-session scenario: N equal prompts accruing to 80% of a 1M window.
All rates are published third-party values (see data/sourced_data.json); everything
computed here is DERIVED and labeled as such in the report."""
import json

D = json.load(open("data/sourced_data.json"))

W = 800_000            # 80% of 1M window

# Output share of the accrued window. This was originally an unmeasured assumption swept 0.2-0.8
# and centred at 0.5. It is now MEASURED, from 56 real Claude Code sessions (16,240 assistant
# messages) belonging to one heavy user: see measure_usage.py. The measurement gives 19-24%
# depending on how cache-writes are attributed, so the central case is 0.20 and the swept band is
# the measured one. A user whose work is more output-heavy would sit higher; f = 0.5 is retained
# below as a labelled sensitivity because it was this brief's previous central case.
F_CENTRAL = 0.20
F_RANGE = (0.19, 0.24)
F_LEGACY = 0.50

c = D["couch_2026"]
R_IN, R_OUT, R_CACHE = (c["wh_per_million_input_tokens"] / 1e6,
                        c["wh_per_million_output_tokens"] / 1e6,
                        c["wh_per_million_cached_read_tokens"] / 1e6)

def session(N, f_out, cached=True):
    """Context grows by W/N per turn to W. f_out = fraction of window that is model output.
    Turn k: reads context of size (k-1)*step (cached or fresh), adds step new tokens.
    New tokens per turn: (1-f_out)*step user input (fresh) + f_out*step model output."""
    step = W / N
    hist = sum((k - 1) * step for k in range(1, N + 1))   # total history tokens re-read
    fresh_new = (1 - f_out) * W
    out_new = f_out * W
    if cached:
        e = fresh_new * R_IN + out_new * R_OUT + hist * R_CACHE
        parts = (fresh_new * R_IN, out_new * R_OUT, hist * R_CACHE)
    else:
        e = (fresh_new + hist) * R_IN + out_new * R_OUT
        parts = ((fresh_new + hist) * R_IN, out_new * R_OUT, 0.0)
    return e, parts, hist

print("=== Couch (Opus 4.5) rate-set, Wh per session ===")
for N in (20, 25, 30):
    for f in (0.2, 0.5, 0.8):
        for cached in (True, False):
            e, parts, hist = session(N, f, cached)
            print(f"N={N} f_out={f} cached={cached}: {e:8.0f} Wh  "
                  f"(fresh {parts[0]:.0f} + out {parts[1]:.0f} + cache {parts[2]:.0f}); hist={hist/1e6:.1f}M tok")

# Digital Applied (Opus 4.7) alternative: per-request Wh at ~800 tok and 800k ctx.
# Linear interpolation in context size (labeled derivation): e(ctx) = 0.78 + (14.1-0.78)*ctx/800k
da = D["digital_applied_2026"]["claude_opus_4_7"]
def session_da(N):
    step = W / N
    tot = 0
    for k in range(1, N + 1):
        ctx = k * step
        tot += da["chat_wh"] + (da["long_context_wh"] - da["chat_wh"]) * ctx / da["long_context_tokens"]
    return tot
print("\n=== Digital Applied (Opus 4.7) interpolation, Wh per session ===")
for N in (20, 25, 30):
    print(f"N={N}: {session_da(N):6.0f} Wh  (x3 => {session_da(N)*3:.0f}, /3 => {session_da(N)/3:.0f})")

# Central + bounds
e_lo = session_da(25) / 3          # DA low bound (their /3 uncertainty)
e_central, _, _ = session(25, F_CENTRAL, True)
e_legacy, _, _ = session(25, F_LEGACY, True)
e_hi, _, _ = session(25, F_RANGE[1], False)
rng = [session(N, f, True)[0] for N in (20, 25, 30) for f in F_RANGE]
rng_off = [session(N, f, False)[0] for N in (20, 25, 30) for f in F_RANGE]
print(f"\n=== HEADLINE (measured f = {F_CENTRAL}) ===")
print(f"  central          : {e_central:6.0f} Wh   range {min(rng):.0f}-{max(rng):.0f} Wh")
print(f"  caching off      : {min(rng_off):6.0f}-{max(rng_off):.0f} Wh "
      f"({min(rng_off)/min(rng):.1f}x)")
print(f"  legacy f=0.5     : {e_legacy:6.0f} Wh   -> old central was {e_legacy/e_central:.2f}x high")
print(f"  optimistic (DA)  : {e_lo:6.0f} Wh")

# Carbon and water
GRIDS = {"eGRID NYUP (upstate NY)": 110, "eGRID ERCT": 333, "eGRID US average": 348,
         "eGRID RFCW (Indiana PJM)": 413,
         "Cambium LRMER ERCOT": D["cambium_2023_lrmer"]["gco2_per_kwh"]["ERCOT"],
         "Cambium LRMER NYISO": D["cambium_2023_lrmer"]["gco2_per_kwh"]["NYISO"],
         "Cambium LRMER PJM_West": D["cambium_2023_lrmer"]["gco2_per_kwh"]["PJM_West"],
         "AVERT SRMER New York": D["avert_2023"]["gco2_per_kwh"]["New York"],
         "AVERT SRMER Texas": D["avert_2023"]["gco2_per_kwh"]["Texas"],
         "AVERT SRMER Mid-Atlantic": D["avert_2023"]["gco2_per_kwh"]["Mid-Atlantic"],
         "AVERT SRMER US national": D["avert_2023"]["gco2_per_kwh"]["US_national"],
         "PJM SRMER 2022 flat": D["pjm_emissions_2022"]["flat_load_marginal_gco2_per_kwh_derived"]}
WUE_ON, WUE_OFF = 0.18, 3.142   # L/kWh, Jegham v6 AWS multipliers
kwh = e_central / 1000
print(f"\n=== Central session {kwh:.3f} kWh under every grid convention ===")
for g, ci in sorted(GRIDS.items(), key=lambda kv: kv[1]):
    print(f"  {g:28s} {ci:6.1f} g/kWh -> {kwh*ci:6.0f} g")
vals = [kwh*ci for ci in GRIDS.values()]
print(f"  BAND: {min(vals):.0f}-{max(vals):.0f} g  ({max(vals)/min(vals):.1f}x)")

print(f"\n=== Water (central) ===")
print(f"  on-site {kwh*WUE_ON:.2f} L | off-site {kwh*WUE_OFF:.2f} L | total {kwh*(WUE_ON+WUE_OFF):.2f} L")
print(f"  per prompt: {e_central/25:.1f} Wh | {kwh*348/25:.1f} g CO2e (US avg) | "
      f"{kwh*(WUE_ON+WUE_OFF)/25*1000:.0f} mL total water")

print(f"\n=== Everyday denominators (central, US-average grid) ===")
co2 = kwh * 348
print(f"  {co2:.0f} g CO2e = {co2/10000*100:.1f}% of a household's daily electricity emissions (~10 kg)")
print(f"                = {co2/38000*100:.2f}% of an American's total daily footprint (~38 kg)")
print(f"                = {co2/400:.2f} miles / {co2/400*1.609:.2f} km driving (EPA 400 g/mi)")
print(f"  {kwh*(WUE_ON+WUE_OFF):.2f} L water = {kwh*(WUE_ON+WUE_OFF)/310*100:.1f}% of daily indoor use (~310 L)"
      f" = {kwh*(WUE_ON+WUE_OFF)/6:.2f} toilet flushes = {kwh*(WUE_ON+WUE_OFF)/0.5:.1f} x 500 mL bottles")
print(f"  {e_central/0.24:.0f} median Gemini prompts | {kwh/29*100:.1f}% of household daily kWh (29 kWh)"
      f" | {kwh/0.17:.1f} EV km")
print(f"  one session per working day (260/yr): {co2*260/1000:.0f} kg CO2e/yr, "
      f"{kwh*(WUE_ON+WUE_OFF)*260:.0f} L/yr")
print(f"  lab of 20 doing that daily: {kwh*20*260/1000:.1f} MWh/yr")
