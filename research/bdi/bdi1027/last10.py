"""bdi1027: cheap first look at backlog nightly-1027-flatten-1545 on the open two-year history: the move from the 15:45
5-min close to the 15:55 close (the live flatten) for every liquid symbol-day (ADV >= $95M), in R = 0.25 x daily ATR,
long side; a lot still open at 15:45 gains this by holding to 15:55 (costs are identical either way: one exit).
By split, regime, and conditioned on the stock's move from 15:00 to 15:45 (open winners vs losers). 1 descriptive config.
Locked block never read. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
sys.path[:0] = ["/home/user/MCF/research/history2y", "/home/user/MCF/research/bdi/refire1014"]
import lib, scan  # noqa: E401,E402
out = []
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    t = scan.tail_rows(m)
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "atr_d", "adv20"])
    f["symbol"] = f.symbol.astype(str)
    d = f[f.tod == 1500][["symbol", "date", "close", "atr_d", "adv20"]].rename(columns={"close": "c1500"})
    p = t[t.tod.isin([1545, 1555])].pivot_table(index=["symbol", "date"], columns="tod", values="close").reset_index()
    x = d.merge(p, on=["symbol", "date"]).dropna()
    x = x[(x.adv20 >= 95e6) & (x.atr_d > 0)]
    x["r_last10"] = (x[1555] - x[1545]) / (0.25 * x.atr_d)
    x["r_1500_1545"] = (x[1545] - x.c1500) / (0.25 * x.atr_d)
    out.append(x[["symbol", "date", "r_last10", "r_1500_1545"]])
X = pd.concat(out); X["date"] = pd.to_datetime(X.date).dt.date
X["split"] = np.where(X.date <= pd.Timestamp("2025-12-31").date(), "train", "valid")
X["regime"] = X.date.map(lib.regimes()["regime"])
day = X.groupby("date").r_last10.mean()
print(f"symbol-days {len(X)}, sessions {X.date.nunique()}")
print("long R gained by holding 15:45 -> 15:55: mean %+.4f, day-clustered t %.2f, days positive %.0f%%" % (
    X.r_last10.mean(), day.mean() / (day.std(ddof=1) / np.sqrt(len(day))), 100 * (day > 0).mean()))
print(X.groupby("split").r_last10.agg(["size", "mean"]).round(4).to_string())
print(X.groupby("regime").r_last10.agg(["size", "mean"]).round(4).to_string())
X["leg"] = pd.cut(X.r_1500_1545, [-np.inf, -1, 0, 1, np.inf], labels=["<-1R", "-1..0", "0..1", ">1R"])
print("by the stock's 15:00-15:45 move (an open long's state):")
print(X.groupby("leg", observed=True).r_last10.agg(["size", "mean"]).round(4).to_string())
print("\nEducational only - not financial advice.")
