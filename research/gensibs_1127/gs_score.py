"""GENSIBS-1127 scoring. Stage `fit`: FIT-only stats of the 56 configs -> top-5 finalists frozen in fit_pick.json.
Stage `all` (only after fit_pick.json exists): CHECK / T2 / FIT for every config, LIVE-L (headline) and LR8, same-gate
size-matched random control for the finalists, per-family sibling-vs-parent table.
Usage (cwd = repo root): python research/gensibs_1127/gs_score.py W fit|all. Locked block asserted absent.
Educational only - not financial advice."""
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd())); sys.path.insert(0, "research/ultimate_1119/top10"); sys.path.insert(0, "research/primshorts_1126")
sys.path.insert(0, str(Path(__file__).resolve().parent))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
import bench10 as B  # noqa: E402
import calib_live as CL  # noqa: E402
from gs_grid import CTX, PARENTS, grid  # noqa: E402

HERE = Path(__file__).resolve().parent
W = Path(sys.argv[1]); STAGE = sys.argv[2]
G = {x["id"]: x for x in grid()}
NR, MIN_FIT_N, NFIN = 500, 60, 5


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def load():
    fs = ("trades_t1",) if STAGE == "fit" else ("trades_t1", "trades_t2")     # FIT needs no T2 lots
    x = pd.concat([pd.read_parquet(W / f"{f}.parquet") for f in fs], ignore_index=True)
    x["date"] = x.date.astype(str)
    B.no_locked(x.date.unique())
    x = B.add_r(x)
    x["per"] = x.date.map(period)
    x = x[x.per != "none"].copy()
    cells = json.load(open("research/primshorts_1126/cells_live.json"))
    kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
    x["r_lr8"] = x.r
    x["r_livel"] = x.r_gross - CL.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd)
    etb = pd.read_parquet(W / "etb_rate.parquet").rate
    sess = {p: int(x.loc[x.per == p, "date"].nunique()) for p in ("FIT", "CHECK", "T2")}
    rnd = x[x.setup.str.startswith("RND-")]
    rnd = rnd[(rnd.entry >= 5) & ((rnd.side > 0) | rnd.symbol.map(etb).fillna(0).ge(0.9)) & (rnd.stop_cost_r <= 0.15)]
    parts = []
    for s, g in x[~x.setup.str.startswith("RND-")].groupby("setup"):
        parts.append(B.book(g, B.TESTING_RULES, etb))      # cap 100, <= 3 per symbol, cost filter, $5, ETB
    lots = pd.concat(parts, ignore_index=True)
    return lots, rnd, sess


def stats(g, col, nsess):
    if len(g) < 3:
        return {"n": int(len(g))}
    r, d = g[col], g.date
    day = r.groupby(d).sum(); tot = float(r.sum()); best = day.idxmax()
    m = float(r.mean()); e = (r - m).groupby(d).sum(); se = math.sqrt(float((e ** 2).sum())) / len(r)
    return {"n": int(len(r)), "days": int(day.size), "per_session": round(len(r) / nsess, 2), "avg": round(m, 4),
            "total": round(tot, 1), "t": round(m / se, 2) if se > 0 else None,
            "wo_best": round(float(r[d != best].mean()), 4) if (d != best).any() else None,
            "best_share": round(float(day.max() / tot), 3) if tot > 0 else None, "best_day": best,
            "green": round(float((day > 0).mean()), 3)}


def control(f, rnd, per, col, rng):
    c = G[f]; side = 1 if c["side"] == "long" else -1
    p = rnd[(rnd.setup == f"RND-{c['side']}-{c['geom']}") & (rnd.per == per) & (rnd.tod >= c["window"][0])
            & (rnd.tod <= c["window"][1]) & (rnd.adv20 >= c["min_adv"])]
    for nm, op, v in c["conds"]:
        if nm in CTX:
            a = p[nm].to_numpy(float)
            with np.errstate(invalid="ignore"):
                p = p[{"<": a < v, ">": a > v, "<=": a <= v, ">=": a >= v}[op]]
    assert (p.side == side).all()
    return p


def ctrl_draws(lots_f, pool, col, rng):
    need = lots_f.groupby("date").size()
    byd = {d: g[col].to_numpy() for d, g in pool.groupby("date")}
    days = [(d, n) for d, n in need.items() if d in byd]
    cov = sum(n for _, n in days) / max(1, need.sum())
    if not days:
        return None
    means = []
    for _ in range(NR):
        s = np.concatenate([rng.choice(byd[d], size=n, replace=True) for d, n in days])
        means.append(s.mean())
    act = lots_f[lots_f.date.isin([d for d, _ in days])][col].mean()
    means = np.array(means)
    return {"pool_n": int(len(pool)), "day_coverage": round(cov, 3), "ctrl_mean": round(float(means.mean()), 4),
            "ctrl_p95": round(float(np.quantile(means, 0.95)), 4), "actual_on_covered": round(float(act), 4),
            "pct_rank": round(float((means < act).mean() * 100), 1)}


if __name__ == "__main__":
    lots, rnd, sess = load()
    if STAGE == "fit":
        fit = {s: stats(lots[(lots.setup == s) & (lots.per == "FIT")], "r_livel", sess["FIT"]) for s in G}
        el = sorted([s for s in G if fit[s].get("n", 0) >= MIN_FIT_N and (fit[s].get("avg") or -1) > 0 and fit[s].get("t") is not None],
                    key=lambda s: -fit[s]["t"])
        fin = el[:NFIN]
        if len(fin) < NFIN:
            rest = sorted([s for s in G if s not in fin and fit[s].get("t") is not None and fit[s]["n"] >= MIN_FIT_N],
                          key=lambda s: -fit[s]["t"])
            fin += rest[:NFIN - len(fin)]
        json.dump({"sessions": sess, "eligible": el, "finalists": fin, "fit": fit}, open(HERE / "fit_pick.json", "w"), indent=1)
        for s in sorted(G, key=lambda s: -(fit[s].get("t") or -99)):
            print(s, G[s]["family"], G[s]["parent"], fit[s])
        print("finalists", fin)
        sys.exit()
    pick = json.load(open(HERE / "fit_pick.json"))
    fin = pick["finalists"]
    rows, res = [], {"sessions": sess, "finalists": fin, "configs": {}}
    for s in G:
        o = {}
        for per in ("FIT", "CHECK", "T2"):
            g = lots[(lots.setup == s) & (lots.per == per)]
            o[per] = {"livel": stats(g, "r_livel", sess[per]), "lr8": stats(g, "r_lr8", sess[per])}
            L = o[per]["livel"]
            rows.append(dict(id=s, family=G[s]["family"], parent=G[s]["parent"], period=per, n=L.get("n"), days=L.get("days"),
                             avg_livel=L.get("avg"), t=L.get("t"), wo_best=L.get("wo_best"), best_share=L.get("best_share"),
                             avg_lr8=o[per]["lr8"].get("avg"), finalist=s in fin))
        res["configs"][s] = o
    rng = np.random.default_rng(20261127)
    res["control"] = {}
    for f in fin:
        res["control"][f] = {}
        for per in ("FIT", "CHECK", "T2"):
            g = lots[(lots.setup == f) & (lots.per == per)]
            pool = control(f, rnd, per, "r_livel", rng)
            res["control"][f][per] = ctrl_draws(g, pool, "r_livel", rng) if len(g) else None
    # per-family: sibling minus its parent replica, per period (LIVE-L avg)
    par = {k: f"S{i + 1:02d}" for i, k in enumerate(PARENTS)}
    fam = {}
    for per in ("CHECK", "T2"):
        better, worse, d = 0, 0, []
        for s in G:
            if G[s]["family"] == "A-parent" or G[s]["family"] == "H-transplant":
                continue
            a = res["configs"][s][per]["livel"].get("avg"); b = res["configs"][par[G[s]["parent"]]][per]["livel"].get("avg")
            if a is None or b is None:
                continue
            d.append(a - b); better += a > b; worse += a < b
        fam[per] = {"siblings": len(d), "better": int(better), "worse": int(worse),
                    "median_diff": round(float(np.median(d)), 4) if d else None,
                    "mean_better": round(float(np.mean([x for x in d if x > 0])), 4) if better else None,
                    "mean_worse": round(float(np.mean([x for x in d if x < 0])), 4) if worse else None}
    res["vs_parent"] = fam
    # bars
    bars = {}
    for f in fin:
        c = res["configs"][f]; ck, t2 = c["CHECK"]["livel"], c["T2"]["livel"]
        ctl = res["control"][f]
        def ok(x, tmin):
            return bool(x.get("n", 0) >= 3 and (x.get("avg") or -1) > 0 and (x.get("t") or -9) >= tmin
                        and (x.get("wo_best") or -1) > 0 and (x.get("best_share") or 9) < 0.25)
        b = {"CHECK": ok(ck, 2.0), "T2": ok(t2, 2.6),
             "lr8_pos": bool((c["CHECK"]["lr8"].get("avg") or -1) > 0 and (c["T2"]["lr8"].get("avg") or -1) > 0),
             "control": bool(all(ctl[p] and ctl[p]["actual_on_covered"] > ctl[p]["ctrl_p95"] for p in ("CHECK", "T2"))),
             "lead": bool((ck.get("avg") or -1) > 0 and (t2.get("avg") or -1) > 0 and (ck.get("t") or -9) >= 1.5
                          and (t2.get("t") or -9) >= 1.5)}
        b["pass"] = b["CHECK"] and b["T2"] and b["lr8_pos"] and b["control"]
        bars[f] = b
    res["bars"] = bars
    res["verdict"] = "PASS" if any(b["pass"] for b in bars.values()) else (
        "LEAD" if any(b["lead"] and b["control"] for b in bars.values()) else "FAIL")
    json.dump(res, open(HERE / "results.json", "w"), indent=1, default=str)
    pd.DataFrame(rows).to_csv(HERE / "results.csv", index=False)
    print(json.dumps({"verdict": res["verdict"], "bars": bars, "vs_parent": fam, "control": res["control"]}, indent=1, default=str))
