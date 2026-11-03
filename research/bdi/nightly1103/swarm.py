"""Small swarm, nightly 2026-11-03 (4 configurations, declared before scoring), on the 2-year lab trade lists
(research/history2y/data/lab_trades.parquet, production costs; the locked block 2024-11-01..2025-02-28 is not in the file
and is never read) and the 5-minute index context (research/history2y/data/context: SPY % from the open).

  U1..U3  swing1103 lead L3 "up-morning delay": skip short-family entries (RW3, RW5, MF2, MF4 lab versions) entered
          before 10:50 on days SPY is >= +0.10 / +0.15 / +0.25 % above its open at 10:00. (The lead's IWM leg is not in the
          context file; SPY only.)
  V1      swing1103 lead L1 "vol-ETP beta guard": NS5 longs skip volatility ETPs (UVIX UVXY VXX VIXY VIXM SVIX SVXY).

A skip rule helps iff the skipped trades lose: day-clustered t of the skipped trades' R (sign flipped) over all split
sessions. Pass = skipped avg R < 0 in train AND valid, valid n >= 30, valid t >= max(1.5, sqrt(2 ln 4)) = 1.665.
Train < 2025-09-01, valid >= 2025-09-01. Not testable on these lists: the BRAKE-1 time gate and the -2R latch (no exit
times in the lab lists). Usage: python swarm.py   Educational only - not financial advice."""
import sys, glob
from pathlib import Path
import numpy as np, pandas as pd
WT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-nightly"
sys.path.insert(0, WT)
from mcf.research.gates import t_required
H = Path("/home/user/MCF/research/history2y/data"); OUT = Path(__file__).resolve().parent
L = pd.read_parquet(H / "lab_trades.parquet"); L["date"] = L.date.astype(str)
assert not L.date.between("2024-11-01", "2025-02-28").any(), "locked block present"
C = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(H / "context" / "*.parquet")))]); C["date"] = C.date.astype(str)
spy10 = C[C.tod == 1000].set_index("date").spy_fo
L["split"] = np.where(L.date < "2025-09-01", "train", "valid")
N = 4; bar = t_required(N)
FAM = ["RW3 bdi-rw-gapdn-rsi5pop-flowsell", "RW5 bdi-rw-heat30-flowsell-rsi5pop-gapdn", "MF2-open-rsimidhi-flowsell", "MF4-h40-open-flowsell"]
VOL = {"UVIX", "UVXY", "VXX", "VIXY", "VIXM", "SVIX", "SVXY"}


def stats(sk, pool, s):
    days = pool[pool.split == s].date.unique(); x = sk[sk.split == s]
    if len(x) == 0: return dict(n=0, avgR=np.nan, sumR=0.0, t=np.nan, exbest=np.nan)
    day = (-x.groupby("date").r.sum()).reindex(days, fill_value=0.0)
    t = day.mean() / (day.std(ddof=1) / np.sqrt(len(day))) if day.std() > 0 else np.nan
    bd = x.groupby("date").r.sum().idxmin()                      # the skip's best day = the skipped trades' worst day
    ex = x[x.date != bd].r.mean() if x.date.nunique() > 1 else np.nan
    return dict(n=len(x), avgR=round(x.r.mean(), 3), sumR=round(x.r.sum(), 1), t=round(t, 2), exbest=round(ex, 3))


rows = []
fam = L[L.setup.isin(FAM)].copy(); fam["spy10"] = fam.date.map(spy10)
for q, thr in (("U1 skip<10:50 SPY>=+0.10", 0.10), ("U2 skip<10:50 SPY>=+0.15", 0.15), ("U3 skip<10:50 SPY>=+0.25", 0.25)):
    m = (fam.tod < 1050) & (fam.spy10 >= thr)
    rows.append((q, fam[m], fam[~m], fam))
ns5 = L[L.setup == "NS5-sma50-flush-oversold-long"]
m = ns5.symbol.isin(VOL); rows.append(("V1 NS5 skip vol ETPs", ns5[m], ns5[~m], ns5))
R = []
for q, sk, keep, pool in rows:
    r = dict(q=q)
    for s in ("train", "valid"):
        st = stats(sk, pool, s); r.update({f"{s}_{k}": v for k, v in st.items()})
        r[f"{s}_kept_avgR"] = round(keep[keep.split == s].r.mean(), 3)
    r["pass"] = bool(r["train_avgR"] < 0 and r["valid_avgR"] < 0 and r["valid_n"] >= 30 and r["valid_t"] >= bar)
    R.append(r)
R = pd.DataFrame(R)
pd.set_option("display.width", 300)
cov = f"spy10 coverage: {fam.spy10.notna().mean():.1%} of family trades; NS5 vol-ETP trades in the list: {int(m.sum())} ({sorted(set(ns5[m].symbol))})"
per = fam.assign(skip=(fam.tod < 1050) & (fam.spy10 >= 0.15)).groupby(["setup", "split", "skip"]).r.agg(["size", "mean"]).round(3)
txt = (f"configs {N}, bar t {bar}\n{cov}\n" + R.T.to_string() + "\n\nU2 per setup (skip = entered < 10:50 on SPY >= +0.15% at 10:00):\n" + per.to_string())
open(OUT / "swarm_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
