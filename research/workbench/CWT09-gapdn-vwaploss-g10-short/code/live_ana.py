"""Live trades (diagnosis only) joined to their signal-bar features and the replay of each copy.
Educational only - not financial advice."""
import pandas as pd, numpy as np
import wb
from variants import V
T = pd.read_parquet(wb.OUT + "live_trades.parquet"); T = T[T.exit_time.notna()].copy()
s, P = wb.load("replay")
raw = pd.read_parquet(wb.OUT + "sig_replay.parquet")
f = raw[(raw.gap <= -10)].drop_duplicates(["symbol", "date"])
T = T.merge(f, left_on=["symbol", "date"], right_on=["symbol", "date"], how="left", suffixes=("", "_s"))
T["below_open"] = T.fromOpen < 0; T["cab"] = T.cab >= 1; T["adv20M"] = T.adv20 >= 20e6
T["stopdist_atr"] = (T.fh - T.close) / T.atr_d
T["entry_hm"] = pd.to_datetime(T.entry_time, utc=True).dt.tz_convert("America/New_York").dt.strftime("%H:%M")
names = pd.read_parquet(wb.OUT + "univ_snaps.parquet").drop_duplicates("symbol", keep="last").set_index("symbol").name.astype(str)
T["etf"] = T.symbol.map(names).fillna("").str.contains(wb.ETF_RX, regex=True)
sp, day = wb._spy(P); T["spyday"] = T.date.map(day)
T = T.merge(sp, on=["date", "tod"], how="left")
rep = {}
for vn in ["parent", "C4 S4+S3", "C11 S4+S3+ADV20M", "S4 below day open", "S3 first-hour CLOSE above VWAP"]:
    cfg = wb.BASE if vn == "parent" else {**wb.BASE, **V[vn][0]}
    tr = wb.trades(s, P, cfg); rep[vn] = tr.set_index(["symbol", "date"]).r
for vn, r in rep.items():
    T["rep_" + vn.split()[0]] = [r.get((a, b), np.nan) for a, b in zip(T.symbol, T.date)]
pd.set_option("display.width", 300)
cols = ["acct", "date", "symbol", "entry_hm", "entry", "stop", "exit", "exit_reason", "R", "mfe_r", "mae_r", "gap", "fromOpen", "below_open", "cab", "adv20", "stopdist_atr", "etf", "spy50", "spyday"] + [c for c in T if c.startswith("rep_")]
T = T.sort_values("R")
print(T[cols].round(3).to_string())
T[cols].to_csv(wb.OUT + "live_join.csv", index=False)
for k in ["below_open", "cab", "adv20M", "etf"]:
    print(k, T.groupby(k).R.agg(["count", "mean", "sum"]).round(3).to_dict("index"))
print("dtype", T.assign(dt=np.where(T.spyday > 0.3, "up", np.where(T.spyday < -0.3, "down", "flat"))).groupby("dt").R.agg(["count", "mean"]).round(3).to_dict("index"))
print("exit", T.groupby("exit_reason").R.agg(["count", "mean", "sum"]).round(3).to_dict("index"))
print("MFE>=1R but R<0.5:", ((T.mfe_r >= 1) & (T.R < 0.5)).sum(), "of", len(T))
