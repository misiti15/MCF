"""Swing-autopsy leads L1-L3 (research/bdi/swing1103/AUTOPSY.md, pre-registered 2026-11-03 before any test): ONE
pre-registered 2-year backtest per lead, written before scoring (BDI 2026-11-03 night).

Data: research/history2y lab trade lists (production costs, tod entry multiplier; lab_trades.parquet) + 5-min frames
(SPY / IWM rows) + 1-min frames (QQQ / IWM rows) + daily closes. The locked block 2024-11-01..2025-02-28 is not in the
frame directories and is dropped from the daily table BEFORE anything is computed (asserted). Train < 2025-09-01,
valid >= 2025-09-01 (nightly convention). Every lead reports R by SPY day type (open-to-close up > +0.25%, down <
-0.25%, else quiet) and by SPY vs its open at 10:00 (above / below).

  L1  vol / inverse-ETP beta guard. Beta = 60-session daily-return beta to SPY, trailing, exclusive of the day (the
      lead's 20-session 5-min beta is not in the 2-year store; declared proxy). Pool = every LONG lab setup (NS5 alone
      has 8 such trades, untestable: nightly1103). Class A = beta <= -1.5. PASS (fixed now): class A avg R <= class B
      avg R - 0.10 with Welch t >= bar, n_A >= 10, and corr(class-A day R, SPY open-to-close) <= -0.5.   1 config.
  L2  rotation turn. Trigger per day = first minute 10:30..11:30 where QQQ makes a new session high (1-min HOD rises)
      while IWM is >= +0.40% from its open and has been >= 0.10% below its own HOD for >= 5 consecutive minutes.
      Tagged = RW3/RW5/MF2/MF4 lab shorts entered 1..30 min after the trigger, in names whose best-correlated sector
      ETF (daily returns, train dates) is not XLK / SMH / SOXX. PASS: tagged avg R >= +0.25, n >= 30, and tagged minus
      the same day's other family shorts >= +0.15R with day-clustered t >= bar.                         1 config.
  L3  up-morning delay (full rule incl. the IWM leg the nightly could not test). Qualifying day: SPY >= +0.15% and
      IWM >= +0.25% from the open at the 10:00 bar. Cut = first SPY 5-min bar after 10:30 closing below the prior
      bar's low (10:50 if none). Before = family shorts entered at bar close < cut, after = >= cut. PASS: before avg
      <= -0.20R, after >= 0, (after - before) >= 0.25R with day-clustered t >= bar, n >= 40, >= 6 days.  1 config.
  L6  (new, BDI 2026-11-03 night, from today's per-trade hindsight check: shorts entered with SPY >= +0.25% from the
      open made +0.357R live on 11-03 (n 177) and +0.314R on 11-02 (n 86)) counter-index entries. Pool = all 21 lab
      setups. Counter = short with SPY from-open >= +0.25% at the entry bar, or long with SPY <= -0.25%. R is taken as
      the excess over the setup's own mean on the same split (setup-mix adjusted). PASS: counter excess >= +0.05R in
      train AND valid, day-clustered t (all days) >= bar, and counter excess > 0 on up, down AND quiet days. 1 config.
Bar: t >= max(1.5, sqrt(2 ln N)) with N = all configurations tried tonight (passed on the command line).
Usage: python leads_bt.py <N_tonight>  -> leads_bt_out.txt, leads_bt.json.   Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as ds
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research.gates import t_required
H = ROOT / "research/history2y/data"; OUT = Path(__file__).resolve().parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3; BAR = t_required(N)
LK0, LK1 = "2024-11-01", "2025-02-28"; SPLIT = "2025-09-01"
FAM = ["RW3 bdi-rw-gapdn-rsi5pop-flowsell", "RW5 bdi-rw-heat30-flowsell-rsi5pop-gapdn", "MF2-open-rsimidhi-flowsell", "MF4-h40-open-flowsell"]
LONGS = ["NS5-sma50-flush-oversold-long", "NS1-rsidip-rsi5pop-long", "heat_fade_long"]
P = []
def pr(*a): P.append(" ".join(str(x) for x in a))

L = pd.read_parquet(H / "lab_trades.parquet"); L["date"] = L.date.astype(str)
assert not L.date.between(LK0, LK1).any()
D = pd.read_parquet(H / "daily.parquet", columns=["symbol", "date", "open", "close"]); D["date"] = pd.to_datetime(D.date).dt.date.astype(str)
D = D[~D.date.between(LK0, LK1)]
spy_d = D[D.symbol == "SPY"].set_index("date"); spy_oc = (spy_d.close / spy_d.open - 1) * 100
dtype = pd.Series(np.where(spy_oc > 0.25, "up", np.where(spy_oc < -0.25, "down", "quiet")), index=spy_oc.index)

def frames(dirn, syms, cols):
    t = ds.dataset(str(H / dirn), format="parquet", partitioning="hive").to_table(columns=cols, filter=ds.field("symbol").isin(syms)).to_pandas()
    t["date"] = pd.to_datetime(t.date).dt.date.astype(str); assert not t.date.between(LK0, LK1).any()
    return t.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)

F5 = frames("frames", ["SPY", "IWM"], ["symbol", "date", "tod", "close", "low", "fromOpen"])
spy10 = F5[(F5.symbol == "SPY") & (F5.tod == 1000)].set_index("date").fromOpen
L["dtype"] = L.date.map(dtype); L["s10"] = np.where(L.date.map(spy10) >= 0, "SPY>open@10", "SPY<open@10")
L["split"] = np.where(L.date < SPLIT, "train", "valid")

def split_tbl(x, name):
    g1 = x.groupby("dtype").r.agg(["size", "mean"]).round(3); g2 = x.groupby("s10").r.agg(["size", "mean"]).round(3)
    pr(f"   {name} by day type: " + "; ".join(f"{k} n {int(r['size'])} {r['mean']:+.3f}R" for k, r in g1.iterrows())
       + " | " + "; ".join(f"{k} n {int(r['size'])} {r['mean']:+.3f}R" for k, r in g2.iterrows()))

def dayt(diff):
    diff = diff.dropna()
    return round(diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff))), 2) if len(diff) > 2 and diff.std() > 0 else np.nan

def exbest(x):
    g = x.groupby("date").r.sum(); b = g.idxmax(); tot = g.sum()
    return round(x[x.date != b].r.mean(), 3), (round(g.max() / tot, 2) if tot > 0 else None)

res = {}
pr(f"configs tonight N = {N}, bar t {BAR}")
# ------------------------------------------------------------------ L1
W = D.pivot(index="date", columns="symbol", values="close").sort_index().pct_change(fill_method=None)
W.loc[W.index[W.index > LK1][0]] = np.nan   # no return across the dropped locked block
s = W["SPY"]; Wv = W[s.notna()].reindex(W.index)
S2 = pd.DataFrame(np.where(Wv.notna(), s.to_numpy()[:, None], np.nan), index=W.index, columns=W.columns)   # pairwise-complete
rm = lambda z: z.rolling(60, min_periods=40).mean()
cov = rm(Wv * S2) - rm(Wv) * rm(S2); var = rm(S2 * S2) - rm(S2) ** 2
beta = (cov / var).shift(1)
bl = beta.stack().rename("beta").reset_index(); bl.columns = ["date", "symbol", "beta"]
X = L[L.setup.isin(LONGS)].merge(bl, on=["date", "symbol"], how="left")
A, B = X[X.beta <= -1.5], X[X.beta > -1.5]
pr(f"\nL1 vol / inverse-ETP beta guard (long lab setups {LONGS}); beta coverage {X.beta.notna().mean():.1%}")
pr(f"   class A beta<=-1.5: n {len(A)} avg {A.r.mean():+.3f}R symbols {sorted(A.symbol.unique())[:15]}")
pr(f"   class B others    : n {len(B)} avg {B.r.mean():+.3f}R")
dlt = A.r.mean() - B.r.mean(); wt = dlt / np.sqrt(A.r.var() / max(1, len(A)) + B.r.var() / len(B)) if len(A) > 1 else np.nan
dr = A.groupby("date").r.sum(); cr = dr.corr(spy_oc.reindex(dr.index)) if len(dr) > 2 else np.nan
okL1 = len(A) >= 10 and dlt <= -0.10 and -wt >= BAR and cr <= -0.5
pr(f"   A - B = {dlt:+.3f}R (Welch t {wt:.2f}); corr(A day R, SPY o-c) {cr:.2f}; PASS {okL1}")
for sp in ("train", "valid"):
    a, b = A[A.split == sp], B[B.split == sp]; pr(f"   {sp}: A n {len(a)} {a.r.mean():+.3f} | B n {len(b)} {b.r.mean():+.3f}")
if len(A): split_tbl(A, "class A")
Sx = L[~L.setup.isin(LONGS)].merge(bl, on=["date", "symbol"], how="left"); Sa = Sx[Sx.beta <= -1.5]
pr(f"   descriptive (no pass test): short lab setups on beta<=-1.5 symbols n {len(Sa)} avg {Sa.r.mean():+.3f}R vs other shorts {Sx[Sx.beta > -1.5].r.mean():+.3f}R")
res["L1"] = dict(n=len(A), avgR=round(A.r.mean(), 3) if len(A) else None, delta=round(dlt, 3) if len(A) else None, t=round(wt, 2) if len(A) > 1 else None,
                 corr=round(cr, 2) if cr == cr else None, passed=bool(okL1))
# ------------------------------------------------------------------ L2
F1 = frames("frames_tf/1min", ["QQQ", "IWM"], ["symbol", "date", "tod", "close", "atr_d", "fromOpen", "dist_hod_atr"])
F1["hod"] = F1.close + F1.dist_hod_atr * F1.atr_d; F1["below"] = F1.dist_hod_atr * F1.atr_d / F1.close * 100
Q = F1[F1.symbol == "QQQ"].set_index(["date", "tod"]); I = F1[F1.symbol == "IWM"].set_index(["date", "tod"])
J = Q[["hod"]].join(I[["fromOpen", "below"]], rsuffix="_i", how="inner").reset_index()
J["newhi"] = J.groupby("date").hod.diff() > 1e-9
J["run"] = J.groupby("date").below.transform(lambda b: (b >= 0.10).astype(int).groupby(((b < 0.10)).cumsum()).cumsum())
J["runprev"] = J.groupby("date").run.shift(1)
trig = J[(J.tod >= 1030) & (J.tod <= 1130) & J.newhi & (J.fromOpen >= 0.40) & (J.runprev >= 5)].groupby("date").tod.first()
days1 = J.date.nunique()
pr(f"\nL2 rotation turn: 1-min days {days1} ({J.date.min()}..{J.date.max()}), trigger days {len(trig)}")
ETF = ["XLK", "SMH", "SOXX", "XLE", "XLF", "XLI", "XLV", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "KRE"]
Wt = W[W.index < SPLIT]; Ce = Wt.corr().loc[:, ETF] if False else None
best = {}
E = Wt[ETF]
for c in Wt.columns:
    x = Wt[c]
    if x.notna().sum() < 60 or c in ETF: continue
    best[c] = E.corrwith(x).idxmax()
tech = {k for k, v in best.items() if v in ("XLK", "SMH", "SOXX")} | {"XLK", "SMH", "SOXX"}
mins = lambda t: (np.asarray(t) // 100) * 60 + np.asarray(t) % 100
FS = L[L.setup.isin(FAM)].copy(); FS["m"] = mins(FS.tod); FS["trig"] = FS.date.map(trig); FS["tm"] = mins(FS.trig.fillna(0))
FS["tag"] = FS.trig.notna() & (FS.m > FS.tm) & (FS.m <= FS.tm + 30) & ~FS.symbol.isin(tech)
tg = FS[FS.tag]; oth = FS[FS.trig.notna() & ~FS.tag]
dd = (tg.groupby("date").r.mean() - oth.groupby("date").r.mean())
tdd = dayt(dd)
okL2 = len(tg) >= 30 and tg.r.mean() >= 0.25 and dd.mean() >= 0.15 and tdd >= BAR
pr(f"   tech names excluded {len(tech)}; tagged n {len(tg)} on {tg.date.nunique()} days avg {tg.r.mean():+.3f}R; other family shorts on trigger days n {len(oth)} avg {oth.r.mean():+.3f}R")
pr(f"   paired day diff (tagged - other) {dd.mean():+.3f}R over {dd.notna().sum()} days, t {tdd}; PASS {okL2}")
if len(tg): split_tbl(tg, "tagged"); xb = exbest(tg); pr(f"   tagged w/o best day {xb[0]:+.3f}R, best-day share {xb[1]}")
for sp in ("train", "valid"):
    a = tg[tg.split == sp]; pr(f"   {sp}: tagged n {len(a)} {a.r.mean():+.3f}R")
res["L2"] = dict(trigger_days=int(len(trig)), n=len(tg), avgR=round(tg.r.mean(), 3) if len(tg) else None, diff=round(dd.mean(), 3) if len(dd.dropna()) else None,
                 t=tdd, passed=bool(okL2))
# ------------------------------------------------------------------ L3
sp5 = F5[F5.symbol == "SPY"].copy(); sp5["plow"] = sp5.groupby("date").low.shift(1)
brk = sp5[(sp5.tod > 1030) & (sp5.close < sp5.plow)].groupby("date").tod.first()
iwm10 = F5[(F5.symbol == "IWM") & (F5.tod == 1000)].set_index("date").fromOpen
qd = sorted(d for d in spy10.index if spy10.get(d, -9) >= 0.15 and iwm10.get(d, -9) >= 0.25)
cut = pd.Series({d: brk.get(d, 1050) for d in qd})
FQ = L[L.setup.isin(FAM) & L.date.isin(qd)].copy(); FQ["cut"] = FQ.date.map(cut); FQ["after"] = FQ.tod >= FQ.cut
bf, af = FQ[~FQ.after], FQ[FQ.after]
d3 = af.groupby("date").r.mean() - bf.groupby("date").r.mean(); t3 = dayt(d3)
diff3 = af.r.mean() - bf.r.mean()
okL3 = len(FQ) >= 40 and FQ.date.nunique() >= 6 and bf.r.mean() <= -0.20 and af.r.mean() >= 0 and diff3 >= 0.25 and t3 >= BAR
pr(f"\nL3 up-morning delay: qualifying days {len(qd)} (of {spy10.size}), cut median {int(cut.median()) if len(cut) else None}, cut=10:50 (no break) on {(~cut.index.isin(brk.index)).sum()} days")
pr(f"   before n {len(bf)} avg {bf.r.mean():+.3f}R | after n {len(af)} avg {af.r.mean():+.3f}R | after-before {diff3:+.3f}R; paired day diff {d3.mean():+.3f}R on {d3.notna().sum()} days t {t3}; PASS {okL3}")
for sp in ("train", "valid"):
    a, b = af[af.split == sp], bf[bf.split == sp]; pr(f"   {sp}: before n {len(b)} {b.r.mean():+.3f} | after n {len(a)} {a.r.mean():+.3f}")
pr("   by setup: " + "; ".join(f"{k[:4]} b {g[~g.after].r.mean():+.3f}({(~g.after).sum()}) a {g[g.after].r.mean():+.3f}({g.after.sum()})" for k, g in FQ.groupby("setup")))
split_tbl(af, "after"); split_tbl(bf, "before")
res["L3"] = dict(days=len(qd), n_before=len(bf), before=round(bf.r.mean(), 3), n_after=len(af), after=round(af.r.mean(), 3), t=t3, passed=bool(okL3))
# ------------------------------------------------------------------ L6
import glob
C = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(H / "context" / "*.parquet")))]); C["date"] = pd.to_datetime(C.date).dt.date.astype(str)
assert not C.date.between(LK0, LK1).any()
X6 = L.merge(C[["date", "tod", "spy_fo"]], on=["date", "tod"], how="left")
X6["side"] = np.where(X6.setup.str.contains("long"), 1, -1)
X6["ex"] = X6.r - X6.groupby(["setup", "split"]).r.transform("mean")
X6["counter"] = ((X6.side == -1) & (X6.spy_fo >= 0.25)) | ((X6.side == 1) & (X6.spy_fo <= -0.25))
X6["chase"] = ((X6.side == 1) & (X6.spy_fo >= 0.25)) | ((X6.side == -1) & (X6.spy_fo <= -0.25))
cn = X6[X6.counter]; d6 = cn.groupby("date").ex.mean(); alld = X6.date.unique()
t6 = dayt(cn.groupby("date").ex.sum().reindex(alld, fill_value=0.0)) if len(cn) else np.nan
ex_tr, ex_va = cn[cn.split == "train"].ex.mean(), cn[cn.split == "valid"].ex.mean()
bytype = cn.groupby("dtype").ex.mean()
ok6 = ex_tr >= 0.05 and ex_va >= 0.05 and t6 >= BAR and all(bytype.get(k, -1) > 0 for k in ("up", "down", "quiet"))
pr(f"\nL6 counter-index entries: spy_fo coverage {X6.spy_fo.notna().mean():.1%}; counter n {len(cn)} ({cn.side.eq(-1).mean():.0%} shorts) raw {cn.r.mean():+.3f}R excess {cn.ex.mean():+.3f}R | chase n {int(X6.chase.sum())} raw {X6[X6.chase].r.mean():+.3f}R excess {X6[X6.chase].ex.mean():+.3f}R | neither {X6[~X6.counter & ~X6.chase].r.mean():+.3f}R")
pr(f"   counter excess train {ex_tr:+.3f} / valid {ex_va:+.3f}; day-clustered t {t6}; PASS {ok6}")
pr("   counter excess by day type: " + "; ".join(f"{k} n {int((cn.dtype == k).sum())} {v:+.3f}R (raw {cn[cn.dtype == k].r.mean():+.3f})" for k, v in bytype.items()))
pr("   counter by side: " + "; ".join(f"{'long' if k == 1 else 'short'} n {len(g)} raw {g.r.mean():+.3f} excess {g.ex.mean():+.3f}" for k, g in cn.groupby("side")))
split_tbl(cn, "counter (raw R)")
xb = exbest(cn); pr(f"   counter raw w/o best day {xb[0]:+.3f}R, best-day share {xb[1]}")
res["L6"] = dict(n=len(cn), raw=round(cn.r.mean(), 3), excess=round(cn.ex.mean(), 3), train=round(ex_tr, 3), valid=round(ex_va, 3), t=t6,
                 by_type={k: round(v, 3) for k, v in bytype.items()}, passed=bool(ok6))
pr("\nEducational only - not financial advice.")
(OUT / "leads_bt_out.txt").write_text("\n".join(P) + "\n"); (OUT / "leads_bt.json").write_text(json.dumps(res, indent=1, default=float))
print("\n".join(P))
