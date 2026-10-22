"""ns3var1022: assemble the candidate table (scan.py) + daily features (real prior days only) + regime labels +
same-minute controls; and the as-run machinery (refire chain, lot cap). Educational only - not financial advice."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from nv import G21SCR, HERE, NV, RG22, ROOT, lib, no_locked, split_of

sys.path.insert(0, str(ROOT / "research" / "bdi" / "regime1022" / "scripts"))
from mcf.strategies.setups import refire_select  # noqa: E402

PATHK = ("h", "l", "c", "t", "v")


def load_cand():
    tabs, P, Q = [], {k: [] for k in PATHK}, {k: [] for k in PATHK}
    for p in sorted((NV / "cand").glob("*.npz")):
        z = np.load(p, allow_pickle=False)
        cols = {k: z[k] for k in z.files if not (k[0] in "PQ" and k[1:] in PATHK)}
        tabs.append(pd.DataFrame(cols))
        for k in PATHK:
            P[k].append(z["P" + k])
            Q[k].append(z["Q" + k])
    df = pd.concat(tabs, ignore_index=True)
    P = {k: np.vstack(v).astype(float) for k, v in P.items()}
    Q = {k: np.vstack(v).astype(float) for k, v in Q.items()}
    df["date"] = pd.to_datetime(df["date"]).dt.date
    no_locked(df["date"].unique())
    append_tail(P, df["symbol"].to_numpy(), df["date"].astype(str).to_numpy(), df["tod"].to_numpy(float))
    append_tail(Q, df["p_symbol"].to_numpy(), df["date"].astype(str).to_numpy(), df["tod"].to_numpy(float))
    return df, P, Q


_TAIL = None


def append_tail(P, syms, dates, tod0):
    """Append the 15:05..15:55 bars (tail.py, from the 1-minute cache) after the last stored frame bar."""
    global _TAIL
    if _TAIL is None:
        t = pd.read_parquet(NV / "tail.parquet")
        no_locked(t["date"].unique())
        t = t.sort_values(["symbol", "date", "tod"])
        _TAIL = {k: (g["tod"].to_numpy(float), g["high"].to_numpy(float), g["low"].to_numpy(float),
                     g["close"].to_numpy(float)) for k, g in t.groupby(["symbol", "date"], sort=False)}
    n, m = P["c"].shape
    nfin = np.isfinite(P["c"]).sum(1)
    for i in range(n):
        tl = _TAIL.get((syms[i], dates[i]))
        if tl is None:
            continue
        k = int(nfin[i])
        last = P["t"][i, k - 1] if k else tod0[i]
        sel = tl[0] > last
        q = int(sel.sum())
        if not q:
            continue
        q = min(q, m - k)
        P["t"][i, k:k + q] = tl[0][sel][:q]
        P["h"][i, k:k + q] = tl[1][sel][:q]
        P["l"][i, k:k + q] = tl[2][sel][:q]
        P["c"][i, k:k + q] = tl[3][sel][:q]


def daily_feats() -> pd.DataFrame:
    """Per symbol-date features known at that date's open: 20-session return to the PRIOR close, 60-session beta to
    SPY on prior daily returns, prior close. Returns across the locked gap (> 5 calendar days) are NaN."""
    d = lib.daily()[["symbol", "date", "close"]].copy()
    d = d.sort_values(["symbol", "date"])
    dd = pd.to_datetime(d["date"])
    gap = dd.groupby(d["symbol"]).diff().dt.days > 5
    d["ret"] = d.groupby("symbol")["close"].pct_change()
    d.loc[gap.to_numpy(), "ret"] = np.nan
    spy = d[d["symbol"] == "SPY"].set_index("date")["ret"]
    d["spy_ret"] = d["date"].map(spy)
    g = d.groupby("symbol", group_keys=False)
    # 20-session return ending at the prior close (window must not cross the locked gap: sum of log returns)
    d["lr"] = np.log1p(d["ret"])
    d["ret20"] = g["lr"].transform(lambda x: x.shift(1).rolling(20, min_periods=20).sum())
    d["ret20"] = np.expm1(d["ret20"]) * 100

    def beta(x):
        y, m = x["ret"].shift(1), x["spy_ret"].shift(1)
        cov = (y * m).rolling(60, min_periods=40).mean() - y.rolling(60, min_periods=40).mean() * m.rolling(60, min_periods=40).mean()
        var = (m * m).rolling(60, min_periods=40).mean() - m.rolling(60, min_periods=40).mean() ** 2
        return cov / var

    d["beta60"] = d.groupby("symbol", group_keys=False).apply(beta)
    d["prev_close"] = g["close"].shift(1)
    return d[["symbol", "date", "ret20", "beta60", "prev_close"]]


def day_table():
    import regime  # regime1022/scripts/regime.py (reads $G21SCR/idx_live_daily.parquet via rc)
    return regime.day_table()


def controls() -> pd.DataFrame:
    c = pd.concat([pd.read_parquet(p) for p in sorted((G21SCR / "ctrl").glob("*.parquet"))], ignore_index=True)
    c["date"] = pd.to_datetime(c["date"]).dt.date
    no_locked(c["date"].unique())
    return c


def bar_no(tod) -> np.ndarray:
    t = np.asarray(tod, int)
    return ((t // 100) * 60 + t % 100 - 9 * 60 - 30) // 5


def chain(sym, date, tod, refire=True, cooldown=1, first_only=False) -> np.ndarray:
    """Boolean keep over rows already sorted by (symbol, date, tod): LabStrategy refire chain."""
    key = pd.Series(sym).astype(str).to_numpy() + "|" + pd.Series(date).astype(str).to_numpy()
    keep = np.zeros(len(key), bool)
    if not len(key):
        return keep
    brk = np.r_[True, key[1:] != key[:-1]]
    starts = np.flatnonzero(brk)
    ends = np.r_[starts[1:], len(key)]
    b = bar_no(tod)
    for a, e in zip(starts, ends):
        if first_only or not refire:
            keep[a] = True
            continue
        sel = set(refire_select(list(b[a:e]), cooldown))
        for j in range(a, e):
            if b[j] in sel:
                keep[j] = True
                sel.discard(b[j])
    return keep


def lot_cap(dates, tods, syms, exits, cap=3) -> np.ndarray:
    """Per-setup open-lot cap per symbol; a lot is open while exit tod > entry tod (regime1022 asrun.sequence)."""
    keep = np.zeros(len(dates), bool)
    order = np.lexsort((syms, tods, dates))
    cur_d, lots = None, []
    for i in order:
        if dates[i] != cur_d:
            cur_d, lots = dates[i], []
        t = tods[i]
        lots = [x for x in lots if x[1] > t]
        if sum(x[0] == syms[i] for x in lots) >= cap:
            continue
        keep[i] = True
        lots.append((syms[i], exits[i]))
    return keep


def build():
    df, P, Q = load_cand()
    df = df.sort_values(["symbol", "date", "tod"], kind="mergesort")
    o = df.index.to_numpy()
    df = df.reset_index(drop=True)
    P = {k: v[o] for k, v in P.items()}
    Q = {k: v[o] for k, v in Q.items()}
    fe = daily_feats()
    df = df.merge(fe, on=["symbol", "date"], how="left")
    dt = day_table()
    df = df.join(dt[["regime", "o2c", "spy_prev"]], on="date")
    c = controls()
    df = df.merge(c, on=["date", "tod"], how="left")
    df["split"] = split_of(df["date"])
    df["atr_pct_d"] = df["atr_d"] / df["prev_close"] * 100
    df["rs"] = df["fromOpen"] - df["spy_fo"]
    df["dow"] = pd.to_datetime(df["date"]).dt.dayofweek
    df["p0"] = (df["sma50_dist_pct"] > 0) & (df["fromOpen"] < -2)
    return df, P, Q
