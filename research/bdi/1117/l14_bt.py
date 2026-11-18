"""swing1117-L14 'down-day bounce, matured' - ONE pre-registered 2-year backtest (BDI 2026-11-17, rule fixed in
research/bdi/swings/hypotheses.jsonl before this script was run; configs = 1).

Data: research/history2y/data/bt_lab1104 (uncapped lab lists, production costs in, locked block 2024-11..2025-02 absent:
asserted) + 5-min SPY frames (research/history2y/data/frames, hive; locked months absent: asserted).
Family = RW3 / RW5 / MF2 / MF4 -FD shorts (the Primary short family). Times = bar-close tod of the 5-min frames.
  Qualifying day: SPY's lowest 5-min close from the open (fromOpen) over bars 09:35..12:00 is <= -0.75%; m = that low,
  tl = its bar. Bounce B = first SPY bar after tl and <= 13:30 with fromOpen >= m + 0.30. Days without B do not qualify.
  A (tagged) = family shorts entered B+10 .. B+45 min.  C (control) = same-day family shorts entered B-60 .. B+10 min.
PASS (fixed): n_A >= 40 on >= 8 days; avg R A >= +0.10; A - C >= +0.20R; paired day diff (days with both) t >= bar
(t_required(1)); paired diff > 0 in train (< 2025-09-01) AND valid. Also reported: day type split, A without best day.
Usage: python l14_bt.py  -> l14_bt_out.txt next to this file.   Educational only - not financial advice."""
import glob, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as ds
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research.gates import t_required
H = ROOT / "research/history2y/data"; LK0, LK1 = "2024-11-01", "2025-02-28"; SPLIT = "2025-09-01"; BAR = t_required(1)
FAM = ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "MF2-open-rsimidhi-flowsell-FD",
       "MF4-h40-open-flowsell-FD"]
T = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob(str(H / "bt_lab1104/sig_*.parquet"))))
T["date"] = T.date.astype(str); assert not T.date.between(LK0, LK1).any()
T = T[T.setup.isin(FAM) & (T.side == -1)].copy()
F = ds.dataset(str(H / "frames"), format="parquet", partitioning="hive").to_table(
    columns=["symbol", "date", "tod", "close", "fromOpen"], filter=ds.field("symbol") == "SPY").to_pandas()
F["date"] = pd.to_datetime(F.date).dt.date.astype(str); assert not F.date.between(LK0, LK1).any()
mn = lambda t: (t // 100) * 60 + t % 100
B = {}
for d, g in F.sort_values("tod").groupby("date"):
    a = g[g.tod <= 1200]
    if a.empty or a.fromOpen.min() > -0.75: continue
    m, tl = a.fromOpen.min(), a.loc[a.fromOpen.idxmin(), "tod"]
    b = g[(g.tod > tl) & (g.tod <= 1330) & (g.fromOpen >= m + 0.30)]
    if len(b): B[d] = mn(int(b.tod.iloc[0]))
T = T[T.date.isin(B)].copy(); T["dm"] = mn(T.tod) - T.date.map(B)
A, C = T[(T.dm >= 10) & (T.dm <= 45)], T[(T.dm >= -60) & (T.dm < 10)]
dd = (A.groupby("date").r.mean() - C.groupby("date").r.mean()).dropna()
tt = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan
tr, va = dd[dd.index < SPLIT], dd[dd.index >= SPLIT]
D = pd.read_parquet(H / "daily.parquet", columns=["symbol", "date", "open", "close"]); D["date"] = pd.to_datetime(D.date).dt.date.astype(str)
s = D[D.symbol == "SPY"].set_index("date"); oc = (s.close / s.open - 1) * 100
dtyp = lambda d: "up" if oc.get(d, 0) > 0.25 else ("down" if oc.get(d, 0) < -0.25 else "quiet")
g = A.groupby("date").r.sum(); best = g.idxmax() if len(g) else None
ok = (len(A) >= 40 and A.date.nunique() >= 8 and A.r.mean() >= 0.10 and A.r.mean() - C.r.mean() >= 0.20 and tt(dd) >= BAR
      and tr.mean() > 0 and va.mean() > 0)
out = [f"swing1117-L14 down-day bounce, matured | configs 1 | bar t {BAR} | qualifying days {len(B)} (SPY sessions {F.date.nunique()})",
       f"A (B+10..45) n {len(A)} on {A.date.nunique()} days avg {A.r.mean():+.3f}R | C (B-60..B+10) n {len(C)} avg {C.r.mean():+.3f}R | A-C {A.r.mean()-C.r.mean():+.3f}R",
       f"paired day diff {dd.mean():+.3f}R on {len(dd)} days t {tt(dd):.2f} | train {tr.mean():+.3f} (n {len(tr)}) valid {va.mean():+.3f} (n {len(va)})",
       f"A w/o best day ({best}, share {g.max()/g.sum() if g.sum()>0 else float('nan'):.2f}) avg {A[A.date!=best].r.mean():+.3f}R",
       "A by SPY day type: " + "; ".join(f"{k} n {len(x)} {x.r.mean():+.3f}R" for k, x in A.groupby(A.date.map(dtyp))),
       "C by SPY day type: " + "; ".join(f"{k} n {len(x)} {x.r.mean():+.3f}R" for k, x in C.groupby(C.date.map(dtyp))),
       "A by setup: " + "; ".join(f"{k[:4]} n {len(x)} {x.r.mean():+.3f}R" for k, x in A.groupby("setup")),
       f"PASS {ok}", "Educational only - not financial advice."]
(Path(__file__).resolve().parent / "l14_bt_out.txt").write_text("\n".join(out) + "\n"); print("\n".join(out))
