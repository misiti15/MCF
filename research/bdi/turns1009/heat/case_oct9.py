"""Heat (V0 port / V1 formula / V2 as-run) and components for AAPL, SPCX, CAT, TSLA on 2026-10-09, 5-minute bars.
(1) checks V2 against MarcoFlow's own /api/heat-tracker snapshot (taken 2026-10-11 = the Oct-9 close state);
(2) prints the 60 minutes around each owner-marked moment; (3) lists every |heat| >= 30 reading and every heat
extreme of the day (false alarms = readings away from the marked moments). Writes data/oct9_heat.csv.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from heat_lib import COMPONENTS, all_heats  # noqa: E402

MOMENTS = [("AAPL", "13:40", "long"), ("AAPL", "15:00", "short"), ("SPCX", "10:10", "short"),
           ("CAT", "10:10", "long"), ("TSLA", "10:50", "short")]


def bars5(df):
    df = df.set_index("timestamp").sort_index()
    out = []
    for d, g in df.groupby(df.index.date):
        r = g.resample("5min", origin="start_day").agg({"open": "first", "high": "max", "low": "min", "close": "last",
                                                        "volume": "sum"}).dropna(subset=["close"])
        out.append(r)
    return pd.concat(out)


def main():
    raw = pd.read_parquet(HERE / "data" / "oct9_1m.parquet")
    api = json.load(open(HERE / "data" / "api_heat_snapshot_20261011.json"))
    res = {}
    print("== V2 (as-run) at the Oct-9 close vs MarcoFlow /api/heat-tracker (Yahoo bars, same state) ==")
    for s, g in raw.groupby("symbol"):
        d5 = bars5(g)
        days = sorted(set(d5.index.date))
        h_full = all_heats(d5)
        h5 = all_heats(d5[d5.index.date >= days[-5]])        # Yahoo range=5d window, as MarcoFlow
        res[s] = (d5, h_full)
        if s not in api:
            continue
        last = h5.iloc[-1]
        a = api[s]["heatTracker"]
        comp = {k: (round(float(last[k + "_ar"]), 1), a["components"][k]) for k in COMPONENTS + ["candleHeat"]
                if k != "candleHeat"}
        comp["candlestickHeat"] = (float(last["candleHeat_ar"]), a["components"]["candlestickHeat"])
        print(f"{s}: MCF V2 {last.heat_v2:.0f} vs MarcoFlow {a['heat']} | rsi {last.rsi_ar:.1f} vs {a['indicators']['rsi']}"
              f" | " + ", ".join(f"{k[:-4] if k.endswith('Heat') else k} {x}/{y}" for k, (x, y) in comp.items()))
    rows = []
    for s, (d5, h) in res.items():
        day = h[h.index.date == pd.Timestamp("2026-10-09").date()].copy()
        day["symbol"] = s
        day["close"] = d5.loc[day.index, "close"]
        rows.append(day)
    allh = pd.concat(rows)
    allh.reset_index(names="bar_start").to_csv(HERE / "data" / "oct9_heat.csv", index=False)
    cols = ["close", "heat_v0", "heat_v1", "heat_v2", "volumeHeat", "rsiHeat", "momentumHeat", "priceActionHeat",
            "trendHeat", "macdHeat", "vwapHeat", "candleHeat", "candleHeat_ar", "volumeHeat_ar"]
    for s, hhmm, side in MOMENTS:
        day = allh[allh.symbol == s]
        t0 = pd.Timestamp(f"2026-10-09 {hhmm}", tz="America/New_York")
        w = day[(day.index >= t0 - pd.Timedelta(minutes=30)) & (day.index < t0 + pd.Timedelta(minutes=30))]
        print(f"\n== {s} {hhmm} ({side}); bar = 5-min bar START (decision at its close) ==")
        print(w[cols].round(1).to_string())
    print("\n== every |heat| >= 30 reading (MarcoFlow's record threshold) on Oct 9, 09:50-15:55 bar closes ==")
    for v in ("heat_v0", "heat_v2"):
        x = allh[(allh[v].abs() >= 30) & (allh.tod >= 950)]
        print(v, len(x), "readings;", x.groupby("symbol").size().to_dict())
        print(x[["symbol", "tod", "close", v]].to_string())
    for v in ("heat_v0", "heat_v2"):
        s = allh[allh.symbol != "SPY"]
        print(f"\nheat extremes per symbol ({v}): bar-close tod of the day's 3 highest and 3 lowest readings")
        for sym, g in s.groupby("symbol"):
            g = g[g.tod >= 950]
            print(sym, "max", list(zip(g.nlargest(3, v).tod, g.nlargest(3, v)[v].round(0))),
                  "min", list(zip(g.nsmallest(3, v).tod, g.nsmallest(3, v)[v].round(0))))


if __name__ == "__main__":
    main()
