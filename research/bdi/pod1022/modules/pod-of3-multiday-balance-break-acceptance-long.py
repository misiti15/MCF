"""pod-of3-multiday-balance-break-acceptance-long - Three-day balance breakout with 30-minute time acceptance, buy the
first retest of the balance high (LONG).

Source: auction market theory - initiative moves out of balance that gain acceptance lead to value migration (LuxAlgo
'Responsive vs Initiative Activity'; Dalton balance-to-imbalance), Axia volume-profile teaching on multi-day balance
areas.
URL: https://www.luxalgo.com/library/concept/responsive-vs-initiative-activity.md

VARIANT of pod-of-pdh-time-acceptance (level = PDH, no balance precondition). Stated changes: the level is the
3-session composite high, a multi-day balance precondition is required, and acceptance is followed by a
pullback-and-hold entry.
Rules (plain English, LONG):
  1. Balance: H3 / L3 = high / low of the last 3 completed days (D-1..D-3, daily table); H3 - L3 <= 1.8 x atr_d, and
     each of those days' ranges overlaps the previous day's range by >= 60% of its own range (D-1 vs D-2, D-2 vs
     D-3, D-3 vs D-4).
  2. Today's open <= H3.
  3. Acceptance: after 10:30, 6 consecutive 5m closes above H3 with every one of those bars' lows >= H3 - 0.10 x
     atr_d.
  4. First retest: the first bar after the acceptance run whose low comes within 0.10 x atr_d of H3 (low <= H3 +
     0.10 x atr_d) is the only candidate; it must be a bar close 11:00-14:45 (scorer clips to 15:00 anyway), keep its
     low >= H3 - 0.10 x atr_d, close above H3 with lower_wick >= 0.35 and volumeRatio <= 1.2.
  5. breadth >= 0.5.
  Entry: close. Stop (GEOM S): H3 - 0.25 x atr_d. Target: H3 + 0.5 x (H3 - L3). Flat 15:55.
Reading declared up front: 'each of those days' overlaps the previous day' is read literally (3 pairs, D-3 is
compared with D-4); 'within 0.10 x atr_d of H3' = |low - H3| <= 0.10 x atr_d. No tweak made. Costs per
config/default.yaml (scorer). Daily values come only from completed days; intraday only from bars up to the decision.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1445)
CONTEXT = ["breadth"]
LAYERS = ["3-day balance: H3-L3 <= 1.8 ATR, day overlaps >= 60%", "open <= H3",
          "6 closes above H3 after 10:30, lows >= H3 - 0.1 ATR", "first retest within 0.1 ATR, lower wick >= 0.35, vr <= 1.2",
          "breadth >= 0.5", "stop H3 - 0.25 ATR, target H3 + 0.5 x balance height"]

import sys
from pathlib import Path

import numba
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


@numba.njit(cache=False)
def _scan(st, tod, l, c, H, atr):
    """Per row: True on the first-retest bar after a 6-bar acceptance run above H (after 10:30)."""
    n = len(c)
    sig = np.zeros(n, np.bool_)
    run = 0
    acc = False
    done = False
    prev_i = -1
    for i in range(n):
        if st[i]:
            run = 0
            acc = False
            done = False
            prev_i = -1
        if done or not np.isfinite(H[i]) or not np.isfinite(atr[i]):
            prev_i = i
            continue
        if acc:
            if l[i] <= H[i] + 0.10 * atr[i]:
                sig[i] = True
                done = True
            prev_i = i
            continue
        if tod[i] > 1030:
            if c[i] > H[i] and l[i] >= H[i] - 0.10 * atr[i]:
                run += 1
                if run >= 6:
                    acc = True
            else:
                run = 0
        prev_i = i
    return sig


def _ov(h, l, ph, pl):
    with np.errstate(invalid="ignore", divide="ignore"):
        return (np.minimum(h, ph) - np.maximum(l, pl)) / (h - l)


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
    D = U.map_sess(df, k, U.daily_hl(), ["h1", "l1", "h2", "l2", "h3", "l3", "h4", "l4"])
    H3 = np.maximum(np.maximum(D["h1"], D["h2"]), D["h3"])
    L3 = np.minimum(np.minimum(D["l1"], D["l2"]), D["l3"])
    with np.errstate(invalid="ignore"):
        bal = (H3 - L3 <= 1.8 * atr)
        bal &= _ov(D["h1"], D["l1"], D["h2"], D["l2"]) >= 0.6
        bal &= _ov(D["h2"], D["l2"], D["h3"], D["l3"]) >= 0.6
        bal &= _ov(D["h3"], D["l3"], D["h4"], D["l4"]) >= 0.6
        H = np.where(bal, H3, np.nan)
    sig = _scan(U.start(k), tod, b["l"], c, H, atr)
    with np.errstate(invalid="ignore"):
        m = sig & (b["opn"] <= H3)
        m &= (np.abs(b["l"] - H3) <= 0.10 * atr) & (c > H3)
        m &= (U.f(df, "lower_wick") >= 0.35) & (U.f(df, "volumeRatio") <= 1.2) & (U.f(df, "breadth") >= 0.5)
        stop[:] = H3 - 0.25 * atr
        tgt[:] = H3 + 0.5 * (H3 - L3)
        m &= (stop < c) & (tgt > c)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
