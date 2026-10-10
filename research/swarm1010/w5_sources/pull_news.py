"""Alpaca news history (Benzinga feed), compact: id, created_at, updated_at, headline, symbols, source, author.
DATA ONLY (owner: no news rules yet). Open months of the 2-year history; the rule-19 locked block 2024-11..2025-02
is skipped. Out: data/news/news_YYYY-MM.parquet. Read-only GETs. Educational only - not financial advice."""
import os, sys, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd, requests
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "news"); os.makedirs(OUT, exist_ok=True)
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
LOCKED = ("2024-11-01", "2025-02-28")

def day(d):
    rows, tok = [], None
    s, e = d.strftime("%Y-%m-%dT00:00:00Z"), (d + pd.Timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    while True:
        p = {"start": s, "end": e, "limit": 50, "sort": "asc", "include_content": "false"}
        if tok: p["page_token"] = tok
        for a in range(10):
            try:
                r = requests.get("https://data.alpaca.markets/v1beta1/news", headers=H, params=p, timeout=60)
            except requests.exceptions.RequestException:
                time.sleep(3 + 5 * a); continue
            if r.status_code in (429, 500, 502, 503): time.sleep(2 + 3 * a); continue
            r.raise_for_status(); break
        j = r.json()
        for n in j.get("news", []):
            rows.append({"id": n["id"], "created_at": n["created_at"], "updated_at": n["updated_at"], "headline": n["headline"],
                         "symbols": ",".join(n.get("symbols") or []), "source": n.get("source") or "", "author": n.get("author") or ""})
        tok = j.get("next_page_token")
        if not tok: return rows

if __name__ == "__main__":
    start, end = sys.argv[1] if len(sys.argv) > 1 else "2024-10-01", sys.argv[2] if len(sys.argv) > 2 else "2026-10-09"
    for m in pd.period_range(start[:7], end[:7], freq="M"):
        f = os.path.join(OUT, f"news_{m}.parquet")
        days = [d for d in pd.date_range(max(m.start_time, pd.Timestamp(start)), min(m.end_time.normalize(), pd.Timestamp(end)))
                if not (LOCKED[0] <= str(d.date()) <= LOCKED[1])]
        if not days or os.path.exists(f): continue
        t0 = time.time()
        with ThreadPoolExecutor(3) as ex:
            rows = [x for r in ex.map(day, days) for x in r]
        df = pd.DataFrame(rows).drop_duplicates("id")
        for c in ("created_at", "updated_at"): df[c] = pd.to_datetime(df[c], utc=True)
        df["source"] = df["source"].astype("category")
        df.to_parquet(f, compression="zstd")
        print(m, len(df), f"{os.path.getsize(f)/1e6:.1f}MB", f"{time.time()-t0:.0f}s", flush=True)
