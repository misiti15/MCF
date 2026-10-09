"""Step 2: trend-guard features (NOTES.md 1.2) on 5-minute bars from the 1-minute SIP cache, for the symbol-days that
carry a raw signal (signals.parquet) or a backtester trade (bt_trades.parquet). Rows inside the rule-19 locked block
(2024-11-01..2025-02-28) are dropped at load, before any computation. Values are known at each 5-min bar's close.
Outputs (git-ignored): data/feat/part-*.parquet (5-min rows), data/bt1m.parquet (1-min bars of the bt trade days).
    python research/bdi/trendguard/features.py [--workers 4]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.data.bars import resample  # noqa: E402
from mcf.research.heat import _rsi_simple  # noqa: E402

CACHE = ROOT / "data" / "cache_hist" / "1Min"
LOCKED = ("2024-11-01", "2025-02-28")
DATA = HERE / "data"
NBINS, VA_SHARE = 50, 0.70


def drop_locked(m1: pd.DataFrame) -> pd.DataFrame:
    d = m1.index.strftime("%Y-%m-%d")
    return m1[(d < LOCKED[0]) | (d > LOCKED[1])]


def value_area(m1: pd.DataFrame) -> pd.DataFrame:
    """Per session: VAH / VAL of that session's 1-min volume profile (50 bins, 70%)."""
    out = {}
    tp_all = ((m1["high"] + m1["low"] + m1["close"]) / 3).to_numpy()
    v_all = m1["volume"].to_numpy(float)
    days = m1.index.date
    bounds = np.flatnonzero(np.r_[True, days[1:] != days[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        lo, hi = float(m1["low"].iloc[a:b].min()), float(m1["high"].iloc[a:b].max())
        v = v_all[a:b]
        if not np.isfinite(lo) or hi <= lo or v.sum() <= 0:
            out[days[a]] = (np.nan, np.nan)
            continue
        w = (hi - lo) / NBINS
        k = np.clip(((tp_all[a:b] - lo) / w).astype(int), 0, NBINS - 1)
        prof = np.bincount(k, weights=v, minlength=NBINS)
        top = bot = int(np.argmax(prof))
        acc, tot = prof[top], prof.sum()
        while acc < VA_SHARE * tot:
            up = prof[top + 1] if top + 1 < NBINS else -1.0
            dn = prof[bot - 1] if bot - 1 >= 0 else -1.0
            if up < 0 and dn < 0:
                break
            if up >= dn:
                top += 1; acc += up
            else:
                bot -= 1; acc += dn
        out[days[a]] = (lo + (top + 1) * w, lo + bot * w)
    return pd.DataFrame.from_dict(out, orient="index", columns=["vah", "val"])


def features(m1: pd.DataFrame) -> pd.DataFrame:
    """5-min feature frame for one symbol's (locked-free) 1-minute RTH bars."""
    d5 = resample(m1, "5min")
    c, h, l, v, o = d5["close"], d5["high"], d5["low"], d5["volume"], d5["open"]
    day = pd.Series(d5.index.date, index=d5.index)
    f = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}, index=d5.index)
    tp = (h + l + c) / 3
    cv = v.groupby(day).cumsum().replace(0, np.nan)
    vw = (tp * v).groupby(day).cumsum() / cv
    f["vwap"] = vw
    f["vsd"] = np.sqrt(((tp * tp * v).groupby(day).cumsum() / cv - vw * vw).clip(lower=0))
    f["ema9"] = c.ewm(span=9, adjust=False).mean()
    f["ema21"] = c.ewm(span=21, adjust=False).mean()
    rng = (h - l)
    mfv = np.where(rng > 0, ((c - l) - (h - c)) / rng.replace(0, np.nan), 0.0) * v
    f["cmf"] = pd.Series(mfv, index=d5.index).rolling(20).sum() / v.rolling(20).sum().replace(0, np.nan)
    f["obv"] = (np.sign(c.diff()).fillna(0) * v).cumsum()
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    upm, dnm = h.diff(), -l.diff()
    pdm = pd.Series(np.where((upm > dnm) & (upm > 0), upm, 0.0), index=d5.index)
    mdm = pd.Series(np.where((dnm > upm) & (dnm > 0), dnm, 0.0), index=d5.index)
    a = 1 / 14
    atr = tr.ewm(alpha=a, adjust=False).mean().replace(0, np.nan)
    f["pdi"] = 100 * pdm.ewm(alpha=a, adjust=False).mean() / atr
    f["mdi"] = 100 * mdm.ewm(alpha=a, adjust=False).mean() / atr
    dx = 100 * (f["pdi"] - f["mdi"]).abs() / (f["pdi"] + f["mdi"]).replace(0, np.nan)
    f["adx"] = dx.ewm(alpha=a, adjust=False).mean()
    f["rsi"] = _rsi_simple(c, 14)
    # slopes over the last 3 bars and lookbacks, on the continuous series (before any day filtering)
    f["ema9_sl"], f["ema21_sl"] = f["ema9"] - f["ema9"].shift(3), f["ema21"] - f["ema21"].shift(3)
    f["cmf_sl"], f["obv_sl"] = f["cmf"] - f["cmf"].shift(3), f["obv"] - f["obv"].shift(3)
    f["hi6"], f["lo6"] = h.rolling(6).max(), l.rolling(6).min()
    hv, lv, vv = h.to_numpy(), l.to_numpy(), v.to_numpy(float)
    hh = np.full(len(f), np.nan); hhv = hh.copy(); ll = hh.copy(); llv = hh.copy()
    if len(f) > 20:
        from numpy.lib.stride_tricks import sliding_window_view as sw
        wh, wl, wv = sw(hv[:-1], 20), sw(lv[:-1], 20), sw(vv[:-1], 20)     # window i-20..i-1 for row i
        ah, al = wh.argmax(1), wl.argmin(1)
        r = np.arange(len(ah))
        hh[20:], hhv[20:] = wh[r, ah], wv[r, ah]
        ll[20:], llv[20:] = wl[r, al], wv[r, al]
    f["hh20"], f["hh20v"], f["ll20"], f["ll20v"] = hh, hhv, ll, llv
    end = d5.index + pd.Timedelta(minutes=5)
    f["tod"] = (end.hour * 100 + end.minute).astype(np.int16)
    # prior-session value area (prior session only; missing if the prior session is not adjacent in the open data)
    va = value_area(m1)
    sess = sorted(va.index)
    prev = {s: p for p, s in zip(sess[:-1], sess[1:])}
    vah = {s: va.loc[prev[s], "vah"] if s in prev else np.nan for s in sess}
    val = {s: va.loc[prev[s], "val"] if s in prev else np.nan for s in sess}
    # a prior session inside the locked block was dropped: the first open session after it gets no value area
    gap_after_lock = {s for s in sess if s in prev and str(prev[s]) < LOCKED[0] and str(s) > LOCKED[1]}
    for s in gap_after_lock:
        vah[s] = val[s] = np.nan
    f["vah"], f["val"] = day.map(vah).astype(float), day.map(val).astype(float)
    # daily ATR(14) as heat_frame (used for the bt setups only)
    daily = d5.groupby(d5.index.date).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    pcd = daily["close"].shift(1)
    dtr = pd.concat([daily.high - daily.low, (daily.high - pcd).abs(), (daily.low - pcd).abs()], axis=1).max(axis=1)
    f["atr_d"] = day.map(dtr.rolling(14, min_periods=10).mean().shift(1)).to_numpy()
    f["date"] = pd.to_datetime(day.to_numpy())
    return f


def one(args):
    sym, days, btdays = args
    m1 = pd.read_parquet(CACHE / f"{sym}.parquet")
    m1 = drop_locked(m1)
    if m1.empty:
        return sym, None, None
    f = features(m1)
    f = f[f["date"].isin(days)].reset_index(drop=True)
    f.insert(0, "symbol", sym)
    b = None
    if btdays:
        dd = pd.to_datetime(m1.index.date)
        b = m1[dd.isin(btdays)].reset_index(names="ts")
        b.insert(0, "symbol", sym)
    return sym, f, b


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    sig = pd.read_parquet(DATA / "signals.parquet", columns=["symbol", "date"]).drop_duplicates()
    bt = pd.read_parquet(ROOT / "research" / "history2y" / "data" / "bt_trades.parquet", columns=["symbol", "date"])
    bt["date"] = pd.to_datetime(bt["date"])
    need = pd.concat([sig, bt]).drop_duplicates()
    s = need["date"].dt.strftime("%Y-%m-%d")
    need = need[(s < LOCKED[0]) | (s > LOCKED[1])]
    btd = bt.groupby("symbol")["date"].apply(set).to_dict()
    jobs = [(sym, set(g["date"]), btd.get(sym, set())) for sym, g in need.groupby("symbol")]
    (DATA / "feat").mkdir(exist_ok=True)
    buf, bts, k = [], [], 0
    with Pool(a.workers) as pool:
        for i, (sym, f, b) in enumerate(pool.imap_unordered(one, jobs, chunksize=4)):
            if f is not None and len(f):
                buf.append(f)
            if b is not None and len(b):
                bts.append(b)
            if sum(len(x) for x in buf) > 2_000_000 or i == len(jobs) - 1:
                if buf:
                    pd.concat(buf, ignore_index=True).to_parquet(DATA / "feat" / f"part-{k:03d}.parquet", index=False)
                    buf, k = [], k + 1
            if i % 100 == 0:
                print(f"{i}/{len(jobs)} symbols", flush=True)
    if bts:
        pd.concat(bts, ignore_index=True).to_parquet(DATA / "bt1m.parquet", index=False)
    print("done", flush=True)
