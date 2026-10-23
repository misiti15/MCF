"""pod-smb-2day-avwap-first-touch-quiet-long - SMB 2-day VWAP pullback, first touch after 11:00 on a quiet tape (LONG).

Source: SMB Training blog/video 'A 2 Day VWAP Trade (CNC)' (junior trader buys a 2-day VWAP pullback; Bellafiore desk
critique).
URL: https://www.smbtraining.com/blog/a-2-day-vwap-trade-cnc

VARIANT of 'Earnings / catalyst-bar anchored VWAP (SMB catalyst hold, Dale)'. Stated changes: no earnings filter (any
in-play day 1), first touch only after 11:00, a quiet-SPY gate, and the exit at the day-2 high instead of a hold.

Data: daily bars of COMPLETED days (research/history2y lib.daily()); the 2-day AVWAP is anchored at the day-1 09:30 bar
and built from the 1-minute vendor bars (5m typical price x volume, helper _smbv5_bars; the locked block is never
read), cumulative through the decision bar only. SPY first-hour range = SPY high - low of 09:30-10:30, compared with
its mean over the 20 prior sessions (min 15). ATR14(5m) = atrPct x close (frame). "Volume <= 1.2x its 20-bar average"
= the frame's volumeRatio.

Rules (plain English):
  Day 1 (= D-1): return >= +3%, daily rvol (volume / 20-session mean) >= 2.5, close in the top 25% of the range.
  Day 2 (today):
  1. SPY's first-hour range < 0.8 x its 20-day average.
  2. Every 5m bar closing at or before 11:00 has its low above the 2-day AVWAP at that bar.
  3. The first 5m bar closing 11:05-14:30 whose low is within 0.1 x ATR14(5m) of the AVWAP (low <= AVWAP + 0.1 ATR)
     is the touch bar; only this first touch counts.
  4. The touch bar or the next bar closes above the AVWAP with volumeRatio <= 1.2 (no heavy selling); that bar is the
     decision bar.
  Entry: next bar open (scorer: decision-bar close). Stop (GEOM S): the lower of AVWAP - 0.25 x ATR14(5m) and the
  touch-bar low. Target: the day-2 high of day so far (must be above entry); else flat 15:55. One trade per
  symbol-day. Costs in (scorer). 1 config, no tweak.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

import _smbv5_bars as V

SIDE = "long"
GEOM = "S"
WINDOW = (1105, 1435)
LAYERS = ["D-1 ret >= 3%, rvol >= 2.5, close in top 25%", "SPY first-hour range < 0.8 x 20d avg",
          "lows above the 2-day AVWAP through 11:00", "first touch 11:05-14:30 within 0.1 ATR5",
          "touch or next bar closes above AVWAP, volumeRatio <= 1.2",
          "stop min(AVWAP - 0.25 ATR5, touch low), target day-2 HOD"]
_STASH = {}
_C = {}


def _tables():
    if "t" in _C:
        return _C["t"]
    dc = V.daily_ctx()
    cand = dc[(dc["ret1"] >= 0.03) & (dc["rvol1"] >= 2.5) & (dc["clpos1"] >= 0.75) & dc["d1date"].notna()]
    cand = cand[["symbol", "date", "d1date"]]
    E = V.evbars()
    a = cand.merge(E.rename(columns={"date": "d1date"}), on=["symbol", "d1date"], how="inner")
    a["ord"] = 0
    b = cand.merge(E, on=["symbol", "date"], how="inner")
    b["ord"] = 1
    x = pd.concat([a, b], ignore_index=True).sort_values(["symbol", "date", "ord", "tod"], kind="mergesort")
    g = x.groupby(["symbol", "date"], sort=False)
    x["avwap"] = g["pv"].cumsum() / g["v"].cumsum()
    nd1 = a.groupby(["symbol", "date"]).size().rename("n1")
    x = x[x["ord"] == 1].copy()
    x = x.merge(nd1.reset_index(), on=["symbol", "date"], how="left")
    x = x[x["n1"] >= 60]                                   # need a full day 1 for the anchor
    pre = x[x["tod"] <= 1100]
    ok = (pre["l"] > pre["avwap"]).groupby([pre["symbol"], pre["date"]]).all().rename("pre_ok").reset_index()
    ok = ok.merge(pre.groupby(["symbol", "date"]).size().rename("npre").reset_index(), on=["symbol", "date"])
    ok = ok[ok["pre_ok"] & (ok["npre"] >= 18)]
    # SPY first-hour gate
    D = V.dayagg()
    s = D[D["symbol"] == "SPY"].sort_values("date")[["date", "fh_h", "fh_l"]].copy()
    s["fh"] = s["fh_h"] - s["fh_l"]
    s["fh20"] = s["fh"].shift(1).rolling(20, min_periods=15).mean()
    quiet = set(s.loc[s["fh"] < 0.8 * s["fh20"], "date"])
    ok = ok[ok["date"].isin(quiet)]
    bars = x.merge(ok[["symbol", "date"]], on=["symbol", "date"], how="inner")[["symbol", "date", "tod", "avwap"]]
    _C["t"] = bars
    return bars


@numba.njit(cache=False)
def _kernel(b, e, tod, c, l, ap, vr, dh, atr, av, w0):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not (av[i0] == av[i0]):
            continue
        t = -1
        for k in range(i0, i1):
            if tod[k] < w0:
                continue
            if tod[k] > 1430:
                break
            a5 = ap[k] / 100.0 * c[k]
            if l[k] <= av[k] + 0.1 * a5:
                t = k
                break
        if t < 0:
            continue
        a5 = ap[t] / 100.0 * c[t]
        sp = min(av[t] - 0.25 * a5, l[t])
        for i in (t, t + 1):
            if i >= i1 or not (av[i] == av[i]):
                break
            if c[i] > av[i] and vr[i] <= 1.2:
                hod = c[i] + dh[i] * atr[i]
                if hod > c[i] and sp < c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = hod
                break
    return m, stop, tgt


def compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if n == 0:
        return z
    try:
        T = _tables()
    except Exception:  # noqa: BLE001 - no cache -> no trades
        return z
    r = V.rowmap(df, T, ["avwap"])
    sym, dat, b, e = V.keys(df)
    f = lambda k: df[k].to_numpy(float)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("low"), f("atrPct"), f("volumeRatio"),
                   f("dist_hod_atr"), f("atr_d"), r["avwap"], 1105)


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
