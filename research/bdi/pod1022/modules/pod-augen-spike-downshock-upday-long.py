"""pod-augen-spike-downshock-upday-long - Augen price-spike (sigma) down-shock fade on an up day (LONG).

Source: Jeff Augen, 'The Volatility Edge in Options Trading' / 'Day Trading Options' (price-spike charts); R-bloggers
'Trading Mean Reversion with Augen Spikes' (Shifting Sands).
URL: https://www.r-bloggers.com/2011/10/trading-mean-reversion-with-augen-spikes/

VARIANT of pod-smb-rubberband-2bar-snap-long. What changes: the trigger is a volatility-normalised single-bar shock
(Augen sigma units) instead of a distance-from-mean stretch, and an up-day gate is added.
Rules (plain English, LONG; 5m bars 09:35..15:00 with volume):
  spike_j = (close_j - close_{j-1}) / (close_{j-1} x stdev of the 20 PRIOR intraday 5m log returns) (Augen: the
  stdev window ends one bar before the bar being measured; the overnight / first-bar return is left out of the
  window; the window is carried across sessions of the same symbol).
  1. Spike bar j: spike <= -3.0, bar close 10:00-14:30 ET.
  2. Before bar j: the stock closed above session VWAP on >= 60% of today's bars (09:35..j-1), and the day return from
     the 09:30 open at bar j-1 is >= 0.
  3. SPY's spike on the same bar is > -1.5 (idiosyncratic shock, not a market flush).
  4. Holding bar j+1: its low is not below bar j's low. Entry: the close of bar j+1.
  Skip the day once SPY has printed >= 3 bars with |spike| >= 3 so far today (the 'market-wide spike' count, counted
  causally up to bar j).
  Stop (GEOM S+x): spike-bar low - 0.1 x ATR5m(14). Target: the nearer (above entry) of the spike bar's 50% body
  retrace (midpoint of close_{j-1} and close_j; the bar open is not stored, so the previous close stands in for it)
  and session VWAP; no trade when neither is above the entry. Time exit: 6 bars (30 min) after entry; flat 15:55.
  Universe: adv20 >= $100M (liquid large caps and sector ETFs) - pre-declared.
No tweak used. No tuning on valid. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision
bar are used. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r311_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 6
WINDOW = (1005, 1435)
MIN_ADV = 100e6
LAYERS = ["Augen spike <= -3 sigma (20 prior 5m returns), 10:00-14:30",
          ">= 60% of prior bars above VWAP, day return from open >= 0", "SPY same-bar spike > -1.5",
          "next bar holds the spike low; entry its close", "skip after >= 3 SPY |spike|>=3 bars today",
          "stop spike low - 0.1 ATR5, target nearer of 50% body / VWAP, 6-bar time exit"]
_S = U.Stash()


@numba.njit(cache=False)
def _spike(nd, c, o):
    n = len(c)
    sp = np.full(n, np.nan)
    buf = np.zeros(20)
    cnt = 0
    pos = 0
    for i in range(n):
        if nd[i] == 2:
            cnt = 0
            pos = 0
        if nd[i] != 0:
            continue                  # first bar of a day: overnight return, not measured, not in the window
        pc = c[i - 1]
        if not (pc > 0 and c[i] > 0):
            continue
        r = np.log(c[i] / pc)
        if cnt >= 20:
            mu = 0.0
            for q in range(20):
                mu += buf[q]
            mu /= 20.0
            ss = 0.0
            for q in range(20):
                ss += (buf[q] - mu) ** 2
            sd = np.sqrt(ss / 19.0)
            if sd > 0:
                sp[i] = (c[i] - pc) / (pc * sd)
        buf[pos] = r
        pos = (pos + 1) % 20
        cnt += 1
    return sp


@numba.njit(cache=False)
def _kern(nd, tod, o, h, l, c, v, atr, sp, spy_sp, spy_cnt):
    n = len(c)
    m = np.zeros(n)
    s = np.full(n, np.nan)
    t = np.full(n, np.nan)
    ca = np.nan
    na = 0
    trs = 0.0
    pv = 0.0
    vv = 0.0
    nb = 0
    nab = 0
    o9 = np.nan
    vwp = np.full(n, np.nan)
    a5 = np.full(n, np.nan)
    abv = np.zeros(n)        # share of today's bars up to and incl. this one closing above VWAP
    for i in range(n):
        if nd[i] == 2:
            na = 0
            trs = 0.0
            ca = np.nan
        if nd[i] >= 1:
            pv = 0.0
            vv = 0.0
            nb = 0
            nab = 0
            o9 = o[i]
        pc = c[i - 1] if (i > 0 and nd[i] != 2) else np.nan
        tr = h[i] - l[i]
        if pc == pc:
            tr = max(tr, abs(h[i] - pc), abs(l[i] - pc))
        if na < 14:
            trs += tr
            na += 1
            if na == 14:
                ca = trs / 14.0
        else:
            ca = (ca * 13.0 + tr) / 14.0
        a5[i] = ca
        pv += (h[i] + l[i] + c[i]) / 3.0 * v[i]
        vv += v[i]
        vwp[i] = pv / vv if vv > 0 else np.nan
        nb += 1
        if c[i] > vwp[i]:
            nab += 1
        abv[i] = nab / nb
        # entry check: this bar i is the holding bar, j = i - 1 the spike bar
        if nd[i] != 0 or i < 2:
            continue
        j = i - 1
        if nd[j] != 0 or tod[j] < 1000 or tod[j] > 1430:
            continue
        if not (sp[j] <= -3.0):
            continue
        if not (abv[j - 1] >= 0.6) or not (c[j - 1] / o9 - 1.0 >= 0.0):
            continue
        if not (spy_sp[j] > -1.5) or not (spy_cnt[j] < 3):
            continue
        if l[i] < l[j]:
            continue
        stop = l[j] - 0.1 * a5[i]
        e = c[i]
        mid = 0.5 * (c[j - 1] + c[j])
        tg = np.nan
        if mid > e:
            tg = mid
        if vwp[i] > e and (tg != tg or vwp[i] < tg):
            tg = vwp[i]
        if tg == tg and stop < e:
            m[i] = 1.0
            s[i] = stop
            t[i] = tg
    return m, s, t


def mask(df) -> np.ndarray:
    n = len(df)
    nanv = np.full(n, np.nan)
    _S.put(df, s=nanv, t=nanv)
    X = U.vbars(df)
    if X is None or not len(X) or not n:
        return np.zeros(n, bool)
    nd = U.flags(X)
    sp = _spike(nd, X["c"].to_numpy(float), X["o"].to_numpy(float))
    Sx = U.sym_bars(df, ["SPY"])
    sn = U.flags(Sx.assign(dn=Sx["dn"]))
    ssp = _spike(sn, Sx["c"].to_numpy(float), Sx["c"].to_numpy(float))
    T = pd.DataFrame({"date": Sx["date"].to_numpy(), "tod": Sx["tod"].to_numpy(np.int64), "sp": ssp})
    T["big"] = (np.abs(T["sp"]) >= 3).astype(float)
    T["cnt"] = T.groupby("date")["big"].cumsum()
    mm = U.map_dt(X, T, ["sp", "cnt"])
    r = U.run_kernel(df, _kern, extra=(sp, mm["sp"], np.nan_to_num(mm["cnt"], nan=99.0)), cols=("m", "s", "t"))
    _S.put(df, s=r["s"], t=r["t"])
    tod = df["tod"].to_numpy(np.int64)
    return np.asarray(r["m"] & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)


def stop_price(f, i):
    return float(_S.get(f, "s", mask)[i])


def target_price(f, i, stop):
    return float(_S.get(f, "t", mask)[i])
