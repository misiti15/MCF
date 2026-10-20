"""Vectorised 1-minute exit simulator (holdtr, time60, and t1s1/t05s1 for the parity check) for every needed entry.
Entry = open of the first 1-minute bar starting at or after the decision time (bar-close HHMM), stop checked first
inside each bar, gap through the stop fills at the open, flat at the close of the 15:55 bar. R = 0.25 x atr_d.
Production costs (common.cost_r), x tier. Educational only - not financial advice."""
import sys

import numpy as np
import pandas as pd

from common import SCR, cost_r, load_1min

MODES = ("holdtr", "time60", "t1s1", "t05s1")


def day_mats(df):
    m = (df.index.hour * 60 + df.index.minute - 570).to_numpy()
    d = pd.Index(df.index.date)
    days, di = np.unique(d, return_inverse=True)
    shp = (len(days), 390)
    out = {}
    for k in ("open", "high", "low", "close"):
        a = np.full(shp, np.nan)
        ok = (m >= 0) & (m < 390)
        a[di[ok], m[ok]] = df[k].to_numpy(float)[ok]
        out[k] = a
    return days, out


def simulate(mats, row, i0, R, mode):
    """Vectorised over entries: row (day row), i0 (entry minute index), R. Returns gross R, kind (0 time,1 stop,2 tgt)."""
    O, H, L, C = (mats[k][row] for k in ("open", "high", "low", "close"))
    E, W = O.shape
    k = np.arange(W)[None, :]
    # first valid open at or after i0
    validO = np.isfinite(O) & (k >= i0[:, None])
    has = validO.any(1)
    j0 = np.where(has, validO.argmax(1), W - 1)
    e = O[np.arange(E), j0]
    last = np.full(E, 385) if mode != "time60" else np.minimum(385, j0 + 59)
    win = (k >= j0[:, None]) & (k <= last[:, None])
    Hn = np.where(win & np.isfinite(H), H, -np.inf)
    Ln = np.where(win & np.isfinite(L), L, np.inf)
    stop0 = e - R
    if mode == "holdtr":
        best = np.maximum.accumulate(Hn, axis=1)
        bprev = np.concatenate([np.full((E, 1), -np.inf), best[:, :-1]], axis=1)
        bprev = np.maximum(bprev, e[:, None])
        stop = np.where(bprev - e[:, None] >= R[:, None], bprev - R[:, None], stop0[:, None])
    else:
        stop = np.broadcast_to(stop0[:, None], (E, W))
    hit = Ln <= stop
    tgt = None
    if mode in ("t1s1", "t05s1"):
        tgt = e + (1.0 if mode == "t1s1" else 0.5) * R
        thit = Hn >= tgt[:, None]
    else:
        thit = np.zeros_like(hit)
    any_s, any_t = hit.any(1), thit.any(1)
    ks = np.where(any_s, hit.argmax(1), W + 1)
    kt = np.where(any_t, thit.argmax(1), W + 1)
    gross = np.full(E, np.nan)
    kind = np.zeros(E, int)
    s_first = any_s & (ks <= kt)        # stop first inside a bar
    t_first = any_t & (kt < ks)
    ar = np.arange(E)
    ops = O[ar, np.minimum(ks, W - 1)]
    sp = stop[ar, np.minimum(ks, W - 1)]
    px_s = np.where(np.isfinite(ops), np.minimum(ops, sp), sp)
    gross[s_first] = ((px_s - e) / R)[s_first]
    kind[s_first] = 1
    if tgt is not None:
        opt = O[ar, np.minimum(kt, W - 1)]
        px_t = np.where(np.isfinite(opt) & (opt > tgt), opt, tgt)
        gross[t_first] = ((px_t - e) / R)[t_first]
        kind[t_first] = 2
    rest = ~(s_first | t_first)
    Cw = np.where(win & np.isfinite(C), C, np.nan)
    # last valid close inside the window
    idx = np.where(np.isfinite(Cw), k, -1).max(1)
    pc = Cw[ar, np.maximum(idx, 0)]
    gross[rest] = ((pc - e) / R)[rest]
    gross[~has | ~np.isfinite(e)] = np.nan
    return gross, kind, e


def main():
    T = pd.read_parquet(SCR / "b_trades.parquet", columns=["symbol", "date", "tod", "atr_d", "tier"])
    C = pd.read_parquet(SCR / "ctrl_rows.parquet")
    C["src"] = "ctrl"
    T["src"] = "trade"
    E = pd.read_parquet(SCR / "etf_rows.parquet", columns=["symbol", "date", "atr_d", "gap", "close"])
    E = E[E.symbol.isin(["SPXL", "TQQQ"])].drop_duplicates(["symbol", "date"])
    tods = [h * 100 + m for h in (9, 10, 11) for m in range(60) if 946 <= h * 100 + m <= 1100]
    A = E.loc[E.index.repeat(len(tods))].copy()
    A["tod"] = np.tile(tods, len(E))
    A["tier"] = 1.0
    A["src"] = "etf"
    allE = pd.concat([T, C[["symbol", "date", "tod", "atr_d", "tier", "src"]], A[["symbol", "date", "tod", "atr_d", "tier", "src"]]],
                     ignore_index=True)
    allE["date"] = pd.to_datetime(allE["date"]).dt.date
    U = allE.drop_duplicates(["symbol", "date", "tod"]).reset_index(drop=True)
    print("unique entries", len(U), flush=True)
    res = []
    for n, (sym, g) in enumerate(U.groupby("symbol", sort=True)):
        df = load_1min(sym)
        if df is None:
            continue
        days, mats = day_mats(df)
        pos = pd.Index(days).get_indexer(g["date"])
        ok = pos >= 0
        g = g[ok]
        pos = pos[ok]
        tod = g["tod"].to_numpy(int)
        i0 = (tod // 100) * 60 + tod % 100 - 570
        R = 0.25 * g["atr_d"].to_numpy(float)
        out = {"symbol": sym, "date": g["date"].to_numpy(), "tod": tod}
        for mode in MODES:
            if mode in ("t1s1", "t05s1") and not (sym in ("SPXL", "TQQQ") or n % 10 == 0):
                continue           # lab outcomes are used for t1s1/t05s1; the sim's copy is a parity sample
            gr = np.full(len(g), np.nan)
            kd = np.zeros(len(g), int)
            ep = np.full(len(g), np.nan)
            for a in range(0, len(g), 4000):
                sl = slice(a, a + 4000)
                gr[sl], kd[sl], ep[sl] = simulate(mats, pos[sl], i0[sl], R[sl], mode)
            net = gr - cost_r(kd, ep, R, tod, g["tier"].to_numpy(float))
            out["s_" + mode] = net.astype(np.float32)
        res.append(pd.DataFrame(out))
        if n % 100 == 0:
            print(n, sym, len(g), flush=True)
    S = pd.concat(res, ignore_index=True)
    S.to_parquet(SCR / "sim.parquet", index=False)
    print(S.describe().T)


if __name__ == "__main__":
    main()
