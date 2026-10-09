"""Read-only Alpaca news headlines for the traded symbols of 2026-10-09 (2026-10-08 16:00 ET .. 2026-10-09 16:00 ET)
-> data/cache/bdi1009/news.json {SYM: [{t (ET), headline, material}]}. 'material' = a keyword screen (earnings,
guidance, M&A, rating changes, FDA, offering, legal, management; routine "maintains/reiterates" notes and SPY macro
headlines are not material); reviewed by hand in AUTOPSY.md.
Educational only - not financial advice."""
import json
import os
import re
from pathlib import Path

import pandas as pd
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "data" / "cache" / "bdi1009" / "news.json"
RX = re.compile(r"earnings|results|guidance|outlook|acqui|merger|to buy|deal|downgrad|upgrad|price target|initiat|"
                r"\bFDA\b|approval|offering|lawsuit|probe|investigat|contract|award|CEO|resign|buyback|repurchase|"
                r"bankrupt|\bSEC\b|recall|partnership|stake|spin-off|layoff|takeover|why is .* (falling|soaring|trending)|"
                r"stock (rises|falls|hits|surges|plunges)|52-week|sold out|EPS", re.I)
ROUTINE = re.compile(r"\bMaintains\b|\bReiterates\b|Performance Comparison|Invested In|Forecasters Revamp", re.I)
syms = set()
for f in ("primary", "testing"):
    syms |= set(pd.read_csv(ROOT / "data" / "bdi1009" / f"{f}.csv").symbol)
syms = sorted(syms)
cli = NewsClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
out = {}
a, b = pd.Timestamp("2026-10-08 16:00", tz="America/New_York"), pd.Timestamp("2026-10-09 16:00", tz="America/New_York")
for i in range(0, len(syms), 25):
    tok = None
    while True:
        req = NewsRequest(symbols=",".join(syms[i:i + 25]), start=a.to_pydatetime(), end=b.to_pydatetime(), limit=50,
                          page_token=tok)
        res = cli.get_news(req)
        for n in res.data.get("news", []):
            t = pd.Timestamp(n.created_at).tz_convert("America/New_York")
            for s in n.symbols or []:
                if s in syms and len(n.symbols) <= 4:
                    out.setdefault(s, []).append({"t": str(t)[:19], "headline": n.headline or "",
                                                  "material": bool(RX.search(n.headline or "")) and not ROUTINE.search(n.headline or "")})
        tok = getattr(res, "next_page_token", None)
        if not tok:
            break
for s in out:
    out[s] = sorted({h["t"] + h["headline"]: h for h in out[s]}.values(), key=lambda h: h["t"])
for h in out.get("SPY", []):
    h["material"] = False          # macro headlines, not a symbol catalyst
json.dump(out, open(OUT, "w"), indent=1)
print(len(out), sum(len(v) for v in out.values()))
for s, v in sorted(out.items()):
    for h in v:
        print(s, h["t"][5:16], "M" if h["material"] else " ", h["headline"][:110])
