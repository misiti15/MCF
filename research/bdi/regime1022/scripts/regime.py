"""regime1022: one hindsight market-condition label per session from SPY's regular session (PLAN.md):
Bull o2c >= +0.5%, Bear o2c <= -0.5%, Choppy |o2c| < 0.5% and range >= median range of the previous 20 sessions,
Quiet |o2c| < 0.5% and range below it. History from lab daily bars (locked block excluded by lib), live sessions
(after 2026-10-07) from read-only SIP bars (fetch_live_idx.py). Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from rc import SCR, lib, no_locked

LABELS = ["Bull", "Bear", "Choppy", "Quiet"]
DEFS = {
    "Bull": "SPY closed at least +0.5% above its open",
    "Bear": "SPY closed at least -0.5% below its open",
    "Choppy": "SPY open-to-close within +-0.5%, but the day's high-low range was at or above its 20-day median",
    "Quiet": "SPY open-to-close within +-0.5% and a high-low range below its 20-day median",
}


def label(o2c, rng, med, cut=0.5):
    return np.where(o2c >= cut, "Bull", np.where(o2c <= -cut, "Bear", np.where(rng >= med, "Choppy", "Quiet")))


def day_table(cut: float = 0.5) -> pd.DataFrame:
    d = lib.daily()
    spy = d[d["symbol"] == "SPY"][["date", "open", "high", "low", "close"]].copy()
    spy["date"] = pd.to_datetime(spy["date"]).dt.date
    live = pd.read_parquet(SCR / "idx_live_daily.parquet")
    live = live[live["symbol"] == "SPY"].drop(columns="symbol")
    live["date"] = pd.to_datetime(live["date"]).dt.date
    spy = pd.concat([spy, live[live["date"] > spy["date"].max()]]).sort_values("date").reset_index(drop=True)
    no_locked(spy["date"])
    spy["o2c"] = (spy["close"] / spy["open"] - 1) * 100
    spy["range"] = (spy["high"] - spy["low"]) / spy["open"] * 100
    spy["med20"] = spy["range"].shift(1).rolling(20, min_periods=10).median()
    spy["prev_c2c"] = spy["close"].pct_change() * 100
    gap = pd.to_datetime(spy["date"]).diff().dt.days > 5
    spy.loc[gap.to_numpy(), "prev_c2c"] = np.nan
    # prev_c2c on day d = close(d) / close(d-1): it includes day d itself (hindsight). The PRIOR session's return,
    # known at day d's open, is close(d-1) / close(d-2) = prev_c2c shifted by one session.
    # NB gates1021's spy_prev.parquet (scan.py) stored prev_c2c un-shifted, i.e. today's close-to-close: lookahead.
    spy["spy_c2c_today"] = spy["prev_c2c"]
    spy["spy_prev"] = spy["prev_c2c"].shift(1)
    spy["regime"] = label(spy["o2c"].to_numpy(), spy["range"].to_numpy(), spy["med20"].to_numpy(), cut)
    spy.loc[spy["med20"].isna() & (spy["o2c"].abs() < cut), "regime"] = None
    try:
        reg = lib.regimes()["med_o2c"]
        reg.index = pd.to_datetime(reg.index).date
        spy["uni_med_o2c"] = spy["date"].map(reg)
    except Exception:  # noqa: BLE001
        spy["uni_med_o2c"] = np.nan
    return spy.set_index("date")


if __name__ == "__main__":
    t = day_table()
    print(t.tail(14)[["o2c", "range", "med20", "regime"]].round(2).to_string())
    t["split"] = np.where(pd.Index(t.index) <= pd.Timestamp("2025-12-31").date(), "train", "valid")
    print(t.groupby(["split", "regime"]).size().unstack())
    for c in (0.3, 0.75):
        tt = day_table(c)
        print(c, tt["regime"].value_counts().to_dict())
