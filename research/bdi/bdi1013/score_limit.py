"""Part A step 2 (PLAN.md): score 6 signals x 3 exits x 49 entries (+ 75 controls) on the limit945.npz arrays.
Writes limit_results.csv, limit_finalists.csv, limit_summary.json (repo) from <data_dir> (scratch).
    python score_limit.py <data_dir>
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y")]
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

DD = Path(sys.argv[1])
IX = ROOT / "research" / "bdi" / "indexlink"
N_STUDY_A = 957
N_LINEAGE = 102021 + N_STUDY_A
TREQ = gates.t_required(N_LINEAGE)


def dstat(r, s, nsess):
    """mean, day-clustered t, number of trades."""
    ok = np.isfinite(r)
    r, s = r[ok], s[ok]
    n = len(r)
    if n < 2:
        return np.nan, np.nan, n
    mu = r.mean()
    gs = np.bincount(s, weights=r, minlength=nsess)
    gn = np.bincount(s, minlength=nsess)
    se = np.sqrt(((gs - gn * mu) ** 2).sum()) / n
    return mu, (mu / se if se > 0 else np.nan), n


def main():
    z = np.load(DD / "limit945.npz")
    days = pd.read_parquet(DD / "days.parquet")
    ENT, EXT = [str(x) for x in z["entries"]], [str(x) for x in z["exits"]]
    nets, fills = z["nets"], z["fills"]
    have, o0, c945, pc, capd = z["have"], z["o0"], z["c945"], z["pc"], z["capd"]
    gap = days["gap"].to_numpy(float)
    sess = days["sess"].to_numpy(int)
    reg = lib.regimes()
    dates = sorted(reg.index)
    nsess = len(dates)
    code = np.array([reg.loc[d, "regime"] for d in dates])
    valid_s = np.array([str(d) > "2025-12-31" for d in dates])
    up_s, dn_s = code == "up", code == "down"
    # QQQ mid at the 09:45 close
    meta = json.load(open(IX / "data" / "meta.json"))
    assert meta["dates"] == [str(d) for d in dates]
    e = np.load(IX / "data" / "etf1m.npz")
    qi = [str(x) for x in e["syms"]].index("QQQ")
    qo, ql, qc = e["open"][qi][:, 0], np.nanmin(e["low"][qi][:, :15], 1), e["close"][qi][:, 14]
    qqqmid = (qc > (qo + ql) / 2)[sess]
    with np.errstate(invalid="ignore"):
        do = (1 - c945 / o0) * 100
        dp = (1 - c945 / pc) * 100
    SIG = {"S1-O-p0.75-none": do >= 0.75, "S2-O-p0.75-capd": (do >= 0.75) & capd, "S3-O-p0.75-qqqmid": (do >= 0.75) & qqqmid,
           "S4-B-p0.75-capd": (do >= 0.75) & (dp >= 0.75) & capd, "S5-B-p1.0-capd": (do >= 1.0) & (dp >= 1.0) & capd,
           "S6-PC-p0.75-flat-qqqmid": (dp >= 0.75) & (np.abs(gap) < 0.5) & qqqmid}
    SIG = {k: v & have for k, v in SIG.items()}
    elig = have & np.isfinite(nets[0, 0])
    # same-session controls: market (all eligible, MKT) and random-limit (all eligible, same entry rule)
    CT = np.full((len(ENT), len(EXT), nsess), np.nan)
    for i in range(len(ENT)):
        for j in range(len(EXT)):
            r = nets[i, j]
            ok = elig & np.isfinite(r)
            sm = np.bincount(sess[ok], weights=r[ok], minlength=nsess)
            cn = np.bincount(sess[ok], minlength=nsess)
            with np.errstate(invalid="ignore"):
                CT[i, j] = sm / cn
    rows = []
    # controls (75 counted): MKT random (3) + random-limit LIM (24 x 3) rows; CHASE controls reported, not counted
    for i, en in enumerate(ENT):
        for j, ex in enumerate(EXT):
            r = np.where(elig, nets[i, j], np.nan).astype(float)
            mu, t, n = dstat(r, sess, nsess)
            rows.append({"cfg": f"CTRL-{en}-{ex}", "signal": "CTRL-all", "entry": en, "exit": ex, "open_n": n, "open_exp": mu,
                         "open_t": t, "counted": en == "MKT" or en.startswith("LIM")})
    for sn, sm in SIG.items():
        idx = np.flatnonzero(sm)
        s = sess[idx]
        vm, um, dm = valid_s[s], up_s[s], dn_s[s]
        for i, en in enumerate(ENT):
            for j, ex in enumerate(EXT):
                r = nets[i, j, idx].astype(float)
                rm = nets[0, j, idx].astype(float)
                row = {"cfg": f"{sn}|{en}|{ex}", "signal": sn, "entry": en, "exit": ex, "n_signals": len(idx), "counted": True}
                for nm, m in (("open", np.ones(len(idx), bool)), ("train", ~vm), ("valid", vm)):
                    mu, t, n = dstat(np.where(m, r, np.nan), s, nsess)
                    row.update({f"{nm}_n": n, f"{nm}_exp": mu, f"{nm}_t": t})
                row["fill_rate"] = row["open_n"] / max(1, len(idx))
                for nm, m in (("up", um), ("down", dm)):
                    row[f"{nm}_exp"] = np.nanmean(np.where(m, r, np.nan)) if np.isfinite(r[m]).sum() >= 30 else np.nan
                xm = r - CT[0, j, s]
                mu, t, _ = dstat(xm, s, nsess)
                row.update({"excess_mkt": mu, "excess_mkt_t": t})
                xl = r - CT[i, j, s]
                mu, t, _ = dstat(xl, s, nsess)
                row.update({"excess_ctrl": mu, "excess_ctrl_t": t})
                for nm, m in (("up", um), ("down", dm)):
                    row[f"{nm}_excess_mkt"] = np.nanmean(np.where(m, xm, np.nan)) if np.isfinite(xm[m]).sum() >= 30 else np.nan
                fin = np.isfinite(r)
                if fin.any():
                    g = pd.Series(r[fin]).groupby(s[fin]).agg(["sum", "size"])
                    b = g["sum"].idxmax()
                    row["ex_best"] = (r[fin].sum() - g.loc[b, "sum"]) / max(1, fin.sum() - g.loc[b, "size"])
                    row["busiest"] = g["size"].max() / fin.sum()
                if en.startswith("LIM"):
                    f = fin
                    row["mkt_R_filled"] = np.nanmean(rm[f]) if f.any() else np.nan
                    row["mkt_R_unfilled"] = np.nanmean(rm[~f]) if (~f).any() else np.nan
                    row["n_unfilled"] = int((~f & np.isfinite(rm)).sum())
                    row["improvement_on_filled"] = np.nanmean(r[f] - rm[f]) if f.any() else np.nan
                    mu, t, _ = dstat(np.where(~f, rm, np.nan), s, nsess)
                    row["unfilled_mkt_t"] = t
                rows.append(row)
    R = pd.DataFrame(rows)
    counted = int(R.counted.sum())
    print("configurations counted", counted, flush=True)
    assert counted == N_STUDY_A, counted
    # plateau for LIM / CHASE: neighbour offsets (same validity) and neighbour validities (same offset)
    chain = {"b0": ["b5"], "b5": ["b0", "b10"], "b10": ["b5", "b20"], "b20": ["b10"], "a05": ["a10"], "a10": ["a05"]}
    vch = {1: [3], 3: [1, 5], 5: [3, 10], 10: [5]}
    key = R.set_index("cfg")["open_exp"].to_dict()
    pl = []
    for r in R.itertuples():
        if r.signal == "CTRL-all" or r.entry == "MKT":
            pl.append(np.nan); continue
        p, o, v = r.entry.split("-")
        v = int(v[1:])
        nb = [f"{p}-{x}-v{v}" for x in chain[o]] + [f"{p}-{o}-v{x}" for x in vch[v]]
        pl.append(min(key.get(f"{r.signal}|{x}|{r.exit}", np.nan) for x in nb))
    R["plateau_min"] = pl
    R.to_csv(HERE / "limit_results.csv", index=False, float_format="%.5g")
    # finalists: per signal x exit, the best LIM/CHASE by train exp (train n >= 100) + its MKT baseline
    S = R[R.signal != "CTRL-all"]
    fin = []
    for (sn, ex), g in S.groupby(["signal", "exit"]):
        c = g[(g.entry != "MKT") & (g.train_n >= 100)].sort_values("train_exp", ascending=False)
        fin.append(g[g.entry == "MKT"].iloc[0])
        if len(c):
            fin.append(c.iloc[0])
    Fd = pd.DataFrame(fin).reset_index(drop=True)
    # walk-forward and gates for finalists
    wfs = []
    regs = []
    for r in Fd.itertuples():
        sm = SIG[r.signal]
        idx = np.flatnonzero(sm)
        i, j = ENT.index(r.entry), EXT.index(r.exit)
        rr = nets[i, j, idx].astype(float)
        ok = np.isfinite(rr)
        tr = pd.DataFrame({"date": pd.to_datetime(np.array(dates, dtype="datetime64[D]")[sess[idx][ok]]), "r": rr[ok]})
        wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
        wfs.append(wf.get("share_positive"))
    Fd["wf"] = wfs
    Fd["research_pass"] = ((Fd.open_n >= 150) & (Fd.open_exp > 0) & (Fd.open_t >= TREQ) & (Fd.up_exp > 0) & (Fd.down_exp > 0)
                           & (Fd.wf >= 0.6) & (Fd.ex_best > 0) & (Fd.busiest <= 0.10))
    Fd["testing_pass"] = ((Fd.open_exp > 0) & (Fd.open_t >= 2) & (Fd.train_exp > 0) & (Fd.valid_exp > 0) & (Fd.up_exp > 0)
                          & (Fd.down_exp > 0) & (Fd.excess_mkt > 0) & (Fd.excess_mkt_t >= 2) & (Fd.wf >= 0.6)
                          & (Fd.ex_best > 0) & (Fd.busiest <= 0.10) & (Fd.plateau_min > 0))
    Fd.to_csv(HERE / "limit_finalists.csv", index=False, float_format="%.4g")
    # summary
    L = S[S.entry.str.startswith("LIM")]
    C = S[S.entry.str.startswith("CHASE")]
    M = S[S.entry == "MKT"]
    summ = {"n_configs_counted": counted, "lineage_N": N_LINEAGE, "t_required": TREQ, "study_t_required": gates.t_required(N_STUDY_A),
            "n_open_exp_pos": {"MKT": int((M.open_exp > 0).sum()), "LIM": int((L.open_exp > 0).sum()), "CHASE": int((C.open_exp > 0).sum())},
            "n_total": {"MKT": len(M), "LIM": len(L), "CHASE": len(C)},
            "max_open_t": {"MKT": float(M.open_t.max()), "LIM": float(L[L.open_n >= 150].open_t.max()), "CHASE": float(C.open_t.max())},
            "research_pass": Fd[Fd.research_pass].cfg.tolist(), "testing_pass": Fd[Fd.testing_pass].cfg.tolist(),
            "controls": R[R.signal == "CTRL-all"][["cfg", "open_n", "open_exp", "open_t"]].round(4).values.tolist()}
    # adverse selection table: LIM by offset x validity, pooled medians over signals/exits
    L2 = L.copy()
    L2["off"] = L2.entry.str.split("-").str[1]
    L2["val"] = L2.entry.str.split("-").str[2]
    summ["adverse"] = L2.groupby(["off", "val"])[["fill_rate", "open_exp", "mkt_R_filled", "mkt_R_unfilled", "improvement_on_filled", "excess_mkt"]].median().round(4).reset_index().values.tolist()
    json.dump(summ, open(HERE / "limit_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 300)
    cols = ["cfg", "n_signals", "fill_rate", "train_n", "train_exp", "train_t", "valid_n", "valid_exp", "valid_t", "open_n", "open_exp", "open_t",
            "excess_mkt", "excess_mkt_t", "excess_ctrl", "up_exp", "down_exp", "mkt_R_filled", "mkt_R_unfilled", "improvement_on_filled", "wf", "plateau_min", "testing_pass"]
    print(Fd[cols].round(3).to_string(index=False))
    print(json.dumps({k: v for k, v in summ.items() if k != "adverse"}, indent=0, default=float)[:3000])
    print(pd.DataFrame(summ["adverse"], columns=["off", "val", "fill", "exp", "mktR_filled", "mktR_unfilled", "improve", "excess"]).to_string(index=False))


if __name__ == "__main__":
    main()
