"""Restated lots (journal rows that did not exist in the 10-14 EOD journal, dated before 10-15): booked exit vs the SIP 1-min bars.
Checks whether the bracket stop/target was crossed between the entry fill and the booked exit (then the broker would normally
have closed the lot earlier, at a different price than the booked flatten). Read-only SIP data. Educational only."""
import sys, sqlite3, os, pandas as pd
from datetime import datetime, timezone
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import fetch_bars
S = sys.argv[1]
rows = []
for a in ("t1", "t2"):
    n = pd.read_sql("select * from trades where run_id=1", sqlite3.connect(f"{S}/{a}/journal.db"))
    o = pd.read_sql("select broker_order_id from trades where run_id=1", sqlite3.connect(f"{S}/{a}/journal_1014.db"))
    new = n[~n.broker_order_id.isin(o.broker_order_id) & (n.date < "2026-10-15")]
    for r in new.itertuples():
        p = f"{S}/bars_{r.date}/{r.symbol}.parquet"
        if not os.path.exists(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            y, m, d = map(int, r.date.split("-"))
            fetch_bars([r.symbol], datetime(y, m, d, 13, tzinfo=timezone.utc), datetime(y, m, d, 21, tzinfo=timezone.utc), feed="sip")[r.symbol].to_parquet(p)
        b = pd.read_parquet(p); b.index = pd.to_datetime(b.index, utc=True)
        t0, t1 = pd.Timestamp(r.entry_time).floor("1min"), pd.Timestamp(r.exit_time).floor("1min")
        w = b[(b.index > t0) & (b.index < t1)]          # bars strictly after the entry minute and before the exit minute
        hit_stop = bool((w.low <= r.stop).any() if r.side == 1 else (w.high >= r.stop).any())
        hit_tgt = bool((w.high >= r.target).any() if r.side == 1 else (w.low <= r.target).any())
        first = None
        if hit_stop or hit_tgt:
            s = w[(w.low <= r.stop) | (w.high >= r.target)] if r.side == 1 else w[(w.high >= r.stop) | (w.low <= r.target)]
            first = s.index[0].tz_convert("America/New_York").strftime("%H:%M")
            x = s.iloc[0]
            stop_first = (x.low <= r.stop) if r.side == 1 else (x.high >= r.stop)
            alt = (r.stop if stop_first else r.target)
        else:
            alt = r.exit
        rows.append(dict(acct=a, date=r.date, symbol=r.symbol, strategy=r.strategy, side=r.side, qty=r.shares, entry=round(r.entry, 3),
                         stop=round(r.stop, 3), target=round(r.target, 3), booked_exit=round(r.exit, 3), booked_pnl=round(r.pnl, 2),
                         stop_crossed=hit_stop, target_crossed=hit_tgt, first_cross=first,
                         bracket_pnl=round(r.side * (alt - r.entry) * r.shares, 2)))
d = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(d.to_string())
print(d.groupby(["acct", "date"]).agg(n=("qty", "size"), booked=("booked_pnl", "sum"), bracket=("bracket_pnl", "sum"),
                                      crossed=("first_cross", lambda x: x.notna().sum())).round(2))
d.to_csv("restated_lots.csv", index=False)
