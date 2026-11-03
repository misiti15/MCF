"""Can historical SIP NBBO stand in for the quote live saw, for signals that have no recording (a NEW setup)?
Sample of live quoted signals 10-27..11-02 (all accounts; seed 11; one per symbol+second). For each, the quotes from
the poll start (journal ts) to +240 s (read-only GET /v2/stocks/{sym}/quotes). Spread-skip decision (> 30 bps or
> 25% of the stop) from the quote in force at: (a) the poll start, (b) poll start + the account's median
poll-start -> submit delay (Primary 28 s, T1 22, T2 56, Graveyard 42, Gen 80; journal 10-27..11-02), (c) the first
quote equal to the journaled bid/ask (oracle, upper bound). Truth = the decision from the journaled quote.
Educational only - not financial advice."""
import json, sqlite3, subprocess, sys, tempfile
from pathlib import Path
import pandas as pd
from mcf.replay.store import _get, _session

N = int(sys.argv[1]); OUT = Path(sys.argv[2])
DELAY = {"mcf-data": 28, "mcf-data-testing": 22, "mcf-data-testing2": 56, "mcf-data-graveyard": 42, "mcf-data-gen": 80}
rows = []
for br in DELAY:
    raw = subprocess.run(["git", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(raw); f.flush()
        c = sqlite3.connect(f.name)
        for ts, sym, ref, stop, info in c.execute("SELECT ts, symbol, ref_price, stop, info FROM signals WHERE run_id=1 AND "
                                                  "day>='2026-10-27' AND info LIKE '%spread_bps%'"):
            i = json.loads(info)
            rows.append(dict(br=br, ts=ts, sym=sym, ref=float(ref), risk=abs(float(ref) - float(stop)), bid=i["bid"], ask=i["ask"]))
d = pd.DataFrame(rows)
d["sec"] = d.ts.str[:19]
d = d.drop_duplicates(["sym", "sec"]).sample(n=N, random_state=11).reset_index(drop=True)
sess = _session()
sk = lambda bid, ask, ref, risk: ((ask - bid) / ((ask + bid) / 2) * 1e4 > 30) or (risk > 0 and (ask - bid) / risk > 0.25)  # noqa
res = []
for r in d.itertuples():
    t = pd.Timestamp(r.ts).tz_convert("UTC")
    qs, params = [], {"start": (t - pd.Timedelta(seconds=30)).isoformat(), "end": (t + pd.Timedelta(seconds=240)).isoformat(),
                      "feed": "sip", "limit": 10000}
    j = _get(sess, f"https://data.alpaca.markets/v2/stocks/{r.sym}/quotes", params)
    qs = [(pd.Timestamp(q["t"]), q["bp"], q["ap"]) for q in (j.get("quotes") or []) if q["bp"] > 0 and q["ap"] >= q["bp"]]
    def at(x):
        p = [q for q in qs if q[0] <= x]
        return p[-1] if p else None
    truth = sk(r.bid, r.ask, r.ref, r.risk)
    out = {"truth": truth}
    for name, x in (("at_poll", t), ("at_delay", t + pd.Timedelta(seconds=DELAY[r.br]))):
        q = at(x)
        out[name] = None if q is None else sk(q[1], q[2], r.ref, r.risk)
    hit = [q for q in qs if q[0] >= t - pd.Timedelta(seconds=5) and abs(q[1] - r.bid) < 1e-9 and abs(q[2] - r.ask) < 1e-9]
    out["oracle"] = truth if hit else None
    out["paged"] = bool(j.get("next_page_token"))
    res.append(out)
x = pd.DataFrame(res)
x.to_csv(OUT, index=False)
print(f"sample {len(x)}; live spread skips {int(x.truth.sum())}; quote page truncated (busy names) {x.paged.mean():.0%}")
for c in ("at_poll", "at_delay", "oracle"):
    m = x[c].notna()
    print(f"{c:9s} coverage {m.mean():.0%} skip-decision agree {(x.loc[m, c] == x.truth[m]).mean():.1%}  "
          f"recall {((x[c] == True) & x.truth).sum() / max(1, x.truth[m].sum()):.0%}")  # noqa: E712
print("Educational only - not financial advice.")
