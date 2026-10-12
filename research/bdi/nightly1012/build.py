"""Build per-trade table with MFE/MAE from 1-min SIP bars. Educational only."""
import sys, sqlite3, json
from pathlib import Path
import pandas as pd, numpy as np
S = Path(sys.argv[1])
rows = []
for a in ("p", "t1", "t2"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select * from trades where date='2026-10-12' and run_id=1", c)
    t["acct"] = a
    rows.append(t)
T = pd.concat(rows, ignore_index=True)
for col in ("signal_time", "entry_time", "exit_time"):
    T[col] = pd.to_datetime(T[col].str.replace("T", " "), utc=True, format="mixed").dt.tz_convert("America/New_York")
T["lat_s"] = (T.entry_time - T.signal_time).dt.total_seconds()
T["hold_min"] = (T.exit_time - T.entry_time).dt.total_seconds() / 60
T["risk"] = (T.entry - T.stop).abs()
T["stop_wrong_side"] = T.side * (T.entry - T.stop) <= 0
T["tgt_wrong_side"] = T.target.notna() & (T.side * (T.target - T.entry) <= 0)
T["spread_bps"] = T.meta.str.extract(r'"spread_bps": ([0-9.]+)').astype(float)
T["structural"] = T.target.isna()
cache = {}
mfe, mae, tmfe, ok = [], [], [], []
for r in T.itertuples():
    if r.symbol not in cache:
        f = S / "bars" / f"{r.symbol}.parquet"
        cache[r.symbol] = pd.read_parquet(f) if f.exists() else None
    b = cache[r.symbol]
    if b is None or r.risk <= 0:
        mfe.append(np.nan); mae.append(np.nan); tmfe.append(np.nan); ok.append(False); continue
    e0 = r.entry_time.floor("min"); e1 = r.exit_time.floor("min")
    w = b[(b.index >= e0) & (b.index <= e1)]
    if w.empty:
        mfe.append(np.nan); mae.append(np.nan); tmfe.append(np.nan); ok.append(False); continue
    fav = (w.high - r.entry) if r.side == 1 else (r.entry - w.low)
    adv = (r.entry - w.low) if r.side == 1 else (w.high - r.entry)
    mfe.append(max(fav.max(), 0) / r.risk); mae.append(max(adv.max(), 0) / r.risk)
    tmfe.append((fav.idxmax() - r.entry_time).total_seconds() / 60); ok.append(True)
T["mfe"], T["mae"], T["t_mfe"], T["bars_ok"] = mfe, mae, tmfe, ok
T["giveback"] = T.mfe - T.r_multiple
T["win"] = T.pnl > 0
T["entry_hhmm"] = T.entry_time.dt.strftime("%H:%M")
T["bucket"] = T.entry_time.dt.floor("30min").dt.strftime("%H:%M")
T.drop(columns=["meta"]).to_csv(S / "trades_all.csv", index=False)
print(T.groupby("acct").agg(n=("pnl", "size"), pnl=("pnl", "sum"), bars=("bars_ok", "sum")))
