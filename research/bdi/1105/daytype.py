"""QDAY report (owner, through 11-17): live R per account and per setup split by SPY day type (open-to-close > +0.25% up,
< -0.25% down, else quiet) and by SPY vs its open at 10:00 (09:59 close), all live sessions in the journals (run 1, R =
pnl_adj / $ risk, costs in). SPY from data/cache_hist/1Min/SPY.parquet (to 11-04) + <scratch>/bars/SPY.parquet (11-05).
Usage: python daytype.py <scratch-with-journals>     Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); TZ = "America/New_York"; HERE = Path(__file__).resolve().parent
b = pd.read_parquet("/home/user/MCF/data/cache_hist/1Min/SPY.parquet"); b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
b = b[b.index >= pd.Timestamp("2026-09-01", tz=TZ)]
b5 = pd.read_parquet(S / "bars" / "SPY.parquet"); b5.index = pd.to_datetime(b5.index, utc=True).tz_convert(TZ); b5 = b5.between_time("09:30", "15:59")
b = pd.concat([b[b.index < b5.index.min()], b5[b.columns.intersection(b5.columns)]]); d = b.index.strftime("%Y-%m-%d"); m = b.index.hour * 60 + b.index.minute
g = b.groupby(d); o = g.open.first(); c = g.close.last(); c959 = b[m < 600].groupby(d[m < 600]).close.last()
oc = (c / o - 1) * 100; f10 = (c959 / o - 1) * 100
DT = pd.DataFrame({"spy_oc": oc.round(2), "spy_fo10": f10.round(2),
                   "dtype": np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")),
                   "s10": np.where(f10 >= 0, "above", "below")})
NM = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2", "gy": "Graveyard", "gen": "Generator", "ex1": "Explore 1", "ll": "Live Lab"}
rows = []
for a in NM:
    t = pd.read_sql("select date, strategy, side, entry, stop, shares, pnl_adj from trades where run_id=1", sqlite3.connect(S / a / "journal.db"))
    t["R"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares).replace(0, np.nan); t = t.dropna(subset=["R"]).join(DT, on="date"); t["acct"] = a
    rows.append(t)
T = pd.concat(rows)
print("SPY day types in the live window:", DT.loc[sorted(T.date.unique())].dtype.value_counts().to_dict(), "| 2026-11-05:", DT.loc["2026-11-05"].to_dict())
for col in ("dtype", "s10"):
    x = T.groupby(["acct", col]).agg(days=("date", "nunique"), n=("R", "size"), avgR=("R", "mean"), usd=("pnl_adj", "sum")).round(3)
    print(f"\n== by {col} (all live sessions)\n" + x.to_string())
# setups positive on up AND down days (>= 10 trades each), all accounts, live
s = T.groupby(["acct", "strategy", "dtype"]).R.agg(["size", "mean"]).unstack("dtype")
ok = s[(s[("size", "up")] >= 10) & (s[("size", "down")] >= 10) & (s[("mean", "up")] > 0) & (s[("mean", "down")] > 0)]
print(f"\n== live setups positive on BOTH up and down days (>= 10 trades each): {len(ok)}")
print(ok.round(3).to_string() if len(ok) else "  none")
q = s[(s[("size", "quiet")] >= 10)].sort_values(("mean", "quiet"), ascending=False).head(8)
print("\n== best live setups on quiet days (>= 10 quiet-day trades)\n" + q.round(3).to_string())
T.groupby(["acct", "dtype", "s10"]).agg(n=("R", "size"), avgR=("R", "mean")).round(4).to_csv(HERE / "daytype_live.csv")
print("\nEducational only - not financial advice.")
