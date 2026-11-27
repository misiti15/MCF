"""B1 on live trades: max entries of one setup within any 5-minute window, per account-day; and per account-day
max entries of the whole account in 5 min. Educational only - not financial advice."""
import pandas as pd, numpy as np
t = pd.read_parquet("../capfit/all_trades.parquet")
t["et"] = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
t["day"] = t.date
rows = []
for (a, d, s), g in t.groupby(["account", "day", "strategy"]):
    e = np.sort(g.et.values.astype("datetime64[s]").astype(np.int64))
    j = np.searchsorted(e, e + 300, side="left")
    mx = int((j - np.arange(len(e))).max())
    k = int((j - np.arange(len(e))).argmax())
    rows.append(dict(account=a, date=d, setup=s, n=len(e), max5=mx, at=pd.Timestamp(e[k], unit="s", tz="UTC").tz_convert("America/New_York").strftime("%H:%M"),
                     R=g.r.sum(), R_burst=g[(g.et.values.astype("datetime64[s]").astype(np.int64) >= e[k]) & (g.et.values.astype("datetime64[s]").astype(np.int64) < e[k] + 300)].r.sum()))
S = pd.DataFrame(rows)
S.to_csv("live_burst.csv", index=False)
print("setup-days", len(S), "account-days", S.groupby(["account", "date"]).ngroups)
for x in (6, 8, 10, 12, 15, 20):
    f = S[S.max5 >= x]
    print(f">= {x} lots/5min: setup-days {len(f)}, account-days {f.groupby(['account','date']).ngroups}, R of burst lots {f.R_burst.sum():.1f}, R_burst<0 share {(f.R_burst<0).mean():.2f}")
print(S.sort_values("max5", ascending=False).head(25).to_string(index=False))
print(S[(S.account == "primary")].sort_values("max5", ascending=False).head(12).to_string(index=False))
