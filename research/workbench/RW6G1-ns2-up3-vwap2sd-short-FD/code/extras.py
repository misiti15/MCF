"""Day-type split (SPY 09:30 open -> 16:00 close: up > +0.3%, down < -0.3%, else flat) per config/test from trades_*.pkl."""
import sys, glob, pandas as pd
s = pd.read_parquet("spy1m.parquet"); s.index = pd.DatetimeIndex(s.index).tz_convert("America/New_York")
s = s[(s.index.hour * 60 + s.index.minute >= 570) & (s.index.hour * 60 + s.index.minute < 960)]
g = s.groupby(s.index.strftime("%Y-%m-%d")); oc = (g.close.last() / g.open.first() - 1) * 100
typ = oc.map(lambda x: "up" if x > 0.3 else ("down" if x < -0.3 else "flat"))
rows = []
for f in sorted(glob.glob("trades_*.pkl")):
    for cfg, o in pd.read_pickle(f).items():
        for test, t in o.items():
            r = dict(cfg=cfg, test=test)
            for k in ("up", "flat", "down"):
                x = t[t.date.map(typ) == k]; r[k] = x.r.mean() if len(x) else float("nan"); r["n_" + k] = len(x)
            rows.append(r)
pd.DataFrame(rows).drop_duplicates(["cfg", "test"], keep="last").to_csv("extras.csv", index=False, float_format="%.4f")
print(pd.DataFrame(rows).drop_duplicates(["cfg", "test"], keep="last").round(3).to_string())
