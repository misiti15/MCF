"""Setup lab v2: extended features + multiple exit geometries for the layered-setup swarm.

Builds on the heat frame (mcf/research/heat.py) and adds the conditions the owner asked to test:
  levels      distance to prior-day high/low, high/low of day, nearest round number (in daily ATRs)
  averages    5-min SMA20 / SMA50 distance and slope
  volume flip signed-volume over the last 3 bars vs the prior 9 (buyers/sellers taking over),
              volume climax (bar volume vs 20-bar average)
  divergence  price at a 20-bar extreme while RSI is not
Outcomes per bar, long and short, after costs (R = 0.25 x daily ATR; exits by 15:55):
  t1s1   target +1R / stop -1R   (symmetric; success = first touch)
  t05s1  target +0.5R / stop -1R (high win-rate geometry)
  t1s05  target +1R / stop -0.5R (low win-rate, high payoff)
Each geometry gives win (0/1, target first) and r (realised R after costs, timed exit at 15:55).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .heat import COMPONENTS, RAW, heat_frame

GEOMS = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}


def _outcomes_asym(f: pd.DataFrame, r_frac: float, cost_ps: float, up_k: float, dn_k: float, close_by: int = 1555):
    c, h, l = f.close.to_numpy(), f.high.to_numpy(), f.low.to_numpy()
    r = f.atr_d.to_numpy() * r_frac
    tod = f.tod.to_numpy()
    out = {k: np.full(len(f), np.nan) for k in ("win_long", "win_short", "r_long", "r_short")}
    bounds = np.flatnonzero(np.r_[True, np.array(f.index.date[1:]) != np.array(f.index.date[:-1]), True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        cc, hh, ll, rr = c[a:b], h[a:b], l[a:b], r[a:b]
        m = b - a
        later = np.triu(np.ones((m, m), bool), 1) & (tod[a:b] <= close_by)[None, :]
        last = np.where(later.any(1), m - 1 - np.argmax(later[:, ::-1], 1), np.arange(m))
        ok = np.isfinite(rr) & (rr > 0)
        for side, nm in ((1, "long"), (-1, "short")):
            tgt, stp = cc + side * up_k * rr, cc - side * dn_k * rr
            hit_t = ((hh[None, :] >= tgt[:, None]) if side == 1 else (ll[None, :] <= tgt[:, None])) & later
            hit_s = ((ll[None, :] <= stp[:, None]) if side == 1 else (hh[None, :] >= stp[:, None])) & later
            big = m + 1
            ft = np.where(hit_t.any(1), np.argmax(hit_t, 1), big)
            fs = np.where(hit_s.any(1), np.argmax(hit_s, 1), big)
            won = ft < fs
            lost = (fs <= ft) & (fs < big)
            val = np.where(won, up_k, np.where(lost, -dn_k, side * (cc[last] - cc) / np.where(ok, rr, 1)))
            out[f"win_{nm}"][a:b] = np.where(ok, won.astype(float), np.nan)
            out[f"r_{nm}"][a:b] = np.where(ok, val - 2 * cost_ps / np.where(ok, rr, 1), np.nan)
    return out


def extra_features(d5: pd.DataFrame, f: pd.DataFrame) -> pd.DataFrame:
    day = pd.Series(d5.index.date, index=d5.index)
    c, h, l, v, o = d5["close"], d5["high"], d5["low"], d5["volume"], d5["open"]
    atr = f["atr_d"].replace(0, np.nan)
    daily = d5.groupby(d5.index.date).agg(high=("high", "max"), low=("low", "min"))
    pdh, pdl = day.map(daily["high"].shift(1)), day.map(daily["low"].shift(1))
    hod, lod = h.groupby(day).cummax(), l.groupby(day).cummin()
    x = pd.DataFrame(index=d5.index)
    x["dist_pdh_atr"] = (pdh - c) / atr                       # >0 below prior-day high
    x["dist_pdl_atr"] = (c - pdl) / atr                       # >0 above prior-day low
    x["dist_hod_atr"] = (hod - c) / atr
    x["dist_lod_atr"] = (c - lod) / atr
    step = np.where(c >= 100, 5.0, np.where(c >= 20, 1.0, 0.5))
    x["dist_round_atr"] = (np.abs(c - np.round(c / step) * step)) / atr
    sma20, sma50 = c.rolling(20).mean(), c.rolling(50).mean()
    x["sma20_dist_pct"] = (c / sma20 - 1) * 100
    x["sma50_dist_pct"] = (c / sma50 - 1) * 100
    x["sma20_slope_pct"] = (sma20 / sma20.shift(5) - 1) * 100
    sv = np.sign(c - o) * v
    x["flow3"] = (sv.rolling(3).sum() / v.rolling(3).sum().replace(0, np.nan)).clip(-1, 1)
    x["flow9prev"] = (sv.shift(3).rolling(9).sum() / v.shift(3).rolling(9).sum().replace(0, np.nan)).clip(-1, 1)
    x["vol_climax"] = v / v.rolling(20).mean().replace(0, np.nan)
    hi20, lo20 = h.rolling(20).max(), l.rolling(20).min()
    rsi = f["rsi"]
    x["bear_div"] = ((h >= hi20) & (rsi < rsi.rolling(20).max() - 5)).astype(int)
    x["bull_div"] = ((l <= lo20) & (rsi > rsi.rolling(20).min() + 5)).astype(int)
    x["upper_wick"] = (h - np.maximum(o, c)) / (h - l).replace(0, np.nan)
    x["lower_wick"] = (np.minimum(o, c) - l) / (h - l).replace(0, np.nan)
    return x


def build(bars: dict[str, pd.DataFrame], cost_ps: float = 0.01, r_frac: float = 0.25, log=print) -> pd.DataFrame:
    frames = []
    for n, (sym, d5) in enumerate(bars.items()):
        if len(d5) < 300:
            continue
        f = heat_frame(d5)
        f = f.join(extra_features(d5, f))
        for g, (up, dn) in GEOMS.items():
            o = _outcomes_asym(f, r_frac, cost_ps, up, dn)
            for k, arr in o.items():
                f[f"{k}_{g}"] = arr
        f["symbol"] = sym
        f = f[(f.tod >= 950) & (f.tod <= 1500) & f.atr_d.notna() & f.rsi.notna()]
        num = f.select_dtypes("number").columns
        frames.append(f.astype({k: "float32" for k in num if k != "tod"}))
        if n % 200 == 0:
            log(f"setup_lab: {n}/{len(bars)}")
    x = pd.concat(frames)
    x["date"] = x.index.date
    return x
