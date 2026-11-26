"""First hand-built crypto setups (pre-registered in research/crypto_setups1/PREREG.md; sha256 in PREREG.sha256).

    python research/crypto_setups1/run_s1.py fit     # 14 configs on FIT -> fit.csv, fit_stats.json (frozen)
    python research/crypto_setups1/run_s1.py check   # all 14 scored ONCE on CHECK + random baselines -> check.csv
Engine: mcf/crypto/setups1.py (maker limit entries, Amendment-1 traded-through fills, absolute stop/target levels).
Clean signal bars (mcf/crypto/exec1m.clean_traded). LOCKED is never read: the loader clips at its start.
Cache: MCF_CRYPTO_CACHE (default data/crypto/1Min). Educational only — not financial advice.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
assert os.environ.get("MCF_CRYPTO_ALLOW_LOCKED") != "1", "LOCKED must stay sealed"
from mcf.crypto import data as D  # noqa: E402
from mcf.crypto import setups1 as S1  # noqa: E402
from mcf.crypto import splits as SP  # noqa: E402
from mcf.crypto.backtest import summarize  # noqa: E402
from mcf.crypto.costs import CostModel  # noqa: E402
from mcf.crypto.exec1m import Minutes, clean_prints, clean_traded, to_min  # noqa: E402

HERE = Path(__file__).parent
N_PRIOR = 1477
SEED = 20261127
RAND = 100
MIN_TRADES, MAX_SHARE, CHECK_T, MIN_YEARS = 60, 0.5, 1.5, 3
M, A, X = S1.MAJORS, S1.ALTS, S1.ALL6
CONFIGS = [
    dict(id=1478, setup="CRY-FLUSH-1", var="a", kind="flush", coins=M),
    dict(id=1479, setup="CRY-FLUSH-1", var="b", kind="flush", coins=A),
    dict(id=1480, setup="CRY-SHOCK-1", var="a", kind="shock", coins=A),
    dict(id=1481, setup="CRY-REV12-1", var="a", kind="rev12", coins=M),
    dict(id=1482, setup="CRY-REV12-1", var="b", kind="rev12", coins=X),
    dict(id=1483, setup="CRY-UPDIP-1", var="a", kind="updip", coins=M),
    dict(id=1484, setup="CRY-UPDIP-1", var="b", kind="updip", coins=A),
    dict(id=1485, setup="CRY-DAY2-1", var="a", kind="day2", coins=X, mode="reclaim"),
    dict(id=1486, setup="CRY-DAY2-1", var="b", kind="day2", coins=X, mode="open"),
    dict(id=1487, setup="CRY-WKND-1", var="a", kind="wknd", coins=("BTC", "ETH", "LINK")),
    dict(id=1488, setup="CRY-WKND-1", var="b", kind="wknd", coins=X),
    dict(id=1489, setup="CRY-CPI-1", var="a", kind="cpi", coins=M),
    dict(id=1490, setup="CRY-DIP-1", var="a", kind="dip", coins=M),
    dict(id=1491, setup="CRY-DIP-1", var="b", kind="dip", coins=A),
]
N_CUM = N_PRIOR + len(CONFIGS)
BAR = float(np.sqrt(2 * np.log(N_CUM)))
COSTS = CostModel()
P: dict = {}
MINS: dict = {}
SIG: dict = {}          # config id -> pair -> full-history signal frame


def load() -> None:
    t0 = time.time()
    end = pd.Timestamp(SP.LOCKED_START, tz="UTC")
    for p in X:
        raw = D.load_bars(p)
        MINS[p] = Minutes.from_bars(clean_prints(raw))
        s = clean_traded(raw)
        P[p] = S1.prep_pair(s, end)
        if p in M:
            P[p]["M1"] = s[["c", "v", "vw"]]
        del raw
        print(p, f"{time.time()-t0:.0f}s", flush=True)
    for c in CONFIGS:
        SIG[c["id"]] = {p: S1.BUILDERS[c["kind"]](P, p, c) for p in c["coins"]}
    print(f"loaded + signals in {time.time()-t0:.0f}s", flush=True)


def trades_for(cid: int, split: str, rng=None) -> tuple[pd.DataFrame, int, int]:
    a, z = SP.bounds(split)
    am, zm = int(to_min(pd.DatetimeIndex([a]))[0]), int(to_min(pd.DatetimeIndex([z]))[0])
    out, offered, missed = [], 0, 0
    for p, sg in SIG[cid].items():
        sg = sg[(sg["t"] >= am) & (sg["t"] < zm)]
        if rng is not None:
            sg = S1.random_signals(rng, sg, P[p]["H"], a, z)
        tr, o, mi = S1.run_levels(p, MINS[p].slice(am, zm), sg, COSTS)
        offered += o
        missed += mi
        if len(tr):
            out.append(tr)
    tr = pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=S1.TRADE_COLS)
    return tr, offered, missed


def score(args) -> dict:
    cid, split, seed = args
    c = next(x for x in CONFIGS if x["id"] == cid)
    tr, offered, missed = trades_for(cid, split)
    sm = summarize(tr)
    a, z = SP.bounds(split)
    n_days = (z - a).days
    act = S1.active_days(tr)
    btc = P["BTC"]["D"]
    below = btc.index[(btc["c"] < btc["sma50"]).to_numpy() & (btc.index >= a) & (btc.index < z)]
    row = {"id": cid, "setup": c["setup"], "var": c["var"], "coins": " ".join(c["coins"]), "split": split,
           "offered": offered, "missed": missed, "fill": (offered - missed) / offered if offered else np.nan, **sm,
           "maxdd_r": S1.max_dd_r(tr), "active_share": len(act) / n_days,
           "active_below_sma50": len(act.intersection(below)) / max(1, len(below)),
           "trades_in_below": int(tr["day"].isin(below).sum()) if len(tr) else 0}
    for k, (n, v) in S1.by_year(tr).items():
        row[f"y{k}_n"], row[f"y{k}_r"] = n, v
    for p in c["coins"]:
        x = tr.loc[tr["pair"] == p, "r"] if len(tr) else pd.Series(dtype=float)
        row[f"{p}_n"], row[f"{p}_r"] = int(len(x)), float(x.mean()) if len(x) else np.nan
    if seed is not None and len(tr):
        rng = np.random.default_rng(seed)
        rb = np.array([trades_for(cid, split, rng)[0]["r"].mean() for _ in range(RAND)], float)
        row["rand_mean"] = float(np.nanmean(rb))
        row["rand_pct"] = float(np.nanmean(rb < sm["avg_r"]))
    tr.assign(id=cid).to_csv(HERE / f"trades_{split}_{cid}.csv.gz", index=False, float_format="%.6g")
    return row


def fit_eligible(r) -> bool:
    return bool(r["n"] >= MIN_TRADES and r["best_day_share"] < MAX_SHARE and r["avg_r_wo_best"] > 0
                and r["day_t"] >= BAR)


SHOW = ["id", "setup", "var", "n", "fill", "avg_r", "avg_r_wo_best", "best_day_share", "day_t", "win", "avg_cost_r",
        "maxdd_r", "active_share", "rand_mean", "rand_pct"]


def fit() -> None:
    load()
    with mp.get_context("fork").Pool(4) as pool:
        rows = pool.map(score, [(c["id"], "fit", SEED + c["id"]) for c in CONFIGS])
    df = pd.DataFrame(rows)
    df["fit_eligible"] = df.apply(fit_eligible, axis=1)
    df.to_csv(HERE / "fit.csv", index=False, float_format="%.4f")
    stats = {"frozen_utc": pd.Timestamp.now(tz="UTC").isoformat(), "configs": len(CONFIGS), "n_cum": N_CUM,
             "noise_bar": BAR, "fit_eligible": df.loc[df.fit_eligible, "id"].tolist()}
    (HERE / "fit_stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))
    print(df[SHOW].to_string())


def check() -> None:
    fz = json.loads((HERE / "fit_stats.json").read_text())
    load()
    with mp.get_context("fork").Pool(4) as pool:
        rows = pool.map(score, [(c["id"], "check", SEED + 5000 + c["id"]) for c in CONFIGS])
    df = pd.DataFrame(rows)
    fit_df = pd.read_csv(HERE / "fit.csv").set_index("id")
    yrs = ["y2021_r", "y2022_r", "y2023_r", "y2024_r"]
    out = []
    for r in df.itertuples():
        f = fit_df.loc[r.id]
        pos_years = int(sum(1 for y in yrs if pd.notna(f[y]) and f[y] > 0)) + int(r.avg_r > 0 and r.n > 0)
        passed = bool(r.id in fz["fit_eligible"] and r.avg_r > 0 and r.day_t >= CHECK_T and pos_years >= MIN_YEARS)
        out.append({"id": r.id, "pos_years": pos_years, "pass": passed})
    df = df.merge(pd.DataFrame(out), on="id")
    df.to_csv(HERE / "check.csv", index=False, float_format="%.4f")
    # gate state at the last readable day (LOCKED is sealed; see REPORT for the Nov-2026 regime from KNOWLEDGE)
    b = P["BTC"]["D"].dropna(subset=["sma50"]).iloc[-1]
    state = {"last_day": str(P["BTC"]["D"].dropna(subset=["sma50"]).index[-1].date()), "btc_c": float(b["c"]),
             "btc_sma50": float(b["sma50"]), "btc_up": bool(b["up"]), "btc_down_off": bool(b["down_off"])}
    bd = P["BTC"]["D"].dropna(subset=["sma50"])
    bd = bd[bd.index >= "2021-03-01"]
    state["share_days_btc_up"] = float(bd["up"].mean())
    state["share_days_down_off"] = float(bd["down_off"].mean())
    state["share_below_sma50_that_are_down_off"] = float(bd.loc[~bd["up"], "down_off"].mean())
    (HERE / "check_stats.json").write_text(json.dumps({"fit": fz, "state": state,
                                                       "passes": df.loc[df["pass"], "id"].tolist()}, indent=1))
    print(json.dumps(state, indent=1))
    print(df[SHOW + ["pos_years", "pass"]].to_string())


if __name__ == "__main__":
    {"fit": fit, "check": check}[sys.argv[1]]()
