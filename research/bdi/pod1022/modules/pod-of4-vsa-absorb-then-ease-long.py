"""pod-of4-vsa-absorb-then-ease-long - Effort-vs-result 2-bar: high-volume narrow down bar absorbed, then a
low-volume wide up bar (LONG).

Source: VSA effort-vs-result absorption indicator (TradingView 3LKt0yLg) + ProRealCode Volume Spread Analysis IQ
percentile method; Jigsaw absorption concept.
URL: https://my.tradingview.com/script/3LKt0yLg

VARIANT of pod-of-absorption-bar-level / pod-vsa-stopping-volume-no-supply-test-long. Change: no level is required;
the trigger is a 2-bar sequence that needs an 'ease of movement' confirmation bar.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars; a bar's open is
not stored, so open = the previous bar's close - stated proxy). Percentile ranks are over the last 100 5m bars of the
symbol (the series runs across days), the ranked bar included.
  1. Bar A: close <= open or |body| <= 25% of its range; volume pct-rank >= 90; range pct-rank <= 30; A closes
     below the session VWAP (own VWAP from the same bars) or in the lower third of the day's range so far.
  2. Bar B (the next bar, same day): green (close > open), range pct-rank >= 70, volume below the median of the 20
     bars before B, close > high of A.
  3. SPY not down more than 1.0% from its open (spy_fo > -1.0 on bar B).
  Entry: the next bar's open, proxied by B's close (the scorer enters at the signal bar's close). Bar B closes
  10:00-15:00. Stop (GEOM S+x): min(low A, low B) - 0.05 x 5m ATR14 (simple mean of 14 true ranges). Target: the
  nearer of entry + 1.5R and the session VWAP (VWAP only when it is above the entry). Time stop 60 min (MAX_BARS 12).
  One per symbol per day (scorer). Flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r39_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 12
WINDOW = (1000, 1500)
CONTEXT = ["spy_fo"]
LAYERS = ["bar A: down/narrow body, vol rank >= 90, range rank <= 30, below VWAP or lower third",
          "bar B: green, range rank >= 70, vol < 20-bar median, close > high A", "spy_fo > -1.0",
          "stop min low - 0.05 ATR5, target min(1.5R, VWAP), 60 min time stop"]
_ST = {}


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    tg = np.full(n, np.nan)
    s0 = 0
    sp = 0.0
    sv = 0.0
    hod = -np.inf
    lod = np.inf
    vw_prev = np.nan
    hod_prev = np.nan
    lod_prev = np.nan
    rg = h - l
    tr = np.full(n, np.nan)
    for i in range(n):
        if nd[i] == 2:
            s0 = i
        if nd[i] >= 1:
            sp = 0.0
            sv = 0.0
            hod = -np.inf
            lod = np.inf
        tr[i] = rg[i] if i == s0 else max(rg[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        tp = (h[i] + l[i] + c[i]) / 3.0
        if v[i] == v[i]:
            sp += tp * v[i]
            sv += v[i]
        hod = max(hod, h[i])
        lod = min(lod, l[i])
        vw = sp / sv if sv > 0 else np.nan
        # i = bar B, a = bar A (same day, previous bar)
        a = i - 1
        if nd[i] == 0 and a - 99 >= s0 and i - 20 >= s0 and v[a] == v[a] and v[i] == v[i]:
            ra = rg[a]
            okA = ra > 0 and (c[a] <= o[a] or abs(c[a] - o[a]) <= 0.25 * ra)
            if okA:
                okA = (c[a] < vw_prev) or (c[a] <= lod_prev + (hod_prev - lod_prev) / 3.0)
            if okA:
                cv = 0
                cr = 0
                for j in range(a - 99, a + 1):
                    if v[j] <= v[a]:
                        cv += 1
                    if rg[j] <= ra:
                        cr += 1
                okA = cv >= 90 and cr <= 30
            if okA and c[i] > o[i] and c[i] > h[a]:
                cr = 0
                for j in range(i - 99, i + 1):
                    if rg[j] <= rg[i]:
                        cr += 1
                med = np.median(v[i - 20:i])
                atr5 = 0.0
                cnt = 0
                for j in range(i - 13, i + 1):
                    if tr[j] == tr[j]:
                        atr5 += tr[j]
                        cnt += 1
                if cr >= 70 and v[i] < med and cnt == 14:
                    atr5 /= 14.0
                    s = min(l[a], l[i]) - 0.05 * atr5
                    R = c[i] - s
                    if R > 0:
                        t = c[i] + 1.5 * R
                        if vw > c[i] and vw < t:
                            t = vw
                        m[i] = 1.0
                        st[i] = s
                        tg[i] = t
        vw_prev = vw
        hod_prev = hod
        lod_prev = lod
    return m, st, tg


def compute(df):
    r = U.run_kernel(df, _k)
    tod = df["tod"].to_numpy(np.int64)
    m = r["m"] & (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (U.f(df, "spy_fo") > -1.0) & (r["s"] < U.f(df, "close"))
    return m, r["s"], r["t"]


def mask(df):
    m, s, t = compute(df)
    _ST.clear()
    _ST[id(df)] = (s, t)
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
