"""Small swarm for backlog nightly-1030-late-short-extended-index (and its long mirror), on the 2-year lab trade lists
(research/history2y/data/lab_trades.parquet: 21 live / probation setups, production costs, locked block 2024-11-01..
2025-02-28 not in the file and never read) joined to SPY's from-open % at the entry bar (history2y context).
Q1 (9 configs): skip SHORT entries at tod >= T when SPY from-open <= -K (T 1300/1330/1400, K 0.75/1.0/1.25). The rule
    helps iff the skipped trades lose: score = -(sum R of skipped) per session; day-clustered t of the skipped trades.
Q2 (3 configs): LONG lab trades at tod >= 1400 when SPY from-open <= -K (K 0.75/1.0/1.25): afternoon reversal longs.
12 configurations in all -> bar t >= max(1.5, sqrt(2 ln 12)) = 2.23. Train < 2025-09-01, valid >= 2025-09-01.
A rule passes only if the skipped (Q1) / kept (Q2) set has the right sign in train AND valid, valid n >= 30 and |t| >= bar.
Usage: python lateext.py   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import t_required
H = Path("/home/user/MCF/research/history2y/data"); OUT = Path(__file__).resolve().parent
L = pd.read_parquet(H / "lab_trades.parquet"); C = pd.read_parquet(H / "context")
L["date"] = L.date.astype(str); C["date"] = C.date.astype(str)
assert not L.date.between("2024-11-01", "2025-02-28").any(), "locked block present"
SHORT = ("short", "RW", "MF", "NS2", "NS3", "NS4")
L["side"] = np.where(L.setup.str.contains("|".join(SHORT)) & ~L.setup.str.contains("long"), -1, 1)
# context is on 5-min bar closes; align each entry to the last context bar <= tod
C = C.sort_values(["date", "tod"]); L = L.sort_values(["date", "tod"])
L = pd.merge_asof(L.sort_values("tod"), C[["date", "tod", "spy_fo"]].sort_values("tod"), on="tod", by="date", direction="backward").dropna(subset=["spy_fo"])
L["split"] = np.where(L.date < "2025-09-01", "train", "valid")
ses = L.groupby("split").date.nunique()
def stats(d, sign):
    if len(d) == 0: return dict(n=0)
    day = d.groupby("date").r.sum() * sign
    allday = day.reindex(L[L.split == d.split.iloc[0]].date.unique(), fill_value=0.0)
    t = allday.mean() / (allday.std(ddof=1) / np.sqrt(len(allday))) if allday.std() > 0 else np.nan
    return dict(n=len(d), days=d.date.nunique(), avgR=round(d.r.mean(), 3), sumR=round(d.r.sum(), 1), t_day=round(t, 2))
rows = []
for T in (1300, 1330, 1400):
    for K in (0.75, 1.0, 1.25):
        m = (L.side == -1) & (L.tod >= T) & (L.spy_fo <= -K)
        r = dict(q="Q1 skip shorts", T=T, K=K)
        for s in ("train", "valid"):
            st = stats(L[m & (L.split == s)], -1)
            r.update({f"{s}_{k}": v for k, v in st.items()})
        rows.append(r)
for K in (0.75, 1.0, 1.25):
    m = (L.side == 1) & (L.tod >= 1400) & (L.spy_fo <= -K)
    r = dict(q="Q2 longs kept", T=1400, K=K)
    for s in ("train", "valid"):
        st = stats(L[m & (L.split == s)], 1)
        r.update({f"{s}_{k}": v for k, v in st.items()})
    rows.append(r)
R = pd.DataFrame(rows); bar = t_required(12)
# Q1 passes if skipped trades lose in both (avgR < 0) and valid t (of -R) >= bar; Q2 if kept longs win in both and t >= bar
R["pass"] = (R.train_avgR * np.where(R.q.str.startswith("Q1"), -1, 1) > 0) & (R.valid_avgR * np.where(R.q.str.startswith("Q1"), -1, 1) > 0) & (R.valid_n >= 30) & (R.valid_t_day >= bar)
pd.set_option("display.width", 250)
base = L.groupby(["split", "side"]).r.agg(["size", "mean"]).round(3)
by = L[(L.side == -1) & (L.tod >= 1330) & (L.spy_fo <= -1.0)].groupby("setup").r.agg(["size", "mean"]).round(3)
txt = (f"lab trades {len(L)} (sessions train {ses.get('train')}, valid {ses.get('valid')}); bar t {bar:.2f} (12 configs)\n"
       f"baseline by split x side:\n{base}\n\n{R.to_string()}\n\npasses: {int(R['pass'].sum())} of {len(R)}\n\n"
       f"Q1 T1330 K1.0 skipped shorts by setup (both splits):\n{by}\n\nEducational only - not financial advice.\n")
open(OUT / "lateext_out.txt", "w").write(txt); print(txt)
