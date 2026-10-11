"""Market context [session, bar]: SPY / QQQ bars and features, SPY strict turns, breadth (% of non-ETF symbols above
session VWAP). Output (git-ignored): data/context.npz. Educational only - not financial advice."""
import time

import numpy as np

from common import DATA, ETFS, KS, fill, load_bars, open_dates, symbols, turn_labels

syms, dates = symbols(), open_dates()
dates64 = np.array([np.datetime64(str(x)) for x in dates], dtype="datetime64[us]")
aux = np.load(DATA / "aux.npz")
D, NB = len(dates), 77
above = np.zeros((D, NB), np.float64)
count = np.zeros((D, NB), np.float64)
out = {}
t0 = time.time()
for j, s in enumerate(syms):
    b = load_bars(s, dates64)
    if b is None:
        continue
    if s in ("SPY", "QQQ"):
        f = fill(b)
        for k in ("O", "H", "L", "C"):
            out[f"{s}_{k}"] = f[k]
        out[f"{s}_present"] = f["present"]
    if s in ETFS:
        continue
    pres = np.isfinite(b["C"])
    V = np.where(pres, b["V"], 0).astype(np.float64)
    tp = np.where(pres, (b["H"] + b["L"] + b["C"]) / 3, 0).astype(np.float64)
    cv = np.cumsum(V, 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = np.cumsum(tp * V, 1) / np.where(cv > 0, cv, np.nan)
        ab = b["C"] > vw
    ok = pres & np.isfinite(vw)
    above += ab & ok
    count += ok
    if j % 100 == 0:
        print(j, s, round(time.time() - t0), flush=True)
with np.errstate(invalid="ignore"):
    out["breadth"] = (above / np.where(count > 0, count, np.nan)).astype(np.float32)
out["breadth_n"] = count.astype(np.float32)
spy_atr = aux["atr"][:, syms.index("SPY")].astype(np.float64)
labs, _ = turn_labels(out["SPY_H"].astype(np.float64), out["SPY_L"].astype(np.float64), 0.25 * spy_atr, tols=(0.0,))
for (side, k, tol), v in labs.items():
    out[f"spyturn_{side}_{k}"] = v
np.savez(DATA / "context.npz", **out)
print("done", round(time.time() - t0), {k: float(np.nanmean(v)) for k, v in out.items() if k.startswith("spyturn") or k == "breadth"})
