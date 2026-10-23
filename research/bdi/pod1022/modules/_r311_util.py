"""_r311_util - shared helpers for the pod r3_11 modules (Elder triple screen Force Index dip, Williams Will-Spread
SPY/TLT, pre-opex-week charm drift, Augen spike fade, Grimes Keltner thrust pullback, HYG credit non-confirmation).
Not a setup (no SIDE / mask).

Point-in-time inputs the scorer frame does not carry (all causal):
  * full-session 5m bars 09:35..15:00 with volume (_r37_util.vbars; previous open month as warm-up; the rule-19 locked
    block is never read), run through numba kernels that only look at bars up to the decision bar for the mask
    (exit bars are found by scanning forward from an entry, like the scorer's own path simulation).
  * daily values as of D-1's close (_r37_util.daily_tab, completed days only, restart after > 7-day gaps).
  * per (date, tod) 5m closes of any cached symbol (TLT, SPY, ...) from the _r24 bar cache, previous open month as
    warm-up.
Callers use a bar's values only on that bar or later. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _r24_bars as R24  # noqa: E402
import _r37_util as U37  # noqa: E402
import _r39_util as U39  # noqa: E402
import _cwt3_bars as C3  # noqa: E402

_LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
_MEM = {}
f, key, start, lag, base, map_day, spy_rows = (U37.f, U37.key, U37.start, U37.lag, C3.base, U37.map_day,
                                              U37.spy_rows)
vbars, to_frame, flags, run_kernel = U37.vbars, U37.to_frame, U39.flags, U39.run_kernel
daily_tab = U37.daily_tab


def months_of(df, warm=True):
    ds = pd.Series(pd.unique(pd.Series(df["date"].to_numpy()).astype(str)))
    ms = sorted(set(ds.str[:7]) - _LOCKED_MONTHS)
    if warm and ms:
        y, mo = int(ms[0][:4]), int(ms[0][5:7])
        y, mo = (y - 1, 12) if mo == 1 else (y, mo - 1)
        pm = f"{y:04d}-{mo:02d}"
        if pm not in _LOCKED_MONTHS:
            ms = [pm] + ms
    return ms


def sym_bars(df, syms):
    """r24 5m bars (symbol, dn, date str, tod, c, v) of the given symbols for the frame's months (+ warm-up month),
    sorted by symbol, dn, tod. Empty frame when nothing is cached."""
    ms = months_of(df)
    ck = ("sb", tuple(ms), tuple(sorted(syms)))
    if ck in _MEM:
        return _MEM[ck]
    for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "sb"]:
        del _MEM[kk]
    parts = []
    for m in ms:
        assert m not in _LOCKED_MONTHS
        p = R24._OUT / "bars" / f"month={m}.parquet"
        if p.exists():
            parts.append(pd.read_parquet(p, columns=["symbol", "dn", "tod", "c", "v"],
                                         filters=[("symbol", "in", list(syms))]))
    if parts:
        B = pd.concat(parts, ignore_index=True)
        B["symbol"] = B["symbol"].astype(str)
        B["dn"] = B["dn"].astype(np.int64)
        B["tod"] = B["tod"].astype(np.int64)
        B["c"] = B["c"].astype(float)
        B["v"] = B["v"].astype(float)
        B = B[B["tod"] <= 1500].sort_values(["symbol", "dn", "tod"], kind="mergesort").reset_index(drop=True)
        B["date"] = pd.to_datetime(B["dn"], unit="D").dt.strftime("%Y-%m-%d")
    else:
        B = pd.DataFrame(columns=["symbol", "dn", "tod", "c", "v", "date"])
    _MEM[ck] = B
    return B


def map_dt(df_or_X, T, cols):
    """Left-join a (date str, tod) table onto rows of a frame / vbars table, in row order."""
    k = pd.DataFrame({"date": pd.Series(df_or_X["date"].to_numpy()).astype(str).to_numpy(),
                      "tod": df_or_X["tod"].to_numpy(np.int64)})
    TT = T[["date", "tod"] + list(cols)].drop_duplicates(["date", "tod"]).copy()
    TT["tod"] = TT["tod"].astype(np.int64)
    m = k.merge(TT, on=["date", "tod"], how="left")
    assert len(m) == len(k)
    return {c: m[c].to_numpy(float) for c in cols}


def map_date(df_or_X, T, cols):
    """Left-join a (date str) table onto rows, in row order."""
    k = pd.DataFrame({"date": pd.Series(df_or_X["date"].to_numpy()).astype(str).to_numpy()})
    m = k.merge(T[["date"] + list(cols)].drop_duplicates("date"), on="date", how="left")
    assert len(m) == len(k)
    return {c: m[c].to_numpy(float) for c in cols}


def daily_of(sym, cols):
    """Per date str: daily_tab values (as of D-1) of one symbol."""
    t = daily_tab()
    return t[t["symbol"] == sym][["date"] + list(cols)].reset_index(drop=True)


def exit_from_tod(f_, i, xt):
    """Frame row of the same symbol-day as row i whose tod >= xt (first one after i); -1 if none / NaN."""
    if not np.isfinite(xt):
        return -1
    sym, d = f_["symbol"].iat[i], f_["date"].iat[i]
    tod = f_["tod"].to_numpy(np.int64)
    n = len(f_)
    j = i + 1
    while j < n and f_["symbol"].iat[j] == sym and f_["date"].iat[j] == d:
        if tod[j] >= xt:
            return j
        j += 1
    return -1


class Stash:
    """Per-frame arrays computed in mask(), looked up by stop_price / target_price / exit_index."""

    def __init__(self):
        self.d = {}

    def put(self, df, **arrs):
        self.d.clear()
        self.d[id(df)] = arrs

    def get(self, f_, name, mask_fn):
        s = self.d.get(id(f_))
        if s is None or len(s[name]) != len(f_):
            mask_fn(f_)
            s = self.d.get(id(f_))
        return s[name]
