"""Does Alpaca's historical SIP NBBO at the live decision second reproduce the quote the live runner journaled?
Sample of live quoted signals 10-27..11-02 (all accounts, seed 7). Read-only market-data GET (/v2/stocks/{sym}/quotes,
latest quote at or before the journaled signal time: sort=desc, limit=1). Educational only - not financial advice."""
import json, sqlite3, sys
from pathlib import Path
import pandas as pd
from mcf.replay.store import _get, _session

J = Path(sys.argv[1]); N = int(sys.argv[2]); OUT = Path(sys.argv[3])
BR = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard", "mcf-data-gen"]
rows = []
for br in BR:
    c = sqlite3.connect(str(J / f"{br}.db"))
    for ts, sym, ref, stop, info in c.execute("SELECT ts, symbol, ref_price, stop, info FROM signals WHERE run_id=1 AND "
                                              "day>='2026-10-27' AND info LIKE '%spread_bps%'"):
        i = json.loads(info)
        rows.append(dict(br=br, ts=ts, sym=sym, ref=float(ref), risk=abs(float(ref) - float(stop)), bid=i["bid"],
                         ask=i["ask"], bps=float(i["spread_bps"]), age=i.get("quote_age_s")))
d = pd.DataFrame(rows)
# one row per (symbol, second): accounts poll at the same second and see the same quote
d["sec"] = d.ts.str[:19]
d = d.drop_duplicates(["sym", "sec"]).sample(n=min(N, len(d)), random_state=7).reset_index(drop=True)
sess = _session()
out = []
for r in d.itertuples():
    t = pd.Timestamp(r.ts).tz_convert("UTC")
    for lag in (0.0, 3.0):     # at the journaled time, and 3 s later (fetch latency between quote and journal stamp)
        pass
    j = _get(sess, f"https://data.alpaca.markets/v2/stocks/{r.sym}/quotes",
             {"start": (t - pd.Timedelta(seconds=60)).isoformat(), "end": t.isoformat(), "feed": "sip",
              "sort": "desc", "limit": 1})
    q = (j.get("quotes") or [None])[0]
    out.append(dict(hbid=q["bp"] if q else None, hask=q["ap"] if q else None, ht=q["t"] if q else None))
d = pd.concat([d, pd.DataFrame(out)], axis=1)
d.to_csv(OUT, index=False)
m = d.hbid.notna() & (d.hbid > 0) & (d.hask >= d.hbid)
d = d[m].copy()
d["hbps"] = (d.hask - d.hbid) / ((d.hask + d.hbid) / 2) * 1e4
sk = lambda b, ref, risk: (b > 30) | ((risk > 0) & (b / 1e4 * ref / risk.where(risk > 0, 1) > 0.25))  # noqa
t, p = sk(d.bps, d.ref, d.risk), sk(d.hbps, d.ref, d.risk)
same = (abs(d.hbid - d.bid) < 1e-6) & (abs(d.hask - d.ask) < 1e-6)
print(f"sample {len(d)} quotes with history: identical bid+ask {same.mean():.1%}; |spread diff| median "
      f"{(d.hbps - d.bps).abs().median():.2f} bps, p90 {(d.hbps - d.bps).abs().quantile(.9):.2f}; "
      f"spread-skip decision agree {(t == p).mean():.1%} (live skips {int(t.sum())}, hist skips {int(p.sum())}, "
      f"both {int((t & p).sum())})")
print("Educational only - not financial advice.")
