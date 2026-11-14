"""NEWSMID data: Alpaca news (headline, symbols, created_at, source; no content) 13:30-21:00 UTC per session (covers
09:30-16:00 ET across the DST change), sessions 2026-10-08..2026-11-09. Market-data GET only; keys from env, never printed.
    python -I fetch.py <out.csv.gz>        Educational only - not financial advice."""
import os, sys, json, gzip, time, urllib.request, urllib.parse, datetime as dt
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def get(q):
    url = "https://data.alpaca.markets/v1beta1/news?" + urllib.parse.urlencode(q)
    for a in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60))
        except Exception: time.sleep(2 ** (a + 1))
    raise RuntimeError("fetch failed")
with gzip.open(sys.argv[1], "wt") as f:
    f.write("id\tcreated_at\tupdated_at\tsource\tsymbols\theadline\n"); n = 0
    d = dt.date(2026, 10, 8)
    while d <= dt.date(2026, 11, 9):
        if d.weekday() < 5:
            tok = None
            while True:
                q = {"start": f"{d}T13:30:00Z", "end": f"{d}T21:00:00Z", "limit": 50, "sort": "asc", "include_content": "false"}
                if tok: q["page_token"] = tok
                j = get(q)
                for i in j["news"]:
                    h = i["headline"].replace("\t", " ").replace("\n", " ")
                    f.write(f"{i['id']}\t{i['created_at']}\t{i['updated_at']}\t{i['source']}\t{'|'.join(i['symbols'])}\t{h}\n"); n += 1
                tok = j.get("next_page_token")
                if not tok: break
            print(d, n, flush=True)
        d += dt.timedelta(days=1)
