"""One pass over the open lab-frame months: Part-B stock trades (first bar per symbol-day per base config), Part-A ETF
rows and context. Educational only - not financial advice."""
import sys

import numpy as np
import pandas as pd

from common import ROOT, SCR, lib
from mcf.research import gates

sys.path.insert(0, str(ROOT / "research" / "swarm1017" / "rework-st"))
import stcore  # noqa: E402

MIN_ADV = 95e6
GE = ("t1s1", "t05s1", "t1s05")
COLS = ["symbol", "date", "tod", "close", "high", "low", "rsi", "rsi5", "fromOpen", "gap", "vwapDistPct",
        "dist_pdl_atr", "dist_pdh_atr", "dist_lod_atr", "dist_hod_atr", "sma50_dist_pct", "sma20_slope_pct", "emaDiff",
        "buyPressure", "macdPct", "flow3", "volumeRatio", "atr_d", "adv20"] + \
       [f"{k}_long_{g}" for g in GE for k in ("r", "win")]
ETFS = ["SPY", "QQQ", "SPXL", "TQQQ", "IWM"]


def base_masks(c, F, pv, spymin, spyfo, brd, brdmin, brd2):
    """name -> (mask, window). c: column dict; pv: prev-bar dict."""
    fo, vx, rsi = c["fromOpen"], c["vwapDistPct"], c["rsi"]
    hl = (c["low"] > pv["low"]) & (c["close"] > pv["high"])
    vwup = (vx > 0) & (pv["vwapDistPct"] <= 0)
    turn = spyfo >= spymin + 0.10
    M = {}
    for d in (0.15, 0.30):
        for rs in (0, 1):
            m = (spymin <= -d) & turn & vwup
            if rs:
                m &= fo > spyfo
            M[f"B1-d{int(d*100):03d}-rs{rs}"] = (m, (950, 1100))
    for d in (0.30, 0.60):
        for w, win in (("am", (950, 1100)), ("mid", (1100, 1400))):
            m = (spyfo <= -d) & (fo > 0) & (vx > 0) & (c["dist_pdl_atr"] > 0) & (c["close"] > pv["high"])
            M[f"B2-d{int(d*100):03d}-{w}"] = (m, win)
    for x in (30, 40):
        for b in (0.05, 0.10):
            m = (rsi <= x) & (brd >= brdmin + b) & (spyfo >= spymin + 0.15)
            M[f"B3-rsi{x}-b{int(b*100):02d}"] = (m, (950, 1130))
    for d in (0.15, 0.30):
        for w, win in (("1030", (950, 1030)), ("1100", (950, 1100))):
            m = (spymin <= -d) & (fo - spyfo >= 0.5) & hl
            M[f"B4-d{int(d*100):03d}-w{w}"] = (m, win)
    par = {
        "NS1": (rsi <= 40) & (pv["rsi"] > 40) & (c["rsi5"] >= 80) & (fo > 2),
        "NS5": (c["sma50_dist_pct"] < 0) & (pv["sma50_dist_pct"] >= 0) & (rsi <= 30) & (fo < -2),
        "ST2": F.st("ST2", stcore.PARENT["ST2"]),
        "ST4": F.st("ST4", stcore.PARENT["ST4"]),
    }
    idxturn = (spymin <= -0.15) & turn
    brdup = brd >= brd2 + 0.05
    for p, m in par.items():
        M[f"B5-{p}-parent"] = (m, (950, 1130))
        M[f"B5-{p}-IDXTURN"] = (m & idxturn, (950, 1130))
        M[f"B5-{p}-BRDUP"] = (m & brdup, (950, 1130))
    return M


def main():
    idx5 = pd.read_parquet(SCR / "idx5.parquet")
    spy = idx5[idx5.sym == "SPY"][["date", "tod", "fo", "runmin"]].rename(columns={"fo": "spy_fo1", "runmin": "spymin"})
    spy["date"] = pd.to_datetime(spy["date"]).dt.date
    trades, etf, ctx_all, chk = [], [], [], []
    for month in lib.months(locked=False):
        if month in lib.LOCKED_MONTHS:
            continue
        df = lib.load_month(month, columns=COLS, context=True)
        df = df[df["adv20"] >= MIN_ADV].reset_index(drop=True)
        df = df.merge(spy, on=["date", "tod"], how="left")
        n = len(df)
        c = {k: df[k].to_numpy(float) for k in COLS if k not in ("symbol", "date")}
        c["tod"] = df["tod"].to_numpy(float)
        key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        new = np.r_[True, key[1:] != key[:-1]]
        tier = np.where((np.abs(c["gap"]) >= 20) | (c["close"] < 5), 3.0, 1.0)
        R = 0.25 * c["atr_d"]
        tod = c["tod"]
        # production R (long) and same-minute controls over the universe (tod 950..1500)
        pr = {}
        dk = pd.MultiIndex.from_arrays([df["date"], df["tod"]])
        with np.errstate(invalid="ignore", divide="ignore"):
            for g in GE:
                lab = c[f"r_long_{g}"]
                p = gates.prod_r(lab, c[f"win_long_{g}"], c["close"], c["atr_d"], g, tod=tod)
                gross = lab + 2 * gates.SLIP_PS / R
                v = np.where(np.isfinite(lab) & (c["atr_d"] > 0), gross - tier * (gross - p), np.nan)
                pr[g] = v
                pr["c_" + g] = pd.Series(v, index=dk).groupby(level=[0, 1]).transform("mean").to_numpy()
        pv = {}
        for k in ("low", "high", "vwapDistPct", "rsi", "sma50_dist_pct"):
            p = np.r_[np.nan, c[k][:-1]]
            p[new] = np.nan
            pv[k] = p
        spyfo = df["spy_fo"].to_numpy(float)
        spymin = np.fmin(df["spymin"].to_numpy(float), spyfo)
        brd = df["breadth"].to_numpy(float)
        ctx = df[["date", "tod", "spy_fo", "qqq_fo", "breadth", "breadth_open", "spy_fo1", "spymin"]].drop_duplicates(["date", "tod"])
        ctx = ctx.sort_values(["date", "tod"])
        ctx["brdmin"] = ctx.groupby("date")["breadth"].cummin()
        ctx["brd2"] = ctx.groupby("date")["breadth"].shift(2)
        ctx_all.append(ctx)
        cm = df[["date", "tod"]].merge(ctx[["date", "tod", "brdmin", "brd2"]], on=["date", "tod"], how="left")
        brdmin, brd2 = cm["brdmin"].to_numpy(float), cm["brd2"].to_numpy(float)
        F = stcore.Frame({k: c[k] for k in c}, new)
        with np.errstate(invalid="ignore"):
            M = base_masks(c, F, pv, spymin, spyfo, brd, brdmin, brd2)
        for name, (m, (a, b)) in M.items():
            m = np.asarray(m, bool) & (tod >= a) & (tod <= b) & np.isfinite(pr["t1s1"])
            idx = gates.first_per_symbol_day(df["symbol"].to_numpy(), df["date"].to_numpy(), m)
            if not len(idx):
                continue
            t = pd.DataFrame({"base": name, "symbol": df["symbol"].to_numpy()[idx], "date": df["date"].to_numpy()[idx],
                              "tod": tod[idx].astype(int), "close": c["close"][idx], "atr_d": c["atr_d"][idx],
                              "tier": tier[idx], "spy_fo": spyfo[idx]})
            for g in GE:
                t["r_" + g] = pr[g][idx]
                t["c_" + g] = pr["c_" + g][idx]
            trades.append(t)
        e = np.isin(df["symbol"].to_numpy(), ETFS)
        ed = df.loc[e, ["symbol", "date", "tod", "close", "high", "low", "vwapDistPct", "atr_d", "gap"]].copy()
        for g in GE:
            ed["r_" + g] = pr[g][e]
        etf.append(ed)
        ok = np.isfinite(spyfo) & np.isfinite(df["spy_fo1"].to_numpy(float))
        chk.append(float(np.nanmax(np.abs(spyfo[ok] - df["spy_fo1"].to_numpy(float)[ok]))) if ok.any() else np.nan)
        print(month, n, sum(len(x) for x in trades), flush=True)
    T = pd.concat(trades, ignore_index=True)
    T.to_parquet(SCR / "b_trades.parquet", index=False)
    pd.concat(etf, ignore_index=True).to_parquet(SCR / "etf_rows.parquet", index=False)
    pd.concat(ctx_all, ignore_index=True).to_parquet(SCR / "ctx.parquet", index=False)
    print("max |spy_fo(context) - spy_fo(1min)| per month:", [round(x, 4) for x in chk])
    print(T.groupby("base").size().to_string())


if __name__ == "__main__":
    main()
