"""Mechanic GEN-261023-09: identical engine for parent and copies (both tests). SHORT, holdtr.
Signal = module conditions on the 5-minute bar close (arena compute, context=False; breadth = lab context column, share of
stocks above their session VWAP), adv20 >= $150M, price >= $5; first qualifying bar per symbol-day (refire false).
Fill = open of the 1-minute bar starting `lat` (1) minute after the signal bar closes; stop = signal close + 1R (as
LabStrategy), 1R = 0.25 x daily ATR; no target; trail 1R (of fill risk) behind the best low once +1R (holdtr: runner
trail_r / trail_after_r); flat at the 15:55 bar open. Stop checked first in each minute; the trail moves from the next
minute. R = net P/L / |fill - stop| (live R definition). Costs = LR8 production model (SEC fee + TAF on the short sale).
Testing E cost filter (max_stop_cost_r 0.15, runner._precheck: (2 x (1c + 1 bp x px) + 2c) / |px - stop|) applied by
default (cf=0.15) - the parent as it runs today. Educational only - not financial advice."""
import pickle, numpy as np, pandas as pd
from common import OUT, LOCK
from mcf.research.gates import tod_cost_mult
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
PARENT = dict(lo=1400, hi=1500, conds=(("breadth", ">", 0.7), ("ret3", ">=", 0.54)), extra=(), adv=150e6, minpx=5.0,
              lat=1, rf=0.25, sk=1.0, tk=None, trr=1.0, tra=1.0, flat=1555, mh=None, be=None, cf=0.15, daycap=None,
              cte=None, excl=None, lots=1, cool=6, conc=None)
OPS = {"<=": np.less_equal, ">=": np.greater_equal, "<": np.less, ">": np.greater, "==": np.equal}

def cost_entry(px, tod): return (0.01 + px * 1e-4) * tod_cost_mult([tod])[0] + px * 1e-4 + CAT + FEE_SEC * px + TAF
def cost_exit(px, why):
    base = 0.01 + px * 1e-4
    c = 0.0 if why == "target" else (base + max(0.02, 4e-4 * px) if why == "stop" else base + max(0.01, 1e-4 * px))
    return c + CAT
def add_min(t, k):
    h, m = divmod(int(t), 100); x = h * 60 + m + k; return (x // 60) * 100 + x % 60
def mdiff(a, b): return (a // 100 * 60 + a % 100) - (b // 100 * 60 + b % 100)

def exit_one(path, px, atr, tod, v):
    mins, o, h, l, c = path
    R0 = v["rf"] * atr; t0 = add_min(tod, v["lat"])
    i0 = np.searchsorted(mins, t0)
    if i0 >= len(mins) or mins[i0] > add_min(t0, 4): return None
    fill = o[i0]; stop = px + v["sk"] * R0; tgt = None if v["tk"] is None else px - v["tk"] * R0
    risk = stop - fill
    if risk <= 0: return dict(r=-1.0, why="gapstop", xt=int(mins[i0]), mfe=0.0, mae=-1.0, fill=fill, ent=int(mins[i0]), risk=0.0, hold=0)
    ce = cost_entry(fill, tod); cur = stop; trough = fill; peak = fill; why = None
    for i in range(i0, len(mins)):
        if mins[i] >= v["flat"] or (v["mh"] and mdiff(mins[i], mins[i0]) >= v["mh"]):
            ex, why = o[i], "time"; break
        if v["cte"] and mdiff(mins[i], mins[i0]) >= v["cte"][0] and (fill - trough) / risk < v["cte"][1]:
            ex, why = o[i], "time"; break
        if h[i] >= cur:
            ex = max(cur, o[i]) if i > i0 else cur; why = "stop" if cur > fill + 1e-9 else ("be" if cur >= fill - 1e-9 else "trail")
            peak = max(peak, h[i]); break
        if tgt is not None and l[i] <= tgt:
            ex, why = tgt, "target"; trough = min(trough, l[i]); break
        trough = min(trough, l[i]); peak = max(peak, h[i])
        if v["trr"] is not None and fill - trough >= v["tra"] * risk: cur = min(cur, trough + v["trr"] * risk)
        if v["be"] is not None and fill - trough >= v["be"] * risk: cur = min(cur, fill)
    else:
        ex, why = c[-1], "time"; i = len(mins) - 1
    pnl = fill - ex - cost_exit(ex, "stop" if why in ("be", "trail") else why) - ce
    return dict(r=pnl / risk, why=why, xt=int(mins[i]), mfe=(fill - trough) / risk, mae=(fill - peak) / risk, fill=fill,
                ent=int(mins[i0]), risk=risk, hold=mdiff(int(mins[i]), int(mins[i0])))

def select(cand, v):
    c = cand
    m = (c.tod >= v["lo"]) & (c.tod <= v["hi"]) & (c.adv20 >= v["adv"]) & (c.close >= v["minpx"]) & (c.orb_fail_dn == 1)
    for col, op, val in tuple(v["conds"]) + tuple(v["extra"]):
        a = c[col].to_numpy(float)
        with np.errstate(invalid="ignore"):
            m &= OPS[op](a, float(np.float32(val)) if col not in ("breadth", "breadth_open", "br_chg", "br950", "spy950") else val)
    if v["cf"]:
        R = v["sk"] * v["rf"] * c.atr_d
        m &= (2 * (0.01 + c.close * 1e-4) + 0.02) / R <= v["cf"]
    if v["excl"]:
        m &= ~c.symbol.isin(v["excl"])
    s = c[np.asarray(m)].sort_values(["symbol", "date", "tod"])
    return s.groupby(["symbol", "date"]).head(1)

KEEP = [k for k in ["breadth", "breadth_open", "br_chg", "br950", "spy950", "close", "atr_d", "adv20"]]

def trades(cand, paths, v):
    v = {**PARENT, **v}
    s = select(cand, v); rows = []
    for r in s.itertuples():
        p = paths.get((r.symbol, r.date))
        if p is None: continue
        x = exit_one(p, r.close, r.atr_d, r.tod, v)
        if x is None: continue
        rows.append(dict(symbol=r.symbol, date=r.date, tod=int(r.tod), idx=r.Index, **x))
    t = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["symbol", "date", "tod", "idx", "r", "why", "ent", "mfe", "mae", "hold"])
    if len(t) and v["daycap"]:
        t = t.sort_values(["date", "ent", "symbol"]).groupby("date").head(v["daycap"])
    if len(t) and v["conc"]:   # P14 open lots per setup (live max_positions_per_strategy): skip a signal while `conc` are open
        t = t.sort_values(["date", "ent", "symbol"]); keep = []
        for d, g in t.groupby("date", sort=False):
            xs = []
            for i, e, x in zip(g.index, g.ent, g.xt):
                xs = [q for q in xs if q > e]
                if len(xs) < v["conc"]: xs.append(x); keep.append(i)
        t = t.loc[keep]
    return t

def stats(t):
    if not len(t): return dict(n=0)
    d = t.groupby("date").r.sum()
    best, worst = d.idxmax(), d.idxmin()
    wo = t[t.date != best].r
    return dict(n=len(t), days=t.date.nunique(), win=round(100 * (t.r > 0).mean(), 1), avg=round(t.r.mean(), 3),
                wobest=round(wo.mean(), 3) if len(wo) else np.nan, woworst=round(t[t.date != worst].r.mean(), 3) if (t.date != worst).any() else np.nan,
                total=round(t.r.sum(), 1), worst=round(d.min(), 2), bestshare=round(d.max() / t.r.sum(), 2) if t.r.sum() > 0 else np.nan,
                avgw=round(t.r[t.r > 0].mean(), 3), avgl=round(t.r[t.r <= 0].mean(), 3), hold=float(t.hold.median()))

def paired(t, base, days):
    a = t.groupby("date").r.sum().reindex(days).fillna(0); b = base.groupby("date").r.sum().reindex(days).fillna(0)
    dd = a - b
    return round(dd.mean(), 3), (round(dd.mean() / (dd.std(ddof=1) / np.sqrt(len(days))), 2) if dd.std() > 0 else 0.0)

def load():
    C = pd.read_parquet(OUT + "cand2y.parquet")
    assert not C.date.between(*LOCK).any()
    P = pickle.load(open(OUT + "paths2y.pkl", "rb"))
    RC = pd.read_parquet(OUT + "cand_replay.parquet")
    RP = pickle.load(open(OUT + "paths_replay.pkl", "rb"))
    return dict(y2=(C, P), rep=(RC, RP))
