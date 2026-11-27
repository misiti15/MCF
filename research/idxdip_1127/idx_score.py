"""IDXDIP-1127 scoring (PREREG.md): LIVE-L / LR8 costs, stress S1 (+1 min), S2 (+2 bp/side), S12, per-split stats,
size-matched random-day control, H-FAM, robust-region lattice, book impact and correlation with Primary's base-book
daily R (regsteer_1126 base.parquet). Locked block never read (asserted).
    python research/idxdip_1127/idx_score.py OUT_DIR RAW_DIR[,RAW_DIR2] PRIMARY_BASE_PARQUET
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
import idx_sim  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402

CELLS = json.load(open(HERE.parent / "primshorts_1126/cells_live.json"))
PB = [0, 5, 10, 20, 50, 100, 1e9]; PBL = ["<5", "5-10", "10-20", "20-50", "50-100", "100+"]
KIND = {0: "market", 1: "stop", 2: "target"}
LOCK = ("2024-11-01", "2025-02-28")
SPLITS = ["EARLY", "T2", "FIT", "CHECK"]
TBAR = float(np.sqrt(2 * np.log(40)))


def nolock(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked row"


def costs(t):
    price = t.entry.to_numpy(float); risk = t.risk.to_numpy(float); kind = t.kind.to_numpy(int)
    pb = pd.cut(price, PB, labels=PBL, right=False).astype(str)
    ab = np.array([CELLS.get(f"{p}|{KIND[k]}", CELLS[f"*|{KIND[k]}"])[:2] for p, k in zip(pb, kind)])
    t["c_livel"] = ab[:, 0] / (risk / price * 1e4) + ab[:, 1]
    side = t.side.to_numpy(); px = t.exit_px.to_numpy(float)
    tier = np.where(price < 5, 3.0, 1.0)
    ec = (0.01 + price * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xc = 0.01 + px * 1e-4 + np.where(kind == 1, 0.02, 0.0)
    br = np.where(side < 0, 1.2e-4 * price, 0.0)
    t["c_lr8"] = (tier * (ec + xc) + br) / risk
    t["c_2bp"] = 2e-4 * (price + px) / risk
    t["r_livel"] = t.gross - t.c_livel
    t["r_lr8"] = t.gross - t.c_lr8
    t["r_2bp"] = t.r_livel - t.c_2bp
    return t


def st(x, d):
    x = np.asarray(x, float); n = len(x)
    if n == 0:
        return dict(n=0)
    s = pd.Series(x).groupby(np.asarray(d)).sum().to_numpy()
    m = s.mean(); sd = s.std(ddof=1) if len(s) > 1 else np.nan
    tot = x.sum(); best = s.max()
    return dict(n=n, days=len(s), mean=round(float(x.mean()), 3), tot=round(float(tot), 2),
                t=round(float(m / (sd / np.sqrt(len(s)))), 2) if len(s) > 1 and sd > 0 else None,
                win=round(float((x > 0).mean()), 3),
                best_share=round(float(best / tot), 3) if tot > 0 else None,
                wo_best=round(float((tot - best) / (n - 1)), 3) if n > 1 else None)


@numba.njit(cache=False)
def sim_nb(o, h, l, c, mins, j, fill, stop, side, exit_min, trail, tgt):
    risk = side * (fill - stop)
    mfe = 0.0
    n = len(o)
    tp = fill + side * tgt * risk
    for k in range(j, n):
        if mins[k] >= exit_min:
            return side * (o[k] - fill) / risk
        hit = (l[k] <= stop) if side == 1 else (h[k] >= stop)
        if hit:
            gap = (o[k] < stop) if side == 1 else (o[k] > stop)
            px = o[k] if (gap and k > j) else stop
            return side * (px - fill) / risk
        if tgt > 0:
            th = (h[k] >= tp) if side == 1 else (l[k] <= tp)
            if th:
                gap = (o[k] > tp) if side == 1 else (o[k] < tp)
                px = o[k] if (gap and k > j) else tp
                return side * (px - fill) / risk
        fav = h[k] if side == 1 else l[k]
        v = side * (fav - fill) / risk
        if v > mfe:
            mfe = v
        if trail and mfe >= 1.0:
            tr = fill + side * (mfe - 1.0) * risk
            if side == 1:
                stop = max(stop, tr)
            else:
                stop = min(stop, tr)
    return side * (c[n - 1] - fill) / risk


def control(tr, days, ex, draws, rng):
    actual = tr.r_livel.mean()
    sig_days = set(tr.date)
    pools = {s: [d for d in days if idx_sim.qo_sim.split_of(pd.Timestamp(d).date()) == s and d not in sig_days] for s in SPLITS}
    rows = tr[["split", "emin", "stop_pct", "side", "c_livel"]].to_numpy()
    means = np.empty(draws)
    trail = ex == "TRAIL"; tgt = 2.0 if ex == "TGT2" else 0.0
    for b in range(draws):
        rs = []
        for sp, em, spct, side, cst in rows:
            for _ in range(20):
                d = pools[sp][rng.integers(len(pools[sp]))]
                o, h, l, c, mins = days[d]
                js = np.searchsorted(mins, em)
                if js < len(mins) - 1 and mins[js] == em:
                    break
            fill = o[js]; stop = fill * (1 - side * spct / 100)
            exit_min = min(955, mins[-1] + 1 - 5)
            rs.append(sim_nb(o, h, l, c, mins, js, fill, stop, int(side), exit_min, trail, tgt) - cst)
        means[b] = np.mean(rs)
    return dict(actual=round(float(actual), 3), ctrl_mean=round(float(means.mean()), 3),
                ctrl_p95=round(float(np.quantile(means, 0.95)), 3), pct=round(float((means < actual).mean()), 3))


def main(out, raws, base_pq):
    out = Path(out); raws = [Path(r) for r in raws.split(",")]
    t = pd.read_csv(out / "idx_trades.csv.gz"); nolock(t.date.unique())
    t = costs(t)
    ctx = pd.read_csv(out / "idx_ctx.csv.gz")
    t = t.merge(ctx[["date", "sig", "above50"]], on=["date", "sig"], how="left")
    B = t[t["var"] == "BASE"].copy(); S1 = t[t["var"] == "S1"].copy()
    cfgs = {c["name"]: c for c in idx_sim.configs()}
    traded = {}
    for s in ("SPXL", "TQQQ", "TNA", "UDOW"):
        df = idx_sim.load(s, raws)
        traded[s] = {str(d): (g.open.to_numpy(float), g.high.to_numpy(float), g.low.to_numpy(float),
                              g.close.to_numpy(float), idx_sim.qo_sim.tmin(g.index).astype(np.int64))
                     for d, g in df.groupby(df.index.date) if len(g) >= 60}
        nolock(traded[s].keys())
    rng = np.random.default_rng(20261127)
    res = {"n_configs": len(cfgs), "t_bar": round(TBAR, 2), "configs": {}}
    dayR = {}
    for name, cf in cfgs.items():
        g = B[B.name == name]; g1 = S1[S1.name == name]
        r = {"ALL": st(g.r_livel, g.date), "ALL_lr8": st(g.r_lr8, g.date), "ALL_gross": st(g.gross, g.date),
             "S1": st(g1.r_livel, g1.date), "S2": st(g.r_2bp, g.date), "S12": st(g1.r_2bp, g1.date)}
        for s in SPLITS:
            gs = g[g.split == s]; r[s] = st(gs.r_livel, gs.date); r[s + "_lr8"] = st(gs.r_lr8, gs.date)
            g1s = g1[g1.split == s]; r[s + "_S12"] = st(g1s.r_2bp, g1s.date)
        for a, x in g.groupby("above50"):
            r[f"above50={a}"] = st(x.r_livel, x.date)
        r["years"] = g.groupby(g.date.str[:4]).r_livel.agg(["size", "mean"]).round(3).reset_index().to_dict("records")
        r["control"] = control(g, traded[cf["trd"]], cf["exit"], 500, rng) if len(g) >= 5 else None
        a = r["ALL"]
        r["crit"] = {
            "1_pos_E_T2_C": all((r[s].get("mean") or -9) > 0 for s in ("EARLY", "T2", "CHECK")),
            "2_t_ge_2.72": (a.get("t") or 0) >= TBAR,
            "3_conc": (a.get("wo_best") or -9) > 0 and (a.get("best_share") or 9) < 0.5,
            "4_ctrl_p95": bool(r["control"] and r["control"]["actual"] > r["control"]["ctrl_p95"]),
            "5_S12": (r["S12"].get("mean") or -9) > 0 and (r["S12"].get("t") or 0) >= 1.65,
        }
        res["configs"][name] = r
        dayR[name] = g.groupby("date").r_livel.sum()
        dayR[name + "#S12"] = g1.groupby("date").r_2bp.sum()
        print(name, {k: r[k].get("mean") for k in ("EARLY", "T2", "FIT", "CHECK")}, "ALL", a.get("n"), a.get("mean"),
              a.get("t"), "S1", r["S1"].get("mean"), "S12", r["S12"].get("mean"), r["S12"].get("t"),
              "ctrl", r["control"] and r["control"]["pct"], flush=True)
    # ---- lattice / region
    G1 = [n for n in cfgs if n.startswith("G1")]
    def key(n):
        c = cfgs[n]; return (c["sig"], [0.75, 1.0, 1.5].index(c["X"]), [585, 595, 615].index(c["T"]))
    pos = {key(n): n for n in G1}
    def nbrs(n):
        s, xi, ti = key(n)
        return [pos[k] for k in ((s, xi - 1, ti), (s, xi + 1, ti), (s, xi, ti - 1), (s, xi, ti + 1)) if k in pos]
    C = res["configs"]
    for n in G1:
        nb = nbrs(n)
        C[n]["crit"]["6_nbrs_pos"] = all((C[m]["ALL"].get("mean") or -9) > 0 and (C[m]["S12"].get("mean") or -9) > 0 for m in nb)
        C[n]["robust_point"] = all(C[n]["crit"].values())
        C[n]["region_member"] = bool(C[n]["crit"]["1_pos_E_T2_C"] and C[n]["crit"]["5_S12"] and (C[n]["ALL"].get("t") or 0) >= 2.0)
    for n in cfgs:
        if not n.startswith("G1"):
            C[n]["pass_1_5"] = all(C[n]["crit"].values())
    # connected components of region members
    mem = [n for n in G1 if C[n]["region_member"]]
    comps, seen = [], set()
    for n in mem:
        if n in seen:
            continue
        stack, comp = [n], []
        while stack:
            m = stack.pop()
            if m in seen:
                continue
            seen.add(m); comp.append(m)
            stack += [x for x in nbrs(m) if x in mem and x not in seen]
        comps.append(comp)
    res["regions"] = [dict(members=c, size=len(c), has_robust_point=any(C[m]["robust_point"] for m in c),
                           robust=len(c) >= 3 and any(C[m]["robust_point"] for m in c)) for c in comps]
    # relaxed map (information): sign of ALL mean / S12 mean on the lattice
    res["lattice_map"] = {n: dict(all=C[n]["ALL"].get("mean"), t=C[n]["ALL"].get("t"), n=C[n]["ALL"].get("n"),
                                  E=C[n]["EARLY"].get("mean"), T2=C[n]["T2"].get("mean"), C=C[n]["CHECK"].get("mean"),
                                  S12=C[n]["S12"].get("mean")) for n in G1}
    # ---- H-FAM
    def fam(sfx=""):
        D = pd.concat({n: dayR[n + sfx] for n in G1}, axis=1).fillna(0.0)
        return D.mean(axis=1)
    F = fam(); F12 = fam("#S12")
    def fst(s):
        sp = [idx_sim.qo_sim.split_of(pd.Timestamp(d).date()) for d in s.index]
        o = {"ALL": st(s.values, s.index)}
        for k in SPLITS:
            m = np.array(sp) == k; o[k] = st(s.values[m], s.index[m])
        return o
    hf = fst(F); hf12 = fst(F12)
    res["H_FAM"] = dict(base=hf, S12=hf12, bars={
        "pos_E_T2_C": all((hf[s].get("mean") or -9) > 0 for s in ("EARLY", "T2", "CHECK")),
        "t_ge_2": (hf["ALL"].get("t") or 0) >= 2.0,
        "S12_pos_t165": (hf12["ALL"].get("mean") or -9) > 0 and (hf12["ALL"].get("t") or 0) >= 1.65,
        "conc": (hf["ALL"].get("wo_best") or -9) > 0 and (hf["ALL"].get("best_share") or 9) < 0.5})
    res["H_FAM"]["passed"] = all(res["H_FAM"]["bars"].values())
    # ---- book impact + correlation with Primary base book
    P = pd.read_parquet(base_pq); P["date"] = P.date.astype(str); nolock(P.date.unique())
    pday = P.groupby("date").r.sum()
    def impact(names, label):
        g = B[B.name.isin(names)].sort_values(["date", "sig", "emin"])
        one = g.groupby(["date", "sig"]).head(1)          # one trade per index per day (union)
        yrs = one.date.str[:4]
        nyrs = len(sorted(set(B.date.str[:4])))
        dr = one.groupby("date").r_livel.sum()
        win = pday.index
        x = dr.reindex(win).fillna(0.0)
        on = x != 0
        comb = pday + x
        sh = lambda s: float(s.mean() / s.std(ddof=1) * np.sqrt(252))
        two = one[one.date >= "2023-01-01"]
        return dict(label=label, configs=names, trades=len(one), trades_per_year_all=round(len(one) / (2646 / 252), 1),
                    trades_per_year_2023on=round(len(two) / (len(pday) / 252), 1),
                    trade_days=int(dr.size), mean_r=round(float(one.r_livel.mean()), 3),
                    corr_primary_all_days=round(float(np.corrcoef(pday.values, x.values)[0, 1]), 3),
                    corr_primary_idx_days=round(float(np.corrcoef(pday[on].values, x[on].values)[0, 1]), 3) if on.sum() > 2 else None,
                    primary_mean_on_idx_days=round(float(pday[on].mean()), 3), primary_mean_other_days=round(float(pday[~on].mean()), 3),
                    idx_days_in_primary_window=int(on.sum()), idx_R_in_primary_window=round(float(x.sum()), 2),
                    primary_R_window=round(float(pday.sum()), 2),
                    sharpe_primary=round(sh(pday), 3), sharpe_combined=round(sh(comb), 3),
                    by_year=one.groupby(yrs).r_livel.agg(["size", "mean"]).round(3).reset_index().to_dict("records"))
    res["impact"] = {}
    for rg in res["regions"]:
        if len(rg["members"]) >= 2:
            res["impact"]["region:" + "+".join(rg["members"])] = impact(rg["members"], "region")
    res["impact"]["G1_lattice_union"] = impact(G1, "lattice")
    res["impact"]["IDX3_SPY075_0955"] = impact(["G1|L|SPY|0.75|0955|B0.2|TRAIL"], "IDX3")
    res["impact"]["IDX6_QQQ150_0955"] = impact(["G1|L|QQQ|1.5|0955|B0.2|TRAIL"], "IDX6")
    pos_all = [n for n in G1 if (C[n]["ALL"].get("mean") or -9) > 0 and (C[n]["S12"].get("mean") or -9) > 0]
    if pos_all:
        res["impact"]["G1_positive_ALL_and_S12"] = impact(pos_all, "pos")
    res["primary_days"] = int(len(pday))
    json.dump(res, open(HERE / "results.json", "w"), indent=1, default=str)
    print("REGIONS", json.dumps(res["regions"], indent=0))
    print("HFAM", json.dumps(res["H_FAM"], default=str)[:3000])
    for k, v in res["impact"].items():
        print("IMPACT", k, {kk: vv for kk, vv in v.items() if kk not in ("by_year", "configs")})
    for n in cfgs:
        print("CRIT", n, C[n]["crit"], C[n].get("robust_point", C[n].get("pass_1_5")))


if __name__ == "__main__":
    main(*sys.argv[1:4])
