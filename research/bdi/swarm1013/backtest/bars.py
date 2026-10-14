"""swarm1013 backtest step 2: 5-minute bars for the signal symbol-days, closes for the correlation cap, ETF context.

Bars are rebuilt from the SIP 1-minute cache with dips1013/prep.py semantics (bar close 09:35..16:00, heat_frame VWAP);
the rule-19 locked block rows are dropped right after each read. The RW6G1 VWAP 2 SD guard is applied here with the
module's own vwap_band_block on today's bars from 09:35, then the first qualifying bar per symbol-day is kept.
Outputs in $SCR: trades0.parquet (one row per setup trade), bars.npz ([day, 78] O H L C V VW for the trade days,
day index = trades0.drow), c5.npz (5-minute closes [sym, sess, 78] of every traded symbol), mkt.npz (ETF 5-minute close
and VWAP [sess, 78]). Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT / "research" / "bdi" / "dips1013"))
sys.path.insert(0, str(ROOT))
import lib  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from signals import SCR  # noqa: E402

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
    Cf = pd.DataFrame(C.T).ffill().bfill().T.to_numpy()
    miss = ~np.isfinite(C)
    O, H, L, C = (np.where(miss, Cf, x) for x in (O, H, L, C))
    V = np.where(miss, 0.0, V)
    C = np.where(have[:, None], C, np.nan)
    return O, H, L, C, V, have


def vwap(H, L, C, V):
    typ = (H + L + C) / 3
    cv = np.cumsum(V, 1)
    with np.errstate(all="ignore"):
        return np.cumsum(typ * V, 1) / np.where(cv > 0, cv, np.nan)


def work(args):
    sym, sess = args
    store = BarStore(ROOT / "data" / "cache_hist")
    mn = minutes(store, sym)
    if mn is None:
        return sym, None
    O, H, L, C, V, have = five(mn)
    VW = vwap(H, L, C, V)
    o0 = agg5(mn["open"], "first")[:, 0]
    si = np.array(sess, int)
    return sym, {"O": O[si].astype(np.float32), "H": H[si].astype(np.float32), "L": L[si].astype(np.float32),
                 "C": C[si].astype(np.float32), "V": V[si].astype(np.float32), "VW": VW[si].astype(np.float32),
                 "open0": o0[si], "have": have[si], "C5": C.astype(np.float32)}


def main():
    sig = pd.read_parquet(SCR / "signals.parquet")
    sidx = {pd.Timestamp(d): i for i, d in enumerate(DATES)}
    sig["sess"] = sig["date"].map(sidx)
    assert sig["sess"].notna().all()
    sig["sess"] = sig["sess"].astype(int)
    days = sig[["symbol", "sess"]].drop_duplicates().sort_values(["symbol", "sess"]).reset_index(drop=True)
    days["drow"] = np.arange(len(days))
    print("signal rows", len(sig), "symbol-days", len(days), "symbols", days.symbol.nunique(), flush=True)
    jobs = [(s, g.sess.tolist()) for s, g in days.groupby("symbol", sort=True)]
    res = {}
    with Pool(4) as p:
        for i, (sym, r) in enumerate(p.imap_unordered(work, jobs, chunksize=2)):
            res[sym] = r
            if i % 100 == 0:
                print("bars", i, len(jobs), flush=True)
    keys = ["O", "H", "L", "C", "V", "VW"]
    arr = {k: [] for k in keys}
    o0, have, syms, c5 = [], [], [], []
    for sym, g in days.groupby("symbol", sort=True):
        r = res[sym]
        n = len(g)
        syms.append(sym)
        if r is None:
            for k in keys:
                arr[k].append(np.full((n, NB), np.nan, np.float32))
            o0.append(np.full(n, np.nan)); have.append(np.zeros(n, bool))
            c5.append(np.full((ND, NB), np.nan, np.float32))
            continue
        for k in keys:
            arr[k].append(r[k])
        o0.append(r["open0"]); have.append(r["have"]); c5.append(r["C5"])
    arr = {k: np.concatenate(v) for k, v in arr.items()}
    days["open0"] = np.concatenate(o0)
    days["have"] = np.concatenate(have)

    # parity: rebuilt 5-minute close vs the frame close at the signal bar
    t = sig.merge(days[["symbol", "sess", "drow"]], on=["symbol", "sess"])
    k = ((t["tod"] // 100) * 60 + t["tod"] % 100 - 575) // 5
    t["k"] = k.astype(int)
    rc = arr["C"][t["drow"].to_numpy(), t["k"].to_numpy()]
    rel = np.abs(rc / t["close"].to_numpy() - 1)
    par = {"close_match_1e-4": float(np.nanmean(rel < 1e-4)), "close_rel_p99": float(np.nanpercentile(rel, 99)),
           "missing": int(np.isnan(rel).sum())}
    print("parity", par, flush=True)

    # RW6G1 guard (module's vwap_band_block on today's 5-minute bars from 09:35), then first bar per symbol-day
    spec = importlib.util.spec_from_file_location("rw6g1", ROOT / "research/bdi/live1009/RW6G1-ns2-up3-vwap2sd-short.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rw = t[t.setup == "RW6G1"]
    keep = []
    for (dr), g in rw.groupby("drow"):
        bars = pd.DataFrame({"high": arr["H"][dr].astype(float), "low": arr["L"][dr].astype(float),
                             "close": arr["C"][dr].astype(float), "volume": arr["V"][dr].astype(float)})
        blk = m.vwap_band_block(bars)
        ok = g[~blk[g["k"].to_numpy()]]
        if len(ok):
            keep.append(ok.sort_values("k").index[0])
    t = pd.concat([t[t.setup != "RW6G1"], t.loc[keep]]).sort_values(["date", "k", "setup", "symbol"]).reset_index(drop=True)
    print(t.groupby("setup").size(), flush=True)
    t.to_parquet(SCR / "trades0.parquet", index=False)
    days.to_parquet(SCR / "days.parquet", index=False)
    np.savez(SCR / "bars.npz", **arr)
    np.savez(SCR / "c5.npz", syms=np.array(syms), C5=np.stack(c5))
    del c5

    # ETF context
    meta = json.load(open(IX / "data" / "meta.json"))
    assert meta["dates"] == [str(x) for x in DATES], "session lists differ"
    z = np.load(IX / "data" / "etf1m.npz")
    esyms = [str(s) for s in z["syms"]]
    mk = {}
    for i, e in enumerate(esyms):
        mn = {kk: z[kk][i].astype(float) for kk in ("open", "high", "low", "close", "volume")}
        O, H, L, C, V, hv = five(mn)
        mk[f"{e}_C"] = C.astype(np.float32)
        mk[f"{e}_VW"] = vwap(H, L, C, V).astype(np.float32)
    np.savez(SCR / "mkt.npz", syms=np.array(esyms), **mk)
    json.dump({"parity": par, "symbol_days": len(days), "trades": len(t)}, open(SCR / "bars.json", "w"), indent=1)
    print("done", flush=True)


if __name__ == "__main__":
    main()
