"""pod-cwt3-fabrio-commodity-etf-underreact-gap-long - Commodity/sector ETF gaps up, linked stock under-reacts at the
open: buy the catch-up (LONG).

Source: Chat With Traders EP164, Nick Fabrio (overnight commodity / sector ETF read-through) [~00:44:45]; the same
idea in EP051, Bryce Edwards (overnight commodity move into resource stocks) [~00:34:37].
URL: https://chatwithtraders.com/164

NEW in MCF (driver-ETF read-through; not the sector-peer leader setup, which keys off peers turning green, nor the
intraday stock-vs-SPY/sector spread fade).

Rules (plain English, LONG). Daily values only from completed days (research/history2y daily table); the 09:30 print,
the 09:30-09:35 range and the 09:35-09:45 driver closes come from the 1-minute cache (research/bdi/pod1022/
cwt3_openbars.py), because the lab frames start at 09:50.
  Driver map (stand-in for the guest's industry map, pre-declared): drivers = GLD, GDX, SLV, USO, XLE, XOP, XME,
  COPX. Candidate stocks = names in the energy / materials sector buckets (XLE, XLB in the sector map) or unmapped,
  minus the driver ETFs themselves. A stock's driver = the driver with the highest 60-session daily-return
  correlation (completed sessions before D, post-locked-block history only), and that correlation must be >= 0.5.
  (a) driver gap at 09:30 (daily open D / close D-1) >= +1.5%;
  (b) the stock's 60-session daily beta to that driver >= 0.8;
  (c) expected gap = beta x driver gap; the stock's actual gap is > 0 and < 50% of the expected gap (under-reaction;
      the guest skips a stock that already gapped as much as the ETF);
  (d) the driver's 5-minute closes at 09:35, 09:40 and 09:45 are all above its 09:30 opening print.
  Entry: the first 5-minute close above the stock's 09:30-09:35 high, bar close 09:35-10:15. The scorer cannot enter
  before the 09:50 bar, so a day whose first such close came at 09:40 or 09:45 is skipped (not entered late); the
  scored window is 09:50-10:15.
  Stop (GEOM S): the 09:30-09:35 low. Target: the price at which the stock's gap equals the expected gap (prior close
  x (1 + expected gap)); a day already at or beyond it at the trigger is skipped.
  Exit deviation (scorer limit): the guest's 10:30 time exit (10-20 minute scalp) cannot be modelled by the pod1022
  scorer (no time exit); unfilled trades are held to 15:55. Costs in (scorer).
No tweak used. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1015)
CONTEXT = []
LAYERS = ["driver (GLD/GDX/SLV/USO/XLE/XOP/XME/COPX, top 60d corr >= 0.5) gap >= +1.5%",
          "60d beta to driver >= 0.8", "0 < stock gap < 0.5 x beta x driver gap",
          "driver 09:35/09:40/09:45 closes above its 09:30 print",
          "first 5m close above the 09:30-09:35 high (none at 09:40/09:45)", "09:50-10:15",
          "stop 09:30-09:35 low, target = expected-gap price, else 15:55"]

DRIVERS = ["GLD", "GDX", "SLV", "USO", "XLE", "XOP", "XME", "COPX"]
_ROOT = Path(__file__).resolve().parents[4]
_STASH = {}
_CACHE = {}


def _imp():
    for p in (str(_ROOT / "research" / "history2y"), str(_ROOT / "research" / "bdi" / "pod1022")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import cwt3_openbars  # noqa: E402
    import lib  # noqa: E402
    return lib, cwt3_openbars


def _daily_map():
    if "m" in _CACHE:
        return _CACHE["m"]
    lib, _ = _imp()
    d = lib.daily()[["symbol", "date", "open", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d[d["date"] > pd.Timestamp("2025-02-28").date()]          # post-locked-block history only (contiguous)
    cl = d.pivot(index="date", columns="symbol", values="close").sort_index()
    op = d.pivot(index="date", columns="symbol", values="open").sort_index()
    ret = cl.pct_change(fill_method=None)
    smap = json.loads((_ROOT / "research" / "rework" / "web_families" / "sector_map.json").read_text())
    cand = [s for s in cl.columns if s not in DRIVERS and smap.get(s, "SPY") in ("XLE", "XLB", "SPY")]
    best_corr = pd.DataFrame(-np.inf, index=cl.index, columns=cand)
    best_beta = pd.DataFrame(np.nan, index=cl.index, columns=cand)
    best_drv = pd.DataFrame("", index=cl.index, columns=cand)
    R = ret[cand]
    for drv in DRIVERS:
        if drv not in ret:
            continue
        x = ret[drv]
        cov = R.rolling(60, min_periods=60).cov(x)
        var = x.rolling(60, min_periods=60).var()
        cor = R.rolling(60, min_periods=60).corr(x)
        beta = cov.div(var, axis=0)
        cor, beta = cor.shift(1), beta.shift(1)                    # day D sees sessions up to D-1 only
        better = cor > best_corr
        best_corr = best_corr.where(~better, cor)
        best_beta = best_beta.where(~better, beta)
        best_drv = best_drv.where(~better, drv)
    dgap = (op[DRIVERS] / cl[DRIVERS].shift(1) - 1) * 100            # 09:30 open vs completed prior close
    long = pd.DataFrame({"corr": best_corr.stack(), "beta": best_beta.stack(), "drv": best_drv.stack()})
    long.index.names = ["date", "symbol"]
    long = long.reset_index()
    long = long[np.isfinite(long["corr"]) & (long["corr"] >= 0.5)]
    dg = dgap.stack().rename("dgap").reset_index()
    dg.columns = ["date", "drv", "dgap"]
    long = long.merge(dg, on=["date", "drv"], how="left")
    pc = cl.shift(1).stack().rename("pc").reset_index()
    pc.columns = ["date", "symbol", "pc"]
    long = long.merge(pc, on=["date", "symbol"], how="left")
    _CACHE["m"] = long
    return long


def compute(df):
    n = len(df)
    nil = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if n == 0:
        return nil
    lib, ob = _imp()
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    mp = key.merge(_daily_map(), on=["symbol", "date"], how="left")
    t = ob.table()
    mine = key.merge(t[["symbol", "date", "h5", "l5", "or5_cross_pre950"]], on=["symbol", "date"], how="left")
    dv = t[t["symbol"].isin(DRIVERS)].copy()
    dv["drv_ok"] = ((dv["c935"] > dv["o930"]) & (dv["c940"] > dv["o930"]) & (dv["c945"] > dv["o930"])).astype(float)
    dv = dv[["symbol", "date", "drv_ok"]].rename(columns={"symbol": "drv"})
    mp = mp.merge(dv, on=["drv", "date"], how="left")
    f = lambda k: df[k].to_numpy(float)
    c, gap = f("close"), f("gap")
    beta, dgap, pc = (mp[k].to_numpy(float) for k in ("beta", "dgap", "pc"))
    h5, l5, pre = (mine[k].to_numpy(float) for k in ("h5", "l5", "or5_cross_pre950"))
    with np.errstate(invalid="ignore", divide="ignore"):
        exp_gap = beta * dgap
        tgt = pc * (1 + exp_gap / 100)
        m = (dgap >= 1.5) & (beta >= 0.8)
        m &= (gap > 0) & (gap < 0.5 * exp_gap)
        m &= mp["drv_ok"].to_numpy(float) == 1
        m &= pre == 0
        up = c > h5
        k = pd.factorize(key["symbol"] + "|" + key["date"].astype(str))[0]
        prior = pd.Series(up.astype(int)).groupby(k).cumsum().to_numpy() - up.astype(int)
        m &= up & (prior == 0)                                     # the first frame close above the 09:30-09:35 high
        m &= (l5 < c) & (tgt > c)
    return np.asarray(m, bool), l5, tgt


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
