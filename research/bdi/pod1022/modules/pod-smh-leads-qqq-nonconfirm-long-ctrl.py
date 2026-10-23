"""pod-smh-leads-qqq-nonconfirm-long-ctrl - CONTROL (pre-declared): the same entry rules without the SMH leg (conditions 1-2).
highs (continuation LONG of the laggard).

Source: MarketGauge, 'SMH's Trading on Volume, and Back To Lead?' (semis lead or warn the broad market; SMH-vs-QQQ
divergence as the tell). Anecdotal (no quantified test): treated as a hypothesis.
URL: https://marketgauge.com/uncategorized/smhs-trading-on-volume-and-back-to-lead/

VARIANT of pod-hill-iwm-leads-reversal-long. Stated change: the leader is semis (SMH), not small caps, and it is a
continuation trigger in an up tape (SMH confirms a new HOD that QQQ has not matched yet); the parent is a reversal
after SPY is down >= 0.5%.
Rules (plain English, LONG). Traded: QQQ, XLK; the mask also sees SMH rows.
  1. SMH's bar high is at the session high so far (high >= running HOD from the frame, i.e. dist to HOD at the bar
     high is 0) and SMH close > SMH session VWAP.
  2. SMH fromOpen - QQQ fromOpen (qqq_fo) >= +0.30% (semis leading).
  3. The traded ETF is above its session VWAP but dist_hod_atr >= 0.15 (it has not made the new high yet).
  4. spy_fo > 0.
  Entry: the traded ETF's bar close, first such bar 10:30-14:00, one per symbol-day. Stop (GEOM S): the traded
  ETF's lowest low of the prior 6 bars - 0.05 x atr_d. Target: its session HOD + 0.25 x atr_d, else flat 15:55.
Pre-declared configurations (2): this main; -ctrl (the same entry rules without conditions 1-2, the SMH leg).
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r38_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1400)
TRADED = ["QQQ", "XLK"]
SYMBOLS = ["QQQ", "XLK", "SMH"]
CONTEXT = ["spy_fo", "qqq_fo"]
USE_SMH = False
LAYERS = ["SMH bar high at a new HOD, SMH > VWAP", "SMH fromOpen - QQQ fromOpen >= +0.30%",
          "traded ETF > VWAP, dist_hod_atr >= 0.15", "spy_fo > 0", "10:30-14:00",
          "stop prior-6-bar low - 0.05 ATR, target HOD + 0.25 ATR"]
_ST = {}


def _compute(df):
    n = len(df)
    nanv = np.full(n, np.nan)
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool), nanv, nanv
    b = U.base(df)
    k = U.key(df)
    c, atr, tod = b["c"], b["atr"], b["tod"]
    with np.errstate(invalid="ignore"):
        lo6 = np.max(np.vstack([np.isnan(U.lag(b["l"], k, j)) for j in range(1, 7)]), axis=0)
        low6 = np.min(np.vstack([U.lag(b["l"], k, j) for j in range(1, 7)]), axis=0)
        low6[lo6] = np.nan
        m = np.isin(df["symbol"].astype(str).to_numpy(), TRADED)
        if USE_SMH:
            s = U.rows_at(df, "SMH", ["high", "close", "dist_hod_atr", "atr_d", "vwapDistPct", "fromOpen"])
            shod = s["close"] + s["dist_hod_atr"] * s["atr_d"]
            m &= s["high"] >= shod - 1e-9 * s["close"]
            m &= s["vwapDistPct"] > 0
            qfo = U.f(df, "qqq_fo")
            if not np.isfinite(qfo).any():
                qfo = U.rows_at(df, "QQQ", ["fromOpen"])["fromOpen"]
            m &= (s["fromOpen"] - qfo) >= 0.30
        m &= (U.f(df, "vwapDistPct") > 0) & (U.f(df, "dist_hod_atr") >= 0.15)
        m &= U.f(df, "spy_fo") > 0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
        stop = low6 - 0.05 * atr
        tgt = b["hod"] + 0.25 * atr
    return np.asarray(m, bool), stop, tgt


def mask(df):
    m, s, t = _compute(df)
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


def target_price(f, i, stop):
    return float(_get(f)[1][i])
