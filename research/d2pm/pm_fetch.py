"""D2PM premarket fetcher: Alpaca SIP 1-min bars 04:00-09:29 ET per symbol into data/cache_pm/<SYM>.parquet (read-only data GETs).
Refuses to run 07:30-16:00 ET on weekdays (the live job's data budget). Keys from the environment, never printed.
usage (from the MCF checkout): python pm_fetch.py <start YYYY-MM-DD> <end YYYY-MM-DD> <symbols.txt> [workers=3]
Educational only - not financial advice."""
import os, sys, time, multiprocessing as mp
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import pandas as pd, requests
ET = ZoneInfo("America/New_York"); OUT = Path("data/cache_pm"); URL = "https://data.alpaca.markets/v2/stocks/bars"
def guard():
    n = datetime.now(ET)
    if n.weekday() < 5 and (7 * 60 + 30) <= n.hour * 60 + n.minute < 16 * 60:
        sys.exit("refusing: 07:30-16:00 ET on a weekday (live data budget)")
def fetch(a):
    sym, start, end = a; p = OUT / f"{sym}.parquet"
    if p.exists(): return sym, "skip"
    guard()
    s = requests.Session(); s.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    prm = {"symbols": sym, "timeframe": "1Min", "start": f"{start}T08:00:00Z", "end": f"{end}T15:00:00Z", "feed": "sip", "adjustment": "split", "limit": 10000}
    rows = []
    for _ in range(200):
        for k in range(6):
            r = s.get(URL, params=prm, timeout=30)
            if r.status_code == 429: time.sleep(2 ** k); continue
            break
        if r.status_code != 200: return sym, f"http {r.status_code}"
        j = r.json(); rows += (j.get("bars") or {}).get(sym, [])
        if not j.get("next_page_token"): break
        prm["page_token"] = j["next_page_token"]
    if not rows: return sym, "empty"
    d = pd.DataFrame(rows); d.index = pd.to_datetime(d.t, utc=True).dt.tz_convert(ET)
    d = d.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume", "n": "trades"})[["open", "high", "low", "close", "volume"] + (["trades"] if "trades" in d.rename(columns={"n": "trades"}) else [])]
    d = d.between_time("04:00", "09:29")
    d.to_parquet(p); return sym, f"ok {len(d)}"
if __name__ == "__main__":
    guard(); OUT.mkdir(parents=True, exist_ok=True)
    st, en, f = sys.argv[1:4]; w = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    syms = Path(f).read_text().split(); bad = []
    with mp.Pool(w) as pool:
        for i, (sym, stt) in enumerate(pool.imap_unordered(fetch, [(x, st, en) for x in syms]), 1):
            if not (stt.startswith("ok") or stt == "skip"): bad.append(f"{sym}\t{stt}")
            if i % 200 == 0: print(f"{i}/{len(syms)}", flush=True)
    print(f"finished {len(syms)}, not ok {len(bad)}"); (OUT / "failed.txt").write_text("\n".join(bad))
