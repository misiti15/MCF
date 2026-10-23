"""pod-vsa-stopping-volume-no-supply-test-long - Stopping volume at the low, then a low-volume 'no supply' retest
(secondary test) long.

Source: Trader Dante (Tom Dante) volume-spread / 'effort vs result' teaching + Jigsaw Trading (Peter Davies)
'Confirming Day Trading Levels with Order Flow' (absorption, then the retest that shows no sellers). Not re-fetched
this round (web budget used up); the URL is the Jigsaw PDF already cited in pod1022.
URL: https://www.jigsawtrading.com/wp-content/uploads/2013/11/ConfirmingLevelsWithOrderFlow.pdf

VARIANT of pod-of-absorption-bar-level-long. Change: it does not buy the break of the absorption bar; it waits for a
second, LOW-volume test of the low (the Wyckoff/VSA secondary test).
Rules (plain English, 5-minute bars):
  1. Stopping bar S: its low is the session low so far, or within 0.1 x ATR14d of PDL. Volume >= 2.0x average
     (volumeRatio >= 2.0). Close in the upper 50% of its range.
  2. Over the next 2-12 bars, price rises at least 0.3 x ATR5m(14) above S.low (max high of S+1..S+12, before T).
  3. Test bar T (3-20 bars after S; no bar between S and T undercuts S.low by more than 0.1 x ATR5m): low within
     +-0.15 x ATR5m of S.low and not more than 0.1 x ATR5m below it. volumeRatio(T) <= 0.6 x volumeRatio(S) and
     <= 1.0. Range <= 0.8 x the average range of the 20 bars before T. Close in the upper half.
  4. SPY did not make a new session low on bar T (spy_fo below its lowest earlier value today).
  Entry: the bar right after T closes above T.high, bar close 10:00-14:30. Stop (GEOM S): min(S.low, T.low) -
  0.05 x ATR5m. Target: 1R, or the S-to-T swing high if that lies between the entry and 1R. Flat 15:55.
  One trade per symbol per day (scorer: first signal).
Harness approximations (data, not tuning): no raw volume in the frames, so 'volume vs 20-bar average for that time
of day' is volumeRatio (vs the plain 20-bar average) and T.volume / S.volume is taken as volumeRatio(T) /
volumeRatio(S); the OR30-low level is dropped because the frames start at 09:50; SPY's session low uses SPY's 5m
closes (spy_fo), not its lows. No tweak made.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["S: session low or PDL +-0.1 ATR, volumeRatio >= 2, close upper half",
          "rise >= 0.3 ATR5m within 2-12 bars", "T: retest S.low +-0.15 ATR5m, vr <= 0.6 x S and <= 1, narrow, close upper half",
          "SPY no new session low on T", "next bar closes above T.high", "stop min low - 0.05 ATR5m, target 1R or swing high"]
_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _base(df):
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=tod, c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr          # prior completed day's low
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") * c / 100                # 5-minute ATR(14), $
    return b


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    if s is None or s[j] is None:
        return float("nan")
    return float(s[j][i])


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


@numba.njit(cache=False)
def _scan(st, h, l, c, lod, pdl, atr, atr5, vr, rng20, spynl):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    rng = h - l
    gs = 0
    for i in range(n):
        if st[i]:
            gs = i
        T = i - 1
        if T < gs + 3:
            continue
        if not (c[i] > h[T]):
            continue
        a5 = atr5[T]
        if not (a5 > 0) or rng[T] <= 0:
            continue
        if not (vr[T] <= 1.0 and rng[T] <= 0.8 * rng20[T] and (c[T] - l[T]) >= 0.5 * rng[T] and not spynl[T]):
            continue
        for S in range(T - 3, max(gs, T - 20) - 1, -1):
            if rng[S] <= 0 or vr[S] < 2.0 or (c[S] - l[S]) < 0.5 * rng[S]:
                continue
            tol = 1e-5 * c[S]
            if not (l[S] <= lod[S] + tol or abs(l[S] - pdl[S]) <= 0.1 * atr[S]):
                continue
            ls = l[S]
            if not (abs(l[T] - ls) <= 0.15 * a5 and l[T] >= ls - 0.1 * a5):
                continue
            if not (vr[T] <= 0.6 * vr[S]):
                continue
            ok = True
            hi = -1e18
            for j in range(S + 1, T):
                if l[j] < ls - 0.1 * a5:
                    ok = False
                    break
                if h[j] > hi:
                    hi = h[j]
            if not ok:
                continue
            rise = -1e18
            for j in range(S + 1, min(S + 12, T - 1) + 1):
                if h[j] > rise:
                    rise = h[j]
            if rise < ls + 0.3 * a5:
                continue
            sp = min(ls, l[T]) - 0.05 * a5
            r = c[i] - sp
            if r <= 0:
                continue
            m[i] = True
            stop[i] = sp
            tg = c[i] + r
            if hi > c[i] and hi < tg:
                tg = hi
            tgt[i] = tg
            break
    return m, stop, tgt


def _spy_newlow(df):
    """True on (date, tod) bars where SPY's close-vs-open (spy_fo) is below every earlier value of that day."""
    ctx = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": df["tod"].to_numpy(np.int64),
                        "s": _f(df, "spy_fo")}).drop_duplicates(["date", "tod"]).sort_values(["date", "tod"])
    prev_min = ctx.groupby("date")["s"].transform(lambda x: x.cummin().shift(1))
    ctx["nl"] = (ctx["s"] < prev_min).to_numpy()
    key = pd.MultiIndex.from_frame(ctx[["date", "tod"]])
    s = pd.Series(ctx["nl"].to_numpy(), index=key)
    q = pd.MultiIndex.from_arrays([df["date"].astype(str).to_numpy(), df["tod"].to_numpy(np.int64)])
    return s.reindex(q).fillna(False).to_numpy(bool)


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l = b["k"], b["tod"], b["c"], b["h"], b["l"]
    sym = pd.factorize(df["symbol"].astype(str).to_numpy())[0]
    with np.errstate(invalid="ignore", divide="ignore"):
        rngs = pd.Series(h - l)
        rng20 = rngs.groupby(sym).transform(lambda x: x.shift(1).rolling(20, min_periods=20).mean()).to_numpy(float)
        m, stop, tgt = _scan(_start(k), h, l, c, b["lod"], b["pdl"], b["atr"], b["atr5"], _f(df, "volumeRatio"),
                             rng20, _spy_newlow(df))
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
