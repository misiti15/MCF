"""pod-em-vix-implied-lower-band-reclaim-long - Options expected-move band: reclaim of the VIX-implied -1 sigma daily
move (LONG SPY / QQQ).

Source: TradingView open-source 'SPX Expected Move' (VIX-scaled 1 / 2 SD bands); Databento docs, 'SPX and the VIX'
(VIX1D / VIX9D implied daily range).
URL: https://www.tradingview.com/script/kvk4QGap-SPX-Expected-Move

NEW (feature family = the options-implied daily range; no prior setup uses it).
EM = prior close x (prior-day VIX close / 100) / sqrt(252). VIX daily closes come from
research/swarm1010/w5_sources/data/vix_daily.parquet (CBOE VIX via the GitHub mirror, the rule-19 locked block
removed; dates in 2024-11-01..2025-02-28 are dropped again here). The VIX close used for day D is the last close
BEFORE D (completed day). VXN is not in the history, so QQQ uses VIX x 1.2 (as the idea says). The VIX file ends
2026-09-22, so later days have no EM and no trades (declared data limit).
Rules (plain English, LONG). SYMBOLS: SPY, QQQ.
  1. The ETF's daily close yesterday > its daily SMA50 (lib.daily()), and the prior VIX close < 25.
  2. Band L = prior close - 1.0 x EM. Some bar closing 10:00-14:30 ET (before the decision bar) traded below L
     (low < L).
  3. The decision bar closes back above L after the previous bar closed at or below L (band reclaim), and its volume
     is >= its 20-bar average (volumeRatio >= 1.0). Decision bar close 10:05-15:00 (the scorer's last entry bar).
  Entry: that bar's close. Stop (GEOM S): session low - 0.1 x EM. Target: the session VWAP (target 1); when VWAP is
  not above the entry, target 2 = prior close - 0.5 x EM. The scorer takes one target, so the runner (target 2 after
  target 1) is not modelled (declared). Flat 15:55. One trade per symbol-day (scorer).
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1005, 1500)
SYMBOLS = ["SPY", "QQQ"]
LAYERS = ["D-1 close > SMA50, prior VIX < 25", "a bar 10:00-14:30 traded below prior close - EM",
          "close back above the band (prev close <= band), volumeRatio >= 1",
          "stop LOD - 0.1 EM, target VWAP (else prior close - 0.5 EM)"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt3_bars as CB  # noqa: E402

_VIX = Path(__file__).resolve().parents[4] / "research" / "swarm1010" / "w5_sources" / "data" / "vix_daily.parquet"
_ST = {}
_C = {}


def _stash(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash(f, i, 0)


def target_price(f, i, stop):
    return _stash(f, i, 1)


def _vix_prev(dates):
    """For each trading date string, the VIX close of the last date strictly before it."""
    if "v" not in _C:
        v = pd.read_parquet(_VIX, columns=["date", "close"])
        v["date"] = pd.to_datetime(v["date"])
        v = v[(v["date"] < "2024-11-01") | (v["date"] > "2025-02-28")]      # never use the locked block
        _C["v"] = v.sort_values("date").reset_index(drop=True)
    v = _C["v"]
    q = pd.DataFrame({"date": pd.to_datetime(pd.Series(dates))})
    q["i"] = np.arange(len(q))
    q = q.sort_values("date")
    m = pd.merge_asof(q, v, on="date", allow_exact_matches=False, direction="backward")
    # a stale value (> 7 calendar days old, e.g. across the locked gap or after the file ends) is dropped
    last = pd.merge_asof(q, v.assign(vd=v["date"]), on="date", allow_exact_matches=False)["vd"]
    m["close"] = np.where((q["date"].to_numpy() - last.to_numpy()) <= np.timedelta64(7, "D"), m["close"], np.nan)
    return m.sort_values("i")["close"].to_numpy(float)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n:
        return z
    b = CB.base(df)
    k = CB.key(df)
    st = CB.start(k)
    tod, c, l = b["tod"], b["c"], b["l"]
    d = CB.map_daily(df, k, ["d_close_1", "sma50_1"])
    vix = _vix_prev(df["date"].astype(str).to_numpy()[st])[np.cumsum(st) - 1]
    sym = df["symbol"].astype(str).to_numpy()
    vixe = np.where(sym == "QQQ", vix * 1.2, vix)
    pc = b["pc"]
    seg = np.cumsum(st) - 1
    with np.errstate(invalid="ignore"):
        em = pc * vixe / 100 / np.sqrt(252)
        band = pc - em
        m = (d["d_close_1"] > d["sma50_1"]) & (vix < 25)                               # (1)
        below = ((tod >= 1000) & (tod <= 1430) & (l < band)).astype(float)
        seen = CB.lag(pd.Series(below).groupby(seg).cummax().to_numpy(float), k, 1)  # (2) before this bar
        m &= seen == 1
        m &= (c > band) & (CB.lag(c, k, 1) <= band)                                  # (3)
        m &= CB.f(df, "volumeRatio") >= 1.0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop[:] = b["lod"] - 0.1 * em
        vw = b["vwap"]
        tgt[:] = np.where(vw > c, vw, pc - 0.5 * em)
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
