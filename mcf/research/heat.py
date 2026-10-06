"""MarcoFlow's Heat Score, ported faithfully, plus a lab for re-weighting it on MCF's own data.

Source: MarcoFlow `lib/heat-tracker.ts` (research/heat/marcoflow_heat_tracker.ts.md). Differences:
  * computed on SIP 5-minute bars (MarcoFlow used ~15-min-delayed Yahoo 5-minute bars)
  * the candlestick component (separate MarcoFlow module, not in the export) is omitted -> 0
  * EMAs use pandas' recursive EMA (MarcoFlow seeds with an SMA; identical after warm-up)

Every row is one 5-minute bar close (09:50-15:00 ET, owner's caution window excluded), with the 8
component scores, the original heat, the raw indicators behind them, and outcomes for a long and
a short entered at that close: success (+1R before -1R) and R after costs, R = 0.25 x daily ATR.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from ..discovery import _outcomes

COMPONENTS = ["volumeHeat", "rsiHeat", "momentumHeat", "priceActionHeat", "trendHeat", "macdHeat", "vwapHeat"]
RAW = ["rsi", "rsi5", "momentum", "volumeRatio", "volumeSurge", "pricePosition", "emaDiff", "macdPct",
       "vwapDistPct", "buyPressure", "rsiSlope", "atrPct", "vwapReclaim", "gap", "fromOpen"]
DATA_DIR = Path(os.environ.get("MCF_HEAT_DATA", "research/heat/data"))


def _rsi_simple(c: pd.Series, n: int) -> pd.Series:
    """MarcoFlow's RSI: plain average gain/loss over the last n changes (not Wilder)."""
    d = c.diff()
    g = d.clip(lower=0).rolling(n).sum() / n
    l = (-d.clip(upper=0)).rolling(n).sum() / n
    rsi = 100 - 100 / (1 + g / l.replace(0, np.nan))
    return rsi.where(l != 0, 100.0)


def heat_frame(d5: pd.DataFrame) -> pd.DataFrame:
    """All heat inputs for one symbol's continuous RTH 5-minute bars (many sessions). Causal."""
    c, h, l, v, o = d5["close"], d5["high"], d5["low"], d5["volume"], d5["open"]
    day = pd.Series(d5.index.date, index=d5.index)
    f = pd.DataFrame(index=d5.index)
    f["close"], f["high"], f["low"] = c, h, l
    f["rsi"] = _rsi_simple(c, 14)
    f["rsi5"] = _rsi_simple(c, 5)
    m5 = (c / c.shift(4) - 1) * 100          # prices[len-5]
    m10 = (c / c.shift(9) - 1) * 100
    f["momentum"] = m5 * 0.6 + m10 * 0.4
    ema = lambda n: c.ewm(span=n, adjust=False).mean()
    e9, e21 = ema(9), ema(21)
    f["emaDiff"] = (e9 - e21) / e21 * 100
    f["macdPct"] = (ema(12) - ema(26)) / c * 100
    avgv = v.rolling(20).mean()
    f["volumeRatio"] = v / avgv.replace(0, np.nan)
    f["volumeSurge"] = v.rolling(5).mean() / v.shift(5).rolling(15).mean().replace(0, np.nan)
    hi20, lo20 = h.rolling(20).max(), l.rolling(20).min()
    f["pricePosition"] = ((c - lo20) / (hi20 - lo20).replace(0, np.nan)).fillna(0.5)
    typ = (h + l + c) / 3
    vw = (typ * v).groupby(day).cumsum() / v.groupby(day).cumsum().replace(0, np.nan)
    f["vwapDistPct"] = (c - vw) / vw * 100
    sgn = np.sign(c - o)
    f["buyPressure"] = ((sgn * v).rolling(19).sum() / v.rolling(19).sum().replace(0, np.nan)).clip(-1, 1)
    f["rsiSlope"] = f["rsi"] - f["rsi"].shift(3)
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    f["atrPct"] = tr.rolling(14).mean() / c * 100
    past = f["vwapDistPct"].shift(3)
    f["vwapReclaim"] = np.where((f.vwapDistPct > 0) & (past <= 0), 1, np.where((f.vwapDistPct < 0) & (past >= 0), -1, 0))
    day_open = o.groupby(day).transform("first")
    daily = d5.groupby(d5.index.date).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    prev_close = daily["close"].shift(1)
    f["gap"] = (day_open / day.map(prev_close) - 1) * 100
    f["fromOpen"] = (c / day_open - 1) * 100
    end = d5.index + pd.Timedelta(minutes=5)
    f["tod"] = end.hour * 100 + end.minute
    dtr = pd.concat([daily.high - daily.low, (daily.high - prev_close).abs(), (daily.low - prev_close).abs()], axis=1).max(axis=1)
    f["atr_d"] = day.map(dtr.rolling(14, min_periods=10).mean().shift(1)).to_numpy()

    # ---- MarcoFlow component scores (piecewise, as in heat-tracker.ts) ----
    vr, vs = f.volumeRatio.fillna(1), f.volumeSurge.fillna(1)
    f["volumeHeat"] = np.select([vs > 2, vr > 1.5, vr < 0.5], [20, np.minimum(20, (vr - 1) * 20), -10], (vr - 1) * 15)
    r = f.rsi.fillna(50)
    f["rsiHeat"] = np.select([r >= 80, r >= 70, r <= 20, r <= 30, r < 45, r > 55],
                             [-25, -((r - 70) / 10) * 20, 25, ((30 - r) / 10) * 20, (45 - r) / 15 * 10, (55 - r) / 15 * 10], 0)
    f["momentumHeat"] = (f.momentum.fillna(0) * 8).clip(-20, 20)
    pp = f.pricePosition
    f["priceActionHeat"] = np.select([pp <= 0.2, pp >= 0.8], [15, -15], (0.5 - pp) * 20)
    f["trendHeat"] = (f.emaDiff.fillna(0) * 5).clip(-15, 15)
    f["macdHeat"] = (f.macdPct.fillna(0) * 20).clip(-10, 10)
    f["vwapHeat"] = (f.vwapDistPct.fillna(0) * 12).clip(-12, 12)
    vh, mh, rh, ph, th = f.volumeHeat, f.momentumHeat, f.rsiHeat, f.priceActionHeat, f.trendHeat
    bonus = (np.where((vh > 5) & (mh > 5), 5, 0) + np.where((rh > 10) & (ph > 5), 5, 0)
             + np.where((vh < -5) & (mh < -5), -5, 0) + np.where((rh < -10) & (ph < -5), -5, 0))
    f["heat"] = (f[COMPONENTS].sum(axis=1) + bonus).clip(-100, 100)
    return f


def build_dataset(bars: dict[str, pd.DataFrame], cost_ps: float = 0.01, r_frac: float = 0.25, log=print) -> pd.DataFrame:
    out = []
    for n, (sym, d5) in enumerate(bars.items()):
        if len(d5) < 300:
            continue
        f = heat_frame(d5)
        f = f.join(_outcomes(f, r_frac, cost_ps))
        f["symbol"] = sym
        f = f[(f.tod >= 950) & (f.tod <= 1500) & f.atr_d.notna() & f.rsi.notna()]
        out.append(f.astype({k: "float32" for k in COMPONENTS + RAW + ["heat", "r_long", "r_short", "succ_long", "succ_short"]}))
        if n % 200 == 0:
            log(f"heat: {n}/{len(bars)} symbols")
    x = pd.concat(out)
    x["date"] = x.index.date
    return x.drop(columns=["high", "low"])


def split_and_save(x: pd.DataFrame, data_dir: Path = DATA_DIR, locked_dir: Path | None = None) -> dict:
    """Chronological split: train 60% of sessions, valid 20%, test 20% (written to locked_dir)."""
    days = np.array(sorted(x.date.unique()))
    a, b = days[int(len(days) * 0.6)], days[int(len(days) * 0.8)]
    data_dir.mkdir(parents=True, exist_ok=True)
    parts = {"train": x[x.date < a], "valid": x[(x.date >= a) & (x.date < b)], "test": x[x.date >= b]}
    for k, df in parts.items():
        d = (locked_dir or data_dir) if k == "test" else data_dir
        Path(d).mkdir(parents=True, exist_ok=True)
        df.reset_index(names="ts").to_parquet(Path(d) / f"{k}.parquet", index=False)
    return {k: {"rows": len(v), "from": str(v.date.min()), "to": str(v.date.max()), "symbols": int(v.symbol.nunique())}
            for k, v in parts.items()}


# ------------------------------------------------------------------------------------- lab
def load(split: str, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    if split == "test" and not os.environ.get("MCF_HEAT_ALLOW_TEST"):
        raise PermissionError("the test split is locked until final verification")
    df = pd.read_parquet(Path(data_dir) / f"{split}.parquet")
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def evaluate(df: pd.DataFrame, score: np.ndarray | pd.Series, long_at: float | None, short_at: float | None,
             first_per_day: bool = True) -> dict:
    """Trade a score: long when score >= long_at, short when score <= short_at (None = side off).
    One entry per symbol-day per side (the FIRST qualifying bar), as a live system would.
    Returns per-side and combined stats; R already includes costs."""
    s = np.asarray(score, dtype=float)
    out, frames = {}, []
    key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
    for side, thr in (("long", long_at), ("short", short_at)):
        if thr is None:
            continue
        m = (s >= thr) if side == "long" else (s <= thr)
        idx = np.flatnonzero(m & np.isfinite(df[f"r_{side}"].to_numpy()))
        if first_per_day and len(idx):
            _, first = np.unique(key[idx], return_index=True)
            idx = idx[first]
        t = pd.DataFrame({"date": df["date"].to_numpy()[idx], "r": df[f"r_{side}"].to_numpy()[idx],
                          "succ": df[f"succ_{side}"].to_numpy()[idx], "side": side})
        out[side] = _stats(t)
        frames.append(t)
    allt = pd.concat(frames) if frames else pd.DataFrame(columns=["date", "r", "succ", "side"])
    out["both"] = _stats(allt)
    return out


def _stats(t: pd.DataFrame) -> dict:
    n = len(t)
    if n == 0:
        return {"n": 0}
    r = t["r"].astype(float)
    daily = t.groupby("date")["r"].sum()
    weeks = t.groupby(pd.to_datetime(t["date"]).dt.isocalendar().week)["r"].sum()
    k = float(t["succ"].sum())
    z = 1.96
    p = k / n
    lb = (p + z * z / (2 * n) - z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)
    gw, gl = r[r > 0].sum(), -r[r <= 0].sum()
    return {"n": n, "per_day": round(n / max(1, daily.size), 1), "success": round(p, 4), "success_lb": round(float(lb), 4),
            "win_rate": round(float((r > 0).mean()), 4), "exp_r": round(float(r.mean()), 4),
            "exp_r_se": round(float(r.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0, 4),
            "profit_factor": round(float(gw / gl), 3) if gl > 0 else None,
            "green_days": round(float((daily > 0).mean()), 3), "green_weeks": round(float((weeks > 0).mean()), 3)}
