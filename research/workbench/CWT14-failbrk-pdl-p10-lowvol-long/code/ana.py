"""Scoring helpers (sibling job's ana.py adapted). Educational only - not financial advice."""
import math, sys, numpy as np, pandas as pd
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14pdl/"
TESTS = {"replay": ("2026-10-12", "2026-11-10"), "2y": ("2024-10-01", "2026-10-09"),
         "train": ("2024-10-01", "2025-12-31"), "valid": ("2026-01-01", "2026-10-09")}
def cost_ps(px): return 2 * (0.01 + px * 1e-4) + 0.02
def load():
    s = pd.read_parquet(OUT + "sig.parquet")
    s["key"] = s.symbol + "|" + s.date + "|" + s.tod.astype(str)
    s = s.merge(pd.read_parquet(OUT + "sim.parquet"), on="key", how="inner")
    s = s.merge(pd.read_parquet(OUT + "ctx.parquet"), on=["date", "tod"], how="left")
    s["poke"] = (s.pdl - s.lod) / s.atr_d; s["reclaim"] = (s.close - s.pdl) / s.atr_d
    s["atrp"] = s.atr_d / s.close; s["drift"] = (s.fill - s.close) / s.atr_d
    s["rng_atr"] = (s.hod - s.lod) / s.atr_d
    return s.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
def pick(s, mask="m10v", window=(950, 1500), extra=None, min_adv=95e6):
    m = s[mask] & (s.adv20 >= min_adv) & (s.tod >= window[0]) & (s.tod <= window[1])
    if extra is not None: m &= extra(s)
    return s[m].drop_duplicates(["symbol", "date"])
def period(t, rng): return t[(t.date >= rng[0]) & (t.date <= rng[1])]
def stats(t, col):
    if not len(t): return dict(n=0)
    r = t[col]; day = t.groupby("date")[col].sum(); best = day.idxmax(); nb = (t.date != best).sum()
    return dict(n=len(t), days=t.date.nunique(), win=float((r > 0).mean()), avg=float(r.mean()),
                wo_best=float((r.sum() - day[best]) / nb) if nb else np.nan,
                wo_worst=float((r.sum() - day.min()) / (t.date != day.idxmin()).sum()),
                total=float(r.sum()), worst_day=float(day.min()), best_share=float(day[best] / r.sum()) if r.sum() > 0 else np.nan)
def paired(tv, tp, cv, cp):
    a = tv.groupby("date")[cv].mean(); b = tp.groupby("date")[cp].mean(); d = (a - b).dropna()
    if len(d) < 3 or d.std() == 0: return dict(diff=np.nan, t=np.nan)
    return dict(diff=float(d.mean()), t=float(d.mean() / d.std(ddof=1) * math.sqrt(len(d))))
def regimes():
    sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/history2y")
    from lib import regimes as rg
    r = rg(); r.index = [str(d) for d in r.index]; return r
def bps(t, ex):
    """net P/L per dollar traded (bps) = R x risk / fill."""
    risk = t[f"{ex}_risk"] if f"{ex}_risk" in t else t["A_risk"]
    return t[f"{ex}_r"] * risk / t.fill * 1e4
