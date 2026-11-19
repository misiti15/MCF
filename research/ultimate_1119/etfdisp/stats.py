"""ETFDISP stats: python stats.py WORK -> etfdisp/results.json (+ printed tables). Uses bench10 add_r / book / stats.
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "top10"))
import bench10 as B  # noqa: E402

DISP_MIN = 2.6438
W = Path(sys.argv[1])
STD = json.load(open(HERE.parent / "top10" / "benchmark.json"))["standard"]
TIER_A = {"T1_combined": dict(avg=-0.0383, wo=-0.0674, rps=-0.4862), "T1_check": dict(avg=-0.0464, wo=-0.0781, rps=-0.5218),
          "T2": dict(avg=-0.1048)}


def prep(t, cap):
    t = t.copy()
    if cap:
        t = t.drop(columns=["px", "kind", "xt"]).rename(columns={"px45": "px", "kind45": "kind", "xt45": "xt"})
    else:
        t = t.drop(columns=["px45", "kind45", "xt45"])
    return B.add_r(t)


spy1 = B.spy_t1()
spy1 = spy1[spy1.index <= "2026-11-04"]
h1 = B.half(pd.Series(spy1.index))
NS = {"fit": int((h1 == "fit").sum()), "check": int((h1 == "check").sum())}
NS["combined"] = NS["fit"] + NS["check"]
spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
spy2.index = spy2.index.astype(str)
spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
NS["T2"] = int(len(spy2))

T1r = pd.read_parquet(W / "t1.parquet")
T1r = T1r[T1r.date <= "2026-11-04"]
T2r = pd.read_parquet(W / "t2.parquet")
B.no_locked(T1r.date.unique())
B.no_locked(T2r.date.unique())
d1 = pd.read_parquet(W / "disp_t1.parquet").disp_prev
d2 = pd.read_parquet(W / "disp_t2.parquet").disp_prev

out = {"note": "Educational only - not financial advice. ETFDISP scored the normal filter way (bench10 engine), "
               "testing-arena book, LR8 costs.", "sessions": NS, "disp_min": DISP_MIN, "views": {}}
rules = B.TESTING_RULES
booked = {}
for cap in (True, False):
    view = "cap45" if cap else "nocap"
    T1, T2 = prep(T1r, cap), prep(T2r, cap)
    T1["half"] = B.half(T1.date)
    out["views"][view] = {}
    for s in ("ETFDISP", "LEG-E-ungated", "WB4"):
        b1 = B.book(T1[T1.setup == s], rules, {})
        b2 = B.book(T2[T2.setup == s], rules, {})
        booked[(view, s)] = (b1, b2)
        out["views"][view][s] = {"T1_fit": B.stats(b1[b1.half == "fit"], NS["fit"], spy1),
                                 "T1_check": B.stats(b1[b1.half == "check"], NS["check"], spy1),
                                 "T1_combined": B.stats(b1[b1.half != "none"], NS["combined"], spy1),
                                 "T2": B.stats(b2, NS["T2"], spy2),
                                 "raw_T1": int((T1.setup == s).sum()), "raw_T2": int((T2.setup == s).sum())}


def tier(e):
    c = []
    for k, th in TIER_A.items():
        z = e[k]
        c.append(z.get("avg_r", -9) is not None and z.get("avg_r", -9) >= th["avg"])
        if "wo" in th:
            c.append((z.get("avg_r_wo_best_day") or -9) >= th["wo"])
            c.append(z.get("total_r_per_session", -9) >= th["rps"])
    enough = e["T1_check"].get("trades", 0) >= 20 and e["T2"].get("trades", 0) >= 20
    bad1 = (e["T1_combined"].get("avg_r", 0) <= -0.05 and (e["T1_combined"].get("t_day_clustered") or 0) <= -2.0)
    legs = [e["T1_fit"].get("avg_r", 0), e["T1_check"].get("avg_r", 0)]
    if e["T2"].get("trades", 0) >= 20:
        legs.append(e["T2"].get("avg_r", 0))
    bad2 = all(x is not None and x < -0.03 for x in legs)
    return {"tier_a_conditions_met": int(sum(c)), "tier_a_conditions": len(c), "tier_a": bool(all(c) and enough),
            "enough_data": enough, "really_bad": bool(bad1 or bad2)}


for view in out["views"]:
    for s in out["views"][view]:
        out["views"][view][s]["verdict"] = tier(out["views"][view][s])

# gate open rate and parity with round 6
def openrate(d, lo, hi, nses_days):
    x = d[(d.index >= lo) & (d.index <= hi)]
    x = x[x.index.isin(nses_days)]
    return {"sessions": int(len(nses_days)), "known": int(x.notna().sum()), "open": int((x >= DISP_MIN).sum()),
            "open_share": round(float((x >= DISP_MIN).sum() / len(nses_days)), 3),
            "median_disp": round(float(x.median()), 3)}


fitd = [d for d, h in zip(spy1.index, h1) if h == "fit"]
chkd = [d for d, h in zip(spy1.index, h1) if h == "check"]
out["gate"] = {"T1_fit": openrate(d1, "2024-10-01", "2025-09-30", fitd), "T1_check": openrate(d1, "2025-10-01", "2026-11-04", chkd),
               "T2": openrate(d2, B.T2_LO, B.T2_HI, list(spy2.index))}
tf = pd.read_csv(HERE.parent / "round6" / "trades_features.csv.gz", usecols=["date", "disp"]).drop_duplicates("date")
tf = tf.set_index("date").disp
both = pd.concat([d1, d2]).groupby(level=0).first()
j = tf.to_frame("r6").join(both.rename("ours"), how="inner").dropna()
out["parity_round6"] = {"dates": int(len(j)), "max_abs_diff": round(float((j.r6 - j.ours).abs().max()), 6)}

# overlap (symbol-session) of ETFDISP with the live WB4 copy and the Primary parent, T1 combined, cap45 book
def ss(t):
    return set(zip(t.symbol, t.date))


e1 = ss(booked[("cap45", "ETFDISP")][0])
wb = ss(booked[("nocap", "WB4")][0])
bt = pd.read_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/top10w/booked_trades.parquet",
                     columns=["setup", "symbol", "date", "test"])
nm = ss(bt[(bt.setup == "NM-ETF-late-dip-di-long") & (bt.test == "T1")])
out["overlap_T1"] = {"etfdisp_symbol_sessions": len(e1),
                     "share_also_WB4": round(len(e1 & wb) / max(1, len(e1)), 3),
                     "share_also_NM_ETF_parent": round(len(e1 & nm) / max(1, len(e1)), 3)}

# remedy-style: what the gate removes from leg E (same rows, cap45)
rm = {}
for k, (lo, hi, dd) in {"T1_fit": (None, None, d1), "T1_check": (None, None, d1), "T2": (None, None, d2)}.items():
    b = booked[("cap45", "LEG-E-ungated")][0 if k != "T2" else 1]
    if k != "T2":
        b = b[b.half == k.split("_")[1]]
    g = b.date.map(dd)
    kept, drop, unk = b[g >= DISP_MIN], b[g < DISP_MIN], b[g.isna()]
    rm[k] = {"kept_n": int(len(kept)), "kept_avg_r": round(float(kept.r.mean()), 4) if len(kept) else None,
             "dropped_n": int(len(drop)), "dropped_avg_r": round(float(drop.r.mean()), 4) if len(drop) else None,
             "unknown_disp_n": int(len(unk))}
out["gate_split_legE"] = rm

# day-type split and best days for ETFDISP cap45
for k, i in (("T1", 0), ("T2", 1)):
    b = booked[("cap45", "ETFDISP")][i]
    day = b.groupby("date").r.sum().sort_values(ascending=False)
    out.setdefault("top_days", {})[k] = [(d, round(float(v), 2)) for d, v in day.head(3).items()]
    out.setdefault("monthly", {})[k] = {m: [int(len(g)), round(float(g.r.mean()), 3)] for m, g in b.groupby(b.date.str[:7])}

(HERE / "results.json").write_text(json.dumps(out, indent=1, default=float))
keys = ("trades", "trades_per_session", "sessions_traded", "win", "avg_r", "avg_r_wo_best_day", "best_day_share",
        "total_r", "total_r_per_session", "worst_day", "t_day_clustered", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down",
        "median_hold_min", "symbols")
for view in out["views"]:
    for s, e in out["views"][view].items():
        print("==", view, s, e["verdict"], "raw", e["raw_T1"], e["raw_T2"])
        print(pd.DataFrame({t: {k: e[t].get(k) for k in keys} for t in ("T1_fit", "T1_check", "T1_combined", "T2")}).to_string())
print(json.dumps({k: out[k] for k in ("gate", "parity_round6", "overlap_T1", "gate_split_legE", "top_days")}, indent=0))
