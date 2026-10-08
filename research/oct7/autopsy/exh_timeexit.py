"""exhaustion_short earlier time exit (WHR 10-07 gave back +0.8R after 15:20). 2 configs (15:00, 15:30). Train/valid only,
bars read with end=2026-09-16. Educational only - not financial advice."""
import sys
sys.path.insert(0, ".")
import numpy as np
import pandas as pd
import research.exits.harness as H

def _sym(symbol):
    df = H._store.load(symbol, end="2026-09-16")
    return {str(d): g for d, g in df.groupby(df.index.date)}
H._sym = _sym
H._day = lambda s, d: _sym(s).get(d, pd.DataFrame())
sigs = [s for s in H.load() if "2026-07-15" <= s["date"] <= "2026-09-15" and s["sig"]["strategy"] == "exhaustion_short"]
for v in ({}, {"exit_by": "15:30"}, {"exit_by": "15:00"}):
    for sp in ("train", "valid"):
        r = H.run(sigs, "exhaustion_short", v, split=sp)
        print(v or "base", sp, {k: r[k] for k in ("n", "exp_r", "exp_r_se", "win_rate", "exp_r_ex_best_day", "exit_reasons")})
