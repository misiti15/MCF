"""ROTA1 step 2: walk-forward rolling book vs static Primary book (2-year lab lists, costs in).
972 pre-declared configs + 3 light (demotion-only) configs. Educational only — not financial advice.

    python research/rota1/wf.py <scratch_dir>            # all 95 setups
    python research/rota1/wf.py <scratch_dir> nogen      # post hoc sensitivity: GEN-* setups removed (mined on this history)
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import prank, split_of, tstat, window_metrics  # noqa: E402

S = Path(sys.argv[1])
NOGEN = len(sys.argv) > 2 and sys.argv[2] == "nogen"
SUF = "_nogen" if NOGEN else ""
OUT = Path(__file__).resolve().parent
PRIMARY = json.load(open(OUT.parents[1] / "docs/live/assignments.json"))["accounts"]["primary"]
START = 90          # first review index (same for every config, = largest long window)
MINN = 30           # capped trades in the long window to qualify

GRID = {"h": [3, 5, 7], "L": [40, 60, 90], "score": ["S1", "S2", "S3"], "m": [0.05, 0.10, 0.20],
        "swaps": [1, 2], "k": [6, 8, 10], "flag": [0, 1]}


def load(prefix):
    R, N = pd.read_parquet(S / f"{prefix}_R.parquet"), pd.read_parquet(S / f"{prefix}_N.parquet")
    if NOGEN:
        keep = [c for c in R.columns if not c.upper().startswith("GEN")]
        R, N = R[keep], N[keep]
    return R, N


def score_fn(name, mL, mS, mask):
    def r3(m):
        return prank(m["wob"], mask), prank(m["green"], mask), prank(m["worst"], mask)
    a, b, c = r3(mL)
    if name == "S1":
        return (a + b + c) / 3
    if name == "S2":
        return 0.5 * a + 0.25 * b + 0.25 * c
    d, e, f = r3(mS)
    return 0.7 * (a + b + c) / 3 + 0.3 * (d + e + f) / 3


def flagged(mS):
    return (mS["n"] > 0) & (np.nan_to_num(mS["avg"], nan=0) < 0) & (np.nan_to_num(mS["green"], nan=1) < 0.40)


def simulate(Rv, Nv, cfg, cache, start, end, init=None):
    """Returns (daily book R array over [start, end), membership log, swap log)."""
    h, L, k = cfg["h"], cfg["L"], cfg["k"]
    book = list(init) if init is not None else None
    streak = {}
    out = np.zeros(end - start)
    held = np.zeros((end - start, Rv.shape[1]), bool)
    swaps_log = []
    for i in range(start, end, h):
        mL, mS = cache[("L", L, i)], cache[("S", i)]
        qual = mL["n"] >= MINN
        if book is None:
            sc = score_fn(cfg["score"], mL, mS, qual)
            book = list(np.argsort(np.nan_to_num(sc, nan=-9))[::-1][:k])
        else:
            mem = np.zeros(len(qual), bool); mem[book] = True
            sc = score_fn(cfg["score"], mL, mS, qual | mem)
            sc = np.nan_to_num(sc, nan=-9)
            flg = flagged(mS) if cfg["flag"] else np.zeros(len(qual), bool)
            weakest_sc = min(sc[b] for b in book)
            chal = [j for j in np.where(qual & ~mem)[0] if sc[j] > weakest_sc + cfg["m"]]
            newstreak = {j: streak.get(j, 0) + 1 for j in chal}
            streak = newstreak
            ready = sorted([j for j, s in streak.items() if s >= 2], key=lambda j: -sc[j])
            nsw = 0
            # flagged incumbents first: replaced by best qualified non-member, no margin / streak
            if cfg["flag"]:
                pool = sorted([j for j in np.where(qual & ~mem)[0]], key=lambda j: -sc[j])
                for b in sorted([b for b in book if flg[b]], key=lambda b: sc[b]):
                    if nsw >= cfg["swaps"] or not pool:
                        break
                    j = pool.pop(0)
                    if sc[j] <= sc[b]:
                        continue
                    book[book.index(b)] = j; mem[b] = False; mem[j] = True; nsw += 1
                    swaps_log.append((i, int(b), int(j), "flag"))
                    streak.pop(j, None)
                    if j in ready:
                        ready.remove(j)
            for j in ready:
                if nsw >= cfg["swaps"]:
                    break
                if mem[j]:
                    continue
                w = min(book, key=lambda b: sc[b])
                if sc[j] <= sc[w] + cfg["m"]:
                    continue
                book[book.index(w)] = j; mem[w] = False; mem[j] = True; nsw += 1
                swaps_log.append((i, int(w), int(j), "margin"))
                streak.pop(j, None)
        hi = min(i + h, end)
        out[i - start:hi - start] = Rv[i:hi][:, book].mean(1)
        held[i - start:hi - start][:, book] = True
    return out, held, swaps_log, book


def light(Rv, Nv, cache, static_idx, h, start, end):
    out = np.zeros(end - start)
    held = np.zeros((end - start, Rv.shape[1]), bool)
    for i in range(start, end, h):
        flg = flagged(cache[("S", i)])
        act = [b for b in static_idx if not flg[b]]
        hi = min(i + h, end)
        # sitting-out members contribute 0 (cash); per-setup mean over the full static size
        out[i - start:hi - start] = Rv[i:hi][:, act].sum(1) / len(static_idx)
        held[i - start:hi - start][:, act] = True
    return out, held


def build_cache(Rv, Nv, end):
    cache = {}
    for i in range(START, end):
        for L in GRID["L"]:
            cache[("L", L, i)] = window_metrics(Rv, Nv, i, L)
        cache[("S", i)] = window_metrics(Rv, Nv, i, 20)
    return cache


def stats(diff, splits):
    res = {}
    for sp in ("TRAIN", "VALID", "FWD"):
        x = diff[splits == sp]
        res[f"{sp}_mean"] = x.mean() if len(x) else np.nan
        res[f"{sp}_t"] = tstat(x)
    tv = diff[(splits == "TRAIN") | (splits == "VALID")]
    res["TV_mean"] = tv.mean(); res["TV_t"] = tstat(tv)
    return res


def main():
    R, N = load("bt")
    setups = list(R.columns)
    Rv, Nv = R.to_numpy(), N.to_numpy()
    dates = R.index.to_numpy()
    end = len(dates)
    splits = np.array([split_of(d) for d in dates[START:end]])
    static_idx = [setups.index(s) for s in PRIMARY]
    static = Rv[START:end][:, static_idx].mean(1)
    cache = build_cache(Rv, Nv, end)
    rows = []
    keys = list(GRID)
    books = {}
    for vals in itertools.product(*GRID.values()):
        cfg = dict(zip(keys, vals))
        out, held, sw, book = simulate(Rv, Nv, cfg, cache, START, end)
        r = {**cfg, **{f"book_{k}": v for k, v in stats(out, splits).items()},
             **stats(out - static, splits), "swaps": cfg["swaps"], "n_swaps": len(sw)}
        r["max_swaps"] = cfg["swaps"]
        rows.append(r)
        books[tuple(vals)] = (out, held, sw, book)
    for h in GRID["h"]:
        out, held = light(Rv, Nv, cache, static_idx, h, START, end)
        rows.append({"h": h, "L": None, "score": "LIGHT", **{f"book_{k}": v for k, v in stats(out, splits).items()},
                     **stats(out - static, splits)})
    df = pd.DataFrame(rows)
    # baselines
    base = {"static": static}
    q = np.zeros(end - START)
    for i in range(START, end):
        m = cache[("L", 60, i)]
        qual = m["n"] >= MINN
        q[i - START] = Rv[i][qual].mean()
    base["all_qualified"] = q
    rng = np.random.default_rng(20261107)
    for h in GRID["h"]:
        for k in GRID["k"]:
            acc = np.zeros(end - START)
            for _ in range(200):
                for i in range(START, end, h):
                    qual = np.where(cache[("L", 60, i)]["n"] >= MINN)[0]
                    b = rng.choice(qual, size=min(k, len(qual)), replace=False)
                    hi = min(i + h, end)
                    acc[i - START:hi - START] += Rv[i:hi][:, b].mean(1)
            base[f"random_h{h}_k{k}"] = acc / 200
    brow = [{"baseline": n, **stats(v, splits), **{f"vs_static_{k}": x for k, x in stats(v - static, splits).items()}}
            for n, v in base.items()]
    pd.DataFrame(brow).round(4).to_csv(OUT / f"baselines{SUF}.csv", index=False)
    df.round(4).to_csv(OUT / f"wf_grid{SUF}.csv", index=False)
    pd.to_pickle({"books": books, "static": static, "dates": dates[START:end], "setups": setups,
                  "base": base}, S / f"wf_books{SUF}.pkl")
    print(pd.DataFrame(brow).round(3).to_string())
    print("sessions scored:", pd.Series(splits).value_counts().to_dict())


if __name__ == "__main__":
    main()
