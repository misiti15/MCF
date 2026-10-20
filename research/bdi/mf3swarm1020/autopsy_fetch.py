"""Step 1a (autopsy): every live MF3-open-flowsell-rsi5hi / -FD trade (run 1) from Primary (origin/mcf-data) and Testing 1
(origin/mcf-data-testing) journals; read-only SIP 1-min bars (Alpaca market data) for those symbols + SPY/QQQ from
2026-08-20 to 2026-10-20; lab features rebuilt with the same pipeline as the frames (resample 5min -> setup_lab.build)
and joined at the decision bar (signal minute floored to 5 min = frame tod). Writes live_trades.csv (no secrets).
Usage: python autopsy_fetch.py <scratch>   (expects <scratch>/{p,t1}/journal.db). Educational only - not financial advice."""
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars  # noqa: E402
from mcf.data.bars import resample  # noqa: E402
from mcf.research.setup_lab import build  # noqa: E402

S = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
TZ = "America/New_York"
rows = []
for a in ("p", "t1"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select * from trades where run_id=1 and strategy like 'MF3-open-flowsell-rsi5hi%'", c)
    t["acct"] = a
    rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["st"] = pd.to_datetime(T.signal_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["dec"] = T.st.dt.floor("5min")
T["tod"] = T.dec.dt.hour * 100 + T.dec.dt.minute
syms = sorted(set(T.symbol) | {"SPY", "QQQ"})
bd = S / "bars"
bd.mkdir(exist_ok=True)
need = [x for x in syms if not (bd / f"{x}.parquet").exists()]
cl = _client()
a, b = datetime(2026, 8, 20, 13, tzinfo=timezone.utc), datetime(2026, 10, 20, 20, 30, tzinfo=timezone.utc)
for i in range(0, len(need), 50):
    for s, g in fetch_bars(need[i:i + 50], a, b, feed="sip", client=cl).items():
        g.to_parquet(bd / f"{s}.parquet")
print(len(syms), "symbols")
F = []
for s in syms:
    f = bd / f"{s}.parquet"
    if not f.exists():
        continue
    d1 = pd.read_parquet(f)
    x = build({s: resample(d1, "5min")}, log=lambda *_: None)
    if x is None or not len(x):
        continue
    x = x.reset_index(names="ts")
    dv = (d1.close * d1.volume).groupby(d1.index.date).sum()
    adv = dv.shift(1).rolling(20, min_periods=5).mean()
    x["adv20"] = x["date"].map(adv)
    F.append(x)
F = pd.concat(F, ignore_index=True)
F["date"] = F["date"].astype(str)
idx = F[F.symbol.isin(["SPY", "QQQ"])].pivot_table(index=["date", "tod"], columns="symbol", values="fromOpen").reset_index()
idx.columns = ["date", "tod", "qqq_fo", "spy_fo"] if list(idx.columns)[2] == "QQQ" else ["date", "tod", "spy_fo", "qqq_fo"]
keep = ["symbol", "date", "tod", "heat", "buyPressure", "rsi", "rsi5", "gap", "fromOpen", "vwapDistPct", "atrPct", "atr_d",
        "volumeRatio", "dist_hod_atr", "sma50_dist_pct", "sma20_slope_pct", "adv20", "close", "r_short_t1s1"]
T["date"] = T.date.astype(str)
M = T.merge(F[keep], on=["symbol", "date", "tod"], how="left").merge(idx, on=["date", "tod"], how="left")
# day type: SPY / QQQ open-to-close of the session
day = F[F.symbol.isin(["SPY", "QQQ"])].groupby(["symbol", "date"]).fromOpen.last().unstack(0)
M["spy_day"] = M.date.map(day["SPY"])
M["qqq_day"] = M.date.map(day["QQQ"])
M["Rps"] = (M.entry - M.stop).abs()
M["stop_atrd"] = M.Rps / M.atr_d
M["risk"] = M.Rps * M.shares
M["radj"] = np.where(M.risk > 0, M.pnl_adj / M.risk, 0.0)
M.drop(columns=["meta", "broker_order_id"]).to_csv(HERE / "live_trades.csv", index=False)
print(len(M), "trades;", int(M.heat.isna().sum()), "without a frame row")
