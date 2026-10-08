"""AUDIT: independently re-run the four exit near-misses (NM1-NM4) with research/oct7/exits Lab (production
simulate + Backtester.allocate), applying each variant to its own setup ONLY (the exits study applied the %
caps to all setups at once). Train/valid only. Educational only - not financial advice."""
import json
import sys

sys.path.insert(0, ".")
from research.oct7.exits.study import Lab, compare  # noqa: E402

V = {
    "NM1 hfs cap 2.0%": ("heat_fade_short", {"cap": 2.0}),
    "NM1 nb cap 1.5%": ("heat_fade_short", {"cap": 1.5}),
    "NM1 nb cap 2.5%": ("heat_fade_short", {"cap": 2.5}),
    "NM1 nb cap 3.0%": ("heat_fade_short", {"cap": 3.0}),
    "NM2 hfl exit 15:30": ("heat_fade_long", {"exit_by": "15:30"}),
    "NM2 nb hfl late 15:30 >0": ("heat_fade_long", {"late": ("15:30", 0.0)}),
    "NM2 nb hfl late 15:00 >0": ("heat_fade_long", {"late": ("15:00", 0.0)}),
    "NM3 exh gb 0.5->0": ("exhaustion_short", {"gb": (0.5, 0.0)}),
    "NM3 nb exh gb 0.5->0.25": ("exhaustion_short", {"gb": (0.5, 0.25)}),
    "NM3 nb exh gb 0.75->0": ("exhaustion_short", {"gb": (0.75, 0.0)}),
    "NM4 im scale 0.5 x0.33": ("intraday_momentum", {"scale_out_r": 0.5, "scale_out_frac": 0.33}),
    "NM4 nb im scale 0.5 x0.5": ("intraday_momentum", {"scale_out_r": 0.5, "scale_out_frac": 0.5}),
}
lab = Lab()
print("verify mismatches", lab.verify(), "of", len(lab.sigs), flush=True)
base = lab.portfolio({}, None)
out = {}
for k, (st, v) in V.items():
    df = lab.portfolio(v, st)
    out[k] = {sp: compare(df, base, st, sp) for sp in ("train", "valid")}
    out[k]["portfolio_valid_d_pnl"] = compare(df, base, None, "valid")["d_pnl"]
    tr, va = out[k]["train"], out[k]["valid"]
    print(f"{k:28s} train dR0 {tr['d_r0']:+.4f} t {tr['d_r0_t']:+.2f} d$ {tr['d_pnl']:+.0f} exbest {tr['d_r0_ex_best']:+.4f} | "
          f"valid dR0 {va['d_r0']:+.4f} t {va['d_r0_t']:+.2f} d$ {va['d_pnl']:+.0f} exbest {va['d_r0_ex_best']:+.4f}", flush=True)
json.dump(out, open("research/oct7/audit/exits_repro.json", "w"), indent=1, default=str)
