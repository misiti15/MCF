"""H-2 (Testing 2, 2026-10-14): list the broker's FILL activities in the restart window and flag fills whose order
is not in the Testing 2 journal. READ-ONLY (GET account activities + GET orders); never places or cancels orders.

Needs the Testing 2 trading keys in the environment (GitHub secrets ALPACA_TESTING2_API_KEY / _SECRET_KEY), exported
as ALPACA_TRADE_API_KEY / ALPACA_TRADE_SECRET_KEY. Prints no secrets.

  git show origin/mcf-data-testing2:journal.db > /tmp/t2.db
  python research/bdi/nightly1014/h2_fills.py /tmp/t2.db 2026-10-14T14:18:54Z 2026-10-14T14:22:13Z

Educational only - not financial advice.
"""
import os
import sqlite3
import sys

import pandas as pd
import requests

BASE = "https://paper-api.alpaca.markets/v2"


def main(db, start, end):
    h = {"APCA-API-KEY-ID": os.environ["ALPACA_TRADE_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_TRADE_SECRET_KEY"]}
    acts, token = [], None
    while True:                                   # activities page newest first, 100 at a time
        p = {"activity_types": "FILL", "after": start, "until": end, "direction": "desc", "page_size": 100}
        if token:
            p["page_token"] = token
        got = requests.get(f"{BASE}/account/activities", headers=h, params=p, timeout=30).json()
        acts += got
        if len(got) < 100:
            break
        token = got[-1]["id"]
    if not acts:
        print("no fills in the window")
        return
    f = pd.DataFrame(acts)
    f["qty"] = f["qty"].astype(float)
    f["price"] = f["price"].astype(float)
    f["cash"] = f.apply(lambda r: (-1 if r.side == "buy" else 1) * r.qty * r.price, axis=1)
    j = sqlite3.connect(db)
    ids = set(pd.read_sql("SELECT broker_order_id FROM orders", j).broker_order_id.astype(str))
    coids = {}
    for oid in f.order_id.unique():               # client order id of each filled order (legs get broker ids)
        o = requests.get(f"{BASE}/orders/{oid}", headers=h, timeout=30).json()
        coids[oid] = o.get("client_order_id", "")
    f["coid"] = f.order_id.map(coids)
    f["in_journal"] = f.order_id.astype(str).isin(ids)
    cols = ["transaction_time", "symbol", "side", "qty", "price", "cash", "type", "coid", "in_journal"]
    print(f[cols].sort_values("transaction_time").to_string(index=False))
    print("\nfills by client-id prefix (cash flow):")
    print(f.groupby(f.coid.str[:4])["cash"].agg(["count", "sum"]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
