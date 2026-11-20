"""OUT-RETIRE study (research only, no config change). Walk-forward backtest of candidate permanent RETIRED rules on
the live record (LR8 R after costs, identical signals once). At each review date d only trades dated <= d are used;
a retirement takes effect from the next session. Educational only - not financial advice.

    python retire_study.py  [trades.pkl]  [outdir]
"""
import math, sys, itertools
from pathlib import Path
import numpy as np, pandas as pd

SP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
T = pd.read_pickle(sys.argv[1] if len(sys.argv) > 1 else SP / "live_trades.pkl")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else SP / "ww_out/retire")
T = T[T.date < "2026-11-20"].copy()
SESS = sorted(T.date.unique())
FRIDAYS = [d for d in SESS if pd.Timestamp(d).weekday() == 4]
NXT = {d: (SESS[i + 1] if i + 1 < len(SESS) else None) for i, d in enumerate(SESS)}
END = SESS[-1]

# Primary membership (proxy: between first and last Primary trade); graduation = first Primary trade date
P = T[T.account == "primary"].groupby("strategy").date.agg(["min", "max"])
def in_primary(s, d):
    return s in P.index and P.loc[s, "min"] <= d <= P.loc[s, "max"]

# per setup per day aggregates
DAY = T.groupby(["strategy", "date"]).r.agg(["sum", "count", "mean"]).reset_index()
BY = {s: g.sort_values("date").reset_index(drop=True) for s, g in DAY.groupby("strategy")}
TR = {s: g.sort_values("date") for s, g in T.groupby("strategy")}

def stats(s, d):
    g = BY[s]; g = g[g.date <= d]
    if not len(g): return None
    n = int(g["count"].sum()); tot = g["sum"].sum(); days = len(g); avg = tot / n
    b = g["sum"].idxmax(); nb = n - g.loc[b, "count"]
    wo = (tot - g.loc[b, "sum"]) / nb if nb > 0 else np.nan
    m = g["mean"]; tday = m.mean() / (m.std(ddof=1) / math.sqrt(days)) if days > 1 and m.std(ddof=1) > 0 else np.nan
    r = TR[s]; r = r[r.date <= d]
    dev = (r.r - avg).groupby(r.date).sum()
    se = math.sqrt((dev ** 2).sum() * days / max(days - 1, 1)) / n
    last10 = g["sum"].iloc[-10:].sum()
    return dict(n=n, days=days, avg=avg, wo=wo, tday=tday, se=se, last10=last10, tot=tot)

def rule_ub(n_min, z, d_min=15):
    return lambda st, h: st["n"] >= n_min and st["days"] >= d_min and st["avg"] + z * st["se"] < 0
def rule_floor(n_min, wo_max, t_max, d_min=15):
    return lambda st, h: (st["n"] >= n_min and st["days"] >= d_min and st["wo"] <= wo_max
                          and not np.isnan(st["tday"]) and st["tday"] <= t_max)
def rule_wo_last10(n_min, wo_max, d_min=15):
    return lambda st, h: st["n"] >= n_min and st["days"] >= d_min and st["wo"] <= wo_max and st["last10"] <= 0
def footrace_hit(st):
    return (st["days"] >= 15 and st["n"] >= 30 and st["avg"] <= 0 and st["wo"] <= 0
            and not np.isnan(st["tday"]) and st["tday"] <= -1.5)
def rule_fr_repeat(k):
    return lambda st, h: h >= k   # h = number of Friday reviews (to date) at which FOOTRACE-EXIT held
def rule_tryscaled(n_min, tcrit, d_min=15):
    return lambda st, h: (st["n"] >= n_min and st["days"] >= d_min and st["wo"] <= 0
                          and not np.isnan(st["tday"]) and st["tday"] <= -tcrit)

COMPASS_EXEMPT = ("CWT14-failbrk-orl-p05-long", "heat_fade_short-FD")   # GY-LIFE owner exception
def rule_rec(n_min=150, wo_max=-0.10, t_max=-2.5, d_min=20):
    f = rule_floor(n_min, wo_max, t_max, d_min)
    return lambda st, h: f(st, h) and st["last10"] <= 0

TC = math.sqrt(2 * math.log(220))
CONFIGS = {}
for n_, z in itertools.product([60, 100, 150], [1.645, 1.96]):
    CONFIGS[f"R1-UB{z}-n{n_}"] = ("R1 UB95", rule_ub(n_, z))
for n_, wo, t in itertools.product([100, 150], [-0.05, -0.10], [-2.0, -2.5]):
    CONFIGS[f"R2-FLOOR-n{n_}-wo{wo}-t{t}"] = ("R2 hard floor", rule_floor(n_, wo, t))
for n_, wo in itertools.product([100, 150], [-0.10, -0.15]):
    CONFIGS[f"R3-WOL10-n{n_}-wo{wo}"] = ("R3 wo+last10", rule_wo_last10(n_, wo))
for k in [2, 3]:
    CONFIGS[f"R4-FRx{k}"] = ("R4 repeat FOOTRACE", rule_fr_repeat(k))
for n_, tc in itertools.product([30, 60], [TC, 2.5]):
    CONFIGS[f"R5-TRY-n{n_}-t{tc:.2f}"] = ("R5 try-scaled t", rule_tryscaled(n_, tc))

CONFIGS["R6-REC-n150-d20-wo-0.10-t-2.5-L10"] = ("R6 floor+last10 (recommended)", rule_rec())

def run(cadence):
    revs = FRIDAYS if cadence == "friday" else SESS
    st_cache = {}
    frh = {s: {} for s in BY}       # Friday FOOTRACE hits up to each date
    for s in BY:
        h = 0
        for d in SESS:
            if d in FRIDAYS:
                st = stats(s, d); st_cache[(s, d)] = st
                if st and footrace_hit(st): h += 1
            frh[s][d] = h
    kills = []
    for name, (fam, fn) in CONFIGS.items():
        for s in BY:
            for d in revs:
                if NXT[d] is None: break
                if in_primary(s, d): continue
                if name.startswith("R6") and s in COMPASS_EXEMPT: continue
                st = st_cache.get((s, d)) or stats(s, d); st_cache[(s, d)] = st
                if st is None: continue
                if fn(st, frh[s][d]):
                    eff = NXT[d]; post = TR[s][TR[s].date >= eff]
                    fin = stats(s, END)
                    grad = s in P.index and P.loc[s, "max"] >= eff
                    kills.append(dict(config=name, family=fam, cadence=cadence, setup=s, review=d, effective=eff,
                                      n_at=st["n"], days_at=st["days"], avg_at=round(st["avg"], 3),
                                      wo_at=round(st["wo"], 3), tday_at=round(st["tday"], 2),
                                      post_n=len(post), post_days=post.date.nunique(), post_R=round(post.r.sum(), 2),
                                      post_primary_R=round(post[post.account == "primary"].r.sum(), 2),
                                      post_wo_avg=(round((post.r.sum() - post.groupby("date").r.sum().max()) /
                                                   max(len(post) - post.groupby("date").size()[post.groupby("date").r.sum().idxmax()], 1), 3)
                                                   if len(post) > 1 else np.nan),
                                      final_wo=round(fin["wo"], 3), final_avg=round(fin["avg"], 3),
                                      later_primary=grad))
                    break
    return pd.DataFrame(kills)

K = pd.concat([run("friday"), run("daily")], ignore_index=True)
K["wrong_post_pos"] = (K.post_R > 0) & (K.post_n >= 10)
K["wrong_final_pos"] = K.final_wo > 0
K["wrongful"] = K.wrong_post_pos | K.wrong_final_pos | K.later_primary
def names(x, col): return "; ".join(f"{r.setup} ({r.post_R:+.1f}R/{r.post_n}t)" for r in x[x[col]].itertuples())
rows = []
for (c, cad), g in K.groupby(["config", "cadence"], sort=False):
    rows.append(dict(config=c, family=g.family.iloc[0], cadence=cad, retired=len(g),
                     post_trades=int(g.post_n.sum()), post_R=round(g.post_R.sum(), 1), R_saved=round(-g.post_R.sum(), 1),
                     post_avg=round(g.post_R.sum() / max(g.post_n.sum(), 1), 3),
                     saved_wo_best_setup=round(-(g.post_R.sum() - g.post_R.min()), 1) if len(g) else 0,
                     best_setup_share=round(g.post_R.min() / g.post_R.sum(), 2) if g.post_R.sum() < 0 else np.nan,
                     setups_post_positive=int(g.wrong_post_pos.sum()), setups_final_positive=int(g.wrong_final_pos.sum()),
                     later_primary=int(g.later_primary.sum()), wrongful=int(g.wrongful.sum()),
                     post_primary_R=round(g.post_primary_R.sum(), 1), median_effective=g.effective.sort_values().iloc[len(g)//2],
                     wrongful_names=names(g, "wrongful")))
E = pd.DataFrame(rows)
def null_post(g, cad):
    """avg post R/trade of setups NOT retired by this config but eligible at the same review (non-Primary, >= 15 days,
    >= 60 trades), from the same effective date: the discrimination baseline."""
    tot = n = 0
    for r in g.itertuples():
        for s2 in BY:
            if s2 in set(g.setup) or in_primary(s2, r.review): continue
            st = stats(s2, r.review)
            if not st or st["days"] < 15 or st["n"] < 60: continue
            post = TR[s2][TR[s2].date >= r.effective]
            tot += post.r.sum(); n += len(post)
    return round(tot / max(n, 1), 3)
E["null_post_avg_eligible_kept"] = [null_post(K[(K.config == r.config) & (K.cadence == r.cadence)], r.cadence)
                                    if r.cadence == "friday" else np.nan for r in E.itertuples()]
E["strict_wrongful"] = [int(((K.config == r.config) & (K.cadence == r.cadence) & (K.later_primary | (K.final_wo > 0) |
                         ((K.post_n >= 10) & (K.post_R > 0) & (K.post_wo_avg > 0)))).sum()) for r in E.itertuples()]
E.to_csv(OUT / "retire_eval.csv", index=False)
K.to_csv(OUT / "retire_kills.csv", index=False)
print(E.drop(columns="wrongful_names").to_string())
print("configs:", len(CONFIGS), "x 2 cadences =", 2 * len(CONFIGS))
