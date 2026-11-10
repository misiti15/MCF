"""SQZ1 (SQZ1_PLAN.md, pre-registered): two-year test of lead swing1106-L10 "scalp the chase burst".
Class A = >= 3rd same-side entry of its setup within 15 min AND QQQ 30-min return at the entry <= -0.40% (short) /
>= +0.40% (long). Rule: class A takes a +0.5 x stop-distance target. ONE configuration.
Inputs: <scratch>/enr (research/bdi/burst1/enrich.py on bt_lab1104), data/cache_hist/1Min/{QQQ,SPY}.parquet.
Usage: python sqz1.py <scratch-with-enr>   -> sqz1_out.txt, sqz1_setups.csv, sqz1_families.csv
Educational only - not financial advice."""
import os, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "SQZ1 never reads the locked block"
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28"); SL, BP = 0.01, 1e-4
TGT = {"t1s1": 1.0, "t1s05": 2.0, "t05s05": 1.0, "t05s1": 0.5}
fam = lambda s: re.sub(r"\d.*", "", s).split("-")[0]
P = []
def pr(*a): P.append(" ".join(str(x) for x in a)); print(P[-1], flush=True)
slot = lambda tod: ((tod // 100) * 60 + tod % 100 - 590) // 5
T, HIT = [], []
for p in sorted((S / "enr").glob("*.parquet")):
    t = pd.read_parquet(p); mf = np.load(str(p).replace(".parquet", "_mfe.npy")).astype(np.float32)
    keep = (t.date <= "2026-10-05").values; t = t[keep].reset_index(drop=True); mf = mf[keep]
    assert not ((t.date >= LOCK[0]) & (t.date <= LOCK[1])).any(), "locked block present"
    mf = pd.DataFrame(mf).ffill(axis=1).to_numpy(np.float32)
    s0 = slot(t.tod.to_numpy()); sx = np.clip(slot(t.xtod.to_numpy()), 0, 73)
    kind = t.kind.to_numpy(); ix = np.arange(len(t))
    pre = np.where(sx - 1 >= s0 + 1, mf[ix, np.clip(sx - 1, 0, 73)], 0.0)     # MFE through the bar before the exit bar
    atx = mf[ix, sx]
    hit = np.where(kind == 1, pre >= 0.5, np.nan_to_num(atx, nan=0.0) >= 0.5)
    t["hit"] = hit; T.append(t)
T = pd.concat(T, ignore_index=True)
pr(f"trades {len(T):,}, setups {T.setup.nunique()}, days {T.date.nunique()}, {T.date.min()}..{T.date.max()}; kinds {T.kind.value_counts().to_dict()}")
# index features: entry at the close of the 5-min bar labelled tod -> entry minute m = tod + 5
I = {}
for s in ("QQQ", "SPY"):
    b = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{s}.parquet"); b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b["d"] = b.index.strftime("%Y-%m-%d"); b = b[~((b.d >= LOCK[0]) & (b.d <= LOCK[1]))]
    b["mm"] = b.index.hour * 60 + b.index.minute; b = b[(b.mm >= 570) & (b.mm < 960)]
    I[s] = {d: (g.mm.to_numpy(), g.close.to_numpy(float), g.open.iloc[0] if g.mm.iloc[0] == 570 else np.nan) for d, g in b.groupby("d")}
    if s == "SPY":
        DT = pd.DataFrame({d: dict(oc=(g.close.iloc[-1] / g.open.iloc[0] - 1) * 100,
                                   f10=(g[g.mm < 600].close.iloc[-1] / g.open.iloc[0] - 1) * 100 if (g.mm < 600).any() else np.nan)
                           for d, g in b.groupby("d")}).T
DT["dtype"] = np.where(DT.oc > 0.25, "up", np.where(DT.oc < -0.25, "down", "quiet")); DT["s10"] = np.where(DT.f10 >= 0, "above", "below")
T["m"] = (T.tod // 100) * 60 + T.tod % 100 + 5
def r30(d, m):
    v = I["QQQ"].get(d)
    if v is None: return np.nan
    mm, c, o = v; i = np.searchsorted(mm, m) - 1; j = np.searchsorted(mm, m - 30) - 1
    return np.nan if i < 0 else (c[i] / (c[j] if j >= 0 else o) - 1) * 100
T["q30"] = [r30(d, m) for d, m in zip(T.date.to_numpy(), T.m.to_numpy())]
# ordinal of the entry among its setup's same-side entries in [t-15, t]
T = T.sort_values(["setup", "side", "date", "tod", "symbol"], kind="mergesort").reset_index(drop=True)
k = (T.setup + "|" + T.side.astype(str) + "|" + T.date).to_numpy(); m = T.m.to_numpy()
st = np.flatnonzero(np.r_[True, k[1:] != k[:-1]]); en = np.r_[st[1:], len(k)]
ordn = np.zeros(len(T), int)
for a, b in zip(st, en):
    mm = m[a:b]; lo = np.searchsorted(mm, mm - 15, side="left"); ordn[a:b] = np.arange(b - a) - lo + 1
T["ordn"] = ordn
T["A"] = (T.ordn >= 3) & (((T.side == -1) & (T.q30 <= -0.40)) | ((T.side == 1) & (T.q30 >= 0.40)))
# scalp R
e = T.entry.to_numpy(float); tier = np.where(e < 5, 3.0, 1.0)
ec = (SL + e * BP) * tod_cost_mult(T.tod.to_numpy()); r05 = 0.5 - tier * ec / (T.stop_pct.to_numpy(float) * e)
elig = T.geom.map(TGT).to_numpy() > 0.5
T["r_s"] = np.where(elig & T.hit.to_numpy(bool) & np.isfinite(r05), r05, T.r)
T["d_all"] = T.r_s - T.r                     # the scalp's effect on any trade (control)
T["d"] = np.where(T.A, T.d_all, 0.0)
T["fam"] = T.setup.map(fam); T["half"] = np.where(T.date <= "2026-02-28", "TRAIN", "VALID")
T = T.join(DT[["dtype", "s10"]], on="date")
pr(f"class A {int(T.A.sum()):,} ({T.A.mean():.2%}); eligible geometry {elig.mean():.0%}; A with q30 known {T[T.A].q30.notna().mean():.0%}")
def dayt(x, col="d"):
    g = x.groupby("date")[col].sum(); return g.sum(), (g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 and g.std() > 0 else np.nan), len(g)
res = {}
for h in ("TRAIN", "VALID"):
    x = T[T.half == h]; a = x[x.A]; sd, tt, nd = dayt(x)
    # excess: A per-trade delta minus the same setups' non-A per-trade delta (setup-weighted by A counts)
    na = x[~x.A].groupby("setup").d_all.mean(); exp = a.setup.map(na).fillna(0)
    ex = (a.d_all - exp); exs = ex.groupby(a.date).sum(); ext = exs.mean() / (exs.std(ddof=1) / np.sqrt(len(exs))) if len(exs) > 2 else np.nan
    res[h] = dict(delta=sd, t=tt, excess=ex.sum(), excess_t=ext, nA=len(a))
    pr(f"{h}: trades {len(x):,}, class A {len(a):,} (live R avg {a.r.mean():+.3f} -> scalp {a.r_s.mean():+.3f}; hit {a.hit.mean():.0%}); "
       f"delta {sd:+.1f}R (day-clustered t {tt:.2f}, {nd} days); excess {ex.sum():+.1f}R (per A trade {ex.mean():+.3f}, t {ext:.2f}); "
       f"control: same scalp on all trades {x.d_all.sum():+.1f}R (per trade {x.d_all.mean():+.4f})")
    for sd_ in (-1, 1):
        y = a[a.side == sd_]; pr(f"   {'short' if sd_ == -1 else 'long'} A n {len(y):,} delta {y.d.sum():+.1f}R avg r {y.r.mean():+.3f} -> {y.r_s.mean():+.3f}")
# QDAY split
for col in ("dtype", "s10"):
    g = T[T.A].groupby(["half", col]).agg(n=("d", "size"), days=("date", "nunique"), r=("r", "mean"), r_s=("r_s", "mean"), delta=("d", "sum")).round(3)
    pr(f"\nclass A by {col}:\n" + g.to_string())
    g2 = T.groupby(["half", col]).agg(n=("r", "size"), all_r=("r", "mean")).round(3); pr(f"all trades by {col} (base):\n" + g2.to_string())
# families / setups (Remedies rule)
F = T[T.A].groupby(["half", "fam"]).agg(n=("d", "size"), delta=("d", "sum")).unstack("half").fillna(0)
F.columns = [f"{a}_{b}" for a, b in F.columns]; F.round(2).to_csv(HERE / "sqz1_families.csv")
pr("\nfamilies (class A n / delta R):\n" + F.round(1).to_string())
Sx = T[T.A].groupby(["setup", "half"]).agg(n=("d", "size"), delta=("d", "sum")).unstack("half").fillna(0)
Sx.columns = [f"{a}_{b}" for a, b in Sx.columns]; Sx.round(2).to_csv(HERE / "sqz1_setups.csv")
for h in ("TRAIN", "VALID"):
    c = Sx[f"delta_{h}"]; pr(f"{h} setups better {(c > 0).sum()} ({c[c > 0].sum():+.1f}R) / worse {(c < 0).sum()} ({c[c < 0].sum():+.1f}R); worst {c.sort_values().head(3).round(1).to_dict()}")
harm = int((F.get("delta_VALID", pd.Series(dtype=float)) < -5).sum())
v, tr = res["VALID"], res["TRAIN"]
ok = v["t"] >= 2.61 and tr["delta"] > 0 and v["excess"] > 0 and harm <= 1
lite = v["t"] >= 2.35 and tr["delta"] > 0 and v["excess"] > 0 and harm <= 1
pr(f"\nVERDICT: VALID t {v['t']:.2f} (bar 2.61, BAR90 2.35), TRAIN delta {tr['delta']:+.1f}R, VALID excess {v['excess']:+.1f}R (t {v['excess_t']:.2f}), "
   f"families harmed (VALID < -5R) {harm} -> {'PASS' if ok else ('Testing / Live Lab suggestion' if lite else 'FAIL')}")
T[T.A][["setup", "side", "date", "tod", "symbol", "q30", "ordn", "r", "r_s", "hit", "half", "dtype", "s10"]].to_parquet(S / "sqz1_A.parquet")
pr("Locked block 2024-11-01..2025-02-28 never read (asserted). Configurations: 1. Educational only - not financial advice.")
(HERE / "sqz1_out.txt").write_text("\n".join(P) + "\n")
