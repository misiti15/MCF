"""eu1103/preopen: pre-market (04:00-09:30 ET) SIP 30-minute bars from Alpaca, aggregated per symbol-day.
Read-only GET on data.alpaca.markets/v2/stocks/bars (the live runner's own data plan); keys from env, never printed.
Dates: TRAIN 2024-10 + 2025-03..12, VALID 2026-01..03 + 2026-07-01..09-15 (lab universe), and the live sessions
(symbols passed in a file). The rule-19 locked block 2024-11-01..2025-02-28 is never requested (asserted).
    python fetch_pm.py <scratch> hist            -> <scratch>/pm/<date>.parquet
    python fetch_pm.py <scratch> live <symfile> <date1,date2,...>
Columns: symbol, date, pm_vol, pm_dvol (sum v*vw), pm_hi, pm_lo, pm_open (first bar open), pm_last (last close),
pm_vol_late (08:00-09:30 volume), pm_nbars. Educational only - not financial advice."""
import os, sys, time
from pathlib import Path
import pandas as pd, requests

S = Path(sys.argv[1]) / "pm"; S.mkdir(parents=True, exist_ok=True)
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
URL = "https://data.alpaca.markets/v2/stocks/bars"


def get(params):
    w = 1.0
    for _ in range(12):
        try:
            r = requests.get(URL, params=params, headers=H, timeout=90)
        except requests.RequestException:
            time.sleep(w); w = min(2 * w, 60); continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(w); w = min(2 * w, 60); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError("gave up")


def fetch_day(day, syms):
    a = pd.Timestamp(f"{day} 04:00", tz="America/New_York").tz_convert("UTC")
    b = pd.Timestamp(f"{day} 09:29:59", tz="America/New_York").tz_convert("UTC")
    rows = []
    for i in range(0, len(syms), 200):
        p = {"symbols": ",".join(syms[i:i + 200]), "timeframe": "30Min", "start": a.isoformat(), "end": b.isoformat(),
             "feed": "sip", "adjustment": "raw", "limit": 10000}
        while True:
            j = get(p)
            for s, bs in (j.get("bars") or {}).items():
                rows += [(s, x["t"], x["o"], x["h"], x["l"], x["c"], x["v"], x.get("vw", x["c"])) for x in bs]
            t = j.get("next_page_token")
            if not t:
                break
            p["page_token"] = t
    if not rows:
        return pd.DataFrame()
    d = pd.DataFrame(rows, columns=["symbol", "t", "o", "h", "l", "c", "v", "vw"])
    d["t"] = pd.to_datetime(d.t, utc=True).dt.tz_convert("America/New_York")
    d = d.sort_values(["symbol", "t"])
    d["dv"] = d.v * d.vw
    late = d.t.dt.hour >= 8
    g = d.groupby("symbol")
    out = pd.DataFrame({"pm_vol": g.v.sum(), "pm_dvol": g.dv.sum(), "pm_hi": g.h.max(), "pm_lo": g.l.min(),
                        "pm_open": g.o.first(), "pm_last": g.c.last(), "pm_nbars": g.size(),
                        "pm_vol_late": d[late].groupby("symbol").v.sum()}).fillna({"pm_vol_late": 0}).reset_index()
    out["date"] = day
    return out


def locked(day):
    return "2024-11-01" <= day <= "2025-02-28"


if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "hist":
        sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
        dd = lib.daily(); dd["d"] = dd.date.astype(str)
        mon = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
        days = sorted(x for x in dd.d.unique() if x[:7] in mon and x <= "2026-09-15")
        syms = sorted(dd.symbol.astype(str).unique())
    else:
        syms = sorted(set(Path(sys.argv[3]).read_text().split())); days = sys.argv[4].split(",")
    t0 = time.time()
    from concurrent.futures import ThreadPoolExecutor   # network-bound; one process, one core

    def job(day):
        assert not locked(day), day
        p = S / f"{mode}_{day}.parquet"
        if not p.exists():
            fetch_day(day, syms).to_parquet(p, index=False)
        return day

    with ThreadPoolExecutor(6) as ex:
        for k, day in enumerate(ex.map(job, days)):
            if k % 10 == 0:
                print(day, k, len(days), f"{time.time() - t0:.0f}s", flush=True)
