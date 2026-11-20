"""Item 3: TAGS1 frozen rules on the fresh session 2026-11-19 (descriptive; no score). Usage:
python item3_tags.py <worktree> <tmpdir with j/*.db> <outdir>.  Educational only - not financial advice."""
import sys, os, json, sqlite3, requests, numpy as np, pandas as pd
WT, TMP, OUT = sys.argv[1:4]
sys.path.insert(0, WT); sys.path.insert(0, f"{WT}/research/tags1")
import tags1
DAY = "2026-11-19"
H = {'APCA-API-KEY-ID': os.environ['ALPACA_API_KEY'], 'APCA-API-SECRET-KEY': os.environ['ALPACA_SECRET_KEY']}
def get(syms, tf, start, end):
    out = []
    for i in range(0, len(syms), 100):
        tok = None
        while True:
            p = {'symbols': ','.join(syms[i:i+100]), 'timeframe': tf, 'start': start, 'end': end, 'limit': 10000,
                 'adjustment': 'split', 'feed': 'sip'}
            if tok: p['page_token'] = tok
            r = requests.get('https://data.alpaca.markets/v2/stocks/bars', headers=H, params=p, timeout=60); r.raise_for_status()
            j = r.json()
            for s, b in (j.get('bars') or {}).items():
                for x in b: x['S'] = s; out.append(x)
            tok = j.get('next_page_token')
            if not tok: break
    d = pd.DataFrame(out).rename(columns={'S': 'symbol', 't': 'ts', 'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'})
    d['ts'] = pd.to_datetime(d.ts, utc=True)
    return d[['symbol', 'ts', 'open', 'high', 'low', 'close', 'volume']]

# decisions: live = run kind paper/live only; shadow = shadow; whatif excluded
rows = []
for b, acct in tags1.ACCOUNTS.items():
    c = sqlite3.connect(f"file:{TMP}/j/{b}.db?mode=ro", uri=True)
    runs = dict(c.execute("select id, kind from runs").fetchall())
    t = pd.read_sql("select * from trades where date=?", c, params=[DAY]); c.close()
    t["kind"] = t.run_id.map(runs); t["acct"] = acct
    rows.append(t)
allt = pd.concat(rows, ignore_index=True)
kinds = allt.groupby(["kind"]).size().to_dict()
dec = allt[allt.kind.isin(["paper", "live", "shadow"])].copy()
dec["source"] = np.where(dec.kind.eq("shadow"), "shadow", "live")
dec = dec.reset_index(drop=True)
syms = sorted(set(dec.symbol.astype(str)) | {"SPY"})
m = get(syms, '1Min', f"{DAY}T14:30:00Z", f"{DAY}T21:00:00Z")
daily = get(syms, '1Day', "2026-09-20", DAY)
out = tags1.build(dec, m, daily, DAY, set())
out["kind"] = dec.kind.values
risk = (out.entry - out.stop).abs() * out.shares.abs()
out["R"] = np.where(out.pnl_adj.notna() & (risk > 0), out.pnl_adj / risk, out.r_multiple)
out["usd"] = np.where(risk > 0, out.R * risk, out.pnl_adj)
EQ = {"primary": 84883.40, "testing": 94680.51, "testing2": 92146.22, "explore1": 100266.73, "livelab": 100190.09,
      "testingd": 100188.97, "testinge": 99024.04, "testingf": 99974.85, "gen": 89646.45, "graveyard": 91417.92}
out["acctR"] = out.usd / (out.acct.map(EQ) * 0.0025)
et = pd.to_datetime(out.entry_time, utc=True, format="ISO8601").dt.tz_convert("America/New_York")
out["k"] = out.strategy + "|" + out.symbol + "|" + out.date + "|" + et.dt.strftime("%H%M")
os.makedirs(OUT, exist_ok=True)
out.to_csv(f"{OUT}/tags_2026-11-19.csv.gz", index=False)
print("run kinds", kinds, "tagged", len(out), "closed", out.exit_time.notna().sum())
print("whatif rows that tags1.decisions() would label live:", int((allt.kind == "whatif").sum()))
