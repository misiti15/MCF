"""BDI 2026-10-14 Part B2: index-aligned stop-and-reverse (PLAN.md Part B2, declared before scoring).
Re-uses the Part B per-signal outcomes in scratch (bdi1014_sar_trades.parquet); adds SPY fromOpen at the stop bar.
Educational only - not financial advice. The locked block is never loaded."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sar1014 as S  # noqa: E402
from sar1014 import lib, gates  # noqa: E402

N_STUDY = 480
N_LINEAGE = 120_599 + 10 + N_STUDY
T = pd.read_parquet(S.SCR / "bdi1014_sar_trades.parquet")
T["date"] = pd.to_datetime(T["date"]).dt.date
spy = []
for m in lib.months():
    f = lib.load_month(m, columns=["symbol", "date", "tod", "fromOpen"])
    f = f[f["symbol"].astype(str) == "SPY"][["date", "tod", "fromOpen"]]
    spy.append(f)
spy = pd.concat(spy).rename(columns={"tod": "stop_tod", "fromOpen": "spy_fo"})
T = T.merge(spy, on=["date", "stop_tod"], how="left")
reg = lib.regimes()
reg.index = pd.to_datetime(reg.index).date
pool = T[T["stopped"]].sort_values(["symbol", "date", "side", "stop_tod", "tod"]).groupby(["symbol", "date", "side", "stop_tod"]).head(1)
unst = T[~T["stopped"]].groupby(["symbol", "date", "side"]).head(1)
books = list(T.groupby("name")) + [("POOLED", pd.concat([pool, unst], ignore_index=True))]
rows = []
for k in (0.0, 0.25):
    for nm, d in books:
        d = d.copy()
        ok = (-d["side"]) * d["spy_fo"] > k
        for g in S.GEOMS:
            c = f"E2_{g}"
            d[c] = d[c].where(ok)
        rr = S.score_book(d.drop(columns=[c for c in d.columns if c.startswith("E1_")]), reg, nm)
        for r in rr:
            r["k"] = k
            v, fails = gates.verdict({"n": r["n"], "exp_r": r["exp"], "t": r["t"]},
                                     {"pass": (r["up"] or -1) > 0 and (r["down"] or -1) > 0}, {"share_positive": r["wf"]}, N_LINEAGE)
            r["verdict_lineage"] = v
        rows += rr
R = pd.DataFrame(rows)
t_l, t_s = gates.t_required(N_LINEAGE), gates.t_required(N_STUDY)
nbg = {"t05s1": ["t1s1"], "t1s1": ["t05s1", "t2s1", "t1s05"], "t2s1": ["t1s1"], "t1s05": ["t1s1"], "eods1": ["t2s1"]}


def plateau(r):
    same = R[(R.book == r.book) & (R.k == r.k) & R.geom.isin(nbg[r.geom])]
    other = R[(R.book == r.book) & (R.k != r.k) & (R.geom == r.geom)]
    return bool((same.exp > 0).all() and (other.exp > 0).all())


R["plateau"] = R.apply(plateau, axis=1)
common = (R.exp > 0) & (R.h1_exp > 0) & (R.h2_exp > 0) & (R.up > 0) & (R.down > 0) & (R.wf >= 0.6) & (R.ex_best_day > 0) & R.plateau
R["testing_pass"] = common & (R.t >= 2.0)
R["research_pass"] = common & (R.t >= t_l) & (R.excess > 0) & (R.verdict_lineage == "keep")
R["t_bar_lineage"], R["t_bar_study"] = t_l, t_s
R.to_csv(Path(__file__).resolve().parent / "sar_ix_results.csv", index=False)
s = {"configs_scored": 2 * len(R), "N_study": N_STUDY, "N_lineage": N_LINEAGE, "t_bar_lineage": t_l, "t_bar_study": t_s,
     "positive_exp": int((R.exp > 0).sum()), "testing_pass": int(R.testing_pass.sum()), "research_pass": int(R.research_pass.sum()),
     "spy_match_share": round(float(T.loc[T.stopped, "spy_fo"].notna().mean()), 4), "locked_block_loaded": False}
(Path(__file__).resolve().parent / "sar_ix_summary.json").write_text(json.dumps(s, indent=1))
print(json.dumps(s, indent=1))
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 200)
print(R[["k", "book", "geom", "n", "exp", "t", "h1_exp", "h2_exp", "up", "down", "wf", "excess", "excess_t", "ex_best_day", "comb_exp", "base_exp", "plateau", "testing_pass"]].to_string())
