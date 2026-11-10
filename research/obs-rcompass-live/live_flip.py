"""Observer: the rolling compass on LIVE trades (Lead lead-20261109-2300-4: which setups does the owner most need switched off on flips?).
Descriptive, 0 configs; flip definitions imported unchanged from Scout's frozen research/rcompass/rcompass.py (day_flips, classify),
compass rows from Builder's research/compassbf/compass_2y.csv.gz (live code, re-run on bars). Live paper trades, all 7 accounts,
run_id 1, entries >= 12:00 ET. 'aligned' = trade side equals the morning reading M; a standby rule would remove post-flip aligned trades.
Net R (pnl_adj / risk) as the owner sees it; small live sample, so this is a map of where flips bit, not evidence for a rule.
usage (from the guild root): python research/obs-rcompass-live/live_flip.py <journal_dir>. Educational only - not financial advice."""
import sys, glob, os, sqlite3, numpy as np, pandas as pd
sys.path.insert(0, "research/rcompass")
from rcompass import day_flips, classify
pd.set_option("display.width", 220)
C = pd.read_csv("research/compassbf/compass_2y.csv.gz")
R = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.db"))):
    a = os.path.basename(f).replace("mcf-data-", "").replace(".db", "").replace("mcf-data", "primary")
    t = pd.read_sql("select date,symbol,strategy,side,entry_time,entry,stop,shares,pnl_adj from trades where run_id=1 and exit is not null", sqlite3.connect(f))
    t["acct"] = a; R.append(t)
T = pd.concat(R, ignore_index=True); T = T[T.date.isin(C.date.unique())]
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
T["em"] = T.et.dt.hour * 60 + T.et.dt.minute
T["R"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares).replace(0, np.nan)
T = T[(T.em >= 720) & T.R.notna()].copy()
T["fam"] = T.strategy.str.extract(r"^(GEN|[A-Za-z]+\d*)")[0]
days = {}
for d, g in C[C.date.isin(T.date.unique())].groupby("date"): days[d] = day_flips(g)
print(f"live afternoon trades {len(T)}, sessions {T.date.nunique()} ({T.date.min()}..{T.date.max()})")
for d in sorted(days): M, f = days[d]; print(f"  {d}  M={M}  " + "  ".join(f"{k}={'%02d:%02d' % divmod(v, 60) if v else '-'}" for k, v in (f or {}).items()))
for K in ("F1", "F2", "F3"):
    rows = []
    for _, r in T.iterrows():
        M, f = days.get(r.date, (None, {}))
        if M is None: continue
        rows.append((r.name, classify(r.em, f.get(K)), "aligned" if (r.side == 1) == (M == "UP") else "counter"))
    Z = T.join(pd.DataFrame(rows, columns=["i", "cls", "al"]).set_index("i"), how="inner"); assert Z.index.is_unique
    print(f"\n=== {K}: reading-day afternoon trades {len(Z)} | flip days {Z[Z.cls != 'held_day'].date.nunique()} | held days {Z[Z.cls == 'held_day'].date.nunique()}")
    print(Z.groupby(["cls", "al"]).R.agg(["count", "mean", "sum"]).round(3).to_string())
    if K == "F1":
        P = Z[(Z.cls == "post_flip") & (Z.al == "aligned")]; H = Z[(Z.cls == "held_day") & (Z.al == "aligned")]
        g = P.groupby("fam").R.agg(post_n="count", post_avg="mean", post_sum="sum").join(H.groupby("fam").R.agg(held_n="count", held_avg="mean"), how="left")
        g["days"] = P.groupby("fam").date.nunique()
        print("\nF1 post-flip ALIGNED trades by family (what a standby would have removed) vs the same family aligned on held days:\n",
              g.sort_values("post_sum").round(3).to_string())
        print("\n  by account:", P.groupby("acct").R.agg(["count", "sum"]).round(2).to_dict("index"))
        cc = Z[Z.fam == "CWT12"]; print("\n  CWT12 coil (owner-named), F1 classes:\n", cc.groupby(["cls", "al"]).R.agg(["count", "mean", "sum"]).round(3).to_string())
print("Educational only - not financial advice.")
