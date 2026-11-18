"""U8 ranking + revival tunes (PLAN.md). Educational only - not financial advice."""
import sys, json, sqlite3, math, numpy as np, pandas as pd
sys.path.insert(0, ".")
from jload import load, S, ACC
OUT = S + "/wt/research/usage/u8_graveyard_prep/"
rng = np.random.default_rng(8)
FIT_END, CHK_START = "2026-10-30", "2026-11-02"
t = pd.read_pickle(S + "/gy_trades.pkl")
F = pd.read_pickle(S + "/feats.pkl")
t = t.join(F)
# extra journal columns
ex = []
for b, a in ACC.items():
    c = sqlite3.connect(f"{S}/j/{b}.db")
    e = pd.read_sql("select strategy,symbol,entry_time,mae_r,mfe_r,target,meta from trades where run_id=1", c); e["acct"] = a; ex.append(e)
ex = pd.concat(ex).drop_duplicates(["acct", "strategy", "symbol", "entry_time"])
t = t.merge(ex, on=["acct", "strategy", "symbol", "entry_time"], how="left")
def spread(m):
    try: return json.loads(m.split(";")[0]).get("spread_bps", np.nan)
    except Exception: return np.nan
t["spread"] = t.meta.map(spread)
t["cost"] = t.r_multiple - t.R
t["tgtR"] = np.where(t.target.notna(), (t.target - t.entry).abs() / (t.entry - t.stop).abs(), np.inf)
t["half"] = np.where(t.date <= FIT_END, "FIT", np.where(t.date >= CHK_START, "CHECK", "x"))
t["mwith"] = t.side * t.ret_open
# ---- menu
G = {"T1": lambda x: x.hhmm < 1030, "T2": lambda x: x.hhmm < 1130, "T3": lambda x: x.hhmm >= 1130, "T4": lambda x: x.hhmm >= 1300,
     "S1": lambda x: x.spy_ret > 0, "S2": lambda x: x.spy_ret < 0, "G1": lambda x: x.spy_gap > 0.002, "G2": lambda x: x.spy_gap <= 0.002,
     "K1": lambda x: x.gap > 0, "K2": lambda x: x.gap < 0, "V1": lambda x: x.above_vwap == True, "V2": lambda x: x.above_vwap == False,
     "M1": lambda x: x.mwith > 0, "M2": lambda x: x.mwith < 0, "C1": lambda x: x.spread <= 10}
def X(x, kind, v):
    R = x.R.copy(); ok = x.mae_r.notna() & x.mfe_r.notna()
    if kind == "tgt":
        hit = ok & (x.mfe_r >= v) & (x.tgtR > v); R[hit] = v - x.cost[hit]
    else:
        hit = ok & (x.mae_r <= -v); R[hit] = -v - x.cost[hit]
    return R
XS = {"X1": ("tgt", 0.5), "X2": ("tgt", 1.0), "X3": ("stop", 0.7)}
MENU = list(G) + list(XS)
def apply(x, changes):
    x = x.copy()
    for c in changes:
        if c in G: x = x[G[c](x).fillna(False).astype(bool)]
    for c in changes:
        if c in XS: x = x.assign(R=X(x, *XS[c]))
    return x
def stats(x):
    if len(x) == 0: return dict(n=0, avg=np.nan, wob=np.nan, share=np.nan, tot=0.0)
    d = x.groupby("date").R.sum(); bd = d.idxmax(); tot = d.sum()
    return dict(n=len(x), avg=x.R.mean(), wob=x[x.date != bd].R.mean() if (x.date != bd).any() else np.nan,
                share=d.max() / tot if tot > 0 else np.nan, tot=tot, days=d.size)
NCONF = 0
def choose(fit):
    global NCONF
    n0 = len(fit); best = None
    sc = {}
    for c in MENU:
        NCONF += 1; y = apply(fit, [c]); s = stats(y)
        if s["n"] >= 20 and s["n"] >= 0.25 * n0 and not np.isnan(s["wob"]): sc[(c,)] = s
    if not sc: return None, None
    b1 = max(sc, key=lambda k: sc[k]["wob"]); best = b1
    sc2 = {}
    for c in MENU:
        if c == b1[0]: continue
        if c in XS and b1[0] in XS: continue  # two exits of the same kind counted but skipped
        NCONF += 1; k = b1 + (c,); y = apply(fit, list(k)); s = stats(y)
        if s["n"] >= 20 and s["n"] >= 0.25 * n0 and not np.isnan(s["wob"]): sc2[k] = s
    if sc2:
        b2 = max(sc2, key=lambda k: sc2[k]["wob"])
        if sc2[b2]["wob"] >= sc[b1]["wob"] + 0.03: best = b2
    return best, (sc2.get(best) or sc[best])
# ---- ranking
MECH = {"RW6G1": 2, "RW6-": 2, "RW3S": 2, "RW4": 2, "NS3": 2, "CWT09": 2, "LIQ": 2, "heat_fade": 1, "NS2": 1, "RW2": 1,
        "CWT13": 1, "MF": 1, "NS5": 1, "ST": 0, "CWT12": 1, "CWT14": 1}
def mech(s):
    for k, v in MECH.items():
        if s.startswith(k): return v
    return 0
prim = load(); prim = prim[prim.acct == "Primary"].groupby("date").R.sum()
rows, tunes = [], {}
for s, g in t.groupby("strategy"):
    closed = s.startswith(("CWT12", "CWT14"))
    per = {"ALL": g, "FIT": g[g.half == "FIT"], "CHECK": g[g.half == "CHECK"], "GY": g[g.acct == "Graveyard"]}
    st = {k: stats(v) for k, v in per.items()}
    pos = [k for k in per if st[k]["n"] >= 10 and st[k]["wob"] > 0]
    d = g.groupby("date").R.sum(); j = pd.concat([d, prim], axis=1, join="inner")
    rho = j.iloc[:, 0].corr(j.iloc[:, 1]) if len(j) > 5 else np.nan
    fit = per["FIT"]
    best, bs = choose(fit) if len(fit) >= 20 else (None, None)
    fx = 0
    if best is not None:
        fx = 2 if bs["wob"] > 0 else (1 if bs["avg"] - st["FIT"]["avg"] >= 0.10 else 0)
    sib = s.startswith("RW3S")
    cs = 1 if (abs(rho) < 0.2 and not sib) else (0 if (abs(rho) < 0.4 and not sib) else -1)
    score = (2 if pos else 0) + 0.5 * len(pos) + mech(s) + fx + cs
    tunes[s] = best
    rows.append(dict(setup=s, closed_guardrail=closed, n=st["ALL"]["n"], days=st["ALL"]["days"], avgR=st["ALL"]["avg"],
        wob=st["ALL"]["wob"], totR=st["ALL"]["tot"], fit_n=st["FIT"]["n"], fit_wob=st["FIT"]["wob"], chk_n=st["CHECK"]["n"],
        chk_wob=st["CHECK"]["wob"], gy_n=st["GY"]["n"], gy_avg=st["GY"]["avg"], gy_wob=st["GY"]["wob"],
        pos_periods="+".join(pos), mech=mech(s), rho_primary=rho, fix=fx, fit_tune="+".join(best) if best else "",
        fit_tune_avg=bs["avg"] if bs else np.nan, fit_tune_wob=bs["wob"] if bs else np.nan, corr_pts=cs, score=score))
R = pd.DataFrame(rows)
R["rank_key"] = np.where(R.closed_guardrail, -99, R.score)
R = R.sort_values(["rank_key", "wob"], ascending=False).reset_index(drop=True)
R["rank"] = np.arange(1, len(R) + 1)
top = R[~R.closed_guardrail & (R.fit_tune != "")].head(10).setup.tolist()
N = NCONF
bar = max(1.5, math.sqrt(2 * math.log(N)))
# ---- CHECK verdicts
V = []
for s in top:
    g = t[(t.strategy == s) & (t.half == "CHECK")]
    ch = tunes[s].split("+") if isinstance(tunes[s], str) else list(tunes[s])
    y = apply(g, ch)
    p, q = stats(g), stats(y)
    pf, qf = stats(t[(t.strategy == s) & (t.half == "FIT")]), stats(apply(t[(t.strategy == s) & (t.half == "FIT")], ch))
    dp = g.groupby("date").R.sum(); dq = y.groupby("date").R.sum().reindex(dp.index, fill_value=0)
    diff = dq - dp
    tt = diff.mean() / (diff.std(ddof=1) / math.sqrt(len(diff))) if len(diff) > 1 and diff.std() > 0 else np.nan
    isgate = any(c in G for c in ch)
    if isgate and 0 < q["n"] < p["n"]:
        sims = np.array([g.R.sample(q["n"], random_state=int(rng.integers(1e9))).mean() for _ in range(2000)])
        pct = (sims < q["avg"]).mean()
    else:
        pct = np.nan
    passed = (q["n"] > 0 and q["avg"] > 0 and q["wob"] > 0 and (q["share"] < 0.5) and tt >= bar and (np.isnan(pct) or pct >= 0.95))
    lead = (not passed) and q["n"] > 0 and q["avg"] > 0 and q["wob"] > 0 and q["avg"] > p["avg"]
    V.append(dict(setup=s, tune="+".join(ch), fit_parent_n=pf["n"], fit_parent_avg=pf["avg"], fit_parent_wob=pf["wob"],
        fit_tuned_n=qf["n"], fit_tuned_avg=qf["avg"], fit_tuned_wob=qf["wob"],
        chk_parent_n=p["n"], chk_parent_avg=p["avg"], chk_parent_wob=p["wob"], chk_parent_tot=p["tot"], chk_parent_share=p["share"],
        chk_tuned_n=q["n"], chk_tuned_avg=q["avg"], chk_tuned_wob=q["wob"], chk_tuned_tot=q["tot"], chk_tuned_share=q["share"],
        chk_days=len(dp), d_tot=q["tot"] - p["tot"], t_paired=tt, bar=bar, rand_pct=pct,
        verdict="PASS" if passed else ("LEAD" if lead else "FAIL")))
V = pd.DataFrame(V)
R.drop(columns="rank_key").round(4).to_csv(OUT + "u8_ranking.csv", index=False)
V.round(4).to_csv(OUT + "u8_tunes.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
print("configs", N, "bar", round(bar, 2))
print(R[["rank","setup","closed_guardrail","n","avgR","wob","fit_wob","chk_wob","gy_n","gy_avg","gy_wob","pos_periods","mech","rho_primary","fix","fit_tune","fit_tune_avg","fit_tune_wob","score"]].round(3).to_string(index=False))
print(V.round(3).to_string(index=False))
