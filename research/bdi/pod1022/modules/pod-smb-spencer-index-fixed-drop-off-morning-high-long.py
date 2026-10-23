"""pod-smb-spencer-index-fixed-drop-off-morning-high-long - Spencer 'drop of a fixed size off the morning high' index
ETF bounce, uptrend only (LONG).

Source: SMB Capital / Steve Spencer - 'Trade Review: Buying SPY & IWM pull backs' (SMB Training blog): 'buying 40
handles off the morning high will give you a bounce the vast majority of the time'.
URL: https://www.smbtraining.com/blog/trade-review-buying-spy-iwm-pull-backs

VARIANT of pod-chop-etf-oversold-vwap-magnet-long. What changes: the trigger is a fixed drop from the morning high, not
an oscillator; it needs a daily uptrend; the target is a partial retrace.

Universe: SPY, IWM, QQQ.
Rules (plain English):
  1. The session high was set before 11:00: the high of day at the decision bar equals the high of day as of the
     10:55-11:00 bar (no new high after 11:00; the high includes 09:30-09:45).
  2. Daily regime (completed days): D-1 close > SMA50(D-1) and SMA20 rising (SMA20(D-1) > SMA20(D-6)).
  3. Armed when, at a bar closing 10:30-13:30, the bar low is >= 0.75% (about 40 ES points) AND >= 0.6 x daily ATR14
     below the session high.
  4. Entry: the first 5m bar after arming (or the arming bar itself) that closes above the prior bar's high and does
     not make a new session low, by 13:30.
  Stop: session low - 0.1 x ATR14(5m). Target: 40% retrace of the high-to-low drop (session low + 0.4 x (high - low)
  at entry). Exit at the 15:30 bar close if neither is hit (EXIT_TOD, GEOM S+x). Once per symbol per day (scorer).
Tweak: none (thresholds from the source idea). 'SMA20 rising' read as SMA20 above its value 5 sessions earlier
(pre-declared). 1 configuration. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import numba
import numpy as np

import _r33_util as U

SIDE = "long"
GEOM = "S+x"
EXIT_TOD = 1530
WINDOW = (1030, 1330)
SYMBOLS = ["SPY", "IWM", "QQQ"]
LAYERS = ["session high set before 11:00", "D-1 close > SMA50, SMA20 rising",
          "bar low >= 0.75% and >= 0.6 ATR below the session high (10:30-13:30)",
          "close above prior bar high without a new session low",
          "stop LOD - 0.1 ATR5, target 40% retrace, exit 15:30"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, lod, atr, atr5, ok):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not ok[i0]:
            continue
        h11 = np.nan
        armed = False
        for i in range(i0, i1):
            if tod[i] <= 1100:
                h11 = hod[i]
            elif not (hod[i] <= h11 + 1e-9):
                break                                       # new high after 11:00: no longer a morning high
            if tod[i] > 1330:
                break
            a = atr[i]
            if tod[i] >= 1030 and a > 0:
                dd = hod[i] - l[i]
                if dd >= 0.0075 * hod[i] and dd >= 0.6 * a:
                    armed = True
            if armed and i > i0 and c[i] > h[i - 1] and l[i] > lod[i - 1]:
                sp = lod[i] - 0.1 * atr5[i]
                tp = lod[i] + 0.4 * (hod[i] - lod[i])
                if c[i] > sp and tp > c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = tp
                break
    return m, stop, tgt


def mask(df):
    _ST.clear()
    n = len(df)
    if not n:
        return np.zeros(0, bool)
    bb = U.base(df)
    d = U.map_day(df, U.daily_tab(), ["c1", "sma50_1", "sma20_1", "sma20_6"])
    with np.errstate(invalid="ignore"):
        ok = (d["c1"] > d["sma50_1"]) & (d["sma20_1"] > d["sma20_6"])
    m, stop, tgt = _kern(bb["b"], bb["e"], bb["tod"], bb["c"], bb["h"], bb["l"], bb["hod"], bb["lod"], bb["atr"],
                         bb["atr5"], np.asarray(ok, np.bool_))
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
