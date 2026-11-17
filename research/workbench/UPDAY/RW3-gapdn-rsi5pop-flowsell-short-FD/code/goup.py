"""python goup.py <rw5|rw3> <decl module> <ROUND>. Educational only - not financial advice."""
import sys, importlib, pandas as pd, numpy as np
import uplayer as U
SETUP = sys.argv[1]
import load as L
if SETUP == "rw5":
    import sim2 as S; import sim as BK
    sig = S.signals; book = BK.book; paired_t = BK.paired_t
else:
    import sim_rw3 as S
    sig = S.signals; book = S.book; paired_t = S.paired_t
S1 = pd.read_parquet("spy1m_all.parquet"); S1.index = pd.DatetimeIndex(S1.index).tz_convert("America/New_York")
SPY, SPYC = U.spy_tables(S1)
DT = pd.read_parquet("spyday.parquet").set_index("date")
CAND = {"replay": (U.add_spy(L.RF, SPY).sort_values(["symbol", "date", "tod"]).reset_index(drop=True), L.getA),
        "2y": (U.add_spy(L.C, SPY).sort_values(["symbol", "date", "tod"]).reset_index(drop=True), L.getB)}
def run(v):
    out = {}
    for test, (cand, get) in CAND.items():
        t = book(U.trades(cand, v, get, SPYC, sig), v)
        t["dtype"] = t.date.map(DT.dtype)
        if test == "2y": t["split"] = t.date.map(L.split)
        out[test] = t
    return out
decl = importlib.import_module(sys.argv[2]); cfgs = getattr(decl, sys.argv[3])
rows = []; base = {}; allt = {}
for name, v in cfgs.items():
    o = run(v); allt[name] = o
    for test, t in o.items():
        if name in ("PARENT", "WB3"): base[(name, test)] = t
        days = L.DAYS[test]
        r = dict(cfg=name, test=test, **U.stats(t), per_day=t.r.sum() / len(days))
        for dt in ("up", "down", "quiet"):
            x = t[t.dtype == dt]; r["n_" + dt] = len(x); r["avg_" + dt] = x.r.sum() / x.w.sum() if len(x) else np.nan; r["R_" + dt] = x.r.sum()
        if test == "2y":
            for sp in ("TRAIN", "VALID", "FWD"):
                x = t[t.split == sp]; r["avg_" + sp] = x.r.sum() / x.w.sum() if len(x) else np.nan
        for bn in ("PARENT", "WB3"):
            b = base.get((bn, test))
            if b is not None:
                r["t_vs_" + bn], r["dR_vs_" + bn] = paired_t(b, t, days)
        rows.append(r)
    a = [x for x in rows if x["cfg"] == name]
    print(f"{name:50s} " + " | ".join(f"{x['test']} n{x['trades']} {x['avg']:+.3f} wo{x['avg_wo_best']:+.3f} wd{x['worst_day']:+.1f} up{x['avg_up']:+.3f} dn{x['avg_down']:+.3f} q{x['avg_quiet']:+.3f}" for x in a), flush=True)
pd.DataFrame(rows).to_csv(f"res_{sys.argv[3]}.csv", index=False, float_format="%.4f")
pd.to_pickle(allt, f"trades_{sys.argv[3]}.pkl")
