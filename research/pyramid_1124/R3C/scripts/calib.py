"""R3C live-calibrated cost model (PREREG.md sec 1). Educational only - not financial advice."""
import sys, json, os
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX)
from mcf.research.gates import tod_cost_mult
H = os.path.dirname(os.path.abspath(__file__))
BORROW = 1.2e-4
PB = [5, 10, 20, 50, 100, 1e9]; PBL = ["5-10", "10-20", "20-50", "50-100", "100+"]
TB = [0, 1030, 1200, 1400, 2400]; TBL = ["<1030", "1030-1200", "1200-1400", ">=1400"]
WB = [0, 50, 100, 200, 1e9]; WBL = ["<50", "50-100", "100-200", "200+"]

def pbucket(p): return pd.cut(p, PB, labels=PBL, right=False).astype(str)
def tband(tod): return pd.cut(tod, TB, labels=TBL, right=False).astype(str)

def prep():
    t = pd.read_parquet(H + "/live.parquet")
    x = pd.read_parquet(H + "/exitbars.parquet").drop_duplicates("k")
    t = t.merge(x, on="k", how="left")
    n0 = len(t)
    t = t[t.ref_price.notna() & t.bar_time.notna() & ~t.multi_part]
    t["kind"] = t.exit_reason.map({"stop": "stop", "target": "target", "flatten": "market", "timestop": "market", "spy_exit": "market"})
    t = t[t.kind.notna()]
    t = t[(t.entry - t.ref_price).abs() / t.ref_price <= 0.02]
    t = t[t.ref_price >= 5]
    need_bar = t.kind.isin(["stop", "market"])
    t = t[~need_bar | t.x_open.notna()].copy()
    bt = t.bar_time.astype(int); m = (bt // 100) * 60 + bt % 100 + 1          # decision = close of bar labelled bar_time
    t["tod"] = (m // 60) * 100 + m % 60
    p = t.ref_price; s = t.side; sh = t.shares.abs()
    t["risk_ps"] = (t.ref_price - t.stop).abs()
    t = t[t.risk_ps > 0]
    p = t.ref_price; s = t.side; sh = t.shares.abs()
    eng_stop = np.where(s > 0, np.minimum(t.x_open, t.stop), np.maximum(t.x_open, t.stop))
    eng_stop = np.where(np.isnan(t.x_open), t.stop, eng_stop)
    xslip = np.where(t.kind == "stop", s * (eng_stop - t.exit), np.where(t.kind == "market", s * (t.x_open - t.exit), 0.0))
    # cleaning (post-PREREG, disclosed): split-adjusted exit bars (>10% off the fill) and stop exits filled > 0.25R better
    # than the journal stop (the stop had been moved: trailing / breakeven) are dropped
    badbar = t.kind.isin(["stop", "market"]) & ((t.x_open / t.exit - 1).abs() > 0.10)
    moved = (t.kind == "stop") & (s * (t.stop - t.exit) < -0.25 * t.risk_ps)
    print("dropped split-bar", int(badbar.sum()), "moved-stop", int(moved.sum()))
    t = t[~badbar & ~moved].copy(); eng_stop = eng_stop[(~badbar & ~moved).to_numpy()]
    p = t.ref_price; s = t.side; sh = t.shares.abs()
    xslip = np.where(t.kind == "stop", s * (eng_stop - t.exit), np.where(t.kind == "market", s * (t.x_open - t.exit), 0.0))
    t["ent_ps"] = s * (t.entry - p) + t.lr8_entry_usd / sh
    t["ext_ps"] = xslip + (t.lr8_usd - t.lr8_entry_usd) / sh          # exit slippage + LR8 exit + fees
    t["ent_bps"] = t.ent_ps / p * 1e4; t["ext_bps"] = t.ext_ps / p * 1e4
    # research model on the same trade (bench10 add_r, tier 1 for live >= $5; gap unknown -> x1)
    xpx = np.where(t.kind == "target", t.target, np.where(t.kind == "stop", t.stop, t.x_open))
    ec = (0.01 + p * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xc = np.where(t.kind == "target", 0.0, 0.01 + xpx * 1e-4) + np.where(t.kind == "stop", 0.02, 0.0)
    t["res_ps"] = ec + xc + np.where(s < 0, BORROW * p, 0.0)
    t["res_ent_ps"] = ec; t["res_ext_ps"] = xc
    t["pb"] = pbucket(p); t["tb"] = tband(t.tod)
    t["wb"] = pd.cut(t.risk_ps / p * 1e4, WB, labels=WBL, right=False).astype(str)
    print("live trades", n0, "-> used", len(t))
    return t

def fit_cells(t):
    lo, hi = {}, {}
    w = t.copy()
    for c in ("ent_bps", "ext_bps"):
        a, b = w[c].quantile([0.01, 0.99]); w[c] = w[c].clip(a, b)
    cells = {"entry": {}, "exit": {}, "entry_pb": {}, "exit_pb": {}, "n": len(w)}
    for pb, g in w.groupby("pb"):
        cells["entry_pb"][pb] = float(g.ent_bps.mean())
        cells["exit_pb"][pb] = {k: float(gg.ext_bps.mean()) for k, gg in g.groupby("kind")}
    for (pb, tb), g in w.groupby(["pb", "tb"]):
        if len(g) >= 50: cells["entry"][f"{pb}|{tb}"] = [float(g.ent_bps.mean()), len(g)]
    for (pb, k), g in w.groupby(["pb", "kind"]):
        if len(g) >= 50: cells["exit"][f"{pb}|{k}"] = [float(g.ext_bps.mean()), len(g)]
    return cells

def fit_cells2(t):
    w = t.copy()
    for c in ("ent_bps", "ext_bps"):
        a, b = w[c].quantile([0.01, 0.99]); w[c] = w[c].clip(a, b)
    c2 = {"entry": {}, "exit": {}, "exit_kw": {}}
    for (pb, wb), g in w.groupby(["pb", "wb"]):
        if len(g) >= 50: c2["entry"][f"{pb}|{wb}"] = float(g.ent_bps.mean())
    for (pb, k, wb), g in w.groupby(["pb", "kind", "wb"]):
        if len(g) >= 50: c2["exit"][f"{pb}|{k}|{wb}"] = float(g.ext_bps.mean())
    for (k, wb), g in w.groupby(["kind", "wb"]):
        if len(g) >= 50: c2["exit_kw"][f"{k}|{wb}"] = float(g.ext_bps.mean())
    return c2

def predict2_ps(c1, c2, price, tod, kind, side, risk):
    """model 2: kind as strings {stop,target,market}; risk $/share."""
    price = np.asarray(price, float); risk = np.asarray(risk, float)
    pb = pbucket(pd.Series(price)).to_numpy(); tb = tband(pd.Series(np.asarray(tod, float))).to_numpy()
    wb = pd.cut(pd.Series(risk / price * 1e4), WB, labels=WBL, right=False).astype(str).to_numpy()
    kind = np.asarray(kind).astype(str)
    k_e = pd.Series([f"{a}|{b}" for a, b in zip(pb, wb)])
    e = k_e.map(c2["entry"]).to_numpy(float)
    e1 = pd.Series([f"{a}|{b}" for a, b in zip(pb, tb)]).map({k: v[0] for k, v in c1["entry"].items()}).to_numpy(float)
    e1 = np.where(np.isnan(e1), pd.Series(pb).map(c1["entry_pb"]).to_numpy(float), e1)
    e = np.where(np.isnan(e), e1, e)
    x = pd.Series([f"{a}|{k}|{b}" for a, k, b in zip(pb, kind, wb)]).map(c2["exit"]).to_numpy(float)
    xk = pd.Series([f"{k}|{b}" for k, b in zip(kind, wb)]).map(c2["exit_kw"]).to_numpy(float)
    x1 = pd.Series([f"{a}|{k}" for a, k in zip(pb, kind)]).map({k: v[0] for k, v in c1["exit"].items()}).to_numpy(float)
    x = np.where(np.isnan(x), np.where(np.isnan(xk), x1, xk), x)
    return (e + x) * price / 1e4 + np.where(np.asarray(side) < 0, BORROW * price, 0.0)

def predict_ps(cells, price, tod, kind, side):
    """calibrated $/share cost for arrays: price, entry tod (HHMM decision), exit kind in {stop,target,market}, side."""
    price = np.asarray(price, float); pb = pbucket(pd.Series(price)).to_numpy(); tb = tband(pd.Series(np.asarray(tod, float))).to_numpy()
    kind = np.asarray(kind); side = np.asarray(side)
    eb = np.array([cells["entry"].get(f"{a}|{b}", [cells["entry_pb"].get(a, np.nan)])[0] for a, b in zip(pb, tb)])
    xb = np.array([cells["exit"].get(f"{a}|{k}", [cells["exit_pb"].get(a, {}).get(k, np.nan)])[0] for a, k in zip(pb, kind)])
    return (eb + xb) * price / 1e4 + np.where(side < 0, BORROW * price, 0.0)

if __name__ == "__main__":
    t = prep()
    t["real_ps"] = t.ent_ps + t.ext_ps + np.where(t.side < 0, BORROW * t.ref_price, 0.0)   # borrow kept on both sides of the comparison
    days = sorted(t.date.unique()); fitd = set(days[0::2])
    F, V = t[t.date.isin(fitd)], t[~t.date.isin(fitd)].copy()
    cf = fit_cells(F)
    V["cal_ps"] = predict_ps(cf, V.ref_price, V.tod, V.kind, V.side)
    MODEL2 = os.environ.get("MODEL2") == "1"
    if MODEL2:
        V["cal_ps"] = predict2_ps(cf, fit_cells2(F), V.ref_price, V.tod, V.kind, V.side, V.risk_ps)
    V["e_res"] = (V.res_ps - V.real_ps) / V.risk_ps; V["e_cal"] = (V.cal_ps - V.real_ps) / V.risk_ps
    V["real_R"] = V.real_ps / V.risk_ps; V["res_R"] = V.res_ps / V.risk_ps; V["cal_R"] = V.cal_ps / V.risk_ps
    out = {"n_fit": len(F), "n_val": len(V), "fit_days": len(fitd), "val_days": len(days) - len(fitd)}
    def tab(g):
        lo, hi = g.real_R.quantile([0.01, 0.99]); rw = g.real_R.clip(lo, hi)
        # robust: trim 1% tails of realised for the mean error display as well as raw
        return pd.Series({"n": len(g), "real_R": g.real_R.mean(), "res_R": g.res_R.mean(), "cal_R": g.cal_R.mean(),
                          "err_res": g.e_res.mean(), "err_cal": g.e_cal.mean(), "real_R_w": rw.mean(),
                          "err_res_w": g.res_R.mean() - rw.mean(), "err_cal_w": g.cal_R.mean() - rw.mean(),
                          "real_R_med": g.real_R.median(), "real_bps": (g.real_ps / g.ref_price * 1e4).mean(),
                          "res_bps": (g.res_ps / g.ref_price * 1e4).mean(), "cal_bps": (g.cal_ps / g.ref_price * 1e4).mean()})
    pd.set_option("display.width", 250)
    res = {"ALL": tab(V).round(4).to_dict()}
    print("VALIDATION ALL\n", tab(V).round(4).to_string())
    for col in ("pb", "wb", "tb", "side", "kind"):
        x = V.groupby(col).apply(tab).round(4)
        print("\n== by", col); print(x.to_string()); res[col] = x.to_dict("index")
    # gap-down short family / small names
    fam = V.strategy.str.startswith(("L3-gap", "RW3", "RW5", "RW6", "RW7"))
    print("\n== gap-down family"); print(tab(V[fam]).round(4).to_string()); res["gapdown_family"] = tab(V[fam]).round(4).to_dict()
    print("\n== spread_bps bucket (diagnostic)"); x = V.groupby(pd.cut(V.spread_bps, [0, 5, 10, 15, 20, 31])).apply(tab).round(4); print(x.to_string())
    res["by_spread"] = {str(k): v for k, v in x.to_dict("index").items()}
    wins = (V.groupby("pb").apply(lambda g: abs(g.cal_R.mean() - g.real_R.clip(*g.real_R.quantile([.01, .99])).mean()) < abs(g.res_R.mean() - g.real_R.clip(*g.real_R.quantile([.01, .99])).mean())).sum(),
            V.groupby("wb").apply(lambda g: abs(g.cal_R.mean() - g.real_R.clip(*g.real_R.quantile([.01, .99])).mean()) < abs(g.res_R.mean() - g.real_R.clip(*g.real_R.quantile([.01, .99])).mean())).sum(),
            V.groupby("tb").apply(lambda g: abs(g.cal_R.mean() - g.real_R.clip(*g.real_R.quantile([.01, .99])).mean()) < abs(g.res_R.mean() - g.real_R.clip(*g.real_R.quantile([.01, .99])).mean())).sum())
    print("bucket wins (pb/wb/tb):", wins)
    res["bucket_wins_pb_wb_tb"] = [int(w) for w in wins]
    # component view on all days
    comp = t.groupby("pb").agg(n=("ent_bps", "size"), ent_bps=("ent_bps", "median"), ent_bps_mean=("ent_bps", "mean"),
                               res_ent_bps=("res_ent_ps", lambda s: (s / t.loc[s.index, "ref_price"] * 1e4).mean()),
                               spread=("spread_bps", "median")).round(2)
    print("\n== entry component (all days)\n", comp.to_string())
    comp2 = t.groupby(["pb", "kind"]).agg(n=("ext_bps", "size"), ext_bps=("ext_bps", "mean"), ext_med=("ext_bps", "median"),
                                          res_ext_bps=("res_ext_ps", lambda s: (s / t.loc[s.index, "ref_price"] * 1e4).mean())).round(2)
    print("\n== exit component (all days)\n", comp2.to_string())
    final = fit_cells(t)
    if MODEL2:
        json.dump(fit_cells2(t), open(H + "/cells2.json", "w"), indent=1)
        json.dump(res, open(H + "/calib_validation2.json", "w"), indent=1, default=float)
        raise SystemExit
    json.dump(final, open(H + "/cells.json", "w"), indent=1)
    json.dump(res, open(H + "/calib_validation.json", "w"), indent=1, default=float)
    print("\nFINAL cells (all days):", json.dumps({k: v for k, v in final.items() if k in ("entry_pb", "exit_pb")}, indent=0))
