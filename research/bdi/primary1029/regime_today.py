"""Class 2026-10-29 up / flat / down with the history's own rule (median open-to-close of the lab universe, tercile cut
points from the open two-year history, mcf.research.gates.session_regimes), from SIP 30-min bars (read-only market data).
Usage: python regime_today.py <scratch-pr29>   Educational only - not financial advice."""
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/history2y")
from mcf.data.alpaca_data import _client, fetch_bars
import lib
S = Path(sys.argv[1])
syms = [x.strip() for x in Path("/home/user/MCF/research/lab_symbols.txt").read_text().split() if x.strip()]
cl = _client(); a, b = datetime(2026, 10, 29, 13, 30, tzinfo=timezone.utc), datetime(2026, 10, 29, 20, 0, tzinfo=timezone.utc)
rows = []
for i in range(0, len(syms), 200):
    for s, g in fetch_bars(syms[i:i + 200], a, b, feed="sip", minutes=30, client=cl).items():
        if len(g):
            rows.append((s, float(g.open.iloc[0]), float(g.close.iloc[-1])))
d = pd.DataFrame(rows, columns=["symbol", "open", "close"])
med = float(np.median((d.close / d.open - 1) * 100))
cuts = lib.regimes().attrs.get("cuts")
print(f"symbols {len(d)}, median open-to-close {med:+.3f}% ; history tercile cuts {cuts}")
lo, hi = cuts
print("regime:", "down" if med <= lo else ("up" if med >= hi else "flat"))
print("share of universe up on the day:", round(float((d.close > d.open).mean()), 3))
