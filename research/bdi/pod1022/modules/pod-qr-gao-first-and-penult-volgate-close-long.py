"""pod-qr-gao-first-and-penult-volgate-close-long - First half-hour and 14:30-15:00 both up, high-volatility regime,
long into the close (LONG).

Source: QuantRocket, 'First Half Hour Predicts Last Half Hour' tutorial (buy SPY when the first and penultimate
half-hour returns are both positive; disabled when VIX < 20), after Gao, Han, Li and Zhou, 'Market Intraday Momentum'.
URL: https://www.quantrocket.com/codeload/first-last/first_last/Introduction.ipynb.html

VARIANT of intraday-momentum-paper (Gao first 30 -> last 30, all days) and pod-gao-newsday-first30-hold-long (news
days, 10:00 entry). Stated changes: the penultimate half hour must agree, a volatility-regime gate as in the
QuantRocket version, and a 15:00 entry (the scorer clips entries to <= 15:00, so the last 'half hour' held is
15:00-15:55). Does NOT require a large prior daily move (vs pod-cwt3-colkitt).

Rules (plain English). Symbols SPY, QQQ.
  1. Return from the prior close to the 10:00 bar close > 0.
  2. Return from the 14:30 bar close to the 15:00 bar close > 0.
  3. Volatility gate: VIXY is not in lib.daily(), so the stated fallback is used - SPY's 10-day average daily range
     (% of close, D-10..D-1) > the median of that 10-day average over the 60 sessions ending D-1 (lib.daily, completed
     days; restarts after the locked block, so the first ~70 sessions after a gap have no signal).
  4. The 15:00 close is above session VWAP.
  Entry: the 15:00 bar close. Stop (GEOM S): entry - 0.15 x daily ATR. No target, flat at 15:55.
Controls (separate modules): ...-ctrl-novol (rules 1, 2, 4 without the gate) and ...-ctrl-short (the mirror short:
both returns negative, close below VWAP, gate on, stop entry + 0.15 ATR).
No tweak used. 1 configuration (+2 controls). Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r39_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1500, 1500)
SYMBOLS = ["SPY", "QQQ"]
LAYERS = ["prior close -> 10:00 close > 0", "14:30 -> 15:00 close > 0",
          "SPY 10d avg range > its 60d median (VIXY fallback)", "15:00 close > VWAP", "stop 0.15 ATR, flat 15:55"]
_ST = {}


def _spy_gate(df):
    t = U.daily_tab()
    s = t[t["symbol"] == "SPY"][["date", "avg10p1", "avg10p_med601"]]
    k = pd.DataFrame({"date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy()})
    m = k.merge(s, on="date", how="left")
    return m["avg10p1"].to_numpy(float) > m["avg10p_med601"].to_numpy(float)


def compute(df, side=1, gate=True):
    n = len(df)
    if not n:
        return np.zeros(0, bool), np.zeros(0)
    b = U.base(df)
    k = U.key(df)
    tod = b["tod"]
    c = b["c"]
    c1000 = U.C3.at_tod(c, k, tod, 1000)
    c1430 = U.C3.at_tod(c, k, tod, 1430)
    with np.errstate(invalid="ignore", divide="ignore"):
        r1 = c1000 / b["pc"] - 1.0
        r2 = c / c1430 - 1.0
        if side == 1:
            m = (r1 > 0) & (r2 > 0) & (c > b["vwap"])
        else:
            m = (r1 < 0) & (r2 < 0) & (c < b["vwap"])
        if gate:
            m &= _spy_gate(df)
        m &= (tod == 1500) & (b["atr"] > 0)
    stop = c - side * 0.15 * b["atr"]
    return np.asarray(m, bool), np.where(m, stop, np.nan)


def mask(df):
    m, s = compute(df, 1, True)
    _ST.clear()
    _ST[id(df)] = s
    return m


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
