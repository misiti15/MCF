"""night1102/regime step 4a: simple point-in-time regime switches scored on LIVE paper trades (all accounts,
10-06..11-02). A switch reads one market state at T (09:50 / 10:00 / 10:30, bar closed at T) and decides, for the rest
of the day, whether longs and/or shorts may open. Trades entered before T are untouched. 'vs random' = kept R minus
total R x kept share (positive = the switch removed worse-than-average trades). Every rule x book is counted.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCR = Path(sys.argv[1])
OUT = Path(__file__).resolve().parents[1]
T = pd.read_parquet(SCR / "tagged.parquet")
D = pd.read_parquet(SCR / "days.parquet")


def states(t):
    return {
        f"vwap@{t}": np.where(D[f"vw_SPY@{t}"] >= 0, "up", "down"),
        f"fo@{t}": np.where(D[f"fo_SPY@{t}"] >= 0, "up", "down"),
        f"fo25@{t}": np.where(D[f"fo_SPY@{t}"] >= 0.25, "up", np.where(D[f"fo_SPY@{t}"] <= -0.25, "down", "flat")),
        f"br@{t}": np.where(D[f"br@{t}"] >= 0, "up", "down"),
    }


ST = {}
for t in (950, 1000, 1030):
    for k, v in states(t).items():
        ST[k] = pd.Series(v, index=D.index)
for t in (950, 1030):
    ST[f"rng@{t}"] = pd.Series(np.where(D[f"rngr@{t}"] >= (0.3 if t == 950 else 0.5), "active", "calm"), index=D.index)

# rules: (name, allow(side, state) -> bool)
from switch_rules import RULES  # noqa: E402
CORE = ["MF2-open-rsimidhi-flowsell-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
        "L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "MF4-h40-open-flowsell-FD", "RW1-gapdn-bounce-flowsell-short-FD"]
BOOKS = {"all": T, "primary": T[T.acct == "P"], "longs": T[T.side > 0], "shorts": T[T.side < 0],
         "core7": T[T.strategy.isin(CORE)]}


def score(t, keep):
    tot = t.R.sum(); k = t[keep]
    share = keep.mean()
    dk = k.groupby("date").R.sum().reindex(sorted(t.date.unique()), fill_value=0)
    dt = t.groupby("date").R.sum()
    diff = dk - dt * share
    se = diff.std(ddof=1) / np.sqrt(len(diff)) if len(diff) > 1 else np.nan
    return {"kept_pct": 100 * share, "total_R": tot, "kept_R": k.R.sum(), "kept_avg": k.R.mean(), "all_avg": t.R.mean(),
            "vs_random": k.R.sum() - tot * share, "vs_random_t": diff.sum() / (se * len(diff)) if se and se > 0 else np.nan,
            "green_days_kept": (dk > 0).mean(), "worst_day_kept": dk.min(), "worst_day_all": dt.min()}


rows = []
for sname, s in ST.items():
    tcut = int(sname.split("@")[1])
    for rname, f in RULES.items():
        if ("rng" in sname) != ("calm" in rname):
            continue
        if "fo25" not in sname and rname == "follow":
            continue  # no flat state: same as follow_strict
        for bname, t in BOOKS.items():
            st = t.date.map(s).to_numpy()
            keep = np.array([(e < tcut) or f(sd, x) for e, sd, x in zip(t.etod, t.side, st)])
            rows.append({"state": sname, "rule": rname, "book": bname, **score(t, pd.Series(keep, index=t.index))})
R = pd.DataFrame(rows)
R.round(3).to_csv(OUT / "switch_live.csv", index=False)
print("configs", len(R), "rules x states", len(R) // len(BOOKS))
pd.set_option("display.width", 250)
for b in BOOKS:
    print(f"\n== {b}")
    print(R[R.book == b].sort_values("vs_random", ascending=False).head(8).round(2).to_string(index=False))
