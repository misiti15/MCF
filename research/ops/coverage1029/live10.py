"""Live journal (Primary, run 1): signals, distinct symbols and the most repeated symbols per setup over the last N
sessions, and how often a symbol was hit by 2+ of the sister short setups (RW3 / RW5 / MF4-FD / MF2-FD) the same day.
Usage: python live10.py <scratch> [N=10]   Educational only - not financial advice."""
import json, sqlite3, sys
from pathlib import Path

import pandas as pd

S = Path(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 10
c = sqlite3.connect(S / "p" / "journal.db")
J = pd.read_sql("select day, symbol, strategy, status, reason from signals where run_id=1", c)
days = sorted(J.day.unique())[-N:]
J = J[J.day.isin(days)]
P8 = ["RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "MF2-open-rsimidhi-flowsell-FD",
      "MF4-h40-open-flowsell-FD", "MF4-h40-open-flowsell", "ST7-rsi50dn-long-pm-t1s1-FD", "NS1-rsidip-rsi5pop-long",
      "NS5-sma50-flush-oversold-long"]
out = {"days": days, "setups": {}}
for s in P8:
    x = J[J.strategy == s]
    sd = x.drop_duplicates(["day", "symbol"])
    out["setups"][s] = {"signals": len(x), "symbol_days": len(sd), "distinct_symbols": int(x.symbol.nunique()),
                        "submitted": int((x.status == "submitted").sum()),
                        "per_day_symbols": sd.groupby("day").size().reindex(days, fill_value=0).tolist(),
                        "top": sd.symbol.value_counts().head(5).to_dict()}
sis = J[J.strategy.isin(P8[:4])].drop_duplicates(["day", "symbol", "strategy"])
k = sis.groupby(["day", "symbol"]).size()
out["sister_symbol_days"] = int(len(k)); out["sister_symbol_days_2plus"] = int((k >= 2).sum())
out["all8_distinct_symbols"] = int(J[J.strategy.isin(P8)].symbol.nunique())
print(json.dumps(out, indent=1))
(S / "out").mkdir(exist_ok=True); (S / "out" / "live10.json").write_text(json.dumps(out, indent=1))
