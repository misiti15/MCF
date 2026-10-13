"""Build trades.csv for 2026-10-13 (all three accounts, real trades run 1) with lot order, retry flag, MFE/MAE on SIP bars.
Educational only - not financial advice."""
import sys, json, sqlite3, pandas as pd
S, OUT = sys.argv[1], sys.argv[2]
EXP = {"intraday_momentum", "orb20_a", "heat_fade_short", "heat_fade_long", "exhaustion_short"}
RESTART = pd.Timestamp("2026-10-13 10:04:50", tz="America/New_York")
bars = {}
def bar(s):
    if s not in bars:
        try:
            b = pd.read_parquet(f"{S}/bars/{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
        except Exception:
            b = None
        bars[s] = b
    return bars[s]
rows = []
for a in ("p", "t1", "t2"):
    c = sqlite3.connect(f"{S}/{a}/journal.db")
    t = pd.read_sql("select * from trades where date='2026-10-13' and run_id=1", c)
    sg = pd.read_sql("select broker_order_id, info, ts from signals where day='2026-10-13' and run_id=1 and status='submitted'", c)
    t = t.merge(sg, on="broker_order_id", how="left")
    t["retry"] = t["info"].fillna("").str.contains('"retry_after_release": true')
    for x, y in [("nt", "entry_time"), ("et", "exit_time")]:
        t[x] = pd.to_datetime(t[y], utc=True, format="mixed").dt.tz_convert("America/New_York")
    t["acct"] = a
    # lot number: same-symbol same-side lots already open at this lot's entry fill (journal times) + 1
    t["lot_no"] = [1 + int(((t.symbol == r.symbol) & (t.side == r.side) & (t.id != r.id) & (t.nt < r.nt) & (t.et > r.nt)).sum())
                   for r in t.itertuples()]
    t["sym_stacked"] = t.symbol.map(t.groupby("symbol").lot_no.max() > 1)
    t["after_restart"] = t.nt >= RESTART
    t["ex_primary"] = t.strategy.isin(EXP)
    t["risk"] = (t.entry - t.stop).abs() * t.shares
    mfe, mae = [], []
    for r in t.itertuples():
        b = bar(r.symbol)
        if b is None:
            mfe.append(None); mae.append(None); continue
        w = b[(b.index >= r.nt.floor("1min")) & (b.index <= r.et.floor("1min"))]
        R = abs(r.entry - r.stop)
        if w.empty or R <= 0:
            mfe.append(None); mae.append(None); continue
        hi, lo = w.high.max(), w.low.min()
        mfe.append((hi - r.entry) / R if r.side == 1 else (r.entry - lo) / R)
        mae.append((r.entry - lo) / R if r.side == 1 else (hi - r.entry) / R)
    t["mfe"], t["mae"] = mfe, mae
    rows.append(t.drop(columns=["info"]))
T = pd.concat(rows)
T["hour"] = T.nt.dt.strftime("%H")
T.to_csv(OUT, index=False)
print(T.groupby("acct").agg(n=("id", "size"), pnl=("pnl", "sum"), stacked=("lot_no", lambda x: (x > 1).sum()), retry=("retry", "sum")))
