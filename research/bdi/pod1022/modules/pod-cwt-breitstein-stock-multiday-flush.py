"""pod-cwt-breitstein-stock-multiday-flush - Multi-day stretched stock: intraday flush then snap-back. Config R
(RubberBand two-bar-high trigger; the primary). Config B (Breitstein higher-low trigger) is
pod-cwt-breitstein-stock-multiday-flush-B.py, which reuses this file with CFG = "B".

Source: Lance Breitstein, Chat With Traders 228/229/236 (multi-day extension, volume climax, wait for the turn); SMB
Capital Scalp Radar 'RubberBand Scalp' (Scribd write-up; SMBU journal 'must run at least two days in a row'). MERGED
from pod-cwt-breitstein-stock-multiday-flush and pod-smb-rubberband-2day-snapback.
URL: https://chatwithtraders.com/228

VARIANT of CWT05-flush (Testing 2), NS5 big-loser flush buy and the Testing 2 'Stretched Below VWAP Bounce'. Stated
changes: a multi-day down-run gate on daily bars plus a confirmed turn (not the first bar above the prior high).

Rules (plain English, LONG). Daily values come only from completed days (research/history2y daily table; a look-back
that spans a gap in the open table - the locked block - is dropped).
  Config R (RubberBand): the last 2 daily closes were both down (each below the close before it) and the 2-day decline
  (close d-1 minus close d-3) is >= 1.0 x daily ATR.
  Config B (Breitstein): the last 3 daily candles were red (close below open), the 5-day return is <= -3 x ATR% and the
  prior close is >= 2.5 daily ATR below the 20-day SMA of closes.
  Climax bar (10:00-14:30): fromOpen <= -1.0%; vwapDistPct <= -1.0% (B: <= -1.5 x atr_d / close, in %);
  volumeRatio >= 1.5 (B: >= 3); R: it closed below the lower 5-minute Bollinger band (20, 2; rolling over the
  symbol's frame bars, which carry no 09:30-09:45 or 15:05-15:55 bars); B: it made a fresh low of day.
  Trigger R: within 6 bars after a climax bar (pre-declared 6 of the source's 3-6), a green bar (close above the prior
  bar's close - the frame has no bar open) closing above max(high[i-1], high[i-2]).
  Trigger B: after a climax bar, the bounce runs until a bar fails to make a higher high (the pullback) while holding
  above the climax low; then the first close above the bounce high (the highest high from the climax to the pullback),
  within 6 bars of the climax (pre-declared 6). A new low below the climax low resets.
  Both: spy_fo > -1% at the trigger; entry at the trigger close, 10:00-14:30.
  Stop (GEOM S): R = lowest low of the last 4 bars - 0.02 x daily ATR; B = the climax low.
  Target: session VWAP at entry (if VWAP is not above the entry the trade holds to 15:55). Flat 15:55. Costs in.
No tweaks beyond picking 6 bars inside the stated 3-6 range. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CFG = "R"
CONTEXT = ["spy_fo"]
LAYERS = ["daily: 2 down closes, 2-day decline >= 1 ATR (R) | 3 red candles, 5d <= -3 ATR%, 2.5 ATR below SMA20 (B)",
          "climax bar: fromOpen <= -1%, vwapDistPct <= -1% (B -1.5 ATR%), volumeRatio >= 1.5 (B 3), below BB (R) / new LOD (B)",
          "trigger: green close above 2-bar high (R) | higher low then close above bounce high (B), within 6 bars",
          "spy_fo > -1%", "10:00-14:30", "stop 4-bar low - 0.02 ATR (R) / climax low (B), target VWAP at entry, flat 15:55"]

_ROOT = Path(__file__).resolve().parents[4]
_STASH = {}
_CACHE = {}


def _lib():
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    return lib


def _daily():
    if "daily" in _CACHE:
        return _CACHE["daily"]
    d = _lib().daily()[["symbol", "date", "open", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    gs = d.groupby("symbol", sort=False)
    c = d["close"]
    c1, c2, c3, c5 = (gs["close"].shift(k) for k in (1, 2, 3, 5))
    red = (d["close"] < d["open"])
    d["R_ok2"] = ((c < c1) & (c1 < c2)).astype(float)
    d["dec2"] = c - c2                                 # close d-1 minus close d-3, seen from day d
    d["B_red3"] = (red & gs["open"].shift(1).gt(c1) & gs["open"].shift(2).gt(c2)).astype(float)
    d["ret5"] = (c / c5 - 1) * 100
    d["sma20"] = gs["close"].transform(lambda x: x.rolling(20).mean())
    dt = pd.to_datetime(d["date"])
    sp2 = (dt - dt.groupby(d["symbol"]).shift(3)).dt.days
    sp20 = (dt - dt.groupby(d["symbol"]).shift(20)).dt.days
    d.loc[~(sp2 <= 9), ["R_ok2", "dec2", "B_red3"]] = np.nan
    d.loc[~(sp20 <= 36), ["ret5", "sma20"]] = np.nan
    d["next_date"] = gs["date"].shift(-1)
    d = d[(pd.to_datetime(d["next_date"]) - dt).dt.days <= 5]
    out = d[["symbol", "next_date", "close", "R_ok2", "dec2", "B_red3", "ret5", "sma20"]].rename(
        columns={"next_date": "date", "close": "pc_d"})
    for k in ("R_ok2", "B_red3"):
        out[k] = out[k].astype(float)
    _CACHE["daily"] = out
    return out


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kern_r(b, e, tod, c, h, l, clim, spy, atr, gate, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not gate[i0]:
            continue
        for i in range(i0 + 2, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            anyc = False
            for k in range(max(i0, i - 6), i):
                if clim[k]:
                    anyc = True
            if anyc and c[i] > c[i - 1] and c[i] > max(h[i - 1], h[i - 2]) and spy[i] > -1.0:
                lo = l[i]
                for k in range(max(i0, i - 3), i + 1):
                    lo = min(lo, l[k])
                m[i] = True
                stop[i] = lo - 0.02 * atr[i]
    return m, stop


@numba.njit(cache=False)
def _kern_b(b, e, tod, c, h, l, clim, spy, gate, w0, w1, lag):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not gate[i0]:
            continue
        k = -1
        bh = 0.0
        pulled = False
        for i in range(i0, i1):
            if k >= 0 and l[i] < l[k]:
                k = -1
            if k < 0:
                if clim[i]:
                    k = i
                    bh = h[i]
                    pulled = False
                continue
            if not pulled:
                if h[i] < bh:
                    pulled = True
                else:
                    bh = h[i]
                continue
            if c[i] > bh and i - k <= lag and tod[i] >= w0 and tod[i] <= w1 and spy[i] > -1.0:
                m[i] = True
                stop[i] = l[k]
    return m, stop


def compute(df, cfg):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    tod = df["tod"].to_numpy(np.int64)
    fo, vd, vr = f("fromOpen"), f("vwapDistPct"), f("volumeRatio")
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - f("dist_lod_atr") * atr
        vw = c / (1 + vd / 100)
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    dg = key.merge(_daily(), on=["symbol", "date"], how="left")
    pc = dg["pc_d"].to_numpy(float)
    inwin = (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    with np.errstate(invalid="ignore", divide="ignore"):
        if cfg == "R":
            gate = (dg["R_ok2"].to_numpy(float) == 1) & (dg["dec2"].to_numpy(float) <= -1.0 * atr)
            s = pd.Series(c)
            sym = df["symbol"].astype(str).to_numpy()
            g = s.groupby(sym, sort=False)
            mu = g.transform(lambda x: x.rolling(20).mean()).to_numpy()
            sd = g.transform(lambda x: x.rolling(20).std(ddof=0)).to_numpy()
            clim = inwin & (fo <= -1.0) & (vd <= -1.0) & (vr >= 1.5) & (c < mu - 2 * sd)
        else:
            gate = (dg["B_red3"].to_numpy(float) == 1) & (dg["ret5"].to_numpy(float) <= -3 * atr / pc * 100) \
                   & (pc <= dg["sma20"].to_numpy(float) - 2.5 * atr)
            clim = inwin & (fo <= -1.0) & (vd <= -1.5 * atr / c * 100) & (vr >= 3.0) & (l <= lod + 1e-6 * c)
    gate = np.asarray(gate, bool)
    clim = np.asarray(clim, bool)
    b, e = _segments(df)
    spy = f("spy_fo")
    if cfg == "R":
        m, stop = _kern_r(b, e, tod, c, h, l, clim, spy, atr, gate, WINDOW[0], WINDOW[1])
    else:
        m, stop = _kern_b(b, e, tod, c, h, l, clim, spy, gate, WINDOW[0], WINDOW[1], 6)
    tgt = np.where(vw > c, vw, c + 50 * atr)
    return m, stop, tgt


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df, CFG)
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
