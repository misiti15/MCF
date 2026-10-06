"""Variant feature builder for the global indicator-length sweep (rework key: lengths).

Educational only -- not financial advice.

Rebuilds the setups2 feature frame from 1-minute bars in data/cache, but with every length-dependent feature
computed at several lengths so any length setting can be applied to any setup:
  rsi_{7,10,14,21}        MarcoFlow simple-average RSI on 5-min closes (the "RSI(14)" slot)
  rsis_{3,5,7,10}         the short RSI slot (setups2 "rsi5")
  rsiSlope_{L}, bear_div_{L}   rsi_L - rsi_L 3 bars ago; price at 20-bar high while rsi_L > 5 below its 20-bar max
  smad_{10,20,50,100}     5-min SMA distance in % (the sma20 / sma50 slots)
  atr_{A}, dpl_{A}, dph_{A}  daily ATR(A); distance to prior-day low/high in daily ATR(A)
  r_{side}_{geom}_a{A}, win_...   outcomes with R = 0.25 x daily ATR(A), A in {10,14,20}
Outcome convention follows mcf/research/setup_lab.py (entry at the signal bar close, first touch of target/stop on
later 5-min bars, stop-first when both are inside one bar, timed exit at the last bar closing <= 15:55), but costs are
the FULL config costs (rule 1): per side 1c/share + 1 bps (3c/share + 1 bps on extended-tier names, 20-day ADV <
$5M), plus 2c/share extra on stop exits. setups2 used a flat 1c/share per side, so these numbers are harsher.

Locked data guard: only bars with timestamp < 2026-09-16 are read (pyarrow filter). Train = 2026-07-15..2026-08-25
(the first ~20 sessions from 2026-06-15 are warm-up so ATR(20) is complete for every variant), valid =
2026-08-26..2026-09-15.
"""
from __future__ import annotations

import gc
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "data" / "cache" / "1Min"
END = pd.Timestamp("2026-09-16", tz="America/New_York")
FIRST = pd.Timestamp("2026-07-15").date()
TRAIN_END = pd.Timestamp("2026-08-25").date()
VALID_END = pd.Timestamp("2026-09-15").date()
RSI_L = (7, 10, 14, 21)
RSIS_L = (3, 5, 7, 10)
SMA_L = (10, 20, 50, 100)
ATR_L = (10, 14, 20)
OUTS = (("short", "t1s1"), ("short", "t05s1"), ("short", "t1s05"), ("long", "t05s1"))
GEOMS = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
PS, BPS, PS_EXT, STOP_X, MIN_ADV = 0.01, 1e-4, 0.03, 0.02, 5_000_000


def rsi_simple(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    g = d.clip(lower=0).rolling(n).sum() / n
    l = (-d.clip(upper=0)).rolling(n).sum() / n
    rsi = 100 - 100 / (1 + g / l.replace(0, np.nan))
    return rsi.where(l != 0, 100.0)


def load_5m(sym: str) -> pd.DataFrame:
    df = pd.read_parquet(CACHE / f"{sym}.parquet", filters=[("timestamp", "<", END)])
    df = df[df.index < END]
    t = df.index.time
    df = df[(t >= pd.Timestamp("09:30").time()) & (t < pd.Timestamp("16:00").time())]
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    return df.resample("5min", label="left", closed="left").agg(agg).dropna(subset=["open"])


def outcomes(c, h, l, tod, dates, rr, cost_side, side, up_k, dn_k, close_by=1555):
    """Realised R after costs and win flag for an entry at each bar close (setup_lab convention)."""
    n = len(c)
    r_out, w_out = np.full(n, np.nan), np.full(n, np.nan)
    bounds = np.flatnonzero(np.r_[True, dates[1:] != dates[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        cc, hh, ll, rrr, cs = c[a:b], h[a:b], l[a:b], rr[a:b], cost_side[a:b]
        m = b - a
        later = np.triu(np.ones((m, m), bool), 1) & (tod[a:b] <= close_by)[None, :]
        last = np.where(later.any(1), m - 1 - np.argmax(later[:, ::-1], 1), np.arange(m))
        ok = np.isfinite(rrr) & (rrr > 0)
        rs = np.where(ok, rrr, 1.0)
        tgt, stp = cc + side * up_k * rrr, cc - side * dn_k * rrr
        hit_t = ((hh[None, :] >= tgt[:, None]) if side == 1 else (ll[None, :] <= tgt[:, None])) & later
        hit_s = ((ll[None, :] <= stp[:, None]) if side == 1 else (hh[None, :] >= stp[:, None])) & later
        big = m + 1
        ft = np.where(hit_t.any(1), np.argmax(hit_t, 1), big)
        fs = np.where(hit_s.any(1), np.argmax(hit_s, 1), big)
        won = ft < fs
        lost = (fs <= ft) & (fs < big)
        val = np.where(won, up_k, np.where(lost, -dn_k, side * (cc[last] - cc) / rs))
        cost = (2 * cs + STOP_X * lost) / rs
        r_out[a:b] = np.where(ok, val - cost, np.nan)
        w_out[a:b] = np.where(ok, won.astype(float), np.nan)
    return r_out, w_out


def features(sym: str, d5: pd.DataFrame) -> pd.DataFrame | None:
    if len(d5) < 300:
        return None
    c, h, l, v, o = d5["close"], d5["high"], d5["low"], d5["volume"], d5["open"]
    day = pd.Series(d5.index.date, index=d5.index)
    f = pd.DataFrame(index=d5.index)
    f["close"], f["low"] = c.astype("float32"), l.astype("float32")
    end = d5.index + pd.Timedelta(minutes=5)
    f["tod"] = (end.hour * 100 + end.minute).astype("int16")
    hi20 = h.rolling(20).max()
    for L in RSI_L:
        r = rsi_simple(c, L)
        f[f"rsi_{L}"] = r
        f[f"rsiSlope_{L}"] = r - r.shift(3)
        f[f"bear_div_{L}"] = ((h >= hi20) & (r < r.rolling(20).max() - 5)).astype("int8")
    for L in RSIS_L:
        f[f"rsis_{L}"] = rsi_simple(c, L)
    for L in SMA_L:
        f[f"smad_{L}"] = (c / c.rolling(L).mean() - 1) * 100
    m5, m10 = (c / c.shift(4) - 1) * 100, (c / c.shift(9) - 1) * 100
    f["momentum"] = m5 * 0.6 + m10 * 0.4
    ema = lambda n: c.ewm(span=n, adjust=False).mean()
    f["macdPct"] = (ema(12) - ema(26)) / c * 100
    typ = (h + l + c) / 3
    vw = (typ * v).groupby(day).cumsum() / v.groupby(day).cumsum().replace(0, np.nan)
    f["vwapDistPct"] = (c - vw) / vw * 100
    day_open = o.groupby(day).transform("first")
    daily = d5.groupby(d5.index.date).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"),
                                          volume=("volume", "sum"))
    pc = daily["close"].shift(1)
    f["gap"] = (day_open / day.map(pc) - 1) * 100
    f["fromOpen"] = (c / day_open - 1) * 100
    sv = np.sign(c - o) * v
    f["flow3"] = (sv.rolling(3).sum() / v.rolling(3).sum().replace(0, np.nan)).clip(-1, 1)
    f["lower_wick"] = (np.minimum(o, c) - l) / (h - l).replace(0, np.nan)
    adv = (daily.close * daily.volume).rolling(20, min_periods=10).mean().shift(1)
    f["adv"] = day.map(adv).to_numpy()
    dtr = pd.concat([daily.high - daily.low, (daily.high - pc).abs(), (daily.low - pc).abs()], axis=1).max(axis=1)
    pdh, pdl = day.map(daily["high"].shift(1)), day.map(daily["low"].shift(1))
    cn, hn, ln = c.to_numpy(), h.to_numpy(), l.to_numpy()
    todn, dn = f["tod"].to_numpy(), np.asarray(d5.index.date)
    advn = f["adv"].to_numpy()
    cost_side = np.where(np.isfinite(advn) & (advn >= MIN_ADV), PS, PS_EXT) + BPS * cn
    for A in ATR_L:
        atr = day.map(dtr.rolling(A, min_periods=A).mean().shift(1)).replace(0, np.nan)
        f[f"atr_{A}"] = atr
        f[f"dpl_{A}"] = (c - pdl) / atr
        f[f"dph_{A}"] = (pdh - c) / atr
        rr = atr.to_numpy() * 0.25
        for side, g in OUTS:
            up, dnk = GEOMS[g]
            r, w = outcomes(cn, hn, ln, todn, dn, rr, cost_side, 1 if side == "long" else -1, up, dnk)
            f[f"r_{side}_{g}_a{A}"], f[f"win_{side}_{g}_a{A}"] = r, w
    f["date"] = dn
    keep = (f.tod >= 950) & (f.tod <= 1500) & (f.date >= FIRST) & (f.date <= VALID_END) & f["r_short_t1s1_a20"].notna()
    f = f[keep]
    num = [k for k in f.columns if f[k].dtype == np.float64]
    f = f.astype({k: "float32" for k in num})
    f["symbol"] = sym
    return f


def main(out: str, limit: int | None = None):
    syms = sorted(p.stem for p in CACHE.glob("*.parquet"))[:limit]
    frames, t0 = [], time.time()
    for i, s in enumerate(syms):
        try:
            f = features(s, load_5m(s))
        except Exception as e:  # noqa: BLE001
            print("skip", s, e, flush=True)
            continue
        if f is not None and len(f):
            frames.append(f)
        if i % 100 == 0:
            print(f"{i}/{len(syms)} {time.time() - t0:.0f}s", flush=True)
            gc.collect()
    x = pd.concat(frames)
    del frames
    x["symbol"] = x["symbol"].astype("category")
    x = x.reset_index(names="ts")
    x.to_parquet(out, index=False)
    print("rows", len(x), "symbols", x.symbol.nunique(), "dates", x.date.nunique(), f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
