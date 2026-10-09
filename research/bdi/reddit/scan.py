"""Reddit study scan (NOTES.md section 1, pre-declared): 20 Reddit strategies x long/short mirror x 16 filter sets
(none, 5 singles, 10 pairs) x exits (t1s1, t05s1, t1s05, + structural S where the strategy has one), full day
09:50-15:00 bar close, first trade per symbol-day, production costs. Every configuration is counted.
Then: cheap probation gates -> full gates (walk-forward, regime split via mcf.research.gates) -> plateau neighbours
(counted) -> random/time-matched baseline. Outputs: data/scan.csv (git-ignored), results.csv, finalists.json,
counts.json. Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402
import strategies as S  # noqa: E402

LO, HI = 950, 1500
COUNT = {"n": 0}


def fkey(fs):
    return "+".join(f if not isinstance(f, tuple) else f"{f[0]}{f[1]}" for f in fs) or "-"


def cheap_ok(q):
    return (q.get("n", 0) >= 150 and q.get("exp_up", -1) > 0 and q.get("exp_down", -1) > 0 and q.get("t", 0) >= 2.0
            and q.get("ex_best_day", -1) > 0 and q.get("maxday", 1) <= 0.10)


def main():
    t0 = time.time()
    D = E.Data()
    print("loaded", round(time.time() - t0), flush=True)
    F = {(f, s): S.filt(D, f, s) for f in S.FILTERS for s in (1, -1)}
    rows, keep = [], {}
    for name, (fn, p, grid, key) in S.STRATS.items():
        for s in (1, -1):
            side = "long" if s > 0 else "short"
            o = fn(D, s, p)
            geoms = list(E.GEOMS) + (["S"] if (o["sx"] is not None or o["tg"] is not None) else [])
            for fs in S.FILTER_SETS:
                m = o["ev"].copy()
                for f in fs:
                    m &= F[(f, s)]
                for g in geoms:
                    idx, r = E.trades(D, m, side, g, o["sx"], o["tg"], LO, HI)
                    COUNT["n"] += 1
                    q = E.quick(D, idx, r)
                    row = {"strategy": name, "side": side, "filters": fkey(fs), "geom": g, "p": p, **q}
                    rows.append(row)
                    if cheap_ok(q):
                        keep[(name, side, fs, g)] = (idx, r)
            print(name, side, COUNT["n"], round(time.time() - t0), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "data" / "scan.csv", index=False)
    n_main = COUNT["n"]
    print("main grid configs", n_main, "cheap passers", len(keep), flush=True)

    # plateau neighbours for every cheap passer (counted), then full gates
    fin = []
    for (name, side, fs, g), (idx, r) in keep.items():
        fn, p, grid, key = S.STRATS[name]
        s = 1 if side == "long" else -1
        neigh = []
        for pp in grid:
            if pp == p:
                continue
            o = fn(D, s, pp)
            m = o["ev"].copy()
            for f in fs:
                m &= F[(f, s)]
            i2, r2 = E.trades(D, m, side, g, o["sx"], o["tg"], LO, HI)
            COUNT["n"] += 1
            neigh.append({"param": f"p={pp}", "n": len(r2), "exp": float(r2.mean()) if len(r2) else None})
        o = fn(D, s, p)
        for f in fs:
            if f in S.FGRID:
                for th in S.FGRID[f]:
                    if th == S.FTH[f]:
                        continue
                    m = o["ev"].copy()
                    for f2 in fs:
                        m &= S.filt(D, f2, s, th if f2 == f else None)
                    i2, r2 = E.trades(D, m, side, g, o["sx"], o["tg"], LO, HI)
                    COUNT["n"] += 1
                    neigh.append({"param": f"{f}={th}", "n": len(r2), "exp": float(r2.mean()) if len(r2) else None})
        # time-matched random baseline: same side/exit, every row at the trades' bar times (fixed exits only)
        tods = D.tod[idx]
        if g != "S":
            pr = D.B[f"p_{side}_{g}"].astype(float)
            means = pd.Series(pr).groupby(D.tod).mean()
            base = float(means.reindex(tods).mean())
        else:
            base = None
        # same strategy, no filters (what the filters add)
        fin.append({"strategy": name, "side": side, "filters": fkey(fs), "geom": g, "p": p, "idx": idx, "r": r,
                    "neigh": neigh, "baseline_timematched": base})
    N = COUNT["n"]
    out = []
    for f in fin:
        g = E.full(D, f["idx"], f["r"], N)
        q = E.quick(D, f["idx"], f["r"])
        ne = [x["exp"] for x in f["neigh"] if x["exp"] is not None]
        plateau = float(np.mean(ne)) if ne else None
        win = {}
        for wn, (a, b) in {"am": (950, 1130), "mid": (1135, 1330), "pm": (1335, 1500)}.items():
            mm = (D.tod[f["idx"]] >= a) & (D.tod[f["idx"]] <= b)
            win[wn] = {"n": int(mm.sum()), "exp": round(float(f["r"][mm].mean()), 4) if mm.any() else None}
        probation = (q["n"] >= 150 and q["exp_up"] > 0 and q["exp_down"] > 0 and q["t"] >= 2.0
                     and (g["wf_share"] or 0) >= 0.6 and plateau is not None and plateau > 0 and q["ex_best_day"] > 0)
        out.append({k: v for k, v in f.items() if k not in ("idx", "r")} | {
            "n": q["n"], "per_day": q["per_day"], "win": round(q["win"], 4), "exp": round(q["exp"], 4),
            "t": round(q["t"], 2), "t_required": g["t_required"], "exp_up": round(q["exp_up"], 4), "n_up": q["n_up"],
            "exp_flat": round(q["exp_flat"], 4), "n_flat": q["n_flat"], "exp_down": round(q["exp_down"], 4),
            "n_down": q["n_down"], "wf_share": g["wf_share"], "wf_folds": g["wf_folds"], "ex_best_day": round(q["ex_best_day"], 4),
            "maxday": round(q["maxday"], 3), "plateau_mean": None if plateau is None else round(plateau, 4),
            "plateau_min": None if not ne else round(float(np.min(ne)), 4), "verdict": g["verdict"], "fails": g["fails"],
            "windows": win, "probation": bool(probation)})
    out.sort(key=lambda x: (-x["probation"], -x["t"]))
    json.dump(out, open(HERE / "finalists.json", "w"), indent=1, default=float)
    json.dump({"configs_main_grid": n_main, "configs_plateau_neighbours": N - n_main, "configs_total": N,
               "t_required": E.gates.t_required(N), "cheap_passers": len(keep),
               "probation_passers": int(sum(x["probation"] for x in out))}, open(HERE / "counts.json", "w"), indent=1)
    print("total configs", N, "probation", sum(x["probation"] for x in out), round(time.time() - t0))


if __name__ == "__main__":
    main()
