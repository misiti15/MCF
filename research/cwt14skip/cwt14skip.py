"""CWT14SKIP (guild Builder, plan PLAN.md frozen 2026-11-09 before any score): skip a CWT14 failed-break LONG entry
when the name is already >= X daily ATR below its open at the entry bar. X in {1.0, 1.5}; N 10 (with swing1104-L8).
Excess over a same-day random block of equal size (200 draws), retention 80% trades / 90% top-decile winners.
    python cwt14skip.py > cwt14skip_out.txt        Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib
from mcf.research import gates as G
HERE = Path(__file__).resolve().parent
LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date(); SPLIT = pd.Timestamp("2025-09-30").date()
N_LINEAGE = 8 + 2; T_FULL = G.t_required(N_LINEAGE); T90 = round(max(1.35, 0.9 * T_FULL), 2)
XS = [1.0, 1.5]; NDRAW = 200

BT = ROOT / "research/history2y/data/bt_lab1104"
L = pd.concat(pd.read_parquet(p) for p in sorted(BT.glob("sig_*.parquet")))
L["date"] = pd.to_datetime(L["date"]).dt.date
assert not ((L.date >= LK0) & (L.date <= LK1)).any()
P = L[L.setup.str.startswith("CWT14-failbrk") & L.setup.str.endswith("-long")].copy().reset_index(drop=True)
P["tod"] = P.tod.astype(int)
print(f"pool: {len(P)} trades, {P.setup.nunique()} variants {sorted(P.setup.unique())}, {P.date.nunique()} days "
      f"({P.date.min()}..{P.date.max()}, locked absent); lineage N {N_LINEAGE}: full bar {T_FULL}, BAR90 {T90}", flush=True)

# point-in-time distance below the open at the entry bar, from the lab frames
parts = []
for m in sorted(pd.to_datetime(P.date).dt.strftime("%Y-%m").unique()):
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "fromOpen", "atr_d"])
    f["tod"] = f.tod.astype(int)
    parts.append(P[pd.to_datetime(P.date).dt.strftime("%Y-%m") == m].reset_index().merge(f, on=["symbol", "date", "tod"], how="left"))
P = pd.concat(parts).set_index("index").sort_index()
miss = P.close.isna().mean(); print(f"frame join missing {miss:.2%} (missing rows count as kept)")
P["_m"] = pd.to_datetime(P.date).dt.strftime("%Y-%m")
print("A1(3) join-miss share by variant:", P.groupby("setup").close.apply(lambda c: round(c.isna().mean(), 4)).to_dict())
mm = P.groupby("_m").close.apply(lambda c: round(c.isna().mean(), 4)); print("A1(3) join-miss share by month:", mm[mm > 0].to_dict() or "none")
op = P.close / (1 + P.fromOpen / 100)
P["dist"] = (op - P.close) / P.atr_d
P[["setup", "symbol", "date", "tod", "r", "fromOpen", "dist"]].to_csv(HERE / "cwt14_dist.csv", index=False)

D = lib.daily(); S = D[D.symbol == "SPY"].set_index("date"); oc = S.close / S.open - 1
dtype = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=S.index)
top = P.r >= P.r.quantile(.9)
rng = np.random.default_rng(20261109)
byday = {d: g.index.to_numpy() for d, g in P.groupby("date")}
VAR = P.setup.to_numpy()
r = P.r.to_numpy(); pos = {ix: i for i, ix in enumerate(P.index)}

rows = []
for X in XS:
    skip = (P.dist >= X).fillna(False).to_numpy()
    ex = {}
    for d, ixs in byday.items():
        ii = np.array([pos[i] for i in ixs]); k = int(skip[ii].sum())
        if k == 0: ex[d] = 0.0; continue
        real = -r[ii][skip[ii]].sum()
        # Amendment 1 (1): the random block is drawn within the same variant, k_v per variant that day
        blocks = [(ii[VAR[ii] == v], int((skip[ii] & (VAR[ii] == v)).sum())) for v in np.unique(VAR[ii])]
        rnd = np.mean([sum(-r[rng.choice(jj, kv, replace=False)].sum() for jj, kv in blocks if kv) for _ in range(NDRAW)])
        ex[d] = real - rnd
    E = pd.Series(ex).sort_index(); Ed = pd.Series(E.index, index=E.index)
    def tstat(s): return round(s.mean() / (s.std(ddof=1) / np.sqrt(len(s))), 2) if len(s) > 2 and s.std() > 0 else None
    tr, va = E[Ed <= SPLIT], E[Ed > SPLIT]
    wob = E.drop(E.idxmax())
    ty = E.groupby(E.index.map(dtype)).sum()
    per = []
    for s_, g in P.groupby("setup"):
        sk = skip[[pos[i] for i in g.index]]
        tv = (g.r >= g.r.quantile(.9)).to_numpy()
        per.append((s_, int(sk.sum()), round(-g.r[sk].sum() + g.r[sk].size * g.r.mean(), 1), round(1 - sk.mean(), 3),
                    round(1 - sk[tv].mean(), 3)))   # skipped vs own mean; A1(2) kept share, own top-decile kept
    better = sum(1 for _, n, v, *_ in per if v > 0); worse = sum(1 for _, n, v, *_ in per if v < 0)
    dts = P.date.map(dtype).to_numpy(); skn = {k: int(skip[dts == k].sum()) for k in ("up", "down", "quiet")}
    row = dict(config=f"CWT14SKIP-X{X:.1f}", n_pool=len(P), skipped=int(skip.sum()), kept_share=round(1 - skip.mean(), 3),
               top_kept=round(1 - skip[top.to_numpy()].mean(), 3), pool_avg=round(r.mean(), 4), kept_avg=round(r[~skip].mean(), 4),
               skipped_avg=round(r[skip].mean(), 4) if skip.any() else None, excess_total=round(E.sum(), 1),
               excess_t=tstat(E), train_ex=round(tr.sum(), 1), train_t=tstat(tr), valid_ex=round(va.sum(), 1), valid_t=tstat(va),
               ex_wo_best=round(wob.sum(), 1), best_day_share=round(E.max() / E.sum(), 2) if E.sum() > 0 else None,
               up=round(ty.get("up", 0), 1), down=round(ty.get("down", 0), 1), quiet=round(ty.get("quiet", 0), 1),
               skips_up=skn["up"], skips_down=skn["down"], skips_quiet=skn["quiet"],
               better=better, worse=worse, per_variant="; ".join(f"{s_.replace('CWT14-failbrk-', '')} n{n} {v:+} kept{k} top{tk}" for s_, n, v, k, tk in per))
    row["pass"] = bool((row["excess_t"] or 0) >= T90 and row["train_ex"] > 0 and row["valid_ex"] > 0 and row["ex_wo_best"] > 0
                       and row["kept_share"] >= .8 and row["top_kept"] >= .9 and better > worse)
    rows.append(row)

R = pd.DataFrame(rows); pd.set_option("display.width", 400); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 400)
print(R.to_string(index=False))
print("\nexcess = skipped-R removed minus a same-day random equal-size block (200 draws); t day-clustered over all pool days;"
      "\nper_variant = R saved vs skipping the same number of that variant's average trade (+ = better); uncapped chains (no re-entry effect).")
print(f"configs 2 (lineage {N_LINEAGE}), pass {int(R['pass'].sum())}")
R.to_csv(HERE / "cwt14skip_results.csv", index=False)
print("Educational only - not financial advice.")
