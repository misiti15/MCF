"""Nightly 2026-11-10: midday flip check (compass-learn standby signal 'SPY back across its open for 15 min after 12:00').
Finds the flip minute on SIP 1-min SPY, then per account: short entries after the flip (R costs in) and shorts open at the
flip (actual R vs closing them at the flip minute's close, before extra costs). Descriptive, one session.
Usage: python flip.py <scratch>   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
spy = pd.read_parquet(S / "bars" / "SPY.parquet"); spy.index = pd.to_datetime(spy.index, utc=True).tz_convert(TZ)
o = spy.open.iloc[0]; fo = spy.close / o - 1
pm = fo[fo.index >= pd.Timestamp("2026-11-10 12:00", tz=TZ)]
side0 = np.sign(fo[fo.index < pd.Timestamp("2026-11-10 12:00", tz=TZ)].iloc[-1])
run = (np.sign(pm) == -side0).astype(int); grp = (run.diff() != 0).cumsum(); cnt = run.groupby(grp).cumsum()
flip = cnt[cnt >= 15].index[0] if (cnt >= 15).any() else None
out = [f"SPY side at 12:00 {side0:+.0f}; flip (15 min across its open after 12:00) confirmed at {flip}; SPY low {fo.min():+.3%} at {fo.idxmin()}"]
T = pd.read_csv(OUT / "trades.csv"); T["nt"] = pd.to_datetime(T.nt, utc=True).dt.tz_convert(TZ); T["et"] = pd.to_datetime(T.et, utc=True).dt.tz_convert(TZ)
def px(sym, t):
    f = S / "bars" / f"{sym}.parquet"
    if not f.exists(): return np.nan
    b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ); b = b[b.index <= t - pd.Timedelta(minutes=1)]
    return float(b.close.iloc[-1]) if len(b) else np.nan
if flip is not None:
    for a, A in T.groupby("acct"):
        sh = A[A.side == side0]  # lots on the 12:00 side (shorts today)
        aft = sh[sh.nt >= flip]; op = sh[(sh.nt < flip) & (sh.et > flip)]
        wi = [r.side * (px(r.symbol, flip) - r.entry) / abs(r.entry - r.stop) for _, r in op.iterrows() if abs(r.entry - r.stop) > 0]
        out.append(f"{a}: 12:00-side entries after flip {len(aft)} sum {aft.radj.sum():+.2f}R avg {aft.radj.mean():+.3f}; open at flip {len(op)} actual {op.radj.sum():+.2f}R vs close at flip {np.nansum(wi):+.2f}R")
txt = "\n".join(out); (OUT / "flip_out.txt").write_text(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
