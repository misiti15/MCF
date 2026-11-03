"""eu1103/universe step 6 (post hoc, 2 configs): does S1 top-500 dollar-ATR still add once a CF-like cost filter is in
(the Testing cost filter CF, live in Testing 1/2 since 10-30: skip entries whose stop-exit round-trip cost > 0.15R)?
2y lab trades at the live floor; stop-exit cost = 2 x (1c + 1 bps x price) x tod-mult(entry side approx 1) + 2c, in R
(R = 0.25 x daily ATR). Usage: python cf_overlap.py <scratch> -> cf_overlap_out.txt. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
sys.argv = [sys.argv[0], str(S)]
import importlib.util
spec = importlib.util.spec_from_file_location("a2", HERE / "analyze2y.py"); A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
T = A.load(); T = T[T.adv20 >= T.floor].copy()
T["cf"] = (2 * (0.01 + 0.0001 * T.px) + 0.02) / (0.25 * T.atr_d)
d = lib.daily().sort_values(["symbol", "date"])
d["pc"] = d.groupby("symbol").close.shift()
tr = np.maximum(d.high - d.low, np.maximum((d.high - d.pc).abs(), (d.low - d.pc).abs()))
d["atr"] = tr.groupby(d.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
d = d[d.adv20 >= 95e6]; d["rk"] = (d.adv20 * d.atr / d.pc).groupby(d.date).rank(ascending=False)
T = T.merge(d[["symbol", "date", "rk"]], on=["symbol", "date"], how="left")
out = ["Educational only - not financial advice. 2y lab trades, 8 setups at live floor, costs in. CF-like = stop-exit cost <= 0.15R."]
for sp in ("TRAIN", "VALID"):
    x = T[T.split == sp]; c = x[x.cf <= 0.15]
    k, dr = c[c.rk <= 500], c[~(c.rk <= 500)]
    dd = pd.concat([k.groupby("date").r.mean().rename("k"), dr.groupby("date").r.mean().rename("d")], axis=1).dropna(); df = dd.k - dd.d
    out.append(f"{sp}: base n {len(x)} R {x.r.mean():.4f} | CF-like kept {len(c)/len(x):.3f} R {c.r.mean():.4f} | CF + S1 top-500 kept "
               f"{len(k)/len(x):.3f} R {k.r.mean():.4f} vs CF-kept-but-outside-top500 R {dr.r.mean():.4f}, kd {df.mean():.4f} t {df.mean()/(df.std()/np.sqrt(len(df))):.2f}")
(HERE / "cf_overlap_out.txt").write_text("\n".join(out) + "\n"); print("\n".join(out))
