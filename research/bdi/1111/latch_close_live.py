"""LATCH-CLOSE forward shadow (lead swing1111-L13, research/bdi/1111/LATCH_CLOSE_PLAN.md): per account and setup, find the
live -2R latch (cumulative journal r_multiple of exited run-1 trades <= -2.0, the runner's trigger basis) and close the
setup's lots still open at the close of the next 5-min bar after the latching exit's bar (1-min SIP close of that bar's
last minute) minus 1c + 1 bp; delta = that - actual (pnl_adj / $ risk, costs in). Journal only; no trading path.
Appends rows to research/bdi/swings/forward.csv (hyp swing1111-L13, idempotent by date) and the day to hypotheses.jsonl.
Usage: python latch_close_live.py <scratch> <day> [--in-sample]   (<scratch>/<acct>/journal.db, 1-min bars in
<scratch>/cov/days/<day>/bars.parquet or <scratch>/bars/<SYM>.parquet). Educational only - not financial advice."""
import json, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S, D = Path(sys.argv[1]), sys.argv[2]; INS = "--in-sample" in sys.argv; TZ = "America/New_York"
SW = Path(__file__).resolve().parents[1] / "swings"; HYP = "swing1111-L13"
ACC = {"p": "Primary", "od": "On Deck", "ta": "Testing A", "tb": "Testing B", "tc": "Testing C", "td": "Testing D", "te": "Testing E", "tf": "Testing F", "gy": "Graveyard", "gen": "Gen"}   # 2026-11-12: scratch codes for the 10 accounts
bf = S / "cov" / "days" / D / "bars.parquet"
B1 = pd.read_parquet(bf) if bf.exists() else pd.DataFrame(columns=["symbol", "close"])
if len(B1): B1.index = pd.to_datetime(B1.index, utc=True).tz_convert(TZ)
def px_at(sym, t):
    g = B1[B1.symbol == sym].close if len(B1) else pd.Series(dtype=float)
    if g.empty:
        f = S / "bars" / f"{sym}.parquet"
        if not f.exists(): return np.nan
        x = pd.read_parquet(f); x.index = pd.to_datetime(x.index, utc=True).tz_convert(TZ); g = x.close
    g = g[g.index <= t - pd.Timedelta(minutes=1)]
    return float(g.iloc[-1]) if len(g) else np.nan
rows, lines = [], []
for a, nm in ACC.items():
    f = S / a / "journal.db"
    if not f.exists(): continue
    t = pd.read_sql("select * from trades where date=? and run_id=1 and exit_time is not null", sqlite3.connect(f), params=(D,))
    if t.empty: continue
    for c in ("entry_time", "exit_time"): t[c] = pd.to_datetime(t[c], utc=True, format="mixed").dt.tz_convert(TZ)
    t["risk"] = (t.entry - t.stop).abs() * t.shares; t["radj"] = t.pnl_adj / t.risk
    tot, nb, nw, nl = 0.0, 0, 0, 0
    for su, g in t.groupby("strategy"):
        g = g.sort_values("exit_time"); cr = g.r_multiple.cumsum()
        hit = g[cr <= -2.0 + 1e-9]
        if hit.empty: continue
        lt = hit.exit_time.iloc[0]; cb = lt.floor("5min") + pd.Timedelta(minutes=10)     # close of the next 5-min bar
        o = t[(t.strategy == su) & (t.entry_time < lt) & (t.exit_time > cb)].copy()
        if o.empty: continue
        sd = (o.entry - o.stop).abs()
        p_ = np.array([px_at(s, cb) for s in o.symbol])
        o["alt"] = o.side * (p_ - o.entry) / sd - (0.01 + 1e-4 * p_) / sd
        d = float((o.alt - o.radj).sum())
        if np.isnan(d): continue
        tot += d; nl += len(o); nb += d > 0; nw += d < 0
        rows.append(dict(date=D, hyp=HYP, n=len(o), avgR=round(d / len(o), 4), note=f"{a} {su} latch {lt:%H:%M} close {cb:%H:%M} delta {d:+.2f}R", in_sample=INS))
    lines.append(f"{nm}: {nl} lots on latched setups, delta {tot:+.2f}R, setups better {nb} / worse {nw}")
    print(lines[-1])
F = SW / "forward.csv"; fw = pd.read_csv(F)
fw = fw[~((fw.date == D) & (fw.hyp == HYP))]; fw = pd.concat([fw, pd.DataFrame(rows)], ignore_index=True); fw.to_csv(F, index=False)
H = [json.loads(l) for l in open(SW / "hypotheses.jsonl")]
for h in H:
    if h["id"] == HYP:
        days = [x for x in h["forward"]["days"] if x["date"] != D]
        days.append(dict(date=D, in_sample=INS, delta=round(sum(r["avgR"] * r["n"] for r in rows), 2), summary=lines))
        h["forward"]["days"] = days; h["forward"]["through"] = D
        h["forward"]["sessions"] = sum(1 for x in days if not x["in_sample"])
(SW / "hypotheses.jsonl").write_text("".join(json.dumps(h) + "\n" for h in H))
