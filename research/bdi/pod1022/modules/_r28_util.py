"""_r28_util - shared helpers for the pod r2_8 modules (TD Sequential, Elder-Ray, ConnorsRSI, OU half-life, hidden
divergence, SPY-new-high loser reversal). Not a setup (no SIDE / mask).

All series are causal: a value at row t uses rows <= t of the same group only. Two group keys are used:
  * day key (symbol + date): resets every session;
  * symbol key: a continuous 5-minute chart across the sessions present in the frame (the frame has 09:50-15:00 bars
    only, and blackout days are missing, so 'spanning days' means across the bars the frame carries).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd


def f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def daykey(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def symkey(df):
    return pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()))[0]


def start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def lag(x, k, n=1):
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def roll_mean(x, k, n):
    return pd.Series(np.asarray(x, float)).groupby(k).transform(lambda s: s.rolling(n, min_periods=n).mean()).to_numpy()


def roll_std(x, k, n):
    return pd.Series(np.asarray(x, float)).groupby(k).transform(lambda s: s.rolling(n, min_periods=n).std()).to_numpy()


def roll_min(x, k, n):
    return pd.Series(np.asarray(x, float)).groupby(k).transform(lambda s: s.rolling(n, min_periods=n).min()).to_numpy()


def roll_max(x, k, n):
    return pd.Series(np.asarray(x, float)).groupby(k).transform(lambda s: s.rolling(n, min_periods=n).max()).to_numpy()


@numba.njit(cache=False)
def ema(x, st, span):
    a = 2.0 / (span + 1.0)
    out = np.full(len(x), np.nan)
    prev = np.nan
    for i in range(len(x)):
        if st[i]:
            prev = np.nan
        v = x[i]
        if np.isnan(v):
            out[i] = prev
            continue
        prev = v if np.isnan(prev) else a * v + (1 - a) * prev
        out[i] = prev
    return out


@numba.njit(cache=False)
def rsi_wilder(x, st, n):
    """Wilder RSI(n) of series x per group (seeded with the simple mean of the first n changes)."""
    out = np.full(len(x), np.nan)
    ag = 0.0
    al = 0.0
    cnt = 0
    for i in range(len(x)):
        if st[i]:
            ag = 0.0
            al = 0.0
            cnt = 0
            continue
        d = x[i] - x[i - 1]
        if np.isnan(d):
            continue
        g = d if d > 0 else 0.0
        lo = -d if d < 0 else 0.0
        cnt += 1
        if cnt <= n:
            ag += g / n
            al += lo / n
            if cnt < n:
                continue
        else:
            ag = (ag * (n - 1) + g) / n
            al = (al * (n - 1) + lo) / n
        if al == 0.0:
            out[i] = 100.0 if ag > 0 else 50.0
        else:
            out[i] = 100.0 - 100.0 / (1.0 + ag / al)
    return out


@numba.njit(cache=False)
def streak(c, st):
    out = np.full(len(c), np.nan)
    s = 0.0
    for i in range(len(c)):
        if st[i]:
            s = 0.0
            out[i] = 0.0
            continue
        if c[i] > c[i - 1]:
            s = s + 1 if s > 0 else 1.0
        elif c[i] < c[i - 1]:
            s = s - 1 if s < 0 else -1.0
        else:
            s = 0.0
        out[i] = s
    return out


@numba.njit(cache=False)
def pct_rank(x, st, n):
    """Share of the previous n values (same group) strictly below the current one, x 100 (ConnorsRSI form)."""
    out = np.full(len(x), np.nan)
    g0 = 0
    for i in range(len(x)):
        if st[i]:
            g0 = i
        if i - g0 < n or np.isnan(x[i]):
            continue
        below = 0
        tot = 0
        for j in range(i - n, i):
            if not np.isnan(x[j]):
                tot += 1
                if x[j] < x[i]:
                    below += 1
        if tot == n:
            out[i] = 100.0 * below / n
    return out


@numba.njit(cache=False)
def ar1_beta(lc, st, n):
    """OLS slope of d(log close) on lagged log close over the last n bars (n-1 pairs) of the same group."""
    out = np.full(len(lc), np.nan)
    g0 = 0
    for i in range(len(lc)):
        if st[i]:
            g0 = i
        if i - g0 < n - 1:
            continue
        m = n - 1
        sx = 0.0
        sy = 0.0
        for j in range(i - m + 1, i + 1):
            sx += lc[j - 1]
            sy += lc[j] - lc[j - 1]
        mx = sx / m
        my = sy / m
        cxy = 0.0
        vxx = 0.0
        for j in range(i - m + 1, i + 1):
            dx = lc[j - 1] - mx
            cxy += dx * (lc[j] - lc[j - 1] - my)
            vxx += dx * dx
        if vxx > 0:
            out[i] = cxy / vxx
    return out


def ctx_ok(df, cols):
    return all(c in df for c in cols)
