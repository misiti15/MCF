"""pod-smb-first-green-day-multiday-loser-long - First green day after a multi-day selloff: red-to-green through the
prior close on a 3+ day loser (LONG).

Source: SMB Capital YouTube / SMB Podcast discussions of 'first green day' bounces on beaten-down in-play names
(mirror of the first-red-day short). Taken from SMB material already known; web was unavailable this round.
URL: https://www.youtube.com/@smbcapital

VARIANT of wi-red-to-green / Reddit R06 red-to-green, and the opposite-side mirror of CWT02 first-red-day short. What
changes: it fires only on multi-day losers (a daily-context gate) and only after 10:00.

Rules (plain English). Daily values come only from completed days (research/history2y daily table, days before D;
a look-back that spans a calendar gap > 10 days - the locked block - is dropped):
  1. >= 3 consecutive lower daily closes (close d-1 < d-2 < d-3 < d-4) and the 5-day return (close d-1 minus close
     d-6) <= -2.5 x atr_d.
  2. Today opens at or below the prior close (gap <= 0).
  3. The first 5-minute close of the day above the prior close ('goes green'; checked over frame bars from 09:50 -
     the 09:30-09:45 closes are not in the frame) with volumeRatio >= 1.5.
  4. That close is above session VWAP.
  Entry: that bar's close (the frame has no bar open; the source says next bar open), bar close 10:00-14:30; if the
  first green close comes before 10:00 the day does not qualify. Once per symbol-day.
  Stop (GEOM S): max(session LOD, VWAP - 0.25 x atr_d). Target: PDH or entry + 1.5R, whichever is nearer above the
  entry. Flat 15:55. Costs in (scorer).
No tweak made. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
LAYERS = ["daily: 3 lower closes, 5d return <= -2.5 ATR", "gap <= 0", "first close above prior close, volumeRatio >= 1.5",
          "close > VWAP", "stop max(LOD, VWAP - 0.25 ATR), target nearer of PDH / 1.5R", "10:00-14:30"]

_ROOT = Path(__file__).resolve().parents[4]
_ST = {}
_CACHE = {}


def _daily():
    if "d" in _CACHE:
        return _CACHE["d"]
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    d = lib.daily()[["symbol", "date", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    gs = d.groupby("symbol", sort=False)
    c = d["close"]
    c1, c2, c3, c5 = (gs["close"].shift(k) for k in (1, 2, 3, 5))
    dt = pd.to_datetime(d["date"])
    span = (dt - dt.groupby(d["symbol"]).shift(5)).dt.days
    d["down3"] = ((c < c1) & (c1 < c2) & (c2 < c3)).astype(float)
    d["ret5d"] = c - c5
    d.loc[~(span <= 10), ["down3", "ret5d"]] = np.nan
    d["next_date"] = gs["date"].shift(-1)
    d = d[(pd.to_datetime(d["next_date"]) - dt).dt.days <= 5]
    out = d[["symbol", "next_date", "down3", "ret5d"]].rename(columns={"next_date": "date"})
    out["date"] = out["date"].astype(str)
    _CACHE["d"] = out
    return out


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return k, np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return k, b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kern(b, e, gate, tod, c, pc, gap, lod, pdh, vw, vr, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not gate[i0] or not (gap[i0] <= 0):
            continue
        for i in range(i0, i1):
            if not (c[i] > pc[i]):
                continue
            # first green close of the day (from 09:50)
            a = atr[i]
            if tod[i] >= w0 and tod[i] <= w1 and a > 0 and vr[i] >= 1.5 and c[i] > vw[i]:
                sp = max(lod[i], vw[i] - 0.25 * a)
                r = c[i] - sp
                if r > 0:
                    tp = c[i] + 1.5 * r
                    if pdh[i] > c[i] and pdh[i] < tp:
                        tp = pdh[i]
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = tp
            break
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, dtype=bool)
    if n == 0:
        return z
    try:
        dd = _daily()
    except Exception:
        return z
    k, b, e = _segments(df)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[b], "date": df["date"].astype(str).to_numpy()[b]})
    u = u.merge(dd, on=["symbol", "date"], how="left")
    f = lambda x: df[x].to_numpy(float)
    c = f("close")
    atr = f("atr_d")
    with np.errstate(invalid="ignore"):
        gate_seg = (u["down3"].to_numpy(float) == 1) & (u["ret5d"].to_numpy(float) <= -2.5 * atr[b])
    gate = np.zeros(n, np.bool_)
    gate[b] = gate_seg
    vw = c / (1 + f("vwapDistPct") / 100)
    opn = c / (1 + f("fromOpen") / 100)
    gap = f("gap")
    pc = opn / (1 + gap / 100)
    lod = c - f("dist_lod_atr") * atr
    pdh = c + f("dist_pdh_atr") * atr
    m, stop, tgt = _kern(b, e, gate, df["tod"].to_numpy(np.int64), c, pc, gap, lod, pdh, vw, f("volumeRatio"), atr,
                         WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


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
