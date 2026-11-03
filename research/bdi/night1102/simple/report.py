"""night1102/simple: tables for NOTES.md from score.py output (scratch trades.parquet / ctrl.parquet) and the journals.
Usage: python report.py <scratch>  -> results.csv, report_out.txt (stdout). Educational only - not financial advice."""
from __future__ import annotations

import math
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(HERE)]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
from score import KERNELS  # noqa: E402

S = Path(sys.argv[1])
T = pd.read_parquet(S / "trades.parquet")
C = pd.read_parquet(S / "ctrl.parquet")
REG = lib.regimes()
N_CFG = T.drop_duplicates(["kernel", "form"]).shape[0]


def ckey(k, form):
    K = KERNELS[k]
    return (K["side"], K["geom"], str(K["win"]), 150e6 if "150M" in form else K["adv"])


def dstat(t, col="r"):
    if not len(t):
        return dict(n=0, exp=np.nan, t=np.nan)
    s = G.summary(t.rename(columns={col: "r"})[["date", "r"]] if col != "r" else t[["date", "r"]])
    return dict(n=s["n"], exp=s["exp_r"], t=s.get("t"), wob=s.get("ex_best_day"))


# live-period day regime proxy: universe median fromOpen at the 15:00 bar, history tercile cuts of med_o2c
lf = pd.read_parquet(S / "live_frames.parquet", columns=["date", "tod", "fromOpen"])
lf["date"] = pd.to_datetime(lf["date"]).dt.date
med = lf[lf.tod == 1500].groupby("date").fromOpen.median()
lo, hi = REG.attrs.get("cuts") or np.quantile(REG.med_o2c, [1 / 3, 2 / 3])
LREG = pd.Series(np.where(med <= lo, "down", np.where(med >= hi, "up", "flat")), index=med.index)

rows = []
for (k, form), g in T.groupby(["kernel", "form"], sort=False):
    side, geom, win, adv = ckey(k, form)
    cc = C[(C.side == side) & (C.geom == geom) & (C.win == win) & (C.adv == adv)][["date", "ctrl", "split"]]
    g = g.merge(cc[["date", "ctrl"]], on="date", how="left")
    g["ex"] = g.r - g.ctrl
    row = dict(kernel=k, form=form, k=int(g.k.iloc[0]))
    for sp in ("TRAIN", "VALID", "LIVE"):
        x = g[g.split == sp]
        days = cc[cc.split == sp].date.nunique()
        a, e = dstat(x), dstat(x.assign(r=x.ex))
        row.update({f"{sp}_n": a["n"], f"{sp}_perday": a["n"] / max(days, 1), f"{sp}_exp": a["exp"], f"{sp}_t": a["t"],
                    f"{sp}_ex": e["exp"], f"{sp}_ex_t": e["t"]})
        if sp == "LIVE" and len(x):
            reg = x.date.map(LREG)
            row.update(LIVE_up=x.r[reg == "up"].mean(), LIVE_down=x.r[reg == "down"].mean(), LIVE_wob=a["wob"])
    tv = g[g.split.isin(["TRAIN", "VALID"])]
    a, e = dstat(tv), dstat(tv.assign(r=tv.ex))
    rs = G.regime_split(tv[["date", "r"]], REG)
    wf = G.walk_forward(tv[["date", "r"]])
    row.update(TV_n=a["n"], TV_exp=a["exp"], TV_t=a["t"], TV_wob=a.get("wob"), TV_ex=e["exp"], TV_ex_t=e["t"],
               up=rs["up"].get("exp_r"), down=rs["down"].get("exp_r"), regime_pass=rs["pass"], wf=wf["share_positive"])
    rows.append(row)
R = pd.DataFrame(rows)
bar90 = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N_CFG))))
R["bar90_study"] = (R.TV_t >= bar90) & (R.wf >= 0.54) & R.regime_pass & (R.TV_ex > 0)
par = R[R.form.str.startswith("parent")].groupby("kernel").first()
for c in ("TV_exp", "TV_n", "LIVE_exp", "LIVE_n", "TRAIN_exp", "VALID_exp"):
    R[f"par_{c}"] = R.kernel.map(par[c])
R["keeps"] = (R.TV_exp >= R.par_TV_exp) & (R.TV_n >= R.par_TV_n) & ~R.form.str.startswith("parent")
R["twin"] = R.keeps & (R.TRAIN_exp > 0) & (R.VALID_exp > 0) & (R.TRAIN_ex > 0) & (R.VALID_ex > 0) & (R.LIVE_exp >= R.par_LIVE_exp)
R.to_csv(HERE / "results.csv", index=False, float_format="%.4f")

# actual live paper trades of the parent (journals) and the re-score's match with them
J = S / "j"
live = []
for br in ("mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard"):
    c = sqlite3.connect(J / f"{br}.db")
    t = pd.read_sql("select symbol,strategy,date,entry,stop,shares,pnl_adj from trades where run_id=1 and date>='2026-10-06' "
                    "and date<='2026-11-02'", c)
    live.append(t.assign(acct=br))
L = pd.concat(live)
L = L[(L.entry - L.stop).abs() * L.shares > 0]
L["R"] = L.pnl_adj / ((L.entry - L.stop).abs() * L.shares)

pd.set_option("display.width", 260); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 60)
print(f"configurations scored (distinct kernel x form): {N_CFG}; BAR90 at study N: t >= {bar90:.2f}")
print("live-period regime proxy:", LREG.value_counts().to_dict())
print("\n== parity of the LIVE re-score with the actual paper trades (parent, symbol-date) ==")
for k in KERNELS:
    p = T[(T.kernel == k) & (T.split == "LIVE") & T.form.str.startswith("parent")]
    p = p[p.form == p.form.iloc[0]] if len(p) else p
    a = L[L.strategy == k]
    ka = set(zip(a.symbol, a.date)); kp = set(zip(p.symbol, p.date.astype(str)))
    both = ka & kp
    print(f"{k:45s} paper {len(a):4d} trades avg {a.R.mean():+.3f}R | re-score {len(p):4d} avg {p.r.mean():+.3f}R | "
          f"paper symbol-days found in re-score {len(both)}/{len(ka)}; on matched: paper {a[[x in both for x in zip(a.symbol, a.date)]].R.mean():+.3f}R")
cols = ["form", "k", "TV_n", "TRAIN_perday", "TRAIN_exp", "VALID_exp", "TV_t", "TV_ex", "TV_ex_t", "up", "down", "wf",
        "LIVE_n", "LIVE_exp", "LIVE_t", "LIVE_ex", "LIVE_up", "LIVE_down", "keeps", "twin"]
for k in KERNELS:
    print(f"\n== {k} ==")
    print(R[R.kernel == k].sort_values(["k", "TV_exp"], ascending=[False, False])[cols].round(3).to_string(index=False))
print("\n== summary: does a simpler form keep or improve avg R with more trades? ==")
for k in KERNELS:
    x = R[(R.kernel == k) & ~R.form.str.startswith("parent")]
    print(f"{k:45s} forms {len(x):2d} | keeps {int(x.keeps.sum()):2d} | twin {int(x.twin.sum()):2d} | better TV exp {int((x.TV_exp > x.par_TV_exp).sum()):2d}"
          f" | better LIVE exp {int((x.LIVE_exp > x.par_LIVE_exp).sum()):2d} | TV>0 {int((x.TV_exp > 0).sum())} | LIVE>0 {int((x.LIVE_exp > 0).sum())}")
print("\n== every form: positive in TRAIN, VALID and the LIVE re-score (any trade count) ==")
z = R[(R.TRAIN_exp > 0) & (R.VALID_exp > 0) & (R.LIVE_exp > 0)]
print(z[["kernel"] + cols + ["bar90_study"]].round(3).to_string(index=False) if len(z) else "none")
print("\n== BAR90 at study N (t, WF >= 54%, up & down > 0, beats random): ", int(R.bar90_study.sum()), "pass")
# by condition count across kernels (pooled forms)
print("\n== avg R by number of conditions (mean over forms of each kernel; TV and LIVE) ==")
print(R.groupby("k").agg(forms=("form", "size"), TV_perday=("TRAIN_perday", "median"), TV_exp=("TV_exp", "mean"),
                         TV_ex=("TV_ex", "mean"), LIVE_exp=("LIVE_exp", "mean"), LIVE_ex=("LIVE_ex", "mean")).round(3).to_string())
