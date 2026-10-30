"""_rc_util - shared helpers for the reddit_1030 modules (not a setup). Shifts are within symbol-day; the frame is
sorted by (symbol, date, tod) by the scorer. Educational only - not financial advice."""
import numpy as np
import pandas as pd


def keys(df):
    return df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()


def shift(a, k, key):
    a = np.asarray(a, float)
    out = np.full(len(a), np.nan)
    if 0 < k < len(a):
        same = key[k:] == key[:-k]
        out[k:] = np.where(same, a[:-k], np.nan)
    return out


def mean_prev(a, k0, n, key):
    """Mean of a over the n bars ending k0 bars back (k0, k0+1, ... k0+n-1), NaN if any is missing."""
    s = np.zeros(len(a))
    for j in range(k0, k0 + n):
        s = s + shift(a, j, key)
    return s / n


def volconfirm(df, level, use_vol):
    key = keys(df)
    c, h, l = (df[x].to_numpy(float) for x in ("close", "high", "low"))
    vr = df["volumeRatio"].to_numpy(float)
    if level == "ema8":
        L = df.groupby("symbol", sort=False)["close"].transform(lambda s: s.ewm(span=8, adjust=False).mean()).to_numpy(float)
    else:
        L = c / (1.0 + df["vwapDistPct"].to_numpy(float) / 100.0)
    with np.errstate(invalid="ignore"):
        test = (l <= L * 1.001) & (c >= L * 0.998)
        if use_vol:
            test &= vr < mean_prev(vr, 1, 3, key)
        trig = (c > shift(c, 1, key)) & (c > L)
        if use_vol:
            trig &= vr > mean_prev(vr, 1, 3, key)
        ctx = ((df["fromOpen"].to_numpy(float) - df["spy_fo"].to_numpy(float)) > 0) & \
              (df["vwapDistPct"].to_numpy(float) > 0) & (df["sma50_dist_pct"].to_numpy(float) > 0)
    m = np.zeros(len(df), bool)
    stop = np.full(len(df), np.nan)
    for k in (1, 2):                                   # test bar k bars before the trigger
        tk = shift(test.astype(float), k, key) == 1
        lo = l.copy()
        for j in range(1, k + 1):
            lo = np.fmin(lo, shift(l, j, key))
        hit = tk & trig & ctx & ~m
        stop = np.where(hit, lo - 0.01, stop)
        m |= hit
    m &= np.isfinite(stop) & (stop < c)
    df["_rc_stop"] = stop
    return m


def rs_spydip_orh(df, D):
    key = keys(df)
    c, l = df["close"].to_numpy(float), df["low"].to_numpy(float)
    tod = df["tod"].to_numpy(int)
    hod = c + df["dist_hod_atr"].to_numpy(float) * df["atr_d"].to_numpy(float)
    orh = pd.Series(np.where(tod == 950, hod, np.nan)).groupby(key, sort=False).transform("first").to_numpy(float)
    ctx = df[["date", "tod", "spy_fo"]].drop_duplicates(["date", "tod"]).sort_values(["date", "tod"])
    ctx["spy_max"] = ctx.groupby("date")["spy_fo"].cummax()
    spy_max = df[["date", "tod"]].merge(ctx[["date", "tod", "spy_max"]], on=["date", "tod"], how="left")["spy_max"].to_numpy(float)
    spy = df["spy_fo"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        m = (spy <= spy_max - D) & ((df["fromOpen"].to_numpy(float) - spy) >= 1.0) & \
            (df["vwapDistPct"].to_numpy(float) > 0) & (shift(c, 1, key) <= orh) & (c > orh) & \
            (df["volumeRatio"].to_numpy(float) >= 1.5)
    lo = np.fmin(np.fmin(l, shift(l, 1, key)), shift(l, 2, key))
    stop = lo - 0.01
    m &= np.isfinite(stop) & (stop < c) & np.isfinite(orh)
    df["_rc_stop"] = stop
    return m
