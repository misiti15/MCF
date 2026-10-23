"""pod-cwt2-barrett-pdh-break-otf-confirm-long - Filtered PDH breakout in a volatile regime, entered after one-time-framing confirmation (LONG).

Source: Chat With Traders ep 208, Brannigan Barrett; record ep208 'Filtered breakout in a volatile market'.
URL: https://chatwithtraders.com

VARIANT of cwt-a-a3-pdh-breakout-day2 (failed: stop entry at the PDH, stop at the prior close). Stated change:
(a) a volatility-regime gate and (b) no entry on the break itself; entry only after the source's two 'objective
facts': two one-time-framing bars that hold above the level + 0.25 x the 5-min ATR.

Rules (plain English):
  1. Regime: the symbol's daily ATR(14) / close as of the prior close is above its own median of the previous 60
     sessions, and SPY's daily ATR% is above its own 60-session median (daily bars, completed days only).
  2. Break: bar b is the first 5-min close above the prior-day high today, and the high of day before bar b is still
     <= PDH (the PDH was not exceeded earlier, including 09:30-09:45).
  3. Confirmation: bars b+1 and b+2 each make a higher low than the bar before, and both close above
     PDH + 0.25 x the 5-min ATR (atrPct% x close).
  4. breadth >= 0.5 at the entry bar.
  Entry: the close of b+2, bar close 10:00-14:30. Stop (GEOM S): the low of bar b - 0.05 x atr_d. Target: 2R; flat
  15:55. Information line: the module prints, per month, the count of regime-qualified breaks and how many failed
  confirmation (stderr, '[barrett]').
Pre-declared choices: daily ATR(14) = 14-session mean true range from the daily bars; the 60-session median needs
>= 20 prior sessions (the history starts 2024-10 and the locked block is not loaded, so early-2025 medians use fewer
sessions). No tweak used. No tuning on the valid period. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = ["breadth"]
LAYERS = ["symbol ATR% and SPY ATR% above their 60-session medians", "first 5-min close above PDH (not exceeded before)",
          "two higher-low bars closing > PDH + 0.25 x 5m ATR", "breadth >= 0.5",
          "stop break-bar low - 0.05 ATR, target 2R", "10:00-14:30 ET"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[4]
_ST = {}
_CACHE = {}


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


def _regime():
    if "r" in _CACHE:
        return _CACHE["r"]
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    d = lib.daily()[["symbol", "date", "high", "low", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)
    pc = g["close"].shift(1)
    tr = np.maximum(d["high"] - d["low"], np.maximum((d["high"] - pc).abs(), (d["low"] - pc).abs()))
    d["atrp"] = tr.groupby(d["symbol"]).transform(lambda x: x.rolling(14, min_periods=14).mean()) / d["close"]
    med = d.groupby("symbol", sort=False)["atrp"].transform(lambda x: x.shift(1).rolling(60, min_periods=20).median())
    d["hi"] = (d["atrp"] > med).astype(float).where(med.notna())
    d["next_date"] = g["date"].shift(-1)                    # the flag as of day d applies to the next session
    out = d.dropna(subset=["next_date"])[["symbol", "next_date", "hi"]].rename(columns={"next_date": "date"})
    out["date"] = out["date"].astype(str)
    spy = out[out["symbol"] == "SPY"][["date", "hi"]].rename(columns={"hi": "spy_hi"})
    out = out.merge(spy, on="date", how="left")
    out["ok"] = ((out["hi"] == 1) & (out["spy_hi"] == 1)).astype(bool)
    r = dict(zip(out["symbol"] + "|" + out["date"], out["ok"]))
    _CACHE["r"] = r
    return r


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n or "breadth" not in df:
        return np.zeros(n, dtype=bool)
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    reg = _regime()
    keys = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    ukeys, inv = np.unique(keys.to_numpy(), return_inverse=True)
    rok = np.array([bool(reg.get(x, False)) for x in ukeys])[inv]
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        pdh = c + _f(df, "dist_pdh_atr") * atr
        above = c > pdh
        cs = np.cumsum(above)
        st = np.r_[True, k[1:] != k[:-1]]
        base = (cs - above)[st][np.cumsum(st) - 1]
        first = above & ((cs - above - base) == 0)
        brk = first & (_lag(hod, k) <= pdh)               # bar b (hod before b <= PDH)
        lvl = pdh + 0.25 * _f(df, "atrPct") / 100 * c
        b2 = _lag(brk.astype(float), k, 2) == 1           # this bar is b+2
        conf = b2 & (l > _lag(l, k, 1)) & (_lag(l, k, 1) > _lag(l, k, 2)) & (c > lvl) & (_lag(c, k, 1) > _lag(lvl, k, 1))
        win = (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        m = conf & rok & win & (_f(df, "breadth") >= 0.5)
        stop = _lag(l, k, 2) - 0.05 * atr
        tgt = c + 2 * (c - stop)
        m &= np.isfinite(stop) & (stop < c)
        nb = int((b2 & rok & win).sum())
        nc = int((conf & rok & win).sum())
    if len(df) > 2000:
        print(f"[barrett] {str(df['date'].iloc[0])[:7]} breaks(regime, b+2 in window) {nb} confirmed {nc} "
              f"failed {nb - nc}", file=sys.stderr, flush=True)
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
    return _get(f, i, 1)
