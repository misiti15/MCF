"""ONE-TIME lead scoring of the Saturday 2026-10-10 rework finalists on the rule-19 locked block 2024-11-01..2025-02-28
(look 2 for both lineages: bar exp > 0 and day-clustered t >= 1.5). Costs as W3 study.py. Written by the worker,
NEVER run by it on the block. Educational only - not financial advice.

Dry run (worker; open data only, locked block still blanked, reproduces the valid2 numbers of gates_ab.csv):
    python research/bdi/saturday1010/rework/score_locked.py --dry-run
Lead, once:
    for f in cboe_vol_indices_lockedblock finra_shvol_2024_lockedblock finra_shvol_2025_lockedblock; do
      git show origin/research-data:$f.parquet > research/bdi/saturday1010/rework/data/$f.parquet; done
    MCF_HIST_ALLOW_LOCKED=1 python research/bdi/saturday1010/rework/score_locked.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = HERE / "data"
W3 = ROOT / "research" / "swarm1010" / "w3_daily"
DRY = "--dry-run" in sys.argv
if not DRY and os.environ.get("MCF_HIST_ALLOW_LOCKED") != "1":
    raise SystemExit("locked scoring is the lead's: set MCF_HIST_ALLOW_LOCKED=1 (or use --dry-run)")

src = (W3 / "study.py").read_text().split('if __name__ == "__main__":')[0]
src = src.replace('cov.to_csv(HERE / "coverage_by_year.csv")', "pass")
src = src.replace('json.dump(regime_info, open(HERE / "regimes.json", "w"), indent=1)', "pass")
if not DRY:
    src = src.replace('LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")',
                      'LOCK_A, LOCK_B = pd.Timestamp("1900-01-01"), pd.Timestamp("1900-01-02")  # lead: no blanking')
S: dict = {"__name__": "w3study", "__file__": str(W3 / "study.py")}
exec(compile(src, str(W3 / "study.py"), "exec"), S)
dates, syms, T, N, C = S["dates"], S["syms"], S["T"], S["N"], S["C"]
ELIG200 = S["ELIG200"]


def load(name):
    d = pd.read_parquet(DATA / f"{name}.parquet")
    if not DRY:
        lb = DATA / f"{name}_lockedblock.parquet"
        if lb.exists():
            d = pd.concat([d, pd.read_parquet(lb)], ignore_index=True)
        elif name.startswith("cboe") or name in ("finra_shvol_2024", "finra_shvol_2025"):
            raise SystemExit(f"missing {lb.name}; fetch it from origin/research-data first")
    return d


# features: identical definitions to study_ab.py
vix = load("cboe_vol_indices")
vw = vix.pivot_table(index="date", columns="index", values="close").sort_index()
vw.index = pd.to_datetime(vw.index)
TR = (vw["VIX"] / vw["VIX3M"]).reindex(dates).to_numpy()
VIXP = vw["VIX"].dropna().rolling(252, min_periods=200).apply(lambda x: (x <= x[-1]).mean(), raw=True).reindex(dates).to_numpy()
uni = set(syms)
parts = []
for y in range(2019, 2027):
    f = load(f"finra_shvol_{y}")[["date", "symbol", "shortvolume", "totalvolume"]]
    f = f[f.symbol.isin(uni) & (f.totalvolume > 0)]
    parts.append(pd.DataFrame({"date": pd.to_datetime(f.date), "symbol": f.symbol.astype(str),
                               "r": (f.shortvolume / f.totalvolume).astype("float32")}))
fin = pd.concat(parts, ignore_index=True).drop_duplicates(["date", "symbol"])
SVR20 = fin.pivot(index="date", columns="symbol", values="r").sort_index().rolling(20, min_periods=10).mean() \
    .reindex(index=dates, columns=syms).to_numpy(float)
del fin, parts


def lag1(x):
    out = np.empty_like(x); out[0] = np.nan; out[1:] = x[:-1]
    return out


def xs_top(X, elig, q):
    A = np.where(elig, X, np.nan)
    out = np.zeros((T, N), bool)
    for i in range(T):
        a = A[i]
        if np.isfinite(a).sum() >= 20:
            out[i] = a >= np.nanquantile(a, 1 - q)
    return out


D19 = np.asarray(dates >= "2019-01-02")[:, None]
with np.errstate(invalid="ignore"):
    above = (C > S["sma200"]).to_numpy()
    sigA = above & (S["rsi3"] < 5).to_numpy() & (VIXP >= 0.3)[:, None]
    sigB = S["xs_decile"](S["ret5"], ELIG200, False) & (lag1(TR) >= 0.95)[:, None] & ~xs_top(lag1(SVR20), ELIG200, 0.20) & D19
FINALISTS = {
    "A_b35_VP30": (lambda: S["make_trades"](sigA, 1, "O", "SMA5", elig=ELIG200), 5),
    "B_k20_TR95+SV20": (lambda: S["make_trades"](sigB, 1, "C", "K", k=20, elig=ELIG200), 20),
}
A_, B_ = (pd.Timestamp("2025-03-01"), pd.Timestamp("2026-12-31")) if DRY else (pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28"))
out = {"_window": f"{A_.date()}..{B_.date()}", "_dry_run": DRY, "_bar": "look 2: exp > 0 and day-clustered t >= 1.5"}
for name, (fn, hold) in FINALISTS.items():
    t = fn()
    t["excess"] = t.gross - S["bench"](t)
    ed = dates[t.ei.to_numpy()]
    t = t[(ed >= A_) & (ed <= B_)] if not DRY else t[(t.date >= A_) & (t.date <= B_)]
    r = t["net"].to_numpy()
    d = pd.Series(r).groupby(dates[t.i.to_numpy()]).agg(["sum", "size"])
    mu = r.mean(); se = math.sqrt(((d["sum"] - d["size"] * mu) ** 2).sum()) / len(r)
    blk = t.i.to_numpy() // (2 * hold)
    db = pd.Series(r).groupby(blk).agg(["sum", "size"])
    seb = math.sqrt(((db["sum"] - db["size"] * mu) ** 2).sum()) / len(r)
    res = {"n": int(len(r)), "net_bps": round(mu * 1e4, 1), "t_day_clustered": round(mu / se, 2),
           "t_block_clustered": round(mu / seb, 2), "win_rate": round(float((r > 0).mean()), 3),
           "excess_bps": round(float(t.excess.mean()) * 1e4, 1), "sessions": int(t.i.nunique())}
    if not DRY:
        res["pass_look2"] = bool(res["net_bps"] > 0 and res["t_day_clustered"] >= 1.5)
    out[name] = res
    print(name, res, flush=True)
json.dump(out, open(HERE / ("locked_dryrun.json" if DRY else "locked.json"), "w"), indent=1)
