"""Fetch 5-min SIP RTH bars for QP1 (Alpaca market-data GET only; keys from env, never printed)."""
import os, sys, time, json, urllib.request, urllib.parse
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
import pandas as pd
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
SYMS = "SPY VXX XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split()
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
RANGES = (("2024-10-01T00:00:00Z", "2024-10-31T23:59:00Z"), ("2025-03-01T00:00:00Z", "2026-11-07T00:00:00Z"))  # two ranges, block never requested
for s in SYMS:
    rows = []
    for a0, b0 in RANGES:
        tok = None
        while True:
            q = {"symbols": s, "timeframe": "5Min", "start": a0, "end": b0, "limit": 10000, "feed": "sip", "adjustment": "split"}
            if tok: q["page_token"] = tok
            req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q), headers=H)
            j = None
            for a in range(4):
                try:
                    j = json.load(urllib.request.urlopen(req, timeout=60)); break
                except RuntimeError: raise                      # the locked-block guard is never retried
                except Exception: time.sleep(2 ** (a + 1))
            if j is None: raise RuntimeError("fetch failed")
            rows += j.get("bars", {}).get(s, []); tok = j.get("next_page_token")
            if not tok: break
    df = pd.DataFrame(rows); df["t"] = pd.to_datetime(df.t, utc=True).dt.tz_convert("America/New_York")
    m = df.t.dt.hour * 60 + df.t.dt.minute; df = df[(m >= 570) & (m < 960)]
    df.to_csv(f"{OUT}/{s}.csv", index=False); print(s, len(df), flush=True)
