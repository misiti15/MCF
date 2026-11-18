"""SIZESTOP Amendment 1 input (Builder): Alpaca corporate actions, cash dividends (ex_date, rate, special) for the lab list,
in two ranges that skip the locked block 2024-11-01..2025-02-28 (no block data requested). Refused weekdays 07:30-16:05 ET.
Output data/cash_div.parquet (git-ignored). Read-only GETs; keys from env, never printed.
    python fetch_div.py          Educational only - not financial advice."""
import json, os, urllib.parse, urllib.request
from pathlib import Path
import numpy as np, pandas as pd
now = pd.Timestamp.now(tz="America/New_York"); hm = now.hour * 100 + now.minute
assert now.dayofweek >= 5 or not (730 <= hm < 1605), "refusing: weekday 07:30-16:05 ET"
HERE = Path(__file__).resolve().parent
syms = sorted(set(Path("/home/user/MCF/research/lab_symbols.txt").read_text().split()))
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
rows, splits = [], []
import sys; sys.path.insert(0, str(HERE.parent)); import builder_blockguard as BG          # checklist 43
for a, b in (("2024-09-01", "2024-10-31"), ("2025-03-01", "2026-11-13")):
    BG.check(a, b)
    for i in range(0, len(syms), 50):
        tok = None
        while True:
            q = {"symbols": ",".join(syms[i:i + 50]), "types": "cash_dividend,forward_split,reverse_split", "start": a, "end": b, "limit": 1000}
            if tok: q["page_token"] = tok
            j = json.load(urllib.request.urlopen(urllib.request.Request("https://data.alpaca.markets/v1/corporate-actions?" + urllib.parse.urlencode(q), headers=H), timeout=60))
            ca = j.get("corporate_actions", {})
            rows += [dict(symbol=x["symbol"], date=x["ex_date"], rate=float(x["rate"]), special=bool(x.get("special") or False))
                     for x in ca.get("cash_dividends", [])]
            for kind in ("forward_splits", "reverse_splits"):
                splits += [dict(symbol=x["symbol"], date=x["ex_date"], ratio=float(x["new_rate"]) / float(x["old_rate"]))
                           for x in ca.get(kind, [])]
            tok = j.get("next_page_token")
            if not tok: break
dv = pd.DataFrame(rows).drop_duplicates(["symbol", "date"])
inb = (dv.date >= "2024-11-01") & (dv.date <= "2025-02-28")       # the API filters on another date: drop block ex-dates
print(f"dropped {int(inb.sum())} ex-dates inside the locked block (returned by the API's own date filter; never used)")
dv = dv[~inb]
# Skeptic 11-14 18:50: Alpaca dividend rates are per pre-split share; the price cache is split-adjusted, so divide each
# rate by the product of split ratios with ex_date AFTER the dividend's ex_date (any range, block splits included as dates only)
sp = pd.DataFrame(splits, columns=["symbol", "date", "ratio"]).drop_duplicates(["symbol", "date"])
def later_factor(r):
    x = sp[(sp.symbol == r.symbol) & (sp.date > r.date)]
    return float(np.prod(x.ratio)) if len(x) else 1.0
dv["split_factor"] = dv.apply(later_factor, axis=1); dv["rate_adj"] = dv.rate / dv.split_factor
print(f"splits: {len(sp)} ({sp.symbol.nunique()} names); dividends adjusted by a later split: {int((dv.split_factor != 1).sum())}")
(HERE / "data").mkdir(exist_ok=True); dv.to_parquet(HERE / "data/cash_div.parquet", index=False); sp.to_parquet(HERE / "data/splits.parquet", index=False)
print(f"cash dividends: {len(dv)} ex-dates, {dv.symbol.nunique()} names, special {int(dv.special.sum())}; {dv.date.min()}..{dv.date.max()}. "
      "Educational only - not financial advice.")
