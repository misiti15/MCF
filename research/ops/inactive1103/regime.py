"""Index regime per session 10-12..11-03 (SPY / QQQ % from the open, max / min inside the windows the index-gated quiet
setups use), to tell "regime-gated, rare by design" from "broken". SIP 1-minute bars via mcf.data.alpaca_data.

    python research/ops/inactive1103/regime.py [<scratch>]  -> research/ops/inactive1103/regime.csv
Educational only - not financial advice."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.data.alpaca_data import fetch_bars        # noqa: E402

WIN = {"0950-1130": ("09:50", "11:30"), "1000-1400": ("10:00", "14:00"), "1130-1400": ("11:30", "14:00"),
       "1300-1500": ("13:00", "15:00"), "1400-1500": ("14:00", "15:00")}
bars = fetch_bars(["SPY", "QQQ"], datetime(2026, 10, 12, 13), datetime(2026, 11, 3, 16, 10), feed="sip")
rows = []
for sym, df in bars.items():
    df = df.tz_convert("America/New_York") if df.index.tz is not None else df
    for d, g in df.groupby(df.index.date):
        o = g["open"].iloc[0]
        r = dict(symbol=sym, day=str(d), close_fo=round(100 * (g["close"].iloc[-1] / o - 1), 2))
        for k, (a, b) in WIN.items():
            w = g.between_time(a, b)
            if len(w):
                r[f"max_{k}"] = round(100 * (w["close"].max() / o - 1), 2)
                r[f"min_{k}"] = round(100 * (w["close"].min() / o - 1), 2)
        rows.append(r)
if len(sys.argv) > 1:   # keep the 1-minute closes for audit.py's per-window regime check
    pd.concat({k: v["close"].tz_convert("America/New_York") if v.index.tz is not None else v["close"]
               for k, v in bars.items()}, axis=1).to_pickle(Path(sys.argv[1]) / "idx_close.pkl")
out = pd.DataFrame(rows).sort_values(["symbol", "day"])
out.to_csv(Path(__file__).resolve().parent / "regime.csv", index=False)
print(out.to_string())
