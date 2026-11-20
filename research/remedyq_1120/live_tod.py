"""REMEDY-Q part 1, live: the trio's closed live trades (exact -FD names, every account journal, run 1, de-duplicated
setup|symbol|date|entry minute), R after costs on the LR8 basis (load: research/whatworks_1120/brake/load_trades.py with
the date bound 2026-11-20). Entry bar = signal minute floored to the 5-min decision bar close (the YAML window unit:
a cutoff C keeps bars with close HHMM <= C, exactly what window [950, C] does live).
Usage: python live_tod.py LIVE.parquet OUTDIR.  Educational only - not financial advice."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import CUTOFFS, SHORT, TRIO, st  # noqa: E402

t = pd.read_parquet(sys.argv[1])
out = Path(sys.argv[2])
t = t[t.strategy.isin(TRIO)].copy()
ts = pd.to_datetime(t.signal_time.fillna(t.entry_time).astype(str), utc=True, format="mixed").dt.tz_convert("America/New_York")
t["bar"] = ts.dt.hour * 100 + (ts.dt.minute // 5) * 5
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
t = t.drop_duplicates("k")
t["s"] = t.strategy.map(SHORT)
print("live trio trades", len(t), t.date.min(), t.date.max(), t.groupby(["s", "account"]).size().to_dict())

B = [(0, 1030, "09:50-10:30"), (1030, 1200, "10:35-12:00"), (1200, 1300, "12:05-13:00"), (1300, 1400, "13:05-14:00"),
     (1400, 1600, "14:05-15:00")]
rows = []
for scope, g in (("all accounts", t), ("primary", t[t.account == "primary"]), ("non-primary", t[t.account != "primary"])):
    for s in ["L3", "RW3", "RW5", "pooled"]:
        x = g if s == "pooled" else g[g.s == s]
        for lo, hi, lab in B:
            rows.append(dict(scope=scope, setup=s, bucket=lab, **st(x[(x.bar > lo) & (x.bar <= hi)])))
        rows.append(dict(scope=scope, setup=s, bucket="<=13:00", **st(x[x.bar <= 1300])))
        rows.append(dict(scope=scope, setup=s, bucket=">13:00", **st(x[x.bar > 1300])))
bk = pd.DataFrame(rows)
bk.to_csv(out / "live_buckets.csv", index=False)

rows = []
for scope, g in (("all accounts", t), ("primary", t[t.account == "primary"]), ("non-primary", t[t.account != "primary"])):
    for s in ["L3", "RW3", "RW5", "pooled"]:
        x = g if s == "pooled" else g[g.s == s]
        base = st(x)
        for c in CUTOFFS:
            k = x[x.bar <= c]
            z = st(k)
            rows.append(dict(scope=scope, setup=s, cutoff=c, **z, kept_pct=round(100 * len(k) / max(len(x), 1), 1),
                             r_lost=round(base["tot"] - z["tot"], 2), d_avg=round(z["avg"] - base["avg"], 4)))
sw = pd.DataFrame(rows)
sw.to_csv(out / "live_cutoff_sweep.csv", index=False)
pd.set_option("display.width", 250)
print(bk[bk.scope != "non-primary"].to_string(index=False))
print(sw[(sw.scope == "all accounts")].to_string(index=False))
print(sw[(sw.scope == "primary")].to_string(index=False))
