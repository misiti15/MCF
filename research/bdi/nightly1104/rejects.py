"""Graveyard buying-power rejects 2026-11-04: count, time span, setups, what-if (SIP 1-min, entry at ref price, stop /
target / 15:50 close, before costs). Usage: python rejects.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-n1104")
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; D = "2026-11-04"; TZ = "America/New_York"
c = sqlite3.connect(S / "gy" / "journal.db")
r = pd.read_sql("select ts, symbol, strategy, side, ref_price, stop, target from signals where day=? and run_id=1 and status='rejected'", c, params=(D,))
need = sorted(x for x in set(r.symbol) if not (S / "bars" / f"{x}.parquet").exists())
if need:
    from mcf.data.alpaca_data import _client, fetch_bars
    for s, g in fetch_bars(need, datetime(2026, 11, 4, 14, 25, tzinfo=timezone.utc), datetime(2026, 11, 4, 21, 5, tzinfo=timezone.utc), feed="sip", client=_client()).items():
        g.to_parquet(S / "bars" / f"{s}.parquet")
def wi(x):
    f = S / "bars" / f"{x.symbol}.parquet"
    if not f.exists(): return np.nan
    b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    w = b[(b.index >= pd.to_datetime(x.ts, utc=True).tz_convert(TZ).floor("1min") + pd.Timedelta(minutes=1)) & (b.index <= pd.Timestamp(f"{D} 15:50", tz=TZ))]
    R = abs(x.ref_price - x.stop)
    if w.empty or not R: return np.nan
    for y in w.itertuples():
        if (x.side == 1 and y.low <= x.stop) or (x.side == -1 and y.high >= x.stop): return -1.0
        if x.target == x.target and x.target and ((x.side == 1 and y.high >= x.target) or (x.side == -1 and y.low <= x.target)): return abs(x.target - x.ref_price) / R
    return (w.close.iloc[-1] - x.ref_price) / R * x.side
r["wi"] = [wi(x) for x in r.itertuples()]
txt = (f"{len(r)} rejects {r.ts.min()[11:19]}..{r.ts.max()[11:19]}; what-if sum {r.wi.sum():+.1f}R avg {r.wi.mean():+.3f} (priced {r.wi.notna().sum()})\n"
       + r.groupby("strategy").wi.agg(["size", "sum"]).round(2).sort_values("size", ascending=False).head(8).to_string())
open(OUT / "rejects_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
