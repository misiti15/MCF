"""saturday1031 B: burst risk sharing (backlog nightly-1029-burst20-one-bet). PLAN.md section B was written first.
A burst = one setup entering >= K symbols on the same 5-min bar (live: the same 5-min entry bucket). Rule: each lot of a
burst of n lots is sized at C / n of normal risk, so the burst risks C R in total. No trade is removed; exits unchanged.
Configs (6): K in {10, 20} x C in {3, 5, 10}.
Part 1, two years (lab_trades, locked block absent, old holdouts dropped): burst lots vs the rest, weighted book.
Part 2, live paper (journals, run 1, all 5 accounts, costs in): the same weights on the realized $ curve by exit time:
per day peak -> close give-back, close, and what the best days give up.
Usage: python burst.py <scratch>   Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
out = []; P = lambda *x: out.append(" ".join(str(y) for y in x))
CFGS = [(K, C) for K in (10, 20) for C in (3, 5, 10)]
bar = max(1.5, np.sqrt(2 * np.log(6)))
# ---------------------------------------------------------------- part 1: two years
L = pd.read_parquet(ROOT / "research/history2y/data/lab_trades.parquet")
ds = L.date.astype(str)
assert not ds.between("2024-11-01", "2025-02-28").any()
L = L[~(ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16"))].reset_index(drop=True)
L["date"] = L.date.astype(str)
L["split"] = np.where(L.date <= "2025-08-31", "train", "valid")
D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close"])
D["date"] = pd.to_datetime(D.date).dt.date.astype(str)
REG = G.session_regimes(D[["date", "open", "close"]])["regime"]
L["regime"] = L.date.map(REG)
L["bn"] = L.groupby(["setup", "date", "tod"]).r.transform("size")
P(f"# Part 1: two-year lab trades {len(L)}, sessions {L.date.nunique()}, setups {L.setup.nunique()}; bar t >= {bar:.2f} (N 6)")
P("burst size distribution (share of trades): " + ", ".join(f">= {k}: {(L.bn >= k).mean():.3f}" for k in (5, 10, 20, 40)))
def tday_diff(x, m):
    """day-clustered t of (mean R of rest - mean R of burst lots): per day, sum over burst lots of (r - rest mean)."""
    mu_rest = x.loc[~m, "r"].mean()
    g = (x.loc[m, "r"] - mu_rest).groupby(x.loc[m, "date"]).sum()
    se = np.sqrt((g ** 2).sum()) / m.sum()
    return -(x.loc[m, "r"].mean() - mu_rest) / se if se > 0 else np.nan
rows = []
base_day = L.groupby("date").r.sum()
for K, C in CFGS:
    m = (L.bn >= K).to_numpy()
    w = np.where(m, np.minimum(1.0, C / L.bn.to_numpy()), 1.0)
    r = dict(K=K, C=C, burst_lots=int(m.sum()), burst_share=m.mean(), burst_avgR=L.r[m].mean(), rest_avgR=L.r[~m].mean(),
             t_rest_minus_burst=tday_diff(L, m))
    for sp in ("train", "valid"):
        mm = (L.split == sp).to_numpy()
        r[f"burst_{sp}"] = L.r[m & mm].mean(); r[f"rest_{sp}"] = L.r[~m & mm].mean()
        r[f"wR_{sp}"] = (w[mm] * L.r.to_numpy()[mm]).sum() / w[mm].sum()
        r[f"R_{sp}"] = L.r[mm].mean()
    for rg in ("up", "down"):
        mm = (L.regime == rg).to_numpy()
        r[f"burst_{rg}"] = L.r[m & mm].mean(); r[f"rest_{rg}"] = L.r[~m & mm].mean()
    day = pd.Series(w * L.r.to_numpy()).groupby(L.date.to_numpy()).sum()
    r["day_std_base"], r["day_std_rule"] = base_day.std(), day.std()
    r["worst5_base"], r["worst5_rule"] = base_day.nsmallest(5).sum(), day.nsmallest(5).sum()
    r["best5_base"], r["best5_rule"] = base_day.nlargest(5).sum(), day.nlargest(5).sum()
    top = L.r >= L.r.quantile(0.9)
    r["top10_wR_kept"] = (w[top] * L.r[top]).sum() / L.r[top].sum()
    r["pass"] = bool(r["burst_train"] < r["rest_train"] and r["burst_valid"] < r["rest_valid"] and r["burst_up"] < r["rest_up"]
                     and r["burst_down"] < r["rest_down"] and r["wR_train"] > r["R_train"] and r["wR_valid"] > r["R_valid"]
                     and r["t_rest_minus_burst"] >= bar)
    rows.append(r)
R1 = pd.DataFrame(rows)
P(R1.round(4).T.to_string())
P("\nburst lots (K 10) by setup: " + str(L[L.bn >= 10].groupby("setup").r.agg(["size", "mean"]).round(3).sort_values("size").tail(8).to_dict("index")))
R1.to_csv(OUT / "burst2y.csv", index=False)
# ---------------------------------------------------------------- part 2: live paper
P("\n# Part 2: live paper journals (run 1, costs in), realized $ curve by exit time")
AC = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2", "gy": "Graveyard", "gen": "Gen"}
rows = []
for a, nm in AC.items():
    t = pd.read_sql("select date, strategy, entry_time, exit_time, entry, stop, shares, pnl_adj from trades where run_id=1 and exit_time is not null",
                    sqlite3.connect(S / a / "journal.db"))
    t["risk"] = ((t.entry - t.stop).abs() * t.shares).replace(0, np.nan)
    t["R"] = t.pnl_adj / t.risk
    t = t[np.isfinite(t.R)]
    et = pd.to_datetime(t.entry_time, utc=True, format="mixed"); xt = pd.to_datetime(t.exit_time, utc=True, format="mixed")
    t["bucket"] = et.dt.floor("5min"); t["xt"] = xt
    t["bn"] = t.groupby(["strategy", "bucket"]).R.transform("size")
    for K, C in [(None, None)] + CFGS:
        w = np.ones(len(t)) if K is None else np.where(t.bn >= K, np.minimum(1.0, C / t.bn), 1.0)
        x = t.assign(pw=t.pnl_adj * w, Rw=t.R * w, w=w).sort_values("xt")
        gb, cl, pk, swing = [], [], [], 0
        for d, g in x.groupby("date"):
            cur = g.pw.cumsum(); peak = max(0.0, cur.max()); close = cur.iloc[-1]
            gb.append(peak - close); cl.append(close); pk.append(peak)
            swing += int(peak >= 100 and close < 0)
        rows.append(dict(acct=nm, K=K or "-", C=C or "-", days=len(cl), trades=len(x), burst_lots=int((t.bn >= (K or 10**9)).sum()),
                         pl=x.pw.sum(), R=x.Rw.sum(), R_per_risk=x.Rw.sum() / x.w.sum(), giveback_mean=np.mean(gb),
                         giveback_max=np.max(gb), worst_day=np.min(cl), best_day=np.max(cl), swing_days=swing,
                         green=int((np.array(cl) > 0).sum())))
R2 = pd.DataFrame(rows)
P(R2.round(3).to_string(index=False))
R2.to_csv(OUT / "burst_live.csv", index=False)
open(OUT / "burst_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
