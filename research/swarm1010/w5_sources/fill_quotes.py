"""For each filled order (data/orders.parquet): the last valid SIP NBBO at or before submitted_at and filled_at.
Read-only GETs. Out: data/fill_quotes.parquet. Educational only - not financial advice."""
import os, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd, requests
HERE = os.path.dirname(os.path.abspath(__file__))
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}

def last_quote(sym, t):
    t = pd.Timestamp(t)
    for back in (5, 60, 900):
        p = {"symbols": sym, "start": (t - pd.Timedelta(seconds=back)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
             "end": t.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "feed": "sip", "limit": 1000, "sort": "desc"}
        for a in range(6):
            try:
                r = requests.get("https://data.alpaca.markets/v2/stocks/quotes", headers=H, params=p, timeout=30)
                if r.status_code != 429: break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(2 + 2 * a)
        for q in (r.json().get("quotes") or {}).get(sym, []):
            if q["bp"] > 0 and q["ap"] > q["bp"]:
                return q["bp"], q["ap"]
    return float("nan"), float("nan")

def row(o):
    b0, a0 = last_quote(o.symbol, o.submitted_at); b1, a1 = last_quote(o.symbol, o.filled_at)
    return {"id": o.id, "bid_sub": b0, "ask_sub": a0, "bid_fill": b1, "ask_fill": a1}

if __name__ == "__main__":
    o = pd.read_parquet(os.path.join(HERE, "data", "orders.parquet"))
    f = o[(o.status == "filled") & o.submitted_at.notna()]
    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(row, [r for r in f.itertuples()]))
    pd.DataFrame(res).to_parquet(os.path.join(HERE, "data", "fill_quotes.parquet")); print(len(res))
