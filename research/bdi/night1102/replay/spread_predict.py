"""Offline check (no replay): how well can a replay know live's spread-skip decision for a signal it has no recorded
quote for? Live signals 10-27..11-02 with a journaled quote (all five accounts). Truth = live spread skip
(spread_bps > 30 or spread > 25% of stop). Predictors: (a) the replay's current model, a deterministic draw from the
symbol's journaled spreads (store.build_spreads pool, crc32 by symbol/day/minute); (b) the nearest recorded quote of the
same symbol the same day >= 2 minutes away (<= 30 min), any account; (c) same, <= 5 min. Educational only."""
import json, sqlite3, sys, zlib
from pathlib import Path
import pandas as pd

J = Path(sys.argv[1]); SP = json.loads(Path(sys.argv[2]).read_text())
BR = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard", "mcf-data-gen"]
rows = []
for br in BR:
    c = sqlite3.connect(str(J / f"{br}.db"))
    for ts, day, sym, ref, stop, info in c.execute("SELECT ts, day, symbol, ref_price, stop, info FROM signals WHERE run_id=1 "
                                                  "AND day>='2026-10-27' AND info LIKE '%spread_bps%'"):
        i = json.loads(info)
        t = pd.Timestamp(ts).tz_convert("America/New_York")
        k = int((t - pd.Timestamp(f"{day} 09:30", tz="America/New_York")) // pd.Timedelta(minutes=1))
        rows.append(dict(br=br, day=day, sym=sym, k=k, ref=float(ref), risk=abs(float(ref) - float(stop)),
                         bps=float(i["spread_bps"])))
d = pd.DataFrame(rows)
skip = lambda bps, ref, risk: (bps > 30) | ((risk > 0) & (bps / 1e4 * ref / risk.where(risk > 0, 1) > 0.25))  # noqa
d["truth"] = skip(d.bps, d.ref, d.risk)
def draw(r):
    pool = SP.get(r.sym) or SP["_all"]
    return float(pool[zlib.crc32(f"{r.sym}|{r.day}|{r.k}".encode()) % len(pool)])
d["p_draw"] = d.apply(draw, axis=1)
q = d.groupby(["day", "sym"]).apply(lambda g: sorted(set(zip(g.k, g.bps))), include_groups=False).to_dict()
def near(r, lim):
    c = [(abs(k - r.k), b) for k, b in q[(r.day, r.sym)] if 2 <= abs(k - r.k) <= lim]
    return min(c)[1] if c else None
for lim in (30, 5):
    d[f"p_near{lim}"] = [near(r, lim) for r in d.itertuples()]
print(f"live quoted signals {len(d)}, live spread skips {int(d.truth.sum())} ({d.truth.mean():.1%})")
for col in ("p_draw", "p_near30", "p_near5"):
    m = d[col].notna()
    pred = skip(d.loc[m, col].astype(float), d.ref[m], d.risk[m])
    t = d.truth[m]
    agree = (pred == t).mean()
    # draw on the same subset for a fair comparison
    pd_ = skip(d.p_draw[m], d.ref[m], d.risk[m])
    print(f"{col:9s} coverage {m.mean():6.1%}  agree {agree:6.1%}  (draw on same rows {(pd_ == t).mean():6.1%})  "
          f"recall of live skips {(pred & t).sum() / max(1, t.sum()):6.1%}  false skips {(pred & ~t).sum()}")
print("Educational only - not financial advice.")
