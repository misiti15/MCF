"""hf1027: score the coil-k4 two-year variants from scan_hf.py (open history only, locked block 2024-11..2025-02 never
read; no holdout scored). 5 configurations: tgt050 / tgt075 / tgt100 (no scale-out) and cost floors on the parent
(entry-side cost 1c + 1 bp <= 5% / 8% of R, R = 0.25 x daily ATR). train = 2024-09..2025-12, valid = 2026-01..2026-10-07.
Lineage N for coil-k4: 230 (top5_1021) + 12 (bdi1026 burst) + 5 here = 247; bar max(1.5, sqrt(2 ln N)).
Usage: python eval2y.py -> eval2y_out.txt   Educational only - not financial advice."""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402
HERE = Path(__file__).resolve().parent
T = pd.read_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/hf/coil2y.parquet")
T["date"] = pd.to_datetime(T.date).dt.date
assert not ((T.date >= pd.Timestamp("2024-11-01").date()) & (T.date <= pd.Timestamp("2025-02-28").date())).any()
T = T[T.filled].copy()
T["split"] = np.where(T.date <= pd.Timestamp("2025-12-31").date(), "train", "valid")
T["regime"] = T.date.map(lib.regimes()["regime"])
T["cost_frac"] = (0.01 + T.close * 1e-4) / (0.25 * T.atr_d)
N = 247; BAR = round(max(1.5, math.sqrt(2 * math.log(N))), 2)
P = T[T["var"] == "P"]
def stats(name, g, base):
    d = g.groupby("date").r.sum(); b = base.groupby("date").r.agg(["sum", "size"])
    D = d.reindex(b.index, fill_value=0.0) - b["sum"]; n = b["size"].sum(); dl = D.sum() / n
    se = np.sqrt(((D - dl * b["size"]) ** 2).sum()) / n
    gd = g.groupby("date").r.sum(); bd = gd.idxmax()
    return dict(config=name, n=len(g), per_day=round(len(g) / g.date.nunique(), 1), win=round((g.r > 0).mean(), 3), exp=round(g.r.mean(), 4),
                t_day=round(gd.mean() / (gd.std(ddof=1) / len(gd) ** .5), 2),
                train=round(g[g.split == "train"].r.mean(), 4), valid=round(g[g.split == "valid"].r.mean(), 4),
                up=round(g[g.regime == "up"].r.mean(), 4), flat=round(g[g.regime == "flat"].r.mean(), 4), down=round(g[g.regime == "down"].r.mean(), 4),
                exbest=round(g[g.date != bd].r.mean(), 4), excess_ctrl=round((g.r - g.ctrl).mean(), 4),
                delta_vs_parent=round(dl, 4), t_delta=round(dl / se, 2) if se > 0 else np.nan)
rows = [stats("P parent_live (0.5R, 0.35 scale-out)", P, P)]
for v, nm in (("T050", "tgt050 no scale-out"), ("T075", "tgt075 no scale-out"), ("T100", "tgt100 no scale-out")):
    rows.append(stats(nm, T[T["var"] == v], P))
for th in (0.05, 0.08):
    rows.append(stats(f"parent + cost/R <= {th}", P[P.cost_frac <= th], P))
R = pd.DataFrame(rows); R.to_csv(HERE / "results2y.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 30)
L = [f"coil-k4 two-year open history (locked block not read), first signal per symbol-day; lineage N {N}, bar t {BAR}; costs in",
     R.to_string(index=False), "\nparent by cost/R bucket:"]
P = P.assign(cf=pd.cut(P.cost_frac, [0, 0.03, 0.05, 0.08, 0.12, 9]))
L.append(P.groupby("cf", observed=True).agg(n=("r", "size"), win=("r", lambda x: (x > 0).mean()), exp=("r", "mean"), ctrl=("ctrl", "mean")).round(4).to_string())
L.append("\nparent by entry window:")
P = P.assign(tw=pd.cut(P.sig_tod, [0, 1014, 1044, 1114, 2400], labels=["09:50-10:14", "10:15-10:44", "10:45-11:14", "11:15-11:30"]))
L.append(P.groupby("tw", observed=True).agg(n=("r", "size"), exp=("r", "mean"), ctrl=("ctrl", "mean")).round(4).to_string())
L.append("\nparent by entries per session (frequency): sessions bucketed by how many coil-k4 signals fired that day")
dd = P.groupby("date").agg(n=("r", "size"), R=("r", "sum"))
dd["nb"] = pd.qcut(dd.n, 4)
L.append(dd.groupby("nb", observed=True).agg(sessions=("n", "size"), trades=("n", "sum"), R=("R", "sum")).assign(per_trade=lambda x: (x.R / x.trades).round(4)).to_string())
txt = "\n".join(L) + "\n\nEducational only - not financial advice.\n"
open(HERE / "eval2y_out.txt", "w").write(txt); print(txt)
