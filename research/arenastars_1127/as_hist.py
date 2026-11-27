"""ARENASTARS-1127 Part B: history replay of G05 / G07 / G37 at their live config (as_gen.py lots), home testing book
(bench10.book: cap 100, <= 3 per symbol, cost filter 0.15, price >= $5, shorts ETB >= 90%), LIVE-L (headline) and LR8
costs, FIT / CHECK / T2, vs a size-matched random-entry control (500 draws from the RND pool, same day, same count).
Usage (cwd repo): python as_hist.py W OUTDIR. Locked block asserted absent. Educational only - not financial advice."""
import json
import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd())); sys.path.insert(0, "research/ultimate_1119/top10"); sys.path.insert(0, "research/primshorts_1126")
sys.path.insert(0, "research/arenastars_1127")
import bench10 as B  # noqa: E402
import calib_live as CL  # noqa: E402

W, OUT = Path(sys.argv[1]), Path(sys.argv[2])
SP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
TAGS = {"GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short": "G05",
        "GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short": "G07",
        "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long": "G37"}
NR = 500


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def lots(W):
    x = pd.concat([pd.read_parquet(W / f"{f}.parquet") for f in ("trades_t1", "trades_t2")], ignore_index=True)
    x["date"] = x.date.astype(str)
    B.no_locked(x.date.unique())
    x["tag"] = x.setup.map(TAGS).fillna(x.setup.str.replace("RND-", "RND-", regex=False))
    x = x[x.tag.isin(["G05", "G07", "G37", "RND-G05", "RND-G07", "RND-G37"])].copy()
    x = B.add_r(x)
    x["per"] = x.date.map(period)
    x = x[x.per != "none"]
    cells = json.load(open("research/primshorts_1126/cells_live.json"))
    kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
    x["r_lr8"] = x.r
    x["r_livel"] = x.r_gross - CL.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd)
    etb = pd.read_parquet(SP / "pyramid/S/etb_rate.parquet").rate
    x = x[x.entry >= 5.0]
    x = x[(x.side > 0) | x.symbol.map(etb).fillna(0).ge(0.9)]
    x = x[x.stop_cost_r <= 0.15]
    return x


def day_t(r, d):
    g = r.groupby(d).mean()
    return float(g.mean() / (g.std(ddof=1) / math.sqrt(len(g)))) if len(g) > 2 and g.std(ddof=1) > 0 else float("nan")


def stats(g, col, nsess):
    if not len(g):
        return {"n": 0}
    r, d = g[col], g.date
    day = r.groupby(d).sum()
    tot = float(r.sum()); best = day.idxmax()
    m = r.mean(); e = (r - m).groupby(d).sum(); se = math.sqrt(float((e ** 2).sum())) / len(r)
    return {"n": int(len(r)), "days": int(day.size), "sessions": int(nsess), "per_session": round(len(r) / nsess, 2),
            "avg": round(float(m), 4), "total": round(tot, 1), "t_clus": round(float(m / se), 2) if se > 0 else None,
            "t_day": round(day_t(r, d), 2), "wo_best": round(float(r[d != best].mean()), 4),
            "best_share": round(float(day.max() / tot), 3) if tot > 0 else None, "best_day": best,
            "green": round(float((day > 0).mean()), 3), "worst_day": round(float(day.min()), 1)}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    x = lots(W)
    spy = B.spy_t1()
    sess = {}
    s1 = pd.Series(sorted(set(pd.read_parquet(W / "trades_t1.parquet", columns=["date"]).date.astype(str))))
    s2 = pd.Series(sorted(set(pd.read_parquet(W / "trades_t2.parquet", columns=["date"]).date.astype(str))))
    alld = pd.concat([s1, s2]); B.no_locked(alld)
    for p in ("FIT", "CHECK", "T2"):
        sess[p] = int((alld.map(period) == p).sum())
    rng = np.random.default_rng(1127)
    res, rows = {}, []
    for tag in ("G05", "G07", "G37"):
        g = x[x.tag == tag].copy()
        g = g.assign(r=g.r_livel)
        bk = B.book(g, dict(cap=100, latch=None, cf=0.15, symcap=3), pd.Series(dtype=float).reindex([]) if False else
                    pd.read_parquet(SP / "pyramid/S/etb_rate.parquet").rate)
        pool = x[x.tag == "RND-" + tag]
        o = {}
        for p in ("FIT", "CHECK", "T2"):
            a = bk[bk.per == p]
            o[p] = {"livel": stats(a, "r_livel", sess[p]), "lr8": stats(a, "r_lr8", sess[p])}
            # regime split (SPY open->close +/-0.3%) on T1; T2 has no SPY map here -> by breadth sign of day R not used
            pl = pool[pool.per == p]
            o[p]["pool_avg_livel"] = round(float(pl.r_livel.mean()), 4) if len(pl) else None
            o[p]["pool_n"] = int(len(pl))
            if len(a) and len(pl):
                byd = {d: v.r_livel.to_numpy() for d, v in pl.groupby("date")}
                allp = pl.r_livel.to_numpy()
                cnt = a.groupby("date").size()
                draws = np.empty(NR)
                for i in range(NR):
                    acc = []
                    for d, k in cnt.items():
                        v = byd.get(d, allp)
                        acc.append(rng.choice(v, k, replace=True))
                    draws[i] = np.concatenate(acc).mean()
                o[p]["ctrl_mean"] = round(float(draws.mean()), 4)
                o[p]["ctrl_p95"] = round(float(np.percentile(draws, 95)), 4)
                o[p]["pct_vs_ctrl"] = round(float((draws < a.r_livel.mean()).mean() * 100), 1)
            if p != "T2" and len(a):
                ty = a.date.map(spy)
                o[p]["spy_regime"] = {k: [int((ty == k).sum()), round(float(a.r_livel[ty == k].mean()), 4) if (ty == k).any() else None]
                                      for k in ("up", "flat", "down")}
            # by year-month totals for concentration view
            o[p]["months"] = {k: [int(len(v)), round(float(v.r_livel.sum()), 1)] for k, v in a.groupby(a.date.str[:7])}
            rows.append({"setup": tag, "period": p, **{f"ll_{k}": v for k, v in o[p]["livel"].items()},
                         **{f"lr8_{k}": o[p]["lr8"].get(k) for k in ("avg", "t_clus", "wo_best")},
                         "ctrl_mean": o[p].get("ctrl_mean"), "ctrl_p95": o[p].get("ctrl_p95"), "pct": o[p].get("pct_vs_ctrl")})
        # pre-registered bars
        ch, t2 = o["CHECK"], o["T2"]
        def bars(q, tmin):
            L = q["livel"]
            return {"avg>0": bool(L.get("avg", -1) > 0), f"t>={tmin}": bool((L.get("t_clus") or -9) >= tmin),
                    "above_ctrl_p95": bool(q.get("ctrl_p95") is not None and L.get("avg", -9) > q["ctrl_p95"]),
                    "wo_best>0": bool((L.get("wo_best") or -1) > 0),
                    "best_share<25%": bool(L.get("best_share") is not None and L["best_share"] < 0.25)}
        o["bars"] = {"CHECK": bars(ch, 1.5), "T2": bars(t2, 2.6)}
        o["pass_B"] = all(o["bars"]["CHECK"].values()) and all(o["bars"]["T2"].values())
        res[tag] = o
        bk.assign(tag=tag)[["tag", "symbol", "date", "per", "tod", "side", "entry", "risk", "px", "kind", "xt", "r_lr8",
                            "r_livel"]].to_parquet(W / f"hist_{tag}.parquet")
        print(tag, "PASS_B" if o["pass_B"] else "fail_B", json.dumps(o["bars"]))
        for p in ("FIT", "CHECK", "T2"):
            print("  ", p, {k: v for k, v in o[p]["livel"].items() if k != "best_day"}, "lr8 avg", o[p]["lr8"].get("avg"),
                  "ctrl", o[p].get("ctrl_mean"), o[p].get("ctrl_p95"), "pct", o[p].get("pct_vs_ctrl"), o[p].get("spy_regime"))
    pd.DataFrame(rows).to_csv(OUT / "hist_results.csv", index=False)
    json.dump(res, open(OUT / "hist_results.json", "w"), indent=1, default=str)
