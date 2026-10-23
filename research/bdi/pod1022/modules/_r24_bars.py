"""_r24_bars - shared helper for the pod r2_4 SMB / Bespoke modules (not a setup; no SIDE / mask).

The scorer frame has no raw 5-minute volume and starts at 09:50. The r2_4 modules need, point in time:
  * per (symbol, dn = days since 1970-01-01, tod) 5m bars 09:35..15:00 with volume `v`, close `c`, the session EMA9 of 5m closes `ema9`
    (started at the 09:35 bar each day) and the cumulative relative volume `rvc` = volume 09:30..bar close / the mean
    of the same cumulative volume (same bar time) over the 20 prior sessions (min 10)  -> bars/month=YYYY-MM.parquet
  * per (symbol, date): 09:30 open `o935`, 09:30-09:45 high / low `or_h` / `or_l`, 09:30-10:00 high / low `dr_h` /
    `dr_l`, mean 5m volume 09:30-10:00 `dr_vavg`, the 10:00 close `c1000`  -> day.parquet
They are aggregated once from the 1-minute vendor bars in data/cache_hist/1Min. Rows inside the rule-19 locked block
(2024-11-01..2025-02-28) are dropped right after each file is read and are never aggregated, cached or used; the
rolling 20-session volume baselines restart after the gap. Callers use a bar's values only on that bar or later.
Cache in the session scratchpad (build: python _r24_bars.py, a few minutes).
Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[4]
_SRC = _ROOT / "data" / "cache_hist" / "1Min"
_OUT = Path(os.environ.get("POD_R24_CACHE",
                           "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pod/r24bars"))
_LOCKED = ("2024-11-01", "2025-02-28")
_LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
_MEM = {}

# BLS CPI release dates (published in advance by BLS; 08:30 ET releases) inside the open history. 2025-10-24 is the
# shutdown-delayed September release; the October 2025 report was cancelled; 2026-02-13 is the rescheduled January
# release. Locked-block dates are omitted on purpose.
CPI_DATES = ["2024-10-10", "2025-03-12", "2025-04-10", "2025-05-13", "2025-06-11", "2025-07-15", "2025-08-12",
             "2025-09-11", "2025-10-24", "2025-12-18", "2026-01-13", "2026-02-13", "2026-03-11", "2026-04-10",
             "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12", "2026-09-11"]


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
    keep = ((day < lo) | (day > hi)) & (mins >= 570) & (mins < 900)       # 09:30 .. 15:00 bar close
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
    a = pd.DataFrame({"dn": day[st], "tod": (tm // 60) * 100 + tm % 60, "o": o[st],
                      "h": np.maximum.reduceat(h, st), "l": np.minimum.reduceat(l, st), "c": c[en - 1],
                      "v": np.add.reduceat(v, st)})
    # complete grid per day (missing bars -> v 0, c ffill) so cumulative volume is comparable across days
    days = np.unique(a["dn"].to_numpy())
    tods = np.array([(t // 60) * 100 + t % 60 for t in range(575, 901, 5)])
    grid = pd.MultiIndex.from_product([days, tods], names=["dn", "tod"])
    a = a.set_index(["dn", "tod"]).reindex(grid)
    a["v"] = a["v"].fillna(0.0)
    a["c"] = a.groupby(level=0)["c"].ffill()
    a = a.reset_index()
    a["cv"] = a.groupby("dn")["v"].cumsum()
    a["ema9"] = a.groupby("dn")["c"].transform(lambda s: s.ewm(span=9, adjust=False).mean())
    W = a.pivot(index="dn", columns="tod", values="cv").sort_index()
    seg = (pd.Series(W.index, index=W.index).diff() > 10).cumsum()
    base = W.groupby(seg.to_numpy()).transform(lambda s: s.shift(1).rolling(20, min_periods=10).mean())
    R = (W / base.where(base > 0)).stack(future_stack=True).rename("rvc").reset_index()
    a = a.merge(R, on=["dn", "tod"], how="left")
    t = a["tod"].to_numpy()
    g = lambda msk: a[msk].groupby("dn")
    D = pd.DataFrame({"o935": g(t == 935)["o"].first()})
    D["or_h"] = g(t <= 945)["h"].max()
    D["or_l"] = g(t <= 945)["l"].min()
    D["dr_h"] = g(t <= 1000)["h"].max()
    D["dr_l"] = g(t <= 1000)["l"].min()
    D["dr_vavg"] = g(t <= 1000)["v"].mean()
    D["c1000"] = g(t == 1000)["c"].last()
    D = D.reset_index()
    D["date"] = pd.to_datetime(D["dn"], unit="D").dt.strftime("%Y-%m-%d")
    D.insert(0, "symbol", sym)
    a.insert(0, "symbol", sym)
    B = a[["symbol", "dn", "tod", "c", "v", "ema9", "rvc"]].copy()
    B["dn"] = B["dn"].astype("int32")
    for col in ("c", "v", "ema9", "rvc"):
        B[col] = B[col].astype("float32")
    B["tod"] = B["tod"].astype("int16")
    D = D[~D["date"].str[:7].isin(_LOCKED_MONTHS)].drop(columns="dn")
    B["m"] = pd.to_datetime(B["dn"].astype("int64"), unit="D").dt.strftime("%Y-%m")
    B = B[~B["m"].isin(_LOCKED_MONTHS)]
    return D, B


def build(procs=3):
    _OUT.mkdir(parents=True, exist_ok=True)
    if (_OUT / "_done").exists():
        return
    syms = sorted(p.stem for p in _SRC.glob("*.parquet"))
    open_m = set(lib().months())
    from multiprocessing import Pool
    Ds = []
    parts = {}
    with Pool(procs) as pool:
        for r in pool.imap_unordered(_one, syms, chunksize=4):
            if r is None:
                continue
            Ds.append(r[0])
            B = r[1]
            B = B[B["m"].isin(open_m)]
            for m, part in B.groupby("m"):
                parts.setdefault(m, []).append(part.drop(columns="m"))
    pd.concat(Ds, ignore_index=True).to_parquet(_OUT / "day.parquet", index=False)
    (_OUT / "bars").mkdir(exist_ok=True)
    for m, ps in parts.items():
        assert m not in _LOCKED_MONTHS
        pd.concat(ps, ignore_index=True).to_parquet(_OUT / "bars" / f"month={m}.parquet", index=False)
    (_OUT / "_done").write_text("ok")


def day():
    if "day" not in _MEM:
        _MEM["day"] = pd.read_parquet(_OUT / "day.parquet")
    return _MEM["day"]


def _months_of(df):
    ds = pd.Series(pd.unique(pd.Series(df["date"].to_numpy()).astype(str)))
    return sorted(set(ds.str[:7]) - _LOCKED_MONTHS)


def bars_for(df, cols):
    """Left-join cached bar columns onto df rows (by symbol, date, tod), in df order. NaN when missing."""
    out = {c: np.full(len(df), np.nan) for c in cols}
    if not len(df):
        return out
    parts = []
    for m in _months_of(df):
        ck = ("bars", m)
        if ck not in _MEM:
            for k in [k for k in _MEM if isinstance(k, tuple) and k[0] == "bars"]:
                del _MEM[k]
            p = _OUT / "bars" / f"month={m}.parquet"
            _MEM[ck] = pd.read_parquet(p) if p.exists() else None
        if _MEM[ck] is not None:
            parts.append(_MEM[ck])
    if not parts:
        return out
    B = pd.concat(parts, ignore_index=True) if len(parts) > 1 else parts[0]
    dn = (pd.to_datetime(pd.Series(df["date"].to_numpy()).astype(str)).to_numpy("datetime64[D]")
          .astype(np.int64))
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "dn": dn,
                      "tod": df["tod"].to_numpy(np.int64)})
    Bk = B[["symbol", "dn", "tod"] + list(cols)].copy()
    Bk["tod"] = Bk["tod"].astype(np.int64)
    Bk["dn"] = Bk["dn"].astype(np.int64)
    m = k.merge(Bk, on=["symbol", "dn", "tod"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


def daymap(df, cols, tab=None):
    """Per-(symbol, date) values broadcast to df rows."""
    tab = day() if tab is None else tab
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(),
                      "date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy()})
    m = k.merge(tab[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


def spy_bars():
    """SPY 5m bars of every open day (09:35..15:00) with running high / low and the 09:30 open (_smbv5_bars evbars,
    which hold every open SPY day)."""
    if "spy" in _MEM:
        return _MEM["spy"]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import _smbv5_bars as V5
    E = V5.evbars()
    E = E[E["symbol"] == "SPY"][["date", "tod", "o", "h", "l", "c"]]
    S = E[E["tod"] <= 1500].sort_values(["date", "tod"]).reset_index(drop=True)
    S["run_h"] = S.groupby("date")["h"].cummax()
    S["run_l"] = S.groupby("date")["l"].cummin()
    S["o935"] = S.groupby("date")["o"].transform("first")
    _MEM["spy"] = S
    return S


def daily_feats():
    """Per (symbol, date D), completed days only (values as of D-1's close), from lib.daily():
    close1, high1, low1, ret1, rvol1 (D-1 volume / mean of the 20 sessions before), clpos1, rng20 (mean high-low of
    D-20..D-1), l60 (min low D-60..D-1), l10 (min low D-10..D-1), next_gap_days (calendar days to the next listed
    session; NaN on the last row - used only for the Friday / pre-holiday flag, a calendar fact known in advance)."""
    if "df" in _MEM:
        return _MEM["df"]
    d = lib().daily()[["symbol", "date", "high", "low", "close", "volume"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, h, l, v = d["close"], d["high"], d["low"], d["volume"]
    ret = c / c.groupby(g).shift(1) - 1
    rvol = v / v.groupby(g).transform(lambda s: s.shift(1).rolling(20, min_periods=20).mean())
    clpos = (c - l) / (h - l).where(h > l)
    rng = h - l
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    out["close1"] = c.groupby(g).shift(1)
    out["high1"] = h.groupby(g).shift(1)
    out["low1"] = l.groupby(g).shift(1)
    out["ret1"] = ret.groupby(g).shift(1)
    out["rvol1"] = rvol.groupby(g).shift(1)
    out["clpos1"] = clpos.groupby(g).shift(1)
    out["rng20"] = rng.groupby(g).transform(lambda s: s.shift(1).rolling(20, min_periods=20).mean())
    out["l60"] = l.groupby(g).transform(lambda s: s.shift(1).rolling(60, min_periods=60).min())
    out["l10"] = l.groupby(g).transform(lambda s: s.shift(1).rolling(10, min_periods=10).min())
    nd = dt.groupby(d["symbol"]).shift(-1)
    out["next_gap_days"] = (nd - dt).dt.days
    _MEM["df"] = out
    return out


if __name__ == "__main__":
    build()
    print("built", _OUT)
