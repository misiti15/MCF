"""rw7_1103 pass 3: score the 24 pre-registered configs (PLAN.md) on the open two-year history with costs in.
Cost per trade = max(0.10R, production model) (PLAN.md); 'prod' columns use the production model alone.
Writes results.csv, drivers_hist.txt, score_out.txt. Usage: python score.py <dir>   Educational only - not financial advice."""
import os, sys, json, math
from pathlib import Path
import numpy as np, pandas as pd
DR = Path(os.environ.get("MCF_DATA_ROOT", "/home/user/MCF"))
sys.path.insert(0, str(DR / "research" / "history2y")); sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402
from mcf.analytics import market_beta as MB  # noqa: E402
from mcf.strategies.setups import refire_select  # noqa: E402
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
D = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
TRAIN_END = pd.Timestamp("2025-12-31").date()
N_CFG = 24; TBAR = gates.t_required(N_CFG); TBAR_T = max(1.35, 0.9 * TBAR)


def load(what):
    a = pd.read_parquet(D / f"{what}.parquet"); s = pd.read_parquet(D / f"{what}_sim.parquet")
    a["rid"] = np.arange(len(a)); a = a.merge(s, on="rid", how="inner")
    a["date"] = pd.to_datetime(a.date).dt.date
    return a.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


C = load("cand"); K = load("ctrl")
# SPY 1-min closes for the BETA1 window and SPY open-to-close day type
spy = pd.read_parquet(DR / "data" / "cache_hist" / "1Min" / "SPY.parquet"); spy.index = pd.to_datetime(spy.index).tz_convert("America/New_York")
spy = spy.between_time("09:30", "15:59")
sk = pd.Series(spy.close.to_numpy(), index=pd.MultiIndex.from_arrays([spy.index.date, spy.index.hour * 60 + spy.index.minute]))
skd = dict(zip(zip(spy.index.date, spy.index.hour * 60 + spy.index.minute), spy.close.to_numpy()))
spy_oc = spy.groupby(spy.index.date).apply(lambda g: (g.close.iloc[-1] / g.open.iloc[0] - 1) * 100)
REG = gates.session_regimes(lib.daily())
lk = pd.read_csv(Path(__file__).resolve().parents[1] / "indexlink" / "linkage.csv", usecols=["symbol", "is_etf"])
ETF = set(lk.loc[lk.is_etf.astype(str).str.lower() == "true", "symbol"])
try:
    import subprocess
    U = pd.read_csv(Path(os.environ.get("RW7_UNIV", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rw7data/universe.csv")))
    LEV = set(U.loc[U.name.str.upper().str.contains(r"2X|3X|ULTRA|LEVERAGED|-1X|INVERSE|DAILY .*BULL|DAILY .*BEAR", na=False), "symbol"])
except Exception:
    LEV = set()
for X in (C, K):
    X["etf"] = X.symbol.isin(ETF | LEV); X["lev"] = X.symbol.isin(LEV)
    m0 = (X.tod // 100) * 60 + X.tod % 100
    X["spy_at"] = [skd.get((d, m - 1), np.nan) for d, m in zip(X.date, m0)]
    X["spy_oc"] = X.date.map(spy_oc).to_numpy(float)
    X["spy_fo"] = X.spy_fo.to_numpy(float) if "spy_fo" in X else np.nan


def cost_r(X, geom, floor=0.10):
    R = 0.25 * X.atr_d.to_numpy(float); px = X.close.to_numpy(float)
    tier = np.where((np.abs(X.gap.to_numpy(float)) >= 20) | (px < 5), 3.0, 1.0)
    side = (gates.SLIP_PS + px * gates.SLIP_BPS)
    k = X[f"k_{geom}"].to_numpy()
    c = side * gates.tod_cost_mult(X.tod.to_numpy(float)) + np.where(k == 2, 0.0, side) + np.where(k == 1, gates.STOP_EXTRA, 0.0)
    if geom == "part":
        c = c + 0.5 * side   # the second exit fill on half the shares
    c = c * tier / R
    return np.maximum(floor, c) if floor else c


def trades(X, mask, geom, cooldown=None, floor=0.10):
    idx = np.flatnonzero(np.asarray(mask, bool))
    if not len(idx):
        return pd.DataFrame(columns=["date", "r"])
    key = X.symbol.to_numpy()[idx].astype(str) + "|" + X.date.astype(str).to_numpy()[idx]
    brk = np.r_[True, key[1:] != key[:-1]]
    if cooldown is None:
        idx = idx[brk]
    else:
        b = ((X.tod.to_numpy()[idx] // 100) * 60 + X.tod.to_numpy()[idx] % 100 - 570) // 5
        st = np.flatnonzero(brk); en = np.r_[st[1:], len(idx)]; keep = []
        for a, e in zip(st, en):
            sel = set(refire_select(list(b[a:e]), cooldown))
            keep.extend(a + j for j, x in enumerate(b[a:e]) if x in sel)
        idx = idx[np.asarray(sorted(keep), int)]
    T = X.iloc[idx].copy()
    T["gross"] = T[f"g_{geom}"].to_numpy(float)
    T["r"] = T.gross - cost_r(T, geom, floor)
    T["kind"] = T[f"k_{geom}"]
    xm = T[f"x_{geom}"].to_numpy(int)
    T["spy_move"] = (np.array([skd.get((d, m), np.nan) for d, m in zip(T.date, xm)]) / T.spy_at.to_numpy(float) - 1) * 100
    return T


def score(T, ctrl_r=None, parent=None):
    s = gates.summary(T[["date", "r", "spy_move"]])
    tr = T[T.date <= TRAIN_END]; va = T[T.date > TRAIN_END]
    rg = gates.regime_split(T[["date", "r"]], REG)
    wf = gates.walk_forward(T[["date", "r"]], exclude_months=lib.LOCKED_MONTHS)
    g = T.groupby("date").r.sum(); best = g.idxmax()
    dt = np.select([T.spy_oc > 0.25, T.spy_oc < -0.25], ["up", "down"], "quiet")
    o = dict(n=s["n"], days=s["days"], per_day=round(s["n"] / max(1, T.date.nunique()), 2), exp_r=s["exp_r"], t=s["t"],
             win=s["win_rate"], wo_best=s["ex_best_day"], best_share=round(g.max() / g.sum(), 3) if g.sum() > 0 else None,
             exmkt=s.get("ex_market_r"), beta=s.get("beta"),
             train=round(tr.r.mean(), 4) if len(tr) else None, train_n=len(tr), valid=round(va.r.mean(), 4) if len(va) else None,
             valid_n=len(va), valid_t=gates.summary(va[["date", "r"]]).get("t") if len(va) else None,
             reg_up=rg["up"].get("exp_r"), reg_flat=rg["flat"].get("exp_r"), reg_down=rg["down"].get("exp_r"), reg_pass=rg["pass"],
             wf=wf["share_positive"], spy_up=round(T.r[dt == "up"].mean(), 4), spy_quiet=round(T.r[dt == "quiet"].mean(), 4),
             spy_down=round(T.r[dt == "down"].mean(), 4),
             tgt=round((T.kind == 2).mean(), 3), stop=round((T.kind == 1).mean(), 3), time=round((T.kind == 0).mean(), 3),
             gross=round(T.gross.mean(), 4), cost=round((T.gross - T.r).mean(), 4))
    if ctrl_r is not None:
        o["random"] = round(ctrl_r, 4); o["vs_random"] = round(o["exp_r"] - ctrl_r, 4)
    if parent is not None:
        pk = set(zip(parent.symbol, parent.date)); k = set(zip(T.symbol, T.date))
        top = parent[parent.r >= parent.r.quantile(0.9)]
        o["kept_trades"] = round(len(pk & k) / len(pk), 3)
        o["kept_top10"] = round(np.mean([(a, b) in k for a, b in zip(top.symbol, top.date)]), 3)
    return o


def ctrl_match(T, geom):
    """Random-entry expectancy matched to T's (date, tod) mix: mean control r per tod bucket (30 min) x month, weighted."""
    Kr = K.copy(); Kr["r"] = Kr[f"g_{geom}"] - cost_r(Kr, geom)
    Kr["b"] = (Kr.tod // 100) * 2 + (Kr.tod % 100 >= 30); Kr["mo"] = pd.PeriodIndex(pd.to_datetime(Kr.date), freq="M")
    cm = Kr.groupby(["mo", "b"]).r.mean()
    tb = (T.tod // 100) * 2 + (T.tod % 100 >= 30); tm = pd.PeriodIndex(pd.to_datetime(T.date), freq="M")
    v = np.array([cm.get((a, b), np.nan) for a, b in zip(tm, tb)])
    return float(np.nanmean(v))


base = (C.heat <= -20) & (C.buyPressure < -0.15) & C.rsi.between(55, 65) & (C.gap < 0)
CFG = {
    "P0": (base, "t1s1", None),
    "W1": (base & (C.tod >= 1030), "t1s1", None), "W2": (base & C.tod.between(1030, 1300), "t1s1", None),
    "W3": (base & (C.tod <= 1400), "t1s1", None),
    "R1": ((C.heat <= -20) & (C.buyPressure < -0.15) & C.rsi.between(50, 60) & (C.gap < 0), "t1s1", None),
    "R2": ((C.heat <= -20) & (C.buyPressure < -0.15) & C.rsi.between(60, 70) & (C.gap < 0), "t1s1", None),
    "H1": ((C.heat <= -24) & (C.buyPressure < -0.18) & C.rsi.between(55, 65) & (C.gap < 0), "t1s1", None),
    "H2": ((C.heat <= -16) & (C.buyPressure < -0.12) & C.rsi.between(55, 65) & (C.gap < 0), "t1s1", None),
    "E1": (base, "t15s1", None), "E2": (base, "t05s1", None), "E3": (base, "part", None), "E4": (base, "ts60", None),
    "E5": (base, "be05", None),
    "M1": (base & (C.spy_fo < 0), "t1s1", None), "M2": (base & (C.spy_fo <= -0.25), "t1s1", None),
    "U1": (base & (C["rank"] <= 500), "t1s1", None), "U2": (base & (C.adv20 >= 300e6), "t1s1", None),
    "C1": (base, "t1s1", 12), "C2": (base, "t1s1", 6),
    "G1": (base & (C.gap <= -1.0), "t1s1", None),
    "K1": (base & (C.spy_fo < 0), "t05s1", None), "K2": (base & (C.spy_fo < 0) & (C.tod >= 1030), "t1s1", None),
    "K3": (base & C.etf, "t1s1", None), "K4": (base & ~C.etf, "t1s1", None),
}
assert len(CFG) == N_CFG
out = []
P = lambda *a: (out.append(" ".join(str(x) for x in a)), print(*a, flush=True))
# sanity: simulated t1s1 vs the lab's r_short_t1s1 (lab charges 1c per side)
par = trades(C, base, "t1s1")
lab_g = par.r_short_t1s1 + 2 * 0.01 / (0.25 * par.atr_d)
P("# rw7_1103 score. Educational only - not financial advice.")
P(f"sanity P0: sim gross t1s1 {par.gross.mean():+.4f} vs lab gross {lab_g.mean():+.4f}; |diff|<0.05R on {(np.abs(par.gross - lab_g) < 0.05).mean():.1%} of {len(par)} trades")
res = {}
for k, (m, g, cd) in CFG.items():
    T = trades(C, m, g, cd)
    res[k] = score(T, ctrl_match(T, g), None if k == "P0" else par)
    Tp = trades(C, m, g, cd, floor=0); res[k]["exp_prod"] = round(Tp.r.mean(), 4); res[k]["t_prod"] = gates.summary(Tp[["date", "r"]])["t"]
    P(k, json.dumps(res[k]))
R = pd.DataFrame(res).T
R.insert(0, "config", R.index)
R["testing_bar"] = TBAR_T; R["full_bar"] = TBAR
R.to_csv(HERE / "results.csv", index=False)
P(f"\nN = {N_CFG} configs; full bar t >= {TBAR}; Testing bar t >= {TBAR_T:.2f}")
# drivers on the parent (history)
par["tb"] = pd.cut(par.tod, [949, 1030, 1130, 1300, 1400, 1501]); par["gb"] = pd.cut(par.gap, [-99, -3, -1.5, -0.75, -0.3, 0])
par["rb"] = pd.cut(par.rsi, [54.99, 58, 61, 65.01]); par["hb"] = pd.cut(par.heat, [-100, -40, -30, -25, -20])
par["bb"] = pd.cut(par.buyPressure, [-1.01, -0.4, -0.3, -0.2, -0.15]); par["ab"] = pd.cut(par.adv20 / 1e6, [0, 150, 300, 700, 2000, 1e7])
par["atrp"] = pd.cut(par.atr_d / par.close * 100, [0, 2, 3, 5, 8, 100]); par["sb"] = pd.cut(par.spy_fo, [-9, -0.5, -0.25, 0, 0.25, 0.5, 9])
par["dt"] = np.select([par.spy_oc > 0.25, par.spy_oc < -0.25], ["up", "down"], "quiet"); par["kd"] = np.where(par.lev, "leveraged", np.where(par.etf, "etf", "stock"))
for c, lab in (("tb", "time of day"), ("gb", "gap %"), ("rb", "RSI"), ("hb", "heat"), ("bb", "buyPressure"), ("ab", "ADV $M"),
               ("atrp", "ATR%"), ("sb", "SPY from open at entry"), ("dt", "SPY day type"), ("kd", "kind"), ("kind", "exit 0 time/1 stop/2 target")):
    P(f"\n## P0 history by {lab}")
    P(par.groupby(c, observed=True).agg(n=("r", "size"), exp=("r", "mean"), win=("r", lambda x: (x > 0).mean())).round(3).to_string())
g = par.groupby("date").r.sum()
p_green = (g > 0).mean()
P(f"\nP0 history: {len(g)} sessions, green-session share {p_green:.3f}; trades/session {len(par) / len(g):.1f}")
# chance of the live run: 3 green in a row anywhere in 17 sessions, at the history green rate and at the live rate
rng = np.random.default_rng(1)
for p in (p_green, 8 / 17):
    sims = rng.random((100000, 17)) < p
    run3 = np.any(sims[:, 2:] & sims[:, 1:-1] & sims[:, :-2], axis=1).mean()
    P(f"p(green)={p:.3f}: P(last 3 green) = {p ** 3:.3f}; P(some 3-green run in 17 sessions) = {run3:.3f}")
(HERE / "score_out.txt").write_text("\n".join(out) + "\n")
