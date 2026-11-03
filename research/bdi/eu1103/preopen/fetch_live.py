"""eu1103/preopen: live-period inputs from Alpaca (read-only GETs): SIP daily bars 2026-08-03..11-02 and the
09:30-09:35 1-minute bars for the 20 live sessions, for the lab universe plus every symbol live traded.
    python fetch_live.py <scratch>  -> <scratch>/live_daily.parquet, <scratch>/live_o5.parquet
Educational only - not financial advice."""
import os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd, requests
sys.path.insert(0, "/home/user/MCF")
from mcf.longhold.data import SipDaily

S = Path(sys.argv[1])
syms = sorted(set((S / "live_syms.txt").read_text().split()))
d = SipDaily().bars(syms, "2026-08-03", "2026-11-03", adjustment="raw")
d.to_parquet(S / "live_daily.parquet", index=False)
days = sorted(x for x in d.date.astype(str).str[:10].unique() if "2026-10-06" <= x <= "2026-11-02")
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}


def get(p):
    w = 1.0
    for _ in range(12):
        try:
            r = requests.get("https://data.alpaca.markets/v2/stocks/bars", params=p, headers=H, timeout=90)
        except requests.RequestException:
            time.sleep(w); w = min(2 * w, 60); continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(w); w = min(2 * w, 60); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError("gave up")


def o5(day):
    a = pd.Timestamp(f"{day} 09:30", tz="America/New_York").tz_convert("UTC")
    b = pd.Timestamp(f"{day} 09:34:59", tz="America/New_York").tz_convert("UTC")
    rows = []
    for i in range(0, len(syms), 200):
        p = {"symbols": ",".join(syms[i:i + 200]), "timeframe": "5Min", "start": a.isoformat(), "end": b.isoformat(),
             "feed": "sip", "adjustment": "raw", "limit": 10000}
        while True:
            j = get(p)
            for s, bs in (j.get("bars") or {}).items():
                rows += [(s, day, x["o"], x["c"], x["v"], x.get("vw", x["c"])) for x in bs]
            t = j.get("next_page_token")
            if not t:
                break
            p["page_token"] = t
    return pd.DataFrame(rows, columns=["symbol", "date", "o5_open", "o5_close", "o5_vol", "o5_vw"])


with ThreadPoolExecutor(4) as ex:
    o = pd.concat(list(ex.map(o5, days)), ignore_index=True)
o.to_parquet(S / "live_o5.parquet", index=False)
(S / "live_days.txt").write_text(",".join(days))
print(len(d), len(o), days)
