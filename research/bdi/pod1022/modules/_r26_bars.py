"""_r26_bars - shared helper for the pod r2_6 modules (Shannon calendar / rolling AVWAPs, pocket pivot, 30m structure,
quarter-end momentum). Not a setup (no SIDE / mask).

The scorer frame has no raw 5-minute volume and starts at 09:50. The r2_6 modules need, point in time:
  * full regular-session 5-minute bars 09:35..16:00 (bar close) with o / h / l / c / v for the 15 index / sector
    ETFs only -> etf_bars.parquet (symbol, dn = days since 1970-01-01, tod, o, h, l, c, v, tpv = typical x volume)
  * per (symbol, date) day aggregates of COMPLETED sessions: S = sum(typical x volume), V = sum(volume), cls = the
    16:00 close, fh_rng = 09:30-10:30 high - low, cv_T = cumulative volume 09:30..T for T = 13:00..14:30,
    ctp_T / cvl_T = cumulative typical x volume / volume 09:30..T for T = 15:05..15:55
    -> day.parquet
They are aggregated once from the 1-minute vendor bars in data/cache_hist/1Min. Rows inside the rule-19 locked block
(2024-11-01..2025-02-28) are dropped right after each file is read and are never aggregated, cached or used. Callers
use a day's aggregates only on LATER days and a bar's values only on that bar or later.
Cache in the session scratchpad (build: python _r26_bars.py).
Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[4]
_SRC = _ROOT / "data" / "cache_hist" / "1Min"
# The scratchpad disk was full on 2026-10-23, so the cache lives in RAM-backed /dev/shm (about 150 MB).
_OUT = Path(os.environ.get("POD_R26_CACHE", "/dev/shm/pod_r26_9c6fc50d"))
_LOCKED = ("2024-11-01", "2025-02-28")
_LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
_MEM = {}
CV_TODS = [1300 + 5 * k for k in range(12)] + [1400 + 5 * k for k in range(7)]       # 13:00 .. 14:30
LATE_TODS = [1505 + 5 * k for k in range(11)]                                           # 15:05 .. 15:55

ETF15 = ["SPY", "QQQ", "IWM", "DIA", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]


def lib():
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib as L
    return L


def _one(sym):
    p = _SRC / f"{sym}.parquet"
    if not p.exists():
        return None
    x = pd.read_parquet(p)
    if not len(x):
        return None
    loc = x.index.tz_localize(None).as_unit("ns").asi8 // 60_000_000_000
    day = loc // 1440
    mins = loc % 1440
    lo = pd.Timestamp(_LOCKED[0]).value // 86_400_000_000_000
    hi = pd.Timestamp(_LOCKED[1]).value // 86_400_000_000_000
    keep = ((day < lo) | (day > hi)) & (mins >= 570) & (mins < 960)       # 09:30 .. 16:00 bar close
    if not keep.any():
        return None
    day, mins = day[keep], mins[keep]
    o, h, l, c, v = (x[k].to_numpy(float)[keep] for k in ("open", "high", "low", "close", "volume"))
    del x
    bucket = (mins - 570) // 5
    gid = day * 100 + bucket
    st = np.flatnonzero(np.r_[True, gid[1:] != gid[:-1]])
    en = np.r_[st[1:], len(gid)]
    tm = 570 + 5 * (bucket[st] + 1)
    a = pd.DataFrame({"dn": day[st].astype(np.int32), "tod": ((tm // 60) * 100 + tm % 60).astype(np.int16),
                      "o": o[st], "h": np.maximum.reduceat(h, st), "l": np.minimum.reduceat(l, st), "c": c[en - 1],
                      "v": np.add.reduceat(v, st)})
    a["tpv"] = (a["h"] + a["l"] + a["c"]) / 3.0 * a["v"]
    t = a["tod"].to_numpy()
    g = a.groupby("dn")
    D = pd.DataFrame({"S": g["tpv"].sum(), "V": g["v"].sum(), "cls": g["c"].last(), "last_tod": g["tod"].last()})
    fh = a[t <= 1030].groupby("dn")
    D["fh_rng"] = fh["h"].max() - fh["l"].min()
    a["cv"] = g["v"].cumsum()
    W = a.pivot(index="dn", columns="tod", values="cv").sort_index().ffill(axis=1)
    for T in CV_TODS:
        D[f"cv_{T}"] = W[T] if T in W.columns else np.nan
    a["ctp"] = g["tpv"].cumsum()
    Wt = a.pivot(index="dn", columns="tod", values="ctp").sort_index().ffill(axis=1)
    for T in LATE_TODS:                  # cumulative typical x volume / volume through the late bars (prior days)
        D[f"ctp_{T}"] = Wt[T] if T in Wt.columns else np.nan
        D[f"cvl_{T}"] = W[T] if T in W.columns else np.nan
    a = a.drop(columns="ctp")
    D = D.reset_index()
    D["date"] = pd.to_datetime(D["dn"].astype("int64"), unit="D").dt.strftime("%Y-%m-%d")
    D.insert(0, "symbol", sym)
    a.insert(0, "symbol", sym)
    a = a.drop(columns="cv")
    for col in ("o", "h", "l", "c", "v", "tpv"):
        a[col] = a[col].astype("float64" if col in ("v", "tpv") else "float32")
    a["m"] = pd.to_datetime(a["dn"].astype("int64"), unit="D").dt.strftime("%Y-%m")
    a = a[~a["m"].isin(_LOCKED_MONTHS)]
    D = D[~D["date"].str[:7].isin(_LOCKED_MONTHS)]
    return D, a


def build(procs=3):
    _OUT.mkdir(parents=True, exist_ok=True)
    if (_OUT / "_done").exists():
        return
    syms = sorted(p.stem for p in _SRC.glob("*.parquet"))
    open_m = set(lib().months()) - _LOCKED_MONTHS
    from multiprocessing import Pool
    Ds, Es = [], []
    with Pool(procs) as pool:
        for r in pool.imap_unordered(_one, syms, chunksize=4):
            if r is None:
                continue
            for c in [c for c in r[0].columns if c.startswith(("cv_", "cvl_", "ctp_")) or c in ("S", "V")]:
                r[0][c] = r[0][c].astype("float64" if c == "S" or c.startswith("ctp_") else "float32")
            Ds.append(r[0])
            if r[0]["symbol"].iloc[0] in ETF15:
                Es.append(r[1][r[1]["m"].isin(open_m)].drop(columns="m"))
    pd.concat(Ds, ignore_index=True).to_parquet(_OUT / "day.parquet", index=False)
    pd.concat(Es, ignore_index=True).sort_values(["symbol", "dn", "tod"]).to_parquet(_OUT / "etf_bars.parquet",
                                                                                      index=False)
    (_OUT / "_done").write_text("ok")


def day():
    if "day" not in _MEM:
        d = pd.read_parquet(_OUT / "day.parquet")
        d["symbol"] = d["symbol"].astype(str)
        d = d.sort_values(["symbol", "dn"], kind="mergesort").reset_index(drop=True)
        _MEM["day"] = d
    return _MEM["day"]


def etf_bars(symbols=None):
    """Full-session 5m bars of the ETFs (every open month; the locked block is not in the cache)."""
    if "etf" not in _MEM:
        B = pd.read_parquet(_OUT / "etf_bars.parquet")
        B["symbol"] = B["symbol"].astype(str)
        _MEM["etf"] = B.sort_values(["symbol", "dn", "tod"], kind="mergesort").reset_index(drop=True)
    B = _MEM["etf"]
    if symbols is not None:
        B = B[B["symbol"].isin(set(symbols))].reset_index(drop=True)
    return B


def prev_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    y, mo = (y - 1, 12) if mo == 1 else (y, mo - 1)
    return f"{y:04d}-{mo:02d}"


def frame_keys(df):
    dn = (pd.to_datetime(pd.Series(df["date"].to_numpy()).astype(str)).to_numpy("datetime64[D]").astype(np.int64))
    return pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "dn": dn,
                         "tod": df["tod"].to_numpy(np.int64)})


def map_bars(df, tab, cols):
    """Left-join tab (symbol, dn, tod, cols) onto df rows, in df order."""
    k = frame_keys(df)
    T = tab[["symbol", "dn", "tod"] + list(cols)].copy()
    T["dn"] = T["dn"].astype(np.int64)
    T["tod"] = T["tod"].astype(np.int64)
    m = k.merge(T, on=["symbol", "dn", "tod"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


def map_day(df, tab, cols):
    """Left-join a per-(symbol, date str) table onto df rows."""
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(),
                      "date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy()})
    m = k.merge(tab[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


def daily():
    """lib.daily() sorted, with a run id that restarts after a > 7-day gap (never bridges the locked block)."""
    if "daily" in _MEM:
        return _MEM["daily"]
    d = lib().daily()[["symbol", "date", "open", "high", "low", "close", "volume", "adv20"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    d["run"] = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    _MEM["daily"] = d
    return d


if __name__ == "__main__":
    build()
    print("built", _OUT)
