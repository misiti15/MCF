"""Compass conditional stats (owner 2026-11-10): "what happens after X time has passed and SPY is already this far from its
open, on this side of yesterday's close?" - a durable, continuously refreshed lookup table.

    python -m mcf.report.compass_cond --date 2026-11-10 --push   # nightly, after the close: append the day, refresh, push
    python -m mcf.report.compass_cond --date 2026-11-10          # same into data/compass/local (no push)

DISPLAY / RESEARCH ONLY - NOT A TRADING SIGNAL. Read-only Alpaca MARKET DATA GET of SPY 1-minute bars
(mcf.replay.store._fetch_bars, as compass_live); places no orders, reads / writes no trading config.

One observation per session per 10-min mark (10:00 .. 15:50 ET, bars that START before the mark, i.e. closed by it):
SPY % from its open, SPY vs the previous session's close, the gap, and the outcomes (close vs open / vs previous close,
move to the close, next 5 / 10 / 30 / 60-min direction). Cells: time x from-open bucket x (vs previous close | gap).
Baseline = the 2-year history (locked block 2024-11-01..2025-02-28 never read; research/compass_5m/build_cond.py
writes research/compass_5m/conditional_obs.csv.gz). The data branch mcf-data-compass carries compass/cond_obs.csv
(seeded from the baseline, one session appended per night; idempotent), compass/cond_stats.csv and
compass/cond_stats.json (the dashboard / compass_live read the JSON). Educational only - not financial advice.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import compass_live as CL

ROOT = CL.ROOT
NY = CL.NY
SEED = ROOT / "research" / "compass_5m" / "conditional_obs.csv.gz"
MARKS = list(range(600, 951, 10))                            # 10:00 .. 15:50 ET
HZ = (5, 10, 30, 60)
EDGES = [-np.inf, -0.004, -0.002, 0.0, 0.002, 0.004, np.inf]
BUCKETS = ["< -0.4%", "-0.4..-0.2%", "-0.2..0%", "0..+0.2%", "+0.2..+0.4%", "> +0.4%"]
GAP = 0.002                                                  # gap up / down = open >= 0.20% from the previous close
OBS_COLS = ["date", "T", "open", "px", "close", "prev_close", "fo", "vs_prev", "gap", "to_close", "eod_open",
            "eod_prev", "next5", "next10", "next30", "next60"]

lab = CL.lab


def bucket(fo: float) -> str:
    return BUCKETS[int(np.searchsorted(EDGES, fo, side="right")) - 1]


def gap_cat(g) -> str:
    if g is None or not np.isfinite(g):
        return "unknown"
    return "gap up" if g >= GAP else ("gap down" if g <= -GAP else "flat open")


def day_obs(spy: pd.DataFrame, day: str, prev_close: float | None) -> list[dict]:
    """Rows for one full session from SPY 1-minute bars (ET index). prev_close None = unknown (first day after a hole)."""
    m = spy.index.hour * 60 + spy.index.minute
    b = spy[(m >= 570) & (m < 960)]
    if not len(b):
        return []
    mm = (b.index.hour * 60 + b.index.minute).values
    c = b.close.values.astype(float)
    o, close = float(b.open.iloc[0]), float(c[-1])

    def px(T):                                               # last close of a bar starting before T
        k = np.searchsorted(mm, T, side="left") - 1
        return float(c[k]) if k >= 0 else np.nan

    pc = float(prev_close) if prev_close else np.nan
    sgn = lambda x: int(np.sign(x)) if np.isfinite(x) else None
    rows = []
    for T in MARKS:
        p = px(T)
        r = dict(date=day, T=lab(T), open=o, px=p, close=close, prev_close=pc if np.isfinite(pc) else None,
                 fo=p / o - 1, vs_prev=sgn(p / pc - 1) if np.isfinite(pc) else None,
                 gap=o / pc - 1 if np.isfinite(pc) else None, to_close=close / p - 1, eod_open=sgn(close / o - 1),
                 eod_prev=sgn(close / pc - 1) if np.isfinite(pc) else None)
        for h in HZ:
            f = close if T + h >= 960 else px(T + h)
            r[f"next{h}"] = sgn(f / p - 1) if T + h <= 960 else None
        rows.append(r)
    return rows


def _sgn(x):
    return np.sign(x.astype(float))


def cells(obs: pd.DataFrame) -> pd.DataFrame:
    """Cell table: grouping 'vs_prev' (above / below the previous close) and 'gap' (gap up / flat / down)."""
    d = obs.copy()
    for k in ["fo", "vs_prev", "gap", "to_close", "eod_open", "eod_prev"] + [f"next{h}" for h in HZ]:
        d[k] = pd.to_numeric(d[k], errors="coerce")
    d["bucket"] = [bucket(x) for x in d.fo]
    d["side"] = _sgn(d.fo)
    d["prev_side"] = d.vs_prev.map({1: "above prev close", -1: "below prev close", 0: "at prev close"}).fillna("unknown")
    d["gap_cat"] = [gap_cat(g) for g in d.gap]
    out = []
    for grouping, key in (("vs_prev", "prev_side"), ("gap", "gap_cat")):
        for (T, b, k), g in d.groupby(["T", "bucket", key], sort=True):
            if k == "unknown":
                continue
            s = g.side.where(g.side != 0, np.nan)
            same_open = (g.eod_open == s)[s.notna()].mean() if s.notna().any() else np.nan
            ps = g.vs_prev.where(g.vs_prev != 0, np.nan)
            same_prev = (g.eod_prev == ps)[ps.notna()].mean() if ps.notna().any() else np.nan
            tc = g.to_close * 100
            r = dict(grouping=grouping, T=T, bucket=b, key=k, n=len(g), same_side_open=same_open,
                     same_side_prev=same_prev, close_above_open=(g.eod_open > 0).mean(),
                     to_close_med=tc.median(), to_close_q1=tc.quantile(0.25), to_close_q3=tc.quantile(0.75))
            for h in HZ:
                x = g[f"next{h}"]; ok = x.notna() & (x != 0) & s.notna()
                r[f"next{h}_hit"] = (x[ok] == s[ok]).mean() if ok.any() else np.nan
                r[f"next{h}_n"] = int(ok.sum())
            out.append(r)
    return pd.DataFrame(out)


def to_json(C: pd.DataFrame, obs: pd.DataFrame) -> dict:
    last = obs.sort_values(["date", "T"]).iloc[-1]
    cl = {}
    for r in C.itertuples(index=False):
        cl[f"{r.grouping}|{r.T}|{r.bucket}|{r.key}"] = {
            k: (None if isinstance(v, float) and not np.isfinite(v) else (round(v, 4) if isinstance(v, float) else v))
            for k, v in r._asdict().items() if k not in ("grouping", "T", "bucket", "key")}
    return dict(asof_date=str(last.date), last_close=float(last.close), sessions=int(obs.date.nunique()),
                first_date=str(obs.date.min()), buckets=BUCKETS, edges_pct=[-0.4, -0.2, 0, 0.2, 0.4], gap_pct=GAP * 100,
                cells=cl, label=CL.LABEL, disclaimer=CL.DISCLAIMER,
                method="mcf/report/compass_cond.py; research/compass_5m/NOTES.md")


def read_obs(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path, dtype={"date": str, "T": str})
    if SEED.exists():
        with gzip.open(SEED, "rt") as f:
            return pd.read_csv(f, dtype={"date": str, "T": str})
    return pd.DataFrame(columns=OBS_COLS)


def lookup(cond: dict | None, T: int, fo: float, px: float | None) -> dict | None:
    """The cell for the latest compass mark (rounded down to the 10-min grid) - None when unknown."""
    if not cond or fo is None or not np.isfinite(fo) or T < 600:
        return None
    t10 = min(950, T - T % 10)
    pc = cond.get("last_close")
    if px is None or not pc:
        return None
    side = "above prev close" if px > pc else ("below prev close" if px < pc else None)
    if side is None:
        return None
    c = cond.get("cells", {}).get(f"vs_prev|{lab(t10)}|{bucket(fo)}|{side}")
    if not c:
        return None
    return dict(T=lab(t10), bucket=bucket(fo), side=side, **c)


def fetch_spy(day: str, log=print) -> pd.DataFrame | None:
    from ..replay import store

    start, end = pd.Timestamp(f"{day} 09:30", tz=NY), pd.Timestamp(f"{day} 16:00", tz=NY)
    log(f"compass_cond: fetching SPY 1-minute bars {day}")
    df = store._fetch_bars(["SPY"], start.tz_convert("UTC").isoformat(), end.tz_convert("UTC").isoformat(), "1Min")
    if not len(df):
        return None
    df = df.set_index("ts")
    df.index = df.index.tz_convert(NY)
    return df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()


def update(out: Path, day: str, spy_fn=fetch_spy, log=print) -> int:
    """Append `day` to out/compass/cond_obs.csv (replacing it if present), refresh the cell CSV / JSON. Returns rows."""
    d = out / "compass"
    d.mkdir(parents=True, exist_ok=True)
    obs = read_obs(d / "cond_obs.csv")
    obs = obs[obs.date != day]
    spy = spy_fn(day, log=log)
    rows = []
    if spy is None or not len(spy) or (spy.index.hour * 60 + spy.index.minute).max() < 955:
        log(f"compass_cond: {day} no full session (holiday / half day / before the close) - tables refreshed only")
    else:
        prev = obs[obs.date < day].sort_values(["date", "T"])
        pc = None
        if len(prev):
            pd_, pcl = str(prev.date.iloc[-1]), float(prev.close.iloc[-1])
            if (pd.Timestamp(day) - pd.Timestamp(pd_)).days <= 5:          # previous session, not across a hole
                pc = pcl
        rows = day_obs(spy, day, pc)
        obs = pd.concat([obs, pd.DataFrame(rows)], ignore_index=True)
    obs = obs.sort_values(["date", "T"]).reset_index(drop=True)[OBS_COLS]
    obs.to_csv(d / "cond_obs.csv", index=False, float_format="%.6g")
    C = cells(obs)
    C.to_csv(d / "cond_stats.csv", index=False, float_format="%.4f")
    (d / "cond_stats.json").write_text(json.dumps(to_json(C, obs), separators=(",", ":")))
    log(f"compass_cond: {day} +{len(rows)} rows; {obs.date.nunique()} sessions, {len(C)} cells")
    return len(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compass conditional stats - display only, not a trading signal")
    ap.add_argument("--date", default=None, help="session date (default: today ET)")
    ap.add_argument("--push", action="store_true", help=f"record on the {CL.BRANCH} data branch")
    ap.add_argument("--state-dir", default=None, help="data-branch checkout (default data/compass/branch)")
    a = ap.parse_args(argv)
    day = a.date or str(pd.Timestamp.now(tz=NY).date())
    if pd.Timestamp(day).dayofweek >= 5:
        print(f"compass_cond: {day} is a weekend - nothing to do")
        return 0
    if a.push:
        wd = Path(a.state_dir) if a.state_dir else CL.WORK / "branch"
        if not CL.open_branch(wd):
            return 1
        n = update(wd, day)
        return 0 if CL.push(wd, f"compass cond stats {day} (+{n})") else 1
    update(Path(a.state_dir) if a.state_dir else CL.WORK / "local", day)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
