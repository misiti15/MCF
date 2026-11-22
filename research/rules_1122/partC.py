"""Part C: $ vs R reconciliation, Primary journal run 1, sessions 2026-10-23..latest, MTUM trades of 11-05/11-06
excluded (broker corporate-action glitch). Per trade: intended $ risk = |entry - stop| x shares, R = LR8 cost-R
(mcf.costs.cost_r_lr8), $ after LR8 costs = R x $risk, plus the journal's gross pnl and booked pnl_adj.
Identity: $ = sum(R_i x risk_i) = mean(risk) x sum(R) + n x cov(R, risk). Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from common import family, ts

W = Path(sys.argv[1]); OUT = Path(__file__).parent
t = pd.read_parquet(W / "live.parquet")
p = t[(t.account == "primary") & (t.date >= "2026-10-23")].copy()
p = p[~((p.symbol == "MTUM") & p.date.isin(["2026-11-05", "2026-11-06"]))]
G = pd.read_csv(W / "groups.csv").set_index("symbol")
etfs = set(pd.read_csv(Path(sys.argv[2]) / "data/universe.csv").query(
    "name.str.contains('ETF|Trust|Fund|ProShares|Direxion|SPDR|iShares', case=False, na=False)", engine="python").symbol)
p["risk_usd"] = (p.entry - p.stop).abs() * p.shares
p["usd_lr8"] = p.r * p.risk_usd
p["notional"] = p.entry * p.shares
p["inst"] = np.where(p.symbol.isin(etfs), "ETF/ETP", "stock")
p["price_bkt"] = pd.cut(p.entry, [0, 10, 25, 50, 100, 250, 1e9], labels=["<10", "10-25", "25-50", "50-100", "100-250", ">=250"])
p["stop_pct"] = (p.entry - p.stop).abs() / p.entry * 100
p["week"] = pd.to_datetime(p.date).dt.to_period("W-FRI").astype(str)
p["family"] = [family(s, sd) for s, sd in zip(p.strategy, p.side)]
n = len(p)
tot = dict(trades=n, R=p.r.sum(), usd_lr8=p.usd_lr8.sum(), usd_gross_journal=p.pnl.sum(), usd_booked_pnl_adj=p.pnl_adj.sum(),
           mean_risk=p.risk_usd.mean(), median_risk=p.risk_usd.median(), p10_risk=p.risk_usd.quantile(.1),
           p90_risk=p.risk_usd.quantile(.9), max_risk=p.risk_usd.max(), cv_risk=p.risk_usd.std() / p.risk_usd.mean())
tot["usd_if_fixed_mean_risk"] = tot["mean_risk"] * tot["R"]
tot["cov_term"] = tot["usd_lr8"] - tot["usd_if_fixed_mean_risk"]
tot["corr_R_risk"] = p.r.corr(p.risk_usd)
tot["avg_R_small_risk_half"] = p.r[p.risk_usd <= p.risk_usd.median()].mean()
tot["avg_R_large_risk_half"] = p.r[p.risk_usd > p.risk_usd.median()].mean()
print("\n".join(f"{k}: {v:,.3f}" if isinstance(v, float) else f"{k}: {v}" for k, v in tot.items()))
pd.Series(tot).to_csv(OUT / "C_totals.csv")

# deciles of $ risk: how much of the $ result and of the R result each holds
p["risk_dec"] = pd.qcut(p.risk_usd.rank(method="first"), 10, labels=[f"D{i}" for i in range(1, 11)])
dec = p.groupby("risk_dec", observed=True).agg(trades=("r", "size"), risk_lo=("risk_usd", "min"), risk_hi=("risk_usd", "max"),
                                               R=("r", "sum"), avgR=("r", "mean"), usd=("usd_lr8", "sum"),
                                               etf_share=("inst", lambda x: (x == "ETF/ETP").mean()),
                                               med_price=("entry", "median"), med_stop_pct=("stop_pct", "median"))
dec.round(2).to_csv(OUT / "C_risk_deciles.csv")
print(dec.round(2).to_string())
top = p.risk_usd >= p.risk_usd.quantile(0.9)
print(f"top 10% $risk: {top.sum()} trades, R {p.r[top].sum():+.1f}, $ {p.usd_lr8[top].sum():+,.0f}; rest: R {p.r[~top].sum():+.1f}, "
      f"$ {p.usd_lr8[~top].sum():+,.0f}")
rest_fixed = p.risk_usd[~top].mean() * p.r[~top].sum()
print(f"rest at its own mean risk: ${rest_fixed:+,.0f}; whole book at mean risk ${tot['usd_if_fixed_mean_risk']:+,.0f}")
for col in ("strategy", "inst", "price_bkt", "date", "family"):
    g = p.groupby(col, observed=True).agg(trades=("r", "size"), mean_risk=("risk_usd", "mean"), median_risk=("risk_usd", "median"),
                                           p90_risk=("risk_usd", lambda x: x.quantile(.9)), max_risk=("risk_usd", "max"),
                                           R=("r", "sum"), usd=("usd_lr8", "sum"), med_stop_pct=("stop_pct", "median"),
                                           med_notional=("notional", "median"))
    g.round(2).to_csv(OUT / f"C_by_{col}.csv")
    if col != "date":
        print(g.sort_values("trades", ascending=False).head(14).round(1).to_string())
# weekly fixed-risk R series vs cash series
wk = p.groupby("week").agg(trades=("r", "size"), R=("r", "sum"), usd_lr8=("usd_lr8", "sum"), usd_gross=("pnl", "sum"),
                           usd_booked=("pnl_adj", "sum"), mean_risk=("risk_usd", "mean"))
wk["usd_at_fixed_risk"] = wk.R * tot["mean_risk"]
wk["cum_R"], wk["cum_usd_lr8"], wk["cum_usd_fixed"] = wk.R.cumsum(), wk.usd_lr8.cumsum(), wk.usd_at_fixed_risk.cumsum()
wk.round(1).to_csv(OUT / "C_weekly.csv")
print(wk.round(1).to_string())
# largest $-risk trades
cols = ["date", "strategy", "symbol", "inst", "entry", "stop", "shares", "risk_usd", "stop_pct", "r", "usd_lr8", "pnl"]
p.sort_values("risk_usd", ascending=False)[cols].head(25).round(2).to_csv(OUT / "C_top_risk_trades.csv", index=False)
print(p.sort_values("risk_usd", ascending=False)[cols].head(12).round(2).to_string(index=False))
# cost gap: gross journal pnl vs LR8 $
print(f"gross journal ${p.pnl.sum():+,.0f} -> LR8 costs ${(p.pnl - p.usd_lr8).sum():,.0f} -> after costs ${p.usd_lr8.sum():+,.0f}; "
      f"gross R {(p.pnl / p.risk_usd).sum():+.1f}")
