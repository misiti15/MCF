"""TOP-10 benchmark, the "normal filter way" (owner 2026-11-19): MCF's top 10 live setups re-scored with their LIVE
config (module mask, YAML window, min_adv on point-in-time ADV20, gap prefilter, refire chain or first hit) AND the live
account book of their home account (mcf.execution.risk / runner): per-setup open-lot cap (Primary 30, Testing 1 150,
other testing arenas 100), <= 3 lots per symbol (live.max_lots_per_symbol, same_setup_reentry), price >= $5, Primary
-2R per-setup daily latch on realized cost-R (max_setup_daily_loss_r), Testing cost filter (live.max_stop_cost_r 0.15:
(2 x (1c + 1 bp) + 2c) / risk per share), shorts easy-to-borrow (>= 90% of 26 universe snapshots, as the Workbench).
This fixes the uncapped lab pipeline of benchmark/bench.py (L3-fromopen ~98 fires/session there).

Stages (WORK = scratch dir; nothing big is written into the repo):
  python bench10.py WORK sig1      T1 signals from the lab frames (research/history2y), open months only
  python bench10.py WORK walk1     T1 exits on 1-minute bars (data/cache_hist/1Min)
  python bench10.py WORK t2        T2 2023-01-03..2024-09-13: frames built from data/cache_fresh/1Min (469 symbols),
                                   signals + 1-minute exits in one pass
  python bench10.py WORK score     book + stats + medians -> benchmark.json (this folder)
Entry = decision-bar close; exits walked minute by minute from the decision bar close: stop first (gap-through fills at
the worse of open/stop), target only when traded through by >= $0.01 (Workbench rule), flat at 15:55.
Costs (LR8 research basis, as every ultimate_1119 round): entry (1c + 1 bp) x time-of-day multiplier; exit 1c + 1 bp
except target (limit) fills; +2c on stops; x3 on the extended tier (|gap| >= 20% or price < $5); shorts + 1.2 bp of
entry notional borrow. R = per unit of risk (|entry - stop|).
Locked block 2024-11-01..2025-02-28 is NEVER read (lib refuses it; pyarrow filters + asserts on every load).
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import math
import os
import re
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads
import yaml

HERE = Path(__file__).resolve().parent
ROOT = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox")
sys.path.insert(0, str(ROOT))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402
from mcf.strategies.setups import refire_select  # noqa: E402

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
FRESH = Path("/home/user/MCF/data/cache_fresh")
HT = Path("/home/user/MCF/research/bdi/cwt/test_b/data/headtail.parquet")
TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
T2_LO, T2_HI, T2_WARM = "2023-01-03", "2024-09-13", "2022-10-03"
BORROW = 1.2e-4
GEOMS = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5), "t05s05": (0.5, 0.5)}
# (setup, config file holding its live block in its HOME account, home account). Top 10 by live total R (>= 20 trades,
# GEN-* one-day records excluded) + ST7-FD as a reference row (11th; not in the medians).
SETUPS = [
    ("NM-RWN4-ns2-spyup05-notfri-short", "account_testingf.yaml", "testingf"),
    ("CWT14-failbrk-orl-p10-long-WB5", "account_testingd.yaml", "testingd"),
    ("CWT09-gapdn-vwaploss-g10-short", "account_testing.yaml", "testing"),
]
TOP10 = [s for s, _, _ in SETUPS[:10]]
BOOK = {  # live account rules per home account (config/*.yaml as merged by mcf.config; risk.py / runner.py)
    "primary": dict(cap=30, latch=-2.0, cf=None, symcap=3),
    "testing": dict(cap=150, latch=None, cf=0.15, symcap=3),
    "testing2": dict(cap=100, latch=None, cf=0.15, symcap=3),
    "testingd": dict(cap=100, latch=None, cf=0.15, symcap=3),
    "testingf": dict(cap=100, latch=None, cf=0.15, symcap=3),
    "livelab": dict(cap=100, latch=None, cf=0.15, symcap=3),
}
TESTING_RULES = dict(cap=100, latch=None, cf=0.15, symcap=3)   # "as a testing-arena setup" view (variants land there)


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load_mod(name, module):
    p = ROOT / module
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location("t10_" + re.sub(r"\W", "_", name), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def inventory():
    out = []
    for name, f, acct in SETUPS:
        cfg = yaml.safe_load((ROOT / "config" / f).read_text())
        p = cfg["strategies"][name]
        m = load_mod(name, p["module"])
        w = p.get("window") or [950, 1500]
        geom = p.get("geom") or m.GEOM
        out.append(dict(setup=name, module=p["module"], side=1 if m.SIDE == "long" else -1, geom=geom,
                        w_lo=int(w[0]), w_hi=int(w[1]), min_adv=float(p.get("min_adv", 0) or 0),
                        refire=bool(p.get("refire", False)), cooldown=int(p.get("refire_cooldown", 1)),
                        prefilter=p.get("prefilter") or "", account=acct, cfg=f,
                        struct=geom not in GEOMS, cwt="/cwt/" in p["module"]))
    return out


def bar_no(t):
    t = np.asarray(t, int)
    return ((t // 100) * 60 + t % 100 - 570) // 5


def chain(sym, date, tod, refire, cooldown):
    key = np.char.add(np.char.add(sym.astype(str), "|"), date.astype(str))
    if not len(key):
        return np.zeros(0, int)
    starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    ends = np.r_[starts[1:], len(key)]
    if not refire:
        return starts
    b = bar_no(tod)
    out = []
    for a, e in zip(starts, ends):
        pos = {int(x): a + j for j, x in enumerate(b[a:e])}
        out.extend(pos[int(x)] for x in refire_select(list(b[a:e]), cooldown))
    return np.asarray(sorted(out), int)


def signals(f, fx, inv, mods):
    """f = frame 09:50-15:00 (lab), fx = f + 09:35-09:45 head rows (CWT modules need the opening bars, as live)."""
    rows = []
    for st in inv:
        m = mods[st["setup"]]
        g = fx if st["cwt"] else f
        if g is None or not len(g):
            continue
        tod = g["tod"].to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            mk = np.asarray(m.mask(g), bool)
        adv = g["adv20"].fillna(0).to_numpy(float)
        atr = g["atr_d"].to_numpy(float)
        gap = g["gap"].to_numpy(float)
        ok = mk & (tod >= max(950, st["w_lo"])) & (tod <= min(1500, st["w_hi"])) & (adv >= st["min_adv"]) & (atr > 0)
        pf = st["prefilter"]
        if pf.startswith("gap_le:"):
            ok &= gap <= float(pf.split(":", 1)[1])
        elif pf.startswith("gap_ge:"):
            ok &= gap >= float(pf.split(":", 1)[1])
        hit = np.flatnonzero(ok)
        if not len(hit):
            continue
        sy = g["symbol"].astype(str).to_numpy()
        dt = g["date"].astype(str).to_numpy()
        idx = hit[chain(sy[hit], dt[hit], tod[hit], st["refire"], st["cooldown"])]
        c = g["close"].to_numpy(float)
        s = st["side"]
        e = c[idx]
        if st["struct"]:
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
            up, dn = GEOMS[st["geom"]]
            R = 0.25 * atr[idx]
            stop = e - s * dn * R
            tgt = e + s * up * R
        risk = np.abs(e - stop)
        rows.append(pd.DataFrame({"setup": st["setup"], "symbol": sy[idx], "date": dt[idx], "tod": tod[idx].astype(int),
                                  "side": s, "entry": e, "stop": stop, "tgt": tgt, "risk": risk, "gap": gap[idx]}))
    if not rows:
        return pd.DataFrame()
    o = pd.concat(rows, ignore_index=True)
    o = o[(o.risk > 0) & np.isfinite(o.risk)].reset_index(drop=True)
    no_locked(o["date"].unique())
    return o


# ------------------------------------------------------------------------------------------------ T1 signals
def head_rows_t1(month, f):
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht = ht[ht["tod"] < 950].copy()
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date.astype(str)
    return pd.DataFrame({"symbol": ht["symbol"], "date": ht["date"], "tod": ht["tod"].astype(int), "close": ht["c"],
                         "high": ht["h"], "low": ht["l"], "vwapDistPct": (ht["c"] / ht["vwap"] - 1) * 100})


def with_head(f, h):
    h = h.merge(f[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="inner")
    x = pd.concat([f, h], ignore_index=True)
    return x.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


def month_job(args):
    month, W = args
    import research.history2y.lib as lib
    lib.DATA = DATA
    inv = inventory()
    mods = {st["setup"]: load_mod(st["setup"], st["module"]) for st in inv}
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    fx = with_head(f, head_rows_t1(month, f))
    o = signals(f, fx, inv, mods)
    o.to_parquet(Path(W) / f"sig1_{month}.parquet")
    return month, len(o), o.groupby("setup").size().to_dict() if len(o) else {}


# ------------------------------------------------------------------------------------------------ 1-minute walk
def walk_trades(T, b):
    """T: signals of ONE symbol; b: its 1-minute bars (tz NY index). Returns list of (i, px, kind, xt_hhmm)."""
    hhmm = b.index.hour * 100 + b.index.minute
    day = b.index.date.astype(str)
    O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    for dd in np.unique(day):
        byday[dd] = np.flatnonzero(day == dd)
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        if ix is None:
            res.append((r.Index, np.nan, -1, -1))
            continue
        hm = hhmm[ix]
        sel = ix[(hm >= r.tod) & (hm < 1555)]
        after = ix[hm >= 1555]
        s, e, stop, tgt = r.side, r.entry, r.stop, r.tgt
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
                px, kd, xt = O[after[0]], 0, 1555
            elif len(sel):
                px, kd, xt = C[sel[-1]], 0, hhmm[sel[-1]] + 1
            else:
                res.append((r.Index, np.nan, -1, -1))
                continue
        res.append((r.Index, px, kd, xt))
    return res


def hist_bars(sym):
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    L0, L1 = pd.Timestamp(LOCK[0], tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
    b = d.to_table(filter=(fld < L0) | (fld >= L1)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def walk1_job(args):
    sym, T = args
    return walk_trades(T, hist_bars(sym))


def walk1(W):
    sig = pd.concat([pd.read_parquet(p) for p in sorted(Path(W).glob("sig1_*.parquet"))], ignore_index=True)
    no_locked(sig["date"].unique())
    jobs = [(s, g) for s, g in sig.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk1_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
    sig = sig.join(a)
    sig.to_parquet(Path(W) / "trades_t1.parquet")
    print(len(sig), "T1 signals;", int((sig.kind.isna() | (sig.kind < 0)).sum()), "without 1-min path")


# ------------------------------------------------------------------------------------------------ T2 (cache_fresh)
WCTX: dict = {}


def head_rows_from_1min(sym, b):
    x = b[(b.index.hour * 100 + b.index.minute >= 930) & (b.index.hour * 100 + b.index.minute < 945 + 5)].copy()
    if not len(x):
        return pd.DataFrame()
    x["date"] = x.index.date.astype(str)
    mn = x.index.hour * 60 + x.index.minute
    x["tod"] = ((mn - 570) // 5 + 1) * 5 + 570
    x["tod"] = (x["tod"] // 60) * 100 + x["tod"] % 60
    x["pv"] = x["close"] * x["volume"]
    g = x.groupby(["date", "tod"]).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"),
                                        pv=("pv", "sum"), v=("volume", "sum")).reset_index()
    g["cpv"] = g.groupby("date").pv.cumsum()
    g["cv"] = g.groupby("date").v.cumsum()
    vw = g.cpv / g.cv.replace(0, np.nan)
    return pd.DataFrame({"symbol": sym, "date": g.date, "tod": g.tod.astype(int), "close": g.close, "high": g.high,
                         "low": g.low, "vwapDistPct": (g.close / vw - 1) * 100})


def t2_job(sym):
    import research.history2y.build_frames as BF
    p = FRESH / "1Min" / f"{sym}.parquet"
    b = pd.read_parquet(p)
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert ds.min() >= T2_WARM and ds.max() <= T2_HI and not ((ds >= LOCK[0]) & (ds <= LOCK[1])).any()
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
    x = x[(x.date >= T2_LO) & (x.date <= T2_HI)]
    if not len(x):
        return sym, "nodays", None
    if "ctx" not in WCTX:
        c = pd.read_parquet(FRESH / "ctx.parquet")
        c["date"] = c["date"].astype(str)
        WCTX["ctx"] = c
    f = x.drop(columns=["ts"]).merge(WCTX["ctx"], on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    h = head_rows_from_1min(sym, b)
    fx = with_head(f, h) if len(h) else f
    inv = inventory()
    mods = {st["setup"]: load_mod(st["setup"], st["module"]) for st in inv}
    o = signals(f, fx, inv, mods)
    if not len(o):
        return sym, "ok", o
    w = walk_trades(o, b)
    a = pd.DataFrame(w, columns=["i", "px", "kind", "xt"]).set_index("i")
    return sym, "ok", o.join(a)


def t2(W):
    syms = sorted(p.stem for p in (FRESH / "1Min").glob("*.parquet"))
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


# ------------------------------------------------------------------------------------------------ costs, book, stats
def add_r(t):
    t = t[t.kind.notna() & (t.kind >= 0)].copy()
    tier = np.where((np.abs(t.gap) >= 20) | (t.entry < 5), 3.0, 1.0)
    ecost = (0.01 + t.entry * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xcost = np.where(t.kind == 2, 0.0, 0.01 + t.px * 1e-4) + np.where(t.kind == 1, 0.02, 0.0)
    borrow = np.where(t.side < 0, BORROW * t.entry, 0.0)
    gross = t.side * (t.px - t.entry)
    t["r_gross"] = gross / t.risk
    t["r"] = (gross - tier * (ecost + xcost) - borrow) / t.risk
    t["em"] = (t.tod // 100) * 60 + t.tod % 100
    t["xm"] = (t.xt // 100) * 60 + t.xt % 100
    t["stop_cost_r"] = (2 * (0.01 + t.entry * 1e-4) + 0.02) / t.risk
    return t


def book(t, rules, etb):
    """live per-setup book, day by day, in entry order (entry minute, then symbol)."""
    t = t[t.entry >= 5.0]
    t = t[(t.side > 0) | t.symbol.map(etb).fillna(0).ge(0.9)]
    if rules["cf"] is not None:
        t = t[t.stop_cost_r <= rules["cf"]]
    if not len(t):
        return t
    t = t.sort_values(["date", "em", "symbol"], kind="mergesort").reset_index(drop=True)
    keep = np.zeros(len(t), bool)
    em, xm, sy, rr = t.em.values, t.xm.values, t.symbol.values, t.r.values
    for _, idx in t.groupby("date").indices.items():
        open_, real = [], 0.0
        for i in idx:
            still = []
            for (x, s, r) in open_:
                if x <= em[i]:
                    real += r
                else:
                    still.append((x, s, r))
            open_ = still
            if rules["latch"] is not None and real <= rules["latch"] + 1e-12:
                continue
            if len(open_) >= rules["cap"] or sum(1 for o in open_ if o[1] == sy[i]) >= rules["symcap"]:
                continue
            keep[i] = True
            open_.append((xm[i], sy[i], rr[i]))
    return t[keep].reset_index(drop=True)


def clustered_t(t):
    if len(t) < 3:
        return float("nan")
    m = t.r.mean()
    e = (t.r - m).groupby(t.date).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(t)
    return float(m / se) if se > 0 else float("nan")


def stats(t, n_sessions, spy):
    if not len(t):
        return {"trades": 0, "sessions": n_sessions, "trades_per_session": 0.0, "total_r_per_session": 0.0}
    day = t.groupby("date").r.sum()
    tot = float(t.r.sum())
    best = day.idxmax()
    ty = t.date.map(spy)
    o = {"trades": int(len(t)), "sessions": int(n_sessions), "sessions_traded": int(day.size),
         "trades_per_session": round(len(t) / n_sessions, 3), "win": round(float((t.r > 0).mean()), 3),
         "avg_r": round(float(t.r.mean()), 4), "avg_r_gross": round(float(t.r_gross.mean()), 4),
         "avg_r_wo_best_day": round(float(t.loc[t.date != best, "r"].mean()), 4) if (t.date != best).any() else None,
         "best_day": str(best), "best_day_share": round(float(day.max() / tot), 3) if tot > 0 else None,
         "total_r": round(tot, 2), "total_r_per_session": round(tot / n_sessions, 4), "worst_day": round(float(day.min()), 2),
         "t_day_clustered": round(clustered_t(t), 2), "symbols": int(t.symbol.nunique())}
    for k in ("up", "flat", "down"):
        x = t.loc[ty == k, "r"]
        o[f"avg_r_spy_{k}"] = round(float(x.mean()), 4) if len(x) else None
        o[f"n_spy_{k}"] = int(len(x))
    o["median_hold_min"] = float(np.median(t.xm - t.em))
    return o


def spy_t1():
    f = pads.field("__index_level_0__")
    b = pads.dataset(str(CACHE / "SPY.parquet"), format="parquet").to_table(
        filter=(f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b[(b.index.hour * 100 + b.index.minute >= 930) & (b.index.hour * 100 + b.index.minute < 1600)]
    b["date"] = b.index.date.astype(str)
    g = b.groupby("date").agg(o=("open", "first"), c=("close", "last"))
    g = g[g.index >= "2024-10-01"]
    no_locked(g.index)
    ret = (g.c / g.o - 1) * 100
    return pd.Series(np.where(ret >= 0.3, "up", np.where(ret <= -0.3, "down", "flat")), index=g.index)


def half(d):
    d = pd.Series(d).astype(str)
    fit = ((d >= "2024-10-01") & (d <= "2024-10-31")) | ((d >= "2025-03-01") & (d <= "2025-09-30"))
    return np.where(fit, "fit", np.where(d >= "2025-10-01", "check", "none"))


def score(W):
    etb = pd.read_parquet(HERE / "etb_rate.parquet").rate
    inv = {s["setup"]: s for s in inventory()}
    spy1 = spy_t1()
    t1_days = pd.Series(spy1.index)
    last = pd.read_parquet(Path(W) / "trades_t1.parquet", columns=["date"]).date.max()
    t1_days = t1_days[t1_days <= last]
    h1 = half(t1_days)
    nses = {"fit": int((h1 == "fit").sum()), "check": int((h1 == "check").sum())}
    nses["combined"] = nses["fit"] + nses["check"]
    spy2 = pd.read_parquet(FRESH / "spy_days.parquet")
    spy2.index = spy2.index.astype(str)
    spy2 = spy2[(spy2.index >= T2_LO) & (spy2.index <= T2_HI)]["type"]
    nses["T2"] = int(len(spy2))
    T1 = add_r(pd.read_parquet(Path(W) / "trades_t1.parquet"))
    T1["half"] = half(T1.date)
    T2 = add_r(pd.read_parquet(Path(W) / "trades_t2.parquet"))
    no_locked(T1.date.unique())
    no_locked(T2.date.unique())
    t2st = json.load(open(Path(W) / "t2_status.json"))
    out = {"note": "Educational only - not financial advice. TOP-10 benchmark, normal filter way "
                   "(research/ultimate_1119/top10/bench10.py). R after LR8-basis costs (+ borrow on shorts), 1-minute exits, "
                   "live account book of the home account.",
           "sessions": nses, "t2_universe": t2st, "setups": {}}
    keep = {}
    for s in [x for x, _, _ in SETUPS]:
        st = inv[s]
        e = {"account": st["account"], "rules": BOOK[st["account"]], "geom": st["geom"], "window": [st["w_lo"], st["w_hi"]],
             "min_adv": st["min_adv"], "refire": st["refire"], "cooldown": st["cooldown"], "prefilter": st["prefilter"],
             "side": "long" if st["side"] > 0 else "short", "in_median": s in TOP10}
        for view, rules in (("home", BOOK[st["account"]]), ("testing_rules", TESTING_RULES)):
            a = T1[T1.setup == s]
            b1 = book(a, rules, etb)
            b2 = book(T2[T2.setup == s], rules, etb)
            e[view] = {"T1_fit": stats(b1[b1.half == "fit"], nses["fit"], spy1),
                       "T1_check": stats(b1[b1.half == "check"], nses["check"], spy1),
                       "T1_combined": stats(b1[b1.half != "none"], nses["combined"], spy1),
                       "T2": stats(b2, nses["T2"], spy2)}
            e[view]["raw_signals_T1"] = int(len(a))
            e[view]["raw_signals_T2"] = int((T2.setup == s).sum())
            if view == "home":
                keep[s] = (b1, b2)
        e["T2_coverage_symbols_traded"] = e["home"]["T2"].get("symbols", 0)
        out["setups"][s] = e
    # benchmark standard = median of the top 10 (home view) per test; best also shown
    std = {}
    for test in ("T1_fit", "T1_check", "T1_combined", "T2"):
        d = {}
        for k in ("avg_r", "avg_r_wo_best_day", "total_r_per_session", "trades_per_session", "win"):
            v = [out["setups"][s]["home"][test].get(k) for s in TOP10]
            v = [x for x in v if x is not None and x == x]
            d[k] = {"median": round(float(np.median(v)), 4) if v else None, "best": round(float(max(v)), 4) if v else None,
                    "n": len(v)}
        std[test] = d
    out["standard"] = std
    (HERE / "benchmark.json").write_text(json.dumps(out, indent=1, default=float))
    pd.concat([b1.assign(test="T1") for b1, _ in keep.values()] + [b2.assign(test="T2") for _, b2 in keep.values()]).to_parquet(
        Path(W) / "booked_trades.parquet")
    for test in ("T1_fit", "T1_check", "T1_combined", "T2"):
        rows = []
        for s in [x for x, _, _ in SETUPS]:
            z = out["setups"][s]["home"][test]
            rows.append({"setup": s[:30], **{k: z.get(k) for k in ("trades", "trades_per_session", "win", "avg_r",
                                                                    "avg_r_wo_best_day", "best_day_share", "total_r_per_session",
                                                                    "worst_day", "t_day_clustered", "avg_r_spy_up",
                                                                    "avg_r_spy_flat", "avg_r_spy_down")}})
        print("==", test, nses.get(test.replace("T1_", ""), nses.get("T2")))
        print(pd.DataFrame(rows).to_string(index=False))
        print("median", {k: v["median"] for k, v in std[test].items()})


if __name__ == "__main__":
    W = Path(sys.argv[1])
    W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig1":
        import research.history2y.lib as lib
        lib.DATA = DATA
        ms = [m for m in lib.months() if m not in LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(2) as p:
            for r in p.imap_unordered(month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif stage == "walk1":
        walk1(W)
    elif stage == "t2":
        t2(W)
    elif stage == "score":
        score(W)
