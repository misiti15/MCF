"""Primary edit check (1 config, counted): MF2-FD / MF4-FD (and their base versions) with a +0.5 x stop-distance target
on their whole two-year record (same scalp model as sqz1.py: 5-min MFE, stop-first on the exit bar, entry cost only).
Usage: python mf_t05.py <scratch-with-enr>. Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; LOCK = ("2024-11-01", "2025-02-28")
SET = {"MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "MF2-open-rsimidhi-flowsell", "MF4-h40-open-flowsell"}
TGT = {"t1s1": 1.0, "t1s05": 2.0, "t05s05": 1.0, "t05s1": 0.5}
slot = lambda tod: ((tod // 100) * 60 + tod % 100 - 590) // 5
T = []
for p in sorted((S / "enr").glob("*.parquet")):
    t = pd.read_parquet(p); mf = np.load(str(p).replace(".parquet", "_mfe.npy")).astype(np.float32)
    k = t.setup.isin(SET).values
    if not k.any(): continue
    t = t[k].reset_index(drop=True); mf = pd.DataFrame(mf[k]).ffill(axis=1).to_numpy(np.float32)
    assert not ((t.date >= LOCK[0]) & (t.date <= LOCK[1])).any()
    s0 = slot(t.tod.to_numpy()); sx = np.clip(slot(t.xtod.to_numpy()), 0, 73); ix = np.arange(len(t))
    pre = np.where(sx - 1 >= s0 + 1, mf[ix, np.clip(sx - 1, 0, 73)], 0.0); atx = np.nan_to_num(mf[ix, sx], nan=0.0)
    t["hit"] = np.where(t.kind.to_numpy() == 1, pre >= 0.5, atx >= 0.5); T.append(t)
T = pd.concat(T, ignore_index=True)
e = T.entry.to_numpy(float); ec = (0.01 + e * 1e-4) * tod_cost_mult(T.tod.to_numpy()) * np.where(e < 5, 3.0, 1.0)
r05 = 0.5 - ec / (T.stop_pct.to_numpy(float) * e)
T["r_s"] = np.where((T.geom.map(TGT) > 0.5) & T.hit, r05, T.r); T["d"] = T.r_s - T.r
T["half"] = np.where(T.date <= "2026-02-28", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
for (s, h), g in T.groupby(["setup", "half"]):
    dd = g.groupby("date").d.sum(); t_ = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))) if len(dd) > 2 else np.nan
    print(f"{s:<34} {h:<5} n {len(g):>5} geom {g.geom.iloc[0]} live-rule avg {g.r.mean():+.3f} -> t05 {g.r_s.mean():+.3f} (delta {g.d.sum():+.1f}R, day-t {t_:.2f}, hit {g.hit.mean():.0%})")
print("Locked block never read. Configurations: 1. Educational only - not financial advice.")
