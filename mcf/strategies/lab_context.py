"""Point-in-time market context for type: lab setups (owner 2026-10-17, questionnaire Q8 = A).

Opt-in per setup with `context:` (true = every column, or a list of names). The columns are added to the setup's own
copy of the lab feature frame (the shared frame cache is never touched), one value per 5-minute decision bar, as of
that bar's close:

  spy_fo        SPY % change from today's first 5-minute open to the close of the same 5-minute bar
  qqq_fo        the same for QQQ
  breadth       share of the universe whose 5-minute close is above its own session VWAP at that bar
  breadth_open  share of the universe whose 5-minute close is above its own open of the day at that bar
  qqq_vwap      QQQ's 5-minute close vs its own session VWAP, in % ((close - vwap) / vwap x 100; VWAP of the 5-minute
                typical price (h+l+c)/3 weighted by volume since 09:30) - the QQQ frame `vwapDistPct` at the same bar
                (owner 2026-10-22 S1, research/bdi/st7_1022: ST7Q fires only while qqq_vwap <= 0)

These are the frame definitions the swarm1017 near-misses were scored with: spy_fo / qqq_fo are the SPY / QQQ frame
`fromOpen` at the same (date, tod); qqq_vwap is the QQQ frame `vwapDistPct` at the same (date, tod); breadth is the mean of `vwapDistPct > 0` (breadth_open: `fromOpen > 0`) over the
symbols that have a frame row at that (date, tod) - mcf.research.heat.heat_frame on RTH 5-minute bars.

Universe: live, every symbol the runner polls (DayContext.peers = the poll's bars; SPY / QQQ are added to the poll
when a setup asks for spy_fo / qqq_fo / qqq_vwap); in the backtester, every symbol of the session (Backtester peers); in the
2-year history, the lab universe (`context_from_frames` over the frames, research/history2y/build_frames.py --context).

Point-in-time: a bar's values use only 1-minute bars inside that or earlier 5-minute bars, so the full-day backtest
table and the live table built from the bars so far agree on every completed bar (tests/test_lab_context.py).
A symbol without a bar in that 5-minute slot is left out of breadth (as in the frames). Missing data gives NaN, and a
NaN comparison is False, so a mask that needs a missing column fires nothing (fail safe).
Educational only - not financial advice.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

INDEX_COLS = {"spy_fo": "SPY", "qqq_fo": "QQQ"}
BREADTH_COLS = ("breadth", "breadth_open")
INDEX_VWAP_COLS = {"qqq_vwap": "QQQ"}   # owner 2026-10-22 (S1): index close vs its session VWAP, %
CONTEXT_COLS = (*INDEX_COLS, *BREADTH_COLS, *INDEX_VWAP_COLS)

_CACHE: dict = {}


def parse_context(spec) -> tuple[str, ...]:
    """The `context:` YAML value -> column names (validated). None/False -> ()."""
    if spec is None or spec is False:
        return ()
    if spec is True:
        return CONTEXT_COLS
    names = [spec] if isinstance(spec, str) else list(spec)
    bad = [n for n in names if n not in CONTEXT_COLS]
    if bad:
        raise ValueError(f"unknown lab context columns {bad}; known: {list(CONTEXT_COLS)}")
    return tuple(dict.fromkeys(names))


def context_symbols(cols) -> set[str]:
    """Index symbols the runner must poll for these columns."""
    idx = {**INDEX_COLS, **INDEX_VWAP_COLS}
    return {idx[c] for c in cols if c in idx}


def _bucket_frame(peers: dict) -> pd.DataFrame:
    """Every peer's 1-minute bars as one frame with 5-minute buckets (sym, bucket) -> o/c/typ*v/v."""
    parts = []
    for sym, b in peers.items():
        if b is None or len(b) == 0:
            continue
        parts.append(pd.DataFrame({"sym": sym, "ts": b.index, "open": b["open"].to_numpy(float),
                                   "high": b["high"].to_numpy(float), "low": b["low"].to_numpy(float),
                                   "close": b["close"].to_numpy(float), "volume": b["volume"].to_numpy(float)}))
    if not parts:
        return pd.DataFrame()
    x = pd.concat(parts, ignore_index=True)
    x["bucket"] = x["ts"].dt.floor("5min")
    # 5-minute bars exactly as mcf.data.bars.resample (label left, closed left), per symbol
    g = x.sort_values(["sym", "ts"], kind="mergesort").groupby(["sym", "bucket"], sort=True)
    return g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"),
                 volume=("volume", "sum")).reset_index()


def _breadth(peers: dict) -> pd.DataFrame:
    d = _bucket_frame(peers)
    if d.empty:
        return pd.DataFrame(columns=list(BREADTH_COLS))
    d["day"] = d["bucket"].dt.date
    typ = (d["high"] + d["low"] + d["close"]) / 3
    key = [d["sym"], d["day"]]
    cv = d["volume"].groupby(key).cumsum()
    vw = (typ * d["volume"]).groupby(key).cumsum() / cv.where(cv != 0)
    vd = (d["close"] - vw) / vw * 100
    above = np.where(np.isfinite(vd), (vd > 0).astype(float), np.nan)
    day_open = d["open"].groupby(key).transform("first")
    fo = (d["close"] / day_open - 1) * 100
    above_open = np.where(np.isfinite(fo), (fo > 0).astype(float), np.nan)
    t = pd.DataFrame({"bucket": d["bucket"], "breadth": above, "breadth_open": above_open})
    return t.groupby("bucket")[list(BREADTH_COLS)].mean()


def _index_fo(bars: pd.DataFrame | None) -> pd.Series:
    if bars is None or len(bars) == 0:
        return pd.Series(dtype=float)
    from ..data.bars import resample

    d5 = resample(bars, "5min")
    day = pd.Series(d5.index.date, index=d5.index)
    o = d5["open"].groupby(day).transform("first")
    return (d5["close"] / o - 1) * 100


def _index_vwap(bars: pd.DataFrame | None) -> pd.Series:
    """Index 5-minute close vs its session VWAP in %, exactly as mcf.research.heat.heat_frame builds `vwapDistPct`."""
    if bars is None or len(bars) == 0:
        return pd.Series(dtype=float)
    from ..data.bars import resample

    d5 = resample(bars, "5min")
    day = pd.Series(d5.index.date, index=d5.index)
    c, v = d5["close"], d5["volume"]
    typ = (d5["high"] + d5["low"] + c) / 3
    vw = (typ * v).groupby(day).cumsum() / v.groupby(day).cumsum().replace(0, np.nan)
    return (c - vw) / vw * 100


def context_table(peers: dict | None, cols) -> pd.DataFrame:
    """Context columns per 5-minute bar start (index), from today's 1-minute bars of every peer. Cached per poll /
    session: the key is the peers' identity-free state (symbol count and latest bar), so every lab setup and symbol of
    one poll shares one build."""
    cols = tuple(cols)
    if not peers:
        return pd.DataFrame(columns=list(cols))
    last = max((b.index[-1] for b in peers.values() if b is not None and len(b)), default=None)
    first = min((b.index[0] for b in peers.values() if b is not None and len(b)), default=None)
    key = (len(peers), first, last, sum(len(b) for b in peers.values() if b is not None))
    out = {}
    for c in cols:
        k = (key, "breadth" if c in BREADTH_COLS else c)
        if k not in _CACHE:
            if len(_CACHE) > 64:
                _CACHE.clear()
            if c in BREADTH_COLS:
                _CACHE[k] = _breadth(peers)
            elif c in INDEX_VWAP_COLS:
                _CACHE[k] = _index_vwap(peers.get(INDEX_VWAP_COLS[c]))
            else:
                _CACHE[k] = _index_fo(peers.get(INDEX_COLS[c]))
        v = _CACHE[k]
        out[c] = v[c] if isinstance(v, pd.DataFrame) else v
    return pd.DataFrame(out)


def add_context(f: pd.DataFrame, peers: dict | None, cols) -> pd.DataFrame:
    """A copy of the live lab frame `f` (indexed by today's 5-minute bar starts) with the context columns."""
    g = f.copy()
    if not cols:
        return g
    tab = context_table(peers, cols)
    for c in cols:
        s = tab[c] if c in tab else pd.Series(dtype=float)
        g[c] = s.reindex(f.index).to_numpy(dtype=float) if len(s) else np.nan
    return g


def context_from_frames(df: pd.DataFrame) -> pd.DataFrame:
    """History: the context table per (date, tod) from lab frames of many symbols (columns symbol, date, tod,
    fromOpen, vwapDistPct). Same definitions as context_table (the frame rows are the universe)."""
    sym = df["symbol"].astype(str).to_numpy()
    fo = df["fromOpen"].to_numpy(float)
    vd = df["vwapDistPct"].to_numpy(float)
    base = pd.DataFrame({"date": df["date"].to_numpy(), "tod": df["tod"].to_numpy()})
    t = base.assign(breadth=np.where(np.isfinite(vd), (vd > 0).astype(float), np.nan),
                    breadth_open=np.where(np.isfinite(fo), (fo > 0).astype(float), np.nan))
    out = t.groupby(["date", "tod"])[list(BREADTH_COLS)].mean()
    for c, s, x in [*((c, s, fo) for c, s in INDEX_COLS.items()), *((c, s, vd) for c, s in INDEX_VWAP_COLS.items())]:
        m = sym == s
        ser = pd.Series(x[m], index=pd.MultiIndex.from_arrays([base["date"][m], base["tod"][m]]))
        out[c] = ser[~ser.index.duplicated()].reindex(out.index)
    return out[list(CONTEXT_COLS)].reset_index()
