"""FREQ engine = the first pass's engine (../code/sim.py: fill, exits, LR8 costs, R definition - imported unchanged) with
three frequency parts added, each OFF for the parent:
  univ   symbol sets (sets.py) unioned with the parent's 128-ETF list
  refire live LabStrategy refire semantics (mcf.strategies.setups.refire_select): every qualifying bar fires unless it is
         within `cool` bars of the previous emitted signal; each fire is a new lot under `lots` open lots of this setup
         on the symbol (live max_lots_per_symbol, same_setup_reentry true); a skipped fire still starts the cooldown
  flatonly  a re-entry only after the previous lot closed
  barcap N  at most N entries on one decision bar (cluster cap, most liquid first); daycap N  at most N per day
Educational only - not financial advice."""
import sys, os, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))
import sim as S0
from sim import exit_one, cost_entry, cost_exit, mdiff, add_min, INVERSE, LEV3
SC = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/etffreq/"
SETS = json.load(open(SC + "sets.json"))
LOCK = ("2024-11-01", "2025-02-28")
PARENT = dict(S0.PARENT, univ=("PAR",), refire=False, cool=1, lots=1, flatonly=False, gross=False, excl=())

def universe(v):
    u = set()
    for k in v["univ"]:
        u |= set(SETS[k]) if k in SETS else {k}
    return u - set(v["excl"])

def select(c, v):
    m = (c.tod >= v["lo"]) & (c.tod <= v["hi"]) & (c.ret3 <= v["ret3"]) & (c.di_diff7 >= v["di"]) & (c.atr_d_pct >= v["atr"]) \
        & (c.adv20 >= v["adv"]) & (c.close >= 5.0) & c.symbol.isin(universe(v))
    for col, op, val in v["extra"]:
        a = c[col]
        m &= {"<=": a <= val, ">=": a >= val, "<": a < val, ">": a > val}[op]
    s = c[m.to_numpy()].sort_values(["symbol", "date", "tod"])
    if not v["refire"]:
        return s.groupby(["symbol", "date"]).head(1)
    keep, last = [], {}
    for r in s.itertuples():
        k = (r.symbol, r.date); t = last.get(k)
        if t is not None and mdiff(r.tod, t) <= 5 * v["cool"]:
            continue
        last[k] = r.tod; keep.append(r.Index)
    return s.loc[keep]

def trades(cand, paths, v):
    v = {**PARENT, **v}
    s = select(cand, v); rows = []; openlots = {}
    if v.get("barcap"):   # cluster cap: at most N entries on one decision bar (a market-wide drop, not a dip), most liquid first
        s = s.sort_values(["date", "tod", "adv20"], ascending=[True, True, False]).groupby(["date", "tod"]).head(v["barcap"])
        s = s.sort_values(["symbol", "date", "tod"])
    for r in s.itertuples():
        p = paths.get((r.symbol, r.date))
        if p is None: continue
        x = exit_one(p, r.close, r.atr_d, r.tod, v)
        if x is None: continue
        k = (r.symbol, r.date); lots = openlots.setdefault(k, [])
        live = [xt for xt in lots if xt > x["ent"]]
        if len(live) >= v["lots"] or (v["flatonly"] and live): continue
        lots.append(x["xt"])
        if v["gross"]:
            risk = x["fill"] - (r.close - v["sk"] * v["rf"] * r.atr_d)
            ce = cost_entry(x["fill"], r.tod); cx = cost_exit(x["fill"], "stop" if x["why"] == "be" else x["why"])
            x["r"] = x["r"] + (ce + cx) / risk if risk > 0 else x["r"]
        rows.append(dict(symbol=r.symbol, date=r.date, tod=int(r.tod), **x, ret3=r.ret3, di=r.di_diff7, atrp=r.atr_d_pct,
                         adv=r.adv20, ret12=r.ret12, vwap_atr=r.vwap_atr, spy950=r.spy950, rsi7=r.rsi7))
    cols = ["symbol", "date", "tod", "r", "why", "xt", "mfe", "mae", "fill", "ent"]
    t = pd.DataFrame(rows) if rows else pd.DataFrame(columns=cols)
    if len(t) and v.get("daycap"):
        t = t.sort_values(["date", "ent", "symbol"]).groupby("date").head(v["daycap"])
    return t

def stats(t, nsess):
    if not len(t): return dict(n=0, tps=0.0)
    d = t.groupby("date").r.sum(); best = d.idxmax()
    wo = t[t.date != best].r
    gd = (d > 0).sum()
    return dict(n=len(t), tps=round(len(t) / nsess, 3), days=int(t.date.nunique()), green=int(gd), win=round(100 * (t.r > 0).mean(), 1),
                avg=round(t.r.mean(), 3), wobest=round(wo.mean(), 3) if len(wo) else np.nan, total=round(t.r.sum(), 1),
                rps=round(t.r.sum() / nsess, 3), worst=round(d.min(), 2), bestshare=round(d.max() / t.r.sum(), 2) if t.r.sum() > 0 else np.nan)

def load():
    C = pd.read_parquet(SC + "cand2y.parquet"); C = C[C.date <= "2026-10-16"]
    assert not C.date.between(*LOCK).any()
    P = pickle.load(open(SC + "paths2y.pkl", "rb"))
    RC = pd.read_parquet(SC + "cand_replay.parquet"); RP = pickle.load(open(SC + "paths_replay.pkl", "rb"))
    days2 = sorted(set(C.date)); daysr = sorted(set(RC.date))
    return dict(y2=(C, P, days2), rep=(RC, RP, daysr))
