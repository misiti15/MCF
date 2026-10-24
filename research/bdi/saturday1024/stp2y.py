"""saturday1024: ST-P 2-year detail for Primary (B0 vs S1.5 / S2 / S3 from book_sim.py): blocked trades, monthly
walk of the delta, without the best day, by setup. Usage: python stp2y.py <exits.parquet> > stp2y_out.txt
Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
import book_sim as B

sig = B.load_sig(None)
sig["side_i"] = np.where(sig["setup"].map(B.U["side"]) == "long", 1, -1)
ex = pd.read_parquet(sys.argv[1]); ex["date"] = pd.to_datetime(ex["date"]).dt.date
sig = sig.merge(ex[["setup", "symbol", "date", "tod", "exit_sim"]].drop_duplicates(["setup", "symbol", "date", "tod"]),
                on=["setup", "symbol", "date", "tod"], how="left")
sig["exit_tod"] = sig["exit_tod"].fillna(sig["exit_sim"]).fillna(1555)
ak, ck, cap, bstop, X = B.BOOKS["Primary"]
members = [s for s in B.ASG[ak] if s in B.U.index]
groups = B.twin_groups(B.account_cfg(ck))
s = sig[sig["setup"].isin(members)].sort_values(["date", "tod", "symbol", "setup"]).reset_index(drop=True)
acc = {}
for name, rule in [("B0", {}), ("S1.5", {"S": 1.5}), ("S2", {"S": 2.0}), ("S3", {"S": 3.0})]:
    a = np.zeros(len(s), bool)
    for d, g in s.groupby("date"):
        a[g.index.to_numpy()] = B.sim_day(g, rule, cap, bstop, X, groups)[0]
    acc[name] = a
s["month"] = pd.to_datetime(s["date"]).dt.strftime("%Y-%m")
b0 = acc["B0"]
for name in ("S1.5", "S2", "S3"):
    blk = b0 & ~acc[name]
    print(f"== {name}: blocked {blk.sum()} of {b0.sum()} ({100 * blk.mean() / b0.mean():.1f}%), blocked avg R "
          f"{s.r[blk].mean():+.4f} (train {s.r[blk & (s.split == 'train')].mean():+.4f} / valid "
          f"{s.r[blk & (s.split == 'valid')].mean():+.4f}), blocked winners {100 * (s.r[blk] > 0).mean():.1f}%")
    dd = (s.r.where(acc[name], 0).groupby(s.date).sum() - s.r.where(b0, 0).groupby(s.date).sum())
    mo = dd.groupby(pd.to_datetime(dd.index).strftime("%Y-%m")).sum()
    print(f"   months with delta > 0: {(mo > 0).sum()} of {len(mo)} ({100 * (mo > 0).mean():.0f}%); >= 0: {(mo >= 0).sum()}")
    print(f"   total delta {dd.sum():+.1f}R; without the best day {dd.sum() - dd.max():+.1f}R; best day {dd.idxmax()} {dd.max():+.1f}R; "
          f"worst day {dd.idxmin()} {dd.min():+.1f}R; days changed {(dd != 0).sum()} (better {(dd > 0).sum()} / worse {(dd < 0).sum()})")
    print("   monthly delta R:", " ".join(f"{k[2:]}:{v:+.1f}" for k, v in mo.items()))
    per = pd.DataFrame({"setup": s.setup, "b0": s.r.where(b0), "v": s.r.where(acc[name])}).groupby("setup").agg(
        b0_n=("b0", "count"), b0_sum=("b0", "sum"), v_n=("v", "count"), v_sum=("v", "sum"))
    per["delta_R"] = per.v_sum - per.b0_sum
    db0 = s.r.where(b0, 0).groupby(s.date).sum(); dv = s.r.where(acc[name], 0).groupby(s.date).sum()
    top = db0.sort_values(ascending=False).head(20).index
    print(f"   book's 20 best days (B0 {db0[top].sum():+.1f}R): with {name} {dv[top].sum():+.1f}R "
          f"(give-up {dv[top].sum() - db0[top].sum():+.1f}R; days cut {(dv[top] < db0[top] - 1e-9).sum()})")
    pos = db0 > 0
    print(f"   all {pos.sum()} green B0 days: give-up {(dv[pos] - db0[pos]).sum():+.1f}R; red days: {(dv[~pos] - db0[~pos]).sum():+.1f}R")
    if name == "S2":
        print(per.round(1).to_string())
print("Educational only - not financial advice.")
