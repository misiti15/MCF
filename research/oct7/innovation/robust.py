"""Robustness detail for the finalists: per-week, per-half, trades/day, overlap with exhaustion_short.
Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "research/oct7/innovation"); sys.path.insert(0, "research/setups2/candidates")
import bdlib as B, volume_flip_1 as vf
from plateau import e2

def trades(df, m, side, geom, win):
    tod = df.tod.to_numpy(); r = df[f"r_{side}_{geom}"].to_numpy(float)
    mm = np.asarray(m, bool) & (tod >= win[0]) & (tod <= win[1]) & np.isfinite(r)
    idx = B._first_idx(df, mm)
    R = 0.25 * df.atr_d.to_numpy(float)[idx]; px = df.close.to_numpy(float)[idx]
    rr = r[idx]; rp = rr - 2e-4 * px / R - 0.02 / R * (rr < -1 + 1e-9)
    return pd.DataFrame({"symbol": df.symbol.astype(str).to_numpy()[idx], "date": df.date.to_numpy()[idx], "tod": tod[idx], "r": rp})

for name, fn in (("F1 rsi3", e2(0.88, 70, "fo>0")), ("F1b simple", e2(0.88, 70, "fo>0", rsi_on=False))):
    for sp in ("train", "valid"):
        df = B.load(sp)
        t = trades(df, fn(df), "short", "t1s1", (1300, 1430))
        wk = t.groupby(pd.to_datetime(t.date).dt.isocalendar().week).r.agg(["size", "mean"]).round(3)
        dd = t.groupby("date").r.agg(["size", "mean", "sum"])
        ex = trades(df, vf.mask(df), "short", "t1s1", (1300, 1500))
        ov = len(t.merge(ex, on=["symbol", "date"]))
        print(f"{name} {sp}: n={len(t)} trades/day median={dd['size'].median():.0f} max={dd['size'].max()} green_days={(dd['sum']>0).mean():.2f} "
              f"worst_day={dd['sum'].min():.1f}R best_day={dd['sum'].max():.1f}R total={dd['sum'].sum():.1f}R overlap_exh={ov}")
        print("   weekly mean R:", dict(zip(wk.index, wk["mean"])), "\n   tod dist:", t.tod.value_counts().sort_index().head(6).to_dict())
        if sp == "valid":
            # top-20-per-day cap (production slots are limited): earliest entries first, then by symbol
            cap = t.sort_values(["date", "tod"]).groupby("date").head(20)
            dc = cap.groupby("date").r.mean(); print(f"   capped 20/day: n={len(cap)} exp={cap.r.mean():.4f} t_day={dc.mean()/(dc.std(ddof=1)/np.sqrt(len(dc))):.2f}")
        else:
            cap = t.sort_values(["date", "tod"]).groupby("date").head(20)
            dc = cap.groupby("date").r.mean(); print(f"   capped 20/day: n={len(cap)} exp={cap.r.mean():.4f} t_day={dc.mean()/(dc.std(ddof=1)/np.sqrt(len(dc))):.2f}")
