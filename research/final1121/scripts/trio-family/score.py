"""Score trio-family siblings: python score.py trades_fit.parquet fit [cfg,...]   (half = fit | check | t2)
Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gd import B, W  # noqa: E402

ETB = pd.read_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/open-drive/etb_rate.parquet").rate
TOP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/top10w")
TRIO = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]


def filt(t, cf=0.15):
    t = t[t.entry >= 5.0]
    t = t[(t.side > 0) | t.symbol.map(ETB).fillna(0).ge(0.9)]
    return t[t.stop_cost_r <= cf]


def extra(t):
    if not len(t):
        return {}
    day = t.groupby("date").r.sum().sort_values(ascending=False)
    top2 = set(day.index[:2])
    d = {"avg_r_wo_top2": round(float(t.loc[~t.date.isin(top2), "r"].mean()), 4) if (~t.date.isin(top2)).any() else None,
         "pct_days_green": round(float((day > 0).mean()), 3), "days": int(day.size)}
    return d


def run(path, half, cfgs=None, spy=None, nses=None):
    T = pd.read_parquet(W / path)
    T = B.add_r(T)
    if half in ("fit", "check"):
        T = T[B.half(T.date) == half]
    if cfgs:
        T = T[T.cfg.isin(cfgs)]
    out = {}
    trio_raw = pd.read_parquet(TOP / ("trades_t1.parquet" if half != "t2" else "trades_t2.parquet"),
                               columns=["setup", "symbol", "date"])
    trio_raw = trio_raw[trio_raw.setup.isin(TRIO)]
    trio_sd = set(trio_raw.symbol + "|" + trio_raw.date.astype(str))
    bk = pd.read_parquet(TOP / "booked_trades.parquet")
    bk = bk[bk.setup.isin(TRIO) & (bk.test == ("T2" if half == "t2" else "T1"))]
    if half in ("fit", "check"):
        bk = bk[B.half(bk.date) == half]
    trio_bk_sd = set(bk.symbol + "|" + bk.date.astype(str))
    trio_day = bk.groupby("date").r.sum()
    for cfg, g in T.groupby("cfg"):
        real = g[g.grp == "real"]
        b = B.book(real.drop(columns=["cfg"]), B.TESTING_RULES, ETB)
        s = B.stats(b, nses, spy)
        s.update(extra(b))
        sd = b.symbol + "|" + b.date.astype(str)
        s["overlap_trio_raw_symday"] = round(float(sd.isin(trio_sd).mean()), 3) if len(b) else None
        s["overlap_trio_booked_symday"] = round(float(sd.isin(trio_bk_sd).mean()), 3) if len(b) else None
        # daily relation with the trio (booked, home book)
        dd = b.groupby("date").r.sum()
        j = pd.concat([dd.rename("s"), trio_day.rename("t")], axis=1).fillna(0.0)
        s["corr_daily_with_trio"] = round(float(j.s.corr(j.t)), 3) if len(j) > 5 else None
        red = j[j.t < 0]
        s["sum_r_on_trio_red_days"] = round(float(red.s.sum()), 2)
        s["sum_r_on_trio_green_days"] = round(float(j[j.t > 0].s.sum()), 2)
        s["trio_red_days"] = int(len(red))
        # nulls, unbooked per-trade on the same filters
        fr = filt(real)
        for ng in ("null_any", "null_post"):
            nu = filt(g[g.grp == ng])
            if len(nu) and len(fr):
                s[f"unbooked_real_avg"] = round(float(fr.r.mean()), 4)
                s[f"{ng}_avg"] = round(float(nu.r.mean()), 4)
                # day-clustered diff t: per-day mean difference
                a = fr.groupby("date").r.mean()
                c = nu.groupby("date").r.mean()
                k = pd.concat([a, c], axis=1, keys=["a", "c"]).dropna()
                dlt = k.a - k.c
                s[f"{ng}_diff_t_day"] = round(float(dlt.mean() / (dlt.std(ddof=1) / math.sqrt(len(dlt)))), 2) if len(dlt) > 3 else None
        out[cfg] = s
    return out


if __name__ == "__main__":
    path, half = sys.argv[1], sys.argv[2]
    cfgs = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    if half in ("fit", "check"):
        spy = B.spy_t1()
        days = pd.Series(spy.index)
        last = pd.read_parquet(W / path, columns=["date"]).date.max()
        days = days[days <= last]
        nses = int((B.half(days) == half).sum())
    else:
        spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
        spy2.index = spy2.index.astype(str)
        spy = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
        nses = int(len(spy))
    res = run(path, half, cfgs, spy, nses)
    Path(W / f"score_{half}_{Path(path).stem}.json").write_text(json.dumps(res, indent=1, default=float))
    keys = ["trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "avg_r_wo_top2", "best_day_share", "total_r_per_session",
            "t_day_clustered", "pct_days_green", "unbooked_real_avg", "null_any_avg", "null_any_diff_t_day", "null_post_avg",
            "null_post_diff_t_day", "overlap_trio_raw_symday", "overlap_trio_booked_symday", "corr_daily_with_trio",
            "sum_r_on_trio_red_days", "trio_red_days"]
    df = pd.DataFrame({c: {k: v.get(k) for k in keys} for c, v in res.items()}).T
    pd.set_option("display.width", 250)
    print("sessions", nses)
    print(df.to_string())
