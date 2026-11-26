"""COMPASSIDX-1126 CI-2 (PREREG.md): Primary book (primshorts_1126 booksim, Primary rules, open marks) in 4 contexts
(a live rules, b L3-OUT, c LATCH-OPEN, d both) with and without the compass-signed SPY hedge: on CI-1 signal days, from CI-1
entry to CI-1 exit, at entry and each later mark + 1 min, h = side x |E| when the compass side opposes the book's net beta E
(R per 1% SPY, open lots entered before the rebalance minute), else 0; P&L = h x SPY % move; cost 4.4 bp per unit notional
traded. Usage: python ci2_score.py CIXDIR OUT.json (needs ci1_trades.csv). Locked block never read (asserted).
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import ci_lib as C

sys.path.insert(0, str(C.ROOT / "research/primshorts_1126"))
from booksim import sim_day  # noqa: E402

C.prereg_gate()
D, OUT = Path(sys.argv[1]), sys.argv[2]
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
          "NM-ETF-late-dip-di-long"]
CTX = {"a_live": (False, False), "b_L3out": (True, False), "c_latchopen": (False, True), "d_L3out_latchopen": (True, True)}
COST_SIDE = 4.4e-4
X = pd.read_parquet(D / "cand.parquet"); C.no_locked(X.date.unique())
PATH = np.load(D / "paths.npy", mmap_mode="r")
X["si"] = X.setup.map({s: i for i, s in enumerate(SETUPS)})
X["b"] = X.side * X.beta * 0.01 * X.entry / X.risk
X = X.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
T1 = pd.read_csv(C.H / "ci1_trades.csv", dtype={"date": str}).set_index("date")
G = C.spy_days(["FIT", "CHECK", "T2"]); M = C.marks(["FIT", "CHECK", "T2"])
days = sorted(set(G) | set(X.date))
byday = {d: g for d, g in X.groupby("date")}


def hedge(d, g, taken):
    if d not in T1.index or d not in G:
        return 0.0, 0.0
    t = T1.loc[d]; side = int(t.side); sp = G[d]; m = sp.m.to_numpy(); T, L = M[d]
    xm = int(t.xm)
    px_exit = float(t.entry) * (1 + side * float(t.ret_bps) / 1e4)
    reb = [int(t.em)] + [int(k) + 1 for k in T if int(t["T"]) < k and k + 1 < xm]
    gt = g[taken] if g is not None else None
    pnl, cost, h0 = 0.0, 0.0, 0.0
    for j, r in enumerate(reb):
        if gt is not None and len(gt):
            o = (gt.em.to_numpy() < r) & (gt.xm.to_numpy() > r)
            E = float(gt.b.to_numpy()[o].sum())
        else:
            E = 0.0
        h = side * abs(E) if np.sign(E) == -side else 0.0
        cost += abs(h - h0) * 100 * COST_SIDE
        k = np.searchsorted(m, r)
        p0 = float(sp.open.iloc[k])
        if j + 1 < len(reb):
            p1 = float(sp.open.iloc[np.searchsorted(m, reb[j + 1])])
        else:
            p1 = px_exit
        pnl += h * (p1 / p0 - 1) * 100
        h0 = h
    cost += abs(h0) * 100 * COST_SIDE
    return pnl - cost, cost


def run(l3out, lo_all):
    w = np.ones(4); lo = np.full(4, lo_all)
    rows = []
    for d in days:
        g = byday.get(d)
        if g is not None and l3out:
            g = g[g.si != 0]
        if g is None or not len(g):
            hp, hc = hedge(d, None, None)
            rows.append(dict(date=d, book=0.0, hedge=hp, hcost=hc)); continue
        si = g.si.to_numpy(); side = g.side.to_numpy(float); ent = g.entry.to_numpy(float); risk = g.risk.to_numpy(float)
        rr = g.r.to_numpy(float); lc = g.lc.to_numpy(float); em = g.em.to_numpy(int); xm = g.xm.to_numpy(int)
        off = g.off.to_numpy(int); n = g.n.to_numpy(int)

        def markf(o, mm):
            j = np.clip(mm - em[o], 0, n[o] - 1)
            return side[o] * (PATH[off[o] + j] - ent[o]) / risk[o] - lc[o]
        _, taken, tot, _ = sim_day(si, pd.factorize(g.symbol)[0], side, ent, risk, lc, em, xm, rr, markf, 4, w, lo)
        hp, hc = hedge(d, g, taken)
        rows.append(dict(date=d, book=tot, hedge=hp, hcost=hc))
    o = pd.DataFrame(rows); o["per"] = o.date.map(C.period); o["both"] = o.book + o.hedge
    return o


def goal(s):
    s = pd.Series(np.asarray(s, float))
    return dict(mean=round(float(s.mean()), 3), red_per_21=round(float((s < 0).mean() * 21), 2),
                worst5=round(float(s.nsmallest(5).sum()), 1), roll20_floor=round(float(s.rolling(20).sum().min()), 1),
                avg_wo_best=round(float((s.sum() - s.max()) / (len(s) - 1)), 3))


res = {"prereg_sha256": open(C.H / "PREREG.sha256").read().split()[0]}
for name, (l3, lo) in CTX.items():
    o = run(l3, lo)
    C.no_locked(o.date)
    o.to_csv(C.H / f"ci2_days_{name}.csv", index=False)
    rc = {}
    for per in ("FIT", "CHECK", "T2"):
        g = o[o.per == per]
        gb, gh = goal(g.book), goal(g.both)
        imp_mean = (gh["mean"] - gb["mean"]) / abs(gb["mean"]) if gb["mean"] else np.nan
        imp_w5 = (gh["worst5"] - gb["worst5"]) / abs(gb["worst5"]) if gb["worst5"] else np.nan
        rc[per] = dict(sessions=len(g), base=gb, with_hedge=gh, hedge_mean=round(float(g.hedge.mean()), 3),
                       hedge_t=round(C.tstat(g.hedge[g.hedge != 0]), 2), hedge_days=int((g.hedge != 0).sum()),
                       hedge_cost_mean=round(float(g.hcost.mean()), 3), paired_t=round(C.tstat(g.hedge), 2),
                       improve_mean=round(float(imp_mean), 3), improve_worst5=round(float(imp_w5), 3))
    rc["pass"] = bool(all(rc[p]["improve_mean"] >= 0.2 and rc[p]["improve_worst5"] >= 0.2 for p in ("CHECK", "T2")))
    res[name] = rc
    print(name, json.dumps({p: {k: v for k, v in rc[p].items()} for p in ("CHECK", "T2")}), "pass", rc["pass"], flush=True)
res["CI2_PASS"] = res["a_live"]["pass"]
json.dump(res, open(OUT, "w"), indent=1)
