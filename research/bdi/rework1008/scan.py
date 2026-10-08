"""Score the declared F1-F3 grid on train and valid (python research/bdi/rework1008/scan.py).
Writes research/bdi/rework1008/data/grid.parquet (git-ignored). Educational only - not financial advice."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from grid import WINDOWS, combos, evaluate, namespace  # noqa: E402
from lib import GEOMS, SIDES, Split, baseline, stats  # noqa: E402

KEYS = ["n", "exp", "t", "green", "h1", "h2", "exbest", "tpd", "win"]


def main():
    t0 = time.time()
    sp = {s: Split(s) for s in ("train", "valid")}
    ns = {s: namespace(sp[s].col, sp[s].prev) for s in sp}
    base = {(s, side, g, w): baseline(sp[s], side, g, *WINDOWS[w]) for s in sp for side in SIDES for g in GEOMS
            for w in WINDOWS}
    cache = {s: {} for s in sp}

    def cmask(s, c):
        if c not in cache[s]:
            cache[s][c] = evaluate((c,), ns[s])
        return cache[s][c]

    rows, tried = [], 0
    allc = list(combos())
    last = None
    for k, (fam, conds, w) in enumerate(allc):
        key = (fam, conds)
        if key != last:
            idxs = {}
            for s in sp:
                m = np.ones(sp[s].n, bool)
                for c in conds:
                    if c != "none":
                        m &= cmask(s, c)
                idxs[s] = np.flatnonzero(m)
            last = key
        lo, hi = WINDOWS[w]
        ent = {}
        for s in sp:
            i = idxs[s]
            i = i[(sp[s].tod[i] >= lo) & (sp[s].tod[i] <= hi)]
            ent[s] = sp[s].first_per_day(i)
        for side in SIDES:
            for g in GEOMS:
                tried += 1
                a = stats(sp["train"], ent["train"], side, g)
                if a is None or a["n"] < 60:
                    continue
                b = stats(sp["valid"], ent["valid"], side, g) or {"n": 0}
                row = {"family": fam, "conds": "+".join(c for c in conds if c != "none") or "none",
                       "c0": conds[0], "c1": conds[1], "c2": conds[2], "c3": conds[3] if len(conds) > 3 else "",
                       "window": w, "side": side, "geom": g}
                row.update({f"tr_{x}": a.get(x, np.nan) for x in KEYS})
                row.update({f"va_{x}": b.get(x, np.nan) for x in KEYS})
                row["tr_base"] = base[("train", side, g, w)]
                row["va_base"] = base[("valid", side, g, w)]
                rows.append(row)
        if k % 1000 == 0:
            print(f"{k}/{len(allc)} combos, {tried} configs, {len(rows)} scored, {time.time() - t0:.0f}s", flush=True)
    r = pd.DataFrame(rows)
    (HERE / "data").mkdir(exist_ok=True)
    r.to_parquet(HERE / "data" / "grid.parquet")
    print("configurations tried:", tried, "scored (train n>=60):", len(r), f"{time.time() - t0:.0f}s")
    pd.Series({"tried_F1_F3": tried, "scored": len(r)}).to_json(HERE / "data" / "grid_counts.json")


if __name__ == "__main__":
    main()
