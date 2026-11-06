"""FB1 live check 2026-11-05 (descriptive, not scored): live shorts (7 accounts, run 1) by the FB1 classes at the last closed
5-min bar before the fill (11-05 frames from research/bdi/moves/frames_today.py). Usage: python fb1_live.py <scratch>
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
F = pd.read_parquet(S / "mh/2026-11-05/frames.parquet")[["symbol", "tod", "dist_lod_atr", "dist_hod_atr", "rsi5"]]
T = pd.read_csv(HERE.parent / "nightly1105" / "trades.csv"); T = T[T.run_id == 1].copy()
nt = pd.to_datetime(T.nt, utc=True, format="mixed").dt.tz_convert(TZ); b = (nt - pd.Timedelta("5min")).dt.floor("5min") + pd.Timedelta("5min")
T["tod"] = b.dt.hour * 100 + b.dt.minute
Q = F[F.symbol == "QQQ"][["tod", "dist_lod_atr"]].rename(columns={"dist_lod_atr": "q_lod"})
T = T.merge(F, on=["symbol", "tod"], how="left").merge(Q, on="tod", how="left")
s = T[T.side == -1]; l = T[T.side == 1]
for nm, x, m in (("FB1-S near LOD", s, s.dist_lod_atr <= 0.15), ("FB1-I QQQ at its low", s, s.q_lod <= 0.15),
                 ("FB1-B bounce-sold", s, (s.dist_lod_atr >= 0.5) & (s.rsi5 >= 50)), ("FB1-L near HOD (longs)", l, l.dist_hod_atr <= 0.15)):
    print(f"{nm}: class n {int(m.sum())} avg {x[m].radj.mean():+.3f}R | rest n {int((~m & x.dist_lod_atr.notna()).sum())} avg {x[~m & x.dist_lod_atr.notna()].radj.mean():+.3f}R | "
          + "; ".join(f"{k} {len(g)} {g.radj.mean():+.2f}" for k, g in x[m].groupby(x[m].strategy.str.split('-').str[0])))
print(f"coverage {T.dist_lod_atr.notna().mean():.0%}\nEducational only - not financial advice.")
