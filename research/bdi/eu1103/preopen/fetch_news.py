"""eu1103/preopen: overnight news counts from Alpaca's news API (/v1beta1/news, Benzinga feed), read-only GET.
Per session date D: articles created in (previous session 16:00 ET, D 09:30 ET], counted per tagged symbol.
Same dates as fetch_pm.py (locked block 2024-11-01..2025-02-28 never requested, asserted).
    python fetch_news.py <scratch> hist | live <symfile> <dates>   -> <scratch>/news/<mode>_<date>.parquet
Educational only - not financial advice."""
import os, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd, requests

S = Path(sys.argv[1]) / "news"; S.mkdir(parents=True, exist_ok=True)
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
URL = "https://data.alpaca.markets/v1beta1/news"


def get(p):
    w = 1.0
    for _ in range(12):
        try:
            r = requests.get(URL, params=p, headers=H, timeout=90)
        except requests.RequestException:
            time.sleep(w); w = min(2 * w, 60); continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(w); w = min(2 * w, 60); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError("gave up")


def fetch(day, prev, syms):
    a = pd.Timestamp(f"{prev} 16:00", tz="America/New_York").tz_convert("UTC")
    b = pd.Timestamp(f"{day} 09:30", tz="America/New_York").tz_convert("UTC")
    a = max(a, pd.Timestamp("2025-03-01", tz="America/New_York").tz_convert("UTC")) if day >= "2025-03-01" else a
    cnt, seen, U = Counter(), set(), set(syms)
    for i in range(0, len(syms), 100):
        p = {"symbols": ",".join(syms[i:i + 100]), "start": a.isoformat(), "end": b.isoformat(), "limit": 50,
             "include_content": "false", "exclude_contentless": "false"}
        while True:
            j = get(p)
            for n in j.get("news", []):
                if n["id"] in seen:
                    continue
                seen.add(n["id"])
                for s in n.get("symbols", []):
                    if s in U:
                        cnt[s] += 1
            t = j.get("next_page_token")
            if not t:
                break
            p["page_token"] = t
    return pd.DataFrame({"symbol": list(cnt), "news_n": list(cnt.values()), "date": day})


if __name__ == "__main__":
    mode = sys.argv[2]
    sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
    if mode == "hist":
        dd = lib.daily(include_locked=False); dd["d"] = dd.date.astype(str)
        alld = sorted(dd.d.unique())
        mon = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
        days = [x for x in alld if x[:7] in mon and x <= "2026-09-15"]
        syms = sorted(dd.symbol.astype(str).unique())
        # previous session from the full calendar (SPY daily bars, locked dates only as calendar labels, no data)
        cal = sorted(pd.read_parquet(lib.DATA / "daily.parquet", columns=["date"]).date.astype(str).unique())
    else:
        syms = sorted(set(Path(sys.argv[3]).read_text().split())); days = sys.argv[4].split(",")
        cal = sorted(set(sys.argv[5].split(",")))
    prev = {d: cal[cal.index(d) - 1] for d in days}

    def job(d):
        assert not ("2024-11-01" <= d <= "2025-02-28"), d
        p = S / f"{mode}_{d}.parquet"
        if not p.exists():
            fetch(d, prev[d], syms).to_parquet(p, index=False)
        return d
    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        for k, d in enumerate(ex.map(job, days)):
            if k % 20 == 0:
                print(d, k, len(days), f"{time.time() - t0:.0f}s", flush=True)
