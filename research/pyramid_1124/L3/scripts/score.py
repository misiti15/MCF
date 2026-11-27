"""PYRAMID L3 scoring.  python score.py fit   -> fit table + fitsel.json (frozen B picks)
                        python score.py check -> everything (check once), results.json
Educational only - not financial advice."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import pyr

B = pyr.B
W = pyr.W
HERE = Path(__file__).resolve().parent
TEST = B.TESTING_RULES
PRIM = dict(cap=30, latch=-2.0, cf=None, symcap=3)
OURS = list(pyr.CFG)
PRIMARY = [s for s, _, _ in B.SETUPS]


def booked(T, cfg, rules, ctrl=0):
    t = T[(T.cfg == cfg) & (T.ctrl == ctrl)]
    if not len(t):
        return t
    etb = pd.Series(1.0, index=t.symbol.unique())   # no ETB snapshot on this machine; longs unaffected
    return B.book(t, rules, etb)


def load():
    T1 = B.add_r(pd.read_parquet(W / "trades_t1.parquet"))
    T1["half"] = B.half(T1.date)
    T1 = T1[T1.half != "none"]
    B.no_locked(T1.date.unique())
    spy1 = B.spy_t1()
    last = T1.date.max()
    days = pd.Series(spy1.index)
    days = days[days <= last]
    h = B.half(days)
    ses = {"fit": sorted(days[h == "fit"]), "check": sorted(days[h == "check"])}
    T2 = None
    if (W / "trades_t2.parquet").exists():
        T2 = B.add_r(pd.read_parquet(W / "trades_t2.parquet"))
        B.no_locked(T2.date.unique())
    spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
    spy2.index = spy2.index.astype(str)
    spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
    return T1, T2, spy1, spy2, ses


def st(t, n, spy):
    return B.stats(t, n, spy) if len(t) else {"trades": 0, "trades_per_session": 0.0}


def fit_stage():
    T1, _, spy1, _, ses = load()
    rows = {}
    for c in OURS:
        b = booked(T1, c, TEST)
        f = b[b.half == "fit"]
        s = st(f, len(ses["fit"]), spy1)
        day = f.groupby("date").r.sum() if len(f) else pd.Series(dtype=float)
        s["fit_total_minus_best"] = round(float(day.sum() - day.max()), 2) if len(day) else None
        rows[c] = s
    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows).T[["trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share",
                                "total_r", "fit_total_minus_best", "t_day_clustered", "median_hold_min"]].to_string())
    pick = {}
    for k in ("B1", "B2", "B3"):
        a, b = rows[k + "a"], rows[k + "b"]
        va = a.get("fit_total_minus_best") or -1e9
        vb = b.get("fit_total_minus_best") or -1e9
        pick[k] = k + ("a" if va >= vb else "b")
    out = {"frozen_utc": datetime.now(timezone.utc).isoformat(), "rule": "higher FIT total R minus best FIT day R",
           "picks": pick, "fit": rows}
    (HERE / "fitsel.json").write_text(json.dumps(out, indent=1, default=float))
    print(pick)


def daily(b, days):
    return b.groupby("date").r.sum().reindex(days, fill_value=0.0) if len(b) else pd.Series(0.0, index=days)


def check_stage():
    sel = json.loads((HERE / "fitsel.json").read_text())
    T1, T2, spy1, spy2, ses = load()
    alld = ses["fit"] + ses["check"]
    # Primary reference book (each setup in its own Primary book, then summed per day)
    pb = pd.concat([booked(T1, s, PRIM) for s in PRIMARY])
    pday = daily(pb, alld)
    worst10 = list(pday.sort_values().index[:10])
    res = {"frozen_picks": sel["picks"], "sessions": {k: len(v) for k, v in ses.items()}, "T2_sessions": int(len(spy2)),
           "primary_ref": {"T1_fit": st(pb[pb.half == "fit"], len(ses["fit"]), spy1),
                           "T1_check": st(pb[pb.half == "check"], len(ses["check"]), spy1),
                           "worst10_days": {d: round(float(pday[d]), 2) for d in worst10}}, "configs": {}}
    ch = ses["check"]
    c1, c2 = ch[: len(ch) // 2], ch[len(ch) // 2:]
    for c in OURS:
        b = booked(T1, c, TEST)
        r = booked(T1, c, TEST, ctrl=1)
        e = {}
        for hn in ("fit", "check"):
            x = b[b.half == hn]
            e[hn] = st(x, len(ses[hn]), spy1)
            y = r[r.half == hn]
            e[hn]["random_avg_r"] = round(float(y.r.mean()), 4) if len(y) else None
            e[hn]["vs_random"] = round(float(x.r.mean() - y.r.mean()), 4) if len(x) and len(y) else None
            e[hn]["win_break_even"] = round(float((-x.loc[x.r < 0, "r"].mean()) / (x.loc[x.r > 0, "r"].mean() - x.loc[x.r < 0, "r"].mean())), 3) if (x.r > 0).any() and (x.r < 0).any() else None
        x = b[b.half == "check"]
        e["check_halves"] = [round(float(x[x.date.isin(c1)].r.mean()), 4) if x.date.isin(c1).any() else None,
                             round(float(x[x.date.isin(c2)].r.mean()), 4) if x.date.isin(c2).any() else None]
        cd = daily(b, alld)
        e["corr_with_primary_daily"] = round(float(np.corrcoef(cd, pday)[0, 1]), 3) if cd.std() > 0 else None
        e["r_on_primary_worst10"] = round(float(cd[worst10].sum()), 2)
        e["n_on_primary_worst10"] = int(b.date.isin(worst10).sum())
        if T2 is not None:
            b2 = booked(T2, c, TEST)
            r2 = booked(T2, c, TEST, ctrl=1)
            e["T2"] = st(b2, len(spy2), spy2)
            e["T2"]["vs_random"] = round(float(b2.r.mean() - r2.r.mean()), 4) if len(b2) and len(r2) else None
        res["configs"][c] = e
    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
    rows = []
    for c, e in res["configs"].items():
        f, k, t2 = e["fit"], e["check"], e.get("T2", {})
        rows.append(dict(cfg=c, fit_n=f.get("trades"), fit_ps=f.get("trades_per_session"), fit_r=f.get("avg_r"),
                         fit_wo=f.get("avg_r_wo_best_day"), chk_n=k.get("trades"), chk_ps=k.get("trades_per_session"),
                         chk_r=k.get("avg_r"), chk_wo=k.get("avg_r_wo_best_day"), chk_share=k.get("best_day_share"),
                         chk_t=k.get("t_day_clustered"), chk_win=k.get("win"), be=k.get("win_break_even"),
                         halves=e["check_halves"], vs_rnd=k.get("vs_random"), t2_n=t2.get("trades"), t2_r=t2.get("avg_r"),
                         t2_wo=t2.get("avg_r_wo_best_day"), corr=e["corr_with_primary_daily"], w10=e["r_on_primary_worst10"],
                         hold=k.get("median_hold_min")))
    pd.set_option("display.width", 300)
    print(pd.DataFrame(rows).to_string(index=False))
    print("primary ref", {k: res["primary_ref"][k].get("avg_r") for k in ("T1_fit", "T1_check")}, res["primary_ref"]["worst10_days"])


if __name__ == "__main__":
    {"fit": fit_stage, "check": check_stage}[sys.argv[1]]()
