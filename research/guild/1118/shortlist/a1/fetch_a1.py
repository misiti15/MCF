"""A1 data (Lead lead-20261118-0300-1): Alpaca 5-min SIP bars 09:30-16:00 ET for the Move Hunt catalogue non-blackout symbol-days.
GET only; keys from env; checklist #43 guard below. python3 -I fetch_a1.py <moves.csv> <out.csv.gz>   Educational only - not financial advice."""
import os, sys, time, json, gzip, re, urllib.request, urllib.parse, pandas as pd
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
from zoneinfo import ZoneInfo
ET = ZoneInfo('America/New_York')
m = pd.read_csv(sys.argv[1]); m = m[(m.set == 'all') & (~m.blackout)]
assert not m.date.between('2024-11-01', '2025-02-28').any()
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def get(q):
    req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q), headers=H)
    for a in range(6):
        try: return json.load(urllib.request.urlopen(req, timeout=90))
        except RuntimeError: raise
        except Exception: time.sleep(2 ** (a + 1))
    raise RuntimeError("fetch failed")
rows = []
for d, g in m.groupby('date'):
    sy = sorted(g.symbol.unique())
    s = pd.Timestamp(f"{d} 09:30", tz=ET).tz_convert('UTC').strftime('%Y-%m-%dT%H:%M:%SZ')
    e = pd.Timestamp(f"{d} 15:59", tz=ET).tz_convert('UTC').strftime('%Y-%m-%dT%H:%M:%SZ')
    for i in range(0, len(sy), 100):
        tok = None
        while True:
            q = {"symbols": ",".join(sy[i:i + 100]), "timeframe": "5Min", "start": s, "end": e, "limit": 10000, "feed": "sip", "adjustment": "split"}
            if tok: q["page_token"] = tok
            j = get(q)
            for sym, bs in (j.get("bars") or {}).items():
                rows += [(d, sym, x["t"], x["o"], x["h"], x["l"], x["c"], x["v"]) for x in bs]
            tok = j.get("next_page_token")
            if not tok: break
pd.DataFrame(rows, columns=['date', 'symbol', 't', 'o', 'h', 'l', 'c', 'v']).to_csv(sys.argv[2], index=False, compression='gzip')
print('symbol-days requested', len(m.groupby(['date', 'symbol'])), 'bars', len(rows))
