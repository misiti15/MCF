"""Testing 1's final state push failed: its journal holds 325 of the 457 trades the job log reports (457 trades,
P/L -$482.70, win 48.1%, exp -0.07R). The 132 missing trades are submitted signals with no trade row (mostly lots still
open at the last push, 15:50-15:54). ESTIMATE ONLY: replay each on SIP 1-min bars from the signal's reference price
(stop-first inside a bar, gaps through the stop fill at the open, target at the limit, flatten at 15:55 bar open),
production costs as giveback1019 (market exit 1 bps + $0.01/sh, stops + $0.02/sh, targets 0). Breakeven/trailing
management is not modelled. Writes t1_missing.csv. Usage: python t1_missing.py <scratch>
Educational only - not financial advice."""
import sys, sqlite3, json
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; D = "2026-10-19"; TZ = "America/New_York"
c = sqlite3.connect(S / "t1" / "journal.db")
s = pd.read_sql("select * from signals where day=? and run_id=1 and status='submitted'", c, params=(D,))
t = pd.read_sql("select broker_order_id from trades where date=? and run_id=1", c, params=(D,))
m = s[~s.broker_order_id.isin(t.broker_order_id)].copy()
m["st"] = pd.to_datetime(m.ts, utc=True, format="mixed").dt.tz_convert(TZ)
FL = pd.Timestamp(f"{D} 15:55", tz=TZ)
rows = []
for r in m.itertuples():
    b = pd.read_parquet(S / "bars" / f"{r.symbol}.parquet") if (S / "bars" / f"{r.symbol}.parquet").exists() else None
    if b is None:
        continue
    b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    sd, E, stop, tgt, q = int(r.side), float(r.ref_price), float(r.stop), (None if pd.isna(r.target) else float(r.target)), float(r.qty)
    R = abs(E - stop)
    w = b[b.index >= r.st.floor("1min") + pd.Timedelta(minutes=1)]
    ex, why, xt, mfe, mae = None, None, None, 0.0, 0.0
    for tt, o, h, l in zip(w.index, w.open.values, w.high.values, w.low.values):
        if tt >= FL:
            ex, why, xt = o, "flatten", tt; break
        fav, adv = (h, l) if sd == 1 else (l, h)
        mae = max(mae, sd * (E - adv) / R)
        if (adv - stop) * sd <= 0:
            ex, why, xt = (o if (o - stop) * sd < 0 else stop), "stop", tt; break
        if tgt is not None and (fav - tgt) * sd >= 0:
            ex, why, xt = tgt, "target", tt; mfe = max(mfe, sd * (fav - E) / R); break
        mfe = max(mfe, sd * (fav - E) / R)
    if ex is None:
        continue
    g = sd * (ex - E) * q
    cost = 0.0 if why == "target" else q * (0.01 + ex * 1e-4) + (q * 0.02 if why == "stop" else 0.0)
    rows.append(dict(symbol=r.symbol, strategy=r.strategy, side=sd, signal=r.st.strftime("%H:%M"), entry=E, stop=stop, target=tgt, qty=q,
                     exit=round(ex, 4), exit_reason=why, exit_t=xt.strftime("%H:%M"), pnl=round(g, 2), pnl_adj=round(g - cost, 2),
                     radj=round((g - cost) / (R * q), 3), mfe=round(mfe, 2), mae=round(mae, 2)))
X = pd.DataFrame(rows); X.to_csv(OUT / "t1_missing.csv", index=False)
print(len(m), "missing,", len(X), "replayed; exits", X.exit_reason.value_counts().to_dict(), "| exit times", X.exit_t.value_counts().head(5).to_dict())
print("est pnl", round(X.pnl.sum(), 2), "est adj", round(X.pnl_adj.sum(), 2), "| job log implies", round(-482.70 - (-140.90), 2))
print("est wins", int((X.pnl > 0).sum()), "| job log implies", round(0.481 * 457) - 160)
pd.set_option("display.width", 200)
print(X.groupby("strategy").agg(n=("symbol", "size"), win=("pnl", lambda x: round((x > 0).mean() * 100)), R=("radj", "mean"), pnl=("pnl", "sum"), adj=("pnl_adj", "sum")).round(2).sort_values("adj").to_string())
