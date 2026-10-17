"""BDI sat1017 rework R3: longhold S2 residual momentum with a 756-session beta / residual-sd window (PLAN.md section 5).

Mechanics copied from research/longhold/study.py (MOO execution at t+1, drift between rebalances, 1c + 1 bps per side,
locked block 2024-11-01..2025-02-28 returns zeroed before simulation and its days dropped from every statistic).
A 252-session parity run must reproduce longhold's S2 active returns (not counted). Educational only - not financial
advice.

Run: python research/bdi/sat1017/study_resmom.py -> gates_resmom.csv
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
W3 = ROOT / "research" / "swarm1010" / "w3_daily"
LH = ROOT / "research" / "longhold"
LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
import os
TRAIN_START = os.environ.get("R3_TRAIN_START", "2017-01-01")
SPLITS = {"train": (TRAIN_START, "2020-12-31"), "valid": ("2021-01-01", "2024-10-31"),
          "valid2": ("2025-03-01", "2026-12-31")}
N_LINEAGE = 135
T_REQ = math.sqrt(2 * math.log(N_LINEAGE))

raw = pd.read_parquet(W3 / "data" / "daily_2016.parquet", columns=["symbol", "date", "open", "close", "volume"])
raw["symbol"] = raw["symbol"].astype(str)
extra = pd.read_parquet(LH / "data" / "etf_extra.parquet", columns=["symbol", "date", "open", "close", "volume"])
raw = pd.concat([raw, extra[~extra.symbol.isin(raw.symbol.unique())]], ignore_index=True)
meta = pd.read_csv(W3 / "assets_meta.csv")
etf = set(meta.loc[meta.is_etf, "symbol"]) | set(extra.symbol.unique())
C = raw.pivot(index="date", columns="symbol", values="close").sort_index()
O = raw.pivot(index="date", columns="symbol", values="open").sort_index()
V = raw.pivot(index="date", columns="symbol", values="volume").sort_index()
del raw
dates = C.index
syms = np.array(C.columns.astype(str))
T, NS = C.shape
locked = np.asarray((dates >= LOCK_A) & (dates <= LOCK_B))
Cn, On = C.to_numpy(), O.to_numpy()
prevC = np.vstack([np.full(NS, np.nan), Cn[:-1]])
R_cc = np.nan_to_num(Cn / prevC - 1); R_co = np.nan_to_num(On / prevC - 1); R_oc = np.nan_to_num(Cn / On - 1)
for R in (R_cc, R_co, R_oc):
    R[locked] = 0.0
COST_O = 0.01 / On + 0.0001
is_etf = np.array([s in etf for s in syms])
adv20 = (C * V).rolling(20, min_periods=15).median().to_numpy()
nbars = C.notna().cumsum().to_numpy()
ELIG = (Cn >= 5) & (adv20 >= 20e6) & (nbars >= 253) & ~is_etf[None, :]
lr = np.log(C / C.shift(1))
m = lr["SPY"]
dser = pd.Series(np.arange(T), index=dates)
MONTH_END = dser.groupby([dates.year, dates.month]).max().to_numpy()
iso = dates.isocalendar()
WEEK_END = dser.groupby([iso.year.values, iso.week.values]).max().to_numpy()
REB = {"M": MONTH_END, "W": WEEK_END}


def resmom_feats(win, minp):
    var_m = m.rolling(win, min_periods=minp).var()
    cov = lr.rolling(win, min_periods=minp).cov(pd.DataFrame({s: m for s in C.columns}), pairwise=False)
    var_r = lr.rolling(win, min_periods=minp).var()
    beta = cov.div(var_m, axis=0)
    rsd = np.sqrt((var_r - beta.pow(2).mul(var_m, axis=0)).clip(lower=1e-10))
    out = {}
    for name, n in (("res12_1", 252), ("res6_1", 126)):
        w = n - 21
        sr = lr.rolling(w, min_periods=int(w * 0.8)).sum().shift(21)
        sm = m.rolling(w, min_periods=int(w * 0.8)).sum().shift(21)
        out[name] = ((sr - beta.mul(sm, axis=0)) / rsd).to_numpy()
    return out


def simulate(targets):
    h = np.zeros(NS); cash = 1.0; E_prev = 1.0
    out_r = np.zeros(T); started = False
    for d in range(1, T):
        w = targets.get(d - 1)
        if w is not None:
            started = True
            h *= 1 + R_co[d]
            E = cash + h.sum()
            tgt = w * E
            co = COST_O[d]
            bad = np.isnan(co)
            if bad.any():
                tgt = np.where(bad, h, tgt)
            trade = tgt - h
            cash -= trade.sum() + np.nansum(np.abs(trade) * co)
            h = tgt * (1 + R_oc[d])
        elif started:
            h *= 1 + R_cc[d]
        if started:
            E = cash + h.sum()
            out_r[d] = E / E_prev - 1
            E_prev = E
    return out_r


def stock_targets(F, n, reb):
    out = {}
    for t in REB[reb]:
        if t < 252 or t >= T - 1:
            continue
        ok = ELIG[t] & ~np.isnan(F[t])
        idx = np.flatnonzero(ok)
        if len(idx) < 2 * n:
            continue
        order = idx[np.argsort(-F[t, idx], kind="stable")]
        w = np.zeros(NS); w[order[:n]] = 1.0 / n
        out[t] = w
    return out


def ew_targets():
    out = {}
    for t in MONTH_END:
        if t < 252 or t >= T - 1:
            continue
        ok = ELIG[t]; w = np.zeros(NS); w[ok] = 1.0 / ok.sum(); out[t] = w
    return out


EW = simulate(ew_targets())
SPYR = R_cc[:, list(syms).index("SPY")]
month_key = dates.year * 100 + dates.month


def pmask(name):
    if name in SPLITS:
        a, b = SPLITS[name]; msk = (dates >= a) & (dates <= b)
    elif name == "trval":
        msk = (dates >= SPLITS["train"][0]) & (dates <= SPLITS["valid"][1])
    else:
        msk = dates >= SPLITS["train"][0]
    return np.asarray(msk) & ~locked


def mprod(x, k):
    return pd.Series(x).groupby(k).apply(lambda s: (1 + s).prod() - 1)


def stats(r, period):
    msk = pmask(period)
    rr, bb, mk = r[msk], EW[msk], month_key[msk]
    act = mprod(rr, mk) - mprod(bb, mk)
    sm = mprod(SPYR[msk], mk)
    return {"active": float((rr.mean() - bb.mean()) * 252),
            "active_t": float(act.mean() / act.std() * math.sqrt(len(act))),
            "up": float(act[sm > 0].mean() * 12), "down": float(act[sm <= 0].mean() * 12),
            "sharpe": float(rr.mean() / rr.std() * math.sqrt(252))}


ref = pd.read_csv(LH / "gates.csv").set_index("id")
rows = []
for label, win, minp in (("b252_parity", 252, 200), ("b756", 756, 500)):
    F = resmom_feats(win, minp)
    for f in ("res12_1", "res6_1"):
        for n in (10, 20, 50):
            for reb in ("M", "W"):
                r = simulate(stock_targets(F[f], n, reb))
                s = {p: stats(r, p) for p in ("train", "valid", "valid2", "trval", "all")}
                lid = f"S2_{f}_N{n}_{reb}"
                rows.append({"id": f"R3_{label}_{f}_N{n}_{reb}", "win": label, "feat": f, "N": n, "reb": reb,
                             "act_train": s["train"]["active"], "act_valid": s["valid"]["active"],
                             "act_valid2": s["valid2"]["active"], "t_trval": s["trval"]["active_t"],
                             "up": s["all"]["up"], "down": s["all"]["down"], "sharpe_trval": s["trval"]["sharpe"],
                             "ref_act_train": ref.loc[lid, "active_train"], "ref_act_valid": ref.loc[lid, "active_valid"],
                             "ref_t": ref.loc[lid, "active_t_trval"]})
                print(rows[-1]["id"], round(rows[-1]["act_train"], 4), round(rows[-1]["ref_act_train"], 4),
                      round(rows[-1]["t_trval"], 2), flush=True)
g = pd.DataFrame(rows)
# gates on the 756 rows only (parity rows are not counted)
FNB = {"res12_1": "res6_1", "res6_1": "res12_1"}
NSTEP = [10, 20, 50]
out = []
for _, r in g[g.win == "b756"].iterrows():
    nb = g[(g.win == "b756") & (
        ((g.feat == FNB[r.feat]) & (g.N == r.N) & (g.reb == r.reb)) |
        ((g.feat == r.feat) & (g.N != r.N) & (g.reb == r.reb) & (abs(g.N.map(NSTEP.index) - NSTEP.index(r.N)) == 1)) |
        ((g.feat == r.feat) & (g.N == r.N) & (g.reb != r.reb)))]
    nb_act = float(((nb.act_train * 4 + nb.act_valid * 3.83) / 7.83).mean())
    A1 = r.act_train > 0 and r.act_valid > 0 and r.act_valid2 > 0
    A2 = r.t_trval >= T_REQ
    A3 = nb_act > 0
    A4 = r.up > 0 and r.down > 0
    out.append({**r.to_dict(), "A1": A1, "A2": A2, "A3": A3, "A4": A4, "nb_act": nb_act, "t_bar": T_REQ,
                "verdict": "A_edge" if (A1 and A2 and A3 and A4) else ("near" if A1 else "fail")})
G = pd.concat([pd.DataFrame(out), g[g.win != "b756"]], ignore_index=True)
G.to_csv(HERE / ("gates_resmom.csv" if TRAIN_START == "2017-01-01" else f"gates_resmom_from{TRAIN_START[:7]}.csv"), index=False, float_format="%.4f")
pd.set_option("display.width", 250)
print(G.round(3).to_string())
