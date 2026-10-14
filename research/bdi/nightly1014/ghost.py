"""T1 orders still 'submitted' in the journal for 2026-10-14 although status.json shows the broker held them until the
close. Re-priced: entry = entry_ref (order ref), exit = SIP close of the 15:55 bar (flatten), and whether the bracket
stop/target was crossed while the broker still held the shares (= legs not working). Educational only."""
import os, sys, sqlite3, pandas as pd
from datetime import datetime, timezone
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import fetch_bars
S = sys.argv[1]
c = sqlite3.connect(f"{S}/t1/journal.db")
o = pd.read_sql("select * from orders where created_at like '2026-10-14%' and status='submitted'", c)
rows = []
for r in o.itertuples():
    p = f"{S}/bars/{r.symbol}.parquet"
    if not os.path.exists(p):   # read-only SIP market data for symbols with no journaled trade
        fetch_bars([r.symbol], datetime(2026, 10, 14, 8, tzinfo=timezone.utc), datetime(2026, 10, 14, 21, tzinfo=timezone.utc), feed="sip")[r.symbol].to_parquet(p)
    b = pd.read_parquet(p)
    b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
    t0 = pd.Timestamp(r.created_at).tz_convert("America/New_York")
    w = b[(b.index >= t0.floor("1min")) & (b.index.strftime("%H:%M") <= "15:55")]
    ent = w.open.iloc[0]
    ex = w[w.index.strftime("%H:%M") == "15:55"].close.iloc[0]
    hi, lo = w.high.max(), w.low.min()
    crossed_stop = hi >= r.stop if r.side == -1 else lo <= r.stop
    crossed_tgt = lo <= r.target if r.side == -1 else hi >= r.target
    rows.append(dict(symbol=r.symbol, strategy=r.strategy, side=r.side, qty=r.qty, created=t0.strftime("%H:%M:%S"), entry_ref=r.entry_ref,
                     entry_bar_open=round(ent, 2), stop=round(r.stop, 2), target=round(r.target, 2), exit_1555=round(ex, 2),
                     stop_crossed=bool(crossed_stop), target_crossed=bool(crossed_tgt), pnl_flatten=round(r.side * (ex - ent) * r.qty, 2)))
d = pd.DataFrame(rows); pd.set_option("display.width", 250); print(d.to_string()); print("sum", d.pnl_flatten.sum().round(2))
d.to_csv("t1_unjournaled_lots.csv", index=False)
