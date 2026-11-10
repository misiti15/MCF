"""COMPASS-LEARN: read-only Alpaca market-data GET (mcf.replay.store._fetch_bars, as compass_live) of the 1-minute RTH
bars of the live compass days since 11-05 for SPY/QQQ/IWM/XL*/the 200 Hunch names. Usage: python fetch_live.py <scratch>.
Educational only - not financial advice."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mcf.replay import store  # noqa: E402
from mcf.report import compass_live as CL  # noqa: E402

S = Path(sys.argv[1]); S.mkdir(parents=True, exist_ok=True)
DAYS = ["2026-11-05", "2026-11-06", "2026-11-09"]
XL = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
syms = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + XL + CL.universe()))
out = []
for d in DAYS:
    df = store._fetch_bars(syms, f"{d}T13:00:00Z", f"{d}T21:30:00Z", "1Min")
    df["ts"] = df.ts.dt.tz_convert("America/New_York")
    m = df.ts.dt.hour * 60 + df.ts.dt.minute
    out.append(df[(m >= 570) & (m < 960)])
    print(d, len(df), df.symbol.nunique())
pd.concat(out).to_parquet(S / "live_bars.parquet")
