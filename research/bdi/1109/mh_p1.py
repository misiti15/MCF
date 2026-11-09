"""MH1109-P1 (MH_PLAN.md, pre-registered): in-play names on the compass side at the 10:00 lab bar, both directions.
Usage: python mh_p1.py <scratch>   -> mh_p1_out.txt. Educational only - not financial advice."""
import importlib.util, os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/history2y")
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
import lib  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402
ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent; LOCK = ("2024-11-01", "2025-02-28"); S = Path(sys.argv[1])
P = []
def pr(*a): P.append(" ".join(str(x) for x in a)); print(P[-1], flush=True)
# ---- W60 at the 10:00 mark (same build as ecg1.py)
spec = importlib.util.spec_from_file_location("state15", ROOT / "research/bdi/hc1/state15.py")
argv0 = sys.argv; sys.argv = ["x", str(S)]; s15 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s15); sys.argv = argv0
st = s15.hist().dropna(subset=["fo"]).sort_values(["date", "T"]).reset_index(drop=True)
sg = lambda x: np.nan_to_num(np.sign(np.asarray(x, float))).astype(int)
st["s"] = sg(st.fo)
base = st.s + sg(st.vw) + np.where(st.breadth_open > 0.5, 1, np.where(st.breadth_open < 0.5, -1, 0)) + \
    np.where((st.s == sg(st.qqq_fo)) & (st.s == sg(st.iwm_fo)), st.s, 0)
piv = st.pivot(index="date", columns="T", values="s")
pW = np.zeros(len(st), int); nm = np.zeros(len(st), int)
for T in sorted(st["T"].unique()):
    marks = [t for t in piv.columns if t <= T and t > T - 60]
    sub = piv[marks]; same = sub.eq(sub[T], axis=0).all(axis=1) & (sub[T] != 0)
    i = (st["T"] == T).values
    pW[i] = np.where(same.reindex(st.date[i]).values, piv[T].reindex(st.date[i]).values, 0); nm[i] = len(marks)
v = base.values + pW
st["W60"] = np.where((v >= 4) & (pW == 1) & (nm >= 2), 2, np.where(v >= 2, 1, np.where((v <= -4) & (pW == -1) & (nm >= 2), -2, np.where(v <= -2, -1, 0))))
W10 = st[st["T"] == 600].set_index("date").W60
dts = st.groupby("date").agg(o=("open", "first"), c=("close", "first")); oc = (dts.c / dts.o - 1) * 100
dtype = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
fo10 = st[st["T"] == 600].set_index("date").fo
# ---- frames at the 10:00 bar
rows = []
for m in lib.months():
    if m in lib.LOCKED_MONTHS: continue
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "fromOpen", "atr_d", "atrPct", "adv20", "r_long_t1s1", "win_long_t1s1",
                                   "r_short_t1s1", "win_short_t1s1"])
    f = f[f.tod == 1000].copy(); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    assert not ((f.date >= LOCK[0]) & (f.date <= LOCK[1])).any()
    rows.append(f)
F = pd.concat(rows, ignore_index=True)
F = F[(F.adv20 >= 95e6) & (F.close >= 5)].copy()
F["w"] = F.date.map(W10); F = F[F.w.abs() == 2].copy()
F["side"] = np.sign(F.w).astype(int)
F["raw"] = np.where(F.side == 1, F.r_long_t1s1, F.r_short_t1s1); F["win"] = np.where(F.side == 1, F.win_long_t1s1, F.win_short_t1s1)
F = F[F.raw.notna()]
Ru = 0.25 * F.atr_d; e = F.close
extra = (2 * (0.01 + e * 1e-4) * tod_cost_mult(F.tod.to_numpy()) - 2 * 0.01 + np.where(F.raw < 0, 0.02, 0.0)) / Ru
F["r"] = F.raw - extra
F["vol_exp"] = F.atrPct / (F.atr_d / F.close * 100)
F["A"] = (F.vol_exp >= 0.12) & (np.sign(F.fromOpen) == F.side)
F["half"] = np.where(F.date <= "2025-12-31", "TRAIN", "VALID"); F["dtype"] = F.date.map(dtype); F["month"] = F.date.str[:7]
F["s10"] = F.date.map(lambda d: "above" if fo10.get(d, 0) >= 0 else "below")
A, Bs = F[F.A], F[~F.A]
pr(f"compass-confirmed days at 10:00: {F.date.nunique()} (UP {F[F.side == 1].date.nunique()}, DOWN {F[F.side == -1].date.nunique()}); class A {len(A):,} on {A.date.nunique()} days; base {len(Bs):,}")
bm = Bs.groupby(["date"]).r.mean(); A = A.assign(ex=A.r - A.date.map(bm))
def dt(x):
    g = x.groupby("date").ex.mean(); return g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 else np.nan
for h in ("TRAIN", "VALID", "ALL"):
    a = A if h == "ALL" else A[A.half == h]; b = Bs if h == "ALL" else Bs[Bs.half == h]
    pr(f"{h}: A n {len(a):,} days {a.date.nunique()} win {a.win.mean():.1%} avg R {a.r.mean():+.3f} | base n {len(b):,} win {b.win.mean():.1%} avg {b.r.mean():+.3f} | excess {a.ex.mean():+.3f} day-t {dt(a):.2f}")
for sd, nmsd in ((1, "long (UP-confirmed)"), (-1, "short (DOWN-confirmed)")):
    a = A[A.side == sd]; b = Bs[Bs.side == sd]
    pr(f"  {nmsd}: A n {len(a):,} days {a.date.nunique()} avg {a.r.mean():+.3f} (TRAIN {a[a.half == 'TRAIN'].r.mean():+.3f} / VALID {a[a.half == 'VALID'].r.mean():+.3f}) vs base {b.r.mean():+.3f}; excess day-t {dt(a):.2f}")
g = A.groupby(["dtype", "side"]).agg(n=("r", "size"), days=("date", "nunique"), avgR=("r", "mean"), ex=("ex", "mean")).round(3)
pr("\nQDAY split (SPY open-to-close +-0.25%) x side:\n" + g.to_string())
pr("by SPY vs open at 10:00: " + "; ".join(f"{k} n {len(x)} avg {x.r.mean():+.3f}" for k, x in A.groupby("s10")))
gd = A.groupby("dtype").r.mean()
dsum = A.groupby("date").r.sum().sort_values(); best = dsum.index[-1]
wo = A[A.date != best].r.mean(); share = dsum.iloc[-1] / dsum.sum() if dsum.sum() > 0 else np.nan
mo = A.groupby("month").r.mean(); pr(f"avg R w/o best day {wo:+.3f} (best {best} {dsum.iloc[-1]:+.1f}R, share of total {share:.0%}); months positive {(mo > 0).mean():.0%} of {len(mo)}")
pr("per month avg R: " + " ".join(f"{k[2:]} {v:+.2f}" for k, v in mo.items()))
BAR, B90 = max(1.5, float(np.sqrt(2 * np.log(4)))), 1.50
tr, va = A[A.half == "TRAIN"].r.mean(), A[A.half == "VALID"].r.mean()
ok = (tr > 0 and va > 0 and dt(A) >= B90 and gd.get("up", -1) > 0 and gd.get("down", -1) > 0 and (mo > 0).mean() >= 0.54 and wo > 0 and len(A) >= 300 and A.date.nunique() >= 30)
light = tr >= -0.02 and va >= -0.02 and dt(A) >= B90
pr(f"\nVERDICT (lineage N 4: full bar {BAR:.2f}, BAR90 {B90:.2f}): {'PASS -> Testing candidate' if ok else 'FAIL'}; light lane (>= -0.02R both halves, excess t >= 1.50): {'PASS -> Live Lab candidate' if light else 'fail'}")
# ---- 11-09 in-sample check (live frames, t1s1 on the 1-min bars, same costs)
D = "2026-11-09"; L = pd.read_parquet(S / "mh" / D / "frames.parquet"); L = L[L.tod == 1000].copy()
B1 = pd.read_parquet(S / f"cov/days/{D}/bars.parquet"); B1.index = pd.to_datetime(B1.index, utc=True).tz_convert("America/New_York")
PRI = pd.read_pickle(S / f"cov/days/{D}/priors.pkl")
L["adv"] = L.symbol.map(lambda s: PRI[s].adv if s in PRI else np.nan); L = L[(L.adv >= 95e6) & (L.close >= 5)]
L["vol_exp"] = L.atrPct / (L.atr_d / L.close * 100); L["A"] = (L.vol_exp >= 0.12) & (L.fromOpen > 0)
def walk(s, e, Ru):
    g = B1[B1.symbol == s]; g = g[(g.index >= pd.Timestamp(f"{D} 10:00", tz="America/New_York")) & (g.index < pd.Timestamp(f"{D} 15:55", tz="America/New_York"))]
    c = (2 * (0.01 + e * 1e-4) * 1.0) / Ru
    for h, l in zip(g.high, g.low):
        if l <= e - Ru: return -1.0 - c - 0.02 / Ru
        if h >= e + Ru: return 1.0 - c
    return ((g.close.iloc[-1] - e) / Ru - c) if len(g) else np.nan
L["r"] = [walk(s, e, 0.25 * a) for s, e, a in zip(L.symbol, L.close, L.atr_d)]
a, b = L[L.A], L[~L.A]
pr(f"\n11-09 in-sample (W60 UP-confirmed at 10:00 -> long): class A n {len(a)} win {(a.r > 0).mean():.0%} avg {a.r.mean():+.3f} | base n {len(b)} avg {b.r.mean():+.3f} | excess {a.r.mean() - b.r.mean():+.3f}")
pr("Locked block never read (asserted). Configurations: 1. Educational only - not financial advice.")
(HERE / "mh_p1_out.txt").write_text("\n".join(P) + "\n")
