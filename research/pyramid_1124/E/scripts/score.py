"""PYRAMID team E scoring.  python score.py fit -> fitsel.json (frozen) | check -> check.json | plateau -> plateau.json
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

CANDS = {"E1": ["E1_X3", "E1_X5"], "E2": ["E2_G05", "E2_G10"], "E3": ["E3_S03", "E3_S06"]}
UCTL = {"E1": "U20", "E2": "U100", "E3": "U20"}
U = pd.read_csv("/home/user/MCF/data/universe.csv")
ETB = pd.Series(np.where(U.easy_to_borrow.astype(str) == "True", 1.0, 0.0), index=U.symbol)


def load(T):
    t = pd.read_parquet(W / f"trades_{T}.parquet")
    t = B.add_r(t)
    t["date"] = t.date.astype(str)
    return t


def bk(t, cfg, geo, kind_, ses=None):
    x = t[(t.cfg == cfg) & (t.geo == geo) & (t.kind_ == kind_)]
    if ses is not None:
        x = x[x.date.isin(ses)]
    return B.book(x, B.TESTING_RULES, ETB)


def sessions():
    spy = B.spy_t1()
    days = [d for d in spy.index if d <= "2026-11-04"]
    h = B.half(pd.Series(days))
    S = {k: [d for d, x in zip(days, h) if x == k] for k in ("fit", "check")}
    s2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
    s2.index = s2.index.astype(str)
    s2 = s2[(s2.index >= B.T2_LO) & (s2.index <= B.T2_HI)]["type"]
    S["T2"] = list(s2.index)
    return spy, s2, S


def extra(b, ses):
    o = {}
    if not len(b):
        return o
    w, l = b.r[b.r > 0], b.r[b.r <= 0]
    o["break_even_win"] = round(float(-l.mean() / (w.mean() - l.mean())), 3) if len(w) and len(l) else None
    d = sorted(ses)
    mid = d[len(d) // 2]
    o["half1_avg_r"] = round(float(b[b.date < mid].r.mean()), 4) if (b.date < mid).any() else None
    o["half2_avg_r"] = round(float(b[b.date >= mid].r.mean()), 4) if (b.date >= mid).any() else None
    o["exit_mix"] = {str(k): int(v) for k, v in b.kind.value_counts().items()}
    return o


def card(t, cand, cfg, geo, ses, spy):
    b = bk(t, cfg, geo, "sig", ses)
    s = B.stats(b, len(ses), spy)
    s.update(extra(b, ses))
    for kind_, key in (("ctl_sd", cfg), ("ctl_u", UCTL[cand]), ("ctl_pool", cfg)):
        c = bk(t, key, geo, kind_, ses)
        if len(c):
            s[f"{kind_}_avg_r"] = round(float(c.r.mean()), 4)
            s[f"{kind_}_n"] = int(len(c))
            ty = c.date.map(spy)
            s[f"{kind_}_spy_up_flat_down"] = [round(float(c.r[ty == k].mean()), 4) if (ty == k).any() else None
                                              for k in ("up", "flat", "down")]
            if len(b):
                s[f"vs_{kind_}"] = round(s["avg_r"] - s[f"{kind_}_avg_r"], 4)
    return s, b


def prim_days(S):
    L1 = W.parent / "L1"
    out = {}
    for tag, f in (("fit", "trades_fit"), ("check", "trades_check"), ("T2", "trades_t2")):
        t = pd.read_parquet(L1 / f"{f}.parquet")
        t = B.add_r(t[t.kind_ == "prim"])
        t["date"] = t.date.astype(str)
        parts = [B.book(t[t.cfg == s], B.BOOK["primary"], ETB) for s in t.cfg.unique()]
        p = pd.concat(parts, ignore_index=True)
        out[tag] = p.groupby("date").r.sum().reindex(sorted(S[tag]), fill_value=0.0)
    return out


def fit():
    spy, _, S = sessions()
    t = load("T1")
    res, rows = {}, []
    for cand, cfgs in CANDS.items():
        for cfg in cfgs:
            for geo in ("G1", "G2"):
                s, _ = card(t, cand, cfg, geo, S["fit"], spy)
                res[f"{cfg}_{geo}"] = s
                rows.append({"cand": cand, "config": f"{cfg}_{geo}", **{k: s.get(k) for k in (
                    "trades", "trades_per_session", "win", "break_even_win", "avg_r", "avg_r_gross", "avg_r_wo_best_day",
                    "best_day_share", "t_day_clustered", "ctl_sd_avg_r", "ctl_u_avg_r", "median_hold_min")}})
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    sel = {}
    for c in CANDS:
        x = df[df.cand == c]
        y = x[x.trades >= 100]
        pick = (y.sort_values("avg_r", ascending=False) if len(y) else x.sort_values("trades", ascending=False)).iloc[0]
        sel[c] = pick.config
    out = {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "selected": sel, "fit": res,
           "configs_counted": 12}
    (W / "fitsel.json").write_text(json.dumps(out, indent=1, default=float))
    print("SELECTED", sel)


def check(plateau=False):
    sel = json.loads((W / "fitsel.json").read_text())["selected"]
    spy, spy2, S = sessions()
    t1, t2 = load("T1"), load("T2")
    pdays = prim_days(S)
    live = pd.read_parquet(W.parent / "X/live_all.parquet")
    lp = live[live.account == "primary"].copy()
    lp["date"] = lp.date.astype(str)
    lpd = lp.groupby("date").r.sum()
    lpd = lpd[(lpd.index >= "2026-10-06") & (lpd.index <= "2026-11-04")]
    out = {"selected": sel, "primary_proxy_total": {k: round(float(v.sum()), 1) for k, v in pdays.items()}}
    todo = sel.items() if not plateau else [(c, f"{cfg}_{g}") for c, cfgs in CANDS.items() for cfg in cfgs
                                            for g in ("G1", "G2")]
    res = {}
    for cand, conf in todo:
        cfg, geo = conf.rsplit("_", 1)
        e = {}
        for tag, t, sp in (("fit", t1, spy), ("check", t1, spy), ("T2", t2, spy2)):
            s, b = card(t, cand, cfg, geo, S[tag], sp)
            if plateau:
                e[tag] = {k: s.get(k) for k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day",
                                                 "ctl_u_avg_r")}
                continue
            dr = b.groupby("date").r.sum().reindex(sorted(S[tag]), fill_value=0.0)
            bkd = pdays[tag]
            s["corr_with_primary_proxy"] = round(float(np.corrcoef(dr, bkd)[0, 1]), 3)
            worst = bkd.nsmallest(10)
            s["R_on_proxy_10_worst_days"] = round(float(dr.reindex(worst.index).sum()), 2)
            s["proxy_R_on_those_days"] = round(float(worst.sum()), 1)
            s["traded_on_proxy_10_worst"] = int((dr.reindex(worst.index) != 0).sum())
            s["worst_days"] = {k: round(float(v), 2) for k, v in dr.nsmallest(3).items()}
            s["best_days"] = {k: round(float(v), 2) for k, v in dr.nlargest(3).items()}
            s["by_month"] = {k: [int(v["size"]), round(float(v["mean"]), 3)] for k, v in
                             b.groupby(b.date.str[:7]).r.agg(["size", "mean"]).to_dict("index").items()}
            if tag == "T2":
                s["by_year"] = {k: [int(v["size"]), round(float(v["mean"]), 4)] for k, v in
                                b.groupby(b.date.str[:4]).r.agg(["size", "mean"]).to_dict("index").items()}
            if tag == "check":
                ov = dr.reindex(lpd.index).fillna(0)
                s["live_overlap_10_06_11_04"] = {"days": len(ov), "corr_with_live_primary": round(
                    float(np.corrcoef(ov, lpd)[0, 1]), 3), "cand_R": round(float(ov.sum()), 2),
                    "live_primary_R": round(float(lpd.sum()), 1),
                    "cand_R_on_live_primary_5_worst": round(float(ov.reindex(lpd.nsmallest(5).index).sum()), 2)}
            e[tag] = s
        res[conf] = e
    out["results"] = res
    name = "plateau.json" if plateau else "check.json"
    (W / name).write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float)[:30000])


if __name__ == "__main__":
    {"fit": fit, "check": check, "plateau": lambda: check(True)}[sys.argv[1]]()
