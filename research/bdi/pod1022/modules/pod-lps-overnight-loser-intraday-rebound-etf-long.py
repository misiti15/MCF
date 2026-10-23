"""pod-lps-overnight-loser-intraday-rebound-etf-long - Cross-period reversal: chronic overnight losers rebound intraday
(ETFs / large caps).

Source: Lou, Polk & Skouras (JFE 2019) offsetting cross-period reversal; QuantReturns 'Overnight Mean-Reversion' (buy
low past overnight return, hold the next intraday session).
URL: https://quantreturns.substack.com/p/overnight-mean-reversion

NEW feature family (history of the gap column). Not pod-chan-buy-on-gap-etf-idio (a single-day gap trigger): here the
signal is the 20-day CUMULATIVE overnight return.

Rules (long). Universe: the 15-ETF list (SPY QQQ IWM DIA XLF XLK XLE XLV XLI XLY XLP XLU SMH XBI KRE) plus stocks with
adv20 >= $200M (as of D-1).
  1) Sum of the prior 20 sessions' overnight gaps (open / prior close - 1, %, D-20..D-1) is in the bottom quintile of
     that universe on the day (rank per date from D-1 values only).
  2) Today's gap <= +0.2% (no relief gap already).
  3) Bar closing 10:00-11:30: close > VWAP (vwapDistPct > 0) and fromOpen > 0.
  4) breadth >= 0.45.
Entry: first qualifying bar's close. Stop: low of day so far - 0.05 x atr_d (GEOM S); hold to 15:55, no target.
Costs per config/default.yaml (scorer). No tweak made.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r35_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1130)
CONTEXT = ["breadth"]


def mask(df) -> np.ndarray:
    if "breadth" not in df or len(df) == 0:
        return np.zeros(len(df), dtype=bool)
    k = U.key(df)
    d = U.map_daily(df, k, ["gap20_pct", "adv_1"])
    sym = df["symbol"].astype(str).to_numpy()
    uni = np.isin(sym, U.ETF15) | (d["adv_1"] >= 200e6)
    tod = df["tod"].to_numpy(np.int64)
    with np.errstate(invalid="ignore"):
        m = uni & (d["gap20_pct"] <= 0.2)
        m &= U.f(df, "gap") <= 0.2
        m &= (U.f(df, "vwapDistPct") > 0) & (U.f(df, "fromOpen") > 0)
        m &= U.f(df, "breadth") >= 0.45
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    c = float(f["close"].iat[i])
    atr = float(f["atr_d"].iat[i])
    lod = c - float(f["dist_lod_atr"].iat[i]) * atr
    return lod - 0.05 * atr
