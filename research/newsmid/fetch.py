"""NEWSMID data: Alpaca news (headline, symbols, created_at, source; no content) 13:30-21:00 UTC per session (covers
09:30-16:00 ET across the DST change), sessions 2026-10-08..2026-11-09. Market-data GET only; keys from env, never printed.
    python -I fetch.py <out.csv.gz>        Educational only - not financial advice."""
import os, sys, json, gzip, time, urllib.request, urllib.parse, datetime as dt
# --- checklist #43 (Lead 2026-11-15): refuse any request whose date range touches the locked block 2024-11-01..2025-02-28 ---
import urllib.parse as _lk_up, urllib.request as _lk_ur
_lk_real_urlopen = _lk_ur.urlopen
def _lk_guarded_urlopen(req, *a, **k):
    u = req.full_url if hasattr(req, "full_url") else str(req)
    q = dict(_lk_up.parse_qsl(_lk_up.urlsplit(u).query))
    s, e = q.get("start", "")[:10], q.get("end", "")[:10]
    if (s and e and not (e < "2024-11-01" or s > "2025-02-28")) or (s and not e and s <= "2025-02-28"):
        raise RuntimeError(f"locked block: request {s}..{e or 'open'} overlaps 2024-11-01..2025-02-28 (checklist #43)")
    return _lk_real_urlopen(req, *a, **k)
_lk_ur.urlopen = _lk_guarded_urlopen
# --- end checklist #43 ---
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
