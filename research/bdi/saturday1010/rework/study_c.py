"""Saturday 2026-10-10 rework, lineage C: crash guards on the longhold momentum near-misses (NOTES.md 1.6/1.7).
Executes research/longhold/study.py up to its grid (data, features, simulator; locked-block returns zeroed there),
reads the parent and benchmark series from its sim_cache.npz (read-only) and writes nothing outside this folder.
Outputs: results_c.csv, gates_c.csv, diag_c.json. Educational only - not financial advice.
    python research/bdi/saturday1010/rework/study_c.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LH = ROOT / "research" / "longhold"
DATA = HERE / "data"
sys.path.insert(0, str(ROOT))
assert os.environ.get("MCF_HIST_ALLOW_LOCKED") is None
from mcf.research.gates import t_required, walk_forward  # noqa: E402

src = (LH / "study.py").read_text()
MARK = "# ---------------------------------------------------------------------------------------------- "
prefix = src.split(MARK + "grid")[0]
stats_src = src.split(MARK + "statistics")[1].split("PERIODS = ")[0]
assert "R[locked] = 0.0" in prefix
S: dict = {"__name__": "lhstudy", "__file__": str(LH / "study.py")}
exec(compile(prefix, str(LH / "study.py"), "exec"), S)
dates, T, NS, col, locked = S["dates"], S["T"], S["NS"], S["col"], S["locked"]
ELIG, R_cc, FEAT = S["ELIG"], S["R_cc"], S["FEAT"]
Cn = S["Cn"]
LOCK_A, LOCK_B = S["LOCK_A"], S["LOCK_B"]

z = np.load(LH / "data" / "sim_cache.npz")
SER = {k: tuple(z[k]) for k in ("BH_SPY", "BENCH_EW", "S6_mom12_1rev_N20_M", "S1_mom12_1_N50_W")}
CACHE_IDS = [k for k in z.files if "__" not in k]
S["SER"] = SER
BENCH_OF = {}
S["BENCH_OF"] = BENCH_OF
exec(compile(stats_src, str(LH / "study.py") + ":statistics", "exec"), S)
stats, period_mask = S["stats"], S["period_mask"]

# ---------------------------------------------------------------------------------------------- guard features
def _no_locked(df):
    d = pd.to_datetime(df["date"])
    assert not ((d >= LOCK_A) & (d <= LOCK_B)).any()
    return df


vix = _no_locked(pd.read_parquet(DATA / "cboe_vol_indices.parquet"))
vw = vix.pivot(index="date", columns="index", values="close").sort_index()
vw.index = pd.to_datetime(vw.index)
TR = (vw["VIX"] / vw["VIX3M"]).reindex(dates).to_numpy()
VIXP = vw["VIX"].dropna().rolling(252, min_periods=200).apply(lambda x: (x <= x[-1]).mean(), raw=True).reindex(dates).to_numpy()
spy = pd.Series(Cn[:, col["SPY"]], index=dates)
SPY200 = (spy > spy.rolling(200, min_periods=200).mean()).to_numpy()
BEAR = (spy / spy.shift(504) - 1 < 0).to_numpy()

# momentum-factor proxy (own bars): top-minus-bottom decile of 12-1 momentum, re-formed at each month end
MONTH_END = S["MONTH_END"]
proxy = np.zeros(T)
F = FEAT["mom12_1"]
for a, b in zip(MONTH_END[:-1], MONTH_END[1:]):
    if a < 252:
        continue
    ok = ELIG[a] & ~np.isnan(F[a])
    idx = np.flatnonzero(ok)
    if len(idx) < 50:
        continue
    q = np.nanquantile(F[a, idx], [0.1, 0.9])
    top, bot = idx[F[a, idx] >= q[1]], idx[F[a, idx] <= q[0]]
    proxy[a + 1:b + 1] = R_cc[a + 1:b + 1][:, top].mean(1) - R_cc[a + 1:b + 1][:, bot].mean(1)
open_idx = np.flatnonzero(~locked)
MOMVOL = np.full(T, np.nan)
first = MONTH_END[MONTH_END >= 252][0] + 1
for d in range(first, T):
    h = open_idx[(open_idx <= d) & (open_idx >= first)][-126:]
    if len(h) >= 100:
        MOMVOL[d] = proxy[h].std() * math.sqrt(252)
MOMVOLP = np.full(T, np.nan)
MOMMED = np.full(T, np.nan)
for d in range(T):
    if np.isfinite(MOMVOL[d]):
        hist = MOMVOL[:d + 1][np.isfinite(MOMVOL[:d + 1]) & ~locked[:d + 1]]
        if len(hist) >= 120:
            MOMVOLP[d] = (hist <= MOMVOL[d]).mean()
            MOMMED[d] = np.median(hist)

# FF momentum diagnostic
ff = _no_locked(pd.read_parquet(DATA / "ff_mom_daily.parquet"))
ffm = ff.set_index(pd.to_datetime(ff.date))["Mom"].reindex(dates)
msk = (dates >= "2017-01-01") & ~locked & ffm.notna().to_numpy() & (proxy != 0)
DIAG = {"proxy_vs_ff_mom_daily_corr": round(float(np.corrcoef(proxy[msk], ffm.to_numpy()[msk])[0, 1]), 3),
        "proxy_vs_ff_days": int(msk.sum())}

# ---------------------------------------------------------------------------------------------- guarded targets
WEEK_END = S["WEEK_END"]
bil = col["BIL"]


def ew_w(t):
    w = np.zeros(NS)
    ok = ELIG[t]
    w[ok] = 1.0 / ok.sum()
    return w


def bil_w(t):
    w = np.zeros(NS)
    w[bil] = 1.0
    return w


GUARDS = {
    "G1": (lambda t: not SPY200[t], ew_w),
    "G2": (lambda t: not SPY200[t], bil_w),
    "G3": (lambda t: bool(TR[t] > 1.0), ew_w),
    "G4": (lambda t: bool(VIXP[t] > 0.8), ew_w),
    "G5a": (lambda t: bool(MOMVOLP[t] > 0.7), ew_w),
    "G5b": (lambda t: bool(MOMVOLP[t] > 0.8), ew_w),
    "G5c": (lambda t: bool(MOMVOLP[t] > 0.9), ew_w),
    "G6": (lambda t: bool(BEAR[t]), ew_w),
}
BASES = {"S6M": lambda: S["stock_targets"]("mom12_1", 20, "M", filt_rev=True),
         "S1W": lambda: S["stock_targets"]("mom12_1", 50, "W")}
BASE_ID = {"S6M": "S6_mom12_1rev_N20_M", "S1W": "S1_mom12_1_N50_W"}
ON_LOG: dict[str, list] = {}


def guarded(base_tg, guard):
    cond, port = GUARDS[guard]
    days = sorted(set(base_tg) | {int(t) for t in WEEK_END if 252 <= t < T - 1})
    out, last_mom, state = {}, None, False
    on_days = []
    for t in days:
        reb = t in base_tg
        if reb:
            last_mom = base_tg[t]
        if last_mom is None:
            continue
        new = cond(t)
        if new:
            on_days.append(t)
        if new and (reb or not state):
            out[t] = port(t)
        elif not new and (reb or state):
            out[t] = last_mom
        state = new
    return out, on_days


def scaled(base_tg):
    out = {}
    for t, w in base_tg.items():
        s = 1.0
        if np.isfinite(MOMVOL[t]) and np.isfinite(MOMMED[t]) and MOMVOL[t] > 0:
            s = min(1.0, MOMMED[t] / MOMVOL[t])
        out[t] = s * w + (1 - s) * ew_w(t)
    return out


CONFIGS = []
for b, fn in BASES.items():
    tg = fn()
    for gname in GUARDS:
        cid = f"C_{b}_{gname}"
        g_tg, on = guarded(tg, gname)
        SER[cid] = S["simulate"](g_tg)
        BENCH_OF[cid] = "BENCH_EW"
        ON_LOG[cid] = on
        CONFIGS.append({"id": cid, "base": b, "guard": gname})
        print(cid, "guard-on weeks", len(on), flush=True)
    cid = f"C_{b}_G7"
    SER[cid] = S["simulate"](scaled(tg))
    BENCH_OF[cid] = "BENCH_EW"
    CONFIGS.append({"id": cid, "base": b, "guard": "G7"})
    print(cid, flush=True)
for b, pid in BASE_ID.items():
    BENCH_OF[pid] = "BENCH_EW"
assert len(CONFIGS) == 18

# ---------------------------------------------------------------------------------------------- statistics + gates
PERIODS = ["train", "valid", "valid2", "trval", "all"] + [f"Y{y}" for y in range(2017, 2027)]
rows = [stats(cid, p) for cid in [c["id"] for c in CONFIGS] + list(BASE_ID.values()) + ["BENCH_EW", "BH_SPY"]
        for p in PERIODS]
res = pd.DataFrame(rows)
R = res.set_index(["id", "period"])
N_LIN = 123
TREQ = t_required(N_LIN)

# deflated Sharpe (absolute), N = 123, cross-trial variance from the 105 longhold configs (cache, V excluded) + these 18
tv = period_mask("trval")
lh_gates = pd.read_csv(LH / "gates.csv")
pool = [k for k in lh_gates.id if k in z.files] + [c["id"] for c in CONFIGS]
srs = {}
for k in pool:
    r = (SER[k][0] if k in SER else z[k][0])[tv]
    srs[k] = r.mean() / r.std()
v = np.var(list(srs.values()), ddof=1)
gm = 0.5772156649
sr0 = math.sqrt(v) * ((1 - gm) * norm.ppf(1 - 1 / N_LIN) + gm * norm.ppf(1 - 1 / (N_LIN * math.e)))


def dsr(cid):
    r = SER[cid][0][tv]
    sr = r.mean() / r.std()
    zz = (r - r.mean()) / r.std()
    sk, ku = float((zz ** 3).mean()), float((zz ** 4).mean())
    return float(norm.cdf((sr - sr0) * math.sqrt(len(r) - 1) / math.sqrt(max(1e-12, 1 - sk * sr + (ku - 1) / 4 * sr ** 2))))


month_key = dates.year * 100 + dates.month


def monthly_active(cid):
    m = ~locked & np.asarray(dates >= "2017-01-01")
    r, b = SER[cid][0][m], SER["BENCH_EW"][0][m]
    mk = month_key[m]
    mr = pd.Series(r).groupby(mk).apply(lambda x: (1 + x).prod() - 1)
    mb = pd.Series(b).groupby(mk).apply(lambda x: (1 + x).prod() - 1)
    a = mr - mb
    return pd.DataFrame({"date": pd.to_datetime([f"{k // 100}-{k % 100:02d}-15" for k in a.index]), "r": a.to_numpy()})


NB = {"G1": ["G2"], "G2": ["G1"], "G3": ["G4"], "G4": ["G3"], "G5a": ["G5b"], "G5b": ["G5a", "G5c"], "G5c": ["G5b"],
      "G6": [], "G7": []}
other = {"S6M": "S1W", "S1W": "S6M"}
grows = []
for c in CONFIGS + [{"id": BASE_ID[b], "base": b, "guard": "PARENT"} for b in BASE_ID]:
    cid = c["id"]
    g = lambda p, k: R.loc[(cid, p), k]  # noqa: E731
    act = [g(p, "active") for p in ("train", "valid", "valid2")]
    sh = [g(p, "sharpe") for p in ("train", "valid", "valid2")]
    bsh = [g(p, "bench_sharpe") for p in ("train", "valid", "valid2")]
    if c["guard"] != "PARENT":
        nb = [f"C_{c['base']}_{x}" for x in NB[c["guard"]]] + [f"C_{other[c['base']]}_{c['guard']}"]
        nb_act = float(np.mean([R.loc[(o, "trval"), "active"] for o in nb]))
        nb_sh = float(np.mean([R.loc[(o, "trval"), "sharpe"] - R.loc[(o, "trval"), "bench_sharpe"] for o in nb]))
    else:
        nb, nb_act, nb_sh = [], np.nan, np.nan
    wf = walk_forward(monthly_active(cid), exclude_months=["2024-11", "2024-12", "2025-01", "2025-02"], min_n=1)
    A1 = all(a > 0 for a in act)
    A2 = g("trval", "active_t") >= TREQ
    A3 = bool(nb) and nb_act > 0
    A4 = g("all", "active_up_months") > 0 and g("all", "active_down_months") > 0
    WF = (wf["share_positive"] or 0) >= 0.6
    B1 = all(s > b for s, b in zip(sh, bsh))
    B2 = g("trval", "maxdd") > g("trval", "bench_maxdd")
    d = dsr(cid)
    B3 = d >= 0.95
    B4 = bool(nb) and nb_sh > 0
    if c["guard"] == "PARENT":
        verdict = "control"
    elif A1 and A2 and A3 and A4 and WF:
        verdict = "A_edge"
    elif B1 and B2 and B3 and B4:
        verdict = "B_risk"
    elif all(s > 0 for s in sh) and sum((a > 0) or (s > b) for a, s, b in zip(act, sh, bsh)) >= 2:
        verdict = "near"
    else:
        verdict = "fail"
    fails = [k for k, v_ in (("A1", A1), ("A2", A2), ("A3", A3), ("A4", A4), ("WF", WF)) if not v_]
    on = ON_LOG.get(cid, [])
    grows.append({"id": cid, "base": c["base"], "guard": c["guard"], "verdict": verdict, "t_req": TREQ,
                  "A1": A1, "A2": A2, "A3": A3, "A4": A4, "WF": WF, "B1": B1, "B2": B2, "B3": B3, "B4": B4,
                  "active_train": act[0], "active_valid": act[1], "active_valid2": act[2],
                  "active_t_trval": g("trval", "active_t"), "sharpe_train": sh[0], "sharpe_valid": sh[1],
                  "sharpe_valid2": sh[2], "bench_sharpe_trval": g("trval", "bench_sharpe"),
                  "sharpe_trval": g("trval", "sharpe"), "cagr_trval": g("trval", "cagr"),
                  "maxdd_trval": g("trval", "maxdd"), "bench_maxdd_trval": g("trval", "bench_maxdd"),
                  "maxdd_valid2": g("valid2", "maxdd"), "turnover_trval": g("trval", "turnover_yr"),
                  "active_up_months_all": g("all", "active_up_months"),
                  "active_down_months_all": g("all", "active_down_months"),
                  "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"], "dsr_abs": d,
                  "nb": ";".join(nb), "nb_active_trval": nb_act, "nb_sharpe_diff_trval": nb_sh,
                  "guard_on_checks": len(on), "guard_on_share": round(len(on) / max(1, len([t for t in WEEK_END if 252 <= t < T - 1])), 3),
                  "fails_A": ";".join(fails)})
G = pd.DataFrame(grows)
res.to_csv(HERE / "results_c.csv", index=False, float_format="%.5f")
G.to_csv(HERE / "gates_c.csv", index=False, float_format="%.4f")
# which months the momentum-vol guard was on, and FF Mom in those months (diagnostic)
ffmo = ffm.groupby(month_key).apply(lambda x: (1 + x.fillna(0)).prod() - 1)
on_m = sorted({int(month_key[t]) for t in ON_LOG.get("C_S6M_G5b", [])})
DIAG["G5b_on_months"] = on_m
DIAG["ff_mom_month_ret_when_G5b_on_mean"] = round(float(ffmo.reindex(on_m).mean()), 4) if on_m else None
DIAG["ff_mom_month_ret_when_G5b_off_mean"] = round(float(ffmo[~ffmo.index.isin(on_m) & (ffmo.index >= 201801)].mean()), 4)
DIAG["ff_mom_worst_months_2017plus"] = {int(k): round(float(v_), 4) for k, v_ in ffmo[ffmo.index >= 201701].nsmallest(6).items()}
DIAG["sr0_daily_abs"] = sr0
json.dump(DIAG, open(HERE / "diag_c.json", "w"), indent=1)
pd.set_option("display.width", 250)
print(DIAG)
print(G[["id", "verdict", "active_train", "active_valid", "active_valid2", "active_t_trval", "sharpe_trval",
         "maxdd_trval", "wf_share", "dsr_abs", "guard_on_share", "fails_A"]].round(3).to_string(index=False))
