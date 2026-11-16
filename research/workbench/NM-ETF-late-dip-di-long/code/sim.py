"""Mechanic NM-ETF: identical engine for parent and copies (both tests).
Signal = module conditions on the 5-minute bar close (arena compute, context=False), adv20 >= $95M, price >= $5, the module's
ETF list; first qualifying bar per symbol-day (refire false) unless a variant says otherwise. Fill = open of the 1-minute bar
starting `lat` (1) minute after the signal bar closes; stop / target from the signal-bar close (as LabStrategy), 1R = rf x
daily ATR; same-minute stop+target = stop first; flat 15:55. R = net P/L / |fill - stop| (live R definition).
Costs = LR8 production model (as the CWT14 / L3 workbench jobs). Educational only - not financial advice."""
import sys, pickle, numpy as np, pandas as pd
from common import OUT, MOD, LOCK
from mcf.research.gates import tod_cost_mult
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
INVERSE = set("SPXS SPXU SDS SH SPDN SQQQ QID PSQ TZA RWM SRTY TWM SDOW DXD DOG SOXS TECS FAZ LABD DUST ERY".split())
LEV3 = set("SPXL SPXS SPXU UPRO TQQQ SQQQ TNA TZA URTY SRTY UDOW SDOW SOXL SOXS TECL TECS FAS FAZ LABU LABD NUGT DUST JNUG GDXU ERX ERY DPST FNGU BULZ".split())
PARENT = dict(lo=1400, hi=1500, ret3=MOD.CONDS[0][2], di=0.0, atr=MOD.CONDS[2][2], adv=95e6, extra=(), lots=1, cool=1,
              lat=1, rf=0.25, sk=1.0, tk=0.5, flat=1555, mh=None, be=None, lock=None, cte=None, daycap=None, univ=None)

def cost_entry(px, tod): return (0.01 + px * 1e-4) * tod_cost_mult([tod])[0] + px * 1e-4 + CAT
def cost_exit(px, why):
    base = 0.01 + px * 1e-4
    c = 0.0 if why == "target" else (base + max(0.02, 4e-4 * px) if why == "stop" else base + max(0.01, 1e-4 * px))
    return c + FEE_SEC * px + TAF + CAT
def add_min(t, k):
    h, m = divmod(int(t), 100); x = h * 60 + m + k; return (x // 60) * 100 + x % 60
def mdiff(a, b): return (a // 100 * 60 + a % 100) - (b // 100 * 60 + b % 100)

def exit_one(path, px, atr, tod, v):
    mins, o, h, l, c = path
    R0 = v["rf"] * atr; t0 = add_min(tod, v["lat"])
    i0 = np.searchsorted(mins, t0)
    if i0 >= len(mins) or mins[i0] > add_min(t0, 4): return None
    fill = o[i0]; stop = px - v["sk"] * R0; tgt = None if v["tk"] is None else px + v["tk"] * R0
    risk = fill - stop
    if risk <= 0: return dict(r=-1.0, why="gapstop", xt=int(mins[i0]), mfe=0.0, mae=-1.0, fill=fill, ent=int(mins[i0]))
    ce = cost_entry(fill, tod); cur = stop; peak = fill; trough = fill; why = None
    for i in range(i0, len(mins)):
        if mins[i] >= v["flat"] or (v["mh"] and mdiff(mins[i], mins[i0]) >= v["mh"]):
            ex, why = o[i], "time"; break
        if v["cte"] and mdiff(mins[i], mins[i0]) >= v["cte"][0] and (peak - fill) / risk < v["cte"][1]:
            ex, why = o[i], "time"; break
        if l[i] <= cur:
            ex = min(cur, o[i]) if i > i0 else cur; why = "stop" if cur < fill else "be"; trough = min(trough, l[i]); break
        if tgt is not None and h[i] >= tgt:
            ex, why = tgt, "target"; peak = max(peak, h[i]); break
        peak = max(peak, h[i]); trough = min(trough, l[i])
        if v["be"] is not None and peak >= fill + v["be"] * risk: cur = max(cur, fill)
        if v["lock"] is not None and peak >= fill + v["lock"][0] * risk: cur = max(cur, fill + v["lock"][1] * risk)
    else:
        ex, why = c[-1], "time"; i = len(mins) - 1
    pnl = ex - fill - cost_exit(ex, "stop" if why == "be" else why) - ce
    return dict(r=pnl / risk, why=why, xt=int(mins[i]), mfe=(peak - fill) / risk, mae=(trough - fill) / risk, fill=fill, ent=int(mins[i0]))

def select(cand, v):
    c = cand
    m = (c.tod >= v["lo"]) & (c.tod <= v["hi"]) & (c.ret3 <= v["ret3"]) & (c.di_diff7 >= v["di"]) & (c.atr_d_pct >= v["atr"]) \
        & (c.adv20 >= v["adv"]) & (c.close >= 5.0)
    for col, op, val in v["extra"]:
        a = c[col]
        m &= {"<=": a <= val, ">=": a >= val, "<": a < val, ">": a > val}[op]
    if v["univ"] == "noinv": m &= ~c.symbol.isin(INVERSE)
    if v["univ"] == "lev3": m &= c.symbol.isin(LEV3)
    s = c[m.to_numpy()].sort_values(["symbol", "date", "tod"])
    if v["lots"] == 1:
        return s.groupby(["symbol", "date"]).head(1)
    keep, last = [], {}
    for r in s.itertuples():
        k = (r.symbol, r.date); n, t = last.get(k, (0, -1))
        if n >= v["lots"] or (t >= 0 and mdiff(r.tod, t) < 5 * v["cool"] + 30): continue   # next lot only after the previous one is >=30 min old
        last[k] = (n + 1, r.tod); keep.append(r.Index)
    return s.loc[keep]

def trades(cand, paths, v):
    v = {**PARENT, **v}
    s = select(cand, v); rows = []
    for r in s.itertuples():
        p = paths.get((r.symbol, r.date))
        if p is None: continue
        x = exit_one(p, r.close, r.atr_d, r.tod, v)
        if x is None: continue
        rows.append(dict(symbol=r.symbol, date=r.date, tod=int(r.tod), **x, spy950=r.spy950, ret3=r.ret3, di=r.di_diff7,
                         atrp=r.atr_d_pct, adx7=r.adx7, vwap_atr=r.vwap_atr, day_pos=r.day_pos, fo=r.fromOpen_atr,
                         fpc=r.from_pc_atr, rvol=r.rvol_day, ret12=r.ret12, s950=r.ret_since950_atr, rsi7=r.rsi7, z12=r.z12))
    t = pd.DataFrame(rows, columns=list(rows[0]) if rows else ["symbol","date","tod","r","why","ent","mfe","mae"])
    if len(t) and v["daycap"]:
        t = t.sort_values(["date", "ent", "symbol"]).groupby("date").head(v["daycap"])
    return t

def stats(t, days=None):
    if not len(t): return dict(n=0)
    d = t.groupby("date").r.sum()
    best, worst = d.idxmax(), d.idxmin()
    wo = t[t.date != best].r
    return dict(n=len(t), days=t.date.nunique(), win=round(100 * (t.r > 0).mean(), 1), avg=round(t.r.mean(), 3),
                wobest=round(wo.mean(), 3) if len(wo) else np.nan, woworst=round(t[t.date != worst].r.mean(), 3),
                total=round(t.r.sum(), 1), worst=round(d.min(), 2), bestshare=round(d.max() / t.r.sum(), 2) if t.r.sum() > 0 else np.nan,
                avgw=round(t.r[t.r > 0].mean(), 3), avgl=round(t.r[t.r <= 0].mean(), 3))

def paired(t, base, days):
    a = t.groupby("date").r.sum().reindex(days).fillna(0); b = base.groupby("date").r.sum().reindex(days).fillna(0)
    dd = a - b; ndays = len(days)
    return round(dd.mean(), 3), round(dd.mean() / (dd.std(ddof=1) / np.sqrt(ndays)), 2) if dd.std() > 0 else 0.0

def load():
    C = pd.read_parquet(OUT + "cand2y.parquet"); C = C[C.date <= "2026-10-16"]
    assert not C.date.between(*LOCK).any()
    P = pickle.load(open(OUT + "paths2y.pkl", "rb"))
    RC = pd.read_parquet(OUT + "cand_replay.parquet"); RC = RC[(RC.date >= "2026-10-19") & (RC.date <= "2026-11-13")]
    RP = pickle.load(open(OUT + "paths_replay.pkl", "rb"))
    return dict(y2=(C, P), rep=(RC, RP))
