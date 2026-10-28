"""hf1027 step 1: every live (paper) trade since start in all 5 accounts (Primary p, Testing 1 t1, Testing 2 t2,
Graveyard gy, Setup Generator gen), run 1, from the journal.db on each mcf-data* state branch (read-only copy):
    for a/b in p/mcf-data t1/mcf-data-testing t2/mcf-data-testing2 gy/mcf-data-graveyard gen/mcf-data-gen:
        git show origin/<b>:journal.db > <scratch>/<a>/journal.db
Adds per trade: rc = pnl_adj / $ risk (costs in, as combined.py), R per share, stop width in bps, target in R,
cost components in R (entry slip = slip_bps x entry / R per share; stop extra = (pnl - pnl_adj)/risk), symbol-day
sequence per setup (1 = first trade of that setup in that symbol that day), lot number (open lots of the same
setup+symbol at entry), hour, exit reason, journal mfe_r / mae_r.
Writes <scratch>/all_trades.parquet.  Usage: python build.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); TZ = "America/New_York"
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    t = pd.read_sql("select * from trades where run_id=1 and exit is not null", sqlite3.connect(S / a / "journal.db"))
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["et"] = pd.to_datetime(T.exit_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["Rps"] = (T.entry - T.stop).abs(); T["risk"] = T.Rps * T.shares
T = T[T.risk > 0].copy()
T["rc"] = T.pnl_adj / T.risk
T["stop_bps"] = T.Rps / T.entry * 1e4
T["tgt_r"] = (T.target - T.entry).abs() / T.Rps
T["slip_r"] = T.slip_bps.fillna(0) * T.entry / 1e4 / T.Rps          # entry fill vs signal price, in R (+ = against us)
T["stopx_r"] = (T.pnl - T.pnl_adj) / T.risk                         # modeled stop-exit slippage, in R
T["cost_r"] = T.slip_r + T.stopx_r
T["gross_r"] = T.rc + T.cost_r                                       # P/L if filled at the signal price, no stop extra
T["win"] = T.pnl > 0
T = T.sort_values("nt").reset_index(drop=True)
T["seq"] = T.groupby(["acct", "strategy", "symbol", "date"]).cumcount() + 1
g = T.groupby(["acct", "strategy", "symbol", "date"])
T["lot_no"] = 1
for _, ix in g.groups.items():
    if len(ix) < 2: continue
    sub = T.loc[ix]
    T.loc[ix, "lot_no"] = [1 + int(((sub.nt < r.nt) & (sub.et > r.nt)).sum()) for r in sub.itertuples()]
T["hhmm"] = T.nt.dt.hour * 100 + T.nt.dt.minute
T["exit_reason"] = T.exit_reason.fillna("?")
T.drop(columns=["meta"]).to_parquet(S / "all_trades.parquet", index=False)
print(len(T), "trades", T.date.min(), T.date.max(), T.groupby("acct").size().to_dict())
