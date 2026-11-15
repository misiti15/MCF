"""Checklist #42 (early-close sessions): detect half days from the data (SPY volume of the 13:30-15:55 ET bars < 0.2 x its 09:30-12:55 volume; normal days ~0.9,
half days ~0.05; a fixed share of the median missed 2025-11-28's busy after-hours)
and write a copy of a bar cache without those sessions. Prints the dates found. Educational only - not financial advice.
    python -I halfday_clean.py <bars.csv.gz> <out.csv.gz>"""
import sys, pandas as pd
m = pd.read_csv(sys.argv[1]); t = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["_d"] = t.dt.strftime("%Y-%m-%d"); hm = t.dt.hour * 100 + t.dt.minute
spy = m.symbol == "SPY"; allday = m[spy]._d.unique()
aft = m[spy & (hm >= 1330) & (hm <= 1555)].groupby("_d").v.sum().reindex(allday).fillna(0)
mor = m[spy & (hm >= 930) & (hm < 1300)].groupby("_d").v.sum().reindex(allday).fillna(0)
half = sorted(aft[aft < 0.2 * mor].index)
print("half days found:", half)
m[~m._d.isin(half)].drop(columns="_d").to_csv(sys.argv[2], index=False)
