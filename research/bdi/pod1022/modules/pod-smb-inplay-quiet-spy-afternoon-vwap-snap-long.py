"""pod-smb-inplay-quiet-spy-afternoon-vwap-snap-long - In-play stock stretched below VWAP on a quiet SPY afternoon
reverts to VWAP (LONG).

Source: SMB Training 'Finding good setups in a quiet tape' plus SMB YouTube in-play lessons (in-play names are the
only ones that move on quiet days). Taken from SMB material already known; the web was unavailable this round.
URL: https://www.youtube.com/@smbcapital

VARIANT of pod-smb-not-in-play-quiet-vwap-snap-long. Stated change: the universe flips to IN-PLAY stocks, there is a
market quiet-day gate, and it runs only in the afternoon.

Values: SPY morning range = SPY (high of day - low of day) at the 12:30 bar close, in SPY daily ATRs = SPY
dist_hod_atr + dist_lod_atr on its 12:30 row (includes 09:30-09:50). Stock rvol at 10:30: the frames hold no raw
volume and no time-of-day rvol, so the pre-declared proxy is the mean volumeRatio of the stock's bars closing
09:50-10:30 (the arena 'rvol_day' proxy) >= 2.0. VWAP = close / (1 + vwapDistPct%). Low of day = close - dist_lod_atr x
atr_d.

Rules (plain English), decision bar i:
  1. Quiet market: SPY 09:30-12:30 range < 0.5 x SPY daily ATR.
  2. In play: rvol proxy at 10:30 >= 2.0.
  3. Stretch: close_{i-1} <= VWAP_{i-1} - 0.5 x daily ATR (pre-declared: on the RSI bar), and VWAP is still above
     close_i (target room).
  4. RSI(5)_{i-1} <= 20, then bar i closes above the prior bar's high.
  Entry: the scorer enters at close_i (= next bar open), bar close 12:30-14:45 ET, one per symbol-day.
  Stop (GEOM S): the tighter of the low of day and entry - 0.4 ATR (= the higher of the two). Target: VWAP at entry.
  The source's 60-minute time stop is not supported by the scorer (it holds to stop, target or 15:55). Costs in.
No tweak used; thresholds are the idea's. Live this needs SPY's day range as context (not yet a context column).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1230, 1445)
LAYERS = ["SPY 09:30-12:30 range < 0.5 SPY ATR", "rvol proxy (mean volumeRatio 09:50-10:30) >= 2",
          "close[i-1] <= VWAP - 0.5 ATR", "rsi5[i-1] <= 20, close > prior high",
          "stop max(LOD, entry - 0.4 ATR), target VWAP", "12:30-14:45 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, dlod, vr, vd, r5, atr, spyq, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = atr[i0]
        if not (a > 0 and spyq[i0] < 0.5):
            continue
        sv = 0.0
        nv = 0
        for k in range(i0, i1):
            if tod[k] > 1030:
                break
            if vr[k] == vr[k]:
                sv += vr[k]
                nv += 1
        if nv == 0 or sv / nv < 2.0:
            continue
        for i in range(i0 + 1, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            vwp = c[i - 1] / (1.0 + vd[i - 1] / 100.0)
            if not (c[i - 1] <= vwp - 0.5 * a and r5[i - 1] <= 20.0 and c[i] > h[i - 1]):
                continue
            vw = c[i] / (1.0 + vd[i] / 100.0)
            lod = c[i] - dlod[i] * a
            sp = max(lod, c[i] - 0.4 * a)
            if sp < c[i] and vw > c[i]:
                m[i] = True
                stop[i] = sp
                tgt[i] = vw
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    spy = df.loc[(df["symbol"].astype(str) == "SPY") & (df["tod"] == 1230), ["date", "dist_hod_atr", "dist_lod_atr"]]
    if not len(spy):
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    spy = spy.drop_duplicates("date")
    spy = pd.DataFrame({"date": spy["date"].to_numpy(),
                        "spyq": spy["dist_hod_atr"].to_numpy(float) + spy["dist_lod_atr"].to_numpy(float)})
    dg = pd.DataFrame({"date": df["date"].to_numpy()}).merge(spy, on="date", how="left")
    spyq = dg["spyq"].to_numpy(float)
    spyq = np.where(np.isfinite(spyq), spyq, 1e9)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("dist_lod_atr"), f("volumeRatio"),
                   f("vwapDistPct"), f("rsi5"), f("atr_d"), spyq, WINDOW[0], WINDOW[1])


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
