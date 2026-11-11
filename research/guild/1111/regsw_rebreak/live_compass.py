"""L3LEASH: the live W60 compass (mcf.report.compass_live.compute, production code) + SPY from-open for every live session
of L3-gap-slope-fromopen-FD (Testing 1 10-13..10-29, Primary 10-21..11-10). 1-minute SIP bars by the read-only market-data
GET that compass_live itself uses. Usage: python live_compass.py <scratch>  -> <scratch>/live_compass.parquet,
<scratch>/live_spy.parquet. Educational only - not financial advice."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mcf.report import compass_live as CL  # noqa: E402

S = Path(sys.argv[1]); NY = "America/New_York"
DAYS = [str(d.date()) for d in pd.bdate_range("2026-10-13", "2026-11-10")]
names = CL.universe(); syms = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + names))
rows, spy = [], []
for d in DAYS:
    now = min(pd.Timestamp.now(tz=NY), pd.Timestamp(f"{d} 16:00", tz=NY))
    bars = CL.fetch(d, syms, now, log=lambda *a: None)
    if "SPY" not in bars:
        print(d, "no bars"); continue
    r = CL.compute(bars, d, now, names)
    rows += r
    b = bars["SPY"].copy(); b["date"] = d; spy.append(b)
    print(d, len(r), len(bars), flush=True)
pd.DataFrame(rows).to_parquet(S / "live_compass.parquet")
pd.concat(spy).to_parquet(S / "live_spy.parquet")
