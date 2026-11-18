"""HKS950 15:30-15:55 re-cut data (Lead lead-20261117-1900-3): Alpaca 1-min SIP bars 15:29-15:59 ET only, the m30 names and days.
GET only; keys from env; checklist #43 guard below. python3 -I fetch_close.py <m30.csv.gz> <outdir>   Educational only - not financial advice."""
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
# HKS950 15:30-15:55 re-cut (Lead lead-20261117-1900-3): 1-min bars 15:29-15:59 ET only, same names and days as m30. Resumable per day.
# usage: python3 -I fetch_close.py <m30.csv.gz> <outdir>      Educational only - not financial advice.
from zoneinfo import ZoneInfo
m = pd.read_csv(sys.argv[1], usecols=['symbol', 't']); O = sys.argv[2]; os.makedirs(O, exist_ok=True)
ET = ZoneInfo('America/New_York')
m['day'] = pd.to_datetime(m.t, utc=True).dt.tz_convert(ET).dt.date.astype(str)
SY = sorted(m.symbol.unique()); DAYS = sorted(set(m.day) - {'2025-07-03', '2025-11-28', '2025-12-24'})
assert not any('2024-11-01' <= d <= '2025-02-28' for d in DAYS)
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def get(q):
    req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q), headers=H)
    for a in range(6):
        try: return json.load(urllib.request.urlopen(req, timeout=90))
        except RuntimeError: raise
        except Exception: time.sleep(2 ** (a + 1))
    raise RuntimeError("fetch failed")
for d in DAYS:
    fn = f"{O}/{d}.csv.gz"
    if os.path.exists(fn): continue
    s = pd.Timestamp(f"{d} 15:29", tz=ET).tz_convert('UTC').strftime('%Y-%m-%dT%H:%M:%SZ')
    e = pd.Timestamp(f"{d} 15:59", tz=ET).tz_convert('UTC').strftime('%Y-%m-%dT%H:%M:%SZ')
    rows = []
    for i in range(0, len(SY), 100):
        tok = None
        while True:
            q = {"symbols": ",".join(SY[i:i + 100]), "timeframe": "1Min", "start": s, "end": e, "limit": 10000, "feed": "sip", "adjustment": "split"}
            if tok: q["page_token"] = tok
            j = get(q)
            for sym, bs in (j.get("bars") or {}).items():
                rows += [(sym, x["t"], x["c"]) for x in bs]
            tok = j.get("next_page_token")
            if not tok: break
    pd.DataFrame(rows, columns=['symbol', 't', 'c']).to_csv(fn + '.tmp', index=False, compression='gzip'); os.replace(fn + '.tmp', fn)
print('done', len(DAYS))
