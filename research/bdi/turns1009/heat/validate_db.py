"""Time handling of MarcoFlow's heat: match recorded live SignalObservation rows (data/marcoflow.sqlite) to V2 (as-run)
heat recomputed on SIP 5-minute bars, at several assumed data lags, for the 60 lab-universe symbols with the most live
rows. Prints agreement (|heat diff| <= 3, RSI corr) by lag. Educational only - not financial advice."""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from heat_lib import all_heats  # noqa: E402

LOCKED = ("2024-11-01", "2025-02-28")


def bars5(sym, start="2026-05-01"):
    d = pd.read_parquet(ROOT / "data" / "cache_hist" / "1Min" / f"{sym}.parquet")
    d = d[d.index >= pd.Timestamp(start, tz="America/New_York")]
    m = d.index.hour * 60 + d.index.minute
    d = d[(m >= 570) & (m < 960)]
    out = [g.resample("5min", origin="start_day").agg({"open": "first", "high": "max", "low": "min", "close": "last",
                                                         "volume": "sum"}).dropna(subset=["close"])
           for _, g in d.groupby(d.index.date)]
    return pd.concat(out)


if __name__ == "__main__":
    lab = set((ROOT / "research" / "lab_symbols.txt").read_text().split())
    c = sqlite3.connect(ROOT / "data" / "marcoflow.sqlite")
    o = pd.read_sql("select observedAt, symbol, heat, rsi, momentum, volumeComp, candlestick, trendComp from SignalObservation "
                    "where source='live' and observedAt >= '2026-06-01'", c)
    o = o[o.symbol.isin(lab)]
    top = o.symbol.value_counts().head(60).index
    o = o[o.symbol.isin(top)].copy()
    o["t"] = pd.to_datetime(o.observedAt, format="ISO8601").dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    res = []
    for s in top:
        h = all_heats(bars5(s))
        h["end"] = h.index + pd.Timedelta(minutes=5)
        oo = o[o.symbol == s].sort_values("t")
        for lag in (0, 5, 10, 15, 20, 25, 30):
            m = pd.merge_asof(oo.assign(k=oo.t - pd.Timedelta(minutes=lag)), h[["end", "heat_v2", "heat_v0", "rsi_ar",
                              "momentumHeat_ar", "candleHeat_ar"]], left_on="k", right_on="end", direction="backward",
                              tolerance=pd.Timedelta(minutes=5))
            m["lag"] = lag
            res.append(m)
    r = pd.concat(res).dropna(subset=["heat_v2"])
    g = r.groupby("lag")
    print("n rows", len(o), "symbols", len(top))
    print(pd.DataFrame({"n": g.size(),
                        "heat_|d|<=3": g.apply(lambda x: (abs(x.heat - x.heat_v2) <= 3).mean()),
                        "sign_agree_v2": g.apply(lambda x: (np.sign(x.heat) == np.sign(x.heat_v2)).mean()),
                        "sign_agree_v0": g.apply(lambda x: (np.sign(x.heat) == np.sign(x.heat_v0)).mean()),
                        "corr_heat_v2": g.apply(lambda x: x.heat.corr(x.heat_v2)),
                        "corr_rsi": g.apply(lambda x: x.rsi.corr(x.rsi_ar)),
                        "corr_mom": g.apply(lambda x: x.momentum.corr(x.momentumHeat_ar)),
                        "candle_eq": g.apply(lambda x: (x.candlestick == x.candleHeat_ar).mean())}).round(3).to_string())
