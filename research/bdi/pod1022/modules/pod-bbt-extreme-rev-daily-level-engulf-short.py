"""pod-bbt-extreme-rev-daily-level-engulf-short - Extreme extension into a daily level, 5-min bearish engulfing (SHORT).

Source: Bear Bull Traders - Andrew Aziz 'Reversals' webinar (June 2023): extreme reversals at a daily moving average,
5-minute bearish engulfing trigger, >= 2:1 reward/risk.
URL: https://bearbulltraders.com/wp-content/uploads/2023/06/Reversal-Andrew-June-22-2023.pdf

VARIANT of CWT14-failbrk-pdh shorts (Testing), RW8 SMA50 spike fade and obos-levels (holdout_failed). Stated changes:
the level set adds the daily SMA50/200, the trigger is a bearish engulfing (not a close back below the level), and an
ATR extension from VWAP is required.

Daily SMA50 / SMA200: means of the last 50 / 200 COMPLETED daily closes from research/history2y daily table (open
part only), mapped to the next trading date; a window whose calendar span shows it straddles the gap left by the
locked block (> 90 / > 320 days) is dropped, so those levels exist only once enough open days have accumulated
(SMA50 from about mid 2025-05, SMA200 from about 2025-12). PDH from the frame (dist_pdh_atr).
Engulfing: the frame has no open, so open_k is approximated by close_{k-1} (as the spec says).

Rules (plain English), decision bar i:
  1. high_i or high_{i-1} within 0.1 x daily ATR of the daily SMA50, the daily SMA200 or the prior-day high.
  2. close_{i-1} - VWAP_{i-1} >= 1.0 x daily ATR and fromOpen_{i-1} >= +2%.
  3. Engulfing: bar i-1 up (close_{i-1} > close_{i-2}), bar i down, close_i < open_{i-1} (= close_{i-2}), body_i >
     body_{i-1}; volumeRatio_i >= volumeRatio_{i-1}.
  4. RSI(14)_{i-1} >= 70.
  Entry: close_i, bar close 10:30-14:30. Stop (GEOM S): max(high_{i-1}, high_i) + 0.03 x daily ATR. Target: session
  VWAP at entry; trade only if (entry - VWAP) >= 2 x (stop - entry). Flat 15:55. Costs in (scorer). No tweak used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = []
LAYERS = ["high_i or high_{i-1} within 0.1 ATR of daily SMA50 / SMA200 / PDH",
          "close_{i-1} >= VWAP + 1.0 ATR, fromOpen >= 2%",
          "bearish engulfing (open ~ prior close), volumeRatio_i >= volumeRatio_{i-1}", "RSI14_{i-1} >= 70",
          "stop max high + 0.03 ATR, target VWAP, reward/risk >= 2", "10:30-14:30 ET"]

_ROOT = Path(__file__).resolve().parents[4]
_STASH = {}
_CACHE = {}


def _lib():
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    return lib


def _daily_sma():
    """Per (symbol, next trading date): SMA50 / SMA200 of completed daily closes (open table only)."""
    if "d" in _CACHE:
        return _CACHE["d"]
    d = _lib().daily()[["symbol", "date", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)["close"]
    d["sma50"] = g.transform(lambda x: x.rolling(50).mean())
    d["sma200"] = g.transform(lambda x: x.rolling(200).mean())
    dt = pd.to_datetime(d["date"])
    gd = dt.groupby(d["symbol"])
    d.loc[~((dt - gd.shift(49)).dt.days <= 90), "sma50"] = np.nan
    d.loc[~((dt - gd.shift(199)).dt.days <= 320), "sma200"] = np.nan
    d["next_date"] = d.groupby("symbol")["date"].shift(-1)
    d = d[(pd.to_datetime(d["next_date"]) - dt).dt.days <= 5]
    out = d[["symbol", "next_date", "sma50", "sma200"]].rename(columns={"next_date": "date"})
    _CACHE["d"] = out
    return out


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, vw, vr, fo, rsi, pdh, s50, s200, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 2, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0):
                continue
            # 3. engulfing (open_k ~ close_{k-1})
            if not (c[i - 1] > c[i - 2] and c[i] < c[i - 1] and c[i] < c[i - 2]):
                continue
            if not ((c[i - 1] - c[i]) > (c[i - 1] - c[i - 2]) and vr[i] >= vr[i - 1]):
                continue
            # 2. extension, 4. RSI
            if not (c[i - 1] - vw[i - 1] >= a and fo[i - 1] >= 2.0 and rsi[i - 1] >= 70):
                continue
            # 1. level touch
            near = False
            for lv in (s50[i], s200[i], pdh[i]):
                if lv == lv:
                    if abs(h[i] - lv) <= 0.1 * a or abs(h[i - 1] - lv) <= 0.1 * a:
                        near = True
            if not near:
                continue
            sp = max(h[i - 1], h[i]) + 0.03 * a
            t = vw[i]
            if not (t < c[i] and sp > c[i] and (c[i] - t) >= 2.0 * (sp - c[i])):
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = t
    return m, stop, tgt


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + f("vwapDistPct") / 100)
        pdh = c + f("dist_pdh_atr") * atr
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    try:
        dg = key.merge(_daily_sma(), on=["symbol", "date"], how="left")
        s50, s200 = dg["sma50"].to_numpy(float), dg["sma200"].to_numpy(float)
    except Exception:  # noqa: BLE001 - no daily table (live) -> PDH only
        s50 = s200 = np.full(n, np.nan)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), vw, f("volumeRatio"), f("fromOpen"), f("rsi"),
                   pdh, s50, s200, atr, WINDOW[0], WINDOW[1])


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
