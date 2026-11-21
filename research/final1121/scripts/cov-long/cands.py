"""cov-long candidate masks (pre-declared grid, written before any score). All LONG, R = 0.25 x daily ATR, t1s1,
entry at decision-bar close, flat 15:55. Decision-time columns only (frame row = 5-min bar, values at bar close;
spy_gap / spy_fo2 / spy_rng from SPY 1-minute bars up to the bar close). Educational only - not financial advice."""
import numpy as np


def _c(df, k):
    return df[k].to_numpy(dtype=float)


def _prev(df, k):
    x = _c(df, k)
    key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
    p = np.r_[np.nan, x[:-1]]
    new = np.r_[True, key[1:] != key[:-1]]
    p[new] = np.nan
    return p


def _tod(df):
    return df["tod"].to_numpy(int)


# M1 GAPGO: gap-up continuation ("gap and go"), news-driven demand holding at the high
def gapgo(G):
    def m(df):
        t = _tod(df)
        g = _c(df, "gap")
        return ((g >= G) & (g < 20) & (t >= 1000) & (t <= 1100) & (_c(df, "fromOpen") > 0) & (_c(df, "vwapDistPct") > 0)
                & (_c(df, "dist_hod_atr") <= 0.05) & (_c(df, "volumeRatio") >= 1.5))
    return m


# M2 PDHBRK: first close above the prior-day high during the session, green tape optional
def pdhbrk(spy):
    def m(df):
        t = _tod(df)
        d, dp = _c(df, "dist_pdh_atr"), _prev(df, "dist_pdh_atr")
        g = _c(df, "gap")
        ok = ((d <= 0) & (dp > 0) & (t >= 1030) & (t <= 1430) & (g > -1) & (g < 2) & (_c(df, "volumeRatio") >= 1.5)
              & (_c(df, "vwapDistPct") > 0))
        if spy is not None:
            ok &= _c(df, "spy_fo2") > spy
        return ok
    return m


# M3 RSHOD: relative-strength leader printing a new high of day after midday
def rshod(K):
    def m(df):
        t = _tod(df)
        rs = _c(df, "fromOpen") - _c(df, "spy_fo2")
        v = _c(df, "vwapDistPct")
        return ((t >= 1130) & (t <= 1430) & (_c(df, "dist_hod_atr") <= 0.02) & (rs >= K) & (v > 0.3) & (v < 3)
                & (_c(df, "sma20_slope_pct") > 0))
    return m


# M4 IMOM: late-day intraday momentum into the close
def imom(F, spy):
    def m(df):
        t = _tod(df)
        ok = ((t >= 1430) & (t <= 1500) & (_c(df, "fromOpen") >= F) & (_c(df, "pricePosition") >= 0.8)
              & (_c(df, "vwapDistPct") > 0.5))
        if spy is not None:
            ok &= _c(df, "spy_fo2") > spy
        return ok
    return m


# M5 QUIETLEAD: idiosyncratic leader on a quiet tape (SPY flat, narrow so far)
def quietlead(RNG):
    def m(df):
        t = _tod(df)
        return ((t >= 1030) & (t <= 1400) & (np.abs(_c(df, "spy_fo2")) <= 0.25) & (_c(df, "spy_rng") <= RNG)
                & (_c(df, "dist_hod_atr") <= 0.02) & (_c(df, "fromOpen") >= 1.5) & (_c(df, "volumeRatio") >= 1.5))
    return m


# M6 RISKON: SPY gapped up (known at 09:30); stock in play breaks to new HOD early
def riskon(SG):
    def m(df):
        t = _tod(df)
        return ((_c(df, "spy_gap") >= SG) & (t >= 1000) & (t <= 1100) & (_c(df, "gap") >= 0) & (_c(df, "gap") < 20)
                & (_c(df, "fromOpen") > 0) & (_c(df, "dist_hod_atr") <= 0.02) & (_c(df, "volumeRatio") >= 2))
    return m


# M7 VWAPPB: trend pullback - up stock dips back to VWAP and reclaims it, in an uptrend
def vwappb(spy):
    def m(df):
        t = _tod(df)
        h = _c(df, "dist_hod_atr")
        ok = ((t >= 1030) & (t <= 1400) & (_c(df, "vwapReclaim") == 1) & (h >= 0.3) & (h <= 1.0)
              & (_c(df, "fromOpen") > 0.5) & (_c(df, "gap") >= 0) & (_c(df, "sma50_dist_pct") > 0))
        if spy is not None:
            ok &= _c(df, "spy_fo2") > spy
        return ok
    return m


ADV = 20e6
CANDS = {
    "M1-gapgo-g2": gapgo(2), "M1-gapgo-g4": gapgo(4), "M1-gapgo-g6": gapgo(6),
    "M2-pdhbrk-any": pdhbrk(None), "M2-pdhbrk-spy0": pdhbrk(0.0), "M2-pdhbrk-spy03": pdhbrk(0.3),
    "M3-rshod-k1": rshod(1), "M3-rshod-k2": rshod(2), "M3-rshod-k3": rshod(3),
    "M4-imom-f15": imom(1.5, None), "M4-imom-f3": imom(3, None), "M4-imom-f15-spy0": imom(1.5, 0.0),
    "M4-imom-f3-spy0": imom(3, 0.0),
    "M5-quiet-r05": quietlead(0.5), "M5-quiet-r08": quietlead(0.8),
    "M6-riskon-sg02": riskon(0.2), "M6-riskon-sg05": riskon(0.5),
    "M7-vwappb-any": vwappb(None), "M7-vwappb-spy0": vwappb(0.0),
}
