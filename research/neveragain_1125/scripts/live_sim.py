"""NEVERAGAIN live replay of Primary (PLAN.md). Educational only - not financial advice.
Usage: python live_sim.py LIVEDIR [ACCOUNT] [BOOK RAW|NEUTRAL]"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

L = Path(sys.argv[1]); ACC = sys.argv[2] if len(sys.argv) > 2 else "primary"
BOOK = sys.argv[3] if len(sys.argv) > 3 else "RAW"
T = pd.read_parquet(L / "lots_all.parquet")
T = T[T.account == ACC].copy()
z = np.load(L / "grid.npz", allow_pickle=True); G = dict(zip(z["keys"], z["arr"]))
T["gd"] = (T.side_n < 0) & T.strategy.str.contains("gap")
shift = {}
if BOOK == "NEUTRAL":
    a = T.groupby("strategy").r.mean(); shift = a.to_dict()
T["sh"] = T.strategy.map(shift).fillna(0.0)
T = T.sort_values(["date", "e_ns"]).reset_index(drop=True)
# cfg: (L_open, lotcap, idx_thr, k4)
CFG = {"NOW": (None, None, None, False), "G1-2": (2.0, None, None, False), "G1-3": (3.0, None, None, False),
       "G2-6": (None, 6, None, False), "G3": (None, None, 0.5, False), "G3-L": (None, None, 0.3, False),
       "G4": (None, None, None, True)}
CFG["G4+SV"] = CFG["G4"]; CFG["NOW+SV"] = CFG["NOW"]
if len(sys.argv) > 4:   # extra combos, e.g. G5a=G1-3+G4
    for spec in sys.argv[4].split(";"):
        n, parts = spec.split("=")
        lo = lc = it = None; k4 = False
        for p in parts.split("+"):
            lo, lc, it, k4b = (CFG[p][0] or lo, CFG[p][1] or lc, CFG[p][2] or it, CFG[p][3])
            k4 = k4 or k4b
        CFG[n] = (lo, lc, it, k4)


def idx_block(d, m, thr):
    s, i = G.get(f"SPY|{d}"), G.get(f"IWM|{d}")
    if s is None or i is None or m - 570 - 30 < 1:
        return False
    j = m - 570
    return bool((s[j] / s[0] - 1 >= thr / 100) and (i[j] / i[0] - 1 >= thr / 100) and s[j] > s[j - 30] and i[j] > i[j - 30])


def run_day(g, d, Lo, cap, thr, X, H=20.0, SV=False):
    S = sorted(g.strategy.unique()); si = g.strategy.map({s: k for k, s in enumerate(S)}).to_numpy(); N = len(S)
    em, xm = g.em.to_numpy(), g.xm.to_numpy()
    side, ent, risk, cost, rr, sh = (g.side_n.to_numpy(float), g.entry.to_numpy(float), g.risk.to_numpy(float),
                                     g.cost.to_numpy(float), g.r.to_numpy(float), g.sh.to_numpy(float))
    gd = g.gd.to_numpy()
    rr = rr - sh; dur = np.maximum(xm - em, 1).astype(float)
    grids = [G.get(f"{s}|{d}") for s in g.symbol]
    hasbar = np.array([x is not None for x in grids])
    for q in range(len(grids)):   # split-adjusted bars (Adjustment.SPLIT) -> rescale to the traded price level
        if hasbar[q]:
            g0 = grids[q][max(1, em[q] - 570)]
            if g0 > 0 and abs(g0 / ent[q] - 1) > 0.05:
                grids[q] = grids[q] * (ent[q] / g0)
    realized = np.zeros(N); nl = np.zeros(N, int); latched = np.zeros(N, bool); olatched = np.zeros(N, bool)
    open_ = []; halted = stopped = False; stop_m = -1; curve = []; why = {}
    by_m = {}
    for k in range(len(g)):
        by_m.setdefault(em[k], []).append(k)
    ps = np.zeros(N)
    for m in range(570, 960):
        keep = []
        for q in open_:
            if xm[q] <= m:
                realized[si[q]] += rr[q]
            else:
                keep.append(q)
        open_ = keep
        for s in range(N):
            if realized[s] <= -2.0 + 1e-12:
                latched[s] = True
        for k in by_m.get(m, ()):
            s = si[k]
            if stopped:
                why[k] = "flat"; continue
            if halted:
                why[k] = "halt"; continue
            if latched[s]:
                why[k] = "latch"; continue
            if olatched[s]:
                why[k] = "G1"; continue
            if cap is not None and sum(1 for q in open_ if si[q] == s) >= cap:
                why[k] = "G2"; continue
            if thr is not None and gd[k] and idx_block(d, m, thr):
                why[k] = "G3"; continue
            nl[s] += 1; open_.append(k)
        if open_:
            o = np.array(open_)
            c = np.array([grids[q][1 + m - 570] if hasbar[q] else ent[q] for q in o])
            mk = side[o] * (c - ent[o]) / risk[o] - cost[o] - sh[o] * np.clip((m - em[o]) / dur[o], 0, 1)
            ps = realized + np.bincount(si[o], weights=mk, minlength=N)
        else:
            o = np.zeros(0, int); mk = np.zeros(0); ps = realized.copy()
        if Lo is not None:
            olatched |= ps <= -Lo + 1e-12
        tot = ps.sum(); curve.append(tot)
        if tot <= -H + 1e-12:
            halted = True
        if SV and len(curve) >= 4:
            XX = X if X else 32.0
            v1, v2 = max(8, 0.5 * XX), max(12, 0.75 * XX)
            hit = lambda c: (c[-3] - c[-1] >= v1) or (max(c[-11:-1]) - c[-1] >= v2)
            if hit(curve) and hit(curve[:-1]):
                halted = True
        if X is not None and tot <= -X + 1e-12:
            stopped = True; stop_m = m
            for q, v in zip(o, mk):
                realized[si[q]] += v
            open_ = []
            curve += [realized.sum()] * (959 - m)
            break
    for q in open_:
        realized[si[q]] += rr[q]
    return dict(zip(S, realized)), dict(zip(S, nl)), stop_m, np.array(curve), why, hasbar.mean()


def shock(curve, X):
    v1, v2 = max(8, 0.5 * X), max(12, 0.75 * X)
    c = np.asarray(curve); hits = []
    for m in range(2, len(c)):
        d2 = c[m - 2] - c[m]; d10 = c[max(0, m - 10):m].max() - c[m]
        hits.append(d2 >= v1 or d10 >= v2)
    for m in range(1, len(hits)):
        if hits[m] and hits[m - 1]:
            return m + 2
    return -1


if __name__ == "__main__":
    rows, curves, whys = [], {}, []
    for cfg, (Lo, cap, thr, k4) in CFG.items():
        hist = []
        for d, g in T.groupby("date"):
            N = g.strategy.nunique()
            X = None
            if k4:
                X = float(np.clip(4 * np.std(hist, ddof=1), 2.5 * N, 8 * N)) if len(hist) >= 10 else 8.0 * N
            R, NL, sm, cv, why, bars = run_day(g, d, Lo, cap, thr, X, SV=cfg.endswith("+SV"))
            hist.append(sum(R.values()))
            curves[(cfg, d)] = cv
            for s in R:
                rows.append(dict(cfg=cfg, date=d, strategy=s, R=R[s], lots=NL[s], stop_m=sm, X=X if X else np.nan,
                                 low=cv.min(), bars=bars, shock=shock(cv, X if X else 32.0) if cfg == "NOW" else -1))
            for k, w in why.items():
                whys.append(dict(cfg=cfg, date=d, strategy=g.strategy.iloc[k], r=g.r.iloc[k], why=w))
    out = pd.DataFrame(rows); out.to_csv(L / f"replay_{ACC}_{BOOK}.csv", index=False)
    pd.DataFrame(whys).to_csv(L / f"blocked_{ACC}_{BOOK}.csv", index=False)
    np.savez_compressed(L / f"curves_{ACC}_{BOOK}.npz", keys=np.array([f"{a}|{b}" for a, b in curves]),
                        arr=np.array([np.pad(v, (0, 390 - len(v)), mode="edge") for v in curves.values()]))
    D = out.groupby(["cfg", "date"]).R.sum().unstack(0)
    print(D.sum().round(1).to_string())
