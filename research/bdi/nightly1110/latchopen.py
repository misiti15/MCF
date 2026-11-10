"""Nightly 2026-11-10: R of lots already open when a Primary setup hit its -2R latch (latch = exit time of the trade that
took the setup's realized R (costs in) to <= -2R). What-if: close every open lot of that setup at the latch minute's
SIP 1-min close (before extra costs; the lot's booked entry costs kept). Also Testing 1/2 + Graveyard (descriptive).
Usage: python latchopen.py <scratch>   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
T = pd.read_csv(OUT / "trades.csv"); T["nt"] = pd.to_datetime(T.nt, utc=True).dt.tz_convert(TZ); T["et"] = pd.to_datetime(T.et, utc=True).dt.tz_convert(TZ); T["r"] = T.radj
def px(sym, t):
    f = S / "bars" / f"{sym}.parquet"
    if not f.exists(): return np.nan
    b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    b = b[b.index <= t - pd.Timedelta(minutes=1)]
    return float(b.close.iloc[-1]) if len(b) else np.nan
out = []; P = out.append; rows = []
for acct in ("p", "t1", "t2", "gy"):
    A = T[T.acct == acct]
    for s, g in A.groupby("strategy"):
        g = g.sort_values("et"); cum = g.r.cumsum()
        hit = g[cum <= -2]
        if hit.empty: continue
        lt = hit.et.iloc[0]
        op = g[(g.nt <= lt) & (g.et > lt)]
        if op.empty: rows.append(dict(acct=acct, setup=s, latch=lt.strftime("%H:%M"), n_open=0, R_actual=0.0, R_close_at_latch=0.0)); continue
        wi = []
        for _, r in op.iterrows():
            p = px(r.symbol, lt); risk = abs(r.entry - r.stop)
            wi.append(np.nan if np.isnan(p) or risk == 0 else r.side * (p - r.entry) / risk)
        rows.append(dict(acct=acct, setup=s, latch=lt.strftime("%H:%M"), n_open=len(op), R_actual=round(op.r.sum(), 2),
                         R_close_at_latch=round(np.nansum(wi), 2), day_R=round(g.r.sum(), 2), R_at_latch=round(cum[cum <= -2].iloc[0], 2)))
D = pd.DataFrame(rows); D["delta"] = D.R_close_at_latch - D.R_actual
P(D.to_string()); P(D.groupby("acct")[["n_open", "R_actual", "R_close_at_latch", "delta"]].sum().round(2).to_string())
P(f"setups improved {int((D.delta > 0).sum())}, worse {int((D.delta < 0).sum())}, same {int((D.delta == 0).sum())}")
txt = "\n".join(out); (OUT / "latchopen_out.txt").write_text(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
