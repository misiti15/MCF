"""pod-wt-micro-pullback-midday-reload-quiet-long - Ross Cameron 'first candle to make a new high' after the 2nd
pullback, quiet midday reload in a morning leader (LONG).

Source: Warrior Trading / Ross Cameron YouTube - 'Squeeze up -> pullback -> first candle to new high' (take only the
1st and 2nd pullbacks) + Warrior Trading blog 'The Simple Scalping Strategy for Day Trading'.
URL: https://www.warriortrading.com/the-simple-scalping-strategy-for-day-trading/

VARIANT of bdi-vid-micropullback-long ('Ross Cameron micro-pullback LONG', failed). Stated changes: used only in the
11:00-13:30 lull, only on the SECOND pullback of the day, only when that pullback is quiet (volume dry-up) and holds
above VWAP / EMA21, with HOD + 0.25 ATR as the target instead of the volume-top exit.

Data: running HOD = close + dist_hod_atr x atr_d (frame); VWAP = close / (1 + vwapDistPct%); EMA9 / EMA21 of continuous
full-session 5-minute closes (frame bars + the 09:35-09:45 / 15:05-15:55 head/tail bars, previous open month as
warm-up; helper _cwt3_bars.full_bars, causal, locked block never read). Pullbacks are
counted from the 09:50 frame bar on.

Rules (plain English), decision bar i (bar close 11:00-13:30 ET):
  1. Morning leader: fromOpen on the 11:00 bar >= 0.8 x atr_d / price (in %), and the close is above VWAP on >= 80% of
     the frame bars up to i.
  2. Pullback count: a pullback = >= 2 consecutive lower highs right after a new-HOD bar, completed by a later new-HOD
     bar. Exactly one such completed pullback since 09:50 before the latest HOD bar H; the current pullback (bars
     H+1..i-1) is 2-6 bars of consecutive lower highs - the second pullback of the day.
  3. Quiet: mean volumeRatio of the pullback bars <= 0.7; their lowest low >= max(VWAP, EMA21) at bar i-1; the
     pullback retraces <= 50% of the leg from the first pullback's low to HOD.
  4. Trigger: high_i > high_{i-1}, close_i > high_{i-1} (first candle to make a new high), close_i >= EMA9_i.
  Entry close_i. Stop (GEOM S): pullback low - 0.02 x atr_d. Target: running HOD + 0.25 x atr_d; skip when target -
  entry < 1.0 x risk. Flat 15:55. Costs in (scorer). 1 config, no tweak.
Educational only - not financial advice."""
import numba
import numpy as np

import _cwt3_bars as W
import _smbv5_bars as V

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1330)
LAYERS = ["fromOpen@11:00 >= 0.8 ATR, above VWAP on >= 80% of bars", "exactly one earlier pullback since 09:50",
          "current pullback 2-6 lower highs, mean volumeRatio <= 0.7, low >= max(VWAP, EMA21), retrace <= 50%",
          "close > prior high, close >= EMA9", "stop pullback low - 0.02 ATR, target HOD + 0.25 ATR (>= 1R)",
          "11:00-13:30 ET"]
_STASH = {}


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, fo, vd, dh, vr, atr, e9, e21, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        fo11 = np.nan
        for k in range(i0, i1):
            if tod[k] == 1100:
                fo11 = fo[k]
                break
        if not (fo11 == fo11):
            continue
        # new-HOD flags
        hod = np.empty(i1 - i0)
        newh = np.zeros(i1 - i0, np.bool_)
        for k in range(i0, i1):
            hod[k - i0] = c[k] + dh[k] * atr[k]
            if h[k] >= hod[k - i0] - 1e-6 * atr[k] and (k == i0 or hod[k - i0] > hod[k - i0 - 1] + 1e-9):
                newh[k - i0] = True
        above = 0
        for i in range(i0, i1):
            if vd[i] > 0:
                above += 1
            if tod[i] < w0 or tod[i] > w1 or i - i0 < 4:
                continue
            a = atr[i]
            if not (a > 0) or above < 0.8 * (i - i0 + 1):
                continue
            if not (fo11 >= 80.0 * a / c[i]):
                continue
            if not (h[i] > h[i - 1] and c[i] > h[i - 1] and c[i] >= e9[i]):
                continue
            # latest HOD bar before i
            H = -1
            for k in range(i - 1, i0 - 1, -1):
                if newh[k - i0]:
                    H = k
                    break
            if H < 0:
                continue
            npb = i - 1 - H
            if npb < 2 or npb > 6:
                continue
            ok = True
            for k in range(H + 1, i):
                if not (h[k] < h[k - 1]):
                    ok = False
                    break
            if not ok:
                continue
            # completed pullbacks before H
            cnt = 0
            plow = np.nan
            last = -1
            for k in range(i0, H + 1):
                if newh[k - i0]:
                    if last >= 0 and k - last >= 3 and h[last + 1] < h[last] and h[last + 2] < h[last + 1]:
                        cnt += 1
                        lo = 1e18
                        for q in range(last + 1, k):
                            lo = min(lo, l[q])
                        plow = lo
                    last = k
            if cnt != 1:
                continue
            vs = 0.0
            lo = 1e18
            for k in range(H + 1, i):
                vs += vr[k]
                lo = min(lo, l[k])
            if not (vs / npb <= 0.7):
                continue
            vw = c[i - 1] / (1.0 + vd[i - 1] / 100.0)
            if not (lo >= max(vw, e21[i - 1])):
                continue
            hd = hod[H - i0]
            if not (hd - plow > 0 and (hd - lo) <= 0.5 * (hd - plow)):
                continue
            sp = lo - 0.02 * a
            hi = c[i] + dh[i] * a
            tp = hi + 0.25 * a
            risk = c[i] - sp
            if risk > 0 and tp - c[i] >= risk:
                m[i] = True
                stop[i] = sp
                tgt[i] = tp
    return m, stop, tgt


def compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if n == 0:
        return z
    try:
        B = W.full_bars(df)
    except Exception:  # noqa: BLE001 - no bars -> no trades
        return z
    if B is None:
        return z
    B = B.copy()
    g = B.groupby("symbol", sort=False)["c"]
    B["ema9"] = g.transform(lambda x: x.ewm(span=9, adjust=False).mean())
    B["ema21"] = g.transform(lambda x: x.ewm(span=21, adjust=False).mean())
    r = W.map_rows(df, B, ["ema9", "ema21"])
    sym, dat, b, e = V.keys(df)
    f = lambda k: df[k].to_numpy(float)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"), f("fromOpen"),
                   f("vwapDistPct"), f("dist_hod_atr"), f("volumeRatio"), f("atr_d"), r["ema9"], r["ema21"],
                   WINDOW[0], WINDOW[1])


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
