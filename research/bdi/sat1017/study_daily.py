"""BDI sat1017: daily-bar reworks R1 (C3 hedge / RS), R2 (C7 on a wider ETF set) and new directions N1 (overnight
persistence) and N2 (high-volume premium). Pre-declared in PLAN.md. Reuses the CWT package C engine
(research/bdi/cwt/test_c/common.py): outcome prices inside the locked block 2024-11-01..2025-02-28 are NaN and trades
touching it are dropped; MCF_HIST_ALLOW_LOCKED is never set. Costs in. Educational only - not financial advice.

Run: python research/bdi/sat1017/study_daily.py -> results_daily.csv (long), gates_daily.csv
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
TC = HERE.parents[1] / "bdi" / "cwt" / "test_c"
sys.path.insert(0, str(TC))
import common as cm  # noqa: E402
import families as fam  # noqa: E402
from common import (C, Cn, Cx, ELIG, Ox, SPY, T, V, book, col, dates, locked, score)  # noqa: E402

assert locked.sum() > 0 and np.isnan(Cx[locked]).all(), "locked block must be NaN in outcomes"


def t_req(n):
    return max(1.5, math.sqrt(2 * math.log(n)))


LINEAGE = {"R1": 31, "R2": 22, "N1": 8, "N2": 8}
GRID: dict[str, dict] = {}

# ------------------------------------------------------------------------------------------------ beta (signal-time)
lr = np.log(C / C.shift(1))
m = lr["SPY"]
var_m = m.rolling(252, min_periods=200).var()
cov = lr.rolling(252, min_periods=200).cov(pd.DataFrame({s: m for s in C.columns}), pairwise=False)
BETA = cov.div(var_m, axis=0).to_numpy()
del cov


def hedge(t):
    """Beta x SPY short over the same entry/exit prints; the leg pays its own costs and 3 %/yr borrow."""
    t = t.copy()
    b = np.clip(np.nan_to_num(BETA[t.i.to_numpy(), t.j.to_numpy()], nan=1.0), 0, 3)
    ei, xi = t.ei.to_numpy(), t.xi.to_numpy()
    se = np.where(t.ek.to_numpy() == "C", Cx[ei, SPY], Ox[ei, SPY])
    sx = np.where(t.xk.to_numpy() == "O", Ox[xi, SPY], Cx[xi, SPY])
    days = np.maximum((dates[xi] - dates[ei]).days.to_numpy(), 1)
    leg = sx / se - 1
    t["gross"] = t.gross - b * leg
    t["net"] = t.net - b * leg - b * (cm.cost(se) + cm.cost(sx)) - b * cm.BORROW * days / 365
    t["beta"] = b
    return t


def reg(cid, famname, params):
    GRID[cid] = {"family": famname, **params}


# ================================================================================================ R1 C3 rework
RET63 = (C / C.shift(63) - 1).to_numpy()
RS = np.nan_to_num(RET63 > RET63[:, [SPY]], nan=0).astype(bool)
for k in (20, 50):
    for entry in ("close", "stop"):
        for ex in ("2nd_sma20", "k10"):
            p = {"k": k, "entry": entry, "exit": ex}
            base = fam.c3(k, entry, ex)
            cid = f"R1A_hedge_sma{k}_{entry}_{ex}"
            reg(cid, "R1", {**p, "var": "hedge"})
            score(cid, "R1", 1, f"C3 pullback SMA{k} {entry} {ex}, beta-hedged with SPY", hedge(base), p)
            fam.ELIGB = ELIG & RS
            rs = fam.c3(k, entry, ex)
            fam.ELIGB = ELIG.copy()
            cid = f"R1B_rs63_sma{k}_{entry}_{ex}"
            reg(cid, "R1", {**p, "var": "rs63"})
            score(cid, "R1", 1, f"C3 pullback SMA{k} {entry} {ex} + 63d return > SPY", rs, p)
print("R1 done", flush=True)

# ================================================================================================ R2 C7 on more ETFs
U_EQ = ["DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "SMH", "SOXX", "XBI",
        "IBB", "KRE", "KBE", "XHB", "ITB", "XRT", "XME", "XOP", "OIH", "IYR", "VNQ", "EFA", "EEM"]
U_ALL = U_EQ + ["SPY", "QQQ", "IWM"]


def c7(names, Nd, cap):
    sigs = []
    for s in names:
        j = col[s]
        c = Cn[:, j]
        st = np.zeros(T, int)
        for t in range(1, T):
            st[t] = st[t - 1] + 1 if (np.isfinite(c[t]) and np.isfinite(c[t - 1]) and c[t] < c[t - 1]) else 0
        sigs += [(i, j) for i in np.flatnonzero(st == Nd)]

    def make(i, j):
        if locked[i] or not np.isfinite(Cx[i, j]):
            return None
        ep = Cx[i, j]
        r = cm.walk(j, i, ep, 1, "C", None, None, lambda d: Cx[d, j] > Cx[d - 1, j], i + cap)
        if r is None:
            return None
        return {"i": i, "j": j, "ei": i, "ep": ep, "ek": "C", "xi": r[0], "xp": r[1], "xk": r[2]}
    return book(sigs, 1, make)


for uni, names in (("eq", U_EQ), ("all", U_ALL)):
    for Nd in (2, 3, 4):
        for cap in (20, 5):
            cid = f"R2_{uni}_streak{Nd}_cap{cap}"
            p = {"uni": uni, "Nd": Nd, "cap": cap}
            reg(cid, "R2", p)
            score(cid, "R2", 1, f"{uni} ETFs: buy close of {Nd}th down close, sell first up close (cap {cap})",
                  c7(names, Nd, cap), p, stock=False, keep=(uni == "eq" and Nd == 3 and cap == 20))
print("R2 done", flush=True)

# ================================================================================================ N1 overnight persistence
On = cm.On
prevC = np.vstack([np.full(Cn.shape[1], np.nan), Cn[:-1]])
with np.errstate(invalid="ignore", divide="ignore"):
    ON = pd.DataFrame(np.log(On / prevC), index=dates)
    ID = pd.DataFrame(np.log(Cn / On), index=dates)
dser = pd.Series(np.arange(T), index=dates)
iso = dates.isocalendar()
WEEK_END = dser.groupby([iso.year.values, iso.week.values]).max().to_numpy()


def entry_moo_hold(H):
    def make(i, j):
        ei = i + 1
        if ei >= T or locked[ei]:
            return None
        ep = Ox[ei, j]
        if not np.isfinite(ep):
            return None
        r = cm.walk(j, ei, ep, 1, "O", None, None, None, i + H)
        if r is None:
            return None
        return {"i": i, "j": j, "ei": ei, "ep": ep, "ek": "O", "xi": r[0], "xp": r[1], "xk": r[2]}
    return make


for L in (20, 60):
    son = ON.rolling(L, min_periods=int(0.8 * L)).sum().to_numpy()
    sid = ID.rolling(L, min_periods=int(0.8 * L)).sum().to_numpy()
    for feat, F in (("ON", son), ("ONID", son - sid)):
        sig = np.zeros_like(ELIG)
        for i in WEEK_END:
            ok = ELIG[i] & np.isfinite(F[i])
            if ok.sum() < 50:
                continue
            thr = np.quantile(F[i, ok], 0.9)
            sig[i] = ok & (F[i] >= thr)
        for H in (5, 20):
            cid = f"N1_{feat}_L{L}_H{H}"
            p = {"feat": feat, "L": L, "H": H}
            reg(cid, "N1", p)
            score(cid, "N1", 1, f"weekly top decile of {feat} over {L}d, MOO, hold to close t+{H}",
                  book(sig, 1, entry_moo_hold(H)), p)
print("N1 done", flush=True)

# ================================================================================================ N2 high-volume premium
Vn = V.to_numpy(float)
MEDV = V.shift(1).rolling(20, min_periods=15).median().to_numpy()
with np.errstate(invalid="ignore", divide="ignore"):
    VR = Vn / MEDV
    R1D = np.abs(Cn / prevC - 1)
for k in (2, 3):
    for a in (0.01, 0.02):
        sig = ELIG & np.nan_to_num(VR >= k).astype(bool) & np.nan_to_num(R1D <= a).astype(bool)
        for H in (5, 20):
            cid = f"N2_vr{k}_abs{int(a*100)}_H{H}"
            p = {"k": k, "a": a, "H": H}
            reg(cid, "N2", p)
            score(cid, "N2", 1, f"volume >= {k}x 20d median, |ret| <= {a:.0%}, MOO, hold to close t+{H}",
                  book(sig, 1, entry_moo_hold(H)), p)
print("N2 done", flush=True)

res = pd.DataFrame(cm.RESULTS)
res.to_csv(HERE / "results_daily.csv", index=False)
cm.save_trades(HERE / "trades_r2_eq3.parquet")

# ================================================================================================ gates (PLAN.md section 2)
P = res.set_index(["id", "split"])


def g(cid, split, k):
    try:
        v = P.loc[(cid, split), k]
        return float(v) if pd.notna(v) else np.nan
    except KeyError:
        return np.nan


STEPS = {"R1": {"k": [20, 50], "entry": ["close", "stop"], "exit": ["2nd_sma20", "k10"]},
         "R2": {"Nd": [2, 3, 4], "cap": [5, 20]},
         "N1": {"L": [20, 60], "H": [5, 20]}, "N2": {"k": [2, 3], "a": [0.01, 0.02], "H": [5, 20]}}
rows = []
for cid, p in GRID.items():
    f = p["family"]
    etf = f == "R2"
    nmin, nreg, v1t = (20, 15, 1.0) if etf else (100, 30, 1.5)
    ex = [g(cid, s, "exp_bps") for s in ("train", "valid1", "valid2")]
    ns = [g(cid, s, "n") for s in ("train", "valid1", "valid2")]
    G1 = all(np.isfinite(e) and e > 0 for e in ex) and all(n >= nmin for n in ns)
    ttv = g(cid, "trainvalid1", "t")
    G2 = np.isfinite(ttv) and ttv >= t_req(LINEAGE[f])
    G3 = np.isfinite(g(cid, "valid1", "t")) and g(cid, "valid1", "t") >= v1t
    exc = [g(cid, s, "excess_bps") for s in ("train", "valid1", "valid2")]
    G4 = True if etf else all(np.isfinite(e) and e > 0 for e in exc)
    up, dn = g(cid, "month_up", "exp_bps"), g(cid, "month_down", "exp_bps")
    G5 = up > 0 and dn > 0 and g(cid, "month_up", "n") >= nreg and g(cid, "month_down", "n") >= nreg
    nb = []
    for o, q in GRID.items():
        if o == cid or q["family"] != f:
            continue
        keys = [k for k in p if k != "family" and p[k] != q.get(k)]
        if len(keys) == 1 and keys[0] in STEPS[f]:
            vals = STEPS[f][keys[0]]
            if abs(vals.index(p[keys[0]]) - vals.index(q[keys[0]])) == 1:
                nb.append(o)
    nb_exp = float(np.nanmean([g(o, "trainvalid1", "exp_bps") for o in nb])) if nb else np.nan
    G6 = (not nb) or nb_exp > 0
    wf = g(cid, "all_open", "wf_share")
    G7 = np.isfinite(wf) and wf >= 0.6
    allg = [G1, G2, G3, G4, G5, G6, G7]
    verdict = "candidate" if all(allg) else ("near" if all(np.isfinite(e) and e > 0 for e in ex) else "fail")
    rows.append({"id": cid, "family": f, "verdict": verdict, **{f"G{n+1}": bool(x) for n, x in enumerate(allg)},
                 "exp_train": ex[0], "exp_valid1": ex[1], "exp_valid2": ex[2], "n_train": ns[0], "n_valid1": ns[1],
                 "n_valid2": ns[2], "t_trval": ttv, "t_bar": round(t_req(LINEAGE[f]), 2), "t_valid1": g(cid, "valid1", "t"),
                 "exc_train": exc[0], "exc_valid1": exc[1], "exc_valid2": exc[2], "up_m": up, "down_m": dn,
                 "nb_exp": nb_exp, "wf": wf, "ex_best": g(cid, "all_open", "ex_best_bps"),
                 "busiest": g(cid, "all_open", "busiest_share"), "sessions": g(cid, "all_open", "sessions"),
                 "y2022": g(cid, "y2022", "exp_bps"), "y2018": g(cid, "y2018", "exp_bps")})
gates = pd.DataFrame(rows)
gates.to_csv(HERE / "gates_daily.csv", index=False, float_format="%.3f")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(gates.drop(columns=["G1", "G2", "G3", "G4", "G5", "G6", "G7"]).round(2).to_string())
print(gates[["id"] + [f"G{n}" for n in range(1, 8)]].to_string())
print(gates.groupby(["family", "verdict"]).size())
