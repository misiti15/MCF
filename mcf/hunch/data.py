"""Hunch data: 1-min SIP cache -> 3-min RTH bars -> point-in-time features.

Bars
  3-min bars from 1-min bars, 09:30-16:00 ET: bucket b = (minute - 09:30) // 3, b = 0..129 (bar b covers
  [09:30+3b, 09:33+3b), closes at 09:33+3b). A bucket with no 1-min rows is carried flat (o=h=l=c=last close,
  volume 0, `filled`=1); guesses on filled bars are skipped.
  Guessed bars: every bar CLOSING 09:51..15:51 (b = 6..126, 121 a session; owner: after 09:50). The guess for bar b
  uses data up to bar b's close only; it is scored on bar b+1.

Locked block
  The rule-19 locked block 2024-11-01..2025-02-28 is filtered out inside the parquet read (pyarrow filter), so it is
  never read. Indicators are computed per contiguous segment (before / after the block) and the first session of each
  segment is a warm-up session (no prior-day values, short indicator history): it is never guessed.

Features (all at bar b's close, using bars <= b only; ATR = Wilder 14-bar ATR of 3-min bars)
  ret1, ret3, ret5   close change over the last 1 / 3 / 5 bars, in ATR units
  vwap_atr           (close - session VWAP) / ATR; VWAP from 1-min typical price x volume, session to date
  rsi14, rsi5        Wilder RSI(14) and RSI(5) on 3-min closes
  vol20              this bar's volume / mean volume of the previous 20 bars
  pressure           buy/sell pressure proxy: close location in bar range ((c-l)-(h-c))/(h-l), in [-1, 1],
                     times vol20 (there is no historical bid/ask flow, so this is the proxy)
  gap                (session open / prior session close - 1) x 100, in %
  fo                 (close - session open) / ATR  (% from open, in ATR units)
  orh, orl           (close - opening-range high) / ATR, (close - opening-range low) / ATR; OR = 09:30-09:45
                     (the first five 3-min bars, complete before the first guess)
  pdh, pdl           (close - prior session RTH high) / ATR, (close - prior session RTH low) / ATR
  atr_pct            ATR / close x 100
  tod                minutes from 09:30 to bar b's close
  spy_ret1, spy_fo   SPY's same-bar return (%) and % from the open (for SPY itself: its own)
  qqq_ret1, qqq_fo   QQQ the same
  sector_ret1        same-bar return (%) of the mapped sector ETF (SECTOR: SMH for semis, IBIT for crypto names);
                     unmapped names use SPY's (so for them it duplicates spy_ret1 - documented, not hidden)
  Winsorized at fixed limits (CLIP): ATR-unit distances, returns and pressure at +-20, vol20 at 20, gap at +-30%.
Educational only - not financial advice.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TZ = "America/New_York"
LOCKED = ("2024-11-01", "2025-02-28")
TRAIN = ("2024-09-16", "2026-02-28")
VALID = ("2026-03-01", "2026-10-07")
# sessions after VALID (2026-10-08 ..) are reported as FORWARD, separately

N_BUCKETS = 130
GUESS_FIRST, GUESS_LAST = 6, 126  # bars closing 09:51 .. 15:51
OR_LAST = 4  # opening range = buckets 0..4 (09:30-09:45)

INDEX = ["SPY", "QQQ", "IWM"]
# the most-traded live symbols in the journals (Primary + Testing 1 + Testing 2, 2026-11-04) that have the full
# two-year 1-min history in the cache (names listed after 2025-03 such as SNXX, SNDQ, RAM, SKHY, SSPC are left out;
# CRWV / INTW / MUU / NBIS start later in the history and join when they list)
LIVE = ["SOXS", "CRWV", "MRNA", "SOXL", "MSTU", "MSTX", "MUU", "CLSK", "CORZ", "HUT", "CIFR", "UVXY", "IREN",
        "RBRK", "CRDO", "NBIS", "RIOT", "USAR", "INTW"]
UNIVERSE = INDEX + LIVE
SECTOR = {**{s: "SMH" for s in ("SOXL", "SOXS", "CRDO", "MUU")},
          **{s: "IBIT" for s in ("MSTU", "MSTX", "CLSK", "CORZ", "HUT", "CIFR", "IREN", "RIOT")}}
CONTEXT = ["SPY", "QQQ", "SMH", "IBIT"]

FEATURES = ["ret1", "ret3", "ret5", "vwap_atr", "rsi14", "rsi5", "vol20", "pressure", "gap", "fo", "orh", "orl",
            "pdh", "pdl", "atr_pct", "tod", "spy_ret1", "spy_fo", "qqq_ret1", "qqq_fo", "sector_ret1"]


# winsor limits (fixed in advance): a near-zero ATR or an unadjusted split (e.g. UVXY / SOXS reverse splits) would
# otherwise give distances of 10^5 ATR and swamp the running scaler
CLIP = {**{k: (-20.0, 20.0) for k in ("ret1", "ret3", "ret5", "vwap_atr", "fo", "orh", "orl", "pdh", "pdl",
                                       "pressure")},
        "vol20": (0.0, 20.0), "gap": (-30.0, 30.0), "atr_pct": (0.0, 10.0)}


def cache_dir(path: str | os.PathLike | None = None) -> Path:
    if path:
        return Path(path)
    if os.environ.get("MCF_HUNCH_CACHE"):
        return Path(os.environ["MCF_HUNCH_CACHE"])
    return ROOT / "data" / "cache_hist" / "1Min"


def load_1min(symbol: str, cache: str | os.PathLike | None = None) -> pd.DataFrame:
    """RTH 1-min bars for `symbol`, the locked block filtered out inside the read (never loaded)."""
    import pyarrow.parquet as pq

    p = cache_dir(cache) / f"{symbol}.parquet"
    lo = pd.Timestamp(LOCKED[0], tz=TZ)
    hi = pd.Timestamp(LOCKED[1], tz=TZ) + pd.Timedelta(days=1)
    col = "__index_level_0__"
    tb = pq.read_table(p, filters=[[(col, "<", lo)], [(col, ">=", hi)]])
    df = tb.to_pandas()
    assert not ((df.index >= lo) & (df.index < hi)).any(), "locked block leaked into the read"
    return df


def bars3(m1: pd.DataFrame) -> pd.DataFrame:
    """3-min RTH bars from 1-min bars (index tz-aware ET). Columns: date, b, o, h, l, c, v, pv (sum tp*v), filled."""
    idx = m1.index.tz_convert(TZ) if m1.index.tz is not None else m1.index.tz_localize(TZ)
    mins = idx.hour * 60 + idx.minute - 570
    keep = (mins >= 0) & (mins < 390)
    m = m1.loc[keep]
    mins = np.asarray(mins[keep])
    date = np.asarray(idx[keep].date)
    tp = (m["high"].to_numpy() + m["low"].to_numpy() + m["close"].to_numpy()) / 3
    df = pd.DataFrame({"date": date, "b": mins // 3, "o": m["open"].to_numpy(), "h": m["high"].to_numpy(),
                       "l": m["low"].to_numpy(), "c": m["close"].to_numpy(), "v": m["volume"].to_numpy(),
                       "pv": tp * m["volume"].to_numpy()})
    g = df.groupby(["date", "b"], sort=True)
    out = g.agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), v=("v", "sum"), pv=("pv", "sum"))
    dates = out.index.get_level_values(0).unique()
    full = pd.MultiIndex.from_product([dates, range(N_BUCKETS)], names=["date", "b"])
    out = out.reindex(full)
    out["filled"] = out["c"].isna().astype(np.int8)
    out["c"] = out.groupby(level=0)["c"].ffill().bfill()
    for k in ("o", "h", "l"):
        out[k] = out[k].fillna(out["c"])
    out["v"] = out["v"].fillna(0.0)
    out["pv"] = out["pv"].fillna(0.0)
    return out.reset_index()


def _wilder(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def _rsi(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    up = _wilder(d.clip(lower=0), n)
    dn = _wilder((-d).clip(lower=0), n)
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50.0)


def segment_of(dates) -> np.ndarray:
    s = pd.Series(pd.to_datetime(pd.Series(dates)).dt.strftime("%Y-%m-%d").to_numpy())
    return np.where(s < LOCKED[0], 0, 1)


def own_features(b3: pd.DataFrame) -> pd.DataFrame:
    """Single-symbol features from its 3-min bars (see module doc). Bars <= b only, per contiguous segment."""
    parts = []
    seg = segment_of(b3["date"])
    for _, d in b3.groupby(seg, sort=True):
        parts.append(_own_segment(d.copy()))
    return pd.concat(parts, ignore_index=True)


def _own_segment(d: pd.DataFrame) -> pd.DataFrame:
    c, h, lo, v = d["c"], d["h"], d["l"], d["v"]
    pc = c.shift(1)
    tr = pd.concat([h - lo, (h - pc).abs(), (lo - pc).abs()], axis=1).max(axis=1)
    atr = _wilder(tr, 14)
    d["atr"] = atr
    a = atr.replace(0, np.nan)
    for k in (1, 3, 5):
        d[f"ret{k}"] = (c - c.shift(k)) / a
    day = d["date"]
    cv = d.groupby(day)["v"].cumsum()
    cpv = d.groupby(day)["pv"].cumsum()
    vwap = (cpv / cv.replace(0, np.nan)).fillna(c)
    d["vwap_atr"] = (c - vwap) / a
    d["rsi14"] = _rsi(c, 14)
    d["rsi5"] = _rsi(c, 5)
    vavg = v.rolling(20, min_periods=20).mean().shift(1)
    d["vol20"] = v / vavg.replace(0, np.nan)
    rng = (h - lo).replace(0, np.nan)
    clv = (((c - lo) - (h - c)) / rng).fillna(0.0)
    d["pressure"] = clv * d["vol20"]
    # session-level values (open, prior close / high / low, opening range)
    sess = d.groupby(day).agg(sopen=("o", "first"), sclose=("c", "last"), shigh=("h", "max"), slow=("l", "min"))
    sess["pclose"] = sess["sclose"].shift(1)
    sess["phigh"] = sess["shigh"].shift(1)
    sess["plow"] = sess["slow"].shift(1)
    orb = d[d["b"] <= OR_LAST].groupby("date").agg(orh=("h", "max"), orl=("l", "min"))
    sess = sess.join(orb)
    m = d[["date"]].merge(sess, left_on="date", right_index=True, how="left")
    sopen = m["sopen"].to_numpy()
    d["gap"] = (sopen / m["pclose"].to_numpy() - 1) * 100
    d["fo"] = (c - sopen) / a
    d["fo_pct"] = (c / sopen - 1) * 100
    orv = d["b"].to_numpy() > OR_LAST  # the opening range is only "known" after bar 4 closes
    d["orh"] = np.where(orv, (c - m["orh"].to_numpy()) / a, np.nan)
    d["orl"] = np.where(orv, (c - m["orl"].to_numpy()) / a, np.nan)
    d["pdh"] = (c - m["phigh"].to_numpy()) / a
    d["pdl"] = (c - m["plow"].to_numpy()) / a
    d["atr_pct"] = atr / c * 100
    d["tod"] = (d["b"] + 1) * 3.0
    d["bret"] = (c / pc - 1) * 100  # same-bar return in % (context use)
    d["range"] = h - lo
    d["range_med20"] = d["range"].rolling(20, min_periods=20).median()
    first = d["date"] == d["date"].iloc[0]
    d["warmup"] = first.astype(np.int8)
    return d


def build_panel(symbols=None, cache=None, verbose: bool = False, loader=None) -> pd.DataFrame:
    """Feature panel for the universe: one row per (symbol, date, b) for every bar 0..129 (labels in metrics).
    `loader(symbol) -> 1-min DataFrame` replaces the cache read (the live shadow passes its fetched bars); a symbol
    with no bars is skipped."""
    symbols = list(symbols or UNIVERSE)
    load = loader or (lambda s: load_1min(s, cache))
    ctx = {}

    def context(s):
        if s not in ctx:
            m1 = load(s)
            ctx[s] = (own_features(bars3(m1)).set_index(["date", "b"])[["bret", "fo_pct"]]
                      if m1 is not None and len(m1) else None)
        return ctx[s]

    rows = []
    for s in symbols:
        if verbose:
            print("  features", s, flush=True)
        m1 = load(s)
        if m1 is None or not len(m1):
            continue
        f = own_features(bars3(m1))
        key = pd.MultiIndex.from_arrays([f["date"], f["b"]])
        for name, src in (("spy", "SPY"), ("qqq", "QQQ"), ("sector", SECTOR.get(s, "SPY"))):
            c = context(src)
            cf = c.reindex(key) if c is not None else pd.DataFrame(index=key, columns=["bret", "fo_pct"], dtype=float)
            f[f"{name}_ret1"] = cf["bret"].to_numpy()
            if name != "sector":
                f[f"{name}_fo"] = cf["fo_pct"].to_numpy()
        for k, (lo, hi) in CLIP.items():
            f[k] = f[k].clip(lo, hi)
        f.insert(0, "symbol", s)
        keep = ["symbol", "date", "b", "filled", "warmup", "o", "h", "l", "c", "v", "atr", "range_med20"] + FEATURES
        f = f[keep]
        f[keep[5:]] = f[keep[5:]].astype(np.float32)  # memory at 100 / 200 tickers
        rows.append(f)
    return pd.concat(rows, ignore_index=True)


def period_of(dates) -> np.ndarray:
    s = pd.Series(pd.to_datetime(pd.Series(dates)).dt.strftime("%Y-%m-%d").to_numpy())
    return np.select([s <= TRAIN[1], s <= VALID[1]], ["TRAIN", "VALID"], "FORWARD")
