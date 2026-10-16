"""Testing 2 broker-vs-journal gap diagnostic (owner approved 2026-10-16). READ-ONLY: GET account activities (all
types) and GET orders; never places or cancels orders; prints no secrets.

For each day it lists every non-FILL cash activity (fees, borrow, dividends, journal entries...) and every FILL whose
order id is not in the journal, then sums them so the day's broker-vs-journal gap can be explained.

  python research/bdi/t2diag/acts.py <journal.db> 2026-10-12 2026-10-15 > report.md

Educational only - not financial advice.
"""
import os
import sqlite3
import sys

import pandas as pd
import requests

BASE = "https://paper-api.alpaca.markets/v2"


def activities(h, day):
    out, token = [], None
    while True:
        p = {"date": day, "direction": "asc", "page_size": 100}
        if token:
            p["page_token"] = token
        r = requests.get(f"{BASE}/account/activities", headers=h, params=p, timeout=30)
        r.raise_for_status()
        got = r.json()
        out += got
        if len(got) < 100:
            return out
        token = got[-1]["id"]


def main(db, d0, d1):
    h = {"APCA-API-KEY-ID": os.environ["ALPACA_TRADE_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_TRADE_SECRET_KEY"]}
    con = sqlite3.connect(db)
    known = set(pd.read_sql("select broker_order_id from orders where broker_order_id is not null", con).broker_order_id)
    tr = pd.read_sql("select date, sum(pnl) pnl, count(*) n from trades where run_id=1 group by date", con).set_index("date")
    print("# Testing 2 broker activity diagnostic\n\n*Educational only - not financial advice.*\n")
    for day in pd.bdate_range(d0, d1).strftime("%Y-%m-%d"):
        acts = pd.DataFrame(activities(h, day))
        print(f"\n## {day}\n")
        if acts.empty:
            print("no activities"); continue
        print("activity types:", acts.activity_type.value_counts().to_dict())
        fills = acts[acts.activity_type == "FILL"].copy()
        cash = acts[acts.activity_type != "FILL"].copy()
        if len(cash):
            cash["net_amount"] = pd.to_numeric(cash.get("net_amount"), errors="coerce")
            print("\nnon-fill cash activities (sum %.2f):\n" % cash.net_amount.sum())
            cols = [c for c in ["activity_type", "date", "net_amount", "symbol", "qty", "per_share_amount", "description"] if c in cash]
            print(cash[cols].to_markdown(index=False))
        if len(fills):
            fills["unknown"] = ~fills.order_id.isin(known)
            for c in ("qty", "price"):
                fills[c] = pd.to_numeric(fills[c], errors="coerce")
            fills["sign"] = fills.side.map({"buy": -1, "sell": 1, "sell_short": 1}).fillna(0)
            fills["cash"] = fills.sign * fills.qty * fills.price
            u = fills[fills.unknown]
            print(f"\nfills: {len(fills)}, orders not in journal: {u.order_id.nunique()}, their cash flow {u.cash.sum():.2f}")
            if len(u):
                print(u[["transaction_time", "symbol", "side", "qty", "price", "order_id"]].head(60).to_markdown(index=False))
        if day in tr.index:
            print(f"\njournal day P/L {tr.loc[day, 'pnl']:.2f} ({tr.loc[day, 'n']} trades)")


if __name__ == "__main__":
    main(*sys.argv[1:4])
