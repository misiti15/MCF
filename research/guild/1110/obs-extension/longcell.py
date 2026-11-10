"""Observer: Skeptic's challenge to the 'longs at a fresh high' cell (skeptic-20261109-2250-1). Descriptive, 0 new configs:
reads extension.py's rows (EXT 0.10 ATR, written with: python extension.py <jdir> 0.10 <rows.csv>) + SPY 1-min bars.
gross_atr = gross R x risk/ATR (price terms, before paper costs); ex_spy_atr = (name return - SPY return over the same hold) in ATR
(beta 1). SPY day type by SPY close vs 09:30 open: up > +0.30%, down < -0.30%, else quiet (hindsight label, descriptive only).
usage: python longcell.py <rows.csv>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
pd.set_option("display.width", 220)
X = pd.read_csv(sys.argv[1]); X["et"] = pd.to_datetime(X.et, utc=True).dt.tz_convert("America/New_York")
X["xt"] = pd.to_datetime(X.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
spy = pd.read_parquet("data/cache_hist/1Min/SPY.parquet"); spy = spy.between_time("09:30", "15:59")
spy["d"] = spy.index.date; dd = spy.groupby("d").agg(o=("open", "first"), c=("close", "last"))
dd["ret"] = dd.c / dd.o - 1; dd["dtype"] = np.select([dd.ret > 0.003, dd.ret < -0.003], ["up", "down"], "quiet")
px = spy.close
def at(t): i = px.index.searchsorted(t.floor("min"), side="right") - 1; return px.iloc[max(i, 0)]
X["spy_ret"] = [at(b) / at(a) - 1 for a, b in zip(X.et, X.xt)]
X["dtype"] = X.et.dt.date.map(dd.dtype)
X["gross_atr"] = X.gross * X.risk_atr
X["ex_spy_atr"] = X.side * ((X.exit / X.entry - 1) - X.spy_ret) * X.entry / X.atr
L = X[X.side == 1]
f = lambda g: pd.Series(dict(n=len(g), gross_R=g.gross.mean(), median_R=g.gross.median(), gross_atr=g.gross_atr.mean(),
                             move_atr=g.move_atr.mean(), ex_spy_atr=g.ex_spy_atr.mean(), risk_atr_med=g.risk_atr.median(), days=g.date.nunique()))
print(f"LONG trades {len(L)}; EXT threshold 0.10 ATR\n\n(1) units:\n", L.groupby("grp").apply(f).round(3).to_string())
print("\n(2) by SPY day type:\n", L.groupby(["dtype", "grp"]).apply(f).round(3).to_string())
e = L[L.grp == "EXT"]; day = e.groupby("date").gross.sum()
print(f"\n(3) EXT longs: best day {day.idxmax()} = {day.max():+.1f}R of {day.sum():+.1f}R total ({day.max() / day.sum():.0%} share)" if day.sum() > 0 else f"\n(3) EXT longs total {day.sum():+.1f}R (not positive)")
print("    EXT longs by family:\n", e.groupby("fam").agg(n=("gross", "size"), gross_R=("gross", "mean"), gross_atr=("gross_atr", "mean"), sumR=("gross", "sum")).sort_values("n", ascending=False).head(8).round(3).to_string())
print(f"    CWT12+CWT14 share of EXT longs: {e.fam.isin(['CWT12', 'CWT14']).mean():.0%}")
# Skeptic's convincer: EXT minus PB longs > 0 in ATR units on up AND down days, day-clustered
for col in ("gross_atr", "ex_spy_atr"):
    print(f"\nEXT minus PB longs, {col}, day-clustered:")
    for dt in ("up", "down", "quiet", "all"):
        s = L if dt == "all" else L[L.dtype == dt]
        g = s.groupby(["date", "grp"])[col].mean().unstack()
        if "EXT" not in g or "PB" not in g: continue
        diff = (g.EXT - g.PB).dropna()
        t = diff.mean() / (diff.std() / np.sqrt(len(diff))) if len(diff) > 1 else np.nan
        print(f"  {dt:5s}: days {len(diff):2d}  mean {diff.mean():+.4f}  t {t:+.2f}  days>0 {int((diff > 0).sum())}")
print("Educational only - not financial advice.")
