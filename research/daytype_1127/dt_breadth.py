"""DAYTYPE-1127: breadth context rebuilt per the arenastars_1127/t2ctx.py method (no look-ahead).
breadth_vwap = share of names whose 5-min bar close > typical-price cumulative VWAP from the first regular bar;
breadth_open = share whose 5-min close > the day's first regular open; per 5-min bar END tod (1130 = bar 11:25-11:30,
known at 11:30:00). Universe = the 469 names of data/cache_fresh/1Min (T2 2023-01..2024-09-13); the same 469 names are
read from data/cache_hist/1Min for 2024-09-16..2026-11-04 (FIT/CHECK), so one universe throughout.
EARLY (2016-2022) mode: 15-min SIP bars for a 130-name random sample of the same universe (dt_fetch15.py), bar END
tod; validated against the 5-min/469 version on T2 (dt_breadth.py val).
Locked block 2024-11-01..2025-02-28 dropped before anything is computed (asserted).
Usage: python dt_breadth.py main OUTDIR | early RAW15 OUTDIR | val RAW15 OUTDIR. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

MAIN = Path("/home/user/MCF/data")
TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
TODS = (1100, 1130, 1200, 1230, 1300, 1330)


def frame(b, rule):
    if b is None or not len(b):
        return None
    b = b[["open", "high", "low", "close", "volume"]].copy()
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index(); b = b[~b.index.duplicated(keep="last")]
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    d = b.index.date.astype(str)
    b = b[~((d >= LOCK[0]) & (d <= LOCK[1]))]
    if not len(b):
        return None
    if rule != "15min":
        b = b.resample(rule, label="left", closed="left").agg({"open": "first", "high": "max", "low": "min",
                                                               "close": "last", "volume": "sum"}).dropna(subset=["close"])
    day = b.index.date.astype(str)
    assert not ((day >= LOCK[0]) & (day <= LOCK[1])).any()
    typ = (b.high + b.low + b.close) / 3
    vw = (typ * b.volume).groupby(day).cumsum() / b.volume.groupby(day).cumsum().replace(0, np.nan)
    op = b.open.groupby(day).transform("first")
    # first bar of the day must start at 09:30 for the open to be the regular open
    first = pd.Series(b.index.hour * 100 + b.index.minute, index=b.index).groupby(day).transform("first")
    step = 5 if rule == "5min" else 15
    end = b.index + pd.Timedelta(minutes=step)
    tod = end.hour * 100 + end.minute
    m = np.isin(tod, TODS) & (first.to_numpy() == 930)
    return pd.DataFrame({"date": day[m], "tod": tod[m].astype(int),
                         "a": np.where(vw.notna(), (b.close > vw).astype(float), np.nan)[m],
                         "o": (b.close > op).astype(float).to_numpy()[m]})


def job_main(sym):
    out = []
    for c in ("cache_fresh", "cache_hist"):
        p = MAIN / c / "1Min" / f"{sym}.parquet"
        if p.exists():
            f = frame(pd.read_parquet(p), "5min")
            if f is not None:
                out.append(f)
    return pd.concat(out) if out else None


def job_15(p):
    try:
        b = pd.read_parquet(p)
    except Exception:
        return None
    return frame(b, "15min")


def job_val(sym):  # 1-min T2 bars aggregated to 15-min, for the EARLY-method validation
    p = MAIN / "cache_fresh" / "1Min" / f"{sym}.parquet"
    return frame(pd.read_parquet(p), "15min_agg")


def agg(parts):
    x = pd.concat([p for p in parts if p is not None], ignore_index=True)
    x = x.drop_duplicates(["date", "tod", "_s"]) if "_s" in x else x
    return x.groupby(["date", "tod"]).agg(breadth_vwap=("a", "mean"), breadth_open=("o", "mean"), n=("o", "size")).reset_index()


if __name__ == "__main__":
    mode = sys.argv[1]
    syms = sorted(p.stem for p in (MAIN / "cache_fresh/1Min").glob("*.parquet"))
    if mode == "main":
        out = Path(sys.argv[2])
        with Pool(4) as pl:
            parts = list(pl.imap_unordered(job_main, syms, chunksize=4))
        br = agg(parts)
        br.to_csv(out / "breadth_main.csv.gz", index=False)
        print(len(syms), "symbols; rows", len(br), br.date.min(), br.date.max()); print(br.describe().to_string())
    elif mode == "early":
        raw, out = Path(sys.argv[2]), Path(sys.argv[3])
        ps = sorted(raw.glob("*.parquet"))
        with Pool(4) as pl:
            parts = list(pl.imap_unordered(job_15, ps, chunksize=4))
        br = agg(parts)
        br.to_csv(out / "breadth_early.csv.gz", index=False)
        print(len(ps), "symbols; rows", len(br), br.date.min(), br.date.max()); print(br.describe().to_string())
    elif mode == "val":
        raw, out = Path(sys.argv[2]), Path(sys.argv[3])
        sample = sorted(p.stem for p in raw.glob("*.parquet"))
        import functools
        def j(s):
            p = MAIN / "cache_fresh" / "1Min" / f"{s}.parquet"
            b = pd.read_parquet(p)
            b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
            b = b[(b.index.hour * 100 + b.index.minute >= 930) & (b.index.hour * 100 + b.index.minute < 1600)]
            b = b.resample("15min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min",
                                                                      "close": "last", "volume": "sum"}).dropna(subset=["close"])
            return frame(b, "15min")
        parts = [j(s) for s in sample if (MAIN / "cache_fresh/1Min" / f"{s}.parquet").exists()]
        v = agg(parts)
        m = pd.read_csv(out / "breadth_main.csv.gz"); m["date"] = m.date.astype(str)
        v["date"] = v.date.astype(str)
        z = m.merge(v, on=["date", "tod"], suffixes=("", "_s"))
        z = z[z.date < "2024-09-14"]
        res = {}
        for c in ("breadth_vwap", "breadth_open"):
            for t in (1130, 1300):
                q = z[z.tod == t]
                agree = (np.sign(q[c] - 0.7) == np.sign(q[c + "_s"] - 0.7)) & (np.sign(q[c] - 0.3) == np.sign(q[c + "_s"] - 0.3))
                res[f"{c}@{t}"] = {"n": len(q), "corr": round(float(q[c].corr(q[c + "_s"])), 3), "agree_extremes": round(float(agree.mean()), 3)}
        import json
        json.dump(res, open(out / "early_validation.json", "w"), indent=1); print(res)
