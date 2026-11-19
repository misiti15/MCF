"""GET-only Alpaca market data: 1-min RTH bars (raw, unadjusted, to match journal prices) for the what-if symbol-days. Keys from env, never printed."""
import os, sys, time, requests, pandas as pd
S = sys.argv[1]
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
U = "https://data.alpaca.markets/v2/stocks/bars"
def get(params):
    rows, tok = [], None
    while True:
        p = dict(params, limit=10000, adjustment="raw", feed="sip")
        if tok: p["page_token"] = tok
        for k in range(6):
            try:
                r = requests.get(U, headers=H, params=p, timeout=60)
            except requests.RequestException:
                time.sleep(3); continue
            if r.status_code == 429: time.sleep(3); continue
            r.raise_for_status(); break
        j = r.json()
        for s, bs in (j.get("bars") or {}).items():
            for b in bs: rows.append((s, b["t"], b["o"], b["h"], b["l"], b["c"]))
        tok = j.get("next_page_token")
        if not tok: return pd.DataFrame(rows, columns=["symbol", "ts", "open", "high", "low", "close"])
sd = pd.read_csv(f"{S}/symdays.csv")
os.makedirs(f"{S}/m1", exist_ok=True)
for d, g in sd.groupby("day"):
    assert d >= "2026-10-06"
    f = f"{S}/m1/{d}.parquet"
    if os.path.exists(f): continue
    syms = sorted(set(g.symbol)); out = []
    for i in range(0, len(syms), 100):
        out.append(get({"symbols": ",".join(syms[i:i+100]), "timeframe": "1Min", "start": f"{d}T13:30:00Z", "end": f"{d}T21:00:00Z"}))
    pd.concat(out).to_parquet(f); print(d, len(syms), flush=True)
