"""dips1013 step 0: 5-minute bar arrays for the eligible symbol-days (open two-year history only) + market context.

The rule-19 locked block is never loaded: lib.load_month / lib.months / lib.daily refuse or skip it, and the 1-minute
cache rows of 2024-11-01..2025-02-28 are dropped right after each read (as research/bdi/indexlink/build.py).
Outputs (git-ignored) in data/:
  days.parquet   one row per eligible symbol-day (adv20 >= $95M, atr_d > 0): symbol, date, sess, atr_d, adv20, gap,
                 open (09:30), pc, pcl, trend, rv15, sector
  bars.npz       [day, 78] float32 O H L C V VW (5-minute, bar close 09:35..16:00, heat_frame VWAP), BB lower bands
                 (k 2.0 / 2.5, 20 bars of the continuous RTH series), frame rsi / rsi5 / sma20_dist_pct (09:50..15:00)
  mkt.npz        [sess, 78] SPY / QQQ / VXX 5-minute close + session low + open, sector ETF closes + opens, VXX calm flag
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT))
import lib  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402

OUT = HERE / "data"
LOCK = (np.datetime64("2024-11-01"), np.datetime64("2025-02-28"))
NM, NB = 390, 78
IX = ROOT / "research" / "bdi" / "indexlink"

DLY = lib.daily()
DATES = sorted(set(DLY["date"]))
D64 = np.array([np.datetime64(str(x)) for x in DATES])
ND = len(DATES)


def agg5(a, how):
    x = a.reshape(a.shape[0], NB, 5)
    with np.errstate(all="ignore"):
        if how == "first":
            ok = np.isfinite(x)
            i = np.argmax(ok, 2)
            v = np.take_along_axis(x, i[..., None], 2)[..., 0]
            return np.where(ok.any(2), v, np.nan)
        if how == "last":
            ok = np.isfinite(x)[..., ::-1]
            i = np.argmax(ok, 2)
            v = np.take_along_axis(x[..., ::-1], i[..., None], 2)[..., 0]
            return np.where(ok.any(2), v, np.nan)
        if how == "max":
            return np.nanmax(x, 2)
        if how == "min":
            return np.nanmin(x, 2)
        return np.nansum(x, 2)


def minutes(store, sym):
    df = store.load(sym)
    if df is None or df.empty:
        return None
    day = df.index.tz_localize(None).normalize().to_numpy().astype("datetime64[D]")
    keep = ~((day >= LOCK[0]) & (day <= LOCK[1]))                     # locked block dropped first
    df, day = df[keep], day[keep]
    m = (df.index.hour * 60 + df.index.minute).to_numpy() - 570
    di = np.searchsorted(D64, day)
    ok = (m >= 0) & (m < NM) & (di < ND)
    ok[ok] &= D64[di[ok]] == day[ok]
    df, m, di = df[ok], m[ok], di[ok]
    out = {}
    for k in ("open", "high", "low", "close", "volume"):
        a = np.full((ND, NM), np.nan)
        a[di, m] = df[k].to_numpy(float)
        out[k] = a
    return out


def five(mn):
    O, H, L, C = agg5(mn["open"], "first"), agg5(mn["high"], "max"), agg5(mn["low"], "min"), agg5(mn["close"], "last")
    V = agg5(np.nan_to_num(mn["volume"]), "sum")
    have = np.isfinite(mn["close"]).any(1)
    # empty 5-minute bins inside a session (rare at adv >= $95M): flat bar at the last close, volume 0
    Cf = pd.DataFrame(C.T).ffill().bfill().T.to_numpy()
    miss = ~np.isfinite(C)
    O, H, L, C = (np.where(miss, Cf, x) for x in (O, H, L, C))
    V = np.where(miss, 0.0, V)
    return O, H, L, C, V, have


def work(args):
    sym, sess_list = args
    store = BarStore(ROOT / "data" / "cache_hist")
    mn = minutes(store, sym)
    if mn is None:
        return sym, None
    O, H, L, C, V, have = five(mn)
    o0 = agg5(mn["open"], "first")[:, 0]
    # heat_frame VWAP: cumulative 5-minute typical price x volume per session
    typ = (H + L + C) / 3
    cv = np.cumsum(V, 1)
    with np.errstate(all="ignore"):
        VW = np.cumsum(typ * V, 1) / np.where(cv > 0, cv, np.nan)
    # Bollinger lower band on the continuous RTH 5-minute series (sessions with data, in order)
    s = np.flatnonzero(have)
    flat = pd.Series(C[s].reshape(-1))
    ma, sd = flat.rolling(20).mean().to_numpy(), flat.rolling(20).std(ddof=0).to_numpy()
    bb2 = np.full((ND, NB), np.nan); bb25 = np.full((ND, NB), np.nan)
    bb2[s] = (ma - 2.0 * sd).reshape(len(s), NB)
    bb25[s] = (ma - 2.5 * sd).reshape(len(s), NB)
    # first session after the dropped block: no warm-up across the gap
    after = np.flatnonzero(D64 > LOCK[1])
    if len(after):
        bb2[after[0], :20] = np.nan; bb25[after[0], :20] = np.nan
    # capitulation volume: 09:30-09:45 volume vs the mean of the prior 20 sessions with data (same window)
    v15 = np.where(have, np.nansum(np.nan_to_num(mn["volume"][:, :15]), 1), np.nan)
    vs = pd.Series(v15[s])
    rv = np.full(ND, np.nan)
    rv[s] = (vs / vs.shift(1).rolling(20, min_periods=15).mean()).to_numpy()
    si = np.array(sess_list, int)
    f32 = lambda a: a[si].astype(np.float32)
    return sym, {"O": f32(O), "H": f32(H), "L": f32(L), "C": f32(C), "V": f32(V), "VW": f32(VW), "BB2": f32(bb2),
                 "BB25": f32(bb25), "open0": o0[si], "rv15": rv[si], "have": have[si]}


def main():
    OUT.mkdir(exist_ok=True)
    sidx = {d: i for i, d in enumerate(DATES)}
    # eligible symbol-days + frame columns (09:50..15:00)
    parts = []
    for m in lib.months():
        assert m not in lib.LOCKED_MONTHS
        f = lib.load_month(m, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "rsi", "rsi5", "sma20_dist_pct",
                               "vwapDistPct", "fromOpen", "dist_pdh_atr", "dist_pdl_atr"])
        f = f[(f.adv20 >= 95e6) & (f.atr_d > 0)]
        parts.append(f)
        print(m, len(f), flush=True)
    F = pd.concat(parts, ignore_index=True)
    F["symbol"] = F["symbol"].astype(str)
    F["sess"] = F["date"].map(sidx)
    assert F["sess"].notna().all()
    first = F.groupby(["symbol", "sess"], sort=True).first().reset_index()
    days = first[["symbol", "date", "sess", "atr_d", "adv20", "gap"]].copy()
    # prior-day close location from the frame's own prior-day levels (frame-computable live)
    c, a = first["close"].to_numpy(float), first["atr_d"].to_numpy(float)
    pdh, pdl = c + first["dist_pdh_atr"].to_numpy(float) * a, c - first["dist_pdl_atr"].to_numpy(float) * a
    o_frame = c / (1 + first["fromOpen"].to_numpy(float) / 100)
    pc = o_frame / (1 + first["gap"].to_numpy(float) / 100)
    with np.errstate(all="ignore"):
        days["pcl"] = (pc - pdl) / (pdh - pdl)
    days["pc"] = pc
    days["open_frame"] = o_frame
    days = days.sort_values(["symbol", "sess"]).reset_index(drop=True)
    print("eligible symbol-days", len(days), flush=True)

    # daily trend: prior close > SMA20 and SMA50 of daily closes (NaN across the dropped block)
    d = DLY.sort_values(["symbol", "date"]).copy()
    d["dt"] = pd.to_datetime(d["date"])
    g = d.groupby("symbol")
    for n, span in ((20, 35), (50, 80)):
        sma = g["close"].transform(lambda x: x.rolling(n).mean())
        first_dt = g["dt"].shift(n - 1)
        d[f"sma{n}"] = np.where((d["dt"] - first_dt).dt.days <= span, sma, np.nan)
    d["up"] = np.where(d[["sma20", "sma50"]].notna().all(1), (d.close > d.sma20) & (d.close > d.sma50), np.nan)
    d["trend"] = g["up"].shift(1)
    d.loc[(d["dt"] - g["dt"].shift(1)).dt.days > 5, "trend"] = np.nan
    days = days.merge(d[["symbol", "date", "trend"]], on=["symbol", "date"], how="left")

    lk = pd.read_csv(IX / "linkage.csv", usecols=["symbol", "sector_etf"])
    days = days.merge(lk, on="symbol", how="left")

    # bars from the 1-minute cache
    jobs = [(s, g.sess.tolist()) for s, g in days.groupby("symbol", sort=True)]
    res = {}
    with Pool(4) as p:
        for i, (sym, r) in enumerate(p.imap_unordered(work, jobs, chunksize=4)):
            res[sym] = r
            if i % 100 == 0:
                print("bars", i, len(jobs), flush=True)
    keys = ["O", "H", "L", "C", "V", "VW", "BB2", "BB25"]
    arr = {k: [] for k in keys}
    o0, rv, have = [], [], []
    for sym, g in days.groupby("symbol", sort=True):
        r = res[sym]
        n = len(g)
        if r is None:
            for k in keys:
                arr[k].append(np.full((n, NB), np.nan, np.float32))
            o0.append(np.full(n, np.nan)); rv.append(np.full(n, np.nan)); have.append(np.zeros(n, bool))
            continue
        for k in keys:
            arr[k].append(r[k])
        o0.append(r["open0"]); rv.append(r["rv15"]); have.append(r["have"])
    arr = {k: np.concatenate(v) for k, v in arr.items()}
    days["open"] = np.concatenate(o0)
    days["rv15"] = np.concatenate(rv)
    days["have"] = np.concatenate(have)

    # frame columns into [day, 78] (bar index k = (minutes since 09:35) / 5)
    tod = F["tod"].to_numpy()
    k = ((tod // 100) * 60 + tod % 100 - 575) // 5
    di = days.reset_index().set_index(["symbol", "sess"])["index"]
    row = di.reindex(pd.MultiIndex.from_arrays([F.symbol, F.sess])).to_numpy()
    for col, nm in (("rsi", "RSI14"), ("rsi5", "RSI5"), ("sma20_dist_pct", "SMA20D"), ("close", "FC"), ("vwapDistPct", "FVD")):
        a = np.full((len(days), NB), np.nan, np.float32)
        a[row, k] = F[col].to_numpy(np.float32)
        arr[nm] = a
    # parity: rebuilt bars vs frame close / VWAP distance
    with np.errstate(all="ignore"):
        dc = np.abs(arr["C"] / arr["FC"] - 1)
        vd = np.abs((arr["C"] / arr["VW"] - 1) * 100 - arr["FVD"])
    ok = np.isfinite(dc)
    par = {"close_rel_diff_p99": float(np.nanpercentile(dc[ok], 99)), "close_match_1e-6": float((dc[ok] < 1e-6).mean()),
           "vwapdist_absdiff_p99": float(np.nanpercentile(vd[np.isfinite(vd)], 99)),
           "open_rel_diff_p99": float(np.nanpercentile(np.abs(days.open / days.open_frame - 1), 99))}
    print("parity", par, flush=True)
    del arr["FC"], arr["FVD"]
    np.savez(OUT / "bars.npz", **arr)
    days["date"] = pd.to_datetime(days["date"])
    days.to_parquet(OUT / "days.parquet", index=False)

    # market context [sess, 78] from the indexlink 1-minute ETF array (open sessions)
    meta = json.load(open(IX / "data" / "meta.json"))
    assert meta["dates"] == [str(x) for x in DATES], "session lists differ"
    z = np.load(IX / "data" / "etf1m.npz")
    syms = list(z["syms"])
    mk = {}
    for e in syms:
        i = syms.index(e)
        mn = {kk: z[kk][i].astype(float) for kk in ("open", "high", "low", "close", "volume")}
        O, H, L, C, V, have = five(mn)
        o0 = agg5(mn["open"], "first")[:, 0]
        mk[f"{e}_C"] = C.astype(np.float32)
        mk[f"{e}_LOD"] = np.fmin.accumulate(L, 1).astype(np.float32)
        mk[f"{e}_O"] = o0.astype(np.float32)
    # VXX calm: prior close <= its 20-session SMA of closes (NaN across the dropped block)
    vc = pd.Series(mk["VXX_C"][:, -1].astype(float))
    sma = vc.rolling(20).mean()
    span = pd.Series(pd.to_datetime(DATES)).diff(19).dt.days
    calm = np.where((span <= 35).to_numpy(), (vc <= sma).astype(float), np.nan)
    mk["VXX_calm_prior"] = np.r_[np.nan, calm[:-1]].astype(np.float32)
    gapd = np.r_[999, np.diff(pd.to_datetime(DATES)).astype("timedelta64[D]").astype(int)]
    mk["VXX_calm_prior"][gapd > 5] = np.nan
    np.savez(OUT / "mkt.npz", syms=np.array(syms), **mk)
    json.dump({"eligible_days": len(days), "sessions": ND, "parity": par}, open(OUT / "prep.json", "w"), indent=1)
    print("done")


if __name__ == "__main__":
    main()
