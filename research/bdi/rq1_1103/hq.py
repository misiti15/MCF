"""REP-Q1: historical SIP NBBO at the live decision second, for a replay WITHOUT recorded quotes (what a new setup gets).
Pass 1 = the FB replay of the account-session (its quote-checked signals: symbol + poll minute + replay poll time).
For each, the last SIP quote at or before (replay poll time + the account's median poll-start -> submit delay;
night1102 hist_quote_delay: Primary 28 s, T1 22, T2 56, Graveyard 42, Gen 80), read-only GET
/v2/stocks/{sym}/quotes (sort desc, limit 1). Written as <journals>/hq_<day>_<account>.pkl {sym: {k: (bid, ask, age)}};
run.py conf FHB replays with these quotes (exact minute) and the OTHER accounts' borrow answers only.
    python hq.py <run dir>/FB <journals dir> <day> <account,...>
Educational only - not financial advice."""
import json
import pickle
import sys
from pathlib import Path

import pandas as pd

from mcf.replay.store import _get, _session

DELAY = {"primary": 28, "testing": 22, "testing2": 56, "graveyard": 42, "gen": 80}
run, jdir, day = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sess = _session()
t0 = pd.Timestamp(f"{day} 09:30", tz="America/New_York")
for ac in sys.argv[4].split(","):
    p = jdir / f"hq_{day}_{ac}.pkl"
    if p.exists():
        continue
    s = pd.read_csv(run / ac / day / "signals.csv.gz")
    s = s[s["info"].fillna("").str.contains('"bid"')]
    out, n, miss = {}, 0, 0
    for ts, sym in sorted(set(zip(s.ts, s.symbol))):
        t = pd.Timestamp(ts)
        t = t.tz_localize("America/New_York") if t.tzinfo is None else t.tz_convert("America/New_York")
        k = int((t - t0) // pd.Timedelta(minutes=1))
        if k in out.get(sym, {}):
            continue
        at = (t + pd.Timedelta(seconds=DELAY[ac])).tz_convert("UTC")
        j = _get(sess, f"https://data.alpaca.markets/v2/stocks/{sym}/quotes",
                 {"start": (at - pd.Timedelta(seconds=600)).isoformat(), "end": at.isoformat(), "feed": "sip",
                  "limit": 1, "sort": "desc"})
        q = [x for x in (j.get("quotes") or []) if x["bp"] > 0 and x["ap"] >= x["bp"]]
        n += 1
        if not q:
            miss += 1
            continue
        age = max(0.0, (at - pd.Timestamp(q[0]["t"])).total_seconds())
        out.setdefault(sym, {})[k] = (float(q[0]["bp"]), float(q[0]["ap"]), age)
    p.write_bytes(pickle.dumps(out))
    print(day, ac, "quote requests", n, "no quote", miss, flush=True)
print(json.dumps({"_note": "Educational only - not financial advice."}))
