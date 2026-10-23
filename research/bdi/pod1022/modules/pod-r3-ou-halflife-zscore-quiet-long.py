"""pod-r3-ou-halflife-zscore-quiet-long - OU half-life gated z-score dip on quiet days, exit at the rolling mean
(LONG).

Source: QuantPy-style stat-arb video theme (OU / half-life); the specific QuantPy video was not located. Rule source:
RC Tools 'Mean-Reversion Half-Life' (TradingView) and the Hudson & Thames ArbitrageLab half-life method.
URL: https://www.tradingview.com/script/37cMMsU1-Mean-Reversion-Half-Life-RC-Tools/

Variant of pod-quantpy-variance-ratio-chop-fade-long: the regime test is a per-stock fitted OU half-life (not a
variance ratio), entry is a z-score threshold, and the exit is a limit at the fitted mean (not an R target).
Rules (plain English), per symbol on the last 48 5m bars (spanning the sessions in the frame):
  Regress d(log close) on lagged log close (47 pairs); require beta < 0; half-life HL = -ln2 / beta.
  1. 3 <= HL <= 10 bars.
  2. z = (close - SMA24) / std24 <= -2.0.
  3. Quiet market: |spy_fo| <= 0.4 and 0.35 <= breadth <= 0.65.
  4. |sma20_slope_pct| <= 0.15.
  5. Not a fresh breakdown: lower_wick >= 0.3 OR rsi5 above the prior bar's rsi5.
  Window 10:30-14:45. Entry at close. Stop (GEOM S): entry - 1.5 x std24 (z = -3.5). Target: SMA24 at entry.
  Otherwise flat 15:55. Scorer control: hold.
Harness notes (pre-declared): ONE configuration tried (HL bucket 3-10 as stated; no other half-life buckets run).
std24 is the sample std (ddof 1). No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r28_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1445)
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["OU half-life 3..10 bars (48-bar AR(1), beta < 0)", "z(close vs SMA24/std24) <= -2",
          "|spy_fo| <= 0.4, breadth 0.35..0.65", "|sma20_slope_pct| <= 0.15", "lower_wick >= 0.3 or rsi5 rising",
          "10:30-14:45", "stop entry - 1.5 std24, target SMA24"]
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
    if not U.ctx_ok(df, ["spy_fo", "breadth"]):
        _ST[id(df)] = (np.full(n, np.nan), np.full(n, np.nan))
        return np.zeros(n, bool)
    c = U.f(df, "close")
    sk = U.symkey(df)
    dk = U.daykey(df)
    with np.errstate(invalid="ignore", divide="ignore"):
        lc = np.log(c)
        beta = U.ar1_beta(lc, U.start(sk), 48)
        hl = np.where(beta < 0, -np.log(2.0) / beta, np.nan)
    sma = U.roll_mean(c, sk, 24)
    sd = U.roll_std(c, sk, 24)
    tod = df["tod"].to_numpy(float)
    br = U.f(df, "breadth")
    r5 = U.f(df, "rsi5")
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (c - sma) / sd
        m = (hl >= 3) & (hl <= 10)
        m &= z <= -2.0
        m &= (np.abs(U.f(df, "spy_fo")) <= 0.4) & (br >= 0.35) & (br <= 0.65)
        m &= np.abs(U.f(df, "sma20_slope_pct")) <= 0.15
        m &= (U.f(df, "lower_wick") >= 0.3) | (r5 > U.lag(r5, dk, 1))
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (c - 1.5 * sd, sma)
    return np.asarray(m, bool)
