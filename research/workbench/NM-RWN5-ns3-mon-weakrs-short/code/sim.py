"""Mechanic NM-RWN5: identical engine for parent and copies (both tests). SHORT, t1s1.
Signal = module conditions on the 5-minute bar close: close crosses above VWAP on this bar (vwapDistPct > 0, previous bar
<= 0), close above the 5-min SMA50, fromOpen < -2%, Monday, fromOpen < SPY fromOpen (spy_fo), bar close 09:50-11:30;
adv20 >= $95M, price >= $5; first qualifying bar per symbol-day (refire false). Fill = open of the 1-minute bar starting
`lat` (1) minute after the signal bar closes; 1R = 0.25 x daily ATR; stop = signal close + 1R, target = signal close - 1R
(LabStrategy bracket, as the live LITE / IONS orders); flat at the 15:55 bar open. Stop checked before target in a minute.
R = net P/L / |fill - stop| (live R definition). Costs = LR8 production model (as the CWT14 / L3 / NM-ETF / GEN workbench
jobs; SEC fee + TAF on the short sale). Testing D cost filter (max_stop_cost_r 0.15: (2 x (1c + 1 bp x px) + 2c) / 1R)
on by default - the parent as it runs today. Educational only - not financial advice."""
import pickle, numpy as np, pandas as pd
from common import OUT, LOCK
from mcf.research.gates import tod_cost_mult
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
PARENT = dict(lo=950, hi=1130, fo=-2.0, sma=0.0, rs=0.0, dows=(0,), adv=95e6, extra=(), lat=1, rf=0.25, sk=1.0, tk=1.0,
              flat=1555, mh=None, be=None, trr=None, tra=None, cf=0.15, lots=1, cool=1, daycap=None, cross=True)

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
    fill = float(o[i0]); stop = px + v["sk"] * R0; tgt = None if v["tk"] is None else px - v["tk"] * R0
    risk = stop - fill
    if risk <= 0: return dict(r=-1.0, why="gapstop", xt=int(mins[i0]), mfe=0.0, mae=-1.0, fill=fill, ent=int(mins[i0]), risk=0.0)
    ce = cost_entry(fill, tod); cur = stop; trough = fill; peak = fill; why = None
    for i in range(i0, len(mins)):
        if mins[i] >= v["flat"] or (v["mh"] and mdiff(mins[i], mins[i0]) >= v["mh"]):
            ex, why = float(o[i]), "time"; break
        if h[i] >= cur:
            ex = max(cur, float(o[i])) if i > i0 else cur; why = "stop" if cur > fill else ("be" if cur >= fill - 1e-9 else "trail")
            peak = max(peak, h[i]); break
        if tgt is not None and l[i] <= tgt:
            ex, why = tgt, "target"; trough = min(trough, l[i]); break
        trough = min(trough, l[i]); peak = max(peak, h[i])
        if v["trr"] is not None and fill - trough >= v["tra"] * risk: cur = min(cur, trough + v["trr"] * risk)
        if v["be"] is not None and fill - trough >= v["be"] * risk: cur = min(cur, fill)
    else:
        ex, why = float(c[-1]), "time"; i = len(mins) - 1
    pnl = fill - ex - cost_exit(ex, "stop" if why in ("be", "trail") else why) - ce
    return dict(r=pnl / risk, why=why, xt=int(mins[i]), mfe=float(fill - trough) / risk, mae=float(fill - peak) / risk,
                fill=fill, ent=int(mins[i0]), risk=risk)

OPS = {"<=": np.less_equal, ">=": np.greater_equal, "<": np.less, ">": np.greater}
def select(cand, v):
    c = cand
    m = (c.tod >= v["lo"]) & (c.tod <= v["hi"]) & (c.fromOpen < v["fo"]) & (c.adv20 >= v["adv"]) & (c.close >= 5.0)
    if v["cross"]: m &= (c.vwapDistPct > 0) & (c.prev_vwap <= 0)
    if v["sma"] is not None: m &= c.sma50_dist_pct > v["sma"]
    if v["rs"] is not None: m &= (c.fromOpen - c.spy_fo) < v["rs"]
    if v["dows"] is not None: m &= c.dow.isin(v["dows"])
    if v["cf"]:
        R = v["sk"] * v["rf"] * c.atr_d
        m &= (2 * (0.01 + c.close * 1e-4) + 0.02) / R <= v["cf"]
    for col, op, val in v["extra"]:
        m &= OPS[op](c[col], val)
    s = c[m.to_numpy()].sort_values(["symbol", "date", "tod"])
    return s.groupby(["symbol", "date"]).head(1)

KEEP = ["fromOpen", "vwapDistPct", "sma50_dist_pct", "sma20_dist_pct", "sma20_slope_pct", "rsi", "rsi5", "heat", "flow3",
        "volumeRatio", "atrPct", "dist_lod_atr", "dist_hod_atr", "dist_pdl_atr", "dist_pdh_atr", "buyPressure", "macdPct",
        "emaDiff", "upper_wick", "lower_wick", "spy_fo", "qqq_fo", "breadth", "breadth_open", "spy950", "fo950", "gap",
        "close", "atr_d", "adv20", "dow", "momentum", "rsiSlope", "pricePosition"]

def trades(cand, paths, v):
    v = {**PARENT, **v}
    s = select(cand, v); rows = []
    for r in s.itertuples():
        p = paths.get((r.symbol, r.date))
        if p is None: continue
        x = exit_one(p, r.close, r.atr_d, r.tod, v)
        if x is None: continue
        rows.append(dict(symbol=r.symbol, date=r.date, tod=int(r.tod), **x, **{k: getattr(r, k) for k in KEEP if hasattr(r, k)}))
    t = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["symbol", "date", "tod", "r", "why", "ent", "xt", "mfe", "mae"])
    if len(t) and v["daycap"]:
        t = t.sort_values(["date", "ent", "symbol"]).groupby("date").head(v["daycap"])
    return t

def stats(t):
    if not len(t): return dict(n=0)
    d = t.groupby("date").r.sum()
    best = d.idxmax()
    wo = t[t.date != best].r
    return dict(n=len(t), days=t.date.nunique(), win=round(100 * (t.r > 0).mean(), 1), avg=round(t.r.mean(), 3),
                wobest=round(wo.mean(), 3) if len(wo) else np.nan, total=round(t.r.sum(), 1), worst=round(d.min(), 2),
                bestshare=round(d.max() / t.r.sum(), 2) if t.r.sum() > 0 else np.nan,
                avgw=round(t.r[t.r > 0].mean(), 3), avgl=round(t.r[t.r <= 0].mean(), 3))

def paired(t, base, days):
    a = t.groupby("date").r.sum().reindex(days).fillna(0); b = base.groupby("date").r.sum().reindex(days).fillna(0)
    dd = a - b
    return round(dd.mean(), 3), round(dd.mean() / (dd.std(ddof=1) / np.sqrt(len(days))), 2) if dd.std() > 0 else 0.0

def load(replay=True):
    C = pd.read_parquet(OUT + "cand2y.parquet"); C = C[C.date <= "2026-10-16"]   # live window 10-19.. is the replay
    assert not C.date.between(*LOCK).any()
    P = pickle.load(open(OUT + "paths2y.pkl", "rb"))
    D = dict(y2=(C, P))
    if replay:
        D["rep"] = (pd.read_parquet(OUT + "cand_replay.parquet"), pickle.load(open(OUT + "paths_replay.pkl", "rb")))
    return D
