"""pod-cwt-morad-day5-pdl-zone-long - Fifth-day reversal: after 4 consecutive lower daily lows, buy the intraday
hook near the prior-day low (LONG).

Source: Chat With Traders ep. 37, Futures Trader 71 (Morad), 'Fifth-day reversal bias after four consecutive lower
lows' (local: research/bdi/cwt/catalog.jsonl, family CWT45).
URL: https://chatwithtraders.com/37
VARIANT of the backlog CWT45 test (index streak bias on SPY/QQQ/IWM, buying the close of day 3/4/5). Stated changes:
an intraday entry at the prior-day-low zone, stocks plus ETFs, and a structural stop. Not CWT14-failbrk-pdl: no PDL
break-and-reclaim is required; the gate is the 4-day lower-low streak.

Rules (plain English, LONG):
  Gate: the daily lows of the last 5 completed sessions are strictly falling, L(d-1) < L(d-2) < L(d-3) < L(d-4) <
  L(d-5) (four consecutive lower lows), per symbol from the completed daily bars (research/history2y lib.daily(),
  the same prior-day highs / lows the frame's dist_pdl_atr uses). A look-back that spans a gap in the open table (the
  locked block) is dropped: the 5 sessions must lie within 9 calendar days.
  1. Bar close 10:00-13:30.
  2. dist_pdl_atr between -0.10 and +0.25 (near the prior-day low).
  3. rsi5 between 25 and 50 with rsiSlope > 0 (hooking up).
  4. lower_wick >= 0.40 on the entry bar.
  Universe: the scorer's adv20 >= $20M (stocks plus ETFs). Entry: bar close.
  GEOM S: stop = today's LOD (so far) - 0.05 x atr_d; target = PDL + 0.50 x atr_d (limit); otherwise flat 15:55.
  Costs per config/default.yaml (applied by the scorer). No tweak made.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1330)
LAYERS = ["4 consecutive lower daily lows (last 5 completed sessions)", "dist_pdl_atr in [-0.10, 0.25]",
          "rsi5 in [25, 50] and rsiSlope > 0", "lower_wick >= 0.40", "10:00-13:30",
          "stop LOD - 0.05 ATR, target PDL + 0.5 ATR, flat 15:55"]
_STASH = {}
_CACHE = {}


def _streak():
    """DataFrame (symbol, date D, ok) where ok = the 5 completed sessions before D have strictly falling lows."""
    if "s" in _CACHE:
        return _CACHE["s"]
    p = str(Path(__file__).resolve().parents[3] / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    d = lib.daily()[["symbol", "date", "low"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)
    L = [g["low"].shift(k) for k in range(5)]                  # L[0] = low of row (as seen after it completes)
    ok = (L[0] < L[1]) & (L[1] < L[2]) & (L[2] < L[3]) & (L[3] < L[4])
    span = (d["date"] - g["date"].shift(4)).dt.days
    ok &= span <= 9
    d["ok"] = ok.astype(float)
    d["next_date"] = g["date"].shift(-1)                        # the row's streak applies to the NEXT session
    d = d[(d["next_date"] - d["date"]).dt.days <= 5]
    out = pd.DataFrame({"symbol": d["symbol"].to_numpy(), "date": d["next_date"].dt.strftime("%Y-%m-%d").to_numpy(),
                        "ok": d["ok"].to_numpy()})
    _CACHE["s"] = out
    return out


def _compute(df):
    n = len(df)
    if not n:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr, tod = f("close"), f("atr_d"), f("tod")
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].astype(str).to_numpy()})
    gate = key.merge(_streak(), on=["symbol", "date"], how="left")["ok"].to_numpy(float) == 1
    with np.errstate(invalid="ignore"):
        dp = f("dist_pdl_atr")
        r5 = f("rsi5")
        m = gate & (dp >= -0.10) & (dp <= 0.25)
        m &= (r5 >= 25) & (r5 <= 50) & (f("rsiSlope") > 0)
        m &= f("lower_wick") >= 0.40
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        lod = c - f("dist_lod_atr") * atr
        pdl = c - dp * atr
        stop = lod - 0.05 * atr
        tgt = pdl + 0.50 * atr
        m &= np.isfinite(stop) & (stop < c) & (tgt > c)
    return np.asarray(m, bool), stop, tgt


def mask(df) -> np.ndarray:
    m, stop, tgt = _compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
