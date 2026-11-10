"""BURST2 live inputs: all 7 journals 2026-10-06..2026-11-06 -> <scratch>/live_trades.parquet (run_id 1 + run_id 2
what-ifs blocked by the per-setup latch or the account halt), 5-min SIP bars for traded symbols (reuses BURST1's file for
10-06..11-05, fetches 11-06), 1-min SPY / QQQ per live date. GET-only market data.
Usage: python live.py <journals dir n1106> <burst1 scratch> <out scratch>   Educational only - not financial advice."""
import os, sys, sqlite3, requests
from pathlib import Path
import numpy as np, pandas as pd
J, B1, S = map(Path, sys.argv[1:4]); TZ = "America/New_York"
AC = dict(p="primary", t1="testing", t2="testing2", gy="graveyard", gen="gen", ex1="explore1", ll="livelab")
rows = []
for a, name in AC.items():
    c = sqlite3.connect(J / a / "journal.db")
    t = pd.read_sql("select * from trades where date>='2026-10-06' and date<='2026-11-06' and exit is not null", c)
    w = t.meta.fillna("").str.extract(r"why=([^;]*)")[0].fillna("")
    t["why"] = np.where(t.run_id == 2, w, None)
    t = t[(t.run_id == 1) | ((t.run_id == 2) & (w.str.contains("setup daily loss limit") | w.str.startswith("halted")))].copy()
    t["account"] = name; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["risk"] = (T.entry - T.stop).abs() * T.shares
T["R"] = np.where(T.run_id == 1, T.pnl_adj / T.risk.replace(0, np.nan), T.r_multiple)
T = T[T.R.notna()]
T["blocked_live"] = T.run_id == 2
for x, y in (("ent_ts", "entry_time"), ("ext_ts", "exit_time")):
    T[x] = pd.to_datetime(T[y], utc=True, format="mixed").dt.tz_convert(TZ)
T["ent"] = T.ent_ts.dt.hour * 60 + T.ent_ts.dt.minute; T["ext"] = T.ext_ts.dt.hour * 60 + T.ext_ts.dt.minute
T["stop_pct"] = (T.entry - T.stop).abs() / T.entry
T = T.drop(columns=["meta"]); T.to_parquet(S / "live_trades.parquet")
print(T.groupby(["account", "run_id"]).size().unstack(), T.date.max())
h = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}


def get(syms, d, tf):
    out = []
    for i in range(0, len(syms), 100):
        tok = None
        while True:
            p = dict(symbols=",".join(syms[i:i + 100]), timeframe=tf, start=f"{d}T13:30:00Z", end=f"{d}T21:00:00Z", feed="sip", limit=10000, adjustment="raw")
            if tok: p["page_token"] = tok
            r = requests.get("https://data.alpaca.markets/v2/stocks/bars", params=p, headers=h, timeout=60); r.raise_for_status(); j = r.json()
            for s, bs in (j.get("bars") or {}).items():
                out += [(d, s, x["t"], x["o"], x["h"], x["l"], x["c"], x["v"]) for x in bs]
            tok = j.get("next_page_token")
            if not tok: break
    return out


B = pd.read_parquet(B1 / "live_bars5.parquet")
d = "2026-11-06"; g = T[T.date == d]
new = pd.DataFrame(get(sorted(set(g.symbol) | {"SPY", "QQQ", "IWM"}), d, "5Min"), columns=["date", "symbol", "t", "o", "h", "l", "c", "v"])
new["t"] = pd.to_datetime(new.t).dt.tz_convert(TZ)
B = pd.concat([B[B.date != d], new], ignore_index=True); B.to_parquet(S / "live_bars5.parquet")
I = []
for d in sorted(T.date.unique()):
    I += get(["SPY", "QQQ"], d, "1Min")
I = pd.DataFrame(I, columns=["date", "symbol", "t", "o", "h", "l", "c", "v"]); I["t"] = pd.to_datetime(I.t).dt.tz_convert(TZ)
I.to_parquet(S / "live_idx1.parquet"); print(len(B), len(I))
