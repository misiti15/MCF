"""pod-r3-connorsrsi-5m-trendday-dip-long - ConnorsRSI(3,2,100) < 10 dip on an up day, Connors-style exit near the
5m SMA5 (LONG).

Source: Larry Connors, ConnorsRSI; TheRightTrader guide on intraday 3/2/100 settings (rebound from < 10, stop under
the pullback low).
URL: https://therighttrader.com/learn/indicators/connors-rsi

Variant of bdi-rdt-r11-rsi-os (plain RSI oversold, failed): (a) the ConnorsRSI composite; (b) only on up days for
both the stock and the market; (c) a mean-reversion exit near SMA5 instead of an R target.
Rules (plain English):
  CRSI = mean(RSI3 of close, RSI2 of the up/down streak, PercentRank100 of the 1-bar ROC), on 5m bars per symbol,
  with the streak and the 100-bar percent rank spanning the sessions in the frame.
  1. CRSI < 10 on the bar.
  2. Stock fromOpen > 0 and close > PDL (dist_pdl_atr > 0).
  3. Market: spy_fo > 0.1 and breadth >= 0.5.
  4. vwapDistPct between -1.0 and +0.5.
  Window 10:00-14:30. Entry at the bar's close. Stop (GEOM S): min low of the last 4 bars (incl. the entry bar)
  - 0.05 x atr_d. Target: SMA5 at entry + 0.1 x atr5 (atr5 = atrPct x close / 100), the source's 'first close above
  SMA5' approximated as a limit because the harness has no dynamic exit; otherwise flat 15:55. Scorer control: hold.
Harness notes (pre-declared): RSIs are Wilder; the percent rank counts the previous 100 ROC values strictly below
the current one. A signal whose SMA5 target is not above the entry is skipped by the scorer. No tweak used.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r28_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["ConnorsRSI(3,2,100) < 10", "fromOpen > 0 and dist_pdl_atr > 0", "spy_fo > 0.1, breadth >= 0.5",
          "vwapDistPct in [-1.0, 0.5]", "10:00-14:30", "stop 4-bar low - 0.05 ATR, target SMA5 + 0.1 atr5"]
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


def crsi(df):
    c = U.f(df, "close")
    sk = U.symkey(df)
    st = U.start(sk)
    r3 = U.rsi_wilder(c, st, 3)
    r2 = U.rsi_wilder(U.streak(c, st), st, 2)
    with np.errstate(invalid="ignore", divide="ignore"):
        roc = c / U.lag(c, sk, 1) - 1.0
    pr = U.pct_rank(roc, st, 100)
    return (r3 + r2 + pr) / 3.0


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not U.ctx_ok(df, ["spy_fo", "breadth"]):
        _ST[id(df)] = (np.full(n, np.nan), np.full(n, np.nan))
        return np.zeros(n, bool)
    c, l, atr = U.f(df, "close"), U.f(df, "low"), U.f(df, "atr_d")
    sk = U.symkey(df)
    dk = U.daykey(df)
    cr = crsi(df)
    sma5 = U.roll_mean(c, sk, 5)
    lo4 = U.roll_min(l, dk, 4)
    atr5 = U.f(df, "atrPct") * c / 100.0
    tod = df["tod"].to_numpy(float)
    vd = U.f(df, "vwapDistPct")
    with np.errstate(invalid="ignore"):
        m = cr < 10
        m &= (U.f(df, "fromOpen") > 0) & (U.f(df, "dist_pdl_atr") > 0)
        m &= (U.f(df, "spy_fo") > 0.1) & (U.f(df, "breadth") >= 0.5)
        m &= (vd >= -1.0) & (vd <= 0.5)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (lo4 - 0.05 * atr, sma5 + 0.1 * atr5)
    return np.asarray(m, bool)
