"""PYRAMID L1 scoring.  python score.py fit  -> fitsel.json (frozen)   |  python score.py check -> check.json
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(__file__).resolve().parent
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

CANDS = {"C1": ["C1_D1", "C1_D2"], "C2": ["C2_S03", "C2_S06"], "C3": ["C3_V15", "C3_V25"]}
PRIM_RULES = B.BOOK["primary"]
U = pd.read_csv("/home/user/MCF/data/universe.csv")
ETB = pd.Series(np.where(U.easy_to_borrow.astype(str) == "True", 1.0, 0.0), index=U.symbol)


def load(tag):
    t = pd.read_parquet(W / f"trades_{tag}.parquet")
    t = B.add_r(t)
    t["date"] = t.date.astype(str)
    return t


def booked(t, cfg, geo, kind_):
    x = t[(t.cfg == cfg) & (t.geo == geo) & (t.kind_ == kind_)]
    return B.book(x, B.TESTING_RULES, ETB)


def prim_book(t):
    parts = []
    for s in t[t.kind_ == "prim"].cfg.unique():
        parts.append(B.book(t[(t.kind_ == "prim") & (t.cfg == s)], PRIM_RULES, ETB))
    return pd.concat(parts, ignore_index=True)


def extra(b, sessions):
    o = {}
    if not len(b):
        return o
    w, l = b.r[b.r > 0], b.r[b.r <= 0]
    o["break_even_win"] = round(float(-l.mean() / (w.mean() - l.mean())), 3) if len(w) and len(l) else None
    d = sorted(sessions)
    mid = d[len(d) // 2]
    o["half1_avg_r"] = round(float(b[b.date < mid].r.mean()), 4) if (b.date < mid).any() else None
    o["half2_avg_r"] = round(float(b[b.date >= mid].r.mean()), 4) if (b.date >= mid).any() else None
    return o


def day_r(b, sessions):
    return b.groupby("date").r.sum().reindex(sorted(sessions), fill_value=0.0)


def sessions_t1():
    spy = B.spy_t1()
    last = "2026-11-04"
    days = [d for d in spy.index if d <= last]
    h = B.half(pd.Series(days))
    return spy, {k: [d for d, x in zip(days, h) if x == k] for k in ("fit", "check")}


def fit():
    spy, S = sessions_t1()
    t = load("fit")
    rows, res = [], {}
    for c, cfgs in CANDS.items():
        for cfg in cfgs:
            for geo in ("G1", "G2"):
                b = booked(t, cfg, geo, "sig")
                r = booked(t, cfg, geo, "ctl")
                s = B.stats(b, len(S["fit"]), spy)
                s.update(extra(b, S["fit"]))
                s["ctl_avg_r"] = round(float(r.r.mean()), 4) if len(r) else None
                res[f"{cfg}_{geo}"] = s
                rows.append({"cand": c, "config": f"{cfg}_{geo}", **{k: s.get(k) for k in (
                    "trades", "trades_per_session", "win", "break_even_win", "avg_r", "avg_r_gross", "avg_r_wo_best_day",
                    "best_day_share", "t_day_clustered", "ctl_avg_r", "median_hold_min")}})
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    sel = {}
    for c in CANDS:
        x = df[df.cand == c]
        y = x[x.trades >= 150]
        pick = (y.sort_values("avg_r", ascending=False) if len(y) else x.sort_values("trades", ascending=False)).iloc[0]
        sel[c] = pick.config
    out = {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "selected": sel, "fit": res,
           "configs_counted": 12}
    (W / "fitsel.json").write_text(json.dumps(out, indent=1, default=float))
    print("SELECTED", sel)


def card(b, ctl, sessions, spy):
    s = B.stats(b, len(sessions), spy)
    s.update(extra(b, sessions))
    s["ctl_avg_r"] = round(float(ctl.r.mean()), 4) if len(ctl) else None
    s["vs_random"] = round(s["avg_r"] - s["ctl_avg_r"], 4) if len(b) and len(ctl) else None
    return s


def check(plateau=False):
    sel = json.loads((W / "fitsel.json").read_text())["selected"]
    spy, S = sessions_t1()
    tf, tc = load("fit"), load("check")
    t2 = load("t2")
    spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
    spy2.index = spy2.index.astype(str)
    spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
    S2 = list(spy2.index)
    pb = {"fit": prim_book(tf), "check": prim_book(tc), "T2": prim_book(t2)}
    pdays = {"fit": day_r(pb["fit"], S["fit"]), "check": day_r(pb["check"], S["check"]), "T2": day_r(pb["T2"], S2)}
    live = pd.read_parquet(W.parent / "X/live_all.parquet")
    lp = live[(live.account == "primary")].copy()
    lp["date"] = lp.date.astype(str)
    lpd = lp.groupby("date").r.sum()
    lpd_ov = lpd[(lpd.index >= "2026-10-06") & (lpd.index <= "2026-11-04")]
    out = {"selected": sel, "primary_book": {k: {"avg_r": round(float(v.r.mean()), 4), "trades": len(v),
                                                 "total": round(float(v.r.sum()), 1)} for k, v in pb.items()}}
    todo = sel.items() if not plateau else [(c, f"{cfg}_{g}") for c, cfgs in CANDS.items() for cfg in cfgs for g in ("G1", "G2")]
    res = {}
    for c, conf in todo:
        cfg, geo = conf.rsplit("_", 1)
        e = {}
        for tag, t, ses, sp in (("fit", tf, S["fit"], spy), ("check", tc, S["check"], spy), ("T2", t2, S2, spy2)):
            b, ctl = booked(t, cfg, geo, "sig"), booked(t, cfg, geo, "ctl")
            e[tag] = card(b, ctl, ses, sp)
            if plateau:
                e[tag] = {k: e[tag].get(k) for k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day")}
                continue
            dr = day_r(b, ses)
            bk = pdays[tag]
            e[tag]["corr_with_primary_book"] = round(float(np.corrcoef(dr, bk)[0, 1]), 3)
            worst = bk.nsmallest(10)
            e[tag]["R_on_book_10_worst_days"] = round(float(dr.reindex(worst.index).sum()), 2)
            e[tag]["book_R_on_those_days"] = round(float(worst.sum()), 1)
            e[tag]["R_on_book_losing_days"] = round(float(dr[bk < 0].sum()), 1)
            e[tag]["R_on_book_winning_days"] = round(float(dr[bk > 0].sum()), 1)
            e[tag]["book_losing_days"] = int((bk < 0).sum())
            if tag == "check":
                ov = dr.reindex(lpd_ov.index).fillna(0)
                e["live_overlap"] = {"days": len(ov), "corr_with_live_primary": round(float(np.corrcoef(ov, lpd_ov)[0, 1]), 3),
                                     "cand_R": round(float(ov.sum()), 2), "live_primary_R": round(float(lpd_ov.sum()), 1),
                                     "cand_R_on_live_primary_5_worst": round(float(ov.reindex(lpd_ov.nsmallest(5).index).sum()), 2),
                                     "live_primary_5_worst": {k: round(float(v), 1) for k, v in lpd_ov.nsmallest(5).items()},
                                     "cand_on_those": {k: round(float(ov.get(k, 0)), 2) for k in lpd_ov.nsmallest(5).index}}
                e["check_worst_days"] = {k: round(float(v), 2) for k, v in dr.nsmallest(3).items()}
                e["check_best_days"] = {k: round(float(v), 2) for k, v in dr.nlargest(3).items()}
                e["check_by_month"] = b.groupby(b.date.str[:7]).r.agg(["size", "mean"]).round(3).to_dict("index")
        res[conf] = e
    out["results"] = res
    name = "plateau.json" if plateau else "check.json"
    (W / name).write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float)[:20000])


if __name__ == "__main__":
    {"fit": fit, "check": check, "plateau": lambda: check(True)}[sys.argv[1]]()
