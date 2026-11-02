"""Small swarm for backlog nightly-1102-skip-inverse-etf-shorts: does a lab setup's trade on a leveraged / inverse ETF
do worse than its other trades? On the 2-year lab trade lists (research/history2y/data/lab_trades.parquet: 21 live /
probation setups, production costs; the locked block 2024-11-01..2025-02-28 is not in the file and is never read).
ETF class from the CURRENT universe names (data/universe.csv; regex: inverse = Short/Bear/Inverse/UltraShort/-1X..-3X,
leveraged = 2X/3X/Ultra/Daily/Bull/Leveraged; not inverse). Symbols not in today's universe count as 'other'.
Configs (4): Q1 shorts skip inverse ETFs, Q2 shorts skip all leveraged + inverse, Q3 longs skip inverse, Q4 longs skip
leveraged-long. A skip rule helps iff the skipped trades lose: day-clustered t of the skipped trades' R (sign flipped)
over all split sessions. Pass = skipped avg R < 0 in train AND valid, valid n >= 30, valid t >= bar
max(1.5, sqrt(2 ln 4)) = 1.665. Train < 2025-09-01, valid >= 2025-09-01. L3 (the setup behind tonight's loss) is NOT
in the lab lists, so this tests the family-wide rule, not L3 itself.
Usage: python levetf.py   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import t_required
H = Path("/home/user/MCF/research/history2y/data"); OUT = Path(__file__).resolve().parent
L = pd.read_parquet(H / "lab_trades.parquet"); L["date"] = L.date.astype(str)
assert not L.date.between("2024-11-01", "2025-02-28").any(), "locked block present"
SHORT = ("short", "RW", "MF", "NS2", "NS3", "NS4")
L["side"] = np.where(L.setup.str.contains("|".join(SHORT)) & ~L.setup.str.contains("long"), -1, 1)
u = pd.read_csv("/home/user/MCF/data/universe.csv", usecols=["symbol", "name"]); nm = u.name.fillna("")
inv = set(u.symbol[nm.str.contains(r"Inverse|Bear\b|Bear [0-9]|\bShort\b|UltraShort|-1X|-2X|-3X", case=False)
                   & nm.str.contains(r"ETF|ETN|Fund|Trust|ProShares|Direxion", case=False)])
lev = set(u.symbol[nm.str.contains(r"\b2X\b|\b3X\b|Ultra|Daily|Bull\b|Leveraged", case=False)
                   & nm.str.contains(r"ETF|ETN|Fund|Trust|ProShares|Direxion", case=False)]) - inv
L["cls"] = np.where(L.symbol.isin(inv), "inverse", np.where(L.symbol.isin(lev), "lev", "other"))
L["split"] = np.where(L.date < "2025-09-01", "train", "valid")
N = 4; bar = t_required(N)
def stats(d, s):
    days = L[L.split == s].date.unique()
    x = d[d.split == s]
    if len(x) == 0: return dict(n=0, avgR=np.nan, t=np.nan)
    day = (-x.groupby("date").r.sum()).reindex(days, fill_value=0.0)
    t = day.mean() / (day.std(ddof=1) / np.sqrt(len(day))) if day.std() > 0 else np.nan
    return dict(n=len(x), avgR=round(x.r.mean(), 3), sumR=round(x.r.sum(), 1), t=round(t, 2))
rows = []
for q, side, cl in [("Q1 shorts skip inverse", -1, ["inverse"]), ("Q2 shorts skip lev+inverse", -1, ["inverse", "lev"]),
                    ("Q3 longs skip inverse", 1, ["inverse"]), ("Q4 longs skip lev-long", 1, ["lev"])]:
    sk = L[(L.side == side) & L.cls.isin(cl)]; keep = L[(L.side == side) & ~L.cls.isin(cl)]
    r = dict(q=q)
    for s in ("train", "valid"):
        st = stats(sk, s); r.update({f"{s}_{k}": v for k, v in st.items()})
        r[f"{s}_kept_avgR"] = round(keep[keep.split == s].r.mean(), 3)
    r["pass"] = bool(r["train_avgR"] < 0 and r["valid_avgR"] < 0 and r["valid_n"] >= 30 and r["valid_t"] >= bar)
    rows.append(r)
R = pd.DataFrame(rows)
top = L[(L.cls != "other")].groupby(["side", "cls", "setup"]).r.agg(["size", "mean"]).round(3)
txt = (f"inverse symbols {len(inv)}, leveraged-long {len(lev)}; configs {N}, bar t {bar}\n" + R.to_string(index=False)
       + "\n\nper setup (non-'other' trades):\n" + top.to_string())
open(OUT / "levetf_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
