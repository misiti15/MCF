"""pod-trush-chandelier-zlsma-flip-long-flip - COMPANION (pre-declared): exit on the CE flip back to short (GEOM S+x, exit_index).
(5-minute bars, LONG).

Source: 'Chandelier Exit + ZLSMA Strategy' (TradingView open-source script; its author credits a YouTube video,
recommended on 5-minute charts); a popular Trading Rush-style indicator combination test.
URL: https://www.tradingview.com/script/njG2EVJ0-Chandelier-Exit-ZLSMA-Strategy/

NEW indicator family (no chandelier or ZLSMA in the repo).
Indicators per symbol on continuous full-session 5m bars across days (previous open month as warm-up), closed bars
only (the source warns its backtest repainted):
  CE_long = highest high(22) - 3 x ATR(22), CE_short = lowest low(22) + 3 x ATR(22) (Wilder ATR; each line ratchets
  as in the standard TradingView Chandelier Exit: CE_long never falls while the prior close stays above it, CE_short
  never rises while the prior close stays below it). Direction flips to long when close > the prior bar's CE_short,
  to short when close < the prior bar's CE_long.
  ZLSMA(32) = LSMA + (LSMA - LSMA of LSMA), LSMA = 32-bar linear-regression end value.
Rules (plain English, LONG):
  1. The CE direction flips to long on this bar (short on the prior bar).
  2. Close > ZLSMA(32), and ZLSMA > its value 3 bars ago.
  3. breadth >= 0.50 or qqq_vwap > 0 (tape support).
  4. Close above the prior-day close (from_pc > 0).
  Entry: bar close, 10:00-14:30. Stop (GEOM S): the CE_long line on the entry bar. Target: none, flat 15:55.
Pre-declared configurations (3): this main (flat 15:55); -flip (the source's exit: close of the first later bar
where the CE direction flips back to short, GEOM S+x with exit_index; frame bars end at 15:00, so a later flip
holds to 15:55); -bar1 (GEOM S+bar1, the closest available trail). No tweak made.
Costs per config/default.yaml (scorer). Only closed bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r38_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
WINDOW = (1000, 1430)
CONTEXT = ["breadth", "qqq_vwap"]
LAYERS = ["Chandelier Exit (22, 3) flips long", "close > ZLSMA(32), ZLSMA rising over 3 bars",
          "breadth >= 0.50 or qqq_vwap > 0", "close > prior close", "10:00-14:30",
          "stop CE_long line, flat 15:55"]
_ST = {}


def _compute(df):
    n = len(df)
    nanv = np.full(n, np.nan)
    if not n or "breadth" not in df:
        return np.zeros(n, bool), nanv, nanv
    b = U.base(df)
    x = U.ce_zlsma_rows(df)
    c, atr, tod = b["c"], b["atr"], b["tod"]
    qv = U.f(df, "qqq_vwap")
    with np.errstate(invalid="ignore"):
        m = (x["dir"] == 1) & (x["dirp"] == -1)
        m &= (c > x["zl"]) & (x["zl"] > x["zl3"])
        m &= (U.f(df, "breadth") >= 0.50) | (qv > 0)
        m &= c > b["pc"]
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
        stop = x["cel"]
    return np.asarray(m, bool), stop, x["dir"]


def mask(df):
    m, s, d = _compute(df)
    _ST.clear()
    _ST[id(df)] = (s, d, U.key(df))
    return m


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def exit_index(f, i, stop, target):
    """The first later frame row of the same symbol-day where the CE direction is short again (-1 = none)."""
    _, d, k = _get(f)
    j = i + 1
    while j < len(f) and k[j] == k[i]:
        if d[j] == -1:
            return j
        j += 1
    return -1
