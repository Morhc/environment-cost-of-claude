"""Researcher-session scenario: N equal prompts accruing to 80% of a 1M window.
All rates are published third-party values (see data/sourced_data.json); everything
computed here is DERIVED and labeled as such in the report."""
import json

D = json.load(open("data/sourced_data.json"))

W = 800_000            # 80% of 1M window
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
e_central, _, _ = session(25, 0.5, True)
e_hi, _, _ = session(25, 0.8, False)
print(f"\nLow / central / high session energy: {e_lo:.0f} / {e_central:.0f} / {e_hi:.0f} Wh")

# Carbon and water
grids = {"NY upstate (NYUP)": 110, "ERCOT (ERCT)": 333, "US average": 348, "Indiana PJM (RFCW)": 413}
WUE_ON, WUE_OFF = 0.18, 3.142   # L/kWh, Jegham v6 AWS multipliers
print("\n=== Carbon (g CO2e/session) and water (L/session) ===")
for name, e in (("low", e_lo), ("central", e_central), ("high", e_hi)):
    kwh = e / 1000
    print(f"\n{name}: {e:.0f} Wh = {kwh:.2f} kWh")
    for g, ci in grids.items():
        print(f"  {g:22s}: {kwh*ci:7.0f} g CO2e")
    print(f"  water on-site: {kwh*WUE_ON:.2f} L; off-site: {kwh*WUE_OFF:.2f} L; total: {kwh*(WUE_ON+WUE_OFF):.2f} L")

# Per prompt (central)
print(f"\ncentral per-prompt: {e_central/25:.1f} Wh; carbon US avg {e_central/1000*348/25:.1f} g; water total {e_central/1000*(WUE_ON+WUE_OFF)/25*1000:.0f} mL")

# Equivalences (central session, 1.31 kWh-ish)
kwh = e_central / 1000
print(f"\nequivalences central: {kwh:.2f} kWh; US household daily 29 kWh -> {kwh/29*100:.1f}%;"
      f" EV km at 0.17 kWh/km -> {kwh/0.17:.1f} km; car miles at 400 g/mi (US avg) -> {kwh*348/400:.2f} mi")
print(f"gemini-prompt equivalents: {e_central/0.24:.0f}")
