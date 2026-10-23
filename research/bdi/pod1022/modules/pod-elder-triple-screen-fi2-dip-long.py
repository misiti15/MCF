"""pod-elder-triple-screen-fi2-dip-long - Elder triple screen: 30m impulse up + 5m Force Index(2) dip, buy-stop over
the prior bar (LONG).

Source: Alexander Elder, 'Trading for a Living' / Triple Screen (Force Index and Impulse System as summarized by
LuxAlgo and TC2000).
URL: https://www.luxalgo.com/library/concept/force-index/

VARIANT of pod-r3-elder-ray-bearpower-hook-long. What changes: the trigger is the volume-weighted Force Index (not
Bear Power) and the trend screen is the 30m Elder Impulse colour.
Rules (plain English, LONG; 5m bars 09:35..15:00 with volume, EMAs carried across sessions of the same symbol):
  Screen 1 (at the entry bar): the last COMPLETED 30m bar (5m closes at :00 / :30) has EMA13(30m) above the previous
    30m bar's EMA13, and the MACD(12,26,9) histogram on 30m closes did not fall on the last 30m bar or on the one
    before it (impulse green, or blue right after green). SPY's daily close yesterday > SPY's daily EMA21 yesterday.
  Screen 2: FI2 = EMA2((close - prev close) x volume) on 5m. A run of 1-3 consecutive bars with FI2 < 0 (a 4th bar
    disarms) whose bars close above EMA13(5m) - 0.5 x ATR5m(14) and above session VWAP arms a buy-stop.
  Screen 3: buy-stop 1 tick ($0.01) over the high of the last FI2 < 0 bar, valid for the next 3 bars; each new FI2 < 0
    bar that qualifies re-arms it at its own high. Fill = the first bar whose high reaches the trigger AND closes above
    it (the harness enters at the bar close).
  Entry window (bar close) 10:15-14:30 ET. Stop (GEOM S+x): the lowest low of the FI2 < 0 run - 0.05 x ATR5m(14).
  Target 1.5R. Exit at the close of the first 5m bar closing below EMA13(5m) once the trade has traded +0.5R; flat
  15:55. Universe: adv20 >= $200M (liquid large caps; SPY / QQQ included) - pre-declared, not tuned.
Harness notes (pre-declared): the 30m series uses the 10:00..15:00 half-hour closes (the 15:30 / 16:00 bars are not in
the 5m cache); the bar open is not stored, so 'prev close' is used for the change. No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used for the entry.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r311_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
WINDOW = (1015, 1430)
MIN_ADV = 200e6
LAYERS = ["30m impulse green / blue-after-green (EMA13 up, MACD hist slope >= 0 in last two 30m bars)",
          "SPY D-1 close > D-1 daily EMA21", "FI2 < 0 run of 1-3 bars, close > EMA13 - 0.5 ATR5 and > VWAP",
          "buy-stop 1c over last FI2<0 bar high, valid 3 bars, close above trigger", "10:15-14:30",
          "stop run low - 0.05 ATR5, target 1.5R, exit close < EMA13 after +0.5R, flat 15:55"]
_S = U.Stash()


@numba.njit(cache=False)
def _kern(nd, tod, o, h, l, c, v, atr, spyok):
    n = len(c)
    m = np.zeros(n)
    s = np.full(n, np.nan)
    t = np.full(n, np.nan)
    xt = np.full(n, np.nan)
    e13 = np.full(n, np.nan)
    a5 = np.full(n, np.nan)
    vw = np.full(n, np.nan)
    fi2 = np.full(n, np.nan)
    imp = np.zeros(n)
    # pass 1: indicators
    ce = np.nan
    ca = np.nan
    cf = np.nan
    na = 0
    trs = 0.0
    pv = 0.0
    vv = 0.0
    e30 = np.nan
    e30p = np.nan
    m12 = np.nan
    m26 = np.nan
    sg = np.nan
    hi = np.nan
    hip = np.nan
    hipp = np.nan
    n30 = 0
    for i in range(n):
        if nd[i] == 2:
            ce = np.nan
            ca = np.nan
            cf = np.nan
            na = 0
            trs = 0.0
            e30 = np.nan
            e30p = np.nan
            m12 = np.nan
            m26 = np.nan
            sg = np.nan
            hi = np.nan
            hip = np.nan
            hipp = np.nan
            n30 = 0
        if nd[i] >= 1:
            pv = 0.0
            vv = 0.0
        pc = c[i - 1] if (i > 0 and nd[i] != 2) else np.nan
        tr = h[i] - l[i]
        if pc == pc:
            tr = max(tr, abs(h[i] - pc), abs(l[i] - pc))
        if na < 14:
            trs += tr
            na += 1
            if na == 14:
                ca = trs / 14.0
        else:
            ca = (ca * 13.0 + tr) / 14.0
        a5[i] = ca
        ce = c[i] if ce != ce else ce + (c[i] - ce) * (2.0 / 14.0)
        e13[i] = ce
        fi = (c[i] - pc) * v[i] if pc == pc else 0.0
        cf = fi if cf != cf else cf + (fi - cf) * (2.0 / 3.0)
        fi2[i] = cf
        tp = (h[i] + l[i] + c[i]) / 3.0
        pv += tp * v[i]
        vv += v[i]
        vw[i] = pv / vv if vv > 0 else np.nan
        mm = tod[i] % 100
        if mm == 0 or mm == 30:
            e30p = e30
            e30 = c[i] if e30 != e30 else e30 + (c[i] - e30) * (2.0 / 14.0)
            m12 = c[i] if m12 != m12 else m12 + (c[i] - m12) * (2.0 / 13.0)
            m26 = c[i] if m26 != m26 else m26 + (c[i] - m26) * (2.0 / 27.0)
            mac = m12 - m26
            sg = mac if sg != sg else sg + (mac - sg) * (2.0 / 10.0)
            hipp = hip
            hip = hi
            hi = mac - sg
            n30 += 1
        if n30 >= 40 and e30 > e30p and ((hi - hip) >= 0 or (hip - hipp) >= 0):
            imp[i] = 1.0
    # pass 2: dip / buy-stop state machine (per symbol-day)
    armed = False
    trig = 0.0
    slv = 0.0
    exp_ = 0
    run = 0
    rlow = 0.0
    for i in range(n):
        if nd[i] >= 1:
            armed = False
            run = 0
        if armed and i > exp_:
            armed = False
        # fill check first (the trigger was armed on an earlier bar)
        if armed and h[i] >= trig and c[i] > trig and tod[i] >= 1015 and tod[i] <= 1430 and imp[i] == 1.0 \
                and spyok[i] == 1.0 and slv < c[i]:
            m[i] = 1.0
            s[i] = slv
            R = c[i] - slv
            t[i] = c[i] + 1.5 * R
            reached = False
            j = i + 1
            while j < n and nd[j] == 0:
                if h[j] >= c[i] + 0.5 * R:
                    reached = True
                if reached and c[j] < e13[j]:
                    xt[i] = tod[j]
                    break
                j += 1
            armed = False
        # arm / re-arm on this bar
        if fi2[i] == fi2[i] and fi2[i] < 0:
            if run == 0:
                rlow = l[i]
            else:
                rlow = min(rlow, l[i])
            run += 1
            ok = (run <= 3) and (a5[i] == a5[i]) and (vw[i] == vw[i]) and (c[i] > e13[i] - 0.5 * a5[i]) \
                and (c[i] > vw[i])
            if ok:
                armed = True
                trig = h[i] + 0.01
                slv = rlow - 0.05 * a5[i]
                exp_ = i + 3
            else:
                armed = False
        else:
            run = 0
    return m, s, t, xt


def mask(df) -> np.ndarray:
    n = len(df)
    sp = U.daily_of("SPY", ["c1", "e211"])
    sp["ok"] = (sp["c1"] > sp["e211"]).astype(float)

    def ex(X):
        return np.nan_to_num(U.map_date(X, sp, ["ok"])["ok"])

    r = U.run_kernel(df, _kern, extra=(ex,), cols=("m", "s", "t", "xt"))
    _S.put(df, s=r["s"], t=r["t"], xt=r["xt"])
    if not n:
        return np.zeros(0, bool)
    tod = df["tod"].to_numpy(np.int64)
    return np.asarray(r["m"] & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)


def stop_price(f, i):
    return float(_S.get(f, "s", mask)[i])


def target_price(f, i, stop):
    return float(_S.get(f, "t", mask)[i])


def exit_index(f, i, stop, target):
    return U.exit_from_tod(f, i, float(_S.get(f, "xt", mask)[i]))
