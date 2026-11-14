"""OBS-LATEDIP (Observer 2026-11-14, Lead lead-20261114-0300-4): is NM-ETF-late-dip-di-long's edge an INDEX effect?
Index analog of its trigger on 2y SPY / QQQ / IWM minute bars (OBS-UPDAY-NULL cache): 5-min bar closes 14:00-14:55,
15-min return <= -0.267% (the setup's -0.80% on 3x funds divided by 3); first trigger per index-day; entry at that
bar close; outcome = return to 15:55 (the setup's flat) in bps of the 1x index, gross. Split by sign-so-far at entry
(vs prior close), TRAIN (<= 2025-12) / VALID (2026-), with and without April 2025; control = same index, same entry
minute, all other days (unconditional late-day drift). Day-level stats (one trade per index-day). 0 configs beyond the
one pre-set threshold (setup's own, scaled). Educational only - not financial advice."""
import pandas as pd, numpy as np
from pathlib import Path
C = Path(__file__).parents[1] / "obs-upday-null" / "cache"
def tstat(x): x = np.asarray(x, float); return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan
for u in ["SPY", "QQQ", "IWM"]:
    d = pd.read_parquet(C / f"{u}_1m.parquet"); d = d[(d.t.dt.time >= pd.Timestamp("09:30").time()) & (d.t.dt.time < pd.Timestamp("16:00").time())]
    d = d.set_index("t").sort_index(); d["day"] = d.index.date
    pc = d.groupby("day").c.last().shift(1)
    b5 = d.c.resample("5min", label="right", closed="right").last().dropna(); b5 = b5[(b5.index.time >= pd.Timestamp("09:35").time())]
    df = pd.DataFrame({"c": b5}); df["day"] = df.index.date; df["r3"] = df.groupby("day").c.pct_change(3) * 100
    close = d.groupby("day").apply(lambda x: x.c[x.index.time <= pd.Timestamp("15:55").time()].iloc[-1])
    w = df[(df.index.time >= pd.Timestamp("14:00").time()) & (df.index.time <= pd.Timestamp("14:55").time())].copy()
    trig = w[w.r3 <= -0.267].groupby("day").head(1).copy()
    trig["fwd"] = (trig.day.map(close).values / trig.c.values - 1) * 1e4
    trig["sofar"] = np.sign(trig.c.values / trig.day.map(pc).values - 1)
    trig["split"] = np.where(pd.to_datetime(trig.day) <= "2025-12-31", "TRAIN", "VALID"); trig = trig.dropna(subset=["fwd", "sofar"])
    # control: every day, entry at the same clock times as triggers (14:00..14:55 grid), to 15:55
    ctl = w.groupby("day").head(12).copy(); ctl["fwd"] = (ctl.day.map(close).values / ctl.c.values - 1) * 1e4
    print(f"\n{u}: triggers {len(trig)} of {df.day.nunique()} days; control late-day drift (all 14:00-14:55 entries) {ctl.fwd.mean():+.1f}bps")
    for lab, x in [("all", trig), ("no Apr-2025", trig[~pd.to_datetime(trig.day).astype(str).str.startswith("2025-04")])]:
        print(f"  {lab:12s} n {len(x):3d} fwd {x.fwd.mean():+.1f}bps t {tstat(x.fwd):+.2f} win {(x.fwd>0).mean():.0%} | " +
              " | ".join(f"{s} n {len(g)} {g.fwd.mean():+.1f} t {tstat(g.fwd):+.2f}" for s, g in x.groupby("split")) + " | " +
              " | ".join(f"sofar {'up' if k>0 else 'down'} n {len(g)} {g.fwd.mean():+.1f} t {tstat(g.fwd):+.2f}" for k, g in x.groupby("sofar")))
print("\nReading: a positive fwd after the trigger, above the control drift, in TRAIN and VALID, = an index-level late-dip "
      "rebound (the setup would then be mostly index beta). Educational only - not financial advice.")
