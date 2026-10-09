"""Per strategy x side summary of data/scan.csv -> results.csv (committed) and printed markdown rows for NOTES.md.
Educational only - not financial advice."""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
d = pd.read_csv(HERE / "data" / "scan.csv")
rows = []
for (s, side), g in d.groupby(["strategy", "side"]):
    base = g[g.filters == "-"].sort_values("t", ascending=False).iloc[0]
    best = g[g.n >= 150].sort_values("t", ascending=False).iloc[0]
    rows.append({"strategy": s, "side": side, "configs": len(g), "positive_exp": int((g.exp > 0).sum()),
                 "base_geom": base.geom, "base_n": int(base.n), "base_per_day": base.per_day, "base_win": round(base.win, 3),
                 "base_exp": round(base.exp, 3), "base_t": round(base.t, 2), "base_up": round(base.exp_up, 3),
                 "base_flat": round(base.exp_flat, 3), "base_down": round(base.exp_down, 3),
                 "best_cfg": f"{best.filters}|{best.geom}", "best_n": int(best.n), "best_per_day": best.per_day,
                 "best_win": round(best.win, 3), "best_exp": round(best.exp, 3), "best_t": round(best.t, 2),
                 "best_up": round(best.exp_up, 3), "best_down": round(best.exp_down, 3),
                 "best_ex_best_day": round(best.ex_best_day, 3), "best_maxday": round(best.maxday, 3)})
r = pd.DataFrame(rows).sort_values("best_t")
r.to_csv(HERE / "results.csv", index=False)
for x in r.itertuples():
    print(f"| {x.strategy} | {x.side} | {x.positive_exp}/{x.configs} | {x.base_geom}: n {x.base_n} ({x.base_per_day:.0f}/day), "
          f"win {x.base_win}, {x.base_exp:+.3f}R, t {x.base_t}; up {x.base_up:+.3f} / flat {x.base_flat:+.3f} / down {x.base_down:+.3f} | "
          f"{x.best_cfg}: n {x.best_n} ({x.best_per_day:.1f}/day), win {x.best_win}, {x.best_exp:+.3f}R, t {x.best_t}; "
          f"up {x.best_up:+.3f} / down {x.best_down:+.3f}; ex-best-day {x.best_ex_best_day:+.3f}; busiest day {x.best_maxday:.0%} |")
