"""Per symbol-day atr_d / prior close / prior-day high-low / adv20 from the open lab frames (NOTES 1.1), the W2 betas,
and a parity sample of frame lab R. Output (git-ignored): data/aux.npz, data/parity_frames.parquet.
Educational only - not financial advice."""
import shutil

import numpy as np
import pandas as pd

from common import DATA, ROOT, lib, open_dates, symbols

DATA.mkdir(exist_ok=True)
syms, dates = symbols(), open_dates()
si = {s: i for i, s in enumerate(syms)}
di = {d: i for i, d in enumerate(dates)}
D, S = len(dates), len(syms)
A = {k: np.full((D, S), np.nan, np.float32) for k in ("atr", "pclose", "pdh", "pdl", "adv20")}
PAR_SYMS = set(syms[::50])
par = []
cols = ["symbol", "date", "tod", "close", "atr_d", "gap", "dist_pdh_atr", "dist_pdl_atr", "adv20", "fromOpen",
        "r_long_t1s1", "r_short_t1s1", "r_long_t05s1", "r_short_t1s05"]
for m in lib.months():
    df = lib.load_month(m, columns=cols)
    first = df.groupby(["symbol", "date"], sort=False).head(1)
    i = first["date"].map(di).to_numpy()
    j = first["symbol"].map(si).to_numpy()
    ok = ~(pd.isna(i) | pd.isna(j))
    i, j, f = i[ok].astype(int), j[ok].astype(int), first[ok]
    atr = f["atr_d"].to_numpy(float)
    c = f["close"].to_numpy(float)
    dopen = c / (1 + f["fromOpen"].to_numpy(float) / 100)
    A["atr"][i, j] = atr
    A["pclose"][i, j] = dopen / (1 + f["gap"].to_numpy(float) / 100)
    A["pdh"][i, j] = c + f["dist_pdh_atr"].to_numpy(float) * atr
    A["pdl"][i, j] = c - f["dist_pdl_atr"].to_numpy(float) * atr
    A["adv20"][i, j] = f["adv20"].to_numpy(float)
    par.append(df[df["symbol"].isin(PAR_SYMS)])
    print(m, len(df), flush=True)
    del df
b = np.load(ROOT / "research/swarm1010/w2_neutral/data/betas.npz")
A["beta_spy"] = b["beta_spy"]
np.savez(DATA / "aux.npz", **A)
pd.concat(par).to_parquet(DATA / "parity_frames.parquet", index=False)
print("done", {k: float(np.isfinite(v).mean()) for k, v in A.items()})
