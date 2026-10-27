"""LATE-CUT scoring (research/ops/late_entry1027.md section 0, declared before this ran).
Usage: G21SCR=$SCRATCH/szp/g python research/ops/late_entry1027/late.py <journals_dir> > research/ops/late_entry1027/late_out.txt
<journals_dir>/<acct>/journal.db for acct in p t1 t2 (live paper, run_id 1) - information only.
Writes results.csv (per setup x cutoff), by_hour.csv, exit_time.csv next to this file.
Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCR = Path(os.environ["G21SCR"])
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
TRAIN_END = pd.Timestamp("2025-12-31").date()
CUTS = (1330, 1400, 1430)
N_CONF = 51 * len(CUTS) * 2
BAR = round(max(1.5, math.sqrt(2 * math.log(N_CONF))), 2)
NM = json.load(open(ROOT / "docs/live/setup_names.json"))
ASG = json.loads((ROOT / "docs/live/assignments.json").read_text())["accounts"]


def name(s):
    if s in NM:
        return NM[s]["name"]
    if s.endswith("-FD") and s[:-3] in NM:
        return NM[s[:-3]]["name"] + " (all day)"
    return "?"


def acct_of(s):
    return "+".join(a for a, lab in (("primary", "P"), ("testing", "T1"), ("testing2", "T2")) if s in ASG[a]) or "-"


def load_trades() -> pd.DataFrame:
    st = pd.read_csv(SCR / "setups.csv")
    keymap = dict(zip(st["setup"], st["ids"]))
    geom = dict(zip(st["setup"], st["geom"]))
    parts = []
    for p in sorted((SCR / "sig").glob("*.parquet")):
        x = pd.read_parquet(p)
        if "error" in x:
            assert x["error"].isna().all(), x[x["error"].notna()]
            x = x.drop(columns="error")
        parts.append(x)
    s = pd.concat(parts, ignore_index=True)
    s["date"] = pd.to_datetime(s["date"]).dt.date
    assert not ((s["date"] >= LOCK[0]) & (s["date"] <= LOCK[1])).any(), "locked row"
    s["geom"] = s["key"].map(geom)
    out = []
    for k, g in s.groupby("key"):
        for i in keymap[k].split(","):
            out.append(g.assign(setup=i))
    t = pd.concat(out, ignore_index=True)
    t["split"] = np.where(t["date"] <= TRAIN_END, "train", "valid")
    from mcf.research.gates import GEOMK
    dn = t["geom"].map(lambda g: GEOMK[g][1])
    gross = t["r"]  # kind from the outcome: target if win, stop if R at/below -dn (costs make it < -dn), else flatten
    t["kind"] = np.where(t["win"] == 1, "target", np.where(gross <= -dn + 1e-6, "stop", "flatten"))
    return t


def mins(tod):
    t = np.asarray(tod, float)                 # NaN stays NaN (bracket hit after 15:00: minute unknown)
    return np.floor(t / 100) * 60 + np.mod(t, 100)


def tstat_days(r: pd.Series, d: pd.Series, all_days) -> float:
    """Day-clustered t of the per-session sum (sessions with no late trade count as 0)."""
    x = r.groupby(d).sum().reindex(all_days, fill_value=0.0)
    if len(x) < 2 or x.std(ddof=1) == 0:
        return float("nan")
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))))


def hour_bucket(tod):
    return pd.cut(tod, [0, 1059, 1159, 1259, 1359, 1500], labels=["09:50-11", "11-12", "12-13", "13-14", "14-15"])


def main():
    t = load_trades()
    days = sorted(t["date"].unique())
    print(f"trades {len(t)}, setups {t.setup.nunique()}, sessions {len(days)}, N configs {N_CONF}, bar {BAR}")
    rows = []
    for s, g in t.groupby("setup"):
        sd = sorted(g["date"].unique())
        for C in CUTS:
            late = g[g.tod > C]; early = g[g.tod <= C]
            r = dict(setup=s, name=name(s), acct=acct_of(s), cut=C, n=len(g), sumR=g.r.sum(), avgR=g.r.mean(),
                     late_n=len(late), late_avg=late.r.mean() if len(late) else np.nan, late_sum=late.r.sum(),
                     early_avg=early.r.mean(), late_win=(late.r > 0).mean() if len(late) else np.nan,
                     late_flat_share=(late.kind == "flatten").mean() if len(late) else np.nan)
            for sp in ("train", "valid"):
                L = late[late.split == sp]; E = early[early.split == sp]
                r[f"late_avg_{sp}"] = L.r.mean() if len(L) else np.nan
                r[f"late_sum_{sp}"] = L.r.sum()
                r[f"late_n_{sp}"] = len(L)
                r[f"early_avg_{sp}"] = E.r.mean() if len(E) else np.nan
            r["t_improve"] = tstat_days(-late.r, late.date, sd) if len(late) else np.nan
            rows.append(r)
    R = pd.DataFrame(rows)
    # plateau: neighbour cutoffs also negative late sum
    R["c1"] = R.late_n >= 30
    R["c2"] = (R.late_avg_train < R.early_avg_train) & (R.late_avg_valid < R.early_avg_valid)
    R["c3"] = (R.late_sum_train < 0) & (R.late_sum_valid < 0)
    R["c4"] = R.t_improve >= BAR
    neg = R.set_index(["setup", "cut"])["late_sum"] < 0
    pl = []
    for r in R.itertuples():
        i = CUTS.index(r.cut)
        nb = [CUTS[j] for j in (i - 1, i + 1) if 0 <= j < len(CUTS)]
        pl.append(all(neg[(r.setup, c)] for c in nb))
    R["c5"] = pl
    R["passes"] = R[["c1", "c2", "c3", "c4", "c5"]].all(axis=1)
    R.round(4).to_csv(HERE / "results.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
    print("\n== per-setup x cutoff (skip / half share conditions; N =", N_CONF, ")")
    print("passing rows:", int(R.passes.sum()))
    for c in ("c1", "c2", "c3", "c4", "c5"):
        print(f"  {c} met: {int(R[c].sum())} of {len(R)}")
    near = R[R.c1 & R.c2 & R.c3].sort_values("t_improve", ascending=False)
    print("\n-- rows meeting 1-3 (late worse than early in train AND valid, late sum < 0 in both):", len(near))
    print(near[["setup", "acct", "cut", "n", "avgR", "late_n", "late_avg", "late_avg_train", "late_avg_valid",
                "early_avg_train", "early_avg_valid", "late_sum", "t_improve", "c5", "passes"]].round(3).to_string(index=False))
    print("\n-- 14:00 cutoff, every setup")
    x = R[R.cut == 1400].sort_values("late_avg")
    print(x[["setup", "acct", "n", "avgR", "late_n", "late_avg", "early_avg", "late_avg_train", "late_avg_valid",
             "late_sum", "late_flat_share", "t_improve"]].round(3).to_string(index=False))
    # by hour
    t["hb"] = hour_bucket(t.tod)
    H = t.groupby(["setup", "hb", "split"], observed=True).r.agg(["size", "mean"]).unstack("split")
    H.columns = [f"{a}_{b}" for a, b in H.columns]
    H.round(4).to_csv(HERE / "by_hour.csv")
    pooled = t.groupby(["hb", "split"], observed=True).r.agg(["size", "mean"]).unstack("split").round(4)
    print("\n-- pooled all 51 setups by entry hour (information; NOT a basis for any cutoff)"); print(pooled.to_string())
    # time to exit
    t["exit_tod2"] = np.where((t.kind != "flatten") & (t.exit_tod >= 1555), np.nan, t.exit_tod)
    t["held_min"] = np.where(t.kind == "flatten", mins(1555) - mins(t.tod), mins(t.exit_tod2) - mins(t.tod))
    t["after1500"] = (t.kind != "flatten") & (t.exit_tod >= 1555)
    E = t.groupby(["setup", "hb"], observed=True).agg(
        n=("r", "size"), target=("kind", lambda k: (k == "target").mean()), stop=("kind", lambda k: (k == "stop").mean()),
        flat1555=("kind", lambda k: (k == "flatten").mean()), hit_after1500=("after1500", "mean"),
        med_min_target=("held_min", lambda v: np.nanmedian(np.where(t.loc[v.index, "kind"] == "target", v, np.nan)) if (t.loc[v.index, "kind"] == "target").any() else np.nan),
        avgR=("r", "mean"))
    E.round(3).to_csv(HERE / "exit_time.csv")
    pe = t.groupby("hb", observed=True).agg(n=("r", "size"), target=("kind", lambda k: (k == "target").mean()),
                                            stop=("kind", lambda k: (k == "stop").mean()),
                                            flat1555=("kind", lambda k: (k == "flatten").mean()), avgR=("r", "mean"))
    print("\n-- pooled exit mix by entry hour (two-year, 51 setups)"); print(pe.round(3).to_string())
    tg = t[t.kind == "target"]
    q = tg.groupby("setup").held_min.quantile([0.5, 0.8]).unstack().round(0)
    q.columns = ["med_min_to_target", "p80_min_to_target"]
    print("\n-- minutes from entry to target (target hits only; within-day), per setup"); print(q.to_string())
    # live information
    if len(sys.argv) > 1:
        J = Path(sys.argv[1]); L = []
        for a in ("p", "t1", "t2"):
            x = pd.read_sql("select * from trades where run_id=1", sqlite3.connect(J / a / "journal.db"))
            x["acct"] = a; L.append(x)
        L = pd.concat(L, ignore_index=True)
        L["risk"] = L.shares * (L.entry - L.stop).abs(); L["R"] = L.pnl_adj / L.risk
        L["et"] = pd.to_datetime(L.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
        L["late"] = L.et.dt.hour >= 14
        P = L[L.acct == "p"]
        for lab, x in (("all", P), ("through 10-26", P[P.date <= "2026-10-26"])):
            y = x[x.late]
            print(f"\nlive Primary entries >= 14:00 ({lab}): n {len(y)}, flatten {int((y.exit_reason == 'flatten').sum())}, "
                  f"avg R after costs {y.R.mean():+.3f}, journal r_multiple {y.r_multiple.mean():+.3f}; earlier entries avg R {x[~x.late].R.mean():+.3f} (n {int((~x.late).sum())})")
        g = L.groupby(["strategy", "late"]).R.agg(["size", "mean"]).unstack("late")
        g.columns = [f"{'late' if b else 'early'}_{a}" for a, b in g.columns]
        g = g[g.index.isin(R.setup)].dropna(subset=["late_size"]).sort_values("late_size", ascending=False)
        print("\n-- live paper (P/T1/T2) by setup: entries before vs from 14:00 (information)"); print(g.round(3).to_string())
    print("\nEducational only - not financial advice.")


if __name__ == "__main__":
    main()
