"""HODSEP data: 5-min SIP RTH bars 2026-09-24..2026-11-09 and daily bars 2026-06-01..2026-11-09 for the lab universe + 11
SPDR sectors + SPY (Alpaca market-data GET only; keys from env, never printed). Open data only (no locked block).
    python fetch.py <out_dir>        Educational only - not financial advice."""
import os, sys, time, json, gzip, urllib.request, urllib.parse
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
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
syms = [s.strip() for s in open("/home/user/MCF/research/lab_symbols.txt") if s.strip()]
syms = sorted(set(syms) | set("SPY XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split()))
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def get(q):
    req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q), headers=H)
    for a in range(5):
        try: return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception: time.sleep(2 ** (a + 1))
    raise RuntimeError("fetch failed")
for tf, start, name in (("1Day", "2026-06-01", "daily"), ("5Min", "2026-09-24", "m5")):
    with gzip.open(f"{OUT}/{name}.csv.gz", "wt") as f:
        f.write("symbol,t,o,h,l,c,v\n"); n = 0
        for i in range(0, len(syms), 100):
            tok = None
            while True:
                q = {"symbols": ",".join(syms[i:i + 100]), "timeframe": tf, "start": f"{start}T00:00:00Z",
                     "end": "2026-11-10T00:00:00Z", "limit": 10000, "feed": "sip", "adjustment": "split"}
                if tok: q["page_token"] = tok
                j = get(q)
                for s, bs in (j.get("bars") or {}).items():
                    for b in bs: f.write(f"{s},{b['t']},{b['o']},{b['h']},{b['l']},{b['c']},{b['v']}\n"); n += 1
                tok = j.get("next_page_token")
                if not tok: break
            print(name, i, n, flush=True)
print("done")
