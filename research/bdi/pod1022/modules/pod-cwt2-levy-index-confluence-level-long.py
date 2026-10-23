"""pod-cwt2-levy-index-confluence-level-long - Synchronous index level touch: 3 of 4 index ETFs hit support together (LONG).

Source: Chat With Traders ep 310, Dr. Efrat Levy (key-level 'fingerprinting'); record x20251030-310.
URL: https://chatwithtraders.com

VARIANT of obos-levels (holdout_failed: single-symbol overbought/oversold touches at PDH/PDL/round numbers) and
pod-camarilla-l3-quiet-fade (single-ETF pivot fade). Stated change: the signal is CROSS-INSTRUMENT agreement - three
of four index ETFs touch a support of the same type in the same 5-min bar; there is no oscillator.

Rules (plain English). SYMBOLS = SPY, QQQ, IWM, DIA; only SPY and QQQ are traded.
  1. Fixed pre-open supports per ETF (prior completed day only): prior-day low (PDL), prior-day close (PDC, only when
     the 09:50 close is above it) and floor pivot S1 = 2 x P - PDH with P = (PDH + PDL + PDC) / 3.
  2. In bar t at least 3 of the 4 ETFs have low <= support + 0.05 x atr_d and close > support - 0.10 x atr_d for the
     SAME support type (checked in the order PDL, S1, PDC; the first type that qualifies is used).
  3. Any ETF that is not touching is not at an opposing level: its close is not within 0.10 x atr_d of its PDH or
     R1 = 2 x P - PDL.
  4. The traded ETF is one of the touching ETFs, closes above its support, and its lower_wick >= 0.3.
  5. Room: the session VWAP OR the nearest resistance above the close (P, PDC, R1, PDH) is >= 3 x (entry - stop)
     above the entry (the source's 'VWAP or nearest resistance'). Target = the nearer of the two (when above the
     close); with nothing above, the trade holds to 15:55.
  Entry: that close, bar close 10:00-15:00. Stop (GEOM S): support - 0.15 x atr_d. Target as in 5; flat 15:55.
Control the source implies (single-ETF touches of the same level, no cross-ETF agreement) is the companion file
pod-cwt2-levy-index-confluence-level-ctrl-long.py (CROSS = False), scored as an information line, not a candidate.
Pre-declared choices: the support-type priority PDL > S1 > PDC; room reads 'either level >= 3x' (a stricter
'target >= 3x' reading gave 0 trades in a 2025-06 smoke test, a build check, not a score). No tweak used. No tuning on the valid period.
Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1500)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
TRADE = ("SPY", "QQQ")
CROSS = True
CONTEXT = []
LAYERS = ["3 of 4 index ETFs touch the same support type (PDL / S1 / PDC) in one bar",
          "the non-touching ETF is not at its PDH / R1", "traded ETF closes above support, lower_wick >= 0.3",
          "room: target >= 3x stop distance", "stop support - 0.15 ATR, target VWAP / nearest resistance",
          "10:00-15:00 ET"]

import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _dayfirst(x, k):
    st = np.r_[True, k[1:] != k[:-1]]
    return np.asarray(x, float)[st][np.cumsum(st) - 1]


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n:
        return np.zeros(n, dtype=bool)
    k = _key(df)
    sym = df["symbol"].astype(str).to_numpy()
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        opn = _dayfirst(c / (1 + _f(df, "fromOpen") / 100), k)
        pdc = opn / (1 + _dayfirst(_f(df, "gap"), k) / 100)
        pdh = _dayfirst(c + _f(df, "dist_pdh_atr") * atr, k)
        pdl = _dayfirst(c - _f(df, "dist_pdl_atr") * atr, k)
        P = (pdh + pdl + pdc) / 3
        S1, R1 = 2 * P - pdh, 2 * P - pdl
        c950 = _dayfirst(np.where(tod == 950, c, np.nan), k)
        sups = {"PDL": pdl, "S1": S1, "PDC": np.where(c950 > pdc, pdc, np.nan)}
        touch = {t: (l <= s + 0.05 * atr) & (c > s - 0.10 * atr) for t, s in sups.items()}
        oppo = (np.abs(c - pdh) <= 0.10 * atr) | (np.abs(c - R1) <= 0.10 * atr)
        slot = pd.factorize(pd.Series(df["date"].astype(str).to_numpy()) + "|" + pd.Series(tod.astype(str)))[0]
        ns = int(slot.max()) + 1
        cnt = {}
        for t in sups:
            cnt[t] = np.bincount(slot, weights=touch[t].astype(float), minlength=ns)
        noppo_untouched = {}
        for t in sups:
            bad = oppo & ~touch[t]
            noppo_untouched[t] = np.bincount(slot, weights=bad.astype(float), minlength=ns)
        m = np.zeros(n, bool)
        sup = np.full(n, np.nan)
        for t in ("PDL", "S1", "PDC"):
            if CROSS:
                ok = touch[t] & (cnt[t][slot] >= 3) & (noppo_untouched[t][slot] == 0)
            else:
                ok = touch[t]
            ok &= ~m & (c > sups[t])
            sup = np.where(ok, sups[t], sup)
            m |= ok
        m &= np.isin(sym, TRADE)
        m &= _f(df, "lower_wick") >= 0.3
        stop = sup - 0.15 * atr
        vwap = c / (1 + _f(df, "vwapDistPct") / 100)
        res = np.full(n, np.inf)
        for lv in (P, pdc, R1, pdh):
            res = np.where(lv > c + 1e-9, np.minimum(res, lv), res)
        vw = np.where(vwap > c + 1e-9, vwap, np.inf)
        tgt = np.minimum(vw, res)
        has = np.isfinite(tgt)
        far = np.where(np.isfinite(vw), vw, -np.inf)
        far = np.maximum(far, np.where(np.isfinite(res), res, -np.inf))
        m &= ~has | ((far - c) >= 3 * (c - stop))
        tgt = np.where(has, tgt, np.nan)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & np.isfinite(stop) & (stop < c)
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
    return t if np.isfinite(t) else float(f["close"].iloc[i]) * 10.0   # nothing above: hold to 15:55
