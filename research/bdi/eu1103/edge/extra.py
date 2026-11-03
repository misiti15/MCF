"""eu1103/edge Q1 extras on per_trade.csv.gz (decompose.py): beta-neutral alpha per profitable setup with day-clustered t
and the one-big-day check; target touch-fill optimism (paper fills a limit on a touch; does the bar trade THROUGH it?);
fade intensity vs residual R. Usage: python extra.py <scratch>. Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

S = Path(sys.argv[1]); OUT = Path(__file__).parent
T = pd.read_csv(S / "per_trade.csv.gz")
for c in ("entry_time", "exit_time"):
    T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert("America/New_York")
T["alpha"] = T.R_net - T.mkt        # net R with the SPY-beta part taken out (what a beta hedge would have left)

def tstat(df, col):
    g = df.groupby("date")[col].agg(["sum", "size"]); mu = df[col].mean()
    se = np.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(df)
    return float(mu / se) if se > 0 else np.nan
def wo_best(df, col):
    d = df.groupby("date")[col].sum(); b = d.idxmax()
    return float((d.sum() - d.max()) / max(1, len(df) - (df.date == b).sum())), (float(d.max() / d.sum()) if d.sum() > 0 else np.nan)

res = {}
rows = []
for (a, s), g in T.groupby(["account", "strategy"]):
    if len(g) < 20 or g.R_net.mean() <= 0:
        continue
    w, sh = wo_best(g, "R_net"); wa, sha = wo_best(g, "alpha")
    rows.append(dict(account=a, strategy=s, n=len(g), sessions=g.date.nunique(), R=g.R_net.mean(), t=tstat(g, "R_net"),
                     R_wo_best=w, best_share=sh, mkt=g.mkt.mean(), alpha=g.alpha.mean(), t_alpha=tstat(g, "alpha"),
                     alpha_wo_best=wa, alpha_best_share=sha, fric=g.fric.mean(), side=g.side.mean()))
P = pd.DataFrame(rows).sort_values("R", ascending=False)
P.round(3).to_csv(OUT / "profitable_alpha.csv", index=False)
res["profitable"] = {"setups": len(P), "t_ge_1.5": int((P.t >= 1.5).sum()), "alpha_pos": int((P.alpha > 0).sum()),
                     "alpha_pos_wo_best": int((P.alpha_wo_best > 0).sum()), "R_wo_best_pos": int((P.R_wo_best > 0).sum()),
                     "alpha_t_ge_1.5": int((P.t_alpha >= 1.5).sum()), "best_share_ge_50": int((P.best_share >= 0.5).sum()),
                     "mkt_share_of_R": round(float((P.mkt * P.n).sum() / (P.R * P.n).sum()), 3)}

# target exits: paper fills a limit when the price TOUCHES it. Re-check on the 1-minute bar of the exit and the next one:
# 'through' = the bar traded at least 1c beyond the target (a real resting limit very likely fills), 'touch only' = not.
X = pd.read_parquet(S / "live_bars.parquet"); X["ts"] = pd.to_datetime(X.ts, utc=True).dt.tz_convert("America/New_York")
X = X.set_index(["symbol", "ts"]).sort_index()
tg = T[T.exit_reason == "target"].copy()
thr = []
for _, r in tg.iterrows():
    m = r.exit_time.floor("min"); best = np.nan
    for k in (0, 1):
        try:
            b = X.loc[(r.symbol, m + pd.Timedelta(minutes=k))]
        except KeyError:
            continue
        v = (b.high - r.target) if r.side > 0 else (r.target - b.low)
        best = v if np.isnan(best) else max(best, v)
    thr.append(best)
tg["beyond"] = thr
ok = tg.beyond.notna()
through = tg.beyond >= 0.01
res["target_fills"] = {"n": int(len(tg)), "with_bar": int(ok.sum()), "traded_through_1c": round(float(through[ok].mean()), 3),
                       "touch_only": round(float((~through)[ok].mean()), 3),
                       "R_if_touch_only_missed_flat0": round(float(-(tg.loc[ok & ~through, "R_net"]).sum() / len(T)), 4)}
# if touch-only target fills had NOT filled, the trade would have run on; a conservative bound: they earn 0 instead of R
# (the stop is still there). The per-book delta in R per trade is reported above.

# fade intensity: prior 30-minute move in units of the stop distance, vs alpha
T["move30_R"] = T.side * T.ret30 * T.entry / T.rps
q = pd.qcut(T.move30_R, 5, duplicates="drop")
res["alpha_by_prior_move_quintile"] = {str(k): {"n": int(len(g)), "alpha": round(float(g.alpha.mean()), 4),
                                                "R_net": round(float(g.R_net.mean()), 4), "timing": round(float(g.timing.mean()), 4)}
                                       for k, g in T.groupby(q, observed=True)}
# book: net R decomposition total
res["book_sum"] = {k: round(float(T[k].sum()), 1) for k in ("R_net", "mkt", "drift", "timing", "fric", "alpha")}
res["book_alpha_t"] = round(tstat(T, "alpha"), 2)
json.dump(res, open(OUT / "extra.json", "w"), indent=1)
print(json.dumps(res, indent=1))
print(P.round(3).to_string())
