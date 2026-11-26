"""PRIMSHORTS-1126 live-calibrated cost model "LIVE-L" (1 cost model; the R3C model-1 data pipeline, refit in R units).
Per live trade (run 1, 10 journals, 10-06..11-25; R3C cleaning: multi-part exits, |fill-ref| > 2 %, price < $5, split-
adjusted exit bars, moved stops dropped) the realised cost in $/share =
  entry: side x (fill - decision-bar close) + LR8 1 bp;  exit: stop -> side x (engine stop fill - fill) (engine = stop, or
  the exit-minute open when gapped through, as bench10), market -> side x (exit-minute open - fill), target -> 0; + LR8
  exit costs and fees; + research borrow 1.2 bp (shorts) on both sides of the comparison.
Model: for each price bucket {5-10,10-20,20-50,50-100,100+} x exit kind {stop,market,target} (fallback: kind; cells < 50
trades). Spec v1 adopted. A v2 adding a side split was tried (validation error -0.015R vs v1 -0.013R; not adopted, disclosed):
  cost_R = a / width_bps + b   (OLS on winsorised [1,99] pct cost_R; width = |ref - stop| in bps of price)
  i.e. cost $/share = a bps of price (spread / fees part) + b x risk per share (volatility-scaled slippage part).
Validated on odd live days after a fit on even days, then refit on all days (cells_live.json). Research LR8 (bench10
add_r) is scored on the same trades. Educational only - not financial advice."""
import json, os, sys
import numpy as np, pandas as pd
WT = os.path.dirname(os.path.abspath(__file__)) + "/../.."
sys.path.insert(0, WT)
from mcf.research.gates import tod_cost_mult  # noqa: E402
L = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = os.path.dirname(os.path.abspath(__file__))
BORROW = 1.2e-4
PB = [5, 10, 20, 50, 100, 1e9]; PBL = ["5-10", "10-20", "20-50", "50-100", "100+"]
WB = [0, 50, 100, 200, 1e9]; WBL = ["<50", "50-100", "100-200", "200+"]
TB = [0, 1030, 1200, 1400, 2400]; TBL = ["<1030", "1030-1200", "1200-1400", ">=1400"]


def pbucket(p): return pd.cut(np.asarray(p, float), PB, labels=PBL, right=False).astype(str)
def wbucket(w): return pd.cut(np.asarray(w, float), WB, labels=WBL, right=False).astype(str)


def prep():
    t = pd.read_parquet(L + "/live.parquet")
    x = pd.read_parquet(L + "/exitbars.parquet").drop_duplicates("k")
    t = t.merge(x, on="k", how="left")
    n0 = len(t)
    t = t[t.ref_price.notna() & t.bar_time.notna() & ~t.multi_part]
    t["kind"] = t.exit_reason.map({"stop": "stop", "target": "target", "flatten": "market", "timestop": "market", "spy_exit": "market"})
    t = t[t.kind.notna()]
    t = t[(t.entry - t.ref_price).abs() / t.ref_price <= 0.02]
    t = t[t.ref_price >= 5]
    t = t[~t.kind.isin(["stop", "market"]) | t.x_open.notna()].copy()
    bt = t.bar_time.astype(int); m = (bt // 100) * 60 + bt % 100 + 1
    t["tod"] = (m // 60) * 100 + m % 60
    t["risk_ps"] = (t.ref_price - t.stop).abs()
    t = t[t.risk_ps > 0].copy()
    s = t.side
    badbar = t.kind.isin(["stop", "market"]) & ((t.x_open / t.exit - 1).abs() > 0.10)
    moved = (t.kind == "stop") & (s * (t.stop - t.exit) < -0.25 * t.risk_ps)
    t = t[~badbar & ~moved].copy()
    p, s, sh = t.ref_price, t.side, t.shares.abs()
    eng = np.where(s > 0, np.minimum(t.x_open, t.stop), np.maximum(t.x_open, t.stop))
    eng = np.where(np.isnan(t.x_open), t.stop, eng)
    xslip = np.where(t.kind == "stop", s * (eng - t.exit), np.where(t.kind == "market", s * (t.x_open - t.exit), 0.0))
    t["ent_ps"] = s * (t.entry - p) + t.lr8_entry_usd / sh
    t["ext_ps"] = xslip + (t.lr8_usd - t.lr8_entry_usd) / sh
    t["real_ps"] = t.ent_ps + t.ext_ps + np.where(s < 0, BORROW * p, 0.0)
    xpx = np.where(t.kind == "target", t.target, np.where(t.kind == "stop", t.stop, t.x_open))
    ec = (0.01 + p * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xc = np.where(t.kind == "target", 0.0, 0.01 + xpx * 1e-4) + np.where(t.kind == "stop", 0.02, 0.0)
    t["res_ps"] = ec + xc + np.where(s < 0, BORROW * p, 0.0)
    t["w_bps"] = t.risk_ps / p * 1e4
    t["pb"] = pbucket(p); t["wb"] = wbucket(t.w_bps)
    t["tb"] = pd.cut(t.tod, TB, labels=TBL, right=False).astype(str)
    t["real_R"] = t.real_ps / t.risk_ps; t["res_R"] = t.res_ps / t.risk_ps
    t["ent_R"] = t.ent_ps / t.risk_ps; t["ext_R"] = t.ext_ps / t.risk_ps
    print("live trades", n0, "-> used", len(t), "dates", t.date.min(), t.date.max())
    return t


def fit(t):
    w = t.copy()
    lo, hi = w.real_R.quantile([0.01, 0.99]); w["y"] = w.real_R.clip(lo, hi)
    cells = {}
    def ols(g):
        X = np.c_[1.0 / g.w_bps.to_numpy(), np.ones(len(g))]
        a, b = np.linalg.lstsq(X, g.y.to_numpy(), rcond=None)[0]
        return [float(a), float(b), int(len(g))]
    for k, g in w.groupby("kind"):
        cells[f"*|{k}"] = ols(g)
    for (pb, k), g in w.groupby(["pb", "kind"]):
        if len(g) >= 50:
            cells[f"{pb}|{k}"] = ols(g)
    return cells


def predict_R(cells, price, risk, kind, side=None):
    """cost in R for arrays (kind strings stop/market/target). Borrow (1.2 bp shorts) is inside the fit (live side)."""
    price = np.asarray(price, float); risk = np.asarray(risk, float); kind = np.asarray(kind).astype(str)
    pb = pbucket(price); w = risk / price * 1e4
    ab = np.array([cells.get(f"{a}|{k}", cells[f"*|{k}"])[:2] for a, k in zip(pb, kind)])
    return ab[:, 0] / w + ab[:, 1]


def tab(g):
    lo, hi = g.real_R.quantile([0.01, 0.99]); rw = g.real_R.clip(lo, hi)
    return pd.Series({"n": len(g), "live_R": rw.mean(), "lr8res_R": g.res_R.mean(), "liveL_R": g.cal_R.mean(),
                      "err_lr8": g.res_R.mean() - rw.mean(), "err_liveL": g.cal_R.mean() - rw.mean(),
                      "live_bps": (g.real_ps / g.ref_price * 1e4).mean(), "lr8_bps": (g.res_ps / g.ref_price * 1e4).mean(),
                      "entry_slip_R": g.ent_R.mean(), "med_w_bps": g.w_bps.median()})


if __name__ == "__main__":
    t = prep()
    days = sorted(t.date.unique()); fitd = set(days[0::2])
    F, V = t[t.date.isin(fitd)], t[~t.date.isin(fitd)].copy()
    V["cal_R"] = predict_R(fit(F), V.ref_price, V.risk_ps, V.kind, V.side)
    pd.set_option("display.width", 250)
    res = {"validation": {"ALL": tab(V).round(4).to_dict()}}
    print("VALIDATION (odd days) ALL\n", tab(V).round(4).to_string())
    fam = V.strategy.str.startswith(("L3-gap", "RW3", "RW5", "RW6", "RW7"))
    res["validation"]["gapdown_family"] = tab(V[fam]).round(4).to_dict()
    print("gap-down family\n", tab(V[fam]).round(4).to_string())
    for col in ("pb", "wb", "tb", "side", "kind"):
        x = V.groupby(col).apply(tab).round(4); print("\n== by", col); print(x.to_string())
        res["validation"][col] = x.to_dict("index")
    x = V[fam].groupby(["pb", "wb"]).apply(tab).round(4); print("\n== gap-down family by price x width"); print(x.to_string())
    # final: all days
    cells = fit(t)
    t["cal_R"] = predict_R(cells, t.ref_price, t.risk_ps, t.kind, t.side)
    A = {}
    for col in ("pb", "wb"):
        A[col] = t.groupby(col).apply(tab).round(4).to_dict("index")
    grid = t.groupby(["pb", "wb"]).apply(tab).round(4)
    print("\n== ALL DAYS price x width (live vs LR8 research)"); print(grid[["n", "live_R", "lr8res_R", "liveL_R", "err_lr8"]].to_string())
    A["pb_wb"] = {f"{a}|{b}": v for (a, b), v in grid.to_dict("index").items()}
    ps = {}
    for s0 in ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
               "L3-gap-slope-rsi5hi-FD", "RW6-ns2-up3-short-FD", "NM-ETF-late-dip-di-long"]:
        g = t[t.strategy == s0]
        if len(g): ps[s0] = tab(g).round(4).to_dict()
    print("\n== per setup (all days)"); print(pd.DataFrame(ps).T[["n", "live_R", "lr8res_R", "liveL_R", "err_lr8", "err_liveL", "entry_slip_R", "med_w_bps"]].to_string())
    res["all_days"] = A; res["per_setup"] = ps
    json.dump(cells, open(OUT + "/cells_live.json", "w"), indent=1)
    json.dump(res, open(OUT + "/calib_live.json", "w"), indent=1, default=float)
