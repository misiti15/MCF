"""What the ST-P latch (setup daily loss limit, -2R) blocked on 2026-10-29 in Primary, priced on SIP 1-min bars:
entry at the next bar open after the signal, the signal's stop / target, stop first inside a bar, flatten 15:55,
costs 1c + 1bp per side (+2c on a stop). Also the cumulative R per setup through the day (when the latch tripped).
Usage: python stp_whatif.py <scratch-pr29>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); D = "2026-10-29"; TZ = "America/New_York"
c = sqlite3.connect(S / "p" / "journal.db")
s = pd.read_sql("select ts,symbol,strategy,side,ref_price,stop,target,reason from signals where day=? and run_id=1 and reason='setup daily loss limit'", c, params=(D,))
s["ts"] = pd.to_datetime(s.ts, utc=True, format="mixed").dt.tz_convert(TZ)
out = []
for r in s.itertuples():
    f = S / "bars" / f"{r.symbol}.parquet"
    if not f.exists():
        out.append(dict(symbol=r.symbol, setup=r.strategy[:12], note="no bars")); continue
    b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    b = b[(b.index > r.ts.floor("1min")) & (b.index <= r.ts.normalize() + pd.Timedelta(hours=15, minutes=55))]
    if b.empty:
        out.append(dict(symbol=r.symbol, setup=r.strategy[:12], note="no later bars")); continue
    e = b.open.iloc[0]; R = abs(e - r.stop); sd = r.side; px, why = b.close.iloc[-1], "flatten/open"
    for t, x in b.iterrows():
        if (sd == -1 and x.high >= r.stop) or (sd == 1 and x.low <= r.stop):
            px, why = r.stop, "stop"; break
        if (sd == -1 and x.low <= r.target) or (sd == 1 and x.high >= r.target):
            px, why = r.target, "target"; break
    cost = 0.01 + e * 1e-4 + (0.0 if why == "target" else 0.01 + px * 1e-4) + (0.02 if why == "stop" else 0.0)
    out.append(dict(time=r.ts.strftime("%H:%M"), symbol=r.symbol, setup=r.strategy[:12], entry=round(e, 3), exit=round(px, 3), how=why,
                    R=round((sd * (px - e) - cost) / R, 2), last_bar=b.index[-1].strftime("%H:%M")))
o = pd.DataFrame(out); print(o.to_string(index=False)); print("sum R", round(o.R.sum(), 2) if "R" in o else None)
