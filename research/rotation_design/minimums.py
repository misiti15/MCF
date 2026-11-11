"""ROT design, owner input 2026-11-10 ~21:55 ET: "organize setups to be tested by traded sessions - not session counts but actual
sessions where setups have been traded in - then maybe trade count; unsure what figure makes sense."

Traded session = a session with >= 1 closed live (paper) trade of the setup (any account; benched / no-signal sessions do not count).
Grid: traded sessions S in {5, 8, 10, 15, 20} x trades N in {15, 20, 30, 50} = 20 minimum pairs (20 configurations, all reported).
For each non-GEN setup, D = the session on which it first has >= S traded sessions AND >= N trades (records up to D only).
Forward = the setup's NEXT 5 traded sessions after D (needs >= 3 to be scored). Reported per pair:
  setups reaching, scored setups, Pearson / Spearman correlation of avg R so far vs forward avg R, sign hit rate of avg R,
  sign hit rate of avg R without the best day (one-big-day check), median live sessions from the setup's first trade to D.
Time-to-reach for today's 72 in-scope setups: sessions still needed at the setup's own traded-session rate (traded sessions /
live sessions since its first trade) and trade rate.
Variance: day-clustered vs trade-level standard error (design effect) per setup -> effective trades.
Usage: python minimums.py   (reads trades_all.parquet, inventory.csv)   Educational only - not financial advice."""
from pathlib import Path
import json
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
T = pd.read_parquet(HERE / "trades_all.parquet"); T = T[~T.strategy.str.startswith("GEN-")].copy()
I = pd.read_csv(HERE / "inventory.csv")
DATES = sorted(T[T.acct == "primary"].date.unique()); DI = {d: i for i, d in enumerate(DATES)}
SS, NN, FWD, MINF = [5, 8, 10, 15, 20], [15, 20, 30, 50], 5, 3

daily = T.groupby(["strategy", "date"]).R.agg(["sum", "size"]).reset_index().sort_values(["strategy", "date"])
res = []
for S in SS:
    for N in NN:
        pts = []
        for s, g in daily.groupby("strategy"):
            g = g.reset_index(drop=True); g["cn"] = g["size"].cumsum(); g["k"] = np.arange(1, len(g) + 1)
            hit = g[(g.k >= S) & (g.cn >= N)]
            if not len(hit): continue
            j = hit.index[0]; past = g.loc[:j]; fut = g.loc[j + 1: j + FWD]
            first = past.date.iloc[0]; D = past.date.iloc[-1]
            row = dict(setup=s, D=D, wait=DI.get(D, np.nan) - DI.get(first, np.nan) + 1 if first in DI and D in DI else np.nan)
            tot = past["sum"].sum(); n = past["size"].sum(); bi = past["sum"].idxmax()
            row.update(past_avg=tot / n, past_exb=(tot - past.loc[bi, "sum"]) / (n - past.loc[bi, "size"]) if n > past.loc[bi, "size"] else np.nan,
                       fut_k=len(fut), fut_n=int(fut["size"].sum()), fut_avg=fut["sum"].sum() / fut["size"].sum() if len(fut) else np.nan)
            pts.append(row)
        P = pd.DataFrame(pts)
        sc = P[P.fut_k >= MINF] if len(P) else P
        r = dict(S=S, N=N, reach=len(P), scored=len(sc),
                 pearson=sc.past_avg.corr(sc.fut_avg) if len(sc) > 2 else np.nan,
                 spearman=sc.past_avg.corr(sc.fut_avg, method="spearman") if len(sc) > 2 else np.nan,
                 hit=(np.sign(sc.past_avg) == np.sign(sc.fut_avg)).mean() if len(sc) else np.nan,
                 hit_exb=(np.sign(sc.past_exb) == np.sign(sc.fut_avg)).mean() if len(sc) else np.nan,
                 pos_then_pos=((sc.past_avg > 0) & (sc.fut_avg > 0)).sum() / max((sc.past_avg > 0).sum(), 1) if len(sc) else np.nan,
                 n_pos=int((sc.past_avg > 0).sum()) if len(sc) else 0,
                 fut_avg_pos=sc[sc.past_avg > 0].fut_avg.mean() if len(sc) else np.nan,
                 fut_avg_neg=sc[sc.past_avg <= 0].fut_avg.mean() if len(sc) else np.nan,
                 base_fut_pos=(sc.fut_avg > 0).mean() if len(sc) else np.nan,
                 median_wait=P.wait.median() if len(P) else np.nan)
        # permutation p for the correlation (shuffle forward values), 2,000 draws, fixed seed
        if len(sc) > 4:
            rng = np.random.default_rng(1111); x, y = sc.past_avg.values, sc.fut_avg.values
            obs = np.corrcoef(x, y)[0, 1]; perm = [np.corrcoef(x, rng.permutation(y))[0, 1] for _ in range(2000)]
            r["perm_p"] = float(np.mean(np.array(perm) >= obs))
        res.append(r)
R = pd.DataFrame(res); R.to_csv(HERE / "minimums.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250)
print("configurations tried: 20 minimum pairs; forward = next 5 traded sessions (>= 3 needed)")
print(R.round(3).to_string(index=False))

# ---- time to reach for today's 72 in-scope setups ------------------------------------------------------------------
rows = []
for _, r in I.iterrows():
    g = T[T.strategy == r.setup]
    if len(g):
        first = g.date.min(); live = len([d for d in DATES if d >= first]); k = g.date.nunique(); n = len(g)
        kr, nr = k / live, n / live
    else:
        live, k, n, kr, nr = 0, 0, 0, np.nan, np.nan
    rows.append(dict(setup=r.setup, home=r.home, traded_sessions=k, trades=n, live_sessions=live, ts_rate=kr, tr_rate=nr))
X = pd.DataFrame(rows)
ttr = {}
for S, N in [(5, 15), (8, 20), (10, 30), (10, 20), (15, 30), (15, 50), (20, 50)]:
    need = []
    for _, x in X.iterrows():
        if x.traded_sessions >= S and x.trades >= N: need.append(0.0); continue
        if not (x.ts_rate > 0): need.append(np.inf); continue
        need.append(max((S - x.traded_sessions) / x.ts_rate, (N - x.trades) / x.tr_rate if x.tr_rate > 0 else np.inf, 0))
    nd = pd.Series(need, index=X.setup)
    ttr[f"{S}/{N}"] = dict(have_now=int((nd == 0).sum()), within_10=int((nd <= 10).sum()), within_20=int((nd <= 20).sum()),
                           never_at_current_rate=int(np.isinf(nd).sum()),
                           median_more_sessions_of_those_not_there=float(nd[(nd > 0) & np.isfinite(nd)].median()) if ((nd > 0) & np.isfinite(nd)).any() else None)
print("\ntime to reach (72 in-scope setups, at each setup's own traded-session and trade rate):")
print(pd.DataFrame(ttr).T.to_string())
X.to_csv(HERE / "traded_sessions.csv", index=False, float_format="%.3f")

# ---- variance: day is the noisy unit ---------------------------------------------------------------------------------
var = []
for s, g in T.groupby("strategy"):
    if len(g) < 40 or g.date.nunique() < 8: continue
    n = len(g); k = g.date.nunique(); se_iid = g.R.std(ddof=1) / n ** .5
    day = g.groupby("date").R.sum(); se_day = day.std(ddof=1) / k ** .5 / (n / k)   # SE of avg R per trade, clustered by day
    bd = day.max() / day.sum() if day.sum() > 0 else np.nan
    var.append(dict(setup=s, trades=n, traded_sessions=k, trades_per_session=n / k, se_trade=se_iid, se_day=se_day,
                    deff=(se_day / se_iid) ** 2, eff_trades=n / (se_day / se_iid) ** 2, best_day_share=bd))
V = pd.DataFrame(var).sort_values("deff", ascending=False); V.to_csv(HERE / "variance.csv", index=False, float_format="%.4f")
print("\nvariance (setups with >= 40 trades and >= 8 traded sessions):", len(V), "| median design effect", round(V.deff.median(), 2),
      "| corr(deff, trades/session)", round(V.deff.corr(V.trades_per_session), 2))
print(V.head(12).round(3).to_string(index=False))
print(V[V.setup.isin(["L3-gap-slope-fromopen-FD", "RW7-gapdn-bounce-early-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
                      "CWT14-failbrk-pdl-p10-long", "RW1-gapdn-bounce-flowsell-short-FD", "NS1-rsidip-rsi5pop-long-FD"])].round(3).to_string(index=False))
json.dump(dict(grid=R.to_dict("records"), time_to_reach=ttr, deff_median=float(V.deff.median())),
          open(HERE / "minimums_out.json", "w"), indent=1, default=float)
