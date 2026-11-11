"""Guild Builder: append ONE session's 1-minute SIP bars (all lab symbols) to data/cache_hist/1Min and its row to
research/history2y/data/daily.parquet, for nightly forward shadows (FAMC). Read-only Alpaca market-data GETs, multi-symbol
requests (100 per call), keys from the environment (never printed). Refuses 07:30-16:05 ET so the live job keeps its
rate budget. Idempotent: rerunning a day replaces that day's rows. Does not touch the locked block (only appends D).
    python append_day.py 2026-11-10          Educational only - not financial advice."""
import os, sys, time
from datetime import datetime
from pathlib import Path
import numpy as np, pandas as pd, requests

ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
from mcf.data.bars import normalize, rth
import download as DL
NY = "America/New_York"
now = pd.Timestamp.now(tz=NY); hm = now.hour * 100 + now.minute
D = pd.Timestamp(sys.argv[1]).date()
assert not (730 <= hm < 1605), "refusing: 07:30-16:05 ET (live job's rate budget)"
assert D <= now.date() and not (D == now.date() and hm < 1605), "day not closed yet"
assert not (pd.Timestamp("2024-11-01").date() <= D <= pd.Timestamp("2025-02-28").date()), "locked block"
syms = (ROOT / "research/lab_symbols.txt").read_text().split()
sess = requests.Session(); sess.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
start = pd.Timestamp(f"{D} 09:30", tz=NY).tz_convert("UTC").isoformat(); end = pd.Timestamp(f"{D} 16:00", tz=NY).tz_convert("UTC").isoformat()
bars = {}
for i in range(0, len(syms), 100):
    chunk = syms[i:i + 100]
    params = {"symbols": ",".join(chunk), "timeframe": "1Min", "start": start, "end": end, "feed": "sip", "adjustment": "split", "limit": 10000}
    while True:
        j = DL._get(sess, params)
        for s, bl in (j.get("bars") or {}).items(): bars.setdefault(s, []).extend(bl)
        tok = j.get("next_page_token")
        if not tok: break
        params["page_token"] = tok
    params.pop("page_token", None)
print(f"{D}: bars for {len(bars)} of {len(syms)} symbols", flush=True)
rows, done = [], 0
for s, bl in bars.items():
    df = pd.DataFrame({"open": [b["o"] for b in bl], "high": [b["h"] for b in bl], "low": [b["l"] for b in bl],
                       "close": [b["c"] for b in bl], "volume": [b["v"] for b in bl]}, index=pd.DatetimeIndex(pd.to_datetime([b["t"] for b in bl], utc=True)))
    df = rth(normalize(df))
    if not len(df): continue
    p = ROOT / "data/cache_hist/1Min" / f"{s}.parquet"
    if p.exists():
        old = pd.read_parquet(p); old = old[old.index.date != D]
        df = pd.concat([old, df]); df = df[~df.index.duplicated(keep="last")].sort_index()
    tmp = p.with_suffix(".tmp"); df.to_parquet(tmp); tmp.replace(p); done += 1
    x = df[df.index.date == D]
    rows.append(dict(symbol=s, date=D, open=float(x.open.iloc[0]), high=float(x.high.max()), low=float(x.low.min()), close=float(x.close.iloc[-1]),
                     volume=float(x.volume.sum()), dollar_volume=float((x.close * x.volume).sum())))
dp = ROOT / "research/history2y/data/daily.parquet"; Dd = pd.read_parquet(dp)
Dd = Dd[pd.to_datetime(Dd.date).dt.date != D]
new = pd.DataFrame(rows)
allr = pd.concat([Dd, new.assign(adv20=np.nan)], ignore_index=True); allr["_d"] = pd.to_datetime(allr.date)
allr = allr.sort_values(["symbol", "_d"])
adv = allr.groupby("symbol").dollar_volume.transform(lambda v: v.shift(1).rolling(20, min_periods=5).mean())
m = allr._d.dt.date == D; allr.loc[m, "adv20"] = adv[m]
allr = allr.drop(columns="_d"); allr.to_parquet(dp, index=False)   # date stays datetime.date (file format)
print(f"appended {D}: {done} symbol files updated, {len(new)} daily rows (adv20 point-in-time from prior sessions). "
      "Educational only - not financial advice.")
