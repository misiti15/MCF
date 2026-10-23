"""_smbv5_bars - shared helper for the pod r2_3 SMB modules (not a setup; no SIDE / mask).

The scorer frame has no raw 5-minute open / volume and starts at 09:50. Some modules need, point in time:
  * per symbol-day opening values (09:30 open, 09:30-09:45 and 09:30-10:00 cumulative volume and their rvol vs the 20
    prior sessions, the 09:30-10:00 drive high / low / mean bar volume, the 10:00 close, the low and range before
    10:30) -> dayagg.parquet,
  * full 5m bars with volume (o, h, l, c, v, typical price x volume) for EVENT symbol-days only (day-2 candidates and
    their day 1, every SPY day, and days with 09:30-10:00 rvol >= 2 and an up first half hour) -> evbars.parquet.
They are aggregated once from the 1-minute vendor bars in data/cache_hist/1Min. Rows inside the rule-19 locked block
(2024-11-01..2025-02-28) are dropped right after each file is read and are never aggregated, cached or used. The cache
lives in the session scratchpad (build: python _smbv5_bars.py, ~1 min). Day-level values that a module reads before
the end of the day (rvol at 09:45 / 10:00, drive values) are only used on bars after that time; daily context comes
from completed days only (daily_ctx).
Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[4]
_SRC = _ROOT / "data" / "cache_hist" / "1Min"
_OUT = Path(os.environ.get("POD_V5_CACHE",
                           "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pod/v5bars"))
_LOCKED = ("2024-11-01", "2025-02-28")
_LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
_MEM = {}


def lib():
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib as L
    return L


def _rv(x, n=20, minp=10):
    """x / mean of the previous n sessions (min minp); the series restarts after a > 10-day gap (locked block)."""
    return x / x.shift(1).rolling(n, min_periods=minp).mean()


def _one(arg):
    sym, need = arg
    p = _SRC / f"{sym}.parquet"
    if not p.exists():
        return None
    x = pd.read_parquet(p)
    if not len(x):
        return None
    loc = x.index.tz_localize(None).as_unit("ns").asi8 // 60_000_000_000          # local minutes since epoch
    day = loc // 1440
    mins = loc % 1440
    lo = pd.Timestamp(_LOCKED[0]).value // 86_400_000_000_000
    hi = pd.Timestamp(_LOCKED[1]).value // 86_400_000_000_000
    d0 = pd.Timestamp("2024-09-01").value // 86_400_000_000_000
    keep = ((day < lo) | (day > hi)) & (day >= d0) & (mins >= 570) & (mins < 960)
    if not keep.any():
        return None
    day, mins = day[keep], mins[keep]
    o, h, l, c, v = (x[k].to_numpy(float)[keep] for k in ("open", "high", "low", "close", "volume"))
    del x
    bucket = (mins - 570) // 5
    gid = day * 100 + bucket
    st = np.flatnonzero(np.r_[True, gid[1:] != gid[:-1]])
    en = np.r_[st[1:], len(gid)]
    tp = (h + l + c) / 3.0
    tm = 570 + 5 * (bucket[st] + 1)
    a = pd.DataFrame({
        "symbol": sym, "dn": day[st],
        "tod": (tm // 60) * 100 + tm % 60,
        "o": o[st], "h": np.maximum.reduceat(h, st), "l": np.minimum.reduceat(l, st), "c": c[en - 1],
        "v": np.add.reduceat(v, st), "pv": np.add.reduceat(tp * v, st)})
    t = a["tod"].to_numpy()
    g = a.groupby("dn", sort=True)
    D = pd.DataFrame({"o935": g["o"].first()})
    sub = lambda msk: a[msk].groupby("dn")
    D["cv0945"] = sub(t <= 945)["v"].sum()
    D["cv1000"] = sub(t <= 1000)["v"].sum()
    D["dr_h"] = sub(t <= 1000)["h"].max()
    D["dr_l"] = sub(t <= 1000)["l"].min()
    D["dr_vavg"] = sub(t <= 1000)["v"].mean()
    D["c1000"] = a[t == 1000].set_index("dn")["c"]
    D["lo_pre1030"] = sub(t <= 1030)["l"].min()
    D["fh_h"] = sub(t <= 1030)["h"].max()
    D["fh_l"] = sub(t <= 1030)["l"].min()
    D = D.reset_index()
    dd = D["dn"]
    grp = (dd.diff() > 10).cumsum()
    D["rv0945"] = D.groupby(grp, group_keys=False)["cv0945"].apply(_rv)
    D["rv1000"] = D.groupby(grp, group_keys=False)["cv1000"].apply(_rv)
    D["date"] = pd.to_datetime(D["dn"], unit="D").dt.strftime("%Y-%m-%d")
    D.insert(0, "symbol", sym)
    ev = set(D.loc[(D["rv1000"] >= 2) & (D["c1000"] > D["o935"]), "dn"]) | set(
        D.loc[D["date"].isin(need), "dn"])
    E = a[a["dn"].isin(ev)].copy()
    E["date"] = pd.to_datetime(E["dn"], unit="D").dt.strftime("%Y-%m-%d")
    D = D[~D["date"].str[:7].isin(_LOCKED_MONTHS)].drop(columns="dn")
    E = E[~E["date"].str[:7].isin(_LOCKED_MONTHS)].drop(columns="dn")
    return D, E


def build(procs=4):
    _OUT.mkdir(parents=True, exist_ok=True)
    if (_OUT / "_done").exists():
        return
    dc = daily_ctx()
    cand = dc[(dc["ret1"] >= 0.03) & (dc["rvol1"] >= 2.5) & (dc["clpos1"] >= 0.75)]
    need = {}
    for sym, d, d1 in zip(cand["symbol"], cand["date"], cand["d1date"]):
        need.setdefault(sym, set()).update([d, d1])
    symbols = sorted(set(dc["symbol"]))
    args = [(s_, need.get(s_, set()) | (set(dc.loc[dc["symbol"] == "SPY", "date"]) if s_ == "SPY" else set()))
            for s_ in symbols]
    from multiprocessing import Pool
    Ds, Es = [], []
    with Pool(procs) as pool:
        for r in pool.imap_unordered(_one, args, chunksize=8):
            if r is not None:
                Ds.append(r[0])
                Es.append(r[1])
    pd.concat(Ds, ignore_index=True).to_parquet(_OUT / "dayagg.parquet", index=False)
    E = pd.concat(Es, ignore_index=True)
    for col in ("v", "pv"):
        E[col] = E[col].astype("float64")
    E.sort_values(["symbol", "date", "tod"]).to_parquet(_OUT / "evbars.parquet", index=False)
    (_OUT / "_done").write_text("ok")


def dayagg():
    if "da" not in _MEM:
        _MEM["da"] = pd.read_parquet(_OUT / "dayagg.parquet")
    return _MEM["da"]


def evbars():
    """5m bars (symbol, date str, tod, o, h, l, c, v, pv) of event symbol-days only (day-2 candidates and their D-1,
    every SPY day, and days with 09:30-10:00 rvol >= 2 and an up first half hour)."""
    if "eb" not in _MEM:
        _MEM["eb"] = pd.read_parquet(_OUT / "evbars.parquet")
    return _MEM["eb"]


def daily_ctx():
    """Per (symbol, date D): completed-day values as of D-1 / D-2 / D-3 (lib.daily(), open dates only).
    ret1 = D-1 close / D-2 close - 1; rvol1 = D-1 volume / mean volume of the 20 sessions before D-1;
    clpos1 = D-1 close location in its range; h60 = max high of the 60 sessions D-60..D-1."""
    if "dc" in _MEM:
        return _MEM["dc"]
    d = lib().daily()[["symbol", "date", "open", "high", "low", "close", "volume"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, h, l, v, o = d["close"], d["high"], d["low"], d["volume"], d["open"]
    ret = c / c.groupby(g).shift(1) - 1
    rvol = v / v.groupby(g).transform(lambda s: s.shift(1).rolling(20, min_periods=20).mean())
    rng = (h - l).where(h > l)
    clpos = (c - l) / rng
    h60 = h.groupby(g).transform(lambda s: s.rolling(60, min_periods=60).max())
    tr = pd.concat([h - l, (h - c.groupby(g).shift(1)).abs(), (l - c.groupby(g).shift(1)).abs()], axis=1).max(axis=1)
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    for nm, s in {"ret": ret, "rvol": rvol, "clpos": clpos, "close": c, "open": o, "high": h, "low": l,
                  "h60": h60}.items():
        out[nm + "1"] = s.groupby(g).shift(1)
        out[nm + "2"] = s.groupby(g).shift(2)
    out["d1date"] = d["date"].groupby(g).shift(1)
    _MEM["dc"] = out
    return out


if __name__ == "__main__":
    build()
    print("built", _OUT)


def keys(df):
    """symbol (str), date (str) arrays and segment bounds (begin, end) of the frame's symbol-days."""
    sym = df["symbol"].astype(str).to_numpy()
    dat = pd.Series(df["date"].to_numpy()).astype(str).to_numpy()
    k = pd.factorize(pd.Series(sym) + "|" + pd.Series(dat))[0]
    n = len(k)
    if n == 0:
        return sym, dat, np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return sym, dat, b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def rowmap(df, B, cols):
    """Left-join bar columns of B (symbol, date str, tod) onto df rows, in df order."""
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(),
                      "date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy(),
                      "tod": df["tod"].to_numpy(np.int64)})
    m = k.merge(B[["symbol", "date", "tod"] + list(cols)], on=["symbol", "date", "tod"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


def segmap(sym, dat, b, tab, cols):
    """Left-join a per-(symbol, date) table onto the frame's segments (one value per segment)."""
    u = pd.DataFrame({"symbol": sym[b], "date": dat[b]})
    m = u.merge(tab[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")
    assert len(m) == len(b)
    return {c: m[c].to_numpy(float) for c in cols}
