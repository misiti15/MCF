"""top20 (2026-11-06): live trades (reports/<date>.csv, run_id 1) for Primary, Testing 1, Testing 2, Graveyard, Live Lab and Explore 1 on
their data branches, plus Alpaca market-data GET only: daily bars for every traded symbol (2026-07-01..today, for
point-in-time gap / ADV / price / ATR% / beta) and 1-minute SPY bars for every live date.
Usage: python fetch_live.py <scratch>. Educational only - not financial advice."""
import io, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.bars import normalize, rth
from mcf.data.priors import _bars, _client

ROOT = "/home/user/MCF"; S = Path(sys.argv[1])
BR = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2", "graveyard": "mcf-data-graveyard",
      "livelab": "mcf-data-livelab", "explore1": "mcf-data-explore1"}  # 11-05: ROLL1 low-rep homes
fr = []
for a, b in BR.items():
    names = subprocess.check_output(["git", "-C", ROOT, "ls-tree", "--name-only", f"origin/{b}", "reports/"]).decode().split()
    for p in names:
        if not p.endswith(".csv") or not p[8:18].startswith("2026"):
            continue
        t = pd.read_csv(io.BytesIO(subprocess.check_output(["git", "-C", ROOT, "show", f"origin/{b}:{p}"])))
        t["acct"] = a
        fr.append(t)
T = pd.concat(fr, ignore_index=True)
T = T[(T.run_id == 1) & T.r_multiple.notna()]
T.to_parquet(S / "trades.parquet")
print("trades", len(T), T.date.min(), T.date.max())
dc = _client()
syms = sorted(set(T.symbol) | {"SPY", "QQQ"})
D = _bars(dc, syms, datetime(2026, 7, 1), datetime(2026, 11, 7), None, "sip")
D = D.reset_index()
D.to_parquet(S / "daily.parquet")
print("daily", len(D), D.symbol.nunique())
fr = []
for d in sorted(T.date.unique()):
    a = datetime.combine(pd.Timestamp(d).date(), datetime.min.time()) + timedelta(hours=13)
    raw = _bars(dc, ["SPY"], a, a + timedelta(hours=8), 1, "sip")
    x = rth(normalize(raw.droplevel(0)))
    fr.append(x.reset_index().rename(columns={"index": "ts", "timestamp": "ts"}))
M = pd.concat(fr, ignore_index=True)
M.to_parquet(S / "spy_1m.parquet")
print("spy 1m", len(M))
