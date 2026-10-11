"""MarcoFlow heat score, three variants, for the T3 heat study (research/bdi/turns1009/heat/HEAT.md).
Educational only - not financial advice.

  V0 "port"    mcf.research.heat.heat_frame: MarcoFlow's formula on COMPLETED 5-min bars, true volume, no candlestick
               component (this is the `heat` column of the two-year lab frames).
  V1 "formula" MarcoFlow's formula as written in lib/heat-tracker.ts + lib/candlestick-patterns.ts on completed bars:
               V0 + candlestickHeat (+-15) + the two candlestick/trend alignment terms (+-3).
  V2 "as-run"  what MarcoFlow actually computed when it scanned: Yahoo's 5m series ends with the in-progress bar,
               whose volume is reported as 0 (volumeRatio = 0 in 108,864 of 108,967 live rows). Modelled as a stub bar
               appended after completed bar t with O=H=L=C=close_t and volume 0. Consequences: volumeHeat is -10 unless
               volumeSurge > 2 (then +20); RSI uses 13 real changes + a zero change; momentum uses c_t/c_{t-3} and
               c_t/c_{t-8}; EMAs/MACD take one extra update at c_t; price position uses the last 19 completed bars;
               candlestick patterns can only sit on the last 4 completed bars, avgBody includes the stub's zero body.
               (The ~15-min Yahoo delay is a separate latency, handled by the caller.)
All functions take one symbol's continuous RTH 5-minute bars (DatetimeIndex = bar start, ET; columns open/high/low/close/
volume) spanning many sessions, and are causal.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from mcf.research.heat import COMPONENTS, heat_frame  # noqa: E402

CANDLE = {  # name: (sign, strength)
    "hammer": (1, 2), "inv_hammer": (1, 1), "hanging_man": (-1, 2), "shooting_star": (-1, 2),
    "bull_engulf": (1, 3), "bear_engulf": (-1, 3), "morning_star": (1, 3), "evening_star": (-1, 3),
    "bull_marubozu": (1, 2), "bear_marubozu": (-1, 2), "three_white": (1, 3), "three_black": (-1, 3),
}


def _rmax(x: np.ndarray, w: int) -> np.ndarray:
    return pd.Series(x).rolling(w, min_periods=1).max().to_numpy()


def candle_heat(d5: pd.DataFrame, as_run: bool = False) -> pd.DataFrame:
    """candlestickHeat per bar: patterns on the last 5 completed bars (as_run: last 4), avgBody over the last 20 bars
    (as_run: 19 completed + the stub's zero body), deduped by name, strength*5*sign summed, clamped to +-15."""
    o, h, l, c = (d5[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    body, rng = np.abs(c - o), h - l
    up, lw = h - np.maximum(o, c), np.minimum(o, c) - l
    bull, bear = c > o, c < o
    doji = np.where(rng == 0, True, body / np.where(rng == 0, 1, rng) < 0.1)
    hammer = (rng > 0) & (body > 0) & (lw >= 2 * body) & (up < 0.5 * body)
    inv = (rng > 0) & (body > 0) & (up >= 2 * body) & (lw < 0.5 * body)
    maru = (rng > 0) & (body / np.where(rng == 0, 1, rng) > 0.9)
    sh = lambda x, k: np.r_[np.full(k, np.nan if x.dtype.kind == "f" else False), x[:-k]]
    pb, pb2 = sh(bull, 1), sh(bull, 2)
    pr, pr2 = sh(bear, 1), sh(bear, 2)
    po, pc = sh(o, 1), sh(c, 1)
    po2, pc2 = sh(o, 2), sh(c, 2)
    pbody, pdoji = sh(body, 1), sh(doji, 1)
    base = {
        "hammer": hammer & pr & pr2, "inv_hammer": inv & pr & pr2,
        "hanging_man": hammer & pb & pb2, "shooting_star": inv & pb & pb2,
        "bull_engulf": pr & bull & (o <= pc) & (c >= po) & (body > pbody * 1.2),
        "bear_engulf": pb & bear & (o >= pc) & (c <= po) & (body > pbody * 1.2),
        "morning_star": pr2 & pdoji & bull & (c > (po2 + pc2) / 2),
        "evening_star": pb2 & pdoji & bear & (c < (po2 + pc2) / 2),
    }
    win = 4 if as_run else 5
    avg_body = pd.Series(body).rolling(19 if as_run else 20, min_periods=1).sum().to_numpy() / 20
    tot = np.zeros(len(c))
    for k, m in base.items():
        s, st = CANDLE[k]
        tot += s * st * 5 * (_rmax(np.nan_to_num(m.astype(float)), win) > 0)
    # avgBody-dependent patterns: any j in window with base_j and metric_j > k*avgBody_t
    neg = -np.inf
    mb = np.where(maru & bull, body, neg)
    mr = np.where(maru & bear, body, neg)
    tot += 2 * 5 * (_rmax(mb, win) > 1.5 * avg_body)
    tot -= 2 * 5 * (_rmax(mr, win) > 1.5 * avg_body)
    # three soldiers / crows: bull_{j-2..j}, rising closes, body_{j-1}, body_j > 0.7 avgBody_t
    tw = pb2 & pb & bull & (pc > pc2) & (c > pc)
    tb = pr2 & pr & bear & (pc < pc2) & (c < pc)
    mbody = np.minimum(body, np.nan_to_num(pbody, nan=0))
    tot += 3 * 5 * (_rmax(np.where(tw, mbody, neg), win) > 0.7 * avg_body)
    tot -= 3 * 5 * (_rmax(np.where(tb, mbody, neg), win) > 0.7 * avg_body)
    return pd.DataFrame({"candlestickHeat": np.clip(tot, -15, 15)}, index=d5.index)


def _bonus(vh, mh, rh, ph, th, ch):
    return (np.where((vh > 5) & (mh > 5), 5, 0) + np.where((rh > 10) & (ph > 5), 5, 0)
            + np.where((vh < -5) & (mh < -5), -5, 0) + np.where((rh < -10) & (ph < -5), -5, 0)
            + np.where((ch > 5) & (th > 3), 3, 0) + np.where((ch < -5) & (th < -3), -3, 0))


def _scores(vr, vs, r, mom, pp, ediff, macdp, vwd):
    vr, vs = np.nan_to_num(vr, nan=1.0), np.nan_to_num(vs, nan=1.0)
    r = np.nan_to_num(r, nan=50.0)
    vh = np.select([vs > 2, vr > 1.5, vr < 0.5], [20, np.minimum(20, (vr - 1) * 20), -10], (vr - 1) * 15)
    rh = np.select([r >= 80, r >= 70, r <= 20, r <= 30, r < 45, r > 55],
                   [-25, -((r - 70) / 10) * 20, 25, ((30 - r) / 10) * 20, (45 - r) / 15 * 10, (55 - r) / 15 * 10], 0)
    mh = np.clip(np.nan_to_num(mom) * 8, -20, 20)
    ph = np.select([pp <= 0.2, pp >= 0.8], [15, -15], (0.5 - pp) * 20)
    th = np.clip(np.nan_to_num(ediff) * 5, -15, 15)
    xh = np.clip(np.nan_to_num(macdp) * 20, -10, 10)
    wh = np.clip(np.nan_to_num(vwd) * 12, -12, 12)
    return vh, rh, mh, ph, th, xh, wh


def all_heats(d5: pd.DataFrame) -> pd.DataFrame:
    """V0, V1, V2 heat plus V2's components (suffix _ar) for one symbol's 5-minute bars."""
    f = heat_frame(d5)
    c, h, l, v = (d5[k].astype(float) for k in ("close", "high", "low", "volume"))
    out = pd.DataFrame(index=d5.index)
    out["heat_v0"] = f["heat"]
    for k in COMPONENTS:
        out[k] = f[k]
    ch1 = candle_heat(d5)["candlestickHeat"].to_numpy()
    out["candleHeat"] = ch1
    b1 = _bonus(f.volumeHeat, f.momentumHeat, f.rsiHeat, f.priceActionHeat, f.trendHeat, ch1)
    out["heat_v1"] = np.clip(f[COMPONENTS].sum(axis=1).to_numpy() + ch1 + b1, -100, 100)
    # ---- V2 as-run (stub bar after t) ----
    d = c.diff()
    g = d.clip(lower=0).rolling(13).sum()
    lo = (-d.clip(upper=0)).rolling(13).sum()
    rsi = np.where(lo == 0, 100.0, 100 - 100 / (1 + g / lo.replace(0, np.nan)))
    m5 = (c / c.shift(3) - 1) * 100
    m10 = (c / c.shift(8) - 1) * 100
    mom = (m5 * 0.6 + m10 * 0.4).to_numpy()
    ema = lambda n: c.ewm(span=n, adjust=False).mean()
    e1 = lambda n: (ema(n) + 2 / (n + 1) * (c - ema(n)))
    e9, e21 = e1(9), e1(21)
    ediff = ((e9 - e21) / e21 * 100).to_numpy()
    macdp = ((e1(12) - e1(26)) / c * 100).to_numpy()
    vs = ((v.rolling(4).sum() / 5) / v.shift(4).rolling(15).mean().replace(0, np.nan)).to_numpy()
    vr = np.zeros(len(c))
    hi, lw = h.rolling(19).max(), l.rolling(19).min()
    pp = ((c - lw) / (hi - lw).replace(0, np.nan)).fillna(0.5).to_numpy()
    vh, rh, mh, ph, th, xh, wh = _scores(vr, vs, rsi, mom, pp, ediff, macdp, f["vwapDistPct"].to_numpy())
    ch2 = candle_heat(d5, as_run=True)["candlestickHeat"].to_numpy()
    for k, x in zip(COMPONENTS + ["candleHeat"], (vh, rh, mh, ph, th, xh, wh, ch2)):
        out[k + "_ar"] = x
    out["rsi_ar"] = rsi
    out["heat_v2"] = np.clip(vh + rh + mh + ph + th + xh + wh + ch2 + _bonus(vh, mh, rh, ph, th, ch2), -100, 100)
    out["vwapDistPct"] = f["vwapDistPct"]
    out["rsi"] = f["rsi"]
    out["tod"] = f["tod"]
    return out
