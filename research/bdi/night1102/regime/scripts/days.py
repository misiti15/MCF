"""night1102/regime: session tags for the live window from SPY/QQQ/IWM/RSP 1-minute SIP bars.
EOD type (hindsight, regime1022 definition): Bull o2c >= +0.5%, Bear <= -0.5%, else Choppy if the high-low range is
>= its prior-20-session median, else Quiet. Simpler 3-way EOD: up (o2c >= +0.25%), down (<= -0.25%), quiet.
Point-in-time snapshots at 09:50 and 10:30 (bar closes at those minutes): SPY % from open, SPY vs its session VWAP,
QQQ % from open, breadth proxy = RSP (equal weight) minus SPY from open. Also a per-minute state frame for at-entry
tags. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def minute_state(scr: Path) -> pd.DataFrame:
    b = pd.read_parquet(scr / "idx_1min.parquet")
    out = []
    for (s, d), g in b.groupby(["symbol", "date"]):
        g = g.sort_index()
        o = g["open"].iloc[0]
        tp = (g["high"] + g["low"] + g["close"]) / 3
        vw = (tp * g["volume"]).cumsum() / g["volume"].cumsum()
        out.append(pd.DataFrame({"symbol": s, "date": d, "tod": g.index.hour * 100 + g.index.minute + 1,  # bar close
                                 "fo": (g["close"] / o - 1) * 100, "vw": (g["close"] / vw - 1) * 100}))
    m = pd.concat(out)
    w = m.pivot_table(index=["date", "tod"], columns="symbol", values=["fo", "vw"])
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.reset_index()
    w["tod"] = np.where(w["tod"] % 100 == 60, w["tod"] + 40, w["tod"])
    w["br"] = w["fo_RSP"] - w["fo_SPY"]
    return w


def day_table(scr: Path) -> pd.DataFrame:
    b = pd.read_parquet(scr / "idx_1min.parquet")
    s = b[b.symbol == "SPY"].groupby("date").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                                                 close=("close", "last"))
    s["o2c"] = (s["close"] / s["open"] - 1) * 100
    s["rng"] = (s["high"] - s["low"]) / s["open"] * 100
    s["med20"] = s["rng"].shift(1).rolling(20, min_periods=10).median()
    s["eod4"] = np.where(s.o2c >= 0.5, "Bull", np.where(s.o2c <= -0.5, "Bear",
                         np.where(s.rng >= s.med20, "Choppy", "Quiet")))
    s["eod3"] = np.where(s.o2c >= 0.25, "up", np.where(s.o2c <= -0.25, "down", "quiet"))
    w = minute_state(scr).set_index(["date", "tod"])
    for t in (950, 1000, 1030):
        x = w.xs(t, level="tod")
        for c in ("fo_SPY", "vw_SPY", "fo_QQQ", "br"):
            s[f"{c}@{t}"] = x[c]
    return s


if __name__ == "__main__":
    scr = Path(sys.argv[1])
    d = day_table(scr)
    d.to_parquet(scr / "days.parquet")
    minute_state(scr).to_parquet(scr / "minute.parquet")
    pd.set_option("display.width", 250)
    print(d[d.index >= pd.Timestamp("2026-10-06").date()].round(2).drop(columns=["open", "high", "low", "close"]).to_string())
