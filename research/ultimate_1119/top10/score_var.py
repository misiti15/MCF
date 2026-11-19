"""Score every variant (bench_var / bench_var_earn trade rows) with bench10's costs, book and stats, booked under the
destination testing-account rules (bench10.TESTING_RULES), and apply the pre-registered PLAN.md rule.
    python score_var.py WORK            -> variants.json (this folder)
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bench10 as B  # noqa: E402
import bench_var as V  # noqa: E402
import bench_var_earn as E  # noqa: E402

# PLAN.md thresholds (fixed before any variant was scored)
TH = dict(comb_avg=-0.0383, chk_avg=-0.0464, comb_wo=-0.0674, chk_wo=-0.0781, comb_rps=-0.4862, chk_rps=-0.5218,
          t2_avg=-0.1048, min_n=20)
# round-6 disp gate, leave-one-window-out frozen cut-offs (gates.json BOOK-EM disp rot cfg.thr): no re-tuning
DISP_THR = {"T2": 3.1274, "fit": 2.579, "check": 2.6438}
GATED = {"BOOK-EM+disp": ["ULT-32-E", "ULT-32-M"], "leg-E+disp": ["ULT-32-E"]}
# promising parent (PLAN.md Tier B "derived"); "loose" = the mechanism is only partly the parent's
PARENT = {
    "ULT-01": "RW3-FD / RW5-FD (gap-down RSI5-pop fade short)",
    "ULT-02": None,
    "ULT-03": "ST7-FD (RSI14 collapse, broadened)",
    "ULT-04": "RW3-FD / RW5-FD (RSI5-pop fade short; loose: down-tape, not gap-down)",
    "ULT-05": "L3-gap-slope family (gap continuation; loose)",
    "ULT-06": None,
    "ULT-07": "NM-ETF-late-dip / WB4 (late-day dip; loose: stocks, RSI5 up-cross)",
    "ULT-08": None,
    "ULT-09": "CWT09-g10 (VWAP loss short; loose: no gap-down condition)",
    "ULT-10": "mixed book (legs 01/03/04/09 derive from RW3/RW5, ST7, CWT09; legs 02/06/08 do not)",
    "ULT-11": None, "ULT-19": None, "ULT-20": None, "ULT-21": None, "ULT-25": None,
    "ULT-12": "WB4 / NM-ETF-late-dip (widened to 205 ETFs)",
    "ULT-13": "ST7-FD (ADV $50M)",
    "ULT-14": "NM-ETF-late-dip / WB4 (14:00-15:00 dip, two-sided; loose)",
    "ULT-16": "ST7-FD (ULT-03 trigger, wide bracket; the frozen LMT entry runs as MKT live)",
    "ULT-22": "WB4 / NM-ETF-late-dip (12:30-15:00)",
    "ULT-23": "ST7-FD (mega-cap one-bar RSI collapse)",
    "ULT-26": "L3-gap-slope family (with-gap VWAP pullback; loose)",
    "ULT-32": "NM-ETF-late-dip / WB4 (leg E) + ST7-FD (leg M); leg D is a stock dip",
    "BOOK-EM": "NM-ETF-late-dip / WB4 (leg E) + ST7-FD (leg M)",
    "leg-E": "NM-ETF-late-dip / WB4 (exact WB4 list)",
    "leg-M": "ST7-FD (ADV >= $500M)",
    "H-V1": "NM-ETF-late-dip / WB4 (mirror: late ETF rip, short)",
    "H-V2": "ST7-FD one-bar collapse applied to ETFs (loose)",
    "BOOK-EM+disp": "NM-ETF-late-dip / WB4 + ST7-FD",
    "leg-E+disp": "NM-ETF-late-dip / WB4",
    "ULT-28": None, "ULT-30": None, "ULT-33": None, "ULT-34": None, "ULT-35": None,
}
OWNER_DECISION = {"leg-E+disp"}


def keyset(t):
    return set(zip(t.symbol.astype(str), t.date.astype(str)))


def main(W):
    W = Path(W)
    etb = pd.read_parquet(HERE / "etb_rate.parquet").rate
    spy1 = B.spy_t1()
    T1 = B.add_r(pd.read_parquet(W / "trades_t1.parquet"))
    T1["half"] = B.half(T1.date)
    t1_days = pd.Series(spy1.index)
    t1_days = t1_days[t1_days <= T1.date.max()]
    h1 = B.half(t1_days)
    nses = {"fit": int((h1 == "fit").sum()), "check": int((h1 == "check").sum())}
    nses["combined"] = nses["fit"] + nses["check"]
    spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
    spy2.index = spy2.index.astype(str)
    spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
    nses["T2"] = int(len(spy2))
    p2 = W / "trades_t2.parquet"
    T2 = B.add_r(pd.read_parquet(p2)) if p2.exists() else T1.iloc[:0].copy()
    B.no_locked(T1.date.unique())
    B.no_locked(T2.date.unique())
    disp = pd.read_parquet(W / "disp.parquet").disp
    rules = B.TESTING_RULES
    allv = {**V.VARIANTS, **E.EARN_VARIANTS, **GATED}
    out, books = {}, {}
    for v, entries in allv.items():
        b1s, b2s = [], []
        for en in entries:
            a1 = T1[T1.setup == en]
            a2 = T2[T2.setup == en]
            if v in GATED:
                d1 = a1.date.map(disp)
                thr1 = np.where(a1.half == "fit", DISP_THR["fit"], DISP_THR["check"])
                a1 = a1[(d1 >= thr1).to_numpy()]
                a2 = a2[(a2.date.map(disp) >= DISP_THR["T2"]).to_numpy()]
            b1s.append(B.book(a1, rules, etb))
            b2s.append(B.book(a2, rules, etb))
        b1 = pd.concat(b1s, ignore_index=True)
        b2 = pd.concat(b2s, ignore_index=True)
        books[v] = b1
        e = {"entries": entries,
             "T1_fit": B.stats(b1[b1.half == "fit"], nses["fit"], spy1),
             "T1_check": B.stats(b1[b1.half == "check"], nses["check"], spy1),
             "T1_combined": B.stats(b1[b1.half != "none"], nses["combined"], spy1),
             "T2": B.stats(b2, nses["T2"], spy2) if v not in E.EARN_VARIANTS else None,
             "raw_signals_T1": int(T1.setup.isin(entries).sum()), "raw_signals_T2": int(T2.setup.isin(entries).sum()),
             "by_entry_T1_combined": {en: B.stats(b1[(b1.setup == en) & (b1.half != "none")], nses["combined"], spy1)
                                      for en in entries if len(entries) > 1}}
        out[v] = e
    # ---- overlap: symbol-sessions on T1 (fit + check) vs the live top 10 + ST7-FD (home books) and vs other variants
    live = pd.read_parquet(Path(W).parent / "top10w" / "booked_trades.parquet")
    live = live[(live.test == "T1") & (live.half != "none")]
    lsets = {s: keyset(g) for s, g in live.groupby("setup")}
    vsets = {v: keyset(b[b.half != "none"]) for v, b in books.items()}
    for v, ks in vsets.items():
        n = len(ks)
        ov_live = {s: round(len(ks & S) / n, 3) for s, S in lsets.items()} if n else {}
        ov_var = {u: round(len(ks & S) / n, 3) for u, S in vsets.items() if u != v} if n else {}
        out[v]["overlap_live_max"] = max(ov_live.items(), key=lambda x: x[1]) if ov_live else None
        out[v]["overlap_var_max"] = max(ov_var.items(), key=lambda x: x[1]) if ov_var else None
        out[v]["overlap_var_ge70"] = sorted(u for u, x in ov_var.items() if x >= 0.7)
    # ---- the pre-registered rule
    for v, e in out.items():
        c, k, f, t2 = e["T1_combined"], e["T1_check"], e["T1_fit"], e["T2"]
        g = lambda d, kk: (d or {}).get(kk)  # noqa: E731
        n_chk, n_t2 = g(k, "trades") or 0, g(t2, "trades") or 0
        scorable = n_chk >= TH["min_n"] and n_t2 >= TH["min_n"]
        conds = {
            "comb_avg": (g(c, "avg_r") is not None) and c["avg_r"] >= TH["comb_avg"],
            "chk_avg": (g(k, "avg_r") is not None) and k["avg_r"] >= TH["chk_avg"],
            "comb_wo": (g(c, "avg_r_wo_best_day") is not None) and c["avg_r_wo_best_day"] >= TH["comb_wo"],
            "chk_wo": (g(k, "avg_r_wo_best_day") is not None) and k["avg_r_wo_best_day"] >= TH["chk_wo"],
            "comb_rps": (g(c, "trades") or 0) > 0 and c["total_r_per_session"] >= TH["comb_rps"],
            "chk_rps": n_chk > 0 and k["total_r_per_session"] >= TH["chk_rps"],
            "t2_avg": (g(t2, "avg_r") is not None) and t2["avg_r"] >= TH["t2_avg"],
        }
        meets = scorable and all(conds.values())
        a_c, t_c = g(c, "avg_r"), g(c, "t_day_clustered")
        leg1 = a_c is not None and t_c is not None and t_c == t_c and a_c <= -0.05 and t_c <= -2.0
        neg = lambda d: (g(d, "avg_r") is not None) and d["avg_r"] < -0.03  # noqa: E731
        leg2 = (neg(f) and neg(k) and neg(t2)) if n_t2 >= TH["min_n"] else (neg(f) and neg(k))
        nt = g(c, "trades") or 0
        e["rule"] = {"tierA_scorable": scorable, "conds": conds, "meets": meets, "really_bad_leg1": leg1,
                     "really_bad_leg2": leg2, "really_bad": leg1 or leg2, "T1_trades": nt,
                     "parent": PARENT.get(v), "owner_decision": v in OWNER_DECISION}
    (HERE / "variants.json").write_text(json.dumps({"note": "Educational only - not financial advice. Variants on the "
                                                    "normal-way engine (bench_var.py / bench10.py), testing-account book.",
                                                    "sessions": nses, "thresholds": TH, "disp_thr": DISP_THR,
                                                    "variants": out}, indent=1, default=float))
    rows = []
    for v, e in out.items():
        r = e["rule"]
        z = lambda d, kk: (d or {}).get(kk)  # noqa: E731
        rows.append({"v": v, "n_fit": z(e["T1_fit"], "trades"), "fit": z(e["T1_fit"], "avg_r"),
                     "n_chk": z(e["T1_check"], "trades"), "chk": z(e["T1_check"], "avg_r"),
                     "chk_wo": z(e["T1_check"], "avg_r_wo_best_day"), "chk_rps": z(e["T1_check"], "total_r_per_session"),
                     "comb": z(e["T1_combined"], "avg_r"), "comb_wo": z(e["T1_combined"], "avg_r_wo_best_day"),
                     "comb_rps": z(e["T1_combined"], "total_r_per_session"), "t": z(e["T1_combined"], "t_day_clustered"),
                     "share": z(e["T1_combined"], "best_day_share"),
                     "n_t2": z(e["T2"], "trades"), "t2": z(e["T2"], "avg_r"), "t2_wo": z(e["T2"], "avg_r_wo_best_day"),
                     "meets": r["meets"], "A_ok": r["tierA_scorable"], "bad": ("L1" if r["really_bad_leg1"] else "")
                     + ("L2" if r["really_bad_leg2"] else ""),
                     "ovL": e["overlap_live_max"], "ovV": e["overlap_var_max"]})
    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1])
