"""pod-smb-lt-support-first-test-hold-long - First intraday test of a long-term (60-day) low in an in-play stock, holds
(LONG).

Source: SMB 'Trade of the Week' series (Bellafiore): 'Long Term Technical Resistance Level' (BIDU) - mirrored to
support.
URL: https://smbtraining.com/blog/category/trade-of-the-week/page/5

VARIANT of pod-smb-pdl-bounce-momentum-confirm (prior-day-low bounce). Stated changes: the level is the 60-day daily low
(multi-month support) that was not touched in the last 10 sessions; only the first intraday test is traded; the gate is
a non-crashing index.

Rules (plain English, LONG):
  Level L = the lowest daily low of D-60..D-1 (completed days, lib.daily()); the lowest low of D-10..D-1 is above L
  (not touched in the last 10 sessions).
  1. Cumulative relative volume at the signal bar >= 1.5 (volume 09:30..bar / the 20-session same-time mean).
  2. Touch bar t (bar close 10:00-14:30): the first bar of the day whose low comes within 0.15 x ATR(5m) of L (the
     running low of day before bar t was above L + 0.15 x ATR(5m), 09:30-09:45 included); its low is in
     [L - 0.2 x ATR(5m), L + 0.15 x ATR(5m)] (an undercut of at most 0.2 ATR(5m)).
  3. The touch bar's lower wick >= 50% of its range and it closes back above L.
  4. SPY's day change (close at the signal bar vs the prior close) > -1.0%.
  5. The next bar (t+1) closes above the touch-bar high -> signal.
  Entry: bar t+1 close (= next bar open). Stop (GEOM S): touch-bar low - 0.1 x ATR(5m). Target: VWAP, or 2R when VWAP
  is less than 1R above the entry. Flat 15:55.
'ATR' in the source's undercut rule is read as ATR(5m), the same unit as the touch band (pre-declared reading).
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1005, 1435)
LAYERS = ["60-day low untouched 10 sessions", "first touch 10:00-14:30 within +0.15/-0.2 ATR5m",
          "lower wick >= 50%, close above level", "cum rvol >= 1.5", "SPY day change > -1%",
          "next bar closes above touch high", "stop touch low - 0.1 ATR5m, target VWAP or 2R"]

import numba
import numpy as np
import pandas as pd

import _cwt3_bars as C
import _r24_bars as R

_ST = {}


@numba.njit(cache=False)
def _kern(bs, be, tod, c, h, l, lod, vw, atr5, lw, L, rvc, spyok):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(bs)):
        i0, i1 = bs[s], be[s]
        lev = L[i0]
        if not (lev > 0):
            continue
        for t in range(i0, i1 - 1):
            near = l[t] <= lev + 0.15 * atr5[t]
            if not near:
                continue
            # first test: nothing earlier today (incl. 09:30-09:45, via the running LOD) came that close
            if t == i0 or tod[t] < 1000 or tod[t] > 1430:      # a touch before 10:00 is the first test -> none
                break
            if lod[t - 1] <= lev + 0.15 * atr5[t]:
                break
            if l[t] < lev - 0.2 * atr5[t] or not (lw[t] >= 0.5) or not (c[t] > lev):        # (2) (3)
                break
            i = t + 1
            if c[i] > h[t] and rvc[i] >= 1.5 and spyok[i]:                                 # (5) (1) (4)
                sp = l[t] - 0.1 * atr5[t]
                Rr = c[i] - sp
                if Rr > 0:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = vw[i] if vw[i] - c[i] >= Rr else c[i] + 2 * Rr
            break
    return m, stop, tgt


def _compute(df):
    n = len(df)
    if not n:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    b = C.base(df)
    k = C.key(df)
    bs = np.flatnonzero(C.start(k)).astype(np.int64)
    be = np.r_[bs[1:], n].astype(np.int64)
    dfe = R.daily_feats()
    d = R.daymap(df, ["l60", "l10"], dfe)
    L = np.where(d["l10"] > d["l60"], d["l60"], np.nan)
    rv = R.bars_for(df, ["rvc"])["rvc"]
    S = R.spy_bars()[["date", "tod", "c"]].copy()
    sp = dfe[dfe["symbol"] == "SPY"][["date", "close1"]]
    S = S.merge(sp, on="date", how="left")
    S["ok"] = (S["c"] / S["close1"] - 1 > -0.01).astype(float)
    S.loc[S["close1"].isna(), "ok"] = np.nan
    S["tod"] = S["tod"].astype(np.int64)
    key = pd.DataFrame({"date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy(),
                        "tod": df["tod"].to_numpy(np.int64)})
    spy = key.merge(S[["date", "tod", "ok"]], on=["date", "tod"], how="left")["ok"].to_numpy(float)
    return _kern(bs, be, b["tod"], b["c"], b["h"], b["l"], b["lod"], b["vwap"], b["atr5"], C.f(df, "lower_wick"),
                 L, rv, spy == 1.0)


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
