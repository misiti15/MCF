"""pod-cwt3-chan-bb-volfloor-quiet-etf-long - Bollinger dip-buy with a volatility-floored band on quiet days (index /
sector ETFs, LONG).

Source: Chat With Traders EP052, Ernie Chan (Bollinger mean reversion with a minimum band width) [~00:39:00].
URL: https://chatwithtraders.com/052

VARIANT, not a copy. Parents: 'Article indicator rules (MACD/BB/...)' faithful BB fade and cwt-b-b2 CWT13
VWAP-stretch fade (both failed). Stated changes: (1) the z-score denominator is floored, z = (close - SMA20) /
max(std20, median of std20 at the same time of day over the previous 20 sessions), so a band set in calm conditions
cannot be too narrow; (2) long only, liquid index / sector ETFs only; (3) a quiet-day gate.

Rules (plain English, LONG, 5-minute bars; SYMBOLS = SPY, QQQ, IWM, DIA and the 11 sector SPDRs):
  SMA20 / std20 (population) on continuous full-session 5m closes (09:35-15:55 bars, across days; frames + head/tail
  table, previous open month as warm-up). Floor = median of std20 at the same bar time over the previous 20 completed
  sessions (today excluded).
  (a) bar close 10:30-14:30 ET;
  (b) quiet day: SPY session range so far (incl. 09:30-09:45) <= 0.6 x SPY daily ATR(14) AND |SPY fromOpen| <= 0.4%;
  (c) z <= -2.0 on the bar close;
  (d) the ETF's daily close yesterday > its daily SMA50 (completed days).
  Entry: the signal bar's close (the scorer's entry; proxy for the next bar open - the alternative 'reclaim' entry is
  not used). Stop (GEOM S): entry - 2 x floored std20 or the session low - 0.05%, whichever is lower (wider).
  Target: SMA20 at entry (z back to 0; fixed limit at the entry-bar SMA20). Flat 15:55.
  Reject if (SMA20 - entry) < 3 x the round-trip cost (config/default.yaml: 1c + 1 bps per side).
Companion: pod-cwt3-chan-bb-volfloor-quiet-etf-long-nofloor.py (same rules with z = (close - SMA20) / std20 and the
stop at 2 x std20), because the guest's point is that the floor cuts the losses on volatility-jump days.
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar and daily values
of completed days are used.
Educational only - not financial advice."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
CONTEXT = ["spy_fo"]
FLOOR = True
Z_ENTRY = -2.0
LAYERS = ["10:30-14:30 ET", "SPY range <= 0.6 SPY ATR14 and |spy_fo| <= 0.4%", "z(floored) <= -2.0",
          "daily close D-1 > SMA50", "stop 2 floored sd or LOD - 0.05%, target SMA20 >= 3x RT cost"]

_ST = {}


def _u():
    n = "_cwt3_bars"
    if n not in sys.modules:
        sp = importlib.util.spec_from_file_location(n, Path(__file__).resolve().parent / "_cwt3_bars.py")
        m = importlib.util.module_from_spec(sp)
        sys.modules[n] = m
        sp.loader.exec_module(m)
    return sys.modules[n]


def _features(df):
    U = _u()
    p = U.full_bars(df, SYMBOLS)
    if p is None or not len(p):
        return None
    g = p.groupby("symbol", sort=False)["c"]
    p["sma"] = g.transform(lambda x: x.rolling(20, min_periods=20).mean())
    p["sd"] = g.transform(lambda x: x.rolling(20, min_periods=20).std(ddof=0))
    p["fl"] = p.groupby(["symbol", "tod"], sort=False)["sd"].transform(
        lambda x: x.shift(1).rolling(20, min_periods=20).median())
    return U.map_rows(df, p, ["sma", "sd", "fl"])


def _compute(df):
    U = _u()
    n = len(df)
    z0 = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if not n or "spy_fo" not in df:
        return z0
    fe = _features(df)
    if fe is None:
        return z0
    b = U.base(df)
    k = U.key(df)
    c, tod = b["c"], b["tod"]
    sym = df["symbol"].astype(str).to_numpy()
    # SPY session range so far vs SPY daily ATR, per (date, tod)
    sp = sym == "SPY"
    if not sp.any():
        return z0
    s = pd.DataFrame({"date": df["date"].to_numpy()[sp], "tod": tod[sp],
                      "srng": (b["hod"] - b["lod"])[sp], "satr": b["atr"][sp]}).drop_duplicates(["date", "tod"])
    m2 = pd.DataFrame({"date": df["date"].to_numpy(), "tod": tod}).merge(s, on=["date", "tod"], how="left")
    srng, satr = m2["srng"].to_numpy(float), m2["satr"].to_numpy(float)
    dl = U.map_daily(df, k, ["d_close_1", "sma50_1"])
    sma, sd, fl = fe["sma"], fe["sd"], fe["fl"]
    with np.errstate(invalid="ignore", divide="ignore"):
        den = np.fmax(sd, fl) if FLOOR else sd
        if FLOOR:
            den = np.where(np.isfinite(fl), den, np.nan)
        z = (c - sma) / den
        m = (tod >= WINDOW[0]) & (tod <= WINDOW[1])                                   # (a)
        m &= (srng <= 0.6 * satr) & (np.abs(U.f(df, "spy_fo")) <= 0.4)                # (b)
        m &= z <= Z_ENTRY                                                             # (c)
        m &= dl["d_close_1"] > dl["sma50_1"]                                          # (d)
        stop = np.fmin(c - 2.0 * den, b["lod"] * (1 - 0.0005))
        tgt = sma
        m &= (tgt - c) >= 3 * U.rt_cost(c, tod)
        m &= np.isfinite(stop) & np.isfinite(tgt) & (stop < c)
    return m, stop, tgt


def mask(df) -> np.ndarray:
    try:
        m, stop, tgt = _compute(df)
    except KeyError:
        n = len(df)
        m, stop, tgt = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


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
