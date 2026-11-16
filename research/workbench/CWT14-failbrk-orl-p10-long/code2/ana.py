"""Mechanic CWT14-orl-p10 scoring helpers. Educational only - not financial advice."""
import math, numpy as np, pandas as pd
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14/"
REPLAY = ("2026-10-12", "2026-11-10")
TWO_Y = ("2024-10-01", "2026-10-09")
TRAIN_END = "2025-12-31"

def load():
    s = pd.concat([pd.read_parquet(OUT + "sig_frames.parquet"), pd.read_parquet(OUT + "sig_extra.parquet")], ignore_index=True)
    s["date"] = s.date.astype(str)
    s["key"] = s.symbol + "|" + s.date + "|" + s.tod.astype(str)
    s = s.drop_duplicates("key")
    r = pd.concat([pd.read_parquet(OUT + f) for f in ("sim_frames.parquet", "sim_extra.parquet")], ignore_index=True)
    s = s.merge(r, on="key", how="inner")
    s = s[(s.close >= 5) & (s.atr_d / s.close >= 0.01)]
    s["poke"] = (s.orl - s.lod) / s.atr_d          # how far under the OR low the session low went (ATR)
    s["reclaim"] = (s.close - s.orl) / s.atr_d      # close above the OR low (ATR)
    s["vwapd"] = s.vwapDistPct
    return s.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)

def pick(s, mask="m10", min_adv=95e6, window=(950, 1200), extra=None):
    m = s[mask] & (s.adv20 >= min_adv) & (s.tod >= window[0]) & (s.tod <= window[1])
    if extra is not None:
        m &= extra(s)
    return s[m].drop_duplicates(["symbol", "date"])   # first qualifying bar per symbol-day (refire false)

def period(t, rng):
    return t[(t.date >= rng[0]) & (t.date <= rng[1])]

def stats(t, col="base_r"):
    if not len(t):
        return dict(n=0)
    r = t[col]; day = t.groupby("date")[col].sum()
    best = day.idxmax(); nb = (t.date != best).sum()
    return dict(n=len(t), days=t.date.nunique(), win=float((r > 0).mean()), avg=float(r.mean()),
                wo_best=float((r.sum() - day[best]) / nb) if nb else float("nan"),
                wo_worst=float((r.sum() - day.min()) / (t.date != day.idxmin()).sum()),
                total=float(r.sum()), worst_day=float(day.min()), best_day=float(day.max()), best_share=float(day[best] / r.sum()) if r.sum() > 0 else None)

def paired(tv, tp, colv="base_r", colp="base_r"):
    """Paired by day: day mean R (copy) - day mean R (parent), days where both trade; t = mean/sd*sqrt(n)."""
    a = tv.groupby("date")[colv].mean(); b = tp.groupby("date")[colp].mean()
    d = (a - b).dropna()
    if len(d) < 3 or d.std() == 0:
        return dict(days=len(d), diff=float(d.mean()) if len(d) else float("nan"), t=float("nan"))
    return dict(days=len(d), diff=float(d.mean()), t=float(d.mean() / d.std(ddof=1) * math.sqrt(len(d))))

def bar(n):
    return max(1.5, math.sqrt(2 * math.log(n)))

def regime_map():
    import sys
    sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/history2y")
    from lib import regimes
    r = regimes(); r.index = [str(d) for d in r.index]
    return r
