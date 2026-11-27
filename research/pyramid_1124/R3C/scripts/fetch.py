"""R3C: for every live stop / market exit, the SIP 1-min bar open of the exit minute (Alpaca GET only; nothing but
per-trade numbers is kept). Educational only - not financial advice."""
import sys, os
from datetime import datetime
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX)
from mcf.data.priors import _bars, _client
HERE = os.path.dirname(os.path.abspath(__file__))
t = pd.read_parquet(HERE + "/live.parquet")
t = t[t.exit_reason.isin(["stop", "flatten", "timestop", "spy_exit", "scaled+breakeven", "scaled+flatten"])].copy()
t["xts"] = pd.to_datetime(t.exit_time.astype(str), utc=True, format="mixed").dt.floor("min")
dc = _client(); out = []
for d, g in t.groupby("date"):
    syms = sorted(g.symbol.unique())
    a = datetime.fromisoformat(d + "T13:00:00+00:00"); b = datetime.fromisoformat(d + "T21:05:00+00:00")
    raw = _bars(dc, syms, a, b, 1, "sip")
    if raw.empty: print(d, "empty", flush=True); continue
    raw = raw.reset_index()
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], utc=True)
    m = g[["k", "symbol", "xts"]].merge(raw[["symbol", "timestamp", "open", "high", "low", "close"]],
                                         left_on=["symbol", "xts"], right_on=["symbol", "timestamp"], how="left")
    m = m[["k", "open", "high", "low", "close"]].rename(columns=lambda c: c if c == "k" else "x_" + c); out.append(m)
    print(d, len(syms), int(m.x_open.notna().sum()), "/", len(m), flush=True)
pd.concat(out).to_parquet(HERE + "/exitbars.parquet")
