"""pod-of4-absorption-box-lower-third-long - High-volume compression box (multi-bar absorption) in the lower third of
the day, break up (LONG).

Source: Jigsaw Trading absorption ('one side cannot move price despite aggression') via NexusFi review; Bookmap
iceberg absorption article.
URL: https://nexusfi.com/a/platforms/jigsaw-daytradr

VARIANT of pod-of-absorption-bar-level (single bar). Change: absorption is measured over a 6-bar (30-min) window.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars).
  Box = the last 6 bars of the same day ending at bar k (box high / low = their max high / min low).
  1. At bar k the stock is >= 0.5 daily ATR below the high of day so far (HOD - close).
  2. Box volume (6-bar sum) >= 1.8x the mean of the same 6-bar sum at the same time of day over the 20 prior
     sessions; box height <= 0.45x the mean 6-bar (30-min) range at the same time of day over the 20 prior sessions
     (stated reading of '20d average 30-min range': same-time-of-day, so the midday lull is not compared with the
     open).
  3. Box high is in the lower third of the session range so far (box high <= LOD + (HOD - LOD) / 3).
  A qualifying box stays armed until a bar closes below its low or a newer box qualifies (the newer one replaces it).
  4. Entry: the first 5m close above the armed box high, bar close 10:30-15:00 (source says 15:15; the scorer clips
     at 15:00), with SPY inside its 09:30-10:30 range on that bar (no trend).
  Stop (GEOM S+x): box low - 0.05 x daily ATR. Target: entry + 2x box height, capped at the session midpoint
  ((HOD + LOD) / 2 at entry); no trade when the cap is not above the entry. Time stop 75 min (MAX_BARS 15). Flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r39_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 15
WINDOW = (1030, 1500)
LAYERS = ["HOD - close >= 0.5 ATR", "6-bar vol >= 1.8x same-tod 20d avg, height <= 0.45x same-tod 20d avg range",
          "box high in lower third of the day range", "close > box high, SPY inside its first-hour range",
          "stop box low - 0.05 ATR, target 2x box capped at session mid, 75 min time stop"]
_ST = {}


@numba.njit(cache=False)
def _six(nd, h, l, v):
    n = len(h)
    sv = np.full(n, np.nan)
    rr = np.full(n, np.nan)
    d0 = 0
    for i in range(n):
        if nd[i] >= 1:
            d0 = i
        if i - 5 >= d0:
            s = 0.0
            hi = -np.inf
            lo = np.inf
            ok = True
            for j in range(i - 5, i + 1):
                if not (v[j] == v[j]):
                    ok = False
                s += v[j]
                hi = max(hi, h[j])
                lo = min(lo, l[j])
            if ok:
                sv[i] = s
            rr[i] = hi - lo
    return sv, rr


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr, sv, rr, avsv, avrr):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    tg = np.full(n, np.nan)
    hod = -np.inf
    lod = np.inf
    bh = np.nan
    bl = np.nan
    for i in range(n):
        if nd[i] >= 1:
            hod = -np.inf
            lod = np.inf
            bh = np.nan
            bl = np.nan
        hod = max(hod, h[i])
        lod = min(lod, l[i])
        A = atr[i]
        if bh == bh:
            if c[i] > bh:
                tgt = min(c[i] + 2.0 * (bh - bl), (hod + lod) / 2.0)
                s = bl - 0.05 * A
                if tgt > c[i] and c[i] - s > 0:
                    m[i] = 1.0
                    st[i] = s
                    tg[i] = tgt
                bh = np.nan
                bl = np.nan
                continue
            if c[i] < bl:
                bh = np.nan
                bl = np.nan
        if A > 0 and sv[i] == sv[i] and avsv[i] > 0 and avrr[i] > 0:
            if hod - c[i] >= 0.5 * A and sv[i] >= 1.8 * avsv[i] and rr[i] <= 0.45 * avrr[i]:
                hi = -np.inf
                lo = np.inf
                for j in range(i - 5, i + 1):
                    hi = max(hi, h[j])
                    lo = min(lo, l[j])
                if hi <= lod + (hod - lod) / 3.0:
                    bh = hi
                    bl = lo
    return m, st, tg


def compute(df):
    n = len(df)
    X = U.vbars(df)
    if X is None or not len(X):
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    nd = U.flags(X)
    sv, rr = _six(nd, X["h"].to_numpy(float), X["l"].to_numpy(float), X["v"].to_numpy(float))
    X2 = X[["symbol", "dn", "tod"]].copy()
    X2["sv"], X2["rr"] = sv, rr
    avsv = U.same_tod_prior_mean(X2, "sv", 20)
    avrr = U.same_tod_prior_mean(X2, "rr", 20)
    r = U.run_kernel(df, _k, extra=(sv, rr, avsv, avrr))
    tod = df["tod"].to_numpy(np.int64)
    sp = U.spy_first_hour(df)
    with np.errstate(invalid="ignore"):
        inside = (sp["c"] >= sp["fh_l"]) & (sp["c"] <= sp["fh_h"])
        m = r["m"] & inside & (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (r["s"] < U.f(df, "close"))
    return m, r["s"], r["t"]


def mask(df):
    m, s, t = compute(df)
    _ST.clear()
    _ST[id(df)] = (s, t)
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
