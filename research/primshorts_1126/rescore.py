"""PRIMSHORTS-1126 task 2-3: re-score Primary's 3 shorts + PSHADOW's 2 on bench10 (FIT / CHECK / T2) with the research
LR8 basis and the live-calibrated LIVE-L costs (cells_live.json), and the live record side by side. Cost fix only:
same signals, exits, books (bench10 book(): Primary rules = cap 30, <= 3 lots/symbol, -2R realised latch; also each
setup's home rules), +0 configurations. Usage: python rescore.py WORK LIVEDIR. Educational only - not financial advice."""
import json, math, os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(H + "/../..")
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/research/ultimate_1119/top10"); sys.path.insert(0, H)
import bench10 as B  # noqa: E402
import calib_live as CL  # noqa: E402
W, LV = sys.argv[1], sys.argv[2]
CELLS = json.load(open(H + "/cells_live.json"))
SETUPS = {"L3-gap-slope-fromopen-FD": "primary", "RW3-gapdn-rsi5pop-flowsell-short-FD": "primary",
          "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "primary", "L3-gap-slope-rsi5hi-FD": "testing",
          "RW6-ns2-up3-short-FD": "livelab"}
SHORT = {"L3-gap-slope-fromopen-FD": "L3-fromopen", "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3",
         "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5", "L3-gap-slope-rsi5hi-FD": "L3-rsi5hi",
         "RW6-ns2-up3-short-FD": "RW6", "NM-ETF-late-dip-di-long": "NM-ETF"}
ETB = pd.read_parquet(H + "/etb_rate.parquet").rate


def period(d):
    d = str(d)
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def costs(t):
    """bench10 add_r (LR8 research) + LIVE-L column; r_gross untouched."""
    t = B.add_r(t)
    t["date"] = t.date.astype(str)
    kd = np.where(t.kind == 2, "target", np.where(t.kind == 1, "stop", "market"))
    t["r_lr8"] = t.r
    t["r_live"] = t.r_gross - CL.predict_R(CELLS, t.entry.to_numpy(), t.risk.to_numpy(), kd)
    t["per"] = t.date.map(period)
    return t


def load_trades(work):
    x = pd.concat([pd.read_parquet(f"{work}/trades_t1.parquet"), pd.read_parquet(f"{work}/trades_t2.parquet")], ignore_index=True)
    x = costs(x)
    x = x[x.per != "none"].copy()
    B.no_locked(x.date.unique())
    return x


def nsess():
    s1 = B.spy_t1(); d1 = [d for d in s1.index if d <= "2026-11-04"]
    sp2 = pd.read_parquet(B.FRESH / "spy_days.parquet"); sp2.index = sp2.index.astype(str)
    d2 = [d for d in sp2.index if B.T2_LO <= d <= B.T2_HI]
    p = pd.Series(d1).map(period)
    return {"FIT": int((p == "FIT").sum()), "CHECK": int((p == "CHECK").sum()), "T2": len(d2)}


def st(t, col, n_ses, tod_col="tod"):
    if not len(t):
        return {"n": 0}
    r = t[col]; day = r.groupby(t.date).sum(); tot = float(r.sum()); best = day.idxmax()
    m = r.mean(); e = (r - m).groupby(t.date).sum(); se = math.sqrt(float((e ** 2).sum())) / len(t)
    am = t[tod_col] < 1200
    return {"n": int(len(t)), "days": int(day.size), "tps": round(len(t) / n_ses, 2) if n_ses else None,
            "avg": round(float(m), 4), "wo_best": round(float(r[t.date != best].mean()), 4) if (t.date != best).any() else None,
            "best_day": str(best), "best_share": round(float(day.max() / tot), 2) if tot > 0 else None,
            "t_day": round(float(m / se), 2) if se > 0 else None, "worst5": round(float(day.nsmallest(5).sum()), 2),
            "worst5_days": [f"{d}:{v:.1f}" for d, v in day.nsmallest(5).items()],
            "am_avg": round(float(r[am].mean()), 4) if am.any() else None, "am_n": int(am.sum()),
            "pm_avg": round(float(r[~am].mean()), 4) if (~am).any() else None, "pm_n": int((~am).sum()),
            "total": round(tot, 1), "per_session": round(tot / n_ses, 3) if n_ses else None}


def live_stats(lv):
    t = pd.read_parquet(lv + "/live.parquet")
    t = t[t.r.notna()].copy()
    tt = pd.to_datetime(t.entry_time.astype(str), utc=True, format="mixed").dt.tz_convert("America/New_York")
    t["tod"] = tt.dt.hour * 100 + tt.dt.minute
    out = {}
    for s in list(SETUPS) + ["NM-ETF-late-dip-di-long"]:
        a = t[t.strategy == s]
        if not len(a):
            continue
        a = a.sort_values("account").drop_duplicates(["symbol", "date", "tod"])   # same signal in two accounts once
        out[s] = {"all_accounts": st(a, "r", a.date.nunique()), "accounts": a.account.value_counts().to_dict()}
        p = a[a.account == "primary"]
        if len(p):
            out[s]["primary"] = st(p, "r", p.date.nunique())
    return out


if __name__ == "__main__":
    x = load_trades(W)
    ns = nsess()
    res = {"note": "Educational only - not financial advice. PRIMSHORTS-1126 re-score (cost fix only, +0 configs).",
           "sessions": ns, "setups": {}}
    rows = []
    for s, home in SETUPS.items():
        e = {}
        for view, rules in (("primary_rules", B.BOOK["primary"]), ("home_rules", B.BOOK[home])):
            if view == "home_rules" and home == "primary":
                continue
            bk = B.book(x[x.setup == s], rules, ETB)
            e[view] = {}
            for per in ("FIT", "CHECK", "T2"):
                b = bk[bk.per == per]
                e[view][per] = {"lr8": st(b, "r_lr8", ns[per]), "live": st(b, "r_live", ns[per]),
                                "cost_lr8": round(float((b.r_gross - b.r_lr8).mean()), 4) if len(b) else None,
                                "cost_live": round(float((b.r_gross - b.r_live).mean()), 4) if len(b) else None,
                                "med_px": round(float(b.entry.median()), 1) if len(b) else None,
                                "lt20": round(float((b.entry < 20).mean()), 2) if len(b) else None,
                                "med_w_bps": round(float((b.risk / b.entry * 1e4).median()), 0) if len(b) else None}
                if view == "primary_rules":
                    z = e[view][per]
                    rows.append([SHORT[s], per, z["live"]["n"], z["lr8"]["avg"], z["live"]["avg"], z["live"]["wo_best"],
                                 z["live"]["best_share"], z["live"]["t_day"], z["live"]["worst5"], z["live"]["am_avg"],
                                 z["live"]["pm_avg"], z["cost_lr8"], z["cost_live"], z["lt20"], z["med_w_bps"]])
        res["setups"][s] = e
    res["live"] = live_stats(LV)
    json.dump(res, open(H + "/rescore.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows, columns=["setup", "per", "n", "avgLR8", "avgLIVE", "woBest", "bestSh", "tDay", "worst5", "AM", "PM",
                                      "costLR8", "costLIVE", "lt20", "wbps"]).to_string(index=False))
    for s, v in res["live"].items():
        for k in ("all_accounts", "primary"):
            if k in v:
                z = v[k]
                print("LIVE", SHORT[s], k, z["n"], z["days"], z["avg"], z["wo_best"], z["best_day"], z["best_share"], z["t_day"],
                      z["worst5"], "AM", z["am_avg"], z["am_n"], "PM", z["pm_avg"], z["pm_n"])
