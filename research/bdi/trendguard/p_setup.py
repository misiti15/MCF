"""Amendment A (P): first pullback that holds VWAP after a morning low - a new long setup, 6 configurations
(t1s1 / t05s1 / t1s05 x cur / E1), scored with mcf/research/gates.py on the 426 open sessions. Every symbol-day of the 1-min
cache; locked block dropped at load (features.drop_locked). Outputs: p_results.csv, data/p_trades.parquet.
    python research/bdi/trendguard/p_setup.py [--workers 4]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y"), str(HERE)]
import features as FT  # noqa: E402
import score as S  # noqa: E402

MIN_ADV = 95e6
WINDOW = (1030, 1430)
N_TRIES = 6
SIDE = 1
LAYERS = ["today's low so far was set by a bar ending <= 11:30", "5-min low within 0.1% of VWAP or EMA9 (low <= level x 1.001)",
          "close above VWAP and above EMA9", "EMA9 rising over 3 bars", "10:30-14:30 ET", "adv20 >= $95M"]


def p_mask(F: pd.DataFrame, adv: np.ndarray) -> np.ndarray:
    X = S.day_extremes(F)
    c, lo, vw, e9 = (F[k].to_numpy() for k in ("close", "low", "vwap", "ema9"))
    tod = F["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        return ((X["t_lod"] <= 11 * 60 + 30) & ((lo <= vw * 1.001) | (lo <= e9 * 1.001)) & (c > vw) & (c > e9)
                & (F["ema9_sl"].to_numpy() > 0) & (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (adv >= MIN_ADV)
                & (F["atr_d"].to_numpy() > 0))


def one(args):
    sym, advmap = args
    m1 = FT.drop_locked(pd.read_parquet(FT.CACHE / f"{sym}.parquet"))
    if m1.empty:
        return None
    F = FT.features(m1).reset_index(drop=True)
    F["dayid"] = pd.factorize(F["date"])[0]
    adv = F["date"].map(advmap).to_numpy(float)
    m = p_mask(F, np.nan_to_num(adv))
    idx = np.flatnonzero(m)
    if not len(idx):
        return None
    _, first = np.unique(F["dayid"].to_numpy()[idx], return_index=True)
    ent = idx[np.sort(first)].astype(np.int64)
    a = {k: F[k].to_numpy(np.float64) for k in ("high", "low", "close", "ema9", "hi6", "lo6", "atr_d")}
    tod, dayid = F["tod"].to_numpy(np.int64), F["dayid"].to_numpy(np.int64)
    out = []
    for geom, (upk, dnk) in S.GEOMK.items():
        for mode, ex in ((0, "cur"), (1, "E1")):
            R = 0.25 * a["atr_d"][ent]
            val, won, stp, unit = S.sim_many(ent, SIDE, upk, dnk, mode, R, a["atr_d"][ent], a["high"], a["low"], a["close"], a["ema9"],
                                             a["hi6"], a["lo6"], tod, dayid)
            r = S.prod_cost(val, won, stp, unit, a["close"][ent])
            out.append(pd.DataFrame({"date": F["date"].to_numpy()[ent], "symbol": sym, "tod": tod[ent], "r": r, "geom": geom, "exit": ex}))
    return pd.concat(out)


if __name__ == "__main__":
    from lib import daily, regimes, LOCKED_MONTHS

    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    d = daily()
    d["date"] = pd.to_datetime(d["date"])
    advs = {s: dict(zip(g["date"], g["adv20"])) for s, g in d.groupby("symbol")}
    syms = sorted(p.stem for p in FT.CACHE.glob("*.parquet"))
    parts = []
    with Pool(a.workers) as pool:
        for i, x in enumerate(pool.imap_unordered(one, [(s, advs.get(s, {})) for s in syms], chunksize=4)):
            if x is not None:
                parts.append(x)
            if i % 200 == 0:
                print(f"{i}/{len(syms)}", flush=True)
    T = pd.concat(parts, ignore_index=True)
    T["date"] = pd.to_datetime(T["date"]).dt.date
    T.to_parquet(HERE / "data" / "p_trades.parquet", index=False)
    reg = regimes()
    wf_months = sorted(set(pd.PeriodIndex(pd.to_datetime(list(reg.index)), freq="M").astype(str)))
    rows = []
    for (geom, ex), g in T.groupby(["geom", "exit"]):
        rows.append({"setup": "P-pullback-vwap-long", "side": "long", "geom": geom, "guard": "none", "exit": ex, "lineage": "P",
                     "tries": N_TRIES, **S.evaluate(g[["date", "symbol", "tod", "r"]], reg, N_TRIES, wf_months)})
    res = pd.DataFrame(rows)
    res.to_csv(HERE / "p_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(res[["geom", "exit", "n", "per_day", "exp_r", "t", "t_required", "up_exp", "down_exp", "wf_share_pos", "verdict"]].to_string())
