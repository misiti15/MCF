"""DAYTYPE-1127 scoring (PREREG.md): 24 configs, LIVE-L / LR8 / ETF-TIGHT costs, per-split stats, controls, stress.
Usage: python dt_score.py DAYTAB_DIR OUTDIR (reads daytab.csv.gz from DAYTAB_DIR, breadth_main / breadth_early from OUTDIR)
Locked block asserted absent. Educational only - not financial advice."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from mcf.research.gates import tod_cost_mult  # noqa: E402

CELLS = json.load(open(HERE.parent / "primshorts_1126/cells_live.json"))
OOS = ["EARLY", "T2", "CHECK"]
SPL = ["EARLY", "T2", "FIT", "CHECK"]
BAR = 2.86
rng = np.random.default_rng(1127)


def cost(entry, risk, kind, xpx, side, tod, extra_bp=0.0):
    a = np.where(kind == 1, CELLS["100+|stop"][0], CELLS["100+|market"][0])
    b = np.where(kind == 1, CELLS["100+|stop"][1], CELLS["100+|market"][1])
    c_l = a / (risk / entry * 1e4) + b
    ec = (0.01 + entry * 1e-4) * tod_cost_mult(tod)
    xc = 0.01 + xpx * 1e-4 + np.where(kind == 1, 0.02, 0.0)
    c_8 = (ec + xc + np.where(side < 0, 1.2e-4 * entry, 0.0)) / risk
    c_t = (1e-4 * entry + 1e-4 * xpx + np.where(kind == 1, 0.01, 0.0)) / risk
    ex = extra_bp * 1e-4 * (entry + xpx) / risk
    return c_l + ex, c_8 + ex, c_t + ex


def trades(dt, side, inst, lag=0, extra_bp=0.0):
    """dt rows with a side (+1/-1) -> per-trade frame with gross and net R."""
    L = side > 0
    g = np.where(L, dt[f"{inst}_{lag}_L_g"], dt[f"{inst}_{lag}_S_g"])
    k = np.where(L, dt[f"{inst}_{lag}_L_k"], dt[f"{inst}_{lag}_S_k"]).astype(int)
    x = np.where(L, dt[f"{inst}_{lag}_L_x"], dt[f"{inst}_{lag}_S_x"])
    e = dt[f"{inst}_{lag}_e"].to_numpy(float); rk = dt[f"{inst}_risk"].to_numpy(float)
    cl, c8, ct = cost(e, rk, k, x, side, dt["T"].to_numpy() + lag, extra_bp)
    return pd.DataFrame({"date": dt.date.to_numpy(), "split": dt.split.to_numpy(), "side": side, "gross": g, "kind": k,
                         "r_livel": g - cl, "r_lr8": g - c8, "r_tight": g - ct,
                         "move_bp": side * (x - e) / e * 1e4})


def st(x, d=None):
    x = np.asarray(x, float); n = len(x)
    if n == 0:
        return dict(n=0)
    tot = x.sum(); best = x.max() if d is None else pd.Series(x).groupby(np.asarray(d)).sum().max()
    sd = x.std(ddof=1) if n > 1 else np.nan
    return dict(n=n, mean=round(float(x.mean()), 4), t=round(float(x.mean() / (sd / np.sqrt(n))), 2) if n > 1 and sd > 0 else None,
                win=round(float((x > 0).mean()), 3), tot=round(float(tot), 2),
                best_share=round(float(best / tot), 3) if tot > 0 else None,
                wo_best=round(float((tot - best) / (n - 1)), 4) if n > 1 else None)


def sides(dt, cfg):
    if cfg["kind"] == "TC":
        return dt.tc.to_numpy()
    b = dt[cfg["meas"]].to_numpy(float)
    s = np.where(b >= cfg["hi"], 1, np.where(b <= cfg["lo"], -1, 0))
    s = np.where(np.isnan(b), 0, s)
    if cfg["tc"]:
        s = np.where(dt.tc.to_numpy() == s, s, 0)
    return s


def evaluate(D, cfg, controls=True):
    dt = D[D["T"] == cfg["T"]].reset_index(drop=True)
    s = sides(dt, cfg); m = s != 0
    tr = trades(dt[m], s[m], cfg["inst"])
    out = dict(cfg)
    for sp in SPL:
        q = tr[tr.split == sp]
        out[sp] = st(q.r_livel); out[sp]["lr8"] = round(float(q.r_lr8.mean()), 4) if len(q) else None
        out[sp]["tight"] = round(float(q.r_tight.mean()), 4) if len(q) else None
        out[sp]["gross"] = round(float(q.gross.mean()), 4) if len(q) else None
        out[sp]["move_bp"] = round(float(q.move_bp.mean()), 2) if len(q) else None
        out[sp]["n_long"] = int((q.side > 0).sum())
    o = tr[tr.split.isin(OOS)]
    out["OOS"] = st(o.r_livel); out["OOS"]["lr8"] = st(o.r_lr8); out["OOS"]["tight_mean"] = round(float(o.r_tight.mean()), 4) if len(o) else None
    out["OOS"]["gross_mean"] = round(float(o.gross.mean()), 4) if len(o) else None
    out["OOS"]["long"] = st(o[o.side > 0].r_livel); out["OOS"]["short"] = st(o[o.side < 0].r_livel)
    yr = o.assign(y=o.date.str[:4]).groupby("y").r_livel.agg(["size", "mean"]).round(3)
    out["years"] = {k: [int(v["size"]), float(v["mean"])] for k, v in yr.iterrows()}
    # stress: +1 min entry and +2 bp per side
    trs = trades(dt[m], s[m], cfg["inst"], lag=1, extra_bp=2.0)
    os_ = trs[trs.split.isin(OOS)]
    out["stress"] = st(os_.r_livel)
    if controls and len(o) > 5:
        dto = dt[dt.split.isin(OOS)].reset_index(drop=True)
        # pre-compute both sides' net R for every eligible OOS day
        allL = trades(dto, np.ones(len(dto), int), cfg["inst"]).r_livel.to_numpy()
        allS = trades(dto, -np.ones(len(dto), int), cfg["inst"]).r_livel.to_numpy()
        idx_by = {sp: np.flatnonzero(dto.split.to_numpy() == sp) for sp in OOS}
        so = s[m][np.isin(dt[m].split.to_numpy(), OOS)]
        sp_of = dt[m].split.to_numpy()[np.isin(dt[m].split.to_numpy(), OOS)]
        A = []
        for _ in range(500):
            vals = []
            for sp in OOS:
                ss = so[sp_of == sp]
                if not len(ss):
                    continue
                pick = rng.choice(idx_by[sp], size=len(ss), replace=False)
                ssh = rng.permutation(ss)
                vals.append(np.where(ssh > 0, allL[pick], allS[pick]))
            A.append(np.concatenate(vals).mean())
        A = np.array(A)
        # random direction on the config's own days
        sel = np.flatnonzero(m & dt.split.isin(OOS).to_numpy())
        pos = {dd: i for i, dd in enumerate(dto.date)}
        ii = np.array([pos[dd] for dd in dt.date.to_numpy()[sel]])
        Bc = np.array([np.where(rng.random(len(ii)) < 0.5, allL[ii], allS[ii]).mean() for _ in range(500)])
        out["ctrl_day"] = dict(mean=round(float(A.mean()), 4), p95=round(float(np.quantile(A, 0.95)), 4),
                               pct=round(float((A < out["OOS"]["mean"]).mean() * 100), 1))
        out["ctrl_dir"] = dict(mean=round(float(Bc.mean()), 4), p95=round(float(np.quantile(Bc, 0.95)), 4),
                               pct=round(float((Bc < out["OOS"]["mean"]).mean() * 100), 1))
    out["_tr"] = tr
    return out


def bars(r):
    O = r["OOS"]; f = {}
    f["pos_splits"] = all((r[sp].get("mean") or -1) > 0 for sp in OOS)
    f["n_ok"] = r["T2"]["n"] >= 30 and r["CHECK"]["n"] >= 30 and r["EARLY"]["n"] >= 50
    f["t_bar"] = (O.get("t") or -9) >= BAR
    f["conc"] = (O.get("best_share") is not None and O["best_share"] < 0.25 and (O.get("wo_best") or -1) > 0
                 and (r["CHECK"].get("wo_best") or -1) > 0)
    f["ctrl_day"] = "ctrl_day" in r and O["mean"] > r["ctrl_day"]["p95"]
    f["ctrl_dir"] = "ctrl_dir" in r and O["mean"] > r["ctrl_dir"]["p95"]
    f["stress"] = (r["stress"].get("mean") or -1) > 0 and (r["stress"].get("t") or -9) >= 2.0
    return f


def main(tabdir, out):
    D = pd.read_csv(tabdir / "daytab.csv.gz"); D["date"] = D.date.astype(str)
    d = pd.to_datetime(D.date).dt.date
    assert not ((d >= pd.Timestamp("2024-11-01").date()) & (d <= pd.Timestamp("2025-02-28").date())).any()
    D = D[D.split != "LATE"]
    bm = pd.read_csv(out / "breadth_main.csv.gz"); bm["date"] = bm.date.astype(str)
    be = pd.read_csv(out / "breadth_early.csv.gz"); be["date"] = be.date.astype(str)
    br = pd.concat([be[be.date < "2023-01-01"], bm[bm.date >= "2023-01-01"]]).rename(columns={"tod": "T"})
    br = br[br.n >= 50] if True else br
    D = D.merge(br[["date", "T", "breadth_vwap", "breadth_open", "n"]], on=["date", "T"], how="left")
    D["tc"] = np.where((D.spy_vw_side > 0) & (D.spy_slope60 > 0), 1, np.where((D.spy_vw_side < 0) & (D.spy_slope60 < 0), -1, 0))
    cov = D.groupby("split").breadth_open.apply(lambda x: round(float(x.notna().mean()), 3)).to_dict()
    cfgs = []
    for meas in ("breadth_open", "breadth_vwap"):
        for T in (1130, 1300):
            for tc in (False, True):
                for inst in ("SPY", "QQQ"):
                    cfgs.append(dict(kind="BR", meas=meas, T=T, tc=tc, inst=inst, lo=0.30, hi=0.70))
    for T in (1130, 1300):
        for inst in ("SPY", "QQQ"):
            cfgs.append(dict(kind="TC", meas="-", T=T, tc=True, inst=inst, lo=None, hi=None))
    res = [evaluate(D, c) for c in cfgs]
    fitr = sorted([r for r in res if r["kind"] == "BR" and r["FIT"]["n"] >= 15], key=lambda r: -r["FIT"]["mean"])[:2]
    for r0 in fitr:
        for lo, hi in ((0.25, 0.75), (0.35, 0.65)):
            c = {k: r0[k] for k in ("kind", "meas", "T", "tc", "inst")}; c.update(lo=lo, hi=hi, neighbour_of=True)
            res.append(evaluate(D, c))
    # bar 7: breadth+TC vs TC-only on the OOS days (selected TC days vs all TC days)
    tco = {(r["T"], r["inst"]): r for r in res if r["kind"] == "TC"}
    for r in res:
        r["name"] = (f"TC-only {r['inst']} {r['T']}" if r["kind"] == "TC" else
                     f"{r['meas'].replace('breadth_', 'B')}{int(r['lo']*100)}/{int(r['hi']*100)} {r['T']} {'TC' if r['tc'] else 'noTC'} {r['inst']}")
        r["bars"] = bars(r); r["pass"] = all(r["bars"].values())
        if r["kind"] == "BR" and r["tc"]:
            a = r["_tr"]; b = tco[(r["T"], r["inst"])]["_tr"]
            a = a[a.split.isin(OOS)]; b = b[b.split.isin(OOS)]
            q = D[(D["T"] == r["T"]) & D[r["meas"]].notna()]
            b = b[b.date.isin(q.date)]                     # TC days where this breadth measure exists
            rest = b[~b.date.isin(a.date)]
            se = np.sqrt(a.r_livel.var() / max(len(a), 1) + rest.r_livel.var() / max(len(rest), 1))
            r["vs_tc"] = dict(sel_mean=round(float(a.r_livel.mean()), 4), tc_all_mean=round(float(b.r_livel.mean()), 4),
                              rest_mean=round(float(rest.r_livel.mean()), 4),
                              t_sel_vs_rest=round(float((a.r_livel.mean() - rest.r_livel.mean()) / se), 2) if se > 0 else None)
    # descriptive: afternoon SPY move by breadth bucket (all OOS days, T=1130, breadth_open)
    desc = {}
    for T in (1130, 1300):
        q = D[(D["T"] == T) & D.split.isin(OOS)].copy()
        q["mv"] = (q["SPY_0_L_x"] / q["SPY_0_e"] - 1) * 1e4
        q["bk"] = pd.cut(q.breadth_open, [0, .2, .3, .4, .6, .7, .8, 1.0001], right=False)
        desc[str(T)] = {str(k): [int(len(g)), round(float(g.mv.mean()), 1), round(float((g.mv > 0).mean()), 3)]
                        for k, g in q.groupby("bk", observed=True)}
    rows = []
    for r in res:
        row = dict(name=r["name"], kind=r["kind"], neighbour=bool(r.get("neighbour_of", False)), passed=r["pass"])
        for sp in SPL + ["OOS"]:
            row[f"{sp}_n"] = r[sp].get("n"); row[f"{sp}_mean"] = r[sp].get("mean"); row[f"{sp}_t"] = r[sp].get("t")
        row["OOS_lr8"] = r["OOS"]["lr8"].get("mean"); row["OOS_lr8_t"] = r["OOS"]["lr8"].get("t")
        row["OOS_tight"] = r["OOS"]["tight_mean"]; row["OOS_gross"] = r["OOS"]["gross_mean"]
        row["OOS_best_share"] = r["OOS"].get("best_share"); row["OOS_wo_best"] = r["OOS"].get("wo_best")
        row["CHECK_wo_best"] = r["CHECK"].get("wo_best")
        row["ctrl_day_p95"] = r.get("ctrl_day", {}).get("p95"); row["ctrl_day_pct"] = r.get("ctrl_day", {}).get("pct")
        row["ctrl_dir_p95"] = r.get("ctrl_dir", {}).get("p95"); row["ctrl_dir_pct"] = r.get("ctrl_dir", {}).get("pct")
        row["stress_mean"] = r["stress"].get("mean"); row["stress_t"] = r["stress"].get("t")
        row["bars_failed"] = ",".join(k for k, v in r["bars"].items() if not v)
        rows.append(row)
    pd.DataFrame(rows).to_csv(out / "results.csv", index=False)
    for r in res:
        r.pop("_tr")
    json.dump(dict(coverage=cov, desc_spy_move_by_breadth_open=desc, configs=res), open(out / "results.json", "w"), indent=1, default=str)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows)[["name", "EARLY_n", "EARLY_mean", "T2_n", "T2_mean", "CHECK_n", "CHECK_mean", "FIT_mean", "OOS_n", "OOS_mean", "OOS_t",
                              "OOS_lr8", "OOS_gross", "OOS_best_share", "ctrl_day_pct", "ctrl_dir_pct", "stress_mean", "bars_failed"]].to_string())
    print("coverage", cov); print(json.dumps(desc, indent=0))
    for r in res:
        if "vs_tc" in r:
            print(r["name"], r["vs_tc"])


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
