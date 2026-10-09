"""NBBO sample for spread calibration (read-only GETs, Alpaca SIP quotes).

For each sample time t (every minute 09:30-10:30 ET, every 5 min 10:35-15:55 ET) on the 5 sessions 2026-10-05..09 and
for every symbol MCF traded 2026-10-06..09 (data/orders.parquet), pull all SIP quotes in [t-3s, t] and keep per
symbol: last valid quote (bid, ask, sizes), quote count, median spread in the window. Out: data/nbbo_sample.parquet.
Valid = bid > 0 and ask > bid (locked/crossed excluded). Educational only - not financial advice.
"""
import os, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd, requests

HERE = os.path.dirname(os.path.abspath(__file__))
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
D = "https://data.alpaca.markets/v2/stocks/quotes"
DAYS = ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"]
WIN = 3

def sample_times(day):
    ts = list(pd.date_range(f"{day} 09:30:05", f"{day} 10:30:05", freq="1min")) + \
         list(pd.date_range(f"{day} 10:35:05", f"{day} 15:55:05", freq="5min"))
    return [t.tz_localize("America/New_York") for t in ts]

def fetch(args):
    syms, t = args
    s = (t - pd.Timedelta(seconds=WIN)).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    e = t.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    agg, tok = {}, None
    for _ in range(200):
        params = {"symbols": ",".join(syms), "start": s, "end": e, "feed": "sip", "limit": 10000}
        if tok: params["page_token"] = tok
        for attempt in range(5):
            r = requests.get(D, headers=H, params=params, timeout=60)
            if r.status_code == 429: time.sleep(2 + attempt * 2); continue
            r.raise_for_status(); break
        j = r.json()
        for sym, qs in (j.get("quotes") or {}).items():
            agg.setdefault(sym, []).extend(qs)
        tok = j.get("next_page_token")
        if not tok: break
    out = []
    for sym, qs in agg.items():
        bp = np.array([q["bp"] for q in qs], float); ap = np.array([q["ap"] for q in qs], float)
        ok = (bp > 0) & (ap > bp)
        if not ok.any(): continue
        i = np.flatnonzero(ok)[-1]
        sp = ap[ok] - bp[ok]
        out.append({"t": t, "symbol": sym, "bid": bp[i], "ask": ap[i], "bs": qs[i]["bs"], "as": qs[i]["as"],
                    "n_quotes": int(ok.sum()), "med_spread": float(np.median(sp)),
                    "med_spread_bps": float(np.median(sp / ((ap[ok] + bp[ok]) / 2)) * 1e4)})
    return out

if __name__ == "__main__":
    o = pd.read_parquet(os.path.join(HERE, "data", "orders.parquet"))
    syms = sorted(o.loc[o.status == "filled", "symbol"].unique())
    jobs = [(syms, t) for d in DAYS for t in sample_times(d)]
    print(len(syms), "symbols,", len(jobs), "sample times", flush=True)
    rows, t0 = [], time.time()
    with ThreadPoolExecutor(4) as ex:
        for k, res in enumerate(ex.map(fetch, jobs)):
            rows.extend(res)
            if k % 50 == 0: print(k, len(rows), f"{time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(HERE, "data", "nbbo_sample.parquet"))
    print("rows", len(df), f"{time.time()-t0:.0f}s")
