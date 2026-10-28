"""htf1028: score the scan_htf.py output (open history only; locked block 2024-11..2025-02 never read; no holdout).
train = 2024-10..2025-12, valid = 2026-01..2026-10-07. Regimes = lib.regimes() (universe median open-to-close terciles).
Bars: max(1.5, sqrt(2 ln N)) with N = configurations in the lineage (rule 19).
  mss-pullback: new lineage, N = 16 (both sides counted)        -> bar 2.35
  coil-k4-trendfilter: coil-k4 lineage 247 (hf1027) + 5 here = 252 -> bar 3.33
Usage: python eval_htf.py -> eval_out.txt, results_mss.csv, results_coil.csv   Educational only - not financial advice."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402

HERE = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/htf1028")
LK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
REG = lib.regimes()["regime"]
pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)


def prep(T):
    T["date"] = pd.to_datetime(T.date).dt.date
    assert not ((T.date >= LK[0]) & (T.date <= LK[1])).any()
    T["split"] = np.where(T.date <= pd.Timestamp("2025-12-31").date(), "train", "valid")
    T["regime"] = T.date.map(REG)
    return T


def core(g):
    gd = g.groupby("date").r.sum()
    bd = gd.idxmax()
    tot = gd.sum()
    return dict(n=len(g), days=g.date.nunique(), win=round((g.r > 0).mean(), 3), exp=round(g.r.mean(), 4),
                se=round(gd.std(ddof=1) * math.sqrt(len(gd)) / len(g), 4),
                t_day=round(gd.mean() / (gd.std(ddof=1) / len(gd) ** .5), 2),
                train=round(g[g.split == "train"].r.mean(), 4), valid=round(g[g.split == "valid"].r.mean(), 4),
                n_valid=int((g.split == "valid").sum()),
                up=round(g[g.regime == "up"].r.mean(), 4), flat=round(g[g.regime == "flat"].r.mean(), 4),
                down=round(g[g.regime == "down"].r.mean(), 4),
                exbest=round(g[g.date != bd].r.mean(), 4),
                best_share=(f"{gd.max() / tot:.0%}" if tot > 0 else "n/a (total<0)"))


L = []
# ------------------------------------------------------------------ 1. MSS pullback
N1 = 16; BAR1 = round(max(1.5, math.sqrt(2 * math.log(N1))), 2)
M = prep(pd.read_parquet(SCR / "mss.parquet"))
rows = []
for (vid, side, k, tgt, p), g in M.groupby(["vid", "side", "k", "tgt", "p"]):
    f = g[g.r.notna()]
    d = dict(vid=vid, side="long" if side == 1 else "short", swing_k=k, target=tgt, entry=p, signals=len(g),
             fill=round(len(f) / len(g), 3), **core(f),
             cost_share=round(float(((0.01 + f.L * 1e-4) / f.R).median()), 3),
             tgt_hit=round((f.code == 1).mean(), 3), stop=round((f.code == 2).mean(), 3))
    d["clears_bar"] = bool(d["t_day"] >= BAR1 and d["up"] > 0 and d["down"] > 0)
    rows.append(d)
R1 = pd.DataFrame(rows)
R1.to_csv(HERE / "results_mss.csv", index=False)
L += [f"1. htf1028-mss-pullback: two-year open history, costs in; {N1} configurations; bar t_day >= {BAR1} plus up>0 and down>0",
      R1.to_string(index=False)]
# extra description on the 'reference' variants (k2 / 2R / 50%): by month-walk and by cost share
for side in (1, -1):
    g = M[(M.side == side) & (M.k == 2) & (M.tgt == 2.0) & (M.p == 0.5) & M.r.notna()].copy()
    g["m"] = pd.to_datetime(g.date).dt.strftime("%Y-%m")
    mm = g.groupby("m").r.mean()
    L.append(f"\n{'long' if side == 1 else 'short'} k2/2R/50%: months positive {int((mm > 0).sum())}/{len(mm)}; by cost/R bucket:")
    g["cf"] = pd.cut((0.01 + g.L * 1e-4) / g.R, [0, 0.03, 0.05, 0.08, 0.12, 9])
    L.append(g.groupby("cf", observed=True).r.agg(["size", "mean"]).round(4).to_string())
    L.append("by signal hour:")
    L.append(g.groupby(g.sig_tod // 100).r.agg(["size", "mean"]).round(4).to_string())

# ------------------------------------------------------------------ 2. coil-k4 trend filter
N2 = 252; BAR2 = round(max(1.5, math.sqrt(2 * math.log(N2))), 2)
C = prep(pd.read_parquet(SCR / "coilfeat.parquet"))
C = C[C.filled].copy()
with np.errstate(invalid="ignore"):
    stock = ((C.p_close > C.p_sma20) & C.h60_hl).to_numpy()
    q_vwap = (C.qqq_vwap > 0).to_numpy()
    b_open = (C.breadth_open > 0.5).to_numpy()
mkt = q_vwap | b_open
cfg = [("parent CWT12-coil-k4-long (as live)", np.ones(len(C), bool)),
       ("(a) stock HTF up: close>SMA20 & 60m HL", stock),
       ("(b) market up: qqq_vwap>0 OR breadth_open>0.5", mkt),
       ("(c) both (a)&(b)", stock & mkt),
       ("(b1) qqq_vwap>0 only", q_vwap),
       ("(b2) breadth_open>0.5 only", b_open)]
base = C.groupby("date").r.agg(["sum", "size"])
rows = []
for name, m in cfg:
    g = C[m]
    d = dict(config=name, keep=round(m.mean(), 3), **core(g), excess_ctrl=round(float((g.r - g.ctrl).mean()), 4))
    dd = g.groupby("date").r.sum().reindex(base.index, fill_value=0.0) - base["sum"]
    n = base["size"].sum(); dl = dd.sum() / n
    se = np.sqrt(((dd - dl * base["size"]) ** 2).sum()) / n
    d["dropped_exp"] = round(float(C[~m].r.mean()), 4) if (~m).any() else np.nan
    d["t_kept_vs_parent"] = round(dl / se, 2) if se > 0 else np.nan
    d["clears_bar"] = bool(d["t_day"] >= BAR2 and d["up"] > 0 and d["down"] > 0)
    rows.append(d)
R2 = pd.DataFrame(rows)
R2.to_csv(HERE / "results_coil.csv", index=False)
L += [f"\n2. htf1028-coil-k4-trendfilter: parent trades from hf1027/scan_hf.py (var P), first signal per symbol-day, "
      f"costs in; 5 configurations here; lineage N {N2}, bar t_day >= {BAR2} plus up>0 and down>0",
      "t_kept_vs_parent = day-clustered t of (kept R - parent R) per day: + means the filter raises total R",
      R2.to_string(index=False)]
L.append("\nfeature coverage (share of parent trades): stock-HTF up %.3f, SMA20 known %.3f, 60m HL %.3f, qqq_vwap known %.3f"
         % (stock.mean(), C.p_sma20.notna().mean(), C.h60_hl.mean(), C.qqq_vwap.notna().mean()))
txt = "\n".join(L) + "\n\nEducational only - not financial advice.\n"
open(HERE / "eval_out.txt", "w").write(txt)
print(txt)
