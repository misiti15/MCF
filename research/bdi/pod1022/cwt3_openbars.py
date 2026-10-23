"""cwt3_openbars - per symbol-day opening statistics for the pod1022 cwt3 modules (helper, not a setup).

The lab frames start at the 09:50 bar, so the cwt3 modules that need the 09:30 print, the 09:30-09:35 / 09:30-10:00
opening ranges, the 09:35-09:45 bars, the first-30-minute volume or a multi-day volume profile get them from the SIP
1-minute cache (data/cache_hist/1Min, the bars the frames were built from). Point in time: every per-day value uses
only that day's bars up to the stated time; the composite value area and the 30-minute relative volume use only
completed prior sessions. The rule-19 locked block (2024-11-01..2025-02-28) is filtered out at the parquet read
(pyarrow filter), so its rows never reach Python, and a look-back that would span it is dropped (calendar-span check).

Built once and cached as parquet in the scratchpad (CACHE below). Educational only - not financial advice.
"""
from __future__ import annotations

import datetime as dt
import os
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data" / "cache_hist" / "1Min"
CACHE = Path(os.environ.get("CWT3_OPEN_CACHE",
                            "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pod/cwt3_open.parquet"))
LOCKED = (dt.date(2024, 11, 1), dt.date(2025, 2, 28))
FIRST = dt.date(2024, 10, 1)
_MEM = {}


def _read(path: Path) -> pd.DataFrame:
    tz = "America/New_York"
    col = ds.field("__index_level_0__")
    lo = pa.scalar(pd.Timestamp(LOCKED[0], tz=tz), type=pa.timestamp("us", tz=tz))
    hi = pa.scalar(pd.Timestamp(LOCKED[1] + dt.timedelta(days=1), tz=tz), type=pa.timestamp("us", tz=tz))
    first = pa.scalar(pd.Timestamp(FIRST, tz=tz), type=pa.timestamp("us", tz=tz))
    flt = (col >= first) & ((col < lo) | (col >= hi))
    t = ds.dataset(str(path), format="parquet").to_table(filter=flt)
    df = t.to_pandas()
    if "__index_level_0__" in df.columns:
        df = df.set_index("__index_level_0__")
    return df


def _va(closes, vols, ref):
    """POC / VAL / VAH (70%) of a volume-at-close profile, bins of 0.1% of ref."""
    w = max(0.01, ref * 0.001)
    b = np.floor(closes / w).astype(np.int64)
    b0 = b.min()
    hist = np.bincount(b - b0, weights=vols)
    tot = hist.sum()
    if tot <= 0:
        return np.nan, np.nan, np.nan
    p = int(np.argmax(hist))
    lo = hi = p
    acc = hist[p]
    while acc < 0.7 * tot:
        up = hist[hi + 1] if hi + 1 < len(hist) else -1.0
        dn = hist[lo - 1] if lo - 1 >= 0 else -1.0
        if up < 0 and dn < 0:
            break
        if up >= dn:
            hi += 1
            acc += up
        else:
            lo -= 1
            acc += dn
    return (b0 + p + 0.5) * w, (b0 + lo) * w, (b0 + hi + 1) * w


def _one(path: str):
    sym = Path(path).stem
    try:
        df = _read(Path(path))
    except Exception:
        return None
    if df.empty:
        return None
    idx = df.index
    mins = idx.hour * 60 + idx.minute
    df = df[(mins >= 570) & (mins < 960)]
    if df.empty:
        return None
    idx = df.index
    m = (idx.hour * 60 + idx.minute).to_numpy() - 570          # minutes since 09:30
    df = df.assign(_d=idx.date, _b=m // 5)
    g5 = df.groupby(["_d", "_b"], sort=True).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"),
                                                  c=("close", "last"), v=("volume", "sum"))
    g5 = g5.reset_index()
    g5["tp"] = (g5["h"] + g5["l"] + g5["c"]) / 3
    g5["pv"] = g5["tp"] * g5["v"]
    gd = g5.groupby("_d", sort=True)
    g5["vwap"] = gd["pv"].cumsum() / gd["v"].cumsum().replace(0, np.nan)
    rows = []
    days = list(gd.groups.keys())
    per = {d: x for d, x in gd}
    for d in days:
        x = per[d]
        b = x["_b"].to_numpy()
        if len(b) == 0 or b[0] != 0:
            rows.append({"date": d})
            continue
        c, h, l, v, vw, o = (x[k].to_numpy(float) for k in ("c", "h", "l", "v", "vwap", "o"))
        r = {"date": d, "o930": o[0], "h5": h[0], "l5": l[0]}
        s30 = b < 6
        r["h30"], r["l30"] = h[s30].max(), l[s30].min()
        r["vol30"] = v[s30].sum()
        r["c1000"] = c[b == 5][0] if (b == 5).any() else np.nan
        r["low950"] = l[b < 4].min()
        for k, tag in ((1, "935"), (2, "940"), (3, "945")):
            sel = b == (k - 1)                                       # bar index 0 closes 09:35
            r["c" + tag] = c[sel][0] if sel.any() else np.nan
            r["vw" + tag] = vw[sel][0] if sel.any() else np.nan
        # first 5m close above the 09:30-09:35 high among the bars closing 09:40 / 09:45 (the 09:50 bar is in the frame)
        r["or5_cross_pre950"] = float(any(c[b == k][0] > h[0] for k in (1, 2) if (b == k).any()))
        r["below_vwap_pre950"] = float(any(c[b == k][0] < vw[b == k][0] for k in (0, 1, 2) if (b == k).any()))
        rows.append(r)
    out = pd.DataFrame(rows)
    out["date"] = pd.to_datetime(out["date"]).dt.date
    out = out.sort_values("date").reset_index(drop=True)
    # completed-session look-backs
    dts = pd.to_datetime(out["date"])
    v30 = out["vol30"]
    mu = v30.shift(1).rolling(20, min_periods=10).mean()
    span = (dts - dts.shift(20)).dt.days
    mu[~(span <= 40) & span.notna()] = np.nan
    out["rvol30"] = v30 / mu
    poc = np.full(len(out), np.nan)
    val = np.full(len(out), np.nan)
    vah = np.full(len(out), np.nan)
    for i in range(3, len(days) if len(days) == len(out) else 0):
        d0 = days[i]
        if (d0 - days[i - 3]).days > 7:
            continue
        xs = [per[days[i - k]] for k in (1, 2, 3)]
        cc = np.concatenate([x["c"].to_numpy(float) for x in xs])
        vv = np.concatenate([x["v"].to_numpy(float) for x in xs])
        ok = np.isfinite(cc) & np.isfinite(vv)
        if ok.sum() < 30:
            continue
        poc[i], val[i], vah[i] = _va(cc[ok], vv[ok], float(xs[0]["c"].iloc[-1]))
    out["poc3"], out["val3"], out["vah3"] = poc, val, vah
    out.insert(0, "symbol", sym)
    return out


def build(procs: int = 3) -> pd.DataFrame:
    files = sorted(str(p) for p in SRC.glob("*.parquet"))
    with Pool(procs) as pool:
        parts = [p for p in pool.imap_unordered(_one, files, chunksize=4) if p is not None]
    out = pd.concat(parts, ignore_index=True)
    s = out["date"]
    assert not ((s >= LOCKED[0]) & (s <= LOCKED[1])).any()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(CACHE, index=False)
    return out


def table() -> pd.DataFrame:
    """The cached per symbol-day table (symbol str, date datetime.date, ...). Builds it on first use."""
    if "t" in _MEM:
        return _MEM["t"]
    if not CACHE.exists():
        build()
    t = pd.read_parquet(CACHE)
    t["date"] = pd.to_datetime(t["date"]).dt.date
    t["symbol"] = t["symbol"].astype(str)
    s = t["date"]
    t = t[(s < LOCKED[0]) | (s > LOCKED[1])].reset_index(drop=True)
    _MEM["t"] = t
    return t


def join(df, cols) -> pd.DataFrame:
    """Left-join `cols` of the table onto df's (symbol, date) rows, in df's row order."""
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    return key.merge(table()[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")


if __name__ == "__main__":
    import sys
    import time
    t0 = time.time()
    if len(sys.argv) > 1:
        print(_one(str(SRC / f"{sys.argv[1]}.parquet")).tail(8).to_string())
    else:
        o = build()
        print(len(o), o["symbol"].nunique(), f"{time.time() - t0:.0f}s")
