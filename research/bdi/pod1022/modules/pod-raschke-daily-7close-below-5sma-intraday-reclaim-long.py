"""pod-raschke-daily-7close-below-5sma-intraday-reclaim-long - Daily one-sided down run (7+ closes under the daily
5-SMA), buy the intraday reclaim of the 5-SMA level (LONG). Exit A: hold to 15:55.

Source: Linda Raschke 5-SMA / extended-run rule (TradingView 'Linda Raschke 5 SMA Reversal [LuciTech]'; 'Raschke
Trade Sheet (scanner)' extended-run exhaustion); Raschke rule 'best reversals occur in the morning'.
URL: https://kr.tradingview.com/script/8MVLfKu4-Raschke-Trade-Sheet-scanner/

VARIANT of the CWT45 index streak bias (buy the close of the 3rd-5th down close) and pod-cwt-morad-day5-pdl-zone-long.
Stated change: the run is >= 7 closes below the daily SMA5 (not down closes) and the trigger is an intraday reclaim of
today's SMA5 level (not a buy at the close or a PDL zone).

Rules (plain English). Daily values from lib.daily() completed days (as of D-1):
  1. >= 7 consecutive daily closes below the daily SMA5 ending D-1; close(D-1) > daily SMA100 (see tweak); the run's
     drawdown (close before the run started -> close of D-1) <= 15%.
  2. Today, a 5-min bar closing 09:50-11:30 (frames start at the 09:50 bar; the 09:45 close is not seen - stated)
     closes above today's live SMA5 = (closes D-4..D-1 + this close) / 5, and above session VWAP.
  3. Entry at the first such close.
  4. Stop (GEOM S): low of day so far - 0.05 x daily ATR. Exit A (this module): no target, flat 15:55.
     Companions: -t15r (target 1.5R) and -holdtr (GEOM holdtr: stop 1R = 0.25 ATR, 1R trail after +1R).
  Earnings days: the scorer universe removes 4 trading days either side of a report.
ONE pre-declared tweak (data limit, not tuning): the daily SMA200 cannot be computed for most of the open history
(lib.daily starts 2024-10 and resumes 2025-03 after the locked block; series restart after the gap), so the
long-term uptrend gate uses the daily SMA100 instead. 3 configurations (exit A / B / holdtr).
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r37_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1130)
TMULT = 0.0          # 0 = no target (exit A), else target = entry + TMULT x R
RUN = 7
LAYERS = [">= 7 daily closes below daily SMA5 to D-1", "close(D-1) > daily SMA100, run drawdown <= 15%",
          "5m close > live daily SMA5 and > session VWAP, 09:50-11:30",
          "stop LOD - 0.05 ATR, exit A flat 15:55"]
_ST = {}


def compute(df):
    n = len(df)
    if not n:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    b = U.base(df)
    d = U.map_daily(df, ["sma5cnt1", "c1", "sma1001", "prerun1", "sum41"])
    c, a = b["c"], b["atr"]
    with np.errstate(invalid="ignore", divide="ignore"):
        live5 = (d["sum41"] + c) / 5.0
        m = d["sma5cnt1"] >= RUN
        m &= d["c1"] > d["sma1001"]
        m &= (1.0 - d["c1"] / d["prerun1"]) <= 0.15
        m &= (c > live5) & (c > b["vwap"])
        m &= (b["tod"] >= WINDOW[0]) & (b["tod"] <= WINDOW[1])
        stop = b["lod"] - 0.05 * a
        R = c - stop
        m &= (R > 0) & (a > 0)
        tgt = np.where(TMULT > 0, c + TMULT * R, np.nan)
    return np.asarray(m, bool), stop, tgt


def mask(df):
    m, s, t = compute(df)
    _ST.clear()
    _ST[id(df)] = (s, t)
    return m


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_b(f, i, stop):
    return float(_get(f)[1][i])
