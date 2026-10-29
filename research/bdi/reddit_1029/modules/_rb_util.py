"""_rb_util - shared helpers for the reddit_1029 modules (not a setup). Keyed shifts within symbol-day.
Educational only - not financial advice."""
import numpy as np
import pandas as pd


def keys(df):
    return df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()


def shift(df, col_or_arr, k, key=None):
    """Value k bars back within the same symbol-day (NaN when not available)."""
    key = keys(df) if key is None else key
    a = df[col_or_arr].to_numpy(float) if isinstance(col_or_arr, str) else np.asarray(col_or_arr, float)
    out = np.full(len(a), np.nan)
    if k < len(a):
        same = key[k:] == key[:-k]
        out[k:] = np.where(same, a[:-k], np.nan)
    return out


def three_bar_play(df, K, inplay):
    key = keys(df)
    h, l, c = (df[x].to_numpy(float) for x in ("high", "low", "close"))
    atr5 = df["atrPct"].to_numpy(float) / 100.0 * c
    vr = df["volumeRatio"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        rng = h - l
        ign = (rng >= K * atr5) & (vr >= 2.0) & ((c - l) >= 0.75 * rng) & (c > shift(df, c, 1, key))
    ign = np.where(np.isnan(ign.astype(float)), False, ign)
    m = np.zeros(len(df), bool)
    rest_low = np.full(len(df), np.nan)
    for nrest in (1, 2):
        j = nrest + 1                          # igniting bar is j bars before the trigger bar
        ig = shift(df, ign.astype(float), j, key) == 1
        ih = shift(df, h, j, key); il = shift(df, l, j, key); mid = (ih + il) / 2
        ok = ig.copy(); rh = np.full(len(df), -np.inf); rl = np.full(len(df), np.inf)
        for r in range(1, nrest + 1):
            hr = shift(df, h, r, key); lr = shift(df, l, r, key)
            with np.errstate(invalid="ignore"):
                ok &= (hr <= ih) & (lr >= mid)
            rh = np.fmax(rh, hr); rl = np.fmin(rl, lr)
        with np.errstate(invalid="ignore"):
            trig = ok & (c > rh)
        new = trig & ~m
        rest_low = np.where(new, rl, rest_low)
        m |= trig
    if inplay:
        with np.errstate(invalid="ignore"):
            m &= (df["gap"].to_numpy(float) >= 1.0) & (df["fromOpen"].to_numpy(float) >= 1.0)
    df["_rb_stop"] = rest_low - 0.01
    m &= np.isfinite(rest_low) & (rest_low < c)
    return m


def vwap_z(df, key=None):
    key = keys(df) if key is None else key
    v = df["vwapDistPct"].to_numpy(float)
    s = pd.Series(v)
    g = s.groupby(key, sort=False)
    sd = g.transform(lambda x: x.expanding(min_periods=6).std()).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        return v / sd


def vwap_absorb(df, proxy):
    key = keys(df)
    z = vwap_z(df, key)
    h, l, c = (df[x].to_numpy(float) for x in ("high", "low", "close"))
    with np.errstate(invalid="ignore"):
        ext = np.zeros(len(df), bool)
        for k in (1, 2, 3):
            ext |= shift(df, z, k, key) <= -2.0
        m = ext & (z > -2.0) & (c > shift(df, h, 1, key))
        if proxy == "A":
            bd = df["bull_div"].to_numpy(float)
            d = bd == 1
            for k in (1, 2):
                d |= shift(df, bd, k, key) == 1
            m &= d
        else:
            m &= df["flow3"].to_numpy(float) > 0
    lo = l.copy()
    for k in (1, 2, 3):
        lo = np.fmin(lo, shift(df, l, k, key))
    df["_rb_stop"] = lo - 0.01
    vw = c / (1.0 + df["vwapDistPct"].to_numpy(float) / 100.0)
    df["_rb_vwap"] = vw
    with np.errstate(invalid="ignore"):
        m &= (lo < c) & (vw > c)
    return np.asarray(m, bool)
