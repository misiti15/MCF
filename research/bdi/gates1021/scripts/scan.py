"""gates1021 step 1: live-shaped signals of every covered live lab setup on the open two-year frames, with production
R (extended tier x3), the market state at entry, the same-minute random control, and (Part A setups) the 5-minute
exit bar and the peer median. PLAN.md was written before this ran. Educational only - not financial advice.

    python research/bdi/gates1021/scripts/scan.py     # -> $G21SCR/sig/<month>.parquet, ctrl/<month>.parquet
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from common import HERE, SCR, chain, gates, lib, load_mod, no_locked
from setups import live_setups

PART_A = ("NS3-failed-vwap-reclaim-short-FD", "L3-gap-slope-fromopen-FD")
GEOMK = gates.GEOMK


def unique_setups() -> pd.DataFrame:
    df = live_setups()
    df = df[df["covered"]].copy()
    df["key"] = df["module"] + "|" + df["window"].astype(str) + "|" + df["min_adv"].astype(str) + "|" + \
        df["refire"].astype(str) + "|" + df["cooldown"].astype(str) + "|" + df["geom"].astype(str)
    g = df.groupby("key", sort=False).agg(setup=("setup", "first"), accounts=("account", lambda x: ",".join(x)),
                                          names=("setup", lambda x: ",".join(sorted(set(x)))),
                                          module=("module", "first"), window=("window", "first"),
                                          min_adv=("min_adv", "first"), refire=("refire", "first"),
                                          cooldown=("cooldown", "first"), geom=("geom", "first"),
                                          side=("side", "first")).reset_index(drop=True)
    # Part A parents must be the Primary configs
    return g


def prod_r_tier(df, idx, side, geom):
    up, dn = GEOMK[geom]
    lab = df[f"r_{side}_{geom}"].to_numpy(float)[idx]
    win = df[f"win_{side}_{geom}"].to_numpy(float)[idx]
    c = df["close"].to_numpy(float)[idx]
    atr = df["atr_d"].to_numpy(float)[idx]
    tod = df["tod"].to_numpy(float)[idx]
    p = gates.prod_r(lab, win, c, atr, geom, tod=tod)
    R = 0.25 * atr
    gross = lab + 2 * gates.SLIP_PS / R
    tier = np.where((np.abs(df["gap"].to_numpy(float)[idx]) >= 20) | (c < 5), 3.0, 1.0)
    return gross - tier * (gross - p)


def exit_bars(df, idx, side, geom):
    """5-minute path exit: (exit tod, kind) per signal row; kind 1 stop, 2 target, 0 held to 15:55 (tod 1555)."""
    up, dn = GEOMK[geom]
    s = 1 if side == "long" else -1
    sym = df["symbol"].to_numpy()
    dat = df["date"].to_numpy()
    c, h, l, tod, atr = (df[k].to_numpy(float) for k in ("close", "high", "low", "tod", "atr_d"))
    n = len(c)
    ex_t = np.full(len(idx), 1555.0)
    kind = np.zeros(len(idx), int)
    for j, i in enumerate(idx):
        R = 0.25 * atr[i]
        stop = c[i] - s * dn * R
        tgt = c[i] + s * up * R
        k = i + 1
        while k < n and sym[k] == sym[i] and dat[k] == dat[i]:
            if (s == -1 and h[k] >= stop) or (s == 1 and l[k] <= stop):
                ex_t[j], kind[j] = tod[k], 1
                break
            if (s == -1 and l[k] <= tgt) or (s == 1 and h[k] >= tgt):
                ex_t[j], kind[j] = tod[k], 2
                break
            k += 1
    return ex_t, kind


def context_extra(month: str, spy_prev: pd.Series) -> pd.DataFrame:
    c = lib.load_context(month).sort_values(["date", "tod"]).reset_index(drop=True)
    b = c["breadth"].to_numpy(float)
    same = np.r_[False, False, c["date"].to_numpy()[2:] == c["date"].to_numpy()[:-2]]
    prev2 = np.r_[np.nan, np.nan, b[:-2]]
    d2 = np.where(same & (c["tod"].to_numpy() >= 1000), b - prev2, np.nan)
    c["d2"] = d2
    c["spy_prev"] = c["date"].map(spy_prev)
    return c[["date", "tod", "d2", "spy_prev"]]


def month_job(args):
    month, sts, peers = args
    t0 = time.time()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    spy_prev = pd.read_parquet(SCR / "spy_prev.parquet").set_index("date")["spy_prev"]
    f = f.merge(context_extra(month, spy_prev), on=["date", "tod"], how="left")
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    tod = f["tod"].to_numpy()
    adv = f["adv20"].fillna(0).to_numpy()
    atr_ok = f["atr_d"].to_numpy(float) > 0
    # same-minute random control (adv20 >= 95M), per side x geom
    ctrl = []
    base95 = (adv >= 95e6) & atr_ok & (tod >= 950) & (tod <= 1500)
    for side in ("short", "long"):
        for geom in ("t1s1", "t05s1", "t1s05"):
            m = base95 & np.isfinite(f[f"r_{side}_{geom}"].to_numpy(float))
            idx = np.flatnonzero(m)
            r = prod_r_tier(f, idx, side, geom)
            g = pd.DataFrame({"date": f["date"].to_numpy()[idx], "tod": tod[idx], "r": r}).groupby(["date", "tod"])["r"].mean()
            ctrl.append(g.rename(f"c_{side}_{geom}"))
    ctrl = pd.concat(ctrl, axis=1).reset_index()
    ctrl.to_parquet(SCR / "ctrl" / f"{month}.parquet")
    # peer median fromOpen (Part A)
    fo_w = f.pivot_table(index=["date", "tod"], columns="symbol", values="fromOpen", aggfunc="first")
    rows = []
    for s in sts:
        try:
            m = load_mod(s["setup"], s["module"])
            lo, hi = s["window"]
            with np.errstate(invalid="ignore", divide="ignore"):
                mk = np.asarray(m.mask(f), bool)
        except Exception as e:  # noqa: BLE001
            rows.append(pd.DataFrame({"setup": [s["setup"]], "error": [repr(e)[:200]]}))
            continue
        side, geom = s["side"], s["geom"]
        ok = mk & (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= s["min_adv"]) & atr_ok \
            & np.isfinite(f[f"r_{side}_{geom}"].to_numpy(float))
        hit = np.flatnonzero(ok)
        if not len(hit):
            continue
        pos = chain(f["symbol"].to_numpy()[hit], f["date"].to_numpy()[hit], tod[hit], s["refire"], s["cooldown"])
        idx = hit[pos]
        out = pd.DataFrame({"setup": s["setup"], "symbol": f["symbol"].to_numpy()[idx], "date": f["date"].to_numpy()[idx],
                            "tod": tod[idx], "r": prod_r_tier(f, idx, side, geom),
                            "win": f[f"win_{side}_{geom}"].to_numpy(float)[idx]})
        for k in ("spy_fo", "qqq_fo", "breadth", "breadth_open", "d2", "spy_prev", "fromOpen", "close", "gap", "adv20",
                  "atr_d"):
            out[k] = f[k].to_numpy(float)[idx]
        if s["setup"] in PART_A:
            et, kd = exit_bars(f, idx, side, geom)
            out["exit_tod"], out["exit_kind"] = et, kd
            pm = np.full(len(idx), np.nan)
            npeer = np.zeros(len(idx), int)
            for j, (sy, d, t) in enumerate(zip(out["symbol"], out["date"], out["tod"])):
                p = [x for x in peers.get(sy, []) if x in fo_w.columns]
                if not p:
                    continue
                try:
                    v = fo_w.loc[(d, t), p].to_numpy(float)
                except KeyError:
                    continue
                v = v[np.isfinite(v)]
                npeer[j] = len(v)
                if len(v) >= 3:
                    pm[j] = float(np.median(v))
            out["peer_med"], out["n_peer"] = pm, npeer
        rows.append(out)
    res = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    res.to_parquet(SCR / "sig" / f"{month}.parquet")
    return month, len(res), round(time.time() - t0, 1)


def peer_map() -> dict:
    """Top-5 peers by TRAIN daily close-to-close return correlation (non-ETF lab symbols, >= 120 train days)."""
    d = lib.daily()
    d = d[pd.to_datetime(d["date"]).dt.date <= pd.Timestamp("2025-12-31").date()].copy()
    d = d.sort_values(["symbol", "date"])
    d["ret"] = d.groupby("symbol")["close"].pct_change()
    # no return across the locked gap
    gap = pd.to_datetime(d["date"]).groupby(d["symbol"]).diff().dt.days > 5
    d.loc[gap.to_numpy(), "ret"] = np.nan
    w = d.pivot_table(index="date", columns="symbol", values="ret")
    lk = pd.read_csv(HERE.parents[0] / "indexlink" / "linkage.csv", usecols=["symbol", "is_etf"])
    etf = set(lk.loc[lk["is_etf"].astype(str).str.lower() == "true", "symbol"])
    cols = [c for c in w.columns if c not in etf and w[c].notna().sum() >= 120]
    w = w[cols]
    cm = w.corr(min_periods=100)
    out = {}
    for s in cols:
        x = cm[s].drop(s).dropna().sort_values(ascending=False)
        out[s] = list(x.index[:5])
    return out


def main():
    (SCR / "sig").mkdir(exist_ok=True)
    (SCR / "ctrl").mkdir(exist_ok=True)
    us = unique_setups()
    us.to_csv(HERE / "setups_scored.csv", index=False)
    # prior-day SPY close-to-close return (NaN after a data gap)
    d = lib.daily()
    spy = d[d["symbol"] == "SPY"].sort_values("date")
    dd = pd.to_datetime(spy["date"])
    prev = spy["close"].pct_change() * 100
    prev[(dd.diff().dt.days > 5).to_numpy()] = np.nan
    pd.DataFrame({"date": spy["date"].to_numpy(), "spy_prev": prev.to_numpy()}).to_parquet(SCR / "spy_prev.parquet")
    pm = peer_map()
    json.dump(pm, open(SCR / "peers.json", "w"))
    sts = us.to_dict("records")
    months = lib.months()
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    with Pool(workers) as p:
        for r in p.imap_unordered(month_job, [(m, sts, pm) for m in months]):
            print(r, flush=True)


if __name__ == "__main__":
    main()
