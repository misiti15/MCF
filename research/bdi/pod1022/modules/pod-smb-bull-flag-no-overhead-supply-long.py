"""pod-smb-bull-flag-no-overhead-supply-long - SMB bullish flag on a strong open, only when the long-term technicals do
not argue against it (no overhead daily supply) (LONG).

Source: SMB Capital - 'Bull Flag Pattern: How to Effectively Use This Classic Pattern to Profit' (SMB Training
blog / video).
URL: https://www.smbtraining.com/blog/bull-flag-pattern-how-to-effectively-use-this-classic-pattern-to-profit

VARIANT of pod-wt-bull-flag-breakout-or-bailout-long. What changes: a stated daily-structure gate (SMB: only when the
long-term technicals do not argue against it), a window limited to flags right after the open (pole = the first half
hour), and a flag-volume dry-up condition.

Data: 09:30 open, 09:30-10:00 high / low and mean 5m volume from the 1-minute vendor bars (_r24_bars day cache), the
09:30-10:00 relative volume rv1000 (cumulative volume vs the 20 prior sessions, _smbv5_bars dayagg), 5m bar volume
(_r24_bars bars, 09:35-15:00), daily values as of D-1 (_r34_util, completed days). Locked block never read.

Rules (plain English):
  1. Daily (as of D-1): close > SMA50, and either blue sky (D-1 close >= the max high of D-61..D-2) or the 60-day high
     (D-60..D-1) is >= 2 daily ATR above the D-1 close (no nearby overhead supply).
  2. Pole = 09:30-10:00: 10:00 high - 09:30 open >= 0.6 x daily ATR, the 10:00 close above the open, and the
     09:30-10:00 relative volume >= 1.5. Pole length P = 09:30-10:00 high - low.
  3. Flag = the k = 3..8 bars just before the entry bar, all closing after 10:00: flag high - flag low <= 0.4 x P, flag
     high <= the pole high, pole high - flag low <= 0.5 x P, mean flag-bar volume <= 0.6 x the mean 09:30-10:00 bar
     volume, every flag close above session VWAP.
  4. Entry: a 5m close above the flag high with volume >= 1.5 x the flag mean volume, bar close by 11:30.
  Stop: flag low. Target: the nearer of entry + P (measured move) and entry + 2R. Time stop 13:00 (GEOM S+x EXIT_TOD).
Reading (pre-declared): the shortest k that passes is used. Tweak: none. 1 configuration. Costs per config/default.yaml.
Educational only - not financial advice."""
import numba
import numpy as np

import _r24_bars as R24
import _r33_util as U
import _r34_util as D34
import _smbv5_bars as V5

SIDE = "long"
GEOM = "S+x"
EXIT_TOD = 1300
WINDOW = (1020, 1130)
LAYERS = ["D-1 close > SMA50 and (blue sky or 60d high >= 2 ATR above)", "09:30-10:00 rise >= 0.6 ATR, rvol30 >= 1.5",
          "3-8 bar flag after 10:00: range <= 40% pole, retrace <= 50%, vol <= 60% pole, closes > VWAP",
          "close > flag high on >= 1.5x flag volume by 11:30", "stop flag low, target min(pole, 2R), time stop 13:00"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, vw, v, ok, ph, P, pv):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not ok[i0]:
            continue
        done = False
        for i in range(i0, i1):
            if tod[i] > 1130 or done:
                break
            for k in range(3, 9):
                j0 = i - k
                if j0 < i0 or tod[j0] <= 1000:
                    break
                fh = -np.inf
                fl = np.inf
                sv = 0.0
                good = True
                for j in range(j0, i):
                    fh = max(fh, h[j])
                    fl = min(fl, l[j])
                    sv += v[j]
                    if not (c[j] > vw[j]) or not (v[j] == v[j]):
                        good = False
                if not good:
                    continue
                fv = sv / k
                if (fh - fl) <= 0.4 * P[i0] and fh <= ph[i0] and (ph[i0] - fl) <= 0.5 * P[i0] \
                        and fv <= 0.6 * pv[i0] and c[i] > fh and v[i] >= 1.5 * fv:
                    R = c[i] - fl
                    if R > 0:
                        m[i] = True
                        stop[i] = fl
                        tgt[i] = c[i] + min(P[i0], 2.0 * R)
                    done = True
                    break
    return m, stop, tgt


def mask(df):
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    if not n:
        return z
    bb = U.base(df)
    Dd = D34.map_daily(df, ["c1", "sma50_1", "h60_1", "h60_2"])
    Dy = R24.daymap(df, ["o935", "dr_h", "dr_l", "dr_vavg", "c1000"])
    Rv = R24.daymap(df, ["rv1000"], tab=V5.dayagg())
    a = bb["atr"]
    with np.errstate(invalid="ignore"):
        daily_ok = (Dd["c1"] > Dd["sma50_1"]) & ((Dd["c1"] >= Dd["h60_2"]) | (Dd["h60_1"] >= Dd["c1"] + 2 * a))
        pole_ok = ((Dy["dr_h"] - Dy["o935"]) >= 0.6 * a) & (Dy["c1000"] > Dy["o935"]) & (Rv["rv1000"] >= 1.5)
        ok = daily_ok & pole_ok & (Dy["dr_vavg"] > 0)
    v = R24.bars_for(df, ["v"])["v"]
    m, stop, tgt = _kern(bb["b"], bb["e"], bb["tod"], bb["c"], bb["h"], bb["l"], bb["vwap"], v,
                         np.asarray(ok, np.bool_), Dy["dr_h"], Dy["dr_h"] - Dy["dr_l"], Dy["dr_vavg"])
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
