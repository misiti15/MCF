"""cov-long round 3 (pre-declared before scoring): Crabel narrow-range -> opening-range breakout, LONG.
Prior-day range (pdh - pdl) / daily ATR <= NR (volatility contraction), today first 5-min close above the 09:30-10:00
high between 10:05 and 11:30, above VWAP, volumeRatio >= 1.2. t1s1, flat 15:55. Educational only - not financial advice."""
import numpy as np
import pandas as pd

ADV = 20e6


def nrorb(NR):
    def m(df):
        t = df["tod"].to_numpy(int)
        c = df["close"].to_numpy(float)
        atr = df["atr_d"].to_numpy(float)
        key = (df["symbol"].astype(str) + "|" + df["date"].astype(str)).values
        orh = np.where(t == 1000, c + df["dist_hod_atr"].to_numpy(float) * atr, np.nan)
        orh = pd.Series(orh).groupby(key).transform("max").to_numpy()
        pr = df["dist_pdh_atr"].to_numpy(float) + df["dist_pdl_atr"].to_numpy(float)
        above = c > orh
        prev = np.r_[False, above[:-1]]
        new = np.r_[True, key[1:] != key[:-1]]
        prev[new] = False
        return ((pr <= NR) & (t >= 1005) & (t <= 1130) & above & ~prev & (df["vwapDistPct"].to_numpy(float) > 0)
                & (df["volumeRatio"].to_numpy(float) >= 1.2))
    return m


CANDS = {"N1-nrorb-06": nrorb(0.6), "N2-nrorb-08": nrorb(0.8)}
