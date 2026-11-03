"""eu1103/open (1): live latency, spread and slippage by time of day, from the five live journals (run_id 1).
signal ts (signals.ts / trades.signal_time) vs the 5-min bar close it acted on; entry_time - signal_time;
spread_bps and slip_bps by entry minute bucket. Educational only - not financial advice.
    python latency.py <journal dir>"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

J = Path(sys.argv[1])
ACC = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard", "mcf-data-gen"]


def et(s):
    return pd.to_datetime(s, utc=True, format="mixed").dt.tz_convert("America/New_York")


rows, sigs = [], []
for a in ACC:
    c = sqlite3.connect(J / f"{a}.db")
    t = pd.read_sql("select symbol,strategy,side,date,signal_time,entry_time,entry,stop,r_multiple,slip_bps,meta "
                    "from trades where run_id=1", c)
    t["acct"] = a
    rows.append(t)
    s = pd.read_sql("select day,ts,symbol,strategy,status,reason,info from signals where run_id=1", c)
    s["acct"] = a
    sigs.append(s)
t = pd.concat(rows, ignore_index=True)
s = pd.concat(sigs, ignore_index=True)
t["sig"], t["ent"] = et(t.signal_time), et(t.entry_time)
t = t[t.sig.notna() & t.ent.notna()]
t["lat_fill"] = (t.ent - t.sig).dt.total_seconds()
mins = t.sig.dt.hour * 60 + t.sig.dt.minute + t.sig.dt.second / 60
t["sec_after_close"] = ((mins % 5) * 60).round(1)      # seconds after the last 5-min bar close
t["bar"] = ((mins // 5) * 5).astype(int)
t["hhmm"] = (t.bar // 60) * 100 + t.bar % 60


def meta(x, k):
    try:
        return json.loads(x).get(k)
    except Exception:
        return None


t["spread_bps"] = t.meta.map(lambda x: meta(x, "spread_bps")).astype(float)
t["risk"] = (t.entry - t.stop).abs()
t["spread_R"] = t.spread_bps / 1e4 * t.entry / t.risk
t["slip_R"] = t.slip_bps / 1e4 * t.entry / t.risk
t["bucket"] = pd.cut(t.hhmm, [0, 944, 949, 954, 959, 1014, 1029, 1059, 1159, 1459, 2400],
                     labels=["<09:45", "09:45-49", "09:50-54", "09:55-59", "10:00-14", "10:15-29", "10:30-59",
                             "11:00-11:59", "12:00-14:59", ">=15:00"])
print("Educational only - not financial advice.")
print(f"live trades run_id 1: {len(t)}  dates {t.date.min()}..{t.date.max()}  accounts {t.acct.nunique()}")
print("\nseconds from the 5-min bar close to the signal (signal_time mod 5 min), all trades:")
print(t.sec_after_close.describe(percentiles=[.1, .5, .9, .99]).round(1).to_string())
print("\nby account: median / p90 seconds after bar close, median / p90 signal->entry fill seconds")
print(t.groupby("acct").agg(n=("r_multiple", "size"), sig_med=("sec_after_close", "median"),
                            sig_p90=("sec_after_close", lambda x: x.quantile(.9)), fill_med=("lat_fill", "median"),
                            fill_p90=("lat_fill", lambda x: x.quantile(.9))).round(1).to_string())
print("\nby entry bucket (all accounts): n, median spread bps, spread as R, median slip bps, mean slip R, avg R")
g = t.groupby("bucket", observed=True).agg(n=("r_multiple", "size"), sec_after=("sec_after_close", "median"),
                                           fill_s=("lat_fill", "median"), spread_bps=("spread_bps", "median"),
                                           spread_R=("spread_R", "median"), slip_bps=("slip_bps", "median"),
                                           slip_R_mean=("slip_R", "mean"), avgR=("r_multiple", "mean"))
print(g.round(3).to_string())
w = t[t.slip_R.abs() <= 1]
print("\nslippage vs the signal price, |slip| <= 1R only (drops stop-entry / ref-price outliers):",
      f"kept {len(w)} of {len(t)}")
print(w.groupby("bucket", observed=True).agg(n=("slip_R", "size"), slip_R_mean=("slip_R", "mean"),
      slip_R_med=("slip_R", "median"), slip_bps_mean=("slip_bps", "mean")).round(4).to_string())
lab = t[~t.strategy.isin(["orb20_a", "intraday_momentum", "index_gap_fill", "gap_continuation"])]
print("\nlab-type setups only (5-min bar-close market entries): seconds after the 5-min close by bucket")
print(lab.groupby("bucket", observed=True).sec_after_close.describe(percentiles=[.1, .5, .9]).round(0).to_string())
# signals: skip reasons by bucket
s["ts_et"] = et(s.ts)
sm = s.ts_et.dt.hour * 100 + s.ts_et.dt.minute
s["bucket"] = pd.cut(sm, [0, 944, 949, 954, 959, 1014, 1029, 1059, 1159, 1459, 2400],
                     labels=list(g.index.astype(str)) if len(g) == 10 else None)
s["reason_k"] = s.reason.fillna("").str.replace(r"[0-9.]+", "#", regex=True).str.slice(0, 40)
print("\nsignals by bucket and status:")
print(pd.crosstab(s.bucket, s.status).to_string())
sk = s[s.status == "skipped"]
print("\nskip share for 'spread' reasons by bucket:")
sp = sk.reason.fillna("").str.contains("spread")
print((sp.groupby(sk.bucket, observed=True).mean().round(3)).to_string())
print("\nearliest signal minutes seen (any status):", sorted(sm.dropna().astype(int).unique())[:8])
print("\nsetups with entries before 09:50:")
pre = t[t.hhmm < 950]
print(pre.groupby(["acct", "strategy"]).agg(n=("r_multiple", "size"), avgR=("r_multiple", "mean"),
                                            first=("hhmm", "min")).sort_values("n", ascending=False).head(15).round(3).to_string())
t.drop(columns=["meta"]).to_parquet(J / "live_trades.parquet")
