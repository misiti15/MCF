"""ER earnings study: shared data (daily arrays, events, features). See NOTES.md section 1.
Locked block 2024-11-01..2025-02-28: events whose bars R-25..R+21 touch it are dropped; no *_lockedblock file is read.
Educational only - not financial advice.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
W3 = ROOT / "research" / "swarm1010" / "w3_daily"
DATA = HERE / "data"
LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
SPLITS = {"train": ("2019-01-01", "2022-12-31"), "valid": ("2023-01-01", "2024-10-31"),
          "valid2": ("2025-03-01", "2026-12-31")}
SLIP_PS, SLIP_BPS, BORROW = 0.01, 1e-4, 0.03

raw = pd.read_parquet(W3 / "data" / "daily_2016.parquet", columns=["symbol", "date", "open", "close", "volume"])
raw["symbol"] = raw["symbol"].astype(str)
meta = pd.read_csv(W3 / "assets_meta.csv")
ETF = set(meta.loc[meta.is_etf, "symbol"])
SHORTABLE = set(meta.loc[meta.shortable.astype(bool), "symbol"])


def _wide(c):
    return raw.pivot(index="date", columns="symbol", values=c).sort_index()


C = _wide("close"); O = _wide("open"); V = _wide("volume")
del raw
dates = C.index
syms = np.array(C.columns.astype(str))
col = {s: i for i, s in enumerate(syms)}
T, NS = C.shape
Cn, On, Vn = C.to_numpy(), O.to_numpy(), V.to_numpy()
SPY = col["SPY"]
locked = np.asarray((dates >= LOCK_A) & (dates <= LOCK_B))
is_etf = np.array([s in ETF for s in syms])
adv20 = (C * V).rolling(20, min_periods=15).median().to_numpy()
vmed20 = V.rolling(20, min_periods=15).median().to_numpy()
nbars = C.notna().cumsum().to_numpy()
ELIG = (Cn >= 5) & (adv20 >= 20e6) & (nbars >= 253) & ~is_etf[None, :]
del C, O, V
# locked rows within this many sessions of an event drop it
lock_rows = np.flatnonzero(locked)


def touches_locked(a, b):
    """True where the row interval [a, b] intersects the locked block."""
    return (np.asarray(b) >= lock_rows.min()) & (np.asarray(a) <= lock_rows.max())


_EW_CACHE: dict = {}


def ew_ret(start_px: str, a: int, b: int, elig_row: int) -> float:
    """Mean return of eligible non-ETF names from price `start_px` ('C' or 'O') at row a to the close at row b."""
    key = (start_px, a, b, elig_row)
    if key not in _EW_CACHE:
        p0 = (Cn if start_px == "C" else On)[a]
        m = ELIG[elig_row] & ~np.isnan(p0) & ~np.isnan(Cn[b])
        _EW_CACHE[key] = float(np.mean(Cn[b, m] / p0[m] - 1)) if m.sum() > 50 else np.nan
    return _EW_CACHE[key]


def events(fixed_window: bool = False) -> pd.DataFrame:
    """One row per event with R and the 1.3 features. fixed_window=True: the causal diagnostic (reaction close d-1 ->
    close d+1, 'R' = d+1, REACT over two days)."""
    ec = pd.read_parquet(DATA / "earnings_cal.parquet", columns=["date", "symbol", "time"])
    ec = ec[ec.symbol.isin(col) & ~ec.symbol.isin(ETF)].copy()
    ec["d"] = np.searchsorted(dates.values, pd.to_datetime(ec["date"]).values)
    ec = ec[(ec.d >= 30) & (ec.d + 2 <= T - 1)]
    ec["j"] = ec.symbol.map(col)
    ec = ec.sort_values(["j", "d"])
    ec = ec[~(ec.groupby("j").d.diff() < 10)].copy()
    d = ec.d.to_numpy(); j = ec.j.to_numpy()
    if fixed_window:
        R = d + 1
    else:
        R = np.where(np.nan_to_num(Vn[d, j]) >= np.nan_to_num(Vn[d + 1, j]), d, d + 1)
    ec["R"] = R
    ec = ec[(R >= 25) & (R + 1 < T)].copy()
    R = ec.R.to_numpy(); j = ec.j.to_numpy(); d = ec.d.to_numpy()
    base = R - 2 if fixed_window else R - 1               # last pre-report close
    s = SPY

    def ex(a, b, pa=Cn, pb=Cn):
        return (pb[b, j] / pa[a, j] - 1) - (pb[b, s] / pa[a, s] - 1)

    ec["REACT"] = ex(base, R)
    ec["GAP"] = ex(base, base + 1, Cn, On)
    ec["INTRA"] = ex(base + 1, R, On, Cn) if not fixed_window else np.nan
    ec["RUN5"] = ex(base - 5, base)
    ec["RUN20"] = ex(base - 20, base)
    ec["elig"] = ELIG[base, j]
    ec["px"] = Cn[R, j]
    ec["date_R"] = dates[R]
    ec["locked_touch"] = touches_locked(R - 25, np.minimum(R + 21, T - 1))
    ec["REACT_feat"] = ec["REACT"].where(~touches_locked(base - 21, R))   # as a PRIOR feature: no locked bars
    ec = ec[np.isfinite(ec.REACT)].reset_index(drop=True)
    # follow-through after each event (sign of reaction x 20-day excess vs EW from C[R]); used only as a PRIOR feature
    ft = np.full(len(ec), np.nan)
    for k, (r, jj, rc) in enumerate(zip(ec.R.to_numpy(), ec.j.to_numpy(), ec.REACT.to_numpy())):
        if r + 20 < T and not touches_locked(r, r + 20) and not np.isnan(Cn[r + 20, jj]):
            ft[k] = np.sign(rc) * ((Cn[r + 20, jj] / Cn[r, jj] - 1) - ew_ret("C", r, r + 20, r))
    ec["FT"] = ft
    # previous events of the same symbol (reaction must be known before R-1; follow-through complete before R-1)
    for k in (1, 2, 3, 4):
        g = ec.groupby("j")
        pr = g.R.shift(k)
        ok = (ec.R - pr <= 400)
        ec[f"PREV{k}"] = g.REACT_feat.shift(k).where(ok)
        ec[f"FTPREV{k}"] = g.FT.shift(k).where(ok & (pr + 20 < ec.R - 1))
    ec["split"] = "none"
    for nm, (a, b) in SPLITS.items():
        ec.loc[(ec.date_R >= a) & (ec.date_R <= b), "split"] = nm
    return ec
