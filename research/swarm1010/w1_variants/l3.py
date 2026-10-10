"""W1: the L3 lineage (min_adv 0, gap prefilter; population not in base.npz). Month-by-month pass over the open frames
(lib.load_month; locked months refused) keeping bar closes 09:50-15:00 with gap <= -1%, all adv; the same coordinate
search as run.py on its threshold axes, the three frame exits and the volume layer. Writes data/configs_l3.csv.
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y"), str(HERE)]
import lib  # noqa: E402
import eng  # noqa: E402
from mcf.research.gates import prod_r  # noqa: E402
from run import Runner  # noqa: E402

COLS = ["close", "tod", "adv20", "gap", "sma20_slope_pct", "fromOpen", "dist_lod_atr", "rsi5", "volumeRatio", "atr_d",
        "symbol", "date"] + [f"{k}_short_{g}" for g in ("t1s1", "t05s1", "t1s05") for k in ("r", "win")]


class LD:
    def __init__(self):
        parts = []
        for m in lib.months():
            df = lib.load_month(m, COLS)
            df = df[(df.tod >= 950) & (df.tod <= 1500) & (df["gap"] <= -1.0)].reset_index(drop=True)
            for g in ("t1s1", "t05s1", "t1s05"):
                df[f"p_short_{g}"] = prod_r(df[f"r_short_{g}"], df[f"win_short_{g}"], df["close"], df["atr_d"], g)
            parts.append(df.drop(columns=[c for c in df.columns if c.startswith(("r_", "win_"))]))
            print("L3 load", m, len(df), flush=True)
        df = pd.concat(parts, ignore_index=True)
        dates = pd.read_csv(eng.SDIR / "dates.csv").iloc[:, 0].astype(str).tolist()
        dmap = {d: i for i, d in enumerate(dates)}
        self.dates, self.nd = dates, len(dates)
        self.day = df["date"].astype(str).map(dmap).to_numpy().astype(np.int32)
        key = df["symbol"].astype(str) + "|" + df["date"].astype(str)
        self.sd = np.r_[0, np.cumsum(key.to_numpy()[1:] != key.to_numpy()[:-1])].astype(np.int64)
        self.new = np.r_[True, self.sd[1:] != self.sd[:-1]]
        self.tod = df["tod"].to_numpy()
        self.df = df
        reg = lib.regimes().reindex(pd.to_datetime(dates).date)["regime"].to_numpy()
        self.regc = np.select([reg == "up", reg == "down"], [1, -1], 0).astype(np.int8)
        per = pd.PeriodIndex(pd.to_datetime(dates), freq="M")
        self.months = sorted(set(per))
        self.mon = np.array([self.months.index(p) for p in per], np.int32)

    def F(self, k):
        return self.df[k].to_numpy(np.float32)

    def trades(self, mask, side, geom, min_adv=0):
        m = np.asarray(mask, bool) & (self.df["adv20"].fillna(0).to_numpy() >= min_adv)
        idx = np.flatnonzero(m)
        if not len(idx):
            return idx, np.zeros(0)
        idx = idx[eng._first_per_sd(idx, self.sd)]
        r = self.df[f"p_{side}_{geom}"].to_numpy(float)[idx]
        ok = np.isfinite(r) & (self.df["atr_d"].to_numpy(float)[idx] > 0)
        return idx[ok], r[ok]

    def stats(self, idx, r):
        return eng.stats(r, self.day[idx], self.nd, self.regc, self.mon, self.months)


G0, S0, S1 = -2.6573517322540283, 0.37244729995727527, 0.5964763522148127


def f_l3(D, P, s):
    with np.errstate(invalid="ignore"):
        m = (D.F("gap") <= P["gap"]) & (D.F("sma20_slope_pct") > P["slope"])
        if P["third"] == "fromopen":
            m &= D.F("fromOpen") > P["fo"]
        elif P["third"] == "lowdist":
            lo = D.F("dist_lod_atr")
            m &= (lo > P["lod"][0]) & (lo <= P["lod"][1])
        else:
            m &= D.F("rsi5") > P["lvl"]
    return m


def specs():
    GAP = [-1.0, -2.0, G0, -3.0, -4.0]
    base = {"geom": "t1s1", "vol": None, "vband": None, "io": None, "ma": None, "_own": ()}
    ax_c = {"gap": GAP, "geom": ["t1s1", "t05s1", "t1s05"], "vol": [None, 1.25, 1.5, 2.0, 3.0]}
    lod0 = (0.7816761255264282, 0.9764953255653381)
    out = [("L3-gap-slope-fromopen", "t1s1", {"third": "fromopen", "slope": S0, "fo": 3.460294628143309},
            {"slope": [0.2, S0, 0.5, 0.6], "fo": [1.0, 2.0, 3.0, 3.460294628143309, 4.0]}),
           ("L3-gap-slope-lowdist", "t1s1", {"third": "lowdist", "slope": S0, "lod": lod0},
            {"slope": [0.2, S0, 0.5, 0.6], "lod": [(0.5, 0.75), lod0, (1.0, 1.25), (0.5, 1.0), (0.75, 1.25)]}),
           ("L3-gap-slope-rsi5hi", "t05s1", {"third": "rsi5", "slope": S1, "lvl": 70},
            {"slope": [0.3, S0, 0.5, S1, 0.7], "lvl": [60, 65, 70, 75, 80]})]
    S = []
    for nm, g, P0, ax in out:
        P = dict(base, geom=g, gap=G0, **P0)
        S.append({"name": nm, "group": "lab", "lineage": "L3", "side": "short", "geom": g, "min_adv": 0, "fn": f_l3,
                  "P0": P, "axes": ax | ax_c, "own": (), "prior_tries": 274247})
    return S


def main():
    D = LD()
    R = Runner(D)
    for sp in specs():
        n0 = len(R.rows)
        R.search(sp)
        b = R.rows[n0]
        print(sp["name"], len(R.rows) - n0, b["n"], b["exp"], b["t"], flush=True)
    pd.DataFrame(R.rows).to_csv(HERE / "data" / "configs_l3.csv", index=False)


if __name__ == "__main__":
    main()
