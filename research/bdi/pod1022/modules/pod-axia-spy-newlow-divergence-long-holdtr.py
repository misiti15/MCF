"""pod-axia-spy-newlow-divergence-long-holdtr - GEOM holdtr check (same mask as pod-axia-spy-newlow-divergence-long; stop 1R = 0.25 x atr_d, 1R trail once
+1R, no target, flat 15:55). Relative absorption: SPY makes a new session low, the stock refuses to
(correlation divergence); buy the SPY turn (LONG). Structural stop under the t0 low, 1R target. The GEOM holdtr
check is pod-axia-spy-newlow-divergence-long-holdtr.py (same mask).

Source: Axia Futures order-flow lectures (correlated-market divergence / 'who is not participating in the move') +
Jigsaw Trading 'Practical Application of Order Flow' Pt 1 (holding a level while the market sells). Not re-fetched
this round.
URL: https://www.jigsawtrading.com/wp-content/uploads/2014/03/PracticalApplicationOfOrderFlow-Pt1.pdf

VARIANT of the backlog idea 'Relative strength vs SPY, long only, 10:30-11:30, no market filter' (and close kin of
pod-cwt-mcdermitt-rs-hold-at-index-newlow-long, scored with --ref for the duplicate check). Stated change: event-
driven - it triggers only on an SPY new-session-low bar where the stock HOLDS above its own low, and it enters on the
SPY reversal (SPY and the stock both close above their t0 highs), across a wider window.

Rules (plain English, LONG, 5-min bars):
  1. Bar t0 closes 10:30-14:30. SPY's t0 low is a new session low at least 0.1% below SPY's previous session low
     (SPY's running low of day before t0, from the SPY rows of the frame; it includes 09:30-09:45).
  2. On t0 the stock's low is >= 0.30 x ATR5m(14) above its own session low, and that session low was set >= 6 bars
     earlier (the running low of day at t0 equals the one 6 bars before).
  3. Beta-adjusted relative return: stock fromOpen - beta x SPY fromOpen >= +0.3 (%), beta = 60-session daily beta
     to SPY as of D-1's close (completed days only; >= 40 sessions; clipped to 0..3 as a numeric guard).
  4. The stock closes in the upper half of the t0 bar.
  Entry: the first bar within 4 bars after t0 where SPY closes above SPY's t0 high AND the stock closes above its t0
  high (entry bar close <= 14:50). Stop (GEOM S): the stock's t0 low - 0.05 x ATR5m, capped at 1.5 x ATR5m below the
  entry. Target: 1R. Flat 15:55. One trade per symbol per day (scorer: first qualifying bar).
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "holdtr"
WINDOW = (1035, 1450)
CONTEXT = ["spy_fo"]
LAYERS = ["t0 10:30-14:30: SPY new session low >= 0.1% below its prior low", "stock low >= 0.30 ATR5m above its LOD, LOD >= 6 bars old",
          "fromOpen - beta x spy_fo >= 0.3%", "stock closes in the upper half of t0",
          "entry within 4 bars: SPY and stock close above their t0 highs", "stop t0 low - 0.05 ATR5m (cap 1.5 ATR5m), target 1R"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _segs(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _lib():
    try:
        import lib
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib


def _base(df):
    """Point-in-time levels per row (all from the bar itself or earlier / completed prior days)."""
    c, atr = _f(df, "close"), _f(df, "atr_d")
    b = dict(c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr, tod=df["tod"].to_numpy(np.int64))
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") / 100 * c               # 5m ATR(14), $
    return b


def _prev_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    y, mo = (y - 1, 12) if mo == 1 else (y, mo - 1)
    return f"{y:04d}-{mo:02d}"


def _open_month(m):
    """True only for an OPEN month (never the rule-19 locked block)."""
    L = _lib()
    return m not in L.LOCKED_MONTHS and m in set(L.months())


def mask(df) -> np.ndarray:
    n = len(df)
    try:
        m, stop, tgt = _compute(df)
    except KeyError:
        m, stop, tgt = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
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


def _beta_table():
    if "beta" in _DC:
        return _DC["beta"]
    d = _lib().daily()[["symbol", "date", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    p = d.pivot_table(index="date", columns="symbol", values="close").sort_index()
    r = p.pct_change(fill_method=None)
    dt = pd.to_datetime(pd.Series(p.index))
    gapm = np.r_[False, (dt.diff().dt.days.to_numpy()[1:] > 7)]
    r.loc[gapm] = np.nan                                # no return across the (absent) locked block
    s = r["SPY"].to_numpy(float)
    R = r.to_numpy(float)
    S = np.repeat(s[:, None], R.shape[1], axis=1)
    ok = np.isfinite(R) & np.isfinite(S)
    R = np.where(ok, R, np.nan)
    S = np.where(ok, S, np.nan)
    roll = lambda x: pd.DataFrame(x).rolling(60, min_periods=40).mean().to_numpy(float)
    mr, ms, mrs, mss = roll(R), roll(S), roll(R * S), roll(S * S)
    with np.errstate(invalid="ignore", divide="ignore"):
        beta = (mrs - mr * ms) / (mss - ms * ms)
    beta = pd.DataFrame(beta, index=p.index, columns=p.columns).shift(1)   # row D = beta through D-1
    t = beta.stack().rename("beta").reset_index()
    t.columns = ["date", "symbol", "beta"]
    _DC["beta"] = t
    return t


def _map_beta(df, k):
    t = _beta_table()
    st = np.r_[True, k[1:] != k[:-1]]
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    v = u.merge(t, on=["symbol", "date"], how="left")["beta"].to_numpy(float)
    return np.clip(v, 0.0, 3.0)[np.cumsum(st) - 1]


def _map_spy(df, b):
    sym = df["symbol"].astype(str).to_numpy()
    sp = sym == "SPY"
    n = len(df)
    if not sp.any():
        return None
    ds = df["date"].astype(str).to_numpy()
    s = pd.DataFrame({"date": ds[sp], "tod": b["tod"][sp], "sh": b["h"][sp], "sl": b["l"][sp], "sc": b["c"][sp],
                      "slod": b["lod"][sp]}).drop_duplicates(["date", "tod"]).sort_values(["date", "tod"])
    s["slodp"] = s.groupby("date")["slod"].shift(1)       # SPY low of day BEFORE this bar
    k = pd.DataFrame({"date": ds, "tod": b["tod"]})
    m = k.merge(s, on=["date", "tod"], how="left")
    assert len(m) == n
    return {c: m[c].to_numpy(float) for c in ("sh", "sl", "sc", "slodp")}


@numba.njit(cache=False)
def _kernel(bs, be, tod, c, h, l, lod, atr5, rel, sh, sl, sc, slodp):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(bs)):
        i0, i1 = bs[s], be[s]
        for t in range(i0 + 6, i1):
            if tod[t] < 1030 or tod[t] > 1430:
                continue
            a = atr5[t]
            if not (a > 0):
                continue
            if not (np.isfinite(slodp[t]) and sl[t] < slodp[t] * (1 - 0.001)):          # (1)
                continue
            if not (l[t] >= lod[t] + 0.30 * a):                                         # (2)
                continue
            if abs(lod[t] - lod[t - 6]) > 1e-6 * c[t]:
                continue
            if not (rel[t] >= 0.3):                                                     # (3)
                continue
            if not (c[t] - l[t] >= 0.5 * (h[t] - l[t])):                                # (4)
                continue
            for j in range(t + 1, min(t + 5, i1)):
                if tod[j] > 1450:
                    break
                if np.isfinite(sc[j]) and sc[j] > sh[t] and c[j] > h[t]:
                    sp = l[t] - 0.05 * a
                    sp = max(sp, c[j] - 1.5 * a)
                    if sp < c[j] and not m[j]:
                        m[j] = True
                        stop[j] = sp
                        tgt[j] = c[j] + (c[j] - sp)
                    break
    return m, stop, tgt


def _compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if not n or "spy_fo" not in df:
        return z
    b = _base(df)
    sp = _map_spy(df, b)
    if sp is None:
        return z
    k = _key(df)
    beta = _map_beta(df, k)
    rel = _f(df, "fromOpen") - beta * _f(df, "spy_fo")
    bs, be = _segs(k)
    return _kernel(bs, be, b["tod"], b["c"], b["h"], b["l"], b["lod"], b["atr5"], rel,
                   sp["sh"], sp["sl"], sp["sc"], sp["slodp"])
