"""Amendment A (NOTES.md 1.8): full gates, plateau neighbours (counted), windows and baseline for the best few.
Writes best_few.json and updates counts.json. Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402
import strategies as S  # noqa: E402

PICK = [("R04-gap-go", "short", ("rvol",), "t1s1"), ("R05-gap-fill", "short", ("rvol", "trend"), "t05s1"),
        ("R03-vwap-fade", "long", ("trend", "inplay"), "t1s1"), ("R19-orb-fib", "long", ("vwap", "inplay"), "t1s1")]


def run(D, name, side, fs, g, p=None, th=None):
    fn, p0, grid, key = S.STRATS[name]
    s = 1 if side == "long" else -1
    o = fn(D, s, p0 if p is None else p)
    m = o["ev"].copy()
    for f in fs:
        m &= S.filt(D, f, s, (th or {}).get(f))
    return E.trades(D, m, side, g, o["sx"], o["tg"], 950, 1500)


def main():
    D = E.Data()
    cnt = json.load(open(HERE / "counts.json"))
    n_extra, out = 0, []
    pr = {}
    for name, side, fs, g in PICK:
        fn, p0, grid, key = S.STRATS[name]
        idx, r = run(D, name, side, fs, g)
        neigh = []
        for pp in grid:
            if pp != p0:
                i2, r2 = run(D, name, side, fs, g, p=pp); n_extra += 1
                neigh.append({"param": f"p={pp}", "n": len(r2), "exp": round(float(r2.mean()), 4)})
        for f in fs:
            for th in S.FGRID.get(f, []):
                if th != S.FTH[f]:
                    i2, r2 = run(D, name, side, fs, g, th={f: th}); n_extra += 1
                    neigh.append({"param": f"{f}={th}", "n": len(r2), "exp": round(float(r2.mean()), 4)})
        for k in range(len(fs)):                       # each filter removed in turn (reported, counted)
            fs2 = fs[:k] + fs[k + 1:]
            i2, r2 = run(D, name, side, fs2, g); n_extra += 1
            neigh.append({"param": f"drop {fs[k]}", "n": len(r2), "exp": round(float(r2.mean()), 4), "plateau": False})
        if g not in pr:
            pr[g] = {sd: pd.Series(D.B[f"p_{sd}_{g}"].astype(float)).groupby(D.tod).mean() for sd in ("long", "short")}
        base = float(pr[g][side].reindex(D.tod[idx]).mean())
        out.append({"cfg": f"{name}|{side}|{'+'.join(fs)}|{g}", "idx": idx, "r": r, "neigh": neigh, "baseline": round(base, 4)})
    N = cnt["configs_main_grid"] + n_extra
    res = []
    for o in out:
        idx, r = o.pop("idx"), o.pop("r")
        q = E.quick(D, idx, r)
        f = E.full(D, idx, r, N)
        pl = [x["exp"] for x in o["neigh"] if x.get("plateau", True)]
        win = {}
        for wn, (a, b) in {"am": (950, 1130), "mid": (1135, 1330), "pm": (1335, 1500)}.items():
            mm = (D.tod[idx] >= a) & (D.tod[idx] <= b)
            win[wn] = {"n": int(mm.sum()), "exp": round(float(r[mm].mean()), 4) if mm.any() else None}
        res.append(o | {"n": q["n"], "per_day": q["per_day"], "win": round(q["win"], 4), "exp": round(q["exp"], 4),
                        "t": round(q["t"], 2), "t_required": f["t_required"],
                        "up": [round(q["exp_up"], 4), q["n_up"]], "flat": [round(q["exp_flat"], 4), q["n_flat"]],
                        "down": [round(q["exp_down"], 4), q["n_down"]], "wf_share": f["wf_share"], "wf_folds": f["wf_folds"],
                        "ex_best_day": round(q["ex_best_day"], 4), "maxday": round(q["maxday"], 3),
                        "plateau_mean": round(float(np.mean(pl)), 4), "plateau_min": round(float(np.min(pl)), 4),
                        "verdict": f["verdict"], "fails": f["fails"], "windows": win})
    json.dump(res, open(HERE / "best_few.json", "w"), indent=1, default=float)
    cnt.update({"configs_best_few_neighbours": n_extra, "configs_total": N, "t_required": E.gates.t_required(N)})
    json.dump(cnt, open(HERE / "counts.json", "w"), indent=1)
    for x in res:
        print(json.dumps({k: v for k, v in x.items() if k != "neigh"}, default=float))
        print("   neigh", x["neigh"])


if __name__ == "__main__":
    main()
