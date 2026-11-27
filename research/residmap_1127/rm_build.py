"""RESID-MAP-1127 builder: per (symbol, session, checkpoint) raw feature inputs, entry/exit prices (PREREG.md).

Reads 1-min bars from data/cache_fresh/1Min + data/cache_hist/1Min with a row filter that never reads the locked block
(2024-11-01..2025-02-28) and asserts none survives. Writes a small parquet in the scratch dir (not committed).
Usage: python research/residmap_1127/rm_build.py OUT.parquet
Educational only - not financial advice."""

from __future__ import annotations

import os
import re
import sys
from datetime import date
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

DATA = Path("/home/user/MCF/data")
SRC = [DATA / "cache_fresh" / "1Min", DATA / "cache_hist" / "1Min"]     # later source wins on duplicate minutes
TZ = "America/New_York"
LOCK_A, LOCK_B = date(2024, 11, 1), date(2025, 2, 28)
RANGES = [("2022-10-01", "2024-11-01"), ("2025-03-01", "2026-11-05")]   # [a, b) - both outside the locked block
CPS = {"0945": 9 * 60 + 45, "1030": 10 * 60 + 30, "1200": 12 * 60, "1400": 14 * 60}
ETF_RE = re.compile(r"\bETFs?\b|\bETN\b|\bFund\b|iShares|ProShares|Direxion|SPDR|Invesco QQQ|GraniteShares|Tradr|"
                    r"Defiance|T-Rex|Leverage Shares|\b[23]X\b|UltraPro|Ultra(?:Short)? |Grayscale|Bitcoin|Ether(?:eum)? ",
                    re.I)
HALF_DAYS = ["2022-11-25", "2023-07-03", "2023-11-24", "2024-07-03", "2024-11-29", "2024-12-24", "2025-07-03",
             "2025-11-28", "2025-12-24"]
assert all(pd.Timestamp(b).date() <= LOCK_A or pd.Timestamp(a).date() > LOCK_B for a, b in RANGES)


def read_sym(sym: str) -> pd.DataFrame | None:
    parts = []
    for base in SRC:
        f = base / f"{sym}.parquet"
        if not f.exists():
            continue
        names = pq.read_schema(f).names
        col = "__index_level_0__" if "__index_level_0__" in names else "timestamp"
        for a, b in RANGES:
            t = pq.read_table(f, filters=[(col, ">=", pd.Timestamp(a, tz=TZ)), (col, "<", pd.Timestamp(b, tz=TZ))])
            df = t.to_pandas()
            if col in df.columns:
                df = df.set_index(col)
            if len(df):
                parts.append(df[["open", "high", "low", "close", "volume"]])
    if not parts:
        return None
    df = pd.concat(parts)
    df.index = pd.DatetimeIndex(df.index).tz_convert(TZ)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    dd = df.index.date
    assert not ((dd >= LOCK_A) & (dd <= LOCK_B)).any(), "locked block read"
    m = df.index.hour * 60 + df.index.minute
    df = df[(m >= 570) & (m < 960)]
    return df


def build(sym: str, spy: pd.DataFrame | None, cal: list, half: set) -> list[dict]:
    """Rows per (session, checkpoint): raw prices for the features plus residual 1-min stats (vs SPY)."""
    df = spy if sym == "SPY" else read_sym(sym)
    if df is None or not len(df):
        return []
    d_ = df.index.date
    mm = df.index.hour * 60 + df.index.minute
    close = df.close.to_numpy(); opn = df.open.to_numpy(); vol = df.volume.to_numpy()
    lr = np.r_[np.nan, np.diff(np.log(close))]
    if sym != "SPY":
        spy_lr = SPY_LR.reindex(df.index).to_numpy()
    rows = []
    # index ranges per day
    ud, start = np.unique(d_, return_index=True)
    ends = np.r_[start[1:], len(d_)]
    pos = {d: (s, e) for d, s, e in zip(ud, start, ends)}
    daily_c = {d: close[e - 1] for d, (s, e) in pos.items()}
    daily_dv = {d: float((close[s:e] * vol[s:e]).sum()) for d, (s, e) in pos.items()}
    for i, d in enumerate(cal):
        if d not in pos:
            continue
        s, e = pos[d]
        p1 = cal[i - 1] if i >= 1 else None
        p2 = cal[i - 2] if i >= 2 else None
        c1 = daily_c.get(p1); c2 = daily_c.get(p2); dv1 = daily_dv.get(p1)
        m = mm[s:e]
        if m[0] != 570:          # no 09:30 bar -> no reliable open
            continue
        o = opn[s]
        close_m = 12 * 60 + 55 if d in half else 15 * 60 + 55
        xi = np.nonzero(m <= close_m)[0]
        if not len(xi) or m[xi[-1]] < close_m - 5:
            continue
        exit_px = close[s + xi[-1]]
        r1 = lr[s:e].copy(); r1[0] = np.log(close[s] / o)
        if sym != "SPY":
            rr = r1 - spy_lr[s:e]
        else:
            rr = r1
        for cp, cm in CPS.items():
            if cp == "1400" and d in half:
                continue
            k = np.searchsorted(m, cm)             # first bar >= c
            if k == 0 or k >= len(m) or m[k] > cm + 4:
                continue
            n = k                                  # bars before c (all have m < cm)
            need = cm - 570
            if n < max(10, 0.8 * need):
                continue
            pc = close[s + k - 1]
            j5 = np.nonzero(m[:k] <= m[k - 1] - 5)[0]
            p5 = close[s + j5[-1]] if len(j5) and m[k - 1] - m[j5[-1]] <= 7 else np.nan
            rs = rr[:k]
            rs = rs[np.isfinite(rs)]
            rows.append({"sym": sym, "d": d, "cp": cp, "o": o, "pc": pc, "p5": p5, "c1": c1, "c2": c2, "dv1": dv1,
                         "entry": opn[s + k], "exit": exit_px,
                         "rsd": float(rs.std(ddof=1)) if len(rs) > 2 else np.nan, "nr": len(rs),
                         "rsum": float(rs.sum())})
    return rows


SPY_LR = None


def _init(spy_lr):
    global SPY_LR
    SPY_LR = spy_lr


def _work(args):
    sym, cal, half = args
    try:
        return build(sym, None, cal, half)
    except Exception as ex:                       # noqa: BLE001
        print("ERR", sym, ex, flush=True)
        return []


def main(out: str):
    spy = read_sym("SPY")
    sd = spy.index.date
    cal = sorted(set(sd))
    # Addendum A: the caches hold post-13:00 prints on half days, so SPY's last bar cannot detect them; use the NYSE list
    # (mcf.execution.market_calendar.PAST_EARLY_CLOSES + the 2022-23 NYSE early closes).
    half = {pd.Timestamp(x).date() for x in HALF_DAYS} & set(cal)
    print("sessions", len(cal), "half days", sorted(half), flush=True)
    lr = np.r_[np.nan, np.diff(np.log(spy.close.to_numpy()))]
    spy_lr = pd.Series(lr, index=spy.index)
    first = pd.Series(sd, index=spy.index).ne(pd.Series(sd, index=spy.index).shift())
    spy_lr[first.to_numpy()] = np.log(spy.close / spy.open)[first.to_numpy()]
    _init(spy_lr)
    spy_rows = build("SPY", spy, cal, half)
    uni = pd.read_csv(DATA / "universe.csv")
    etf = set(uni.symbol[uni.name.fillna("").str.contains(ETF_RE)])
    syms = sorted({p.stem for b in SRC for p in b.glob("*.parquet")} - etf - {"SPY"})
    print("symbols", len(syms), "etf excluded", len(etf), flush=True)
    rows = list(spy_rows)
    with Pool(4, initializer=_init, initargs=(spy_lr,)) as pool:
        for i, r in enumerate(pool.imap_unordered(_work, [(s, cal, half) for s in syms], chunksize=4)):
            rows.extend(r)
            if i % 100 == 0:
                print(i, len(rows), flush=True)
    df = pd.DataFrame(rows)
    df["d"] = pd.to_datetime(df.d)
    dd = df.d.dt.date
    assert not ((dd >= LOCK_A) & (dd <= LOCK_B)).any()
    df.to_parquet(out)
    pd.Series(sorted(half)).astype(str).to_csv(out + ".half.csv", index=False)
    print("rows", len(df))


if __name__ == "__main__":
    main(sys.argv[1])
