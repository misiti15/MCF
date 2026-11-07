"""Block B (PLAN.md): `burst2-mf-after-flush-rework` - MF2-FD / MF4-FD lab trades minus entries with QQQ 30-min return
<= -y at entry, y in {0.30, 0.40, 0.50}% (6 configs, lineage N = 6). Gates as mcf/research/gates.py (summary, regime split on
the universe-median terciles, walk-forward, try-count bar; BAR90 = 0.9 x bar), SPY day type split (QDAY), live paper check.
Usage: python b_mf.py <burst2 scratch>     Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research import gates as G
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
B2 = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
N = 6; BAR = G.t_required(N); B90 = max(1.35, 0.9 * BAR)
T = pd.read_parquet(B2 / "trades2_2y.parquet"); TL = pd.read_parquet(B2 / "trades2_live.parquet")
assert not T.date.between("2024-11-01", "2025-02-28").any()
dl = pd.read_parquet("/home/user/MCF/research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close"])
dl["date"] = dl.date.astype(str); dl = dl[~dl.date.between("2024-11-01", "2025-02-28")]
REG = G.session_regimes(dl)
spy = dl[dl.symbol == "SPY"].set_index("date"); oc = (spy.close / spy.open - 1) * 100
DT = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
out, rows = [], []
for su in ("MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD"):
    x = T[T.setup == su].copy(); lv = TL[(TL.setup == su) & (TL.run_id == 1)]
    for y in (None, 0.003, 0.004, 0.005):
        keep = np.ones(len(x), bool) if y is None else ~(x.qqq_r30.to_numpy() <= -y)
        k = x[keep]; s = G.summary(k[["date", "r"]]); rg = G.regime_split(k[["date", "r"]], REG); wf = G.walk_forward(k[["date", "r"]], exclude_months=["2024-11", "2024-12", "2025-01", "2025-02"])
        dty = k.groupby(k.date.map(DT)).r.agg(["size", "mean"])
        rem = x[~keep]; ex = rem.r.mean() - x.r.mean() if len(rem) else np.nan
        lk = lv if y is None else lv[~(lv.qqq_r30 <= -y)]
        g = k.groupby("date").r.sum(); share = g.max() / g.sum() if g.sum() > 0 else np.nan
        ok = (s.get("t") or -9) >= B90 and rg["pass"] and (wf["share_positive"] or 0) >= 0.54
        rows.append(dict(setup=su, cfg="parent" if y is None else f"qqq30>-{y*100:.1f}%", n=s["n"], days=s["days"], exp_r=s["exp_r"], t=s["t"],
                         wo_best=s["ex_best_day"], best_share=share, up=rg["up"].get("exp_r"), flat=rg["flat"].get("exp_r"), down=rg["down"].get("exp_r"),
                         spy_up=dty["mean"].get("up"), spy_down=dty["mean"].get("down"), spy_quiet=dty["mean"].get("quiet"),
                         wf=wf["share_positive"], removed_n=int((~keep).sum()), removed_avg=rem.r.mean() if len(rem) else np.nan,
                         live_n=len(lk), live_avg=lk.r.mean() if len(lk) else np.nan, live_removed_R=(lv.r.sum() - lk.r.sum()) * -1,
                         passes=bool(ok) if y is not None else None))
D = pd.DataFrame(rows); D.round(4).to_csv(HERE / "b_results.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
txt = f"BAR90 {B90:.2f} (full {BAR:.2f}, N {N}); live_removed_R = live R gained by the filter (positive = it removes losing live trades)\n" + D.round(3).to_string()
open(HERE / "b_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
