"""PYRAMID L1 long candidates (C1 RS-RED, C2 SECTOR-LEAD-PB, C3 OR20-RECLAIM) + Primary-book proxy, on the bench10
pipeline (research/ultimate_1119/top10/bench10.py: lab frames, 1-minute walk, LR8 costs, live book rules).
Run with cwd = repo checkout (inbox).  Stages:
  python l1.py secctx               sector-ETF / SPY from-open table per (date, tod) for T1 and T2 (+ sector map, fit dates)
  python l1.py sig fit|check        signals per month (fit months or check months)
  python l1.py walk fit|check       1-minute exits
  python l1.py t2                   2023-01..2024-09 (cache_fresh) signals + exits
Educational only - not financial advice."""
from __future__ import annotations

import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(__file__).resolve().parent
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
import bench10 as B  # noqa: E402

SECT = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
PRIMARY = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
           "NM-ETF-late-dip-di-long"]
B.SETUPS = [s for s in B.SETUPS if s[0] in PRIMARY]
FIT_M = ["2024-10", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09"]
CONFIGS = {  # name: (candidate, param)
    "C1_D1": ("C1", 1.0), "C1_D2": ("C1", 2.0),
    "C2_S03": ("C2", 0.3), "C2_S06": ("C2", 0.6),
    "C3_V15": ("C3", 1.5), "C3_V25": ("C3", 2.5),
}
WIN = {"C1": (1000, 1130), "C2": (1005, 1300), "C3": (1000, 1200)}
COLS = ["symbol", "date", "tod", "close", "high", "low", "vwapDistPct", "volumeRatio", "fromOpen", "gap", "atr_d", "adv20",
        "spy_fo", "qqq_fo"]


# ------------------------------------------------------------------------------------------------ sector context
def etf_fo(path, lo, hi):
    b = pd.read_parquet(path)
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    d = pd.Series(b.index.date.astype(str), index=b.index)
    b = b[(d >= lo) & (d <= hi) & ~((d >= B.LOCK[0]) & (d <= B.LOCK[1]))]
    b["date"] = b.index.date.astype(str)
    mn = b.index.hour * 60 + b.index.minute + 1           # minute close time
    b["tod"] = (mn // 60) * 100 + mn % 60
    op = b.groupby("date").open.transform("first")
    b["fo"] = (b.close / op - 1) * 100
    x = b[(b.tod % 5 == 0)][["date", "tod", "fo"]]
    return x.set_index(["date", "tod"]).fo


def secctx():
    for tag, src, lo, hi in (("T1", B.CACHE, "2024-10-01", "2026-11-04"), ("T2", B.FRESH / "1Min", B.T2_LO, B.T2_HI)):
        cols = {e: etf_fo(src / f"{e}.parquet", lo, hi) for e in SECT + ["SPY"]}
        c = pd.DataFrame(cols).reset_index()
        B.no_locked(c.date.unique())
        c.to_parquet(W / f"secctx_{tag}.parquet")
        print(tag, c.shape)
    d = pd.read_parquet(B.DATA / "daily.parquet", columns=["symbol", "date", "close"])
    d["date"] = pd.to_datetime(d["date"]).dt.date.astype(str)
    fit = ((d.date >= "2024-10-01") & (d.date <= "2024-10-31")) | ((d.date >= "2025-03-01") & (d.date <= "2025-09-30"))
    d = d[fit]
    px = d.pivot_table(index="date", columns="symbol", values="close").sort_index()
    r = px.pct_change(fill_method=None)
    r.loc["2025-03-03"] = np.nan  # first session after the locked gap
    cm = pd.DataFrame({e: r.corrwith(r[e]) for e in SECT})
    best = cm.idxmax(axis=1)
    best[cm.max(axis=1) < 0.30] = None
    best = best[~best.index.isin(SECT + ["SPY", "QQQ"])].dropna()
    best.to_json(W / "secmap.json")
    print("sector map", best.value_counts().to_dict())


# ------------------------------------------------------------------------------------------------ candidate signals
def cand_signals(f, sec, smap, or20):
    """f: frame rows (COLS) sorted symbol,date,tod. Returns signals + random controls for every config."""
    g = f.merge(sec, on=["date", "tod"], how="left")
    g["sector"] = g.symbol.map(smap)
    S = g[SECT].to_numpy(float)
    ok = np.isfinite(S).all(1)
    top = np.full(len(g), None, object)
    top[ok] = np.array(SECT)[np.nanargmax(np.where(np.isfinite(S), S, -9e9)[ok], 1)]
    g["top"] = top
    g["topfo"] = np.nanmax(np.where(np.isfinite(S), S, -9e9), 1)
    g = g.merge(or20, on=["symbol", "date"], how="left")
    key = g.symbol + "|" + g.date
    prevc = g.close.shift(1).where(key == key.shift(1))
    base = (g.close >= 5) & (g.adv20.fillna(0) >= 2e7) & (g.atr_d > 0)
    vw = g.close / (1 + g.vwapDistPct / 100)
    out = []
    rng = np.random.default_rng(20261124)
    for name, (c, p) in CONFIGS.items():
        lo, hi = WIN[c]
        inw = base & (g.tod >= lo) & (g.tod <= hi)
        if c == "C1":
            m = inw & (g.qqq_fo <= -0.30) & (g.fromOpen > 0) & (g.vwapDistPct > 0) & (g.fromOpen - g.qqq_fo >= p)
        elif c == "C2":
            m = inw & g.sector.notna() & (g.sector == g.top) & (g.topfo - g.SPY >= p) & (g.fromOpen > 0) & \
                (g.low <= vw * 1.001) & (g.close > vw)
        else:
            m = inw & g.or20h.notna() & (g.close > g.or20h) & (prevc <= g.or20h) & (g.volumeRatio >= p) & \
                (g.fromOpen > 0) & (g.vwapDistPct > 0)
        h = g[m.fillna(False).to_numpy()]
        h = h.drop_duplicates(["symbol", "date"], keep="first")
        if not len(h):
            continue
        sig = pd.DataFrame({"cfg": name, "kind_": "sig", "symbol": h.symbol, "date": h.date, "tod": h.tod.astype(int),
                            "entry": h.close, "risk": 0.25 * h.atr_d, "gap": h.gap})
        # random control: one random in-window bar of the same symbol-day
        e = g[inw.to_numpy()][["symbol", "date", "tod", "close", "atr_d", "gap"]]
        e = e.merge(h[["symbol", "date"]], on=["symbol", "date"])
        e["u"] = rng.random(len(e))
        e = e.sort_values("u").drop_duplicates(["symbol", "date"])
        ctl = pd.DataFrame({"cfg": name, "kind_": "ctl", "symbol": e.symbol, "date": e.date, "tod": e.tod.astype(int),
                            "entry": e.close, "risk": 0.25 * e.atr_d, "gap": e.gap})
        out += [sig, ctl]
    if not out:
        return pd.DataFrame()
    o = pd.concat(out, ignore_index=True)
    o["side"] = 1
    o["stop"] = o.entry - o.risk
    return o


def or20_t1(month):
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(B.HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))],
                         columns=["symbol", "date", "tod", "h"])
    ht = ht[ht.tod <= 950]
    ht["symbol"] = ht.symbol.astype(str)
    ht["date"] = pd.to_datetime(ht.date).dt.date.astype(str)
    return ht.groupby(["symbol", "date"]).h.max().rename("or20h").reset_index()


def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    B.no_locked(f.date.unique())
    inv = B.inventory()
    mods = {st["setup"]: B.load_mod(st["setup"], st["module"]) for st in inv}
    prim = B.signals(f, f, inv, mods)
    sec = pd.read_parquet(W / "secctx_T1.parquet")
    smap = pd.read_json(W / "secmap.json", typ="series").to_dict()
    o = cand_signals(f[COLS].copy(), sec, smap, or20_t1(month))
    prim = prim.assign(cfg=prim.setup, kind_="prim")
    o = pd.concat([o, prim.drop(columns=["setup"])], ignore_index=True)
    o.to_parquet(W / f"sig_{month}.parquet")
    return month, o.groupby(["cfg", "kind_"]).size().to_dict()


def months_of(which):
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS]
    return [m for m in ms if (m in FIT_M) == (which == "fit")]


# ------------------------------------------------------------------------------------------------ exits
def expand(sig):
    """one row per geometry for candidate rows (G1 t1s1, G2 t2s1); Primary rows keep their own target."""
    c = sig[sig.kind_ != "prim"]
    p = sig[sig.kind_ == "prim"].assign(geo="P")
    a = c.assign(geo="G1", tgt=c.entry + c.risk)
    b = c.assign(geo="G2", tgt=c.entry + 2 * c.risk)
    return pd.concat([a, b, p], ignore_index=True)


def walk_job(args):
    sym, T, src = args
    if src == "T1":
        b = B.hist_bars(sym)
    else:
        b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
        b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
        b = b.sort_index()
    return B.walk_trades(T, b)


def walk(which):
    ms = months_of(which)
    sig = pd.concat([pd.read_parquet(W / f"sig_{m}.parquet") for m in ms], ignore_index=True)
    sig = expand(sig)
    B.no_locked(sig.date.unique())
    jobs = [(s, g, "T1") for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
    sig = sig.join(a)
    sig.to_parquet(W / f"trades_{which}.parquet")
    print(which, len(sig))


# ------------------------------------------------------------------------------------------------ T2
def t2_job(sym):
    import research.history2y.build_frames as BF
    p = B.FRESH / "1Min" / f"{sym}.parquet"
    b = pd.read_parquet(p)
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    d5 = BF.resample(b, "5min")
    if len(d5) < 300:
        return None
    dd = BF.daily_table(b, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return None
    x = x.reset_index(names="ts")
    x = x[[c for c in x.columns if not c.startswith(("win_", "r_long", "r_short"))]]
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x["date"].astype(str)
    x = x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI)]
    if not len(x):
        return None
    if "ctx" not in B.WCTX:
        c = pd.read_parquet(B.FRESH / "ctx.parquet")
        c["date"] = c["date"].astype(str)
        B.WCTX["ctx"] = c
        B.WCTX["sec"] = pd.read_parquet(W / "secctx_T2.parquet")
        B.WCTX["smap"] = pd.read_json(W / "secmap.json", typ="series").to_dict()
        B.WCTX["inv"] = B.inventory()
        B.WCTX["mods"] = {st["setup"]: B.load_mod(st["setup"], st["module"]) for st in B.WCTX["inv"]}
    f = x.drop(columns=["ts"]).merge(B.WCTX["ctx"], on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    hm = b.index.hour * 100 + b.index.minute
    h = b[(hm >= 930) & (hm < 950)]
    or20 = h.groupby(h.index.date.astype(str)).high.max().rename("or20h").rename_axis("date").reset_index()
    or20["symbol"] = sym
    prim = B.signals(f, f, B.WCTX["inv"], B.WCTX["mods"])
    o = cand_signals(f[COLS].copy(), B.WCTX["sec"], B.WCTX["smap"], or20)
    if len(prim):
        o = pd.concat([o, prim.assign(cfg=prim.setup, kind_="prim").drop(columns=["setup"])], ignore_index=True)
    if not len(o):
        return None
    o = expand(o).reset_index(drop=True)
    w = B.walk_trades(o, b)
    a = pd.DataFrame(w, columns=["i", "px", "kind", "xt"]).set_index("i")
    return o.join(a)


def t2():
    syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    out = []
    with Pool(3) as p:
        for o in p.imap_unordered(t2_job, syms):
            if o is not None and len(o):
                out.append(o)
    T = pd.concat(out, ignore_index=True)
    T.to_parquet(W / "trades_t2.parquet")
    print("T2", len(T))


if __name__ == "__main__":
    st = sys.argv[1]
    if st == "secctx":
        secctx()
    elif st == "sig":
        ms = [m for m in months_of(sys.argv[2]) if not (W / f"sig_{m}.parquet").exists()]
        with Pool(2) as p:
            for r in p.imap_unordered(month_job, ms):
                print(r[0], {k: v for k, v in r[1].items()}, flush=True)
    elif st == "walk":
        walk(sys.argv[2])
    elif st == "t2":
        t2()
