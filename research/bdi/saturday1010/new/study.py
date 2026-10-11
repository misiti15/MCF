"""Saturday 2026-10-10 new-ideas scan: scores the pre-declared grid in NOTES.md section 1 (124 configurations,
+ controls/benchmarks/diagnostics that are not counted). Single process; ~1 GB RAM.

    python research/bdi/saturday1010/new/study.py            # grid + gates + diagnostics -> results.csv, gates.csv, diag.csv

Educational only - not financial advice.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib as L  # noqa: E402

HERE = L.HERE
N_TOTAL = 124
T_REQ = math.sqrt(2 * math.log(N_TOTAL))
T, NS, dates = L.T, L.NS, L.dates
SPY = L.col["SPY"]

# ---------------------------------------------------------------------------------------------- benchmarks
SER: dict[str, tuple] = {}
SER["BENCH_EW"] = L.simulate(L.ew_universe_targets())
SER["BH_SPY"] = L.simulate(L.bh_targets(["SPY"]))
ew_r = SER["BENCH_EW"][0]
spy_r = SER["BH_SPY"][0]
print("benchmarks done", flush=True)

# ---------------------------------------------------------------------------------------------- family P: events
ec = pd.read_parquet(L.DATA / "earnings_cal.parquet", columns=["date", "symbol"])
ec["date"] = pd.to_datetime(ec["date"])
ec = ec[ec.symbol.isin(L.col)]
ec["d"] = np.searchsorted(dates.values, ec["date"].values)
ec = ec[(ec.d >= 70) & (ec.d + 1 <= T - 2)].copy()
ec["j"] = ec.symbol.map(L.col)
ec = ec.sort_values(["j", "d"])
gap = ec.groupby("j").d.diff()
ec = ec[~(gap < 10)]                                       # same symbol within 10 sessions: keep the first
d = ec.d.to_numpy(); j = ec.j.to_numpy(); s = d + 1
Cn, On, Vn = L.Cn, L.On, L.Vn
ok = ~np.isnan(Cn[d - 1, j]) & ~np.isnan(Cn[d + 1, j]) & L.ELIG[d - 1, j] & ~L.locked[s] & ~L.locked[d - 1]
d, j, s = d[ok], j[ok], s[ok]
r2 = Cn[d + 1, j] / Cn[d - 1, j] - 1
r2m = Cn[d + 1, SPY] / Cn[d - 1, SPY] - 1
RAW = r2 - r2m
dr = pd.DataFrame(L.Cn).pct_change(fill_method=None).to_numpy()
ex = dr - dr[:, [SPY]]
exsd = pd.DataFrame(ex).rolling(60, min_periods=40).std().to_numpy()
del ex, dr
Z = RAW / (exsd[d - 2, j] * math.sqrt(2))
vmed = pd.DataFrame(Vn).rolling(20, min_periods=15).median().to_numpy()
VR = np.maximum(Vn[d, j], Vn[d + 1, j]) / vmed[d - 2, j]
del vmed, exsd
oc = Cn / On - 1
OCs = (oc[d, j] - oc[d, SPY]) + (oc[d + 1, j] - oc[d + 1, SPY])
del oc
SCORES = {"RAW": RAW, "Z": Z, "ZV": np.where(VR >= 2, Z, np.nan), "OC": OCs}
print("events", len(d), "first signal", dates[s.min()].date(), "last", dates[s.max()].date(), flush=True)


def percentiles(score):
    """percentile of each event's score among scored events with signal rows in [s-252, s-1] (min 500)."""
    m = ~np.isnan(score)
    o = np.argsort(s[m], kind="stable")
    ss, sc = s[m][o], score[m][o]
    out = np.full(len(score), np.nan)
    idx = np.flatnonzero(m)[o]
    for k in range(len(ss)):
        a = np.searchsorted(ss, ss[k] - 252, "left"); b = np.searchsorted(ss, ss[k], "left")
        if b - a >= 500:
            out[idx[k]] = (sc[a:b] < sc[k]).mean()
    return out


PCT = {k: percentiles(v) for k, v in SCORES.items()}


def p_entries(score, side, q, top300=None, delay=0):
    pc = PCT[score]; sc = SCORES[score]
    sel = (pc >= 1 - q) if side == "top" else (pc < q)
    sel &= ~np.isnan(pc)
    if top300 is not None:
        sel &= top300[d - 1, j]
    out: dict[int, list] = {}
    for k in np.flatnonzero(sel):
        out.setdefault(int(s[k]) + delay, []).append((int(j[k]), float(sc[k] if side == "top" else -sc[k])))
    return out


def control_entries():
    rng = np.random.default_rng(20261010)
    rs = rng.random(len(d))
    out: dict[int, list] = {}
    for k in range(len(d)):
        if s[k] >= L.START_ROW and not np.isnan(PCT["RAW"][k]):    # same event window as the RAW books
            out.setdefault(int(s[k]), []).append((int(j[k]), float(rs[k])))
    return out


def run_slots(entries, H, K, cost_mult=1.0):
    r, to, c, expo = L.simulate_slots(entries, H, K, cost_mult)
    b = np.r_[0.0, expo[:-1]] * ew_r
    return (r, to, c), b, expo


# ---------------------------------------------------------------------------------------------- family V: features
fr = []
for y in range(2019, 2027):
    f = pd.read_parquet(L.DATA / f"finra_shvol_{y}.parquet", columns=["date", "symbol", "shortvolume", "totalvolume"])
    f = f[f.symbol.isin(L.col) & (f.totalvolume > 0)]
    fr.append(f)
f = pd.concat(fr, ignore_index=True)
del fr
f["date"] = pd.to_datetime(f["date"])
assert not ((f.date >= L.LOCK_A) & (f.date <= L.LOCK_B)).any()
f["svr"] = (f.shortvolume / f.totalvolume).astype("float32")
SVR = f.pivot_table(index="date", columns="symbol", values="svr", aggfunc="last").reindex(index=dates, columns=L.syms)
print("finra rows", len(f), "symbols", f.symbol.nunique(), flush=True)
del f
L5 = SVR.rolling(5, min_periods=4).mean()
L20 = SVR.rolling(20, min_periods=15).mean()
FEATV = {
    "L5": L5.to_numpy(), "L20": L20.to_numpy(),
    "D5": (L5 - SVR.shift(5).rolling(60, min_periods=40).mean()).to_numpy(),
    "D20": (L20 - SVR.shift(20).rolling(60, min_periods=40).mean()).to_numpy(),
}
del L5, L20, SVR


def lag1(a):
    return np.vstack([np.full((1, a.shape[1]), np.nan), a[:-1]])


def quint_targets(F, reb, elig=None, delay=0):
    out = {}
    for t in L.REB[reb]:
        if t < L.START_ROW or t >= T - 1 - delay:
            continue
        okk = L.ELIG[t] & ~np.isnan(F[t])
        if elig is not None:
            okk &= elig[t]
        if okk.sum() < 100:
            continue
        cut = np.nanquantile(F[t, okk], 0.2)
        w = np.zeros(NS)
        sel = okk & (F[t] <= cut)
        w[sel] = 1.0 / sel.sum()
        out[t + delay] = w
    return out


def s6_filter_mask(F, q):
    m = np.ones((T, NS), bool)
    for t in np.unique(np.r_[L.WEEK_END, L.MONTH_END]):
        el = L.ELIG[t]
        have = el & ~np.isnan(F[t])
        if have.sum() < 0.5 * el.sum() or have.sum() < 50:
            continue
        cut = np.nanquantile(F[t, have], 1 - q)
        m[t] = ~(have & (F[t] >= cut))
    return m


def shift(tg, k=1):
    return {t + k: w for t, w in tg.items() if t + k < T - 1}


# ---------------------------------------------------------------------------------------------- grid
CONFIGS: list[dict] = []


def add(cid, fam, kind, params, bench):
    CONFIGS.append({"id": cid, "family": fam, "kind": kind, "params": params, "bench": bench})


for sc in ("RAW", "Z", "ZV", "OC"):
    for q in (10, 20):
        for H in (20, 40, 60):
            for K in (20, 50):
                add(f"P_{sc}_top{q}_H{H}_K{K}", "P", "cand", {"score": sc, "q": q, "H": H, "K": K}, "EXPO_EW")
for sc in ("RAW", "Z", "ZV", "OC"):
    for H in (20, 40, 60):
        add(f"P_{sc}_bot10_H{H}_K50", "P", "diag", {"score": sc, "q": 10, "H": H, "K": 50, "side": "bot"}, "EXPO_EW")
for ft in FEATV:
    for n in (20, 50):
        for reb in ("W", "M"):
            add(f"V1_{ft}_low_N{n}_{reb}", "V1", "cand", {"feat": ft, "N": n, "reb": reb}, "BENCH_EW")
for ft in FEATV:
    for reb in ("W", "M"):
        add(f"V1_{ft}_lowQ5_{reb}", "V1q", "cand", {"feat": ft, "reb": reb}, "BENCH_EW")
for ft in FEATV:
    for reb in ("W", "M"):
        add(f"V1_{ft}_high_N50_{reb}", "V1h", "diag", {"feat": ft, "reb": reb}, "BENCH_EW")
for ft in FEATV:
    for q in (10, 20, 30):
        for reb in ("W", "M"):
            add(f"V2_S6_N20_{reb}_drop{ft}_q{q}", "V2", "cand", {"feat": ft, "q": q, "reb": reb, "N": 20}, f"S6_N20_{reb}")
for ft in FEATV:
    for n in (10, 50):
        add(f"V2_S6_N{n}_W_drop{ft}_q20", "V2", "cand", {"feat": ft, "q": 20, "reb": "W", "N": n}, f"S6_N{n}_W")
assert len(CONFIGS) == N_TOTAL, len(CONFIGS)

# ---------------------------------------------------------------------------------------------- run
BENCH: dict[str, np.ndarray] = {}
EXPO: dict[str, np.ndarray] = {}
NTRADE: dict[str, int] = {}
for n, reb in [(20, "W"), (20, "M"), (10, "W"), (50, "W")]:
    SER[f"S6_N{n}_{reb}"] = L.simulate(L.stock_targets(L.MOM12_1, n, reb, filt_rev=True))
for H in (20, 40, 60):
    for K in (20, 50):
        cid = f"CTRL_P_ALL_H{H}_K{K}"
        SER[cid], BENCH[cid], EXPO[cid] = run_slots(control_entries(), H, K)
FMASK: dict[tuple, np.ndarray] = {}


def build(c, cost_mult=1.0, delay=0, top300=None, lagv=False):
    p = c["params"]
    if c["family"] == "P":
        e = p_entries(p["score"], p.get("side", "top"), p["q"] / 100, top300=top300, delay=delay)
        return run_slots(e, p["H"], p["K"], cost_mult)
    F = FEATV[p["feat"]]
    if lagv:
        F = lag1(F)
    if c["family"] == "V1":
        tg = L.stock_targets(F, p["N"], p["reb"], elig=top300, lowest=True)
    elif c["family"] == "V1q":
        tg = quint_targets(F, p["reb"], elig=top300)
    elif c["family"] == "V1h":
        tg = L.stock_targets(F, 50, p["reb"], elig=top300)
    else:
        key = (p["feat"], p["q"], lagv)
        if key not in FMASK:
            FMASK[key] = s6_filter_mask(F, p["q"] / 100)
        tg = L.stock_targets(L.MOM12_1, p["N"], p["reb"], filt_rev=True, elig=FMASK[key])
    if delay:
        tg = shift(tg, delay)
    return L.simulate(tg, cost_mult), None, None


for i, c in enumerate(CONFIGS):
    ser, b, ex = build(c)
    SER[c["id"]] = ser
    if b is not None:
        BENCH[c["id"]], EXPO[c["id"]] = b, ex
    if i % 10 == 0:
        print(i, c["id"], flush=True)
FMASK.clear()

# trades (P entries) for reporting
for cid, ser in SER.items():
    NTRADE[cid] = int((ser[1] > 0).sum())


def bench_of(cid, c=None):
    if cid in BENCH:
        return BENCH[cid]
    if c is not None and c["bench"] in SER:
        return SER[c["bench"]][0]
    return ew_r


# ---------------------------------------------------------------------------------------------- statistics
spy_month = pd.Series(spy_r).groupby(L.month_key).apply(lambda x: (1 + x).prod() - 1)
PERIODS = ["train", "valid", "valid2", "all"] + [f"Y{y}" for y in range(2019, 2027)]


def stats(cid, period, ser=None, b=None, expo=None):
    r, to, c = ser if ser is not None else SER[cid]
    msk = L.period_mask(period)
    rr, bb = r[msk], b[msk]
    yrs = len(rr) / 252
    mr, mb = L.monthly(r, msk), L.monthly(b, msk)
    act = mr - mb
    sd = rr.std()
    sm = spy_month.reindex(act.index)
    best = act.idxmax() if len(act) else None
    out = {
        "id": cid, "period": period, "days": int(msk.sum()), "months": len(mr),
        "cagr": float(np.prod(1 + rr) ** (1 / yrs) - 1) if yrs > 0 else np.nan,
        "vol": float(sd * math.sqrt(252)), "sharpe": float(rr.mean() / sd * math.sqrt(252)) if sd > 0 else np.nan,
        "maxdd": L.mdd(rr), "turnover_yr": float(to[msk].sum() / yrs), "cost_drag_yr": float(c[msk].sum() / yrs),
        "active": float((rr.mean() - bb.mean()) * 252),
        "active_t": L.t_stat(act), "active_t_ex_best": L.t_stat(act.drop(best)) if best is not None else np.nan,
        "hit_vs_bench": float((act > 0).mean()), "wf_share": float((act.iloc[3:] > 0).mean()) if len(act) > 3 else np.nan,
        "active_up_months": float(act[sm > 0].mean() * 12), "active_down_months": float(act[sm <= 0].mean() * 12),
        "excess_ew": float((rr.mean() - ew_r[msk].mean()) * 252), "excess_spy": float((rr.mean() - spy_r[msk].mean()) * 252),
        "ret": float(np.prod(1 + rr) - 1), "bench_ret": float(np.prod(1 + bb) - 1),
        "entry_days": int((to[msk] > 0).sum()),
    }
    if expo is not None:
        out["exposure"] = float(expo[msk].mean())
    return out


rows = []
for c in CONFIGS:
    for p in PERIODS:
        rows.append(stats(c["id"], p, b=bench_of(c["id"], c), expo=EXPO.get(c["id"])) | {"family": c["family"], "kind": c["kind"]})
for cid in [k for k in SER if k.startswith(("CTRL", "S6_", "BENCH", "BH"))]:
    for p in PERIODS:
        rows.append(stats(cid, p, b=BENCH.get(cid, ew_r), expo=EXPO.get(cid)) | {"family": "control/benchmark", "kind": "ref"})
res = pd.DataFrame(rows)
R = res.set_index(["id", "period"])

# ---------------------------------------------------------------------------------------------- gates
NB_FEAT = {("RAW", "Z"), ("Z", "ZV"), ("RAW", "OC"), ("L5", "L20"), ("D5", "D20"), ("L5", "D5"), ("L20", "D20")}
STEPS = {"q": [10, 20, 30], "H": [20, 40, 60], "K": [20, 50], "N": [10, 20, 50], "reb": ["W", "M"]}


def neighbours(c):
    out = []
    for o in CONFIGS:
        if o["family"] != c["family"] or o["id"] == c["id"] or o["kind"] != c["kind"]:
            continue
        diff = [k for k in set(c["params"]) | set(o["params"]) if c["params"].get(k) != o["params"].get(k)]
        if len(diff) != 1:
            continue
        k = diff[0]; a, b = c["params"][k], o["params"][k]
        if k in ("score", "feat"):
            okk = (a, b) in NB_FEAT or (b, a) in NB_FEAT
        else:
            okk = abs(STEPS[k].index(a) - STEPS[k].index(b)) == 1
        if okk:
            out.append(o["id"])
    return out


g_rows = []
for c in CONFIGS:
    cid = c["id"]
    g = lambda p, k: R.loc[(cid, p), k]  # noqa: E731
    act = [g(p, "active") for p in L.SPLITS]
    nb = neighbours(c)
    nb_act = float(np.mean([R.loc[(o, "all"), "active"] for o in nb])) if nb else np.nan
    G1 = all(a > 0 for a in act)
    if c["family"] == "V2":
        G1 = G1 and all(g(p, "excess_ew") > 0 for p in L.SPLITS)
    G2 = g("all", "active_t") >= T_REQ
    G3 = g("all", "wf_share") >= 0.6
    G4 = g("all", "active_up_months") > 0 and g("all", "active_down_months") > 0
    G5 = (not nb) or nb_act > 0
    if c["kind"] == "diag":
        verdict = "diagnostic"
    elif G1 and G2 and G3 and G4 and G5:
        verdict = "A_edge"
    elif g("all", "active") > 0 and sum(a > 0 for a in act) >= 2:
        verdict = "near"
    else:
        verdict = "fail"
    g_rows.append({"id": cid, "family": c["family"], "kind": c["kind"], "bench": c["bench"], "verdict": verdict,
                   "G1": G1, "G2": G2, "G3": G3, "G4": G4, "G5": G5,
                   "active_train": act[0], "active_valid": act[1], "active_valid2": act[2], "active_all": g("all", "active"),
                   "active_t_all": g("all", "active_t"), "active_t_ex_best": g("all", "active_t_ex_best"),
                   "wf_share": g("all", "wf_share"), "act_up": g("all", "active_up_months"),
                   "act_down": g("all", "active_down_months"), "excess_ew_all": g("all", "excess_ew"),
                   "cagr_all": g("all", "cagr"), "sharpe_all": g("all", "sharpe"), "maxdd_all": g("all", "maxdd"),
                   "turnover_all": g("all", "turnover_yr"), "cost_drag_all": g("all", "cost_drag_yr"),
                   "exposure_all": g("all", "exposure") if "exposure" in R.columns else np.nan,
                   "nb_active_all": nb_act, "neighbours": ";".join(nb)})
gates = pd.DataFrame(g_rows)
gates.to_csv(HERE / "gates.csv", index=False, float_format="%.4f")
res["verdict"] = res["id"].map(gates.set_index("id")["verdict"]).fillna("control/benchmark")
res.to_csv(HERE / "results.csv", index=False, float_format="%.5f")
print("T_REQ", T_REQ)
print(gates.groupby(["family", "verdict"]).size().unstack(fill_value=0))

# ---------------------------------------------------------------------------------------------- diagnostics (1.8)
adv = np.where(L.ELIG, L.adv20, -np.inf)
TOP300 = L.ELIG & ((-adv).argsort(axis=1).argsort(axis=1) < 300)
del adv
picks = list(gates.loc[gates.verdict == "A_edge", "id"])
for fam in ("P", "V1", "V1q", "V2"):
    sub = gates[(gates.family == fam) & (gates.verdict != "A_edge") & (gates.kind == "cand")]
    if len(sub):
        picks.append(sub.sort_values("active_t_all", ascending=False).iloc[0]["id"])
drows = []
byid = {c["id"]: c for c in CONFIGS}
for cid in picks:
    c = byid[cid]
    variants = {"cost2x": dict(cost_mult=2.0), "delay1": dict(delay=1)}
    if c["family"] in ("P", "V1", "V1q"):
        variants["top300"] = dict(top300=TOP300)
    if c["family"] != "P":
        variants["lag1"] = dict(lagv=True)
    for vname, kw in variants.items():
        ser, b, ex = build(c, **kw)
        if b is None:
            b = SER[c["bench"]][0] if c["bench"] in SER else ew_r
        for p in ("train", "valid", "valid2", "all"):
            drows.append(stats(f"{cid}__{vname}", p, ser=ser, b=b, expo=ex) | {"base": cid, "variant": vname})
pd.DataFrame(drows).to_csv(HERE / "diag.csv", index=False, float_format="%.5f")
print("diagnostics for", picks)
