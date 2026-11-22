"""Part A: latch dR vs removing the same number of trades at the setup's average R (expected effect of a random trim).
excess = dR - (-(blocked x avg R no-latch)). Positive excess = the latch picks worse-than-average trades.
Educational only - not financial advice."""
import pandas as pd
from pathlib import Path
H = Path(__file__).parent
for tag in ("L", "W"):
    a = pd.read_csv(H / f"A{tag}_per_setup.csv")
    a["blocked"] = a.trades_nolatch - a.trades_latch
    a["rand_dR"] = -a.blocked * a.R_nolatch / a.trades_nolatch
    a["excess"] = a.dR - a.rand_dR
    f = a.groupby("family").agg(blocked=("blocked", "sum"), dR=("dR", "sum"), rand_dR=("rand_dR", "sum"),
                                excess=("excess", "sum"), setups_excess_pos=("excess", lambda x: int((x > 1e-9).sum())),
                                setups_excess_neg=("excess", lambda x: int((x < -1e-9).sum()))).sort_values("excess")
    f.round(1).to_csv(H / f"A{tag}_family_excess.csv")
    print(tag); print(f.round(1).to_string())
    print("ALL", a[["blocked", "dR", "rand_dR", "excess"]].sum().round(1).to_dict())
