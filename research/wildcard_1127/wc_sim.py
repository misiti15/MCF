"""WILDCARD-1127 simulator (PREREG.md; engine label E4 WILD-sim): Gao 'market intraday momentum' on index + sector ETFs.
Builds one row per ETF-day (signal fields + gross R for both stop sizes and both directions), so every config and the
random-direction control are cut from the same rows. Locked block 2024-11-01..2025-02-28 never read (asserted).
    python research/wildcard_1127/wc_sim.py <raw_2016_2022_dir> <out_dir>
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

MAIN = Path("/home/user/MCF")
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
IDX4 = ["SPY", "QQQ", "IWM", "DIA"]
HALF = ["2016-11-25", "2017-07-03", "2017-11-24", "2018-07-03", "2018-11-23", "2018-12-24", "2019-07-03",
        "2019-11-29", "2019-12-24", "2020-11-27", "2020-12-24", "2021-11-26", "2022-11-25", "2023-07-03", "2023-11-24",
        "2024-07-03", "2024-11-29", "2024-12-24", "2025-07-03", "2025-11-28", "2025-12-24", "2026-11-27"]  # Addendum A
SEC12 = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB", "XLRE", "XLC", "SMH"]


def load(sym: str, raw_dir: Path) -> pd.DataFrame:
    out = []
    for f in (raw_dir / f"{sym}_2016_2022.parquet", MAIN / "data/cache_fresh/1Min" / f"{sym}.parquet",
              MAIN / "data/cache_hist/1Min" / f"{sym}.parquet"):
        p = pd.read_parquet(f)[["open", "high", "low", "close", "volume"]].copy()
        p.index = pd.DatetimeIndex(p.index).tz_convert("America/New_York")
        d = p.index.date
        p = p[~((d >= LOCK[0]) & (d <= LOCK[1]))]          # locked block dropped at read
        out.append(p)
    df = pd.concat(out).sort_index()
    df = df[~df.index.duplicated(keep="last")].between_time("09:30", "15:59")
    assert not ((df.index.date >= LOCK[0]) & (df.index.date <= LOCK[1])).any()
    return df


def split_of(day) -> str:
    if LOCK[0] <= day <= LOCK[1]:
        raise AssertionError("locked block day")
    s = str(day)
    if s < "2023-01-01":
        return "EARLY"
    if s < "2024-10-01":
        return "T2"
    if s < "2025-10-01":
        return "FIT"
    if s <= "2026-11-04":
        return "CHECK"
    return "LATE"


def sim(o, h, l, side, entry, stop, j0, j1):
    """bars j0..j1-1 held; market entry at o[j0] (= entry), exit at o[j1] unless stopped. returns (exit_px, kind)."""
    for k in range(j0, j1):
        hit = l[k] <= stop if side > 0 else h[k] >= stop
        if hit:
            gap = (o[k] < stop) if side > 0 else (o[k] > stop)
            return (o[k] if (gap and k > j0) else stop), 1
    return o[j1], 0


def main(raw_dir: str, out_dir: str):
    raw = Path(raw_dir); out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    spy = load("SPY", raw)
    g = spy.groupby(spy.index.date)
    vol_all = g.volume.sum()
    late = spy.between_time("13:05", "15:54"); vol_late = late.groupby(late.index.date).volume.sum()
    share = (vol_late.reindex(vol_all.index).fillna(0) / vol_all)
    half = {pd.Timestamp(x).date() for x in HALF}
    cal = list(vol_all.index)                       # SPY session calendar (locked block absent)
    prev_of = {}
    for a, b in zip(cal[:-1], cal[1:]):
        # previous session must be the real previous trading day (no gap over the locked block / missing data)
        if (b - a).days <= 4:
            prev_of[b] = a
    spy_cc = g.close.last(); spy_ret = (spy_cc / spy_cc.shift(1) - 1)
    rows = []
    for sym in IDX4 + SEC12:
        df = spy if sym == "SPY" else load(sym, raw)
        mins = (df.index.hour * 60 + df.index.minute).to_numpy()
        days = df.index.date
        o = df.open.to_numpy(float); h = df.high.to_numpy(float); l = df.low.to_numpy(float); c = df.close.to_numpy(float)
        bounds = np.flatnonzero(np.r_[True, days[1:] != days[:-1], True])
        close_of = {}
        recs = []
        for a, b in zip(bounds[:-1], bounds[1:]):
            d = days[a]
            mm = mins[a:b]
            pos = {m: a + i for i, m in enumerate(mm)}
            if 959 in pos:
                close_of[d] = c[pos[959]]
            if d in half:
                continue
            need = [599, 899, 924, 925, 955]
            if not all(m in pos for m in need):
                continue
            pd_ = prev_of.get(d)
            if pd_ is None or pd_ not in close_of:
                continue
            r1 = c[pos[599]] / close_of[pd_] - 1
            rov = c[pos[924]] / c[pos[899]] - 1
            j0 = pos[925]; j1 = pos[955]
            rng = h[j0:j1].max() - l[j0:j1].min()
            rec = dict(sym=sym, date=str(d), r1=r1, rov=rov, rng=rng, entry=o[j0])
            recs.append((rec, j0, j1))
        if not recs:
            continue
        r1s = np.array([r[0]["r1"] for r in recs]); rngs = np.array([r[0]["rng"] for r in recs])
        sig20 = pd.Series(r1s).rolling(20).std().shift(1).to_numpy()
        a20 = pd.Series(rngs).rolling(20).mean().shift(1).to_numpy()
        for i, (rec, j0, j1) in enumerate(recs):
            if not np.isfinite(sig20[i]) or not np.isfinite(a20[i]) or a20[i] <= 0:
                continue
            rec["sig20"] = sig20[i]; rec["a20"] = a20[i]
            e = rec["entry"]
            for s in (1.0, 2.0):
                for side, nm in ((1, "L"), (-1, "S")):
                    stop = e - side * s * a20[i]
                    px, kind = sim(o, h, l, side, e, stop, j0, j1)
                    rec[f"g{nm}{s:g}"] = side * (px - e) / (s * a20[i])
                    rec[f"x{nm}{s:g}"] = px; rec[f"k{nm}{s:g}"] = kind
            dd = pd.Timestamp(rec["date"]).date()
            rec["split"] = split_of(dd)
            rec["spy_cc"] = spy_ret.get(dd, np.nan)
            rows.append(rec)
        print(sym, len(recs), flush=True)
    t = pd.DataFrame(rows)
    dd = pd.to_datetime(t.date).dt.date
    assert not ((dd >= LOCK[0]) & (dd <= LOCK[1])).any()
    t.to_csv(out / "rows.csv.gz", index=False)
    print("rows", len(t), "half days", len(half), t.groupby("split").size().to_dict())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
