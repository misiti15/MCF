"""Mechanic GEN-261026-03: identical engine for parent and copies (both tests). SHORT.
Signal = module conditions on the 5-minute bar close (arena compute, context=False; breadth_open from the lab context),
adv20 >= $150M, price >= $5; first qualifying bar per symbol-day (refire false). Fill = open of the 1-minute bar starting
`lat` (1) minute after the signal bar closes; stop = signal close + 1R (as LabStrategy), 1R = 0.25 x daily ATR; no target;
trail 1R (of fill risk) behind the best low once +1R (holdtr: runner trail_r / trail_after_r); flat at the 15:55 bar open.
Stop checked first in each minute; the trail moves from the next minute. R = net P/L / |fill - stop| (live R definition).
Costs = LR8 production model (as the CWT14 / L3 / NM-ETF workbench jobs; SEC fee + TAF on the short sale).
Testing D cost filter (max_stop_cost_r 0.15, runner._precheck: (2 x (1c + 1 bp x px) + 2c) / |px - stop|) applied by
default (cf=0.15) - the parent as it runs today. Educational only - not financial advice."""
import sys, pickle, numpy as np, pandas as pd
from common import OUT, LOCK
from mcf.research.gates import tod_cost_mult
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
PARENT = dict(lo=1130, hi=1400, flow3=-0.37, fo=-0.78, br=0.5, adv=150e6, extra=(), lat=1, rf=0.25, sk=1.0, tk=None,
              trr=1.0, tra=1.0, flat=1555, mh=None, be=None, cf=0.15, daycap=None, lots=1, cool=6, cte=None)

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
    if risk <= 0: return dict(r=-1.0, why="gapstop", xt=int(mins[i0]), mfe=0.0, mae=-1.0, fill=fill, ent=int(mins[i0]), risk=0.0)
    ce = cost_entry(fill, tod); cur = stop; trough = fill; peak = fill; why = None
    for i in range(i0, len(mins)):
        if mins[i] >= v["flat"] or (v["mh"] and mdiff(mins[i], mins[i0]) >= v["mh"]):
            ex, why = o[i], "time"; break
        if v["cte"] and mdiff(mins[i], mins[i0]) >= v["cte"][0] and (fill - trough) / risk < v["cte"][1]:
            ex, why = o[i], "time"; break
        if h[i] >= cur:
            ex = max(cur, o[i]) if i > i0 else cur; why = "stop" if cur > fill else ("be" if cur >= fill - 1e-9 else "trail")
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
                ent=int(mins[i0]), risk=risk)

def select(cand, v):
    c = cand
    m = (c.tod >= v["lo"]) & (c.tod <= v["hi"]) & (c.flow3 <= v["flow3"]) & (c.fromOpen_atr <= v["fo"]) & (c.new_lod == 1) \
        & (c.adv20 >= v["adv"]) & (c.close >= 5.0) & ~c.blackout
    if v["br"] is not None: m &= c.breadth_open > v["br"]
    if v["cf"]:
        R = v["sk"] * v["rf"] * c.atr_d
        m &= (2 * (0.01 + c.close * 1e-4) + 0.02) / R <= v["cf"]
    for col, op, val in v["extra"]:
        a = c[col]
        m &= {"<=": a <= val, ">=": a >= val, "<": a < val, ">": a > val}[op]
    s = c[m.to_numpy()].sort_values(["symbol", "date", "tod"])
    if v["lots"] == 1:
        return s.groupby(["symbol", "date"]).head(1)
    keep, last = [], {}
    for r in s.itertuples():
        k = (r.symbol, r.date); n, t = last.get(k, (0, -1))
        if n >= v["lots"] or (t >= 0 and mdiff(r.tod, t) < 5 * v["cool"]): continue
        last[k] = (n + 1, r.tod); keep.append(r.Index)
    return s.loc[keep]

KEEP = ["flow3", "fromOpen_atr", "breadth_open", "breadth", "spy950", "qqq950", "spy_fo", "ret3", "ret12", "ret_since950_atr",
        "vwap_atr", "day_pos", "atr_d_pct", "gap_atr", "from_pc_atr", "rvol_day", "dist_pdl_atr", "rsi7", "z12", "adx7",
        "di_diff7", "bars_since_hod", "day_range_atr", "flow9prev", "flow_shift", "volumeRatio", "bar_range_atr",
        "sma20_dist_pct", "emaDiff", "lower_wick", "ll_count6", "eff6", "close", "atr_d", "adv20"]

def trades(cand, paths, v):
    v = {**PARENT, **v}
    s = select(cand, v); rows = []
    for r in s.itertuples():
        p = paths.get((r.symbol, r.date))
        if p is None: continue
        x = exit_one(p, r.close, r.atr_d, r.tod, v)
        if x is None: continue
        rows.append(dict(symbol=r.symbol, date=r.date, tod=int(r.tod), **x, **{k: getattr(r, k) for k in KEEP if hasattr(r, k)}))
    t = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["symbol", "date", "tod", "r", "why", "ent", "mfe", "mae"])
    if len(t) and v["daycap"]:
        t = t.sort_values(["date", "ent", "symbol"]).groupby("date").head(v["daycap"])
    return t

def stats(t):
    if not len(t): return dict(n=0)
    d = t.groupby("date").r.sum()
    best, worst = d.idxmax(), d.idxmin()
    wo = t[t.date != best].r
    return dict(n=len(t), days=t.date.nunique(), win=round(100 * (t.r > 0).mean(), 1), avg=round(t.r.mean(), 3),
                wobest=round(wo.mean(), 3) if len(wo) else np.nan, total=round(t.r.sum(), 1), worst=round(d.min(), 2),
                bestshare=round(d.max() / t.r.sum(), 2) if t.r.sum() > 0 else np.nan,
                avgw=round(t.r[t.r > 0].mean(), 3), avgl=round(t.r[t.r <= 0].mean(), 3))

def paired(t, base, days):
    a = t.groupby("date").r.sum().reindex(days).fillna(0); b = base.groupby("date").r.sum().reindex(days).fillna(0)
    dd = a - b
    return round(dd.mean(), 3), round(dd.mean() / (dd.std(ddof=1) / np.sqrt(len(days))), 2) if dd.std() > 0 else 0.0

def load():
    C = pd.read_parquet(OUT + "cand2y.parquet"); C = C[C.date <= "2026-10-16"]
    assert not C.date.between(*LOCK).any()
    P = pickle.load(open(OUT + "paths2y.pkl", "rb"))
    RC = pd.read_parquet(OUT + "cand_replay.parquet")
    RP = pickle.load(open(OUT + "paths_replay.pkl", "rb"))
    return dict(y2=(C, P), rep=(RC, RP))
