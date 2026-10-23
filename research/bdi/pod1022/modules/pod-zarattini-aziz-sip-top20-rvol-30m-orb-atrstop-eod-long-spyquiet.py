"""pod-zarattini-aziz-sip-top20-rvol-30m-orb-atrstop-eod-long-spyquiet - QUIET-INDEX ARM of the Zarattini SIP ORB (adds SPY OR width in its trailing bottom tercile).
Same rules as the all-days module below; only QUIET = True differs.

Source: Zarattini, Barbon & Aziz, 'A Profitable Day Trading Strategy For The U.S. Equity Market' (2024 working paper;
Aziz of Bear Bull Traders / Peak Capital); QuantConnect replication.
URL: https://abarbon.com/papers/a-profitable-day-trading-strategy-for-the-u-s-equity-market

VARIANT of 'ORB on stocks in play: exit re-tests' and orb20_a. Stated change: names picked by a daily cross-sectional
rank instead of a threshold, stop = 10% of daily ATR, exit at the close, long only, and a 30-minute opening range
(research frames start at the 09:50 bar; the 09:30-10:00 values come from the r24 1-minute-built cache).

Rules (plain English):
  1. Universe (completed days): D-1 close > $5, daily ATR14 (as of D-1) > $0.50, 14-day mean share volume >= 1M.
     MIN_ADV = 0 so the scorer does not add its $20M adv20 floor (the paper universe); the scorer's earnings blackout
     still applies (a stated limitation: the paper's in-play names are often earnings names).
  2. At 10:00 rank the universe by rvol_30 = mean 5m volume 09:30-10:00 / the same over the 14 prior sessions; keep
     the top 20 with rvol_30 >= 1 (cross-sectional over the whole 1,227-symbol cache universe that day).
  3. The 09:30-10:00 bar is green (10:00 close > 09:30 open) and not a doji (|close - open| >= 0.1 x OR range).
  4. Entry: the first 5-minute close above the OR high (09:30-10:00 high), bar close 10:05-12:00, one per name per day.
  Stop (GEOM S): entry - 0.10 x atr_d (paper). Exit: 15:55, no target. R = the stop distance (equal-risk).
Arms: this all-days arm; the quiet arm (SPY's 09:30-10:00 range / open in the bottom tercile of its trailing 60
sessions, prior days only) is module ...-spyquiet. The scorer's by_regime gives the hindsight regime split.
No tweak used. Costs per config/default.yaml (scorer; the x1.4 early-entry multiplier hits the 10:05-10:30 entries).
Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r31_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1005, 1200)
MIN_ADV = 0
QUIET = True
LAYERS = ["price > 5, ATR14 > 0.5, ADV14 >= 1M sh", "top-20 rvol_30 rank, rvol_30 >= 1",
          "09:30-10:00 bar green, not doji", "first 5m close above the 30-min OR high 10:05-12:00",
          "stop entry - 0.10 ATR, exit 15:55"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, orh, ok, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not ok[i0]:
            continue
        for i in range(i0, i1):
            if tod[i] <= 1000:
                continue
            if tod[i] > w1:
                break
            if c[i] > orh[i]:
                if tod[i] >= w0:
                    m[i] = True
                break
    return m


def compute(df):
    b = U.base(df)
    k = U.key(df)
    t = U.map_day(df, U.sip_tab(), ["sip", "o935", "dr_h", "dr_l", "c1000", "spy_quiet"])
    with np.errstate(invalid="ignore"):
        body = t["c1000"] - t["o935"]
        ok = (t["sip"] == 1) & (body > 0) & (body >= 0.1 * (t["dr_h"] - t["dr_l"])) & (b["atr"] > 0)
        if QUIET:
            ok &= t["spy_quiet"] == 1
    bb, ee = U.segments(k)
    m = _k(bb, ee, b["tod"], b["c"], t["dr_h"], np.asarray(ok, np.bool_), WINDOW[0], WINDOW[1])
    return m, b["c"] - 0.10 * b["atr"]


def mask(df):
    m, s = compute(df)
    _ST.clear()
    _ST[id(df)] = s
    return m


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
