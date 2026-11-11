"""Observer: live cross-check of the minute-10 exit question (Lead lead-20261111-0300-1, measured on LIVE trades; Builder measures the lab).
For each live paper trade still open at entry+10 min: 'triggered' = price reached entry + side x k x D within the first 10 minutes
(1-min highs/lows, D = |entry - stop|), k in {0.10, 0.25} as CONFIRM. Quantity of interest (Skeptic): the gross move AFTER minute 10,
cont = side x (live exit price - close of the 10th minute) / daily ATR. ~0 for untriggered trades = martingale -> a minute-10 exit only adds cost.
Descriptive, 0 configs. Bars: data/cache_hist/1Min (RTH, through 11-10). usage: python min10.py <journal_dir>. Educational only - not financial advice."""
import sys, glob, os, sqlite3, numpy as np, pandas as pd
from pathlib import Path
pd.set_option("display.width", 220); TZ = "America/New_York"; BARS = Path("data/cache_hist/1Min")
R = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.db"))):
    a = os.path.basename(f).replace("mcf-data-", "").replace(".db", "").replace("mcf-data", "primary")
    t = pd.read_sql("select date,symbol,strategy,side,entry_time,exit_time,entry,stop,exit from trades where run_id=1 and exit is not null", sqlite3.connect(f))
    t["acct"] = a; R.append(t)
T = pd.concat(R, ignore_index=True)
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ); T["xt"] = pd.to_datetime(T.exit_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["D"] = (T.entry - T.stop).abs(); T = T[T.D > 0]
out, bad = [], []
for sym, g in T.groupby("symbol"):
    p = BARS / f"{sym}.parquet"
    if not p.exists(): continue
    b = pd.read_parquet(p).between_time("09:30", "15:59"); b["d"] = b.index.date
    day = b.groupby("d").agg(h=("high", "max"), l=("low", "min"), c=("close", "last"))
    day["atr"] = (np.maximum(day.h, day.c.shift(1)) - np.minimum(day.l, day.c.shift(1))).shift(1).rolling(10, min_periods=5).mean()
    for i, r in g.iterrows():
        d = r.et.date(); e0 = r.et.floor("min")
        if d not in day.index or not np.isfinite(day.at[d, "atr"]) or r.xt <= r.et + pd.Timedelta(minutes=10): continue
        w = b[(b.index >= e0) & (b.index < e0 + pd.Timedelta(minutes=10))]
        if len(w) < 8: continue
        if abs(w.close.iloc[0] / r.entry - 1) > 0.03: bad.append(sym); continue      # split-adjusted bars vs unadjusted live prices
        fav = (w.high.max() - r.entry) if r.side == 1 else (r.entry - w.low.min())
        c10 = w.close.iloc[-1]
        out.append(dict(i=i, atr=day.at[d, "atr"], fav_D=fav / r.D, c10=c10,
                        cont=r.side * (r.exit - c10) / day.at[d, "atr"], first10=r.side * (c10 - r.entry) / day.at[d, "atr"]))
X = T.join(pd.DataFrame(out).set_index("i"), how="inner")
X["fam"] = X.strategy.str.extract(r"^(GEN|[A-Za-z]+\d*)")[0]
print(f"live trades open at minute 10 with bars: {len(X)} of {len(T)} ({X.date.min()}..{X.date.max()}), setups {X.strategy.nunique()}; "
      f"dropped {len(bad)} trades whose entry-minute bar is > 3% from the fill (split-adjusted bars: {sorted(set(bad))})")
def dt(s, by):
    d = s.groupby(by).mean(); return d.mean(), d.mean() / (d.std() / np.sqrt(len(d))), len(d)
for k in (0.10, 0.25):
    X["trig"] = X.fav_D >= k
    print(f"\nk {k}: triggered share {X.trig.mean():.0%}")
    for lab, z in (("triggered", X[X.trig]), ("untriggered", X[~X.trig])):
        m, t, n = dt(z.cont, z.date); m1, t1, _ = dt(z.first10, z.date)
        print(f"   {lab:11s} n {len(z):5d}: first-10-min move {m1:+.4f} ATR (t {t1:+.2f}); AFTER minute 10 to live exit {m:+.4f} ATR (day-t {t:+.2f}, days {n}); median {z.cont.median():+.4f}")
    U = X[~X.trig]
    F = U.groupby("fam").agg(n=("cont", "size"), cont=("cont", "mean"), median=("cont", "median"), days=("date", "nunique")).query("n >= 30").sort_values("cont")
    print(f"   untriggered by family (n >= 30): {len(F)} families; after-minute-10 < 0 in {int((F.cont < 0).sum())}, > 0 in {int((F.cont > 0).sum())}")
    print(F.round(4).to_string())
print("\nReading: a minute-10 exit on untriggered trades helps only if their AFTER-minute-10 move is clearly < 0 (and beats exit cost ~0.01-0.02 ATR).")
print("Educational only - not financial advice.")
