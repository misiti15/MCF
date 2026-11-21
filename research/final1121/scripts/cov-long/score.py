"""cov-long scoring. python score.py fit            -> fit-only table, all configs (selection)
                  python score.py final A,B,C    -> fit/check/T2 + day types + correlations + null, finalists only
Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from eng import B, W, S, PFX  # noqa: E402

TEST = dict(cap=100, latch=None, cf=0.15, symcap=3)
PRIM = dict(cap=30, latch=-2.0, cf=None, symcap=3)
ETB = pd.Series(dtype=float)


def load(name):
    t = B.add_r(pd.read_parquet(W / (PFX + name)))
    t["date"] = t.date.astype(str)
    return t


def ctx():
    d1 = pd.read_parquet(W / "day1.parquet")
    d2 = pd.read_parquet(W / "day2.parquet")
    pp = pd.read_parquet(W / "primproxy.parquet")
    return d1, d2, pp


def lab(day, dates):
    d = day.reindex(dates)
    q = day.rng.quantile(1 / 3)
    return pd.DataFrame({"spy": np.where(d.ret >= 0.3, "up", np.where(d.ret <= -0.3, "down", "flat")),
                         "gapup": d.spy_gap >= 0.3, "quiet": d.rng <= q}, index=dates)


def dstats(t, days, day, proxy):
    """t: booked trades in this test; days: list of session dates in this test."""
    n = len(t)
    o = {"trades": n, "sessions": len(days), "tps": round(n / len(days), 2)}
    if n < 3:
        return o
    dr = t.groupby("date").r.sum().reindex(days).fillna(0.0)
    tot = dr.sum()
    srt = dr.sort_values(ascending=False)
    b1, b2 = srt.index[:1], srt.index[:2]
    m = t.r.mean()
    e = (t.r - m).groupby(t.date).sum()
    se = math.sqrt(float((e ** 2).sum())) / n
    o.update(avg_r=round(m, 4), win=round(float((t.r > 0).mean()), 3), total_r=round(tot, 1),
             r_per_sess=round(tot / len(days), 3),
             wo_best=round(float(t.loc[~t.date.isin(b1), "r"].mean()), 4),
             wo_top2=round(float(t.loc[~t.date.isin(b2), "r"].mean()), 4),
             best_share=round(float(srt.iloc[0] / tot), 2) if tot > 0 else None,
             t_day=round(m / se, 2) if se > 0 else None, green_days=round(float((dr[dr != 0] > 0).mean()), 3),
             worst_day=round(float(dr.min()), 1))
    L = lab(day, days)
    tl = L.reindex(t.date.values)
    tl.index = t.index
    for k in ("up", "flat", "down"):
        x = t.r[tl.spy == k]
        o[f"spy_{k}"] = (round(float(x.mean()), 3) if len(x) else None, int(len(x)))
    for k in ("gapup", "quiet"):
        x = t.r[tl[k].astype(bool)]
        o[k] = (round(float(x.mean()), 3) if len(x) else None, int(len(x)))
    # R per session by day type (what it contributes on those days)
    for k, msk in (("rps_up", L.spy == "up"), ("rps_quiet", L.quiet), ("rps_gapup", L.gapup)):
        o[k] = round(float(dr[msk.values].mean()), 3)
    pr = proxy.reindex(days).fillna(0.0)
    o["corr_proxy"] = round(float(np.corrcoef(dr, pr)[0, 1]), 3)
    red = pr < 0
    o["rps_proxy_red"] = round(float(dr[red].mean()), 3)
    o["rps_proxy_green"] = round(float(dr[~red].mean()), 3)
    o["avg_r_proxy_red"] = round(float(t.r[t.date.isin(pr.index[red])].mean()), 3) if t.date.isin(pr.index[red]).any() else None
    return o


def run(setups, tests=("fit",), rules=TEST, null=False):
    d1, d2, pp = ctx()
    T1 = load("trades_t1.parquet")
    T1["half"] = B.half(T1.date)
    days1 = list(d1.index)
    h = B.half(pd.Series(days1))
    D = {"fit": [d for d, x in zip(days1, h) if x == "fit"], "check": [d for d, x in zip(days1, h) if x == "check"]}
    D["comb"] = D["fit"] + D["check"]
    prox1 = pp[pp.test == "T1"].set_index("date").r
    prox2 = pp[pp.test == "T2"].set_index("date").r
    T2 = load("trades_t2.parquet") if "T2" in tests else None
    D["T2"] = list(d2.index)
    out = {}
    nulls = {}
    if null:
        N1 = load("null_t1.parquet") if (W / (PFX + "null_t1.parquet")).exists() else None
        N2 = load("null_t2.parquet") if (W / (PFX + "null_t2.parquet")).exists() else None
    for s in setups:
        e = {}
        b1 = B.book(T1[T1.setup == s], rules, ETB)
        for k in tests:
            if k == "T2":
                b2 = B.book(T2[T2.setup == s], rules, ETB)
                e[k] = dstats(b2, D["T2"], d2, prox2)
            else:
                x = b1[b1.date.isin(set(D[k]))]
                e[k] = dstats(x, D[k], d1, prox1)
            if null:
                if k == "T2" and N2 is not None:
                    nb = B.book(N2[N2.setup == s], rules, ETB)
                    e[k]["null_avg_r"] = round(float(nb.r.mean()), 4) if len(nb) else None
                elif k != "T2" and N1 is not None:
                    nb = B.book(N1[N1.setup == s], rules, ETB)
                    nb = nb[nb.date.isin(set(D[k]))]
                    e[k]["null_avg_r"] = round(float(nb.r.mean()), 4) if len(nb) else None
        out[s] = e
    return out


def live_corr(setups, rules=TEST):
    """correlation of the backtest daily R with Primary's LIVE daily R on the overlap 2026-10-06..11-04."""
    lt = pd.read_pickle(S / "live_trades.pkl")
    p = lt[lt.account == "primary"]
    p = p.assign(date=p.date.astype(str))
    pdr = p.groupby("date").r.sum()
    pdr = pdr[pdr.index <= "2026-11-04"]
    T1 = load("trades_t1.parquet")
    res = {}
    for s in setups:
        b = B.book(T1[T1.setup == s], rules, ETB)
        dr = b.groupby("date").r.sum().reindex(pdr.index).fillna(0.0)
        red = pdr < 0
        res[s] = {"n_days": int(len(pdr)), "corr_live": round(float(np.corrcoef(dr, pdr)[0, 1]), 3) if dr.std() > 0 else None,
                  "rps_on_live_red": round(float(dr[red].mean()), 3), "rps_on_live_green": round(float(dr[~red].mean()), 3),
                  "live_red_days": int(red.sum()), "bt_total_overlap": round(float(dr.sum()), 1)}
    return res


if __name__ == "__main__":
    C = __import__("eng").C
    if sys.argv[1] == "fit":
        r = run(list(C.CANDS), ("fit",))
        rows = []
        for s, e in r.items():
            z = e["fit"]
            rows.append({"setup": s, **{k: z.get(k) for k in ("trades", "tps", "avg_r", "wo_best", "wo_top2", "t_day",
                                                              "r_per_sess", "spy_up", "spy_flat", "spy_down", "gapup",
                                                              "quiet", "corr_proxy", "rps_proxy_red")}})
        pd.set_option("display.width", 250)
        print(pd.DataFrame(rows).to_string(index=False))
        json.dump(r, open(W / (PFX + "fit.json"), "w"), indent=1, default=str)
    elif sys.argv[1] == "final":
        ss = sys.argv[2].split(",")
        r = run(ss, ("fit", "check", "comb", "T2"), TEST, null=True)
        rp = run(ss, ("fit", "check", "comb", "T2"), PRIM)
        lc = live_corr(ss)
        json.dump({"testing_rules": r, "primary_rules": rp, "live_corr": lc}, open(W / (PFX + "final.json"), "w"), indent=1, default=str)
        print(json.dumps({"testing_rules": r, "live_corr": lc}, indent=1, default=str))


def combo(setups, rules=PRIM):
    """Primary proxy (backtest book of today's 5 Primary setups) + candidate (Primary-rules book), per session."""
    d1, d2, pp = ctx()
    T1 = load("trades_t1.parquet")
    T2 = load("trades_t2.parquet")
    days1 = list(d1.index)
    h = B.half(pd.Series(days1))
    D = {"fit": [d for d, x in zip(days1, h) if x == "fit"], "check": [d for d, x in zip(days1, h) if x == "check"],
         "T2": list(d2.index)}
    prox = {"fit": pp[pp.test == "T1"].set_index("date").r, "check": pp[pp.test == "T1"].set_index("date").r,
            "T2": pp[pp.test == "T2"].set_index("date").r}
    lt = pd.read_pickle(S / "live_trades.pkl")
    p = lt[lt.account == "primary"]
    live = p.assign(date=p.date.astype(str)).groupby("date").r.sum()
    live = live[live.index <= "2026-11-04"]
    out = {}
    for k in ("fit", "check", "T2"):
        pr = prox[k].reindex(D[k]).fillna(0.0)
        out.setdefault("_proxy", {})[k] = {"total": round(pr.sum(), 1), "green": round(float((pr > 0).mean()), 3),
                                           "mean": round(pr.mean(), 3)}
    out["_proxy"]["live"] = {"total": round(live.sum(), 1), "green": round(float((live > 0).mean()), 3), "n": len(live)}
    for s in setups:
        e = {}
        for k in ("fit", "check", "T2"):
            src = T2 if k == "T2" else T1
            b = B.book(src[src.setup == s], rules, ETB)
            dr = b.groupby("date").r.sum().reindex(D[k]).fillna(0.0)
            pr = prox[k].reindex(D[k]).fillna(0.0)
            c = pr + dr
            red = pr < 0
            e[k] = {"cand_total": round(dr.sum(), 1), "combo_total": round(c.sum(), 1),
                    "combo_green": round(float((c > 0).mean()), 3), "proxy_green": round(float((pr > 0).mean()), 3),
                    "red_days_turned_green": int(((pr < 0) & (c > 0)).sum()), "green_days_turned_red": int(((pr > 0) & (c < 0)).sum()),
                    "cand_rps_on_proxy_red": round(float(dr[red].mean()), 3), "cand_rps_on_proxy_green": round(float(dr[~red].mean()), 3),
                    "combo_sd": round(float(c.std()), 2), "proxy_sd": round(float(pr.std()), 2)}
        b = B.book(T1[T1.setup == s], rules, ETB)
        dr = b.groupby("date").r.sum().reindex(live.index).fillna(0.0)
        c = live + dr
        e["live_overlap"] = {"cand_total": round(dr.sum(), 1), "combo_total": round(c.sum(), 1),
                             "combo_green": round(float((c > 0).mean()), 3),
                             "corr_live": round(float(np.corrcoef(dr, live)[0, 1]), 3) if dr.std() > 0 else None}
        out[s] = e
    return out
