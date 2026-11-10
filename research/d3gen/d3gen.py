"""D3GEN (plan PLAN.md, frozen before any score): old GEN screen vs a fold-based re-screen, ranked against live.
    python d3gen.py <hold_lists_dir> <j_gen.db>          Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml
sys.path.insert(0, "/home/user/guild/research/xapbo"); import pbo as PB
ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
cfg = yaml.safe_load(open(ROOT / "config/account_gen.yaml"))["strategies"]
G = {n: p for n, p in cfg.items() if n.startswith("GEN") and isinstance(p.get("gen"), dict)}
L = pd.concat([pd.read_parquet(p, columns=["setup", "date", "r"]) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet"))]
              + [pd.read_parquet(p, columns=["setup", "date", "r"]) for p in sorted(Path(sys.argv[1]).glob("sig_*.parquet"))])
L = L[L.setup.isin(G)].copy(); L["date"] = pd.to_datetime(L.date)
assert not ((L.date >= "2024-11-01") & (L.date <= "2025-02-28")).any()
c = sqlite3.connect(sys.argv[2])
J = pd.read_sql("select strategy, date, entry, stop, shares, pnl_adj, pnl from trades where run_id = 1 and exit_time is not null", c)
J["r"] = J.pnl_adj.fillna(J.pnl) / ((J.entry - J.stop).abs() * J.shares); J = J[np.isfinite(J.r)]
rows, mats = [], {}
for n, p in G.items():
    gd = pd.Timestamp(str(p["gen"]["date"]))
    x = L[(L.setup == n) & (L.date < gd)]; lv = J[J.strategy == n]
    if len(x) < 40 or len(lv) < 10: continue
    q = x.groupby(x.date.dt.to_period("Q")).r.agg(["mean", "size"]); q = q[q["size"] >= 20]
    if len(q) < 3: continue
    gday = lv.groupby("date").r.sum(); wob = lv[lv.date != gday.idxmax()].r.mean()
    sc = p["gen"].get("screen", {})
    rows.append(dict(setup=n, gen_date=str(gd.date()), lab_n=len(x), quarters=len(q), S1_worst_q=q["mean"].min(), S2_pos_share=(q["mean"] > 0).mean(),
                     S3_all_pos=bool((q["mean"] > 0).all()), lab_mean=x.r.mean(), old_score=sc.get("score"),
                     old_valid=(sc.get("valid") or {}).get("exp_r"), live_n=len(lv), live_avg=lv.r.mean(), live_wob=wob))
    mats[n] = x.groupby("date").r.sum()
R = pd.DataFrame(rows)
print(f"GEN setups scored: {len(R)} (>= 40 pre-gen lab trades, >= 3 quarters with >= 20, >= 10 live trades)")
rng = np.random.default_rng(20261110)
def sp(a, b):
    a, b = pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy(); r = np.corrcoef(a, b)[0, 1]
    perm = np.array([np.corrcoef(rng.permutation(a), b)[0, 1] for _ in range(1000)])
    return round(r, 3), round(float((perm >= r).mean()), 3)
out = []
for col in ("old_score", "old_valid", "lab_mean", "S1_worst_q", "S2_pos_share"):
    d = R.dropna(subset=[col])
    for tgt in ("live_avg", "live_wob"):
        rho, pv = sp(d[col], d[tgt]); out.append(dict(score=col, target=tgt, n=len(d), spearman=rho, perm_p_one_sided=pv))
O = pd.DataFrame(out); pd.set_option("display.width", 250); print(O.to_string(index=False))
s3 = R[R.S3_all_pos]; print(f"\nS3 all-quarters-positive survivors: {len(s3)} of {len(R)}; their live avg {s3.live_avg.mean():+.3f} (w/o best day "
      f"{s3.live_wob.mean():+.3f}) vs the rest {R[~R.S3_all_pos].live_avg.mean():+.3f} ({R[~R.S3_all_pos].live_wob.mean():+.3f})")
M = pd.DataFrame(mats).fillna(0.0).sort_index()
print("XA-PBO over the scored setups' pre-gen daily lab P&L:", {k: v for k, v in PB.pbo(M.to_numpy(), 16, "mean").items()})
s1 = O[(O.score == "S1_worst_q") & (O.target == "live_avg")].iloc[0]; old = O[(O.score == "old_score") & (O.target == "live_avg")].iloc[0]
print(f"\nVERDICT (fixed): S1 spearman {s1.spearman} (p {s1.perm_p_one_sided}) vs old {old.spearman} -> stricter screen ranks live better: "
      f"{bool(s1.spearman > old.spearman and s1.spearman > 0 and s1.perm_p_one_sided <= 0.10)}")
R.to_csv(HERE / "d3gen_setups.csv", index=False); O.to_csv(HERE / "d3gen_spearman.csv", index=False)
print("Educational only - not financial advice.")
