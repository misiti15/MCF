"""pod-smb-not-in-play-quiet-vwap-snap-long - Not-in-play stock on a quiet day: snap back to VWAP (LONG).

Source: SMB Training 'Finding good setups in a quiet tape' + SMB 'Opening Drive (UA)' post (only in-play stocks trend).
URL: https://www.smbtraining.com/blog/the-opening-drive-play-ua

VARIANT of R03 VWAP fade (failed), CWT13 VWAP-stretch fade (cwt-b-b2, failed) and Testing 2 'Stretched Below VWAP
Bounce'. Stated change: two gates together - the stock is NOT in play and the market is quiet.

Pre-declared reading (no tuning): the stretch (rsi5 <= 25) is allowed on the trigger bar or the bar before it, because
the trigger bar must close above the previous close; the 0.35 ATR VWAP stretch is checked on the trigger bar itself (so
the VWAP target still has room). Exit: the structural form of the idea (stop LOD - 0.02 x daily ATR, target VWAP).

Rules (plain English), decision bar i:
  1. Not in play: |gap| <= 0.75%, volumeSurge <= 1.0, volumeRatio <= 1.2.
  2. Quiet market: |spy_fo| <= 0.30%, breadth between 0.40 and 0.60.
  3. Stretch: close_i >= 0.35 x daily ATR below the session VWAP; rsi5 <= 25 on bar i or bar i-1.
  4. Trigger: close_i > close_{i-1} with lower_wick_i >= 0.3.
  Entry: close_i, bar close 10:30-14:30, one per symbol-day. Stop (GEOM S): low of day - 0.02 x daily ATR (low of day
  = close - dist_lod_atr x atr_d). Target: VWAP at entry. Flat 15:55. Costs in (scorer). The scorer's by_regime splits
  Quiet vs the other regimes.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["|gap| <= 0.75%, volumeSurge <= 1.0, volumeRatio <= 1.2", "|spy_fo| <= 0.30%, 0.40 <= breadth <= 0.60",
          "close >= 0.35 ATR below VWAP, rsi5 <= 25 (bar i or i-1)", "close > prior close, lower_wick >= 0.3",
          "stop LOD - 0.02 ATR, target VWAP", "10:30-14:30 ET"]

_STASH = {}


def _prev(x, df):
    key = pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    p = np.r_[np.nan, x[:-1]]
    p[np.r_[True, key[1:] != key[:-1]]] = np.nan
    return p


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df or "breadth" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, a = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + f("vwapDistPct") / 100)
        lod = c - f("dist_lod_atr") * a
        r5 = f("rsi5")
        br = f("breadth")
        m = (np.abs(f("gap")) <= 0.75) & (f("volumeSurge") <= 1.0) & (f("volumeRatio") <= 1.2)
        m &= (np.abs(f("spy_fo")) <= 0.30) & (br >= 0.40) & (br <= 0.60)
        m &= (vw - c) >= 0.35 * a
        m &= (r5 <= 25) | (_prev(r5, df) <= 25)
        m &= (c > _prev(c, df)) & (f("lower_wick") >= 0.3)
        tod = df["tod"].to_numpy(float)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (a > 0)
        sp = lod - 0.02 * a
        m &= (sp < c) & (vw > c)
    return np.asarray(m, bool), sp, vw


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
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
