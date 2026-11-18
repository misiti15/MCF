"""GET-only Alpaca market data: 1-min RTH bars for the studied setups' symbol-days, daily bars for ATR14. Keys from env, never printed."""
import os, sys, time, json, requests, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u7"
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
U = "https://data.alpaca.markets/v2/stocks/bars"
def get(params):
    rows, tok = [], None
    while True:
        p = dict(params, limit=10000, adjustment="split", feed="sip")
        if tok: p["page_token"] = tok
        for k in range(5):
            r = requests.get(U, headers=H, params=p, timeout=60)
            if r.status_code == 429: time.sleep(3); continue
            r.raise_for_status(); break
        j = r.json()
        for s, bs in (j.get("bars") or {}).items():
            for b in bs: rows.append((s, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]))
        tok = j.get("next_page_token")
        if not tok: return pd.DataFrame(rows, columns=["symbol", "ts", "open", "high", "low", "close", "volume"])
def main():
    sd = pd.read_csv(f"{S}/symdays.csv")
    os.makedirs(f"{S}/m1", exist_ok=True)
    for d, g in sd.groupby("date"):
        assert not ("2024-11-01" <= d <= "2025-02-28")
        f = f"{S}/m1/{d}.parquet"
        if os.path.exists(f): continue
        syms = sorted(set(g.symbol)); out = []
        for i in range(0, len(syms), 100):
            out.append(get({"symbols": ",".join(syms[i:i+100]), "timeframe": "1Min", "start": f"{d}T13:00:00Z", "end": f"{d}T21:30:00Z"}))
        pd.concat(out).to_parquet(f); print(d, len(syms), flush=True)
    syms = sorted(set(sd.symbol)); out = []
    for i in range(0, len(syms), 100):
        out.append(get({"symbols": ",".join(syms[i:i+100]), "timeframe": "1Day", "start": "2026-08-20", "end": "2026-11-17"}))
    pd.concat(out).to_parquet(f"{S}/daily.parquet"); print("daily", len(syms))
main()
