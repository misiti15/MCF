"""BDI 2026-11-12: what-if of Primary L3-gap-slope-fromopen-FD signals skipped by 'max positions for this setup'.
First cap-skip per symbol (refires repeat each poll), priced on SIP 1-min bars like nightly1112/forward.py whatif
(entry at ref price at the next minute, stop / target / 15:50 mark), gross; a cost haircut = today's L3 mean (gross R - adj R).
Usage: python l3cap.py <scratch with p/journal.db and bars/>. Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); D = "2026-11-12"; TZ = "America/New_York"
c = sqlite3.connect(S / "p" / "journal.db")
sg = pd.read_sql("select * from signals where day=? and run_id=1 and strategy like 'L3-gap-slope-fromopen%'", c, params=(D,))
tr = pd.read_sql("select * from trades where date=? and run_id=1 and strategy like 'L3-gap-slope-fromopen%'", c, params=(D,))
tr["R"] = tr.pnl_adj / ((tr.entry - tr.stop).abs() * tr.shares)
tr["Rg"] = tr.pnl / ((tr.entry - tr.stop).abs() * tr.shares) if "pnl" in tr else tr.R
cost = float((tr.Rg - tr.R).mean())
_bc = {}
def bars(s):
    f = S / "bars" / f"{s}.parquet"
    if not f.exists(): return None
    if s not in _bc:
        b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ); _bc[s] = b
    return _bc[s]
def whatif(r):
    b = bars(r.symbol)
    if b is None: return np.nan
    t0 = pd.to_datetime(r.ts, utc=True).tz_convert(TZ).floor("1min") + pd.Timedelta(minutes=1)
    w = b[(b.index >= t0) & (b.index <= pd.Timestamp(f"{D} 15:50", tz=TZ))]
    e, st, tg = r.ref_price, r.stop, r.target; R = abs(e - st)
    if w.empty or not R: return np.nan
    for x in w.itertuples():
        if r.side == 1:
            if x.low <= st: return -1.0
            if tg == tg and tg and x.high >= tg: return (tg - e) / R
        else:
            if x.high >= st: return -1.0
            if tg == tg and tg and x.low <= tg: return (e - tg) / R
    return (w.close.iloc[-1] - e) / R * r.side
cap = sg[sg.reason == "max positions for this setup"].sort_values("ts")
first = cap.drop_duplicates("symbol").copy()
first["traded_too"] = first.symbol.isin(set(tr.symbol))
first["wi"] = [whatif(r) for r in first.itertuples()]
first["hm"] = pd.to_datetime(first.ts, utc=True).dt.tz_convert(TZ).dt.strftime("%H:%M")
ok = first[first.wi.notna()]
print(f"L3 Primary: {len(tr)} trades {tr.R.sum():+.2f}R adj (gross {tr.Rg.sum():+.2f}R, mean cost {cost:.3f}R/trade)")
print(f"cap skips {len(cap)} over {cap.symbol.nunique()} symbols; first-skip per symbol priced {len(ok)}/{len(first)}")
for lab, g in [("all", ok), ("never traded", ok[~ok.traded_too]), ("also traded", ok[ok.traded_too])]:
    print(f"  {lab:13s} n {len(g):3d} gross {g.wi.sum():+7.2f}R avg {g.wi.mean():+.3f}  net(-cost) {g.wi.sum() - cost * len(g):+7.2f}R  win {(g.wi > 0).mean():.0%}")
print("  by hour (first skip):", ok.groupby(ok.hm.str[:2]).wi.agg(["size", "sum"]).round(2).to_dict("index"))
print("Upper bound: assumes buying power / sizing for every extra lot; one lot per symbol. Educational only - not financial advice.")
