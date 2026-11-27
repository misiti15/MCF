"""PYRAMID L3: Part A (top-3 live longs + live-derived tightenings) and Part B (trend-day momentum longs).
Pre-registered in PREREG.md. Reuses research/ultimate_1119/top10/bench10.py (locked guards, frames, costs, book).
Stages: spy | sig1 | walk1 | t2br | t2 | score.   Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

INBOX = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox")
W = Path(__file__).resolve().parent / "work"
sys.path.insert(0, str(INBOX))
spec = importlib.util.spec_from_file_location("bench10", INBOX / "research/ultimate_1119/top10/bench10.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
from mcf.research.arena.indicators import compute  # noqa: E402

TZ = "America/New_York"
B.SETUPS = [("L3-gap-slope-fromopen-FD", "default.yaml", "primary"),
            ("RW3-gapdn-rsi5pop-flowsell-short-FD", "default.yaml", "primary"),
            ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "default.yaml", "primary"),
            ("NM-ETF-late-dip-di-long", "default.yaml", "primary")]
GEN = {"A1": ("research/generator/modules/GEN-261027-01-macdh-hi-late-long.py", 20e6, (1400, 1500), "t05s1"),
       "A2": ("research/generator/modules/GEN-261020-09-emadchg-hi-mid-long.py", 150e6, (1100, 1300), "holdtr"),
       "A3": ("research/generator/modules/GEN-261019-02-bbpct-lo-pm-long.py", 150e6, (1300, 1500), "t05s1")}
# config -> (random-control window, exit mode, cap minutes)
CFG = {"A1": ((1400, 1500), "t05s1", 0), "A1t": ((1400, 1500), "t05s1", 0),
       "A2": ((1100, 1300), "holdtr", 0), "A2t": ((1100, 1130), "holdtr", 0),
       "A3": ((1300, 1500), "t05s1", 0), "A3t": ((1300, 1500), "t05s1", 0),
       "B1a": ((1030, 1130), "t1s1", 45), "B1b": ((1030, 1130), "holdtr", 0),
       "B2a": ((1330, 1500), "holdtr", 0), "B2b": ((1330, 1500), "t1s1", 45),
       "B3a": ((1330, 1500), "hold", 0), "B3b": ((1330, 1500), "holdtr", 0)}


def load_mod(p):
    s = importlib.util.spec_from_file_location("m_" + Path(p).stem.replace("-", "_"), INBOX / p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ SPY state (point-in-time: bars labelled < T)
def spy_state(b):
    b = b[(b.index.hour * 100 + b.index.minute >= 930) & (b.index.hour * 100 + b.index.minute < 1600)].copy()
    b["d"] = b.index.date.astype(str)
    b["hm"] = b.index.hour * 100 + b.index.minute
    b["pv"] = b.close * b.volume
    out = []
    tods = [t for t in range(950, 1505, 5) if t % 100 < 60]
    for d, g in b.groupby("d"):
        vw = (g.pv.cumsum() / g.volume.cumsum().replace(0, np.nan)).to_numpy()
        hm, c, o = g.hm.to_numpy(), g.close.to_numpy(), g.open.iloc[0]
        mins = (hm // 100) * 60 + hm % 100
        for T in tods:
            tm = (T // 100) * 60 + T % 100
            i = np.searchsorted(mins, tm) - 1          # last bar labelled < T
            j = np.searchsorted(mins, tm - 30) - 1
            if i < 0:
                continue
            out.append((d, T, (c[i] / o - 1) * 100, (c[i] / vw[i] - 1) * 100,
                        (c[i] / c[j] - 1) * 100 if j >= 0 else np.nan))
    s = pd.DataFrame(out, columns=["date", "tod", "spy_fo1", "spy_vw", "spy30"])
    a = s[s.tod == 1030].set_index("date")
    up = (a.spy_vw > 0) & (a.spy30 > 0) & (a.spy_fo1 > 0)   # 10:30 close above VWAP, above 10:00, above open
    s["up1030"] = s.date.map(up).fillna(False).astype(bool)
    return s


def stage_spy():
    s1 = spy_state(B.hist_bars("SPY"))
    B.no_locked(s1.date.unique())
    b2 = pd.read_parquet(B.FRESH / "1Min" / "SPY.parquet")
    b2.index = pd.DatetimeIndex(b2.index).tz_convert(TZ)
    b2 = b2.sort_index()
    s2 = spy_state(b2)
    s2 = s2[(s2.date >= B.T2_LO) & (s2.date <= B.T2_HI)]
    pd.concat([s1, s2]).to_parquet(W / "spy_state.parquet")
    print(len(s1), len(s2), "UP1030 share T1", s1.groupby("date").up1030.first().mean(), "T2", s2.groupby("date").up1030.first().mean())


# ------------------------------------------------------------------ signals for all 12 configs (+ random control)
def first_hit(f, ok):
    idx = np.flatnonzero(ok)
    if not len(idx):
        return idx
    k = f["symbol"].to_numpy()[idx].astype(str).astype(object) + "|" + f["date"].to_numpy()[idx].astype(str).astype(object)
    _, first = np.unique(k, return_index=True)
    return idx[np.sort(first)]


def rows(f, idx, cfg, ctrl=0):
    if not len(idx):
        return None
    _, mode, cap = CFG[cfg]
    e = f["close"].to_numpy(float)[idx]
    R = 0.25 * f["atr_d"].to_numpy(float)[idx]
    up = {"t05s1": 0.5, "t1s1": 1.0}.get(mode, np.nan)
    return pd.DataFrame({"cfg": cfg, "ctrl": ctrl, "symbol": f["symbol"].to_numpy()[idx].astype(str),
                         "date": f["date"].to_numpy()[idx].astype(str), "tod": f["tod"].to_numpy()[idx].astype(int),
                         "side": 1, "entry": e, "stop": e - R, "tgt": e + up * R, "risk": R,
                         "gap": f["gap"].to_numpy(float)[idx], "mode": mode, "cap": cap})


def control(f, sel, cfg, rng):
    """random bar in the config's window on the same symbol-days."""
    if sel is None or not len(sel):
        return None
    lo, hi = CFG[cfg][0]
    tod = f["tod"].to_numpy()
    key = f["symbol"].astype(str) + "|" + f["date"].astype(str)
    want = set(sel.symbol + "|" + sel.date)
    cand = np.flatnonzero(key.isin(want).to_numpy() & (tod >= lo) & (tod <= hi) & (f["atr_d"].to_numpy(float) > 0))
    if not len(cand):
        return None
    ck = key.to_numpy()[cand]
    pick = []
    for k, grp in pd.Series(cand).groupby(ck):
        pick.append(int(rng.choice(grp.to_numpy())))
    return rows(f, np.asarray(sorted(pick)), cfg, ctrl=1)


def all_signals(f, spy, mods, rng):
    f = f.merge(spy, on=["date", "tod"], how="left")
    tod = f["tod"].to_numpy()
    adv = f["adv20"].fillna(0).to_numpy(float)
    atr = f["atr_d"].to_numpy(float)
    c = f["close"].to_numpy(float)
    X = compute(f, names=["new_hod", "fromOpen_atr", "volumeRatio", "vwapDistPct", "dist_hod_atr"], context=False)
    nh, foa, vr, vwd, dh = (X[k].to_numpy(float) for k in ("new_hod", "fromOpen_atr", "volumeRatio", "vwapDistPct", "dist_hod_atr"))
    svw, s30, sfo, up = (f[k].to_numpy(float) for k in ("spy_vw", "spy30", "spy_fo1", "up1030"))
    up = up == 1
    qfo = f["qqq_fo"].to_numpy(float) if "qqq_fo" in f else np.full(len(f), np.nan)
    out = []
    with np.errstate(invalid="ignore"):
        for a, (p, mad, (lo, hi), geom) in GEN.items():
            base = np.asarray(mods[a].mask(f), bool) & (tod >= lo) & (tod <= hi) & (adv >= mad) & (atr > 0) & (c >= 5)
            tight = {"A1": base & (s30 > 0) & (adv >= 100e6),
                     "A2": base & (tod <= 1130) & (qfo <= -1.0),
                     "A3": base & (svw >= -0.3) & (c <= 50)}[a]
            for cfg, ok in ((a, base), (a + "t", tight)):
                r = rows(f, first_hit(f, ok), cfg)
                out += [r, control(f, r, cfg, rng)]
        uni = (adv >= 50e6) & (c >= 10) & (atr > 0)
        b1 = uni & up & (tod >= 1030) & (tod <= 1130) & (nh == 1) & (vr >= 2.0) & (foa >= 0.5) & (vwd > 0)
        b2 = uni & (tod >= 1330) & (tod <= 1500) & (svw > 0) & (sfo >= 0.3) & (foa >= 1.0) & (nh == 1) & (vr >= 1.5)
        b3 = uni & up & (tod == 1430) & (svw > 0) & (sfo >= 0.3) & (foa >= 1.0) & (vwd > 0) & (dh <= 0.25)
        for cfgs, ok in ((("B1a", "B1b"), b1), (("B2a", "B2b"), b2), (("B3a", "B3b"), b3)):
            idx = first_hit(f, ok)
            for cfg in cfgs:
                r = rows(f, idx, cfg)
                out += [r, control(f, r, cfg, rng)]
    out = [o for o in out if o is not None and len(o)]
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    rng = np.random.default_rng(__import__("zlib").crc32(month.encode()))
    spy = pd.read_parquet(W / "spy_state.parquet")
    mods = {a: load_mod(v[0]) for a, v in GEN.items()}
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    B.no_locked(f["date"].unique())
    o = all_signals(f, spy, mods, rng)
    # Primary reference book (bench10 live config signals)
    inv = B.inventory()
    pm = {st["setup"]: B.load_mod(st["setup"], st["module"]) for st in inv}
    fx = B.with_head(f, B.head_rows_t1(month, f))
    p = B.signals(f, fx, inv, pm)
    if len(p):
        p = p.rename(columns={"setup": "cfg"}).assign(ctrl=0, mode="fix", cap=0)
        o = pd.concat([o, p], ignore_index=True)
    B.no_locked(o["date"].unique())
    o.to_parquet(W / f"sig1_{month}.parquet")
    return month, len(o)


def stage_sig1():
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
    with Pool(2) as p:
        for r in p.imap_unordered(month_job, ms):
            print(r, flush=True)


# ------------------------------------------------------------------ 1-minute exits
def walk(T, b):
    hhmm = b.index.hour * 100 + b.index.minute
    mins = (hhmm // 100) * 60 + hhmm % 100
    day = b.index.date.astype(str)
    O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {dd: np.flatnonzero(day == dd) for dd in np.unique(day)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        if ix is None:
            res.append((r.Index, np.nan, -1, -1))
            continue
        hm = hhmm[ix]
        tm = (r.tod // 100) * 60 + r.tod % 100
        end = min(955, tm + r.cap) if r.cap else 955          # 15:55 = 955 minutes
        sel = ix[(hm >= r.tod) & (mins[ix] < end)]
        after = ix[mins[ix] >= end]
        e, R, stop, tgt = r.entry, r.risk, r.stop, r.tgt
        trail = r.mode == "holdtr"
        hh = -np.inf
        px = None
        for k in sel:
            if Lo[k] <= stop:
                px, kd, xt = min(O[k], stop), 1, hhmm[k]
                break
            if tgt == tgt and H[k] >= tgt + 0.01:
                px, kd, xt = tgt, 2, hhmm[k]
                break
            if trail:
                hh = max(hh, H[k])
                if hh >= e + R:
                    stop = max(stop, hh - R)
        if px is None:
            if len(after):
                px, kd, xt = O[after[0]], 0, hhmm[after[0]]
            elif len(sel):
                px, kd, xt = C[sel[-1]], 0, hhmm[sel[-1]] + 1
            else:
                res.append((r.Index, np.nan, -1, -1))
                continue
        res.append((r.Index, px, kd, xt))
    return res


def walk1_job(args):
    sym, T = args
    return walk(T, B.hist_bars(sym))


def stage_walk1():
    sig = pd.concat([pd.read_parquet(p) for p in sorted(W.glob("sig1_*.parquet"))], ignore_index=True)
    B.no_locked(sig["date"].unique())
    sig["mode"] = sig["mode"].fillna("fix")
    sig["cap"] = sig["cap"].fillna(0).astype(int)
    jobs = [(s, g) for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk1_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
    sig = sig.join(a)
    sig.to_parquet(W / "trades_t1.parquet")
    print(len(sig), "T1 rows")


# ------------------------------------------------------------------ T2 (2023-24): breadth pass, then signals + walk
def br_job(sym):
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1500)].copy()
    b["d"] = b.index.date.astype(str)
    b["pv"] = b.close * b.volume
    vw = b.groupby("d").pv.cumsum() / b.groupby("d").volume.cumsum().replace(0, np.nan)
    mn = b.index.hour * 60 + b.index.minute
    tod = ((mn - 570) // 5 + 1) * 5 + 570
    tod = (tod // 60) * 100 + tod % 60
    x = pd.DataFrame({"date": b.d.values, "tod": np.asarray(tod), "above": (b.close / vw > 1).values.astype(float)})
    x = x.groupby(["date", "tod"]).above.last().reset_index()
    return x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI) & (x.tod >= 950)]


def stage_t2br():
    syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    with Pool(3) as p:
        parts = list(p.imap_unordered(br_job, syms, chunksize=8))
    x = pd.concat(parts).groupby(["date", "tod"]).above.mean().rename("breadth").reset_index()
    x.to_parquet(W / "t2_breadth.parquet")
    print(len(x), x.breadth.describe())


WC: dict = {}


def t2_job(sym):
    import research.history2y.build_frames as BF
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert ds.min() >= B.T2_WARM and ds.max() <= B.T2_HI and not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
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
    if "ctx" not in WC:
        c = pd.read_parquet(B.FRESH / "ctx.parquet")
        c["date"] = c["date"].astype(str)
        br = pd.read_parquet(W / "t2_breadth.parquet")
        WC["ctx"] = c.merge(br, on=["date", "tod"], how="left")
        WC["spy"] = pd.read_parquet(W / "spy_state.parquet")
        WC["mods"] = {a: load_mod(v[0]) for a, v in GEN.items()}
    f = x.drop(columns=["ts"]).merge(WC["ctx"], on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    o = all_signals(f, WC["spy"], WC["mods"], np.random.default_rng(__import__("zlib").crc32(sym.encode())))
    if not len(o):
        return None
    w = walk(o, b)
    return o.join(pd.DataFrame(w, columns=["i", "px", "kind", "xt"]).set_index("i"))


def stage_t2():
    syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    out = []
    with Pool(3) as p:
        for o in p.imap_unordered(t2_job, syms):
            if o is not None and len(o):
                out.append(o)
    T = pd.concat(out, ignore_index=True)
    T.to_parquet(W / "trades_t2.parquet")
    print(len(T), "T2 rows")


if __name__ == "__main__":
    W.mkdir(exist_ok=True)
    {"spy": stage_spy, "sig1": stage_sig1, "walk1": stage_walk1, "t2br": stage_t2br, "t2": stage_t2}[sys.argv[1]]()
