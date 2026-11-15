"""SHORTUP data: Alpaca 30-min + daily SIP bars (split-adjusted) for the top-500 adv non-ETF names (universe.csv), 11 SPDRs,
SPY; two ranges around the locked block. GET only; keys from env.
    python -I fetch.py <universe.csv> <out dir>        Educational only - not financial advice."""
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
u = pd.read_csv(sys.argv[1]); O = sys.argv[2]
etf = u.name.str.contains(r"\bETF\b|Trust|Fund|ProShares|iShares|SPDR|Direxion|Invesco|Vanguard|\bShares\b|Leveraged|Bull|Bear", case=False, regex=True)
names = u[~etf & (u.tier == "core")].sort_values("adv_rank").symbol.head(500).tolist()
SY = sorted(set(names) | set("SPY XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split()))
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def get(q):
    req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q), headers=H)
    for a in range(6):
        try: return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception: time.sleep(2 ** (a + 1))
    raise RuntimeError("fetch failed")
for tf, name in (("1Day", "daily"), ("30Min", "m30")):
    with gzip.open(f"{O}/{name}.csv.gz", "wt") as f:
        f.write("symbol,t,o,h,l,c,v\n"); n = 0
        for a, b in (("2024-09-10" if tf == "1Day" else "2024-10-01", "2024-10-31"), ("2025-03-03", "2026-11-13")):
            for i in range(0, len(SY), 100):
                tok = None
                while True:
                    q = {"symbols": ",".join(SY[i:i + 100]), "timeframe": tf, "start": f"{a}T00:00:00Z", "end": f"{b}T23:59:00Z",
                         "limit": 10000, "feed": "sip", "adjustment": "split"}
                    if tok: q["page_token"] = tok
                    j = get(q)
                    for s, bs in (j.get("bars") or {}).items():
                        for x in bs:
                            if tf == "30Min":
                                hm = x["t"][11:16]
                                if not ("13:00" <= hm <= "21:00"): continue      # RTH-ish only (both DST offsets)
                            f.write(f"{s},{x['t']},{x['o']},{x['h']},{x['l']},{x['c']},{x['v']}\n"); n += 1
                    tok = j.get("next_page_token")
                    if not tok: break
                print(name, a, i, n, flush=True)
print("done; names", len(names))
