"""pod-smb-lod-coil-after-down-drive-reversal-long - LOD coil after a down opening drive: seller exhaustion, break up
(LONG).

Source: SMB Training 2011 post: stock 'consolidating at the low of the day after a strong Opening Drive' (SMB desk
commentary). This is the opposite side of the desk's breakdown read.
URL: https://www.smbtraining.com/blog/2011/page/81

New setup. Not a copy of pod-three-push-deceleration-low-long or pod-of-lowerwick-cluster-quiet-lod-long: no pushes or
wicks here, only a flat time-box coil after a measured down drive.

Rules (plain English, LONG):
  1. Down drive 09:30-10:00: 09:30 open - 10:00 close >= 1.5 x ATR14(5m) x sqrt(6) (ATR(5m) at the 10:00 bar), and the
     10:00 close is in the bottom 30% of the 09:30-10:00 range.
  2. Coil: the bars after 10:00 (closing 10:05 .. the bar before the signal), at least 6 of them (30+ min), all inside
     10:00-12:00, print no new low of day (the running LOD stays the 10:00 LOD) and every coil bar's high stays within
     0.5 x ATR(5m) of the LOD (ATR(5m) at the bar being checked). If a bar breaks the coil any other way, no trade.
  3. Volume in the coil (mean 5m volume) <= 0.6 x the drive's mean 5m volume (09:30-10:00).
  4. SPY has not made a new session low in the last 30 minutes (its running low at the signal bar equals its running
     low 30 minutes earlier).
  5. Signal: the first 5m close above the coil high, also above the session EMA9 of 5m closes.
  Entry: the signal bar's close (= next bar open). Stop (GEOM S): LOD - 0.1 x ATR(5m). Target: VWAP or the 50%
  retracement of the drive (LOD + 0.5 x (09:30-10:00 high - LOD)), whichever is nearer above the entry.
Harness deviation (stated): the source's 14:30 time exit is not available in the harness; trades without a target or
stop fill are flat at 15:55.
Data: drive values, 5m volume and EMA9 from _r24_bars (1-minute vendor bars; locked block never read); SPY from
_smbv5_bars evbars.
Score (2026-10-23, r2_4): 0 trades over 21 open months. Funnel check on 2025-06: 1266 symbol-days pass the drive
(1), but on 1261 of them the very first bar after 10:00 already breaks the coil (new LOD or high > LOD + 0.5 ATR5m);
no 6-bar coil formed. Even a 1.0 ATR5m band gives no 6-bar coil, so no tweak was made.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1035, 1205)
LAYERS = ["down drive >= 1.5 ATR5m x sqrt6, close in bottom 30%", ">= 6 bar coil, no new LOD, highs within 0.5 ATR5m",
          "coil vol <= 0.6 x drive vol", "SPY no new low in 30 min", "close > coil high and > EMA9",
          "stop LOD - 0.1 ATR5m, target nearer of VWAP / 50% drive retrace"]

import numba
import numpy as np
import pandas as pd

import _cwt3_bars as C
import _r24_bars as R

_ST = {}


@numba.njit(cache=False)
def _kern(bs, be, tod, c, h, l, lod, vw, atr5, v, ema, o935, drh, drl, c1000, dva, spyok):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(bs)):
        i0, i1 = bs[s], be[s]
        j = -1
        for i in range(i0, i1):
            if tod[i] == 1000:
                j = i
                break
        if j < 0 or not (atr5[j] > 0) or not (drh[i0] > drl[i0]):
            continue
        if not (o935[i0] - c1000[i0] >= 1.5 * atr5[j] * np.sqrt(6.0)):                      # (1)
            continue
        if not ((c1000[i0] - drl[i0]) <= 0.3 * (drh[i0] - drl[i0])):
            continue
        L0 = lod[j]
        eps = 1e-6 * c[j]
        ch = -1e18
        nb = 0
        vs = 0.0
        for i in range(j + 1, i1):
            if nb >= 6 and c[i] > ch:                                                        # (5) break of the coil
                if tod[i - 1] <= 1200 and c[i] > ema[i] and spyok[i] and vs / nb <= 0.6 * dva[i0]:
                    sp = L0 - 0.1 * atr5[i]
                    t1 = vw[i]
                    t2 = L0 + 0.5 * (drh[i0] - L0)
                    t = np.nan
                    if t1 > c[i] and t2 > c[i]:
                        t = min(t1, t2)
                    elif t1 > c[i]:
                        t = t1
                    elif t2 > c[i]:
                        t = t2
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = t
                break
            if tod[i] > 1200:
                break
            if lod[i] < L0 - eps or l[i] < L0 - eps or h[i] > L0 + 0.5 * atr5[i]:            # (2) coil broken
                break
            if not (v[i] == v[i]):
                break
            ch = max(ch, h[i])
            vs += v[i]
            nb += 1
    return m, stop, tgt


def _compute(df):
    n = len(df)
    if not n:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    b = C.base(df)
    k = C.key(df)
    bs, be = np.flatnonzero(C.start(k)).astype(np.int64), None
    be = np.r_[bs[1:], n].astype(np.int64)
    bv = R.bars_for(df, ["v", "ema9"])
    dv = R.daymap(df, ["o935", "dr_h", "dr_l", "c1000", "dr_vavg"])
    S = R.spy_bars()[["date", "tod", "run_l"]].copy()
    S = S.sort_values(["date", "tod"])
    S["run_l30"] = S.groupby("date")["run_l"].shift(6)
    S["ok"] = (S["run_l"] >= S["run_l30"] - 1e-9).astype(float)
    S.loc[S["run_l30"].isna(), "ok"] = np.nan
    key = pd.DataFrame({"date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy(),
                        "tod": df["tod"].to_numpy(np.int64)})
    S["tod"] = S["tod"].astype(np.int64)
    spy = key.merge(S[["date", "tod", "ok"]], on=["date", "tod"], how="left")["ok"].to_numpy(float)
    return _kern(bs, be, b["tod"], b["c"], b["h"], b["l"], b["lod"], b["vwap"], b["atr5"], bv["v"], bv["ema9"],
                 dv["o935"], dv["dr_h"], dv["dr_l"], dv["c1000"], dv["dr_vavg"], spy == 1.0)


def mask(df) -> np.ndarray:
    try:
        m, stop, tgt = _compute(df)
    except (KeyError, FileNotFoundError):
        m, stop, tgt = np.zeros(len(df), bool), np.full(len(df), np.nan), np.full(len(df), np.nan)
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
