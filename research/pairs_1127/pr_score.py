"""PAIRS-1127 scorer (PREREG.md): splits, LIVE-L / LR8 net, day-clustered t, best-day share, stress, market beta,
size-matched random control, per-ETF effect. Usage: python pr_score.py DATADIR SIMDIR OUTDIR.
Educational only - not financial advice."""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

LOCK_A, LOCK_B = date(2024, 11, 1), date(2025, 2, 28)


def split(d):
    if LOCK_A <= d <= LOCK_B:
        raise AssertionError("locked block")
    if date(2023, 1, 1) <= d <= date(2024, 9, 30):
        return "T2"
    if date(2024, 10, 1) <= d <= date(2024, 10, 31) or date(2025, 3, 1) <= d <= date(2025, 9, 30):
        return "FIT"
    if date(2025, 10, 1) <= d <= date(2026, 11, 4):
        return "CHECK"
    return "PRE"


def dayt(x, days):
    g = pd.Series(np.asarray(x)).groupby(np.asarray(days)).mean()
    if len(g) < 3:
        return np.nan, len(g)
    return g.mean() / (g.std(ddof=1) / np.sqrt(len(g))), len(g)


def stats(t, spy):
    if not len(t):
        return {"n": 0}
    net = t.netL.to_numpy()
    tt, nd = dayt(net, t.date)
    ds = t.groupby("date").netL.sum()
    tot = ds.sum(); best = ds.idxmax()
    wo = t[t.date != best].netL.mean()
    ts, _ = dayt(t.netS, t.date)
    # market beta: daily book P/L (sum of trades, bp of one stock notional each) vs SPY open->close (%)
    x = spy.reindex(ds.index); ok = x.notna()
    slope = np.polyfit(x[ok], ds[ok], 1)[0] if ok.sum() > 10 else np.nan
    rho = np.corrcoef(x[ok], ds[ok])[0, 1] if ok.sum() > 10 else np.nan
    # per-trade mean vs SPY up/down days
    up = t.date.map(spy) > 0
    return {"n": int(len(t)), "days": int(nd), "gross": float(t.g1.mean()), "costL": float(t.costL.mean()),
            "netL": float(net.mean()), "net8": float(t.net8.mean()), "R_L": float((t.netL / t.W).mean()),
            "t_L": float(tt), "t_8": float(dayt(t.net8, t.date)[0]), "best_share": float(ds.max() / tot) if tot > 0 else None,
            "wo_best": float(wo), "stress": float(t.netS.mean()), "t_stress": float(ts),
            "beta_bp_per_1pct": float(slope), "rho_spy": float(rho),
            "spy_up": float(t[up].netL.mean()), "spy_dn": float(t[~up].netL.mean()),
            "kinds": t.kind.value_counts(normalize=True).round(3).to_dict(), "W": float(t.W.median())}


def control(t, paths_by_day, hold_cap, rng, ndraw=200):
    """Same days, same count, random eligible stock-day path, random fill bar in [6,66], random side, same hold length,
    matched trade's LIVE-L cost. Returns array of draw means."""
    hold = (t.b - t.a).to_numpy(); cost = t.costL.to_numpy(); days = t.d.to_numpy()
    means = np.empty(ndraw)
    for k in range(ndraw):
        g = np.empty(len(t))
        for dd in np.unique(days):
            idx = np.nonzero(days == dd)[0]
            P = paths_by_day[dd]
            pi = rng.integers(0, len(P), len(idx))
            a = rng.integers(6, 67, len(idx))
            b = np.minimum(a + hold[idx], 77)
            sd = rng.choice([-1.0, 1.0], len(idx))
            g[idx] = sd * (P[pi, b] - P[pi, a]) * 1e4
        means[k] = (g - cost).mean()
    return means


def main(datadir, simdir, outdir):
    sim = Path(simdir); out = Path(outdir)
    cfg = json.load(open(sim / "cfg.json"))
    t = pd.read_pickle(sim / "trades.pkl")
    t["split"] = t.date.map(split)
    t = t[t.split != "PRE"]
    t["netL"] = t.g1 - t.costL; t["net8"] = t.g1 - t.cost8; t["netS"] = t.g2 - t.costL - t.stressadd
    z = np.load(Path(datadir) / "SPY.npz"); cal = [date.fromisoformat(x) for x in np.load(Path(datadir) / "_cal.npy")]
    spy = pd.Series((z["C"][:, 77] / z["O1"][:, 0] - 1) * 100, index=cal)
    rows = []
    for c in cfg:
        tc = t[t.cfg == c["id"]]
        for sp in ("FIT", "CHECK", "T2"):
            r = stats(tc[tc.split == sp], spy); r.update(cfg=c["id"], name=c["name"], split=sp); rows.append(r)
        oo = tc[tc.split.isin(["CHECK", "T2"])]
        r = stats(oo, spy); r.update(cfg=c["id"], name=c["name"], split="CHECK+T2"); rows.append(r)
    R = pd.DataFrame(rows)
    fit = R[(R.split == "FIT") & (R.n >= 100)].sort_values("t_L", ascending=False)
    fin = fit.iloc[0].cfg
    print("primary finalist", fin, fit.iloc[0]["name"])
    # gross by k / baseline (all configs pooled per k, CHECK+T2)
    cmap = {c["id"]: c for c in cfg}
    t["k"] = t.cfg.map(lambda x: cmap[x]["k"]); t["base"] = t.cfg.map(lambda x: cmap[x]["base"])
    oo = t[t.split.isin(["CHECK", "T2"])]
    byk = oo.groupby(["base", "k"]).agg(n=("g1", "size"), gross=("g1", "mean"), costL=("costL", "mean"),
                                        stockL=("stockL", "mean"), etfL=("etfL", "mean"), cost8=("cost8", "mean"),
                                        netL=("netL", "mean"), W=("W", "median")).round(2)
    # controls for the finalist and any config positive after LIVE-L on CHECK and T2
    P = np.load(sim / "paths.npz")
    pos = R.pivot(index="cfg", columns="split", values="netL")
    ctrl_cfgs = sorted(set([fin]) | set(pos[(pos.CHECK > 0) & (pos.T2 > 0)].index))
    rng = np.random.default_rng(1127)
    ctrl = {}
    for cid in ctrl_cfgs:
        top = cmap[cid]["top"]
        m = P["rank"] <= top
        pb = {}
        dd_all = P["d"][m]; PP = P["P"][m]
        order = np.argsort(dd_all, kind="stable"); dd_s = dd_all[order]; PP = PP[order]
        u, st = np.unique(dd_s, return_index=True); en = np.r_[st[1:], len(dd_s)]
        for a_, s_, e_ in zip(u, st, en):
            pb[a_] = PP[s_:e_]
        ctrl[cid] = {}
        for sp in ("CHECK", "T2"):
            tc = t[(t.cfg == cid) & (t.split == sp)]
            draws = control(tc, pb, 77, rng, 200)
            real = tc.netL.mean()
            ctrl[cid][sp] = {"real": float(real), "ctrl_mean": float(draws.mean()), "pct": float((draws < real).mean() * 100)}
        print("control", cid, ctrl[cid], flush=True)
    # per-ETF effect for the finalist (CHECK+T2)
    tf = oo[oo.cfg == fin]
    by_etf = tf.groupby("etf").agg(n=("netL", "size"), gross=("g1", "mean"), netL=("netL", "mean")).round(2)
    res = {"configs": len(cfg), "finalist": fin, "results": R.to_dict("records"), "by_k": byk.reset_index().to_dict("records"),
           "control": ctrl, "by_etf_finalist": by_etf.reset_index().to_dict("records")}
    json.dump(res, open(out / "results.json", "w"), indent=1, default=str)
    cols = ["cfg", "name", "split", "n", "days", "gross", "costL", "netL", "net8", "R_L", "t_L", "t_8", "best_share",
            "wo_best", "stress", "t_stress", "beta_bp_per_1pct", "rho_spy", "spy_up", "spy_dn", "W"]
    R[cols].round(3).to_csv(out / "results.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(R[R.split != "FIT"][cols].round(2).to_string())
    print(R[R.split == "FIT"][cols].round(2).to_string())
    print(byk.to_string()); print(by_etf.to_string())


if __name__ == "__main__":
    main(*sys.argv[1:4])
