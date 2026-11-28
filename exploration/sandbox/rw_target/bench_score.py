"""Score RW-TGT125 on the bench (trades from bench_rwtgt.py). Pre-registered in PREREG.md.
Arms: p/v (11-20 rounding) under LIVE-L (verdict); p_raw/v_raw under LIVE-L (parity with shorts_autopsy rw_t125.py);
p/v under the bench10 LR8 basis (sensitivity). Candidate level + Primary book (cap 30, -2R latch on realized R).
Usage (cwd repo): python bench_score.py WORK. Locked block never read. Educational only - not financial advice."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path.cwd())); sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
sys.path.insert(0, str(Path.cwd() / "research/primshorts_1126"))
import bench10 as B  # noqa: E402
import calib_live as CL  # noqa: E402
W = Path(sys.argv[1])
cells = json.load(open("research/primshorts_1126/cells_live.json"))
etb = pd.read_parquet(W / "etb_rate.parquet").rate
rng = np.random.default_rng(20261128)
KD = {2: "target", 1: "stop", 0: "market"}


def arm_r(t, arm, basis):
    z = t.rename(columns={f"px_{arm}": "px", f"kind_{arm}": "kind", f"xt_{arm}": "xt"})[
        ["setup", "symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px", "kind", "xt", "per"]]
    z = B.add_r(z)
    if basis == "liveL":
        kd = np.vectorize(KD.get)(z.kind.astype(int).to_numpy())
        z["r"] = z.r_gross - CL.predict_R(cells, z.entry.to_numpy(), z.risk.to_numpy(), kd)
    return z


def load(test):
    t = pd.read_parquet(W / f"trades_{test}.parquet")
    t["date"] = t.date.astype(str)
    B.no_locked(t.date.unique())
    t = t[(t.entry >= 5) & t.symbol.map(etb).fillna(0).ge(0.9)].copy()
    if test == "t1":
        t["per"] = B.half(t.date); t["per"] = t.per.map({"fit": "FIT", "check": "CHECK", "none": "none"})
    else:
        t["per"] = "T2"
    for a in ("p_raw", "v_raw", "p", "v"):
        t = t[t[f"kind_{a}"].notna() & (t[f"kind_{a}"] >= 0)]
    return t.reset_index(drop=True)


def tstat(d, date):
    e = (d - d.mean()).groupby(date).sum(); se = np.sqrt((e ** 2).sum()) / len(d)
    return d.mean() / se if se > 0 else np.nan


def flip(dd):
    s = rng.choice([-1, 1], size=(10000, len(dd))) @ dd
    return float((np.abs(s) >= abs(dd.sum())).mean())


def wob(r, date):
    day = r.groupby(date).sum(); b = day.idxmax()
    return float(r[date != b].mean()), (float(day.max() / day.sum()) if day.sum() > 0 else np.nan)


def pair(t, a0, a1, basis):
    P, V = arm_r(t, a0, basis), arm_r(t, a1, basis)
    m = P[["setup", "symbol", "date", "tod", "per", "r", "kind", "xm", "em", "stop_cost_r", "side", "entry"]].copy()
    m["rv"] = V.r.to_numpy(); m["kv"] = V.kind.to_numpy(); m["xmv"] = V.xm.to_numpy(); m["d"] = m.rv - m.r
    return m


def row(z, label):
    if not len(z):
        return None
    dd = z.groupby("date").d.sum(); wk = z.groupby(pd.to_datetime(z.date).dt.to_period("W")).d.sum()
    pw, ps = wob(z.r, z.date); vw, vs = wob(z.rv, z.date)
    h = sorted(z.date.unique()); mid = h[len(h) // 2]
    return dict(cut=label, n=len(z), days=z.date.nunique(), parent=round(z.r.mean(), 4), variant=round(z.rv.mean(), 4),
                d=round(z.d.mean(), 4), t=round(tstat(z.d, z.date), 2), flip_p=round(flip(dd.to_numpy()), 4),
                better=int((z.d > 1e-9).sum()), worse=int((z.d < -1e-9).sum()), total_d=round(z.d.sum(), 1),
                gain_best_share=round(dd.max() / dd.sum(), 2) if dd.sum() > 0 else np.nan,
                weeks_up=f"{(wk > 0).sum()}/{len(wk)}", p_wo_best=round(pw, 4), v_wo_best=round(vw, 4),
                d_h1=round(z[z.date < mid].d.mean(), 4), d_h2=round(z[z.date >= mid].d.mean(), 4))


def book_view(m, per):
    out = {}
    for lab, rc, xc in (("parent", "r", "xm"), ("variant", "rv", "xmv")):
        z = m[m.per == per].copy(); z["r"] = z[rc]; z["xm"] = z[xc]; z["sx"] = z.symbol
        res = []
        for s, g in z.groupby("setup"):
            res.append(B.book(g, B.BOOK["primary"], etb))
        b = pd.concat(res); out[lab] = (len(b), b.r.sum(), b.groupby("date").r.sum())
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
    T = pd.concat([load("t1"), load("t2")], ignore_index=True)
    T = T[T.per != "none"]
    spy1 = B.spy_t1(); spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet"); spy2.index = spy2.index.astype(str)
    spy = pd.concat([spy1, spy2["type"]])
    rows = []
    for basis, a0, a1, tag in (("liveL", "p", "v", "VERDICT liveL+round"), ("liveL", "p_raw", "v_raw", "liveL raw (parity)"),
                               ("lr8", "p", "v", "LR8-bench+round")):
        m = pair(T, a0, a1, basis)
        for per in ("CHECK", "T2", "FIT"):
            for s in ("RW3", "RW5", "both"):
                z = m[(m.per == per) & (m.setup.str.startswith(s) | (s == "both"))]
                r = row(z, f"{tag} | {per} | {s}")
                if r: rows.append(r)
        if tag.startswith("VERDICT"):
            M = m
    R = pd.DataFrame(rows); print(R.to_string(index=False)); R.to_csv("exploration/sandbox/rw_target/bench_rows.csv", index=False)
    m = M
    print("\nexit crosstab (verdict arms, all splits): parent kind (rows) x variant kind (cols); 0 market 1 stop 2 target")
    for per in ("CHECK", "T2", "FIT"):
        z = m[m.per == per]; print(per); print(pd.crosstab(z.kind, z.kv))
        g = z[z.kind == 2]
        print(f"  parent-target lots: reach 1.25x {int((g.kv==2).sum())} (d {g[g.kv==2].d.mean():+.3f}) | flattened "
              f"{int((g.kv==0).sum())} (d {g[g.kv==0].d.mean():+.3f}) | stop {int((g.kv==1).sum())} (d {g[g.kv==1].d.mean():+.3f})")
    print("\nSPY day type split (verdict arms, both setups): d per lot (n)")
    m["spy"] = m.date.map(spy)
    print(m.groupby(["per", "spy"]).d.agg(["mean", "count"]).round(4).to_string())
    print("\nPrimary book view (cap 30, -2R latch on realized R), R per session, both setups")
    for per in ("CHECK", "T2", "FIT"):
        o = book_view(m, per); dp, dv = o["parent"][2], o["variant"][2]
        dd = dv.reindex(dp.index.union(dv.index), fill_value=0) - dp.reindex(dp.index.union(dv.index), fill_value=0)
        nd = m[m.per == per].date.nunique()
        e = dd - dd.mean(); tt = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd)))
        print(f"{per}: parent {o['parent'][0]} lots {o['parent'][1]:+.1f}R | variant {o['variant'][0]} lots {o['variant'][1]:+.1f}R | "
              f"d {dd.sum():+.1f}R over {nd} traded days = {dd.sum()/nd:+.3f} R/day (day t {tt:.2f})")
