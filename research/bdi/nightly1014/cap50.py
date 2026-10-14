"""Testing 2 per-setup cap 25 -> 50 (#55): trades taken while their setup already had >= 25 open lots (would have been
skipped at cap 25), and their P/L. Journal times; lots in the same poll counted in entry order. Educational only."""
import pandas as pd
T = pd.read_csv("trades.csv"); T = T[T.acct == "t2"].copy()
for c in ("nt", "et"):
    T[c] = pd.to_datetime(T[c], utc=True)
T = T.sort_values("nt")
T["open_same_setup"] = [int(((T.strategy == r.strategy) & (T.nt < r.nt) & (T.et > r.nt)).sum()) for r in T.itertuples()]
x = T[T.open_same_setup >= 25]
print("max open per setup:", T.groupby("strategy").open_same_setup.max().sort_values().tail(5).to_dict())
print(f"trades above cap 25: {len(x)}, win {100 * (x.pnl > 0).mean():.0f}%, avgR {x.r_multiple.mean():.3f}, P/L {x.pnl.sum():.2f}")
print(x.groupby("strategy").agg(n=("pnl", "size"), avgR=("r_multiple", "mean"), pnl=("pnl", "sum")).round(3).to_string())
