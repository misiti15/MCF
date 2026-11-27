"""PYRAMID L2 check stage (after fitsel.json freeze). Educational only - not financial advice."""
import json, sys
import numpy as np, pandas as pd
from score import *  # noqa

KEYS = ("trades", "trades_per_session", "avg_r", "avg_r_gross", "avg_r_wo_best_day", "best_day", "best_day_share", "t_day_clustered", "win", "be_win",
        "total_r_per_session", "worst_day", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down", "median_hold_min", "avg_r_wo_0403_0409")
PRIM = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "C4bench"]


def book_daily(T, days):
    parts = [booked(T, s, B.BOOK["primary"]).groupby("date").r.sum() for s in PRIM]
    return pd.concat(parts, axis=1).fillna(0).sum(axis=1).reindex(days).fillna(0)


def team(bk, cand, days):
    c = cand.groupby("date").r.sum().reindex(days).fillna(0)
    w = bk.nsmallest(10)
    return {"corr": round(float(np.corrcoef(c, bk)[0, 1]), 3), "R_on_book_10_worst": round(float(c[w.index].sum()), 2),
            "book_10_worst_R": round(float(w.sum()), 1), "worst_days": list(w.index)}


def run(T1, T2, names, spy1, D, spy2, show_team=True):
    res = {}
    f1 = B.half(pd.Series(D["check"]))
    ck = sorted(D["check"]); mid = ck[len(ck) // 2]
    alld = sorted(D["fit"] + D["check"])
    bk1 = book_daily(T1, alld) if show_team else None
    t2days = list(spy2.index)
    bk2 = book_daily(T2, t2days) if (show_team and T2 is not None) else None
    for k in names:
        b = booked(T1, k); r = booked(T1, "RND-" + k)
        e = {}
        for h in ("fit", "check"):
            e[h] = {x: st(b[b.half == h], D[h], spy1).get(x) for x in KEYS}
            e[h]["random_avg_r"] = round(float(r[r.half == h].r.mean()), 4) if (r.half == h).any() else None
        c = b[b.half == "check"]
        e["check_halves"] = [round(float(c[c.date < mid].r.mean()), 4), round(float(c[c.date >= mid].r.mean()), 4)]
        lw = c[c.date >= "2026-10-06"]
        e["check_liveoverlap_1006_1104"] = {"n": int(len(lw)), "avg_r": round(float(lw.r.mean()), 4) if len(lw) else None}
        if T2 is not None:
            b2 = booked(T2, k); r2 = booked(T2, "RND-" + k)
            e["T2"] = {x: st(b2, t2days, spy2).get(x) for x in KEYS}
            e["T2"]["random_avg_r"] = round(float(r2.r.mean()), 4) if len(r2) else None
            e["T2_by_year"] = {y: round(float(b2[b2.date.str[:4] == y].r.mean()), 4) for y in ("2023", "2024")}
        if show_team:
            e["team_T1"] = team(bk1, b[b.half != "none"], alld)
            if bk2 is not None:
                e["team_T2"] = team(bk2, b2, t2days)
        res[k] = e
    return res


if __name__ == "__main__":
    sel = json.load(open("fitsel.json"))["selection"]
    T1, T2 = load(); spy1, D, spy2 = sessions()
    mode = sys.argv[1]
    if mode == "selected":
        names = [sel[c] for c in ("C1", "C2", "C3", "C4")] + ["C4bench"]
    else:
        names = [k for c in CANDS.values() for k in c]
    out = run(T1, T2, names, spy1, D, spy2, show_team=(mode == "selected"))
    json.dump(out, open(f"check_{mode}.json", "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))
