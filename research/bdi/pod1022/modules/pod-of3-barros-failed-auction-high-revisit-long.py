"""pod-of3-barros-failed-auction-high-revisit-long - Unrepaired failed-auction high from the last 1-5 sessions as a
magnet: buy the VWAP reclaim below it (LONG).

Source: Ray Barros via marketcalls.in ('failed auction zone is expected to be revisited within 5 days') and the
NexusFi failed-auction article (one trader's manual Nifty test: ~74% revisited within 5 days, unverified).
URL: https://nexusfi.com/a/concepts/failed-auction

VARIANT of pod-dante-poor-high-magnet-trend-long. Stated changes: the magnet is a Barros failed-auction HIGH from any
of the last 1-5 completed sessions (not only D-1's poor high), and the entry is a VWAP reclaim, not a pullback hold.
Rules (plain English, LONG):
  1. Zone Z: in one of the last 5 completed sessions, price broke above that session's IB high (09:30-10:30) after
     10:30 by >= 0.05 x atr_d, closed back below the IB high within 6 bars of the excursion's first bar, and that
     excursion's high was the session high; Z = that session high. Z must be untraded since: every later session's
     high < Z and today's high so far < Z. Use the nearest such Z above the current close.
  2. Today: close is 0.4-2.0 x atr_d below Z.
  3. Bar close 10:30-14:00 with vwapReclaim = +1, close > today's open, breadth >= 0.5.
  Entry: close. Stop (GEOM S): LOD - 0.05 x atr_d, capped at 1.0 x the entry-to-Z distance (i.e. the stop is never
  further than entry - (Z - entry)). Target: Z - 0.02 x atr_d. Flat 15:55 (no multi-day hold).
Prior sessions come from completed full-session 5m bars (_r210_util); today's values only from bars up to the
decision bar. No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1400)
CONTEXT = ["breadth"]
LAYERS = ["failed-auction high Z in last 5 sessions, untraded since", "close 0.4-2.0 ATR below nearest Z",
          "vwapReclaim +1, close > open, breadth >= 0.5", "stop LOD - 0.05 ATR capped at 1x dist to Z, target Z - 0.02 ATR"]

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r210_util as U  # noqa: E402

_ST = {}


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i])


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n or "breadth" not in df:
        return np.zeros(n, bool)
    b = U.base(df)
    k = U.key(df)
    c, atr, tod = b["c"], b["atr"], b["tod"]
    sess = U.session_table(df).copy()
    cols = []
    for j in range(1, 6):
        for nm, v in U.prior(sess, ["z", "sh"], j).items():
            sess[nm] = v
            cols.append(nm)
    P = U.map_sess(df, k, sess, cols)
    hod = b["hod"]
    best = np.full(n, np.inf)
    later_max = np.full(n, -np.inf)          # max high of sessions after D-j (D-1 .. D-j+1)
    with np.errstate(invalid="ignore"):
        for j in range(1, 6):
            z = P[f"z_{j}"]
            ok = np.isfinite(z) & (z > later_max) & (hod < z) & (z > c)
            best = np.where(ok & (z < best), z, best)
            sh = P[f"sh_{j}"]
            later_max = np.where(np.isfinite(sh), np.maximum(later_max, sh), np.nan)   # missing session -> stop
        Z = np.where(np.isfinite(best), best, np.nan)
        d = Z - c
        m = (d >= 0.4 * atr) & (d <= 2.0 * atr)
        m &= (U.f(df, "vwapReclaim") == 1) & (c > b["opn"]) & (U.f(df, "breadth") >= 0.5)
        stop[:] = np.maximum(b["lod"] - 0.05 * atr, c - d)
        tgt[:] = Z - 0.02 * atr
        m &= (stop < c) & (tgt > c)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
