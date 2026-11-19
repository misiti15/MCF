import os, sys, json, sqlite3, requests, pandas as pd
W = sys.argv[1]
d = pd.read_pickle(f"{W}/live.pkl")
d = d[d.date > "2026-11-04"]
need = d.groupby("date").symbol.apply(lambda s: sorted(set(s) | {"SPY", "QQQ"}))
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
feed = os.environ.get("ALPACA_DATA_FEED", "sip")
nreq = 0
out = {}
for day, syms in need.items():
    tok = None
    while True:
        p = {"symbols": ",".join(syms), "timeframe": "1Min", "start": f"{day}T14:30:00Z", "end": f"{day}T21:00:00Z",
             "limit": 10000, "feed": feed, "adjustment": "raw"}
        if tok: p["page_token"] = tok
        r = requests.get("https://data.alpaca.markets/v2/stocks/bars", params=p, headers=H, timeout=60)
        nreq += 1
        r.raise_for_status()
        j = r.json()
        for s, bars in (j.get("bars") or {}).items():
            out.setdefault((day, s), []).extend(bars)
        tok = j.get("next_page_token")
        if not tok: break
    print(day, len(syms), nreq, flush=True)
    if nreq >= 19: print("budget stop"); break
rows = []
for (day, s), bars in out.items():
    for b in bars:
        rows.append((day, s, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]))
pd.DataFrame(rows, columns=["day", "symbol", "t", "o", "h", "l", "c", "v"]).to_parquet(f"{W}/bars_recent.parquet")
print("requests", nreq, "rows", len(rows))
