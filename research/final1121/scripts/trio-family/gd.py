"""Trio-family (gap-down short) siblings: signals on the lab frames, 1-minute walk, LR8 costs, testing book.
Uses research/ultimate_1119/top10/bench10.py (inbox checkout) for chain / walk / add_r / book / stats, unchanged.
Stages:  python gd.py sig [months...]   -> sig_{month}.parquet  (real signals + null rows, kind column 'grp')
         python gd.py walk              -> trades.parquet
Locked block never read (bench10 guards + asserts). Educational only - not financial advice."""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

INBOX = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox")
sys.path.insert(0, str(INBOX / "research/ultimate_1119/top10"))
sys.path.insert(0, str(INBOX))
import bench10 as B  # noqa: E402

W = Path(__file__).resolve().parent
ETFS = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLE", "XLK", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLC", "XLRE", "SMH",
        "XBI", "KRE", "XRT", "XHB", "ITB", "IYR", "KWEB", "FXI", "EEM", "EFA", "GDX", "GDXJ", "XOP", "OIH", "ARKK", "TAN",
        "IBB", "XME", "SOXX", "VNQ", "EWZ", "JETS", "KBE", "XAR", "IGV", "HYG", "TLT", "MDY", "IWD", "IWF"]
L3_GAP, L3_SLOPE, L3_FO = -2.6573517322540283, 0.37244729995727527, 3.460294628143309
NULL_REPS = 5
import os
ROUND = os.environ.get("GD_ROUND", "1")
PREFIX = "sig_" if ROUND == "1" else f"r{ROUND}sig_"


def prev_in_day(x, key, k=1):
    p = np.r_[np.full(k, np.nan), x[:-k]]
    same = np.r_[np.zeros(k, bool), key[k:] == key[:-k]]
    p[~same] = np.nan
    return p


def masks(g):
    c = lambda k: g[k].to_numpy(float)  # noqa: E731
    gap, rsi5, heat, bp, adv = c("gap"), c("rsi5"), c("heat"), c("buyPressure"), np.nan_to_num(c("adv20"))
    fo, slope, close, low, pdl = c("fromOpen"), c("sma20_slope_pct"), c("close"), c("low"), c("dist_pdl_atr")
    sym = g["symbol"].to_numpy(str)
    key = np.char.add(np.char.add(sym, "|"), g["date"].to_numpy(str))
    rw3 = (heat <= -20) & (bp < -0.35) & (rsi5 > 80) & (gap < 0)
    rw5 = (heat <= -30) & (bp < -0.15) & (rsi5 > 80) & (gap < 0)
    l3 = (gap <= L3_GAP) & (slope > L3_SLOPE) & (fo > L3_FO)
    big = adv >= 95e6
    out = {}
    for a in (20e6, 40e6):
        out[f"S1-tier2-a{int(a / 1e6)}"] = (rw3 & (adv >= a) & ~big, False)
    s2 = (gap <= L3_GAP) & (fo > L3_FO)
    out["S2-flatslope-all"] = (s2 & (slope <= L3_SLOPE), True)
    out["S2-flatslope-pos"] = (s2 & (slope <= L3_SLOPE) & (slope > 0), True)
    for G in (-1.0, -2.0):
        out[f"S3-noflow-g{abs(int(G))}"] = ((gap <= G) & (rsi5 > 80) & big & ~rw3 & ~rw5, False)
    mx = np.full(len(g), -np.inf)
    for k in range(1, 7):
        mx = np.fmax(mx, np.nan_to_num(prev_in_day(rsi5, key, k), nan=-np.inf))
    plow = prev_in_day(low, key, 1)
    for X in (60, 50):
        out[f"S4-popfail-x{X}"] = ((gap <= -1) & (adv >= 20e6) & (mx > 80) & (rsi5 < X) & (close < plow), False)
    isetf = np.isin(sym, ETFS)
    for G in (-0.5, -1.0):
        out[f"S5-etf-g{G:g}"] = (isetf & (gap <= G) & (rsi5 > 80), False)
    for b in (-0.15, -0.30):
        out[f"S6-pdlrej-b{abs(b):g}"] = ((gap <= -2) & (rsi5 > 70) & (pdl >= b) & (pdl <= 0.05), False)
    trio = l3 | ((rw3 | rw5) & big)
    if ROUND == "2":
        up = slope > L3_SLOPE
        op = close / (1 + fo / 100)
        rec_atr = (close - op) / c("atr_d")
        out = {"REF-L3": (l3, True)}
        for lo in (2.0, 2.7):
            out[f"R2a-midrec-f{lo:g}"] = ((gap <= L3_GAP) & up & (fo > lo) & (fo <= L3_FO), True)
        for F in (2.5, 3.46):
            out[f"R2b-smallgap-f{F:g}"] = ((gap > L3_GAP) & (gap <= -1.5) & up & (fo > F), True)
        for k in (0.6, 0.9):
            out[f"R2c-atrrec-k{k:g}"] = ((gap <= L3_GAP) & up & (fo <= L3_FO) & (rec_atr >= k), True)
    return out, trio, key


def build(g, cfg, mk, refire, rng, null=True):
    """g sorted symbol,date,tod (09:50-15:00). Returns signal rows (+ null rows) for one config."""
    tod = g["tod"].to_numpy(int)
    atr = g["atr_d"].to_numpy(float)
    ok = mk & (tod >= 950) & (tod <= 1500) & (atr > 0)
    hit = np.flatnonzero(ok)
    if not len(hit):
        return None
    sy = g["symbol"].astype(str).to_numpy()
    dt = g["date"].astype(str).to_numpy()
    idx = hit[B.chain(sy[hit], dt[hit], tod[hit], refire, 1)]
    return rows_at(g, idx, cfg, "real", rng, null)


def rows_at(g, idx, cfg, grp, rng, null):
    tod = g["tod"].to_numpy(int)
    atr = g["atr_d"].to_numpy(float)
    c = g["close"].to_numpy(float)
    gap = g["gap"].to_numpy(float)
    sy = g["symbol"].astype(str).to_numpy()
    dt = g["date"].astype(str).to_numpy()

    def mk(ix, gname, rep):
        e = c[ix]
        R = 0.25 * atr[ix]
        return pd.DataFrame({"cfg": cfg, "grp": gname, "rep": rep, "symbol": sy[ix], "date": dt[ix], "tod": tod[ix],
                             "side": -1, "entry": e, "stop": e + R, "tgt": e - R, "risk": R, "gap": gap[ix]})
    out = [mk(idx, grp, 0)]
    if null:
        key = np.char.add(np.char.add(sy, "|"), dt)
        starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
        ends = np.r_[starts[1:], len(key)]
        q = np.searchsorted(starts, idx, side="right") - 1
        lo, hi = starts[q], ends[q]
        for rep in range(1, NULL_REPS + 1):
            a = lo + (rng.random(len(idx)) * (hi - lo)).astype(int)
            a = a[(tod[a] >= 950) & (tod[a] <= 1500) & (atr[a] > 0)]
            out.append(mk(a, "null_any", rep))
            p = idx + rng.integers(1, 7, len(idx))
            okp = (p < hi) & (tod[np.minimum(p, len(tod) - 1)] <= 1500)
            p = p[okp]
            out.append(mk(p, "null_post", rep))
    return pd.concat(out, ignore_index=True)


def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    cols = ["symbol", "date", "tod", "close", "low", "high", "rsi5", "heat", "buyPressure", "gap", "fromOpen", "atr_d",
            "sma20_slope_pct", "dist_pdl_atr", "adv20"]
    f = lib.load_month(month, columns=cols)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    B.no_locked(f["date"].unique())
    f = f[(f.tod >= 950) & (f.tod <= 1500)].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    rng = np.random.default_rng(abs(hash(month)) % (2 ** 32))
    ms, trio, key = masks(f)
    out = []
    for cfg, (mk, refire) in ms.items():
        o = build(f, cfg, mk, refire, rng)
        if o is not None:
            out.append(o)
    if ROUND != "1":
        o = pd.concat(out, ignore_index=True)
        o = o[(o.risk > 0) & np.isfinite(o.risk)].reset_index(drop=True)
        B.no_locked(o["date"].unique())
        o.to_parquet(W / f"{PREFIX}{month}.parquet")
        return month, o[o.grp == "real"].groupby("cfg").size().to_dict()
    # S7: trio union, first signal per symbol-day, delayed D bars inside the same symbol-day
    tod = f["tod"].to_numpy(int)
    hit = np.flatnonzero(trio & (f["atr_d"].to_numpy(float) > 0))
    if len(hit):
        first = hit[np.r_[True, key[hit][1:] != key[hit][:-1]]]
        for D in (3, 6):
            j = first + D
            ok = (j < len(f))
            j, fi = j[ok], first[ok]
            ok = (key[j] == key[fi]) & (tod[j] <= 1500)
            # bars must be D x 5 minutes later (no hole in the frame)
            m0 = (tod[fi] // 100) * 60 + tod[fi] % 100
            m1 = (tod[j] // 100) * 60 + tod[j] % 100
            ok &= (m1 - m0) == 5 * D
            out.append(rows_at(f, j[ok], f"S7-delay-d{D}", "real", rng, True))
    o = pd.concat(out, ignore_index=True)
    o = o[(o.risk > 0) & np.isfinite(o.risk)].reset_index(drop=True)
    B.no_locked(o["date"].unique())
    o.to_parquet(W / f"sig_{month}.parquet")
    return month, o[o.grp == "real"].groupby("cfg").size().to_dict()


def walk_job(args):
    sym, T = args
    return B.walk_trades(T, B.hist_bars(sym))


def walk(pattern="sig_*.parquet", out="trades.parquet"):
    sig = pd.concat([pd.read_parquet(p) for p in sorted(W.glob(pattern))], ignore_index=True)
    B.no_locked(sig["date"].unique())
    # dedupe identical walks (same symbol/date/tod) to save time
    u = sig[["symbol", "date", "tod", "entry", "stop", "tgt", "side"]].drop_duplicates().reset_index(drop=True)
    jobs = [(s, g) for s, g in u.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        res = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(res, columns=["i", "px", "kind", "xt"]).set_index("i")
    u = u.join(a)
    sig = sig.merge(u, on=["symbol", "date", "tod", "entry", "stop", "tgt", "side"], how="left")
    sig.to_parquet(W / out)
    print(len(sig), "rows;", len(u), "unique walks")


if __name__ == "__main__":
    st = sys.argv[1]
    if st == "sig":
        ms = sys.argv[2:]
        with Pool(2) as p:
            for r in p.imap_unordered(month_job, ms):
                print(r, flush=True)
    elif st == "walk":
        walk(*sys.argv[2:])
