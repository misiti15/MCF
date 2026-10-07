"""MarcoFlow's layer catalog (lib/strategy-review buildConditions, knowledge pack guide 08) mapped onto the
setup-lab frame. Each condition is parametric so one-step neighbours can be scored (plateau check).

A MarcoFlow signal is a bar with |heat| >= 30; direction = sign(heat). Every stack is therefore
  side long:  heat >= 30 AND layers      side short: heat <= -30 AND layers
Mapping notes (honest gaps):
  * session windows: MarcoFlow's observedAt minute -> lab bar-end `tod`; the lab frame starts at 09:50,
    so 'open-first10'/'open-first15' cannot be scored (empty) and 'slot-open' etc. lose 09:30-09:50.
  * reg-*: MarcoFlow used SPY > 50-day SMA and 1-month change. SPY history before 2026-06-30 is not in the
    lab frame, so a PROXY is used (prior-day SPY close vs its 20-session mean and 20-session change,
    min 5 sessions). Not deployable through mask(df) (needs another symbol).
  * asset-*: ETF list = symbols MarcoFlow tagged assetClass='etf'. Not deployable through mask(df)
    (the live frame carries no symbol).
  * candlestick heat component is 0 in the lab port, so |heat| differs slightly from MarcoFlow's.
Educational only - not financial advice."""
from __future__ import annotations

import numpy as np

NON_DEPLOYABLE_FAMILIES = {"regime", "asset"}


def _w(lo, hi):
    return ("tod", lo, hi)


# key -> (family, kind, params, step)
# kinds: gt/lt (col, thr), band (col, lo, hi), win (lo, hi in hhmm minutes as tod), side-aligned variants
CAT = {
    "dir-long": ("direction", "dir", 1, None),
    "dir-short": ("direction", "dir", -1, None),
    "heat-40": ("heat", "absheat", 40, 5), "heat-50": ("heat", "absheat", 50, 5),
    "heat-60": ("heat", "absheat", 60, 5), "heat-70": ("heat", "absheat", 70, 5),
    "slot-open": ("session", "win", (930, 1100), 15), "slot-midday": ("session", "win", (1100, 1400), 15),
    "slot-power": ("session", "win", (1400, 1600), 15),
    "open-first10": ("session", "win", (930, 940), 5), "open-after10": ("session", "win", (940, 1100), 15),
    "open-after20": ("session", "win", (950, 1100), 15), "slot-earlypm": ("session", "win", (1300, 1400), 15),
    "open-first15": ("session", "win", (930, 945), 5), "open-945-1030": ("session", "win", (945, 1030), 15),
    "open-1030-11": ("session", "win", (1030, 1100), 15), "open-after15": ("session", "win", (945, 1100), 15),
    "slot-latemorning": ("session", "win", (1100, 1200), 15), "slot-lunch": ("session", "win", (1200, 1300), 15),
    "slot-midafternoon": ("session", "win", (1400, 1500), 15), "slot-close": ("session", "win", (1500, 1600), 15),
    "reg-bull": ("regime", "regime", "bull", None), "reg-bear": ("regime", "regime", "bear", None),
    "reg-neutral": ("regime", "regime", "neutral", None),
    "asset-stock": ("asset", "asset", "stock", None), "asset-etf": ("asset", "asset", "etf", None),
    "rsi-os": ("rsi", "lt", ("rsi", 35), 5), "rsi-mid": ("rsi", "band", ("rsi", 35, 65), 5),
    "rsi-ob": ("rsi", "gt", ("rsi", 65), 5), "rsi-deep-os": ("rsi", "lt", ("rsi", 25), 5),
    "rsi-dip": ("rsi", "band", ("rsi", 25, 45), 5), "rsi-mid-low": ("rsi", "band", ("rsi", 45, 55), 5),
    "rsi-mid-high": ("rsi", "band", ("rsi", 55, 65), 5),
    "vol-surge": ("volume", "gt", ("volumeSurge", 1.5), 0.25), "vol-high": ("volume", "gt", ("volumeRatio", 1.3), 0.2),
    "vol-thin": ("volume", "lt", ("volumeRatio", 0.7), 0.1),
    "flow-buy": ("flow", "gt", ("buyPressure", 0.25), 0.1), "flow-sell": ("flow", "lt", ("buyPressure", -0.25), 0.1),
    "flow-aligned": ("flow", "aligned_gt", ("buyPressure", 0.15), 0.1),
    "vwap-above": ("vwap", "gt", ("vwapDistPct", 0.05), 0.1), "vwap-below": ("vwap", "lt", ("vwapDistPct", -0.05), 0.1),
    "vwap-aligned": ("vwap", "aligned_gt", ("vwapDistPct", 0.05), 0.1),
    "mom-rising": ("momentum", "gt", ("rsiSlope", 1.0), 1.0), "mom-falling": ("momentum", "lt", ("rsiSlope", -1.0), 1.0),
    "mom-aligned": ("momentum", "aligned_gt", ("rsiSlope", 1.0), 1.0),
    "atr-calm": ("volatility", "lt", ("atrPct", 0.3), 0.1), "atr-mid": ("volatility", "band", ("atrPct", 0.3, 0.7), 0.1),
    "atr-wild": ("volatility", "gt", ("atrPct", 0.7), 0.1),
    "vwap-reclaim": ("reclaim", "eq", ("vwapReclaim", 1), None), "vwap-lost": ("reclaim", "eq", ("vwapReclaim", -1), None),
    "vwap-cross-aligned": ("reclaim", "aligned_eq", ("vwapReclaim", 1), None),
    "rsi5-low": ("rsi5", "lt", ("rsi5", 30), 5), "rsi5-mid": ("rsi5", "band", ("rsi5", 30, 70), 5),
    "rsi5-high": ("rsi5", "gt", ("rsi5", 70), 5),
    "rsi-diverge-bull": ("rsi-diverge", "div", ("bull", 35, 40), 5), "rsi-diverge-bear": ("rsi-diverge", "div", ("bear", 65, 60), 5),
    "rsi-diverge-aligned": ("rsi-diverge", "div", ("aligned", 35, 40), 5),
}


def _hhmm_add(t, m):
    mins = (t // 100) * 60 + t % 100 + m
    return (mins // 60) * 100 + mins % 60


def cond_mask(df, key, side, shift=0, extra=None):
    """Boolean mask for condition `key` traded on `side` (+1 long/-1 short). `shift` = neighbour step
    (-1, 0, +1) applied to the condition's threshold(s). `extra` holds regime/asset arrays."""
    fam, kind, p, step = CAT[key]
    s = shift * (step or 0)
    if kind == "dir":
        return np.full(len(df), p == side)
    if kind == "absheat":
        return np.abs(df["heat"].to_numpy()) >= p + s
    if kind == "win":
        lo, hi = p
        lo, hi = _hhmm_add(lo, s), _hhmm_add(hi, s)
        tod = df["tod"].to_numpy()
        return (tod >= lo) & (tod < hi)
    if kind == "regime":
        return extra["regime"] == p
    if kind == "asset":
        return extra["is_etf"] if p == "etf" else ~extra["is_etf"]
    if kind == "gt":
        col, thr = p
        return df[col].to_numpy() > thr + s
    if kind == "lt":
        col, thr = p
        return df[col].to_numpy() < thr + s
    if kind == "band":
        col, lo, hi = p
        x = df[col].to_numpy()
        if key in ("rsi-dip", "rsi-mid-low", "atr-mid"):      # MarcoFlow: lo <= x < hi
            return (x >= lo + s) & (x < hi + s)
        return (x >= lo + s) & (x <= hi + s)                 # rsi-mid, rsi-mid-high, rsi5-mid: inclusive
    if kind == "aligned_gt":
        col, thr = p
        x = df[col].to_numpy() * side
        return x > thr + s
    if kind == "eq":
        col, v = p
        return df[col].to_numpy() == v
    if kind == "aligned_eq":
        col, v = p
        return df[col].to_numpy() == v * side
    if kind == "div":
        which, a, b = p
        rsi, r5 = df["rsi"].to_numpy(), df["rsi5"].to_numpy()
        bull = (rsi < 35 + s) & (r5 > 40 + s)
        bear = (rsi > 65 - s) & (r5 < 60 - s)
        if which == "bull":
            return bull
        if which == "bear":
            return bear
        return bull if side == 1 else bear
    raise KeyError(key)


def stack_sides(keys):
    if "dir-long" in keys:
        return [1]
    if "dir-short" in keys:
        return [-1]
    return [1, -1]


def stack_mask(df, keys, side, extra, heat_floor=30.0, shifts=None):
    sh = shifts or {}
    h = df["heat"].to_numpy()
    m = (h * side) >= heat_floor
    for k in keys:
        m &= cond_mask(df, k, side, sh.get(k, 0), extra)
    return m


def deployable(keys):
    return all(CAT[k][0] not in NON_DEPLOYABLE_FAMILIES for k in keys)
