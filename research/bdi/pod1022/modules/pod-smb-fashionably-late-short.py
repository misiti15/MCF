"""pod-smb-fashionably-late-short - Fashionably Late: EMA9 crosses a flat or rising VWAP after a stretched extreme,
measured-move bracket (SHORT side; the LONG side is pod-smb-fashionably-late-long, the same code with SIDE flipped).

Source: SMB Capital / SMB Training 'The Fashionably Late Scalp Cheat Sheet' (2024, one of the Scalp Radar scalps);
TradingView community port (fabiajero). MERGED from pod-smb-fashionably-late-ema9xvwap-mm, pod-smb-fashionably-late,
pod-smb-fashionably-late-long.
URL: https://www.smbtraining.com/blog/wp-content/uploads/2024/04/The-Fashionably-Late-Scalp-Cheat-Sheet.pdf

VARIANT of R02 VWAP reclaim and R10 / wi-ema-cross EMA crosses (failed) and JD 9-EMA+VWAP ride (failed). Stated
change: the trigger is EMA9 crossing VWAP (not price), after a divergence leg far from VWAP, with a structural
measured-move bracket instead of R multiples.

EMA9: the continuous 5-minute EMA9 behind the frame's emaDiff, recovered exactly (seeds solved from the day's first two
rows; same method as pod-bbt-parabolic-ema9-snapback-short). SPY session low / high: SPY's own frame rows at the same
(date, tod) (close - dist_lod_atr x atr_d). No SPY row -> no trade.

Pre-declared values inside the source ranges (no tuning): adv20 floor $20M (range $20-50M), minimum measured move
0.2 x daily ATR (range 0.15-0.3), VWAP slope compared with the VWAP 6 bars ago (range 3-6).

Rules (plain English), decision bar i (LONG; SHORT = mirror):
  1. adv20 >= $20M and the max volumeSurge of today's bars up to i >= 1.3.
  2. The low of day (its bar inside the frame, set 6-30 bars before i) was >= 0.6 x daily ATR below VWAP at that bar,
     or the minimum vwapDistPct of today up to i <= -1.0%. (A low of day set before 09:50 is outside the frame and
     does not qualify.)
  3. EMA9 rising over 3 bars (EMA9_i > EMA9_{i-3}); VWAP flat or falling: VWAP_i <= VWAP_{i-6} x 1.0002.
  4. Trigger: EMA9 crosses above VWAP on this bar (EMA9_{i-1} <= VWAP_{i-1}, EMA9_i > VWAP_i) and close_i > VWAP_i;
     SPY close >= 0.2% above SPY's session low.
  M = close_i - LOD; skip if M < 0.2 x or > 1.5 x daily ATR. Entry: close_i, bar close 10:00-14:00, one per
  symbol-day. Stop (GEOM S): entry - M/3. Target: entry + M. Flat 15:55. Costs in (scorer).
  SHORT: HOD >= 0.6 ATR above VWAP (or max vwapDistPct >= +1.0%), EMA9 falling, VWAP flat or rising
  (VWAP_i >= VWAP_{i-6} x 0.9998), EMA9 crosses below VWAP, close < VWAP, SPY >= 0.2% below its session high,
  M = HOD - close, stop entry + M/3, target entry - M.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "S"
WINDOW = (1000, 1400)
MIN_ADV = 20e6
CONTEXT = []
LAYERS = ["adv20 >= $20M, max volumeSurge today >= 1.3",
          "day extreme 6-30 bars ago >= 0.6 ATR beyond VWAP (or |vwapDistPct| extreme >= 1%)",
          "EMA9 turning over 3 bars, VWAP flat or against (vs 6 bars ago, 0.02%)",
          "EMA9 crosses VWAP this bar, close beyond VWAP, SPY >= 0.2% off its session extreme",
          "measured move M 0.2-1.5 ATR: stop M/3, target M", "10:00-14:00 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _ema9(b, e, c, ed):
    out = np.full(len(c), np.nan)
    a9, a21 = 0.2, 2.0 / 22.0
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if i1 - i0 < 2:
            continue
        d0, d1 = ed[i0] / 100.0, ed[i0 + 1] / 100.0
        den = (1 - a9) * (1 + d0) - (1 - a21) * (1 + d1)
        if den == 0.0 or d0 != d0 or d1 != d1:
            continue
        E = (a21 * c[i0 + 1] * (1 + d1) - a9 * c[i0 + 1]) / den
        e9 = (1 + d0) * E
        for i in range(i0 + 1, i1):
            e9 = a9 * c[i] + (1 - a9) * e9
            out[i] = e9
    return out


def _spy_cols(df, cols):
    """SPY's own row values at the same (date, tod), aligned to df (NaN where SPY is absent)."""
    key = pd.DataFrame({"date": df["date"].to_numpy(), "tod": df["tod"].to_numpy()})
    sp = df.loc[df["symbol"].astype(str) == "SPY", ["date", "tod"] + cols].drop_duplicates(["date", "tod"])
    sp = sp.rename(columns={c: "spy_" + c for c in cols})
    j = key.merge(sp, on=["date", "tod"], how="left")
    return {c: j["spy_" + c].to_numpy(float) for c in cols}


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, x, vw, e9, vs, vd, spyoff, atr, sg, w0, w1):
    """sg = +1 long / -1 short. x = running LOD (long) or HOD (short)."""
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        mxs = -1e18
        ext = 1e18          # most extreme vwapDistPct today (signed so that smaller = more stretched)
        for i in range(i0, i1):
            mxs = max(mxs, vs[i])
            ext = min(ext, sg * vd[i])
            if i < i0 + 7 or tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and mxs >= 1.3):
                continue
            # 4. EMA9 crosses VWAP, close beyond VWAP, SPY off its extreme
            if not (sg * (e9[i] - vw[i]) > 0 and sg * (e9[i - 1] - vw[i - 1]) <= 0 and sg * (c[i] - vw[i]) > 0):
                continue
            if not (spyoff[i] >= 0.2):
                continue
            # 3. EMA9 turning, VWAP flat or against
            if not (sg * (e9[i] - e9[i - 3]) > 0):
                continue
            if sg > 0:
                if not (vw[i] <= vw[i - 6] * 1.0002):
                    continue
            else:
                if not (vw[i] >= vw[i - 6] * 0.9998):
                    continue
            # 2. day extreme bar inside the frame, 6-30 bars ago
            X = x[i]
            jx = -1
            for k in range(i, i0 - 1, -1):
                v = l[k] if sg > 0 else h[k]
                if abs(v - X) <= 1e-6 * max(abs(X), 1.0):
                    jx = k
                    break
            if jx < 0 or i - jx < 6 or i - jx > 30:
                continue
            stretched = sg * (vw[jx] - X) >= 0.6 * a or ext <= -1.0
            if not stretched:
                continue
            M = sg * (c[i] - X)
            if M < 0.2 * a or M > 1.5 * a:
                continue
            m[i] = True
            stop[i] = c[i] - sg * M / 3.0
            tgt[i] = c[i] + sg * M
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    sg = 1 if SIDE == "long" else -1
    sp = _spy_cols(df, ["close", "dist_lod_atr", "dist_hod_atr", "atr_d"])
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + f("vwapDistPct") / 100)
        if sg > 0:
            x = c - f("dist_lod_atr") * atr
            slo = sp["close"] - sp["dist_lod_atr"] * sp["atr_d"]
            spyoff = (sp["close"] / slo - 1) * 100
        else:
            x = c + f("dist_hod_atr") * atr
            shi = sp["close"] + sp["dist_hod_atr"] * sp["atr_d"]
            spyoff = (1 - sp["close"] / shi) * 100
    b, e = _segments(df)
    e9 = _ema9(b, e, c, f("emaDiff"))
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), x, vw, e9, f("volumeSurge"),
                   f("vwapDistPct"), spyoff, atr, sg, WINDOW[0], WINDOW[1])


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
