"""LATCH-CLOSE (research/bdi/1111/LATCH_CLOSE_PLAN.md, pre-registered and committed df979d85d before this read).
ONE config. bt_lab1104 2-year lab lists + burst1/enrich.py 5-min marks (<enr>), live caps, -2R per-setup latch, costs in,
locked block excluded (asserted). Usage: python latch_close.py <enr dir>   Educational only - not financial advice."""
import math, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult  # noqa: F401  (entry cost already inside r; exit side only below)
E = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
LOCK = ("2024-11-01", "2025-02-28"); L = 2.0
fam = lambda s: re.sub(r"\d.*", "", s).split("-")[0]
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
mins = lambda tod: (np.asarray(tod) // 100) * 60 + np.asarray(tod) % 100


def caps(sym, en, ex, per_sym=3, per_setup=30):
    keep = np.zeros(len(en), bool)
    for i in range(len(en)):
        o = keep[:i] & (ex[:i] > en[i])
        if o.sum() < per_setup and (o & (sym[:i] == sym[i])).sum() < per_sym:
            keep[i] = True
    return keep


rows = []; nsd = 0; nlatch = 0
for f in sorted(E.glob("[0-9]*.parquet")):
    t = pd.read_parquet(f).reset_index(drop=True); mk = np.load(str(f).replace(".parquet", "_mk.npy")).astype(np.float32)
    t["date"] = t.date.astype(str)
    assert not ((t.date >= LOCK[0]) & (t.date <= LOCK[1])).any()
    t["ri"] = np.arange(len(t))
    t = t.sort_values(["setup", "date", "tod", "symbol"], kind="mergesort")
    for (su, d), g in t.groupby(["setup", "date"], sort=False):
        nsd += 1
        g = g[caps(g.symbol.to_numpy(), g.tod.to_numpy(), g.xtod.to_numpy())]
        en, ex, r = g.tod.to_numpy(), g.xtod.to_numpy(), g.r.to_numpy(float)
        # latch: blocked once realised R of exits at or before the entry bar <= -L (stoplab lab2y rule)
        latch = None
        # latch bar = first exit bar where cumulative realised (taken, exit-ordered) <= -L
        o = np.argsort(ex, kind="mergesort"); xs = ex[o]; cr = np.cumsum(r[o])
        ub = np.unique(xs)
        for x in ub:
            if cr[np.searchsorted(xs, x, side="right") - 1] <= -L + 1e-9: latch = x; break
        if latch is None: continue
        nlatch += 1
        taken = en < latch            # entries at / after the latch bar are blocked (ex <= en rule)
        nb = int(mins(latch) + 5)     # next bar (start minute); close at its close
        nbt = (nb // 60) * 100 + nb % 60
        aff = taken & (en < latch) & (ex > nbt)
        if not aff.any(): continue
        a = g[aff].copy(); sl = int((nb - 590) // 5)
        if sl > 73: continue
        mrow = pd.DataFrame(mk[a.ri.to_numpy()]).ffill(axis=1).to_numpy()
        a["mark"] = mrow[:, sl]
        a["cost"] = (0.01 + a.entry * 1e-4) / (a.entry * a.stop_pct)
        a["alt"] = a.mark - a.cost; a["latch"] = latch
        rows.append(a)
T = pd.concat(rows, ignore_index=True).dropna(subset=["alt", "r"])
T["d"] = T.alt - T.r; T["fam"] = T.setup.map(fam)
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
p(f"setup-days {nsd:,}; latched {nlatch:,}; affected lots {len(T):,} ({T.setup.nunique()} setups, {T.date.nunique()} days); "
  f"actual {T.r.sum():+.1f}R ({T.r.mean():+.4f}) -> closed {T.alt.sum():+.1f}R ({T.alt.mean():+.4f}); configs 1")
res = {}
for sp in ("TRAIN", "VALID", "LATE"):
    g = T[T.split == sp]
    if g.empty: continue
    daily = g.groupby("date").d.sum()
    t_ = daily.mean() / (daily.std(ddof=1) / math.sqrt(len(daily))) if len(daily) > 2 else np.nan
    best = daily.max(); res[sp] = dict(delta=daily.sum(), t=t_, wob=daily.sum() - best, n=len(g), days=len(daily))
    p(f"{sp}: affected {len(g):,} lots on {len(daily)} days | actual {g.r.sum():+.1f}R -> closed {g.alt.sum():+.1f}R | "
      f"delta {daily.sum():+.1f}R ({g.d.mean():+.3f}/lot), day-t {t_:.2f}, days better {(daily > 0).mean():.0%}; "
      f"best day {daily.idxmax()} {best:+.1f}R, w/o best {daily.sum() - best:+.1f}R")
    x = g.groupby("side").agg(n=("d", "size"), delta=("d", "sum"))
    p("   by side: " + "; ".join(f"{'long' if k == 1 else 'short'} {int(v.n)} lots {v.delta:+.1f}R" for k, v in x.iterrows()))
V = T[T.split == "VALID"]
fg = V.groupby("fam").agg(n=("d", "size"), act=("r", "sum"), delta=("d", "sum"))
fq = fg[fg.n >= 30].sort_values("delta")
nb_, nw_ = int((fq.delta > 0).sum()), int((fq.delta < 0).sum())
p(f"VALID families (>= 30 affected): {nb_} better, {nw_} worse of {len(fq)}")
for k, v in fg.sort_values("delta").iterrows():
    p(f"   {k}: {int(v.n)} lots, actual {v.act:+.1f}R, delta {v.delta:+.1f}R{'' if v.n >= 30 else ' (< 30, not counted)'}")
sg = V.groupby(["setup", "side"]).agg(n=("d", "size"), delta=("d", "sum")).reset_index(); sq = sg[sg.n >= 20]
p(f"VALID setups (>= 20 affected): {int((sq.delta > 0).sum())} better (+{sq.delta[sq.delta > 0].sum():.1f}R) / "
  f"{int((sq.delta < 0).sum())} worse ({sq.delta[sq.delta < 0].sum():+.1f}R) of {len(sq)}")
for _, v in sq.sort_values("delta").iterrows():
    p(f"   {v.setup} ({'long' if v.side == 1 else 'short'}): {int(v.n)} lots, delta {v.delta:+.1f}R")
v = res.get("VALID", {}); tr = res.get("TRAIN", {})
ok = v.get("t", 0) >= 2.89 and tr.get("delta", 0) > 0 and v.get("wob", 0) > 0 and nb_ >= 0.6 * max(len(fq), 1)
p(f"VERDICT: VALID t {v.get('t', np.nan):.2f} vs 2.89 (BAR90 2.60); TRAIN delta {tr.get('delta', np.nan):+.1f}R; "
  f"VALID w/o best {v.get('wob', np.nan):+.1f}R; families better {nb_}/{len(fq)} -> {'PASS' if ok else 'FAIL'}")
T.to_csv(HERE / "latch_close_lots.csv.gz", index=False, columns=["setup", "side", "symbol", "date", "tod", "xtod", "latch", "r", "alt", "d", "fam", "split"])
(HERE / "latch_close_out.txt").write_text("\n".join(out) + "\n\nEducational only - not financial advice.\n")
