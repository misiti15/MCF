"""Re-score every MarcoFlow rule stack on the setup-lab train/valid frame with MCF fills (entry at the
first qualifying 5-min bar close per symbol-day, R = 0.25 x daily ATR, target/stop geometry, 15:55 exit,
lab cost 1c/side) and a production-cost restatement (+1 bps/side, +2c on stop fills; the 3c
extended-tier surcharge is NOT included here - the auditor applies it).

Usage: python research/primitives/marcoflow/score.py   (from the repo root; train + valid only)
Writes results.csv (every stack x side x geom), ingredients.csv (each single MarcoFlow layer),
plateau.csv (one-step neighbours of gate passers), counts.json. Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
from conds import CAT, cond_mask, deployable, stack_mask, stack_sides  # noqa: E402
from mcf.research.setup_lab import load  # noqa: E402

GEOMS = {"t1s1": 1.0, "t05s1": 1.0, "t1s05": 0.5}   # geom -> stop size in R
FEAT = ["close", "atr_d", "heat", "tod", "rsi", "rsi5", "volumeRatio", "volumeSurge", "buyPressure",
        "vwapDistPct", "rsiSlope", "atrPct", "vwapReclaim", "symbol", "date"]
OUTC = [f"{a}_{s}_{g}" for g in GEOMS for s in ("long", "short") for a in ("r", "win")]


def etf_set():
    import sqlite3
    c = sqlite3.connect("data/marcoflow.sqlite")
    return {s for s, in c.execute("select distinct symbol from SignalObservation where assetClass='etf'")}


def regime_by_date(df):
    """Proxy for MarcoFlow's SPY regime (see conds.py): prior-day SPY 15:00 close vs 20-session mean and change."""
    spy = df[(df["symbol"] == "SPY") & (df["tod"] == 1500)][["date", "close"]].drop_duplicates("date").set_index("date")["close"]
    sma = spy.rolling(20, min_periods=5).mean()
    chg = spy / spy.shift(20).fillna(spy.iloc[0]) - 1
    reg = np.where((spy > sma) & (chg > 0), "bull", np.where((spy < sma) & (chg < 0), "bear", "neutral"))
    reg = pd.Series(reg, index=spy.index).shift(1).fillna("neutral")      # causal: yesterday's close
    return reg


class Split:
    def __init__(self, name, regime_hist=None):
        df = load(name, columns=FEAT + OUTC)
        df["symbol"] = df["symbol"].astype("category")
        self.name = name
        reg = regime_by_date(df if regime_hist is None else pd.concat([regime_hist, df[df.symbol == "SPY"]]))
        self.spy = df[df.symbol == "SPY"][["symbol", "date", "tod", "close"]].copy()
        etfs = etf_set()
        # random baseline: mean over symbol-days of the mean r in the window (expected value of a random bar)
        self._full = df
        self.base_cache = {}
        self.ingr_all = None
        self.extra_full = {"regime": df["date"].map(reg).to_numpy(), "is_etf": df["symbol"].isin(etfs).to_numpy()}
        self.sd_full = pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]

    def subset(self, floor=25.0):
        df = self._full
        keep = np.abs(df["heat"].to_numpy()) >= floor
        self.df = df[keep].reset_index(drop=True)
        self.extra = {k: v[keep] for k, v in self.extra_full.items()}
        self.sd = pd.factorize(self.df["symbol"].astype(str) + "|" + self.df["date"].astype(str))[0]

    def drop_full(self):
        del self._full, self.extra_full, self.sd_full

    def baseline(self, side, geom, lo, hi):
        k = (side, geom, lo, hi)
        if k not in self.base_cache:
            df = self._full
            nm = "long" if side == 1 else "short"
            r = df[f"r_{nm}_{geom}"].to_numpy()
            tod = df["tod"].to_numpy()
            m = (tod >= lo) & (tod < hi) & np.isfinite(r)
            per = pd.Series(r[m]).groupby(self.sd_full[m]).mean()
            self.base_cache[k] = float(per.mean())
        return self.base_cache[k]


def stats(df, sd, m, side, geom):
    nm = "long" if side == 1 else "short"
    r_all = df[f"r_{nm}_{geom}"].to_numpy()
    m = m & np.isfinite(r_all)
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return {"n": 0}
    _, first = np.unique(sd[idx], return_index=True)
    idx = idx[first]
    r = r_all[idx].astype(float)
    w = df[f"win_{nm}_{geom}"].to_numpy()[idx].astype(float)
    close, atr = df["close"].to_numpy()[idx].astype(float), df["atr_d"].to_numpy()[idx].astype(float)
    R = 0.25 * atr
    stop = GEOMS[geom]
    stop_hit = r < -stop - 1e-9
    r_prod = r - (2 * 0.0001 * close + 0.02 * stop_hit) / R
    dates = df["date"].to_numpy()[idx]
    t = pd.DataFrame({"d": dates, "r": r, "rp": r_prod})
    g = t.groupby("d")
    S, n_d = g["r"].sum(), g["r"].size()
    N, mu = len(r), r.mean()
    D = len(S)
    se = np.sqrt(((S - n_d * mu) ** 2).sum() * D / max(D - 1, 1)) / N if D > 1 else np.nan
    if D > 1:
        best = S.idxmax()
        ex = t[t.d != best]["r"].mean()
    else:
        ex = np.nan
    return {"n": N, "days": D, "win": round(float(np.nanmean(w)), 4), "exp_r": round(float(mu), 4),
            "exp_r_prod": round(float(r_prod.mean()), 4), "t_day": round(float(mu / se), 2) if se and se > 0 else None,
            "ex_best_day": round(float(ex), 4) if ex == ex else None, "green_days": round(float((S > 0).mean()), 3)}


def window_of(keys):
    lo, hi = 950, 1505
    for k in keys:
        fam, kind, p, _ = CAT[k]
        if kind == "win":
            lo, hi = max(lo, p[0]), min(hi, p[1])
    return lo, hi


def main():
    stacks = json.load(open(HERE / "stacks.json"))
    counts = {"stacks_extracted": len(stacks)}
    tr = Split("train")
    va = Split("valid", regime_hist=tr.spy)
    tr.spy = None

    # ---- ingredients: every single MarcoFlow layer, (a) on all bars, (b) on heat signals ----
    ing = []
    for sp in (tr, va):
        for key in CAT:
            if CAT[key][0] == "direction":
                continue
            for side in (1, -1):
                m_all = cond_mask(sp._full, key, side, 0, sp.extra_full)
                lo, hi = window_of([key])
                for geom in GEOMS:
                    s = stats(sp._full, sp.sd_full, m_all, side, geom)
                    ing.append({"split": sp.name, "layer": key, "side": side, "geom": geom, "base": "all_bars",
                                "baseline": round(sp.baseline(side, geom, lo, hi), 4), **s})
                    hs = (sp._full["heat"].to_numpy() * side) >= 30
                    s2 = stats(sp._full, sp.sd_full, m_all & hs, side, geom)
                    ing.append({"split": sp.name, "layer": key, "side": side, "geom": geom, "base": "heat30",
                                "baseline": round(sp.baseline(side, geom, lo, hi), 4), **s2})
        print("ingredients done", sp.name, flush=True)
    pd.DataFrame(ing).to_csv(HERE / "ingredients.csv", index=False)
    counts["ingredient_configs"] = len(ing) // 2

    # baselines for every window used (before dropping the full frames)
    wins = {window_of(d["id"].split("+")) for d in stacks} | {(950, 1505)}
    for sp in (tr, va):
        for lo, hi in wins:
            for side in (1, -1):
                for geom in GEOMS:
                    sp.baseline(side, geom, lo, hi)
        sp.subset(25.0)
        sp.drop_full()

    rows = []
    for i, d in enumerate(stacks):
        keys = d["id"].split("+")
        lo, hi = window_of(keys)
        for side in stack_sides(keys):
            mt = stack_mask(tr.df, keys, side, tr.extra)
            mv = stack_mask(va.df, keys, side, va.extra)
            for geom in GEOMS:
                a, b = stats(tr.df, tr.sd, mt, side, geom), stats(va.df, va.sd, mv, side, geom)
                rows.append({"id": d["id"], "kind": d["kind"], "side": "long" if side == 1 else "short", "geom": geom,
                             "deployable": deployable(keys), "win_lo": lo, "win_hi": hi,
                             "mf_lb": d.get("best_lb"), "mf_trades": d.get("mf_trades"), "mf_win": d.get("mf_win"),
                             "mf_reviews": d.get("n_reviews"), "paper_n": d.get("paper_n"), "paper_pnl": d.get("paper_pnl"),
                             **{f"tr_{k}": v for k, v in a.items()}, **{f"va_{k}": v for k, v in b.items()},
                             "tr_base": round(tr.baseline(side, geom, lo, hi), 4), "va_base": round(va.baseline(side, geom, lo, hi), 4)})
        if i % 200 == 0:
            print("stacks", i, flush=True)
    res = pd.DataFrame(rows)
    counts["stack_configs"] = len(res)

    gate = ((res.tr_exp_r > 0) & (res.va_exp_r > 0) & (res.va_n >= 30) & (res.va_t_day >= 1.5) & (res.va_exp_r > res.va_base))
    res["pre_gate"] = gate
    # ---- plateau: one-step neighbours of every pre-gate passer (each threshold +-1 step, heat floor 25/35) ----
    pl = []
    for _, row in res[gate].iterrows():
        keys = row["id"].split("+")
        side = 1 if row.side == "long" else -1
        variants = [({k: s}, 30.0, f"{k}{'+' if s > 0 else '-'}") for k in keys if CAT[k][3] for s in (-1, 1)]
        variants += [({}, 25.0, "heat25"), ({}, 35.0, "heat35")]
        for sh, floor, lab in variants:
            for sp, pre in ((tr, "tr"), (va, "va")):
                s = stats(sp.df, sp.sd, stack_mask(sp.df, keys, side, sp.extra, floor, sh), side, row.geom)
                pl.append({"id": row["id"], "side": row.side, "geom": row.geom, "neighbour": lab, "split": pre,
                           "n": s.get("n", 0), "exp_r": s.get("exp_r")})
    pl = pd.DataFrame(pl)
    pl.to_csv(HERE / "plateau.csv", index=False)
    counts["plateau_configs"] = int(len(pl) // 2) if len(pl) else 0
    if len(pl):
        agg = pl.groupby(["id", "side", "geom", "split"])["exp_r"].agg(["mean", lambda x: (x > 0).mean()]).unstack("split")
        agg.columns = [f"plat_{s}_{'mean' if a == 'mean' else 'pos'}" for a, s in agg.columns]
        res = res.merge(agg.reset_index(), on=["id", "side", "geom"], how="left")
    res["finalist"] = res.pre_gate & (res.get("plat_va_mean", 0) > 0) & (res.get("plat_tr_mean", 0) > 0)
    res.to_csv(HERE / "results.csv", index=False)
    counts["pre_gate"] = int(gate.sum())
    counts["finalists_all"] = int(res.finalist.sum())
    counts["finalists_deployable"] = int((res.finalist & res.deployable).sum())
    json.dump(counts, open(HERE / "counts.json", "w"), indent=1)
    print(counts)


if __name__ == "__main__":
    main()
