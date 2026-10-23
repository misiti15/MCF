"""pod-cwt2-shapiro-ps60-hourly-pivot-long - PS60 hourly pivot confirmation with room to the next level (LONG).

Source: Chat With Traders ep 66, Dan Shapiro (PS60); paraphrased record research/bdi/cwt/extract key ep066.
URL: https://chatwithtraders.com

VARIANT of pod-traderlion-orh60-leader-long (60-min OPENING range only) and cwt-a-a3 PDH breakout (failed).
Stated change: a rolling hourly pivot after 11:00, a two-bar confirmation and a 'room to the next level' gate; no
opening-range or PDH trigger. Not a copy of bdi-reddit1012-liquidity-sweep (60-min swings for reversals).

Rules (plain English):
  1. Clock-hour bars are built from the 5-min bars per symbol-day, closing 10:30, 11:30, 12:30, 13:30, 14:30. The
     10:30 bar uses the running high / low of day at 10:30 (so it includes the 09:30-09:45 bars the frame lacks).
  2. Pivot: a completed hourly bar H1 (closing 11:30 or later) closes above the high of the hourly bar before it (H0).
  3. Confirmation: a 5-min close above H1's high during the NEXT clock hour; that bar is the entry bar.
  4. Room: the nearest overhead level among the PDH (when above), the high of day (when above the close) and the next
     whole-number level above (the dist_round_atr grid: $5 >= $100, $1 >= $20, else $0.5) is >= 0.75 x atr_d above
     the entry. If the close is already above the PDH and at the high of day (HOD - close <= 0.10 x atr_d,
     pre-declared reading of 'at the HOD') the room counts as open.
  5. SPY's 60-min return at the entry bar (from spy_fo, 12 bars back) is >= 0.
  Entry: that close, bar close 11:30-14:30. Stop (GEOM S): H1 low - 0.05 x atr_d. Target: the nearest overhead level
  when room was measured; with open room no target (hold to 15:55). First qualifying signal per symbol-day.
Pre-declared choices: 'at the HOD' = within 0.10 x atr_d. The source's trail alternative (holdtr) is not scored in
this file. No tweak used. No tuning on the valid period. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1130, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["hourly pivot: completed hour H1 (>= 11:30 close) closes above prior hour high",
          "5-min close above H1 high in the next hour", "room >= 0.75 ATR to PDH / HOD / round (or open room)",
          "SPY 60-min return >= 0", "stop H1 low - 0.05 ATR, target nearest overhead level", "11:30-14:30 ET"]

import numpy as np
import pandas as pd

_ST = {}
NB = 7


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _lag(x, k, n=1):
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def hourly(df, k, tod, h, l, c, hod, lod):
    """Per (symbol-day, clock-hour bin) high / low / close of COMPLETED bins (NaN when the closing bar is missing)."""
    mins = (tod // 100) * 60 + tod % 100
    b = np.where(mins <= 630, 0, np.ceil((mins - 630) / 60.0)).astype(np.int64)
    endm = 630 + 60 * b
    nk = int(k.max()) + 1
    HH = np.full((nk, NB), np.nan)
    HL = np.full((nk, NB), np.nan)
    HC = np.full((nk, NB), np.nan)
    ok = b < NB
    g = pd.DataFrame({"k": k[ok], "b": b[ok], "h": h[ok], "l": l[ok]})
    agg = g.groupby(["k", "b"], sort=False).agg(h=("h", "max"), l=("l", "min"))
    kk = agg.index.get_level_values(0).to_numpy()
    bb = agg.index.get_level_values(1).to_numpy()
    HH[kk, bb] = agg["h"].to_numpy()
    HL[kk, bb] = agg["l"].to_numpy()
    endbar = ok & (mins == endm)
    HC[k[endbar], b[endbar]] = c[endbar]
    e0 = tod == 1030
    HH[k[e0], 0] = hod[e0]
    HL[k[e0], 0] = lod[e0]
    inc = np.isnan(HC)
    HH[inc] = np.nan
    HL[inc] = np.nan
    return b, mins == endm, HH, HL, HC


def _round_above(c, px):
    step = np.where(px >= 100, 5.0, np.where(px >= 20, 1.0, 0.5))
    r = np.ceil(c / step) * step
    return np.where(r <= c + 1e-9, r + step, r)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n or "spy_fo" not in df:
        return np.zeros(n, dtype=bool)
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        pdh = c + _f(df, "dist_pdh_atr") * atr
        b, _, HH, HL, HC = hourly(df, k, tod, h, l, c, hod, lod)
        j = b - 1                                           # H1 = the hour before the current one (completed)
        jj = np.clip(j, 0, NB - 1)
        j0 = np.clip(j - 1, 0, NB - 1)
        h1h, h1l, h1c = HH[k, jj], HL[k, jj], HC[k, jj]
        h0h = HH[k, j0]
        m = (j >= 1) & (h1c > h0h) & (c > h1h)
        # room
        lv = np.full(n, np.inf)
        lv = np.where(pdh > c, np.minimum(lv, pdh), lv)
        lv = np.where(hod > c + 1e-9, np.minimum(lv, hod), lv)
        lv = np.minimum(lv, _round_above(c, c))
        room = (lv - c) >= 0.75 * atr
        openroom = (c > pdh) & ((hod - c) <= 0.10 * atr)
        m &= room | openroom
        tgt = np.where(openroom, np.nan, lv)
        # SPY 60-min return >= 0
        spy = 1 + _f(df, "spy_fo") / 100
        m &= (spy / _lag(spy, k, 12) - 1) >= 0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = h1l - 0.05 * atr
        m &= np.isfinite(stop) & (stop < c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    t = _get(f, i, 1)
    return t if np.isfinite(t) else float(f["close"].iloc[i]) * 10.0   # open room: unreachable limit = hold to 15:55
