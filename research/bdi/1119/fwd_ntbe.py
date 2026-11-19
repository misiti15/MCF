"""swing1119-L16 NTBE journal-only check on live lots (all 10 accounts): each lot with a fixed target re-walked on 1-min SIP
bars with the BEREPLAY walk() (fixed vs be at k = 0.8 x target / stop distance), from the minute after the fill, to the lot's
own exit minute or 15:55; R in live $-risk units, BE exit charged 1c + 1bp + 2c extra. Delta = NTBE - fixed walk.
Usage: python fwd_ntbe.py <scratch> <day>. Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/guild/1109/bereplay")
from bereplay import walk  # noqa: E402
S, D = Path(sys.argv[1]), sys.argv[2]; TZ = "America/New_York"
NM = dict(p="Primary", od="On Deck", ta="Testing A", tb="Testing B", tc="Testing C", td="Testing D", te="Testing E", tf="Testing F", gen="Gen", gy="Graveyard")
tot = []
for a, nm in NM.items():
    t = pd.read_sql("select symbol, side, entry_time, entry, stop, target from trades where date=? and run_id=1 and target is not null",
                    sqlite3.connect(S / a / "journal.db"), params=(D,))
    d = []
    for r in t.itertuples():
        f = S / "bars" / f"{r.symbol}.parquet"
        if not f.exists() or not r.target: continue
        b = pd.read_parquet(f); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
        nt = pd.Timestamp(r.entry_time).tz_convert(TZ).floor("min")
        b = b[(b.index > nt) & (b.index.hour * 60 + b.index.minute < 955)]
        if b.empty: continue
        e, s = float(r.entry), int(r.side); Dd = abs(e - r.stop); U = abs(r.target - e)
        if Dd <= 0 or U <= 0: continue
        o, h, l, c = (b[x].to_numpy(float) for x in ("open", "high", "low", "close"))
        out = []
        for mode, k in (("fixed", None), ("be", 0.8 * U / Dd)):
            px, kd = walk(o, h, l, c, e, s, Dd, U, mode, k)
            out.append((s * (px - e) - (0.01 + px * 1e-4 + 0.02 if kd == 1 else 0)) / Dd)
        d.append(out[1] - out[0])
    d = np.array(d)
    tot.append((nm, len(d), int((d != 0).sum()), float(d.sum()) if len(d) else 0.0, int((d > 0).sum()), int((d < 0).sum())))
for r in tot: print(f"{r[0]}: lots {r[1]}, changed {r[2]} (better {r[4]} / worse {r[5]}), delta {r[3]:+.2f}R")
print("all accounts delta %+.2fR on %d changed lots (in-sample day 0)" % (sum(r[3] for r in tot), sum(r[2] for r in tot)))
