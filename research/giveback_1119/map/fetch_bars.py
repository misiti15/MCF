"""Fetch 1-minute SIP bars (09:30-16:00 ET) for every live (day, symbol) + SPY/QQQ from Alpaca market data (read-only GET).
Keys from env only, never written. Usage: python fetch_bars.py live_trades.parquet out.parquet"""
import os, sys, time, requests, pandas as pd
d = pd.read_parquet(sys.argv[1]); OUT = sys.argv[2]
need = d.groupby("date").symbol.apply(lambda s: sorted(set(s) | {"SPY", "QQQ"}))
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
feed = os.environ.get("ALPACA_DATA_FEED", "sip"); S = requests.Session(); nreq = 0; frames = []
for day, syms in need.items():
    rows = []
    off = "-05:00" if day >= "2026-11-02" else "-04:00"
    for i in range(0, len(syms), 150):
        tok = None
        while True:
            p = {"symbols": ",".join(syms[i:i + 150]), "timeframe": "1Min", "start": f"{day}T09:30:00{off}", "end": f"{day}T16:00:00{off}",
                 "limit": 10000, "feed": feed, "adjustment": "raw"}
            if tok: p["page_token"] = tok
            for att in range(5):
                r = S.get("https://data.alpaca.markets/v2/stocks/bars", params=p, headers=H, timeout=60); nreq += 1
                if r.status_code == 429: time.sleep(5); continue
                r.raise_for_status(); break
            j = r.json()
            for s, bars in (j.get("bars") or {}).items():
                rows += [(day, s, b["t"], b["o"], b["h"], b["l"], b["c"]) for b in bars]
            tok = j.get("next_page_token")
            if not tok: break
    f = pd.DataFrame(rows, columns=["day", "symbol", "t", "o", "h", "l", "c"])
    f["t"] = pd.to_datetime(f.t, utc=True).dt.tz_convert("America/New_York")
    f["m"] = (f.t.dt.hour * 60 + f.t.dt.minute).astype("int16")
    for k in "ohlc": f[k] = f[k].astype("float32")
    frames.append(f.drop(columns="t")); print(day, len(syms), len(f), nreq, flush=True)
pd.concat(frames, ignore_index=True).to_parquet(OUT, index=False); print("requests", nreq)
