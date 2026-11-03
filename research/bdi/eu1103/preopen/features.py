"""eu1103/preopen: point-in-time pre-open features per symbol-day (PLAN.md features 1-14), two-year lab and live.
Everything is known by 09:30 ET (pre-market bars end 09:29:59, prior-day daily bars) except o5_* (the 09:30-09:35 bar,
known at 09:35). Rolling statistics use prior sessions only (shift(1)).
    python features.py <scratch> hist   -> <scratch>/feat_hist.parquet   (TRAIN + VALID dates only)
    python features.py <scratch> live   -> <scratch>/feat_live.parquet   (2026-10-06..11-02)
Educational only - not financial advice."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S, MODE = Path(sys.argv[1]), sys.argv[2]
SECT = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]
PM_MIN_DVOL = 50e3        # a name counts in breadth / dispersion only with >= $50k pre-market $ volume (fixed)


def daily_frame():
    if MODE == "hist":
        d = pd.read_parquet(S / "hist_daily_raw.parquet")     # raw, to match the raw pre-market bars
    else:
        d = pd.read_parquet(S / "live_daily.parquet")
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol")
    d["prev_close"] = g.close.shift(1)
    d["prev_high"] = g.high.shift(1)
    d["prev_low"] = g.low.shift(1)
    # the locked block is absent from lib.daily(): the session after the hole has no usable prior day
    hole = (pd.to_datetime(d.date) - pd.to_datetime(g.date.shift(1))).dt.days > 7
    d.loc[hole, ["prev_close", "prev_high", "prev_low"]] = np.nan
    tr = np.maximum(d.high - d.low, np.maximum((d.high - d.prev_close).abs(), (d.low - d.prev_close).abs()))
    d["atr_p"] = tr.groupby(d.symbol).transform(lambda x: x.shift(1).rolling(14, min_periods=5).mean())
    d["dv"] = d.close * d.volume
    d["adv20_p"] = d.dv.groupby(d.symbol).transform(lambda x: x.shift(1).rolling(20, min_periods=5).mean())
    d["pcl"] = ((d.prev_close - d.prev_low) / (d.prev_high - d.prev_low)).where(d.prev_high > d.prev_low)
    d["ret"] = d.close / d.prev_close - 1
    return d


def pm_frame(dates):
    fs = sorted((S / "pm").glob(f"{MODE}_*.parquet"))
    pm = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    pm["symbol"] = pm["symbol"].astype(str)
    return pm


def sector_map(d):
    """Sector SPDR with the highest daily-return correlation; TRAIN dates (hist) or 2026-08-03..10-05 (live)."""
    if MODE == "hist":
        s = d.date
        w = d[((s >= "2024-10-01") & (s <= "2024-10-31")) | ((s >= "2025-03-01") & (s <= "2025-12-31"))]
    else:
        w = d[d.date <= "2026-10-05"]
    r = w.pivot_table(index="date", columns="symbol", values="ret")
    secs = [x for x in SECT if x in r.columns]
    c = r.corrwith  # noqa
    cm = pd.DataFrame({x: r.corrwith(r[x]) for x in secs})
    best = cm.idxmax(axis=1)
    best[cm.max(axis=1) < 0.3] = np.nan
    best[best.index.isin(secs)] = np.nan
    return best


def main():
    d = daily_frame()
    pm = pm_frame(None)
    x = d.merge(pm, on=["symbol", "date"], how="left")
    x["pm_dvol"] = x.pm_dvol.fillna(0.0)
    x = x.sort_values(["symbol", "date"]).reset_index(drop=True)
    med = x.groupby("symbol").pm_dvol.transform(lambda v: v.shift(1).rolling(20, min_periods=10).median())
    x["pm_rvol"] = np.log1p(x.pm_dvol) - np.log1p(med)
    x["pm_share"] = x.pm_dvol / x.adv20_p
    x["pm_gap"] = (x.pm_last / x.prev_close - 1).where(x.pm_dvol >= PM_MIN_DVOL / 10)
    x["pm_gap_atr"] = (x.pm_gap.abs() / (x.atr_p / x.prev_close))
    x["pm_gap_atrs"] = x.pm_gap / (x.atr_p / x.prev_close)          # signed, side applied later
    x["pm_range_atr"] = ((x.pm_hi - x.pm_lo) / x.atr_p).where(x.pm_dvol > 0)
    # news
    nf = sorted((S / "news").glob(f"{MODE}_*.parquet"))
    if nf:
        nw = pd.concat([pd.read_parquet(f) for f in nf], ignore_index=True)
        nw["symbol"] = nw["symbol"].astype(str)
        x = x.merge(nw, on=["symbol", "date"], how="left")
        have = set(nw.date)
        x["news_n"] = np.where(x.date.isin(have), np.log1p(x.news_n.fillna(0)), np.nan)
    else:
        x["news_n"] = np.nan
    # opening 5-minute bar
    if MODE == "hist":
        o = pd.read_parquet(S / "o5_hist.parquet")
    else:
        o = pd.read_parquet(S / "live_o5.parquet")
        o["o5_dvol"] = o.o5_vol * o.o5_vw
    o["symbol"] = o["symbol"].astype(str)
    x = x.merge(o[["symbol", "date", "o5_open", "o5_close", "o5_dvol"]], on=["symbol", "date"], how="left")
    x["o5_rvol"] = x.o5_dvol / x.adv20_p
    x["o5_ret_atrs"] = (x.o5_close / x.o5_open - 1) / (x.atr_p / x.prev_close)
    # market level
    liq = x[(x.pm_dvol >= PM_MIN_DVOL) & x.pm_gap.notna()]
    mk = liq.groupby("date").agg(pm_breadth=("pm_gap", lambda v: (v > 0).mean() - 0.5),
                                 pm_disp=("pm_gap", lambda v: v.clip(-0.2, 0.2).std() * 100))
    for e in ["SPY", "QQQ"] + SECT:
        mk[e + "_pm"] = (x[x.symbol == e].set_index("date").pm_last / x[x.symbol == e].set_index("date").prev_close - 1) * 100
    mk["qqq_spy_pm"] = mk.QQQ_pm - mk.SPY_pm
    x = x.join(mk, on="date")
    sec = sector_map(d)
    x["sector"] = x.symbol.map(sec)
    x["sec_pm"] = np.nan
    for e in SECT:
        m = x.sector == e
        x.loc[m, "sec_pm"] = x.loc[m, e + "_pm"]
    keep = ["symbol", "date", "pm_rvol", "pm_share", "pm_gap_atr", "pm_gap_atrs", "pm_range_atr", "pcl", "news_n",
            "o5_rvol", "o5_ret_atrs", "SPY_pm", "qqq_spy_pm", "pm_breadth", "pm_disp", "sec_pm", "sector", "pm_dvol",
            "adv20_p", "atr_p", "prev_close"]
    x = x[keep]
    if MODE == "hist":
        s = x.date
        ok = ((s >= "2024-10-01") & (s <= "2024-10-31")) | ((s >= "2025-03-01") & (s <= "2025-12-31")) | \
             ((s >= "2026-01-01") & (s <= "2026-03-31")) | ((s >= "2026-07-01") & (s <= "2026-09-15"))
        x = x[ok]
    else:
        x = x[(x.date >= "2026-10-06") & (x.date <= "2026-11-02")]
    assert not ((x.date >= "2024-11-01") & (x.date <= "2025-02-28")).any()
    x.to_parquet(S / f"feat_{MODE}.parquet", index=False)
    print(MODE, x.shape, x.describe().T[["count", "mean", "50%"]].to_string())


if __name__ == "__main__":
    main()
