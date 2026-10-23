"""pod-wt-cup-handle-midday-long - Intraday cup-and-handle ('curl' back to the high, then a handle above VWAP),
break of the handle high (LONG).

Source: Warrior Trading / Ross Cameron, cup-and-handle and 'curl' patterns on intraday charts (Warrior Trading
YouTube pattern lessons). Not re-fetched this round.
URL: https://www.youtube.com/@DaytradeWarrior

VARIANT of pod-of-second-test-hod-break and pod-smb-second-chance-hod-retest. Stated changes: no failed-poke bar;
the cup is a deep rounded pullback (0.4-1.0 x atr_d below an earlier HOD, >= 8 bars), the recovery reaches within
0.10 x atr_d of the lip, a light-volume handle follows, and the entry is the HANDLE-high break (it can be below the
HOD, so price rides into the HOD instead of buying above it).

Rules (plain English):
  1. Cup lip = the running HOD as of the prior bar, set on frame bar C (the last bar whose high equals it) with bar
     close >= 10:00. Cup bottom B = the lowest low after C (up to the prior bar), 0.4-1.0 x atr_d below the lip and
     >= 4 bars after C; no close from C to this bar below session VWAP - 0.2 x atr_d.
  2. Recovery: R = the first bar after B with high >= lip - 0.10 x atr_d, and R - C >= 8 bars.
  3. Handle = the 2-5 bars after R (R+1 .. prior bar): its lowest low is within 40% of the cup depth below the
     recovery-bar high, every close >= EMA9 - 0.05 x atr_d, mean volumeRatio <= 0.8. Handle high = the highest high
     from R to the prior bar.
  4. This bar closes above the handle high with volumeRatio >= 1.3 (it is the first such close by construction).
  Entry: that close, bar close 11:00-14:30. Stop (GEOM S): handle low - 0.03 x atr_d. Target: lip + 0.5 x cup depth,
  else flat 15:55.
Frame note: EMA9 is on the day's 5-minute closes seeded at the 09:50 close. No tweak made. Costs per
config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
LAYERS = ["lip = HOD set at >= 10:00", "cup 0.4-1.0 ATR deep, bottom >= 4 bars after lip, closes >= VWAP - 0.2 ATR",
          "recovery to lip - 0.10 ATR, cup >= 8 bars", "2-5 bar handle, retrace <= 40% depth, closes >= EMA9 - 0.05 ATR, vr <= 0.8",
          "close > handle high, volumeRatio >= 1.3", "stop handle low - 0.03 ATR, target lip + 0.5 depth", "11:00-14:30"]

import numba
import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _base(df):
    k = _key(df)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=df["tod"].to_numpy(np.int64), c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    return b


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, vw, atr, vr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    ema = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        ev = c[i0]
        jc = -1
        for i in range(i0, i1):
            ev = ev + (2.0 / 10.0) * (c[i] - ev)
            ema[i] = ev
            if i > i0 and tod[i] >= w0 and tod[i] <= w1 and jc >= 0 and vr[i] >= 1.3:
                a = atr[i]
                lip = hod[i - 1]
                C = jc
                if tod[C] >= 1000 and abs(h[C] - lip) <= 1e-6 * c[i] and a > 0:
                    B = -1
                    lo = 1e18
                    for t in range(C + 1, i):
                        if l[t] < lo:
                            lo = l[t]
                            B = t
                    D = lip - lo
                    ok = B >= 0 and B - C >= 4 and D >= 0.4 * a and D <= 1.0 * a
                    if ok:
                        for t in range(C, i + 1):
                            if c[t] < vw[t] - 0.2 * a:
                                ok = False
                                break
                    R = -1
                    if ok:
                        for t in range(B + 1, i):
                            if h[t] >= lip - 0.10 * a:
                                R = t
                                break
                    if ok and R >= 0 and R - C >= 8:
                        K = i - 1 - R
                        if K >= 2 and K <= 5:
                            hh = -1e18
                            for t in range(R, i):
                                hh = max(hh, h[t])
                            hl = 1e18
                            vs = 0.0
                            good = True
                            for t in range(R + 1, i):
                                hl = min(hl, l[t])
                                vs += vr[t]
                                if not (c[t] >= ema[t] - 0.05 * a):
                                    good = False
                            if good and h[R] - hl <= 0.4 * D and vs / K <= 0.8 and c[i] > hh:
                                m[i] = True
                                stop[i] = hl - 0.03 * a
                                tgt[i] = lip + 0.5 * D
            if h[i] >= hod[i] - 1e-6 * c[i]:
                jc = i
    return m, stop, tgt


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    bb, ee = _segments(b["k"])
    m, stop, tgt = _kern(bb, ee, b["tod"], b["c"], b["h"], b["l"], b["hod"], b["vwap"], b["atr"],
                         _f(df, "volumeRatio"), WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
