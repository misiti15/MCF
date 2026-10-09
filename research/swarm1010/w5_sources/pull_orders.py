"""Read-only: closed orders (nested legs) of the data-key account, last ~30 days -> data/orders.parquet.
Educational only - not financial advice."""
import os, sys
import pandas as pd, requests
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
P = "https://paper-api.alpaca.markets"
OUT = os.path.join(os.path.dirname(__file__), "data", "orders.parquet")
rows, until = [], None
while True:
    url = f"{P}/v2/orders?status=closed&limit=500&nested=true&after=2026-09-01T00:00:00Z&direction=desc"
    if until: url += f"&until={until}"
    j = requests.get(url, headers=H, timeout=30).json()
    if not j: break
    for o in j:
        for x in [o] + (o.get("legs") or []):
            rows.append({k: x.get(k) for k in ("id", "symbol", "side", "type", "order_class", "status", "qty", "filled_qty",
                         "filled_avg_price", "limit_price", "stop_price", "submitted_at", "filled_at", "created_at")} | {"parent": o["id"]})
    until = j[-1]["submitted_at"] or j[-1]["created_at"]
    if len(j) < 500: break
df = pd.DataFrame(rows).drop_duplicates("id")
df.to_parquet(OUT)
f = df[df.status == "filled"]
print(len(df), "orders;", len(f), "filled;", f.symbol.nunique(), "symbols")
print(f.groupby(["type", "side"]).size())
print(pd.to_datetime(f.filled_at).dt.tz_convert("America/New_York").dt.date.value_counts().sort_index())
