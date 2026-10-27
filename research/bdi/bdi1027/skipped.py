"""BDI 2026-10-27: what the skipped (blocked) signals of each account would have done. Every run-1 signal with
status 'skipped' on 2026-10-27 is replayed as its own bracket on SIP 1-min bars (entry = signal ref price at the next
minute's open, stop / target as signalled, stop first inside a bar, 15:55 close). Cost per trade = the median cost in R
of that setup's real trades today (account median when the setup had none), so the numbers are after costs.
Missing bars are fetched read-only (Alpaca market data) into <scratch>/bars.
Usage: python skipped.py <scratch> ; writes skipped_1027.csv and prints per account x reason. Educational only - not financial advice."""
import sys, sqlite3, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
S = Path(sys.argv[1]); D = "2026-10-27"; TZ = "America/New_York"; HERE = Path(__file__).resolve().parent
PT = pd.read_csv(HERE / "per_trade_1027.csv")
cost_setup = PT.groupby(["acct", "setup"]).cost.median(); cost_acct = PT.groupby("acct").cost.median()
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    for ts, sym, st, side, ref, stop, tgt, reason in c.execute(
            "select ts,symbol,strategy,side,ref_price,stop,target,reason from signals where day=? and run_id=1 and status='skipped'", (D,)):
        rows.append(dict(acct=a, ts=ts, symbol=sym, setup=st, side=int(side), ref=ref, stop=stop, target=tgt,
                         reason=re.sub(r"[0-9.\-]+", "#", reason or "")[:40]))
X = pd.DataFrame(rows)
need = sorted(s for s in X.symbol.unique() if not (S / "bars" / f"{s}.parquet").exists())
if need:
    from mcf.data.alpaca_data import _client, fetch_bars
    cl = _client(); a0, b0 = datetime(2026, 10, 27, 13, tzinfo=timezone.utc), datetime(2026, 10, 27, 20, 30, tzinfo=timezone.utc)
    for i in range(0, len(need), 100):
        for s, g in fetch_bars(need[i:i + 100], a0, b0, feed="sip", client=cl).items():
            g.to_parquet(S / "bars" / f"{s}.parquet")
cache = {}
def bars(s):
    if s not in cache:
        f = S / "bars" / f"{s}.parquet"
        if not f.exists(): cache[s] = None
        else:
            b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ); cache[s] = b.between_time("09:30", "15:55")
    return cache[s]
out = []
for r in X.itertuples():
    b = bars(r.symbol)
    if b is None or not r.stop or r.ref is None: continue
    t0 = pd.Timestamp(r.ts, tz="UTC").tz_convert(TZ).floor("min")
    p = b[b.index > t0]
    if not len(p): continue
    px = float(p.open.iloc[0]); R = abs(float(r.ref) - float(r.stop))
    if R <= 0: continue
    stop = px - r.side * R; tgt = None if r.target is None or r.target != r.target else px + r.side * abs(float(r.target) - float(r.ref))
    res = None
    for h, l, cl_ in zip(p.high.values, p.low.values, p.close.values):
        if (l <= stop) if r.side == 1 else (h >= stop): res = -1.0; break
        if tgt is not None and ((h >= tgt) if r.side == 1 else (l <= tgt)): res = (tgt - px) * r.side / R; break
    if res is None: res = (p.close.values[-1] - px) * r.side / R
    cost = cost_setup.get((r.acct, r.setup), cost_acct.get(r.acct, 0.1))
    out.append(dict(acct=r.acct, setup=r.setup, symbol=r.symbol, t=f"{t0:%H:%M}", side=r.side, reason=r.reason, R=res - cost))
O = pd.DataFrame(out); O.to_csv(HERE / "skipped_1027.csv", index=False)
print(f"skipped signals {len(X)}, replayed {len(O)}")
g = O.groupby(["acct", "reason"]).R.agg(["size", "mean", "sum"]).round(3)
print(g.to_string())
print("\n== by account x setup, reasons 'max positions' / 'daily loss limit' / 'lot cap' (sum R)")
k = O[O.reason.str.contains("max positions|daily loss|lot cap|twin")]
print(k.groupby(["acct", "reason", "setup"]).R.agg(["size", "mean", "sum"]).round(2).sort_values("sum").to_string())
print("\nEducational only - not financial advice.")
