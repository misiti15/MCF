"""VARIANTS vs the TOP-10 benchmark (owner 2026-11-19): every ultimate_1119 variant with a frozen rule, scored on the
IDENTICAL normal-way pipeline as bench10.py (same lab frames / cache_fresh frames, same 1-minute walk, same LR8 costs +
1.2 bp borrow, same live book: per-setup cap, <= 3 lots per symbol, price >= $5, ETB shorts, cost filter 0.15R), booked
under the DESTINATION testing-account rules (bench10.TESTING_RULES: cap 100, cf 0.15, no latch), as PLAN.md says.

Only differences from bench10 (both are what the live runner does for these modules' YAML entries):
  - the module's own WINDOW / MIN_ADV / SYMBOLS (`symbols: module`) stand in for the YAML block (no YAML exists yet);
  - YAML time_stop_min (45 by default; 30 / 20 where the frozen pick says TX30 / X20): exit at the open of the first
    1-minute bar >= entry + hold;
  - geom "hold" (ULT-02 / ULT-06): catastrophic stop 2u = 0.5 x daily ATR (YAML r_atr_frac 0.5), no target.
Refire: modules thin themselves (THIN, YAML refire true / cooldown 0), so every mask hit is a signal.
Stages: sig1 (T1 months), walk1, t2 (cache_fresh per symbol), score. Locked block never read (bench10 guards).
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bench10 as B  # noqa: E402

MOD = HERE.parent / "modules"
H5V = HERE.parent / "round5" / "hunt_volume" / "H5V.py"
# (entry name -> (module file, hold minutes)). The entry name is what the live YAML would call it (sets side / leg).
ENTRIES = {}
def _e(name, f, hold=45):
    ENTRIES[name] = (f, hold)
_e("ULT-01-gapdn-pop-fade-short", MOD / "ULT-01-gapdn-pop-fade-short.py")
_e("ULT-02-tapeflush-washout-long", MOD / "ULT-02-tapeflush-washout-long.py", 45)       # 02k TX45
_e("ULT-03-rsicollapse-dip-long-broad", MOD / "ULT-03-rsicollapse-dip-long-broad.py")
_e("ULT-04-downtape-pop-fade-short", MOD / "ULT-04-downtape-pop-fade-short.py")
for s in ("long", "short"):
    _e(f"ULT-05-{s}", MOD / "ULT-05-withgap-continuation.py")
_e("ULT-06-late-morning-turn-long", MOD / "ULT-06-late-morning-turn-long.py", 30)        # 06a TX30
_e("ULT-07-pm-volatile-dip-long", MOD / "ULT-07-pm-volatile-dip-long.py")
_e("ULT-08-pm-overbought-rollover-short", MOD / "ULT-08-pm-overbought-rollover-short.py", 20)  # 08g X20
_e("ULT-09-failed-vwap-reclaim-short", MOD / "ULT-09-failed-vwap-reclaim-short.py")
for leg in ("01", "02", "03", "04", "05", "06", "07", "08", "09"):
    _e(f"ULT-10-T50b-L{leg}", MOD / "ULT-10-regime-switch-book.py", None)               # HOLD from the module
for k in (11, 14, 16, 19, 20):     # ULT-17 needs sector columns the live runner does not build (fires nothing)
    for s in ("long", "short"):
        _e(f"ULT-{k}-{s}", MOD / f"ULT-{k}.py")
for k in (12, 13, 21, 22, 23):
    _e(f"ULT-{k}", MOD / f"ULT-{k}.py")
for s in ("long", "short"):
    _e(f"ULT-25-{s}", MOD / "ULT-25.py")
    _e(f"ULT-26-{s}", MOD / "ULT-26.py")
for leg in ("E", "M", "D"):
    _e(f"ULT-32-{leg}", MOD / "ULT-32.py")
_e("H5V-X", H5V)
_e("H5V-K", H5V)

# variant -> entries pooled (each entry is its own live setup with its own cap)
VARIANTS = {
    "ULT-01": ["ULT-01-gapdn-pop-fade-short"], "ULT-02": ["ULT-02-tapeflush-washout-long"],
    "ULT-03": ["ULT-03-rsicollapse-dip-long-broad"], "ULT-04": ["ULT-04-downtape-pop-fade-short"],
    "ULT-05": ["ULT-05-long", "ULT-05-short"], "ULT-06": ["ULT-06-late-morning-turn-long"],
    "ULT-07": ["ULT-07-pm-volatile-dip-long"], "ULT-08": ["ULT-08-pm-overbought-rollover-short"],
    "ULT-09": ["ULT-09-failed-vwap-reclaim-short"], "ULT-10": [f"ULT-10-T50b-L{x}" for x in
                                                               ("01", "02", "03", "04", "05", "06", "07", "08", "09")],
    **{f"ULT-{k}": [f"ULT-{k}-long", f"ULT-{k}-short"] for k in (11, 14, 16, 19, 20, 25, 26)},
    **{f"ULT-{k}": [f"ULT-{k}"] for k in (12, 13, 21, 22, 23)},
    "ULT-32": ["ULT-32-E", "ULT-32-M", "ULT-32-D"], "BOOK-EM": ["ULT-32-E", "ULT-32-M"],
    "leg-E": ["ULT-32-E"], "leg-M": ["ULT-32-M"], "H-V1": ["H5V-X"], "H-V2": ["H5V-K"],
}
COOLDOWN = {"ULT-02-tapeflush-washout-long": 14, "ULT-06-late-morning-turn-long": 11}   # RESULTS.md YAML


def load(name, f):
    p = Path(f)
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location("lab_" + name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def inventory():
    out = []
    for name, (f, hold) in ENTRIES.items():
        m = load(name, f)
        leg = getattr(m, "LEG", None)
        w = getattr(m, "WINDOW", None)
        if w is None and hasattr(m, "WIN") and isinstance(leg, str) and leg in m.WIN:
            w = m.WIN[leg]
        if w is None and hasattr(m, "P") and isinstance(leg, str) and leg in getattr(m, "P", {}):
            w = m.P[leg].get("win") or m.P[leg].get("window")
        w = w or (950, 1500)
        adv = getattr(m, "MIN_ADV", 0) or 0
        if isinstance(adv, dict):
            adv = adv.get(getattr(m, "UNIV", None), 0)
        if name.startswith("ULT-32-"):
            adv = m.ADV_E if leg == "E" else m.ADV_MD
        if name.startswith("H5V-"):
            adv = m.ADV_ETF if leg == "X" else m.ADV_K_EQB
        if name.startswith(("ULT-02-", "ULT-06-")):
            adv = 20e6                       # module doc: ADV20 >= $20M is the YAML min_adv
        syms = getattr(m, "SYMBOLS", None)
        syms = frozenset(syms) if syms else None
        geom = m.GEOM
        if hold is None:
            hold = int(getattr(m, "HOLD", 45))
        out.append(dict(setup=name, module=str(f), side=1 if m.SIDE == "long" else -1, geom=geom,
                        w_lo=int(w[0]), w_hi=int(w[1]), min_adv=float(adv), syms=syms, hold=int(hold),
                        cooldown=COOLDOWN.get(name),
                        struct=geom not in B.GEOMS))
    return out


def signals(f, inv, mods):
    rows = []
    for st in inv:
        m = mods[st["setup"]]
        g = f
        tod = g["tod"].to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            mk = np.asarray(m.mask(g), bool)
        adv = g["adv20"].fillna(0).to_numpy(float)
        atr = g["atr_d"].to_numpy(float)
        gap = g["gap"].to_numpy(float)
        ok = mk & (tod >= max(950, st["w_lo"])) & (tod <= min(1500, st["w_hi"])) & (adv >= st["min_adv"]) & (atr > 0)
        sy = g["symbol"].astype(str).to_numpy()
        if st["syms"] is not None:
            ok &= np.isin(sy, list(st["syms"]))
        idx = np.flatnonzero(ok)
        if not len(idx):
            continue
        dt = g["date"].astype(str).to_numpy()
        if st["cooldown"] is not None:       # modules without their own THIN: YAML refire true + refire_cooldown
            idx = idx[B.chain(sy[idx], dt[idx], tod[idx], True, st["cooldown"])]
        c = g["close"].to_numpy(float)
        s = st["side"]
        e = c[idx]
        if st["geom"] == "hold":
            stop, tgt = e - s * 0.5 * atr[idx], np.full(len(idx), np.nan)
        elif st["struct"]:
            stop, tgt = np.empty(len(idx)), np.full(len(idx), np.nan)
            key = np.char.add(np.char.add(sy, "|"), dt)
            starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
            ends = np.r_[starts[1:], len(key)]
            for j, i in enumerate(idx):
                q = np.searchsorted(starts, i, side="right") - 1
                sub = g.iloc[starts[q]:ends[q]].reset_index(drop=True)
                k = i - starts[q]
                stop[j] = float(m.stop_price(sub, k))
                if hasattr(m, "target_price"):
                    tgt[j] = float(m.target_price(sub, k, stop[j]))
        else:
            up, dn = B.GEOMS[st["geom"]]
            R = 0.25 * atr[idx]
            stop = e - s * dn * R
            tgt = e + s * up * R
        rows.append(pd.DataFrame({"setup": st["setup"], "symbol": sy[idx], "date": dt[idx], "tod": tod[idx].astype(int),
                                  "side": s, "entry": e, "stop": stop, "tgt": tgt, "risk": np.abs(e - stop),
                                  "gap": gap[idx], "hold": st["hold"]}))
    if not rows:
        return pd.DataFrame()
    o = pd.concat(rows, ignore_index=True)
    o = o[(o.risk > 0) & np.isfinite(o.risk)].reset_index(drop=True)
    B.no_locked(o["date"].unique())
    return o


def walk_trades(T, b):
    """bench10.walk_trades + the YAML time stop: exit at the open of the first 1-min bar >= entry + hold."""
    hhmm = b.index.hour * 100 + b.index.minute
    mins = b.index.hour * 60 + b.index.minute
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
        em = (r.tod // 100) * 60 + r.tod % 100
        tx = em + int(r.hold)
        live = hm >= r.tod
        early = (hm < 1555) & (mins[ix] < tx)
        sel = ix[live & early]
        after = ix[live & ~early]
        s, stop, tgt = r.side, r.stop, r.tgt
        px = None
        for k in sel:
            if (s == 1 and Lo[k] <= stop) or (s == -1 and H[k] >= stop):
                px, kd, xt = (min(O[k], stop) if s == 1 else max(O[k], stop)), 1, hhmm[k]
                break
            if tgt == tgt and ((s == 1 and H[k] >= tgt + 0.01) or (s == -1 and Lo[k] <= tgt - 0.01)):
                px, kd, xt = tgt, 2, hhmm[k]
                break
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


def month_job(args):
    month, W = args
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    inv = inventory()
    mods = {st["setup"]: load(st["setup"], st["module"]) for st in inv}
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    B.no_locked(f["date"].unique())
    o = signals(f, inv, mods)
    o.to_parquet(Path(W) / f"sig1_{month}.parquet")
    return month, len(o), o.groupby("setup").size().to_dict() if len(o) else {}


def walk1_job(args):
    sym, T = args
    return walk_trades(T, B.hist_bars(sym))


def walk1(W):
    sig = pd.concat([pd.read_parquet(p) for p in sorted(Path(W).glob("sig1*_*.parquet"))], ignore_index=True)
    B.no_locked(sig["date"].unique())
    jobs = [(s, g) for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk1_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
    sig = sig.join(a)
    sig.to_parquet(Path(W) / "trades_t1.parquet")
    print(len(sig), "T1 signals;", int((sig.kind.isna() | (sig.kind < 0)).sum()), "without 1-min path")


def t2_job(sym):
    import research.history2y.build_frames as BF
    p = B.FRESH / "1Min" / f"{sym}.parquet"
    b = pd.read_parquet(p)
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert ds.min() >= B.T2_WARM and ds.max() <= B.T2_HI and not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
    d5 = BF.resample(b, "5min")
    if len(d5) < 300:
        return sym, "short", None
    dd = BF.daily_table(b, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return sym, "noframe", None
    x = x.reset_index(names="ts")
    x = x[[c for c in x.columns if not c.startswith(("win_", "r_long", "r_short"))]]
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x["date"].astype(str)
    x = x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI)]
    if not len(x):
        return sym, "nodays", None
    if "ctx" not in B.WCTX:
        c = pd.read_parquet(B.FRESH / "ctx.parquet")
        c["date"] = c["date"].astype(str)
        B.WCTX["ctx"] = c
    f = x.drop(columns=["ts"]).merge(B.WCTX["ctx"], on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    if "inv" not in B.WCTX:
        inv = inventory()
        B.WCTX["inv"] = inv
        B.WCTX["mods"] = {st["setup"]: load(st["setup"], st["module"]) for st in inv}
    o = signals(f, B.WCTX["inv"], B.WCTX["mods"])
    if not len(o):
        return sym, "ok", o
    w = walk_trades(o, b)
    a = pd.DataFrame(w, columns=["i", "px", "kind", "xt"]).set_index("i")
    return sym, "ok", o.join(a)


def t2(W):
    syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    out, st = [], {}
    with Pool(3) as p:
        for sym, s, o in p.imap_unordered(t2_job, syms):
            st[s] = st.get(s, 0) + 1
            if o is not None and len(o):
                out.append(o)
    T = pd.concat(out, ignore_index=True)
    T.to_parquet(Path(W) / "trades_t2.parquet")
    json.dump({"symbols": len(syms), "status": st}, open(Path(W) / "t2_status.json", "w"))
    print(len(T), "T2 signals", st)


if __name__ == "__main__":
    W = Path(sys.argv[1])
    W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else [m for m in lib.months() if m not in B.LOCKED_MONTHS]
        ms = [m for m in ms if not (W / f"sig1_{m}.parquet").exists()]
        with Pool(int(sys.argv[4]) if len(sys.argv) > 4 else 2) as p:
            for r in p.imap_unordered(month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif stage == "walk1":
        walk1(W)
    elif stage == "t2":
        t2(W)
