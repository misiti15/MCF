"""Score open-drive configs: LR8 costs (+1.2 bp borrow shorts), testing book (cap 100, <=3 lots/symbol, price>=5,
cost filter 0.15R, shorts ETB>=0.9), stats per half. Stage `fit` prints FIT only; stage `final CFG,...` scores CHECK + T2
once for the named finalists. Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

W = Path(__file__).resolve().parent
S = W.parents[1]
TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
BORROW = 1.2e-4
RULES = dict(cap=100, latch=None, cf=0.15, symcap=3)
NSES = {"fit": 170, "check": 276, "T2": 427}


def tod_mult(t):
    t = np.asarray(t, float)
    return np.where(t < 935, 3.8, np.where(t < 950, 2.1, np.where(t < 1030, 1.4, 1.0)))


def costs_r(side, entry, px, kind, risk, gap, tod):
    tier = np.where((np.abs(gap) >= 20) | (entry < 5), 3.0, 1.0)
    ec = (0.01 + entry * 1e-4) * tod_mult(tod)
    xc = np.where(kind == 2, 0.0, 0.01 + px * 1e-4) + np.where(kind == 1, 0.02, 0.0)
    bo = np.where(side < 0, BORROW * entry, 0.0)
    g = side * (px - entry)
    return g / risk, (g - tier * (ec + xc) - bo) / risk


def half(d):
    d = pd.Series(d).astype(str)
    fit = ((d >= "2024-10-01") & (d <= "2024-10-31")) | ((d >= "2025-03-01") & (d <= "2025-09-30"))
    return np.where(fit, "fit", np.where(d >= "2025-10-01", "check", "none"))


def prep(which):
    t = pd.concat([pd.read_parquet(p) for p in sorted(W.glob(f"trades_{which}*.parquet"))], ignore_index=True)
    d = t.date.astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    t["r_gross"], t["r"] = costs_r(t.side.values, t.entry.values, t.px.values, t.kind.values, t.risk.values, t.gap.values,
                                   t.tod.values)
    t["em"] = (t.tod // 100) * 60 + t.tod % 100
    t["xm"] = 570 + t.xt
    t["stop_cost_r"] = (2 * (0.01 + t.entry * 1e-4) + 0.02) / t.risk
    # null: mean cost-R of up to 3 random 09:50-10:30 entries on the same symbol-day / side / risk
    nr = []
    for side, gap, risk, nt, ne, npx, nk in zip(t.side, t.gap, t.risk, t.n_tod, t.n_entry, t.n_px, t.n_kind):
        if len(nt) == 0:
            nr.append(np.nan)
            continue
        nt, ne, npx, nk = (np.asarray(x, float) for x in (nt, ne, npx, nk))
        nr.append(float(np.mean(costs_r(side, ne, npx, nk, risk, gap, nt)[1])))
    t["r_null"] = nr
    t["half"] = half(t.date) if which == "T1" else "T2"
    return t


def book(t, etb):
    t = t[t.entry >= 5.0]
    t = t[(t.side > 0) | t.symbol.map(etb).fillna(0).ge(0.9)]
    t = t[t.stop_cost_r <= RULES["cf"]]
    if not len(t):
        return t
    t = t.sort_values(["date", "em", "symbol"], kind="mergesort").reset_index(drop=True)
    keep = np.zeros(len(t), bool)
    em, xm, sy = t.em.values, t.xm.values, t.symbol.values
    for _, idx in t.groupby("date").indices.items():
        open_ = []
        for i in idx:
            open_ = [o for o in open_ if o[0] > em[i]]
            if len(open_) >= RULES["cap"] or sum(1 for o in open_ if o[1] == sy[i]) >= RULES["symcap"]:
                continue
            keep[i] = True
            open_.append((xm[i], sy[i]))
    return t[keep].reset_index(drop=True)


def clustered_t(t):
    if len(t) < 3:
        return float("nan")
    m = t.r.mean()
    e = (t.r - m).groupby(t.date).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(t)
    return float(m / se) if se > 0 else float("nan")


def stats(t, nses, spy=None):
    if not len(t):
        return {"n": 0}
    day = t.groupby("date").r.sum()
    tot = float(t.r.sum())
    top = day.sort_values(ascending=False)
    o = {"n": int(len(t)), "per_ses": round(len(t) / nses, 2), "days": int(day.size), "win": round(float((t.r > 0).mean()), 3),
         "avg_r": round(float(t.r.mean()), 4), "gross": round(float(t.r_gross.mean()), 4),
         "wo_best": round(float(t.loc[t.date != top.index[0], "r"].mean()), 4) if day.size > 1 else None,
         "wo_top2": round(float(t.loc[~t.date.isin(top.index[:2]), "r"].mean()), 4) if day.size > 2 else None,
         "best_share": round(float(top.iloc[0] / tot), 2) if tot > 0 else None,
         "r_per_ses": round(tot / nses, 4), "worst_day": round(float(day.min()), 2), "t_day": round(clustered_t(t), 2),
         "null": round(float(t.r_null.mean()), 4), "excess": round(float(t.r.mean() - t.r_null.mean()), 4),
         "green_days": round(float((day > 0).mean()), 3)}
    if spy is not None:
        ty = t.date.map(spy)
        for k in ("up", "flat", "down"):
            x = t.loc[ty == k, "r"]
            o[f"spy_{k}"] = round(float(x.mean()), 3) if len(x) else None
    return o


def spy_t1():
    f = pads.field("__index_level_0__")
    b = pads.dataset("/home/user/MCF/data/cache_hist/1Min/SPY.parquet", format="parquet").to_table(
        filter=(f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b[(b.index.hour * 100 + b.index.minute >= 930) & (b.index.hour * 100 + b.index.minute < 1600)]
    b["date"] = b.index.date.astype(str)
    g = b.groupby("date").agg(o=("open", "first"), c=("close", "last"))
    ret = (g.c / g.o - 1) * 100
    return pd.Series(np.where(ret >= 0.3, "up", np.where(ret <= -0.3, "down", "flat")), index=g.index)


def spy_t2():
    s = pd.read_parquet("/home/user/MCF/data/cache_fresh/spy_days.parquet")
    s.index = s.index.astype(str)
    return s["type"]


if __name__ == "__main__":
    stage = sys.argv[1]
    etb = pd.read_parquet(W / "etb_rate.parquet").rate
    T1 = prep("T1")
    spy = spy_t1()
    if stage == "fit":
        rows = []
        for c, g in T1[T1.half == "fit"].groupby("cfg"):
            b = book(g, etb)
            rows.append({"cfg": c, "raw": len(g), **stats(b, NSES["fit"], spy)})
        df = pd.DataFrame(rows).sort_values("avg_r", ascending=False)
        pd.set_option("display.width", 250)
        print(df.to_string(index=False))
        df.to_csv(W / "fit_table.csv", index=False)
    elif stage == "final":
        fins = sys.argv[2].split(",")
        T2 = prep("T2")
        out = {}
        for c in fins:
            g = T1[T1.cfg == c]
            e = {}
            bk = {}
            for h in ("fit", "check"):
                bk[h] = book(g[g.half == h], etb)
                e[h] = stats(bk[h], NSES[h], spy)
            comb = pd.concat([bk["fit"], bk["check"]])
            e["combined"] = stats(comb, NSES["fit"] + NSES["check"], spy)
            b2 = book(T2[T2.cfg == c], etb)
            e["T2"] = stats(b2, NSES["T2"], spy_t2())
            out[c] = e
            comb.assign(test="T1").to_parquet(W / f"bk_{c}.parquet")
            b2.assign(test="T2").to_parquet(W / f"bk2_{c}.parquet")
        json.dump(out, open(W / "final.json", "w"), indent=1)
        for c, e in out.items():
            print("==", c)
            print(pd.DataFrame(e).T.to_string())
