"""Part A summary tables from predict.py outputs + features.parquet: per checkpoint, the from-open (fo) and composite
signals averaged over SPY/QQQ/IWM; Pearson with and without the 5 largest |target| days per split; continuation rate up
vs down. Writes predict_summary.csv, predict_summary.txt. Usage: python summary_a.py <scratch>.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
F = pd.read_parquet(Path(sys.argv[1]) / "features.parquet")
assert not ((F.date >= "2024-11-01") & (F.date <= "2025-02-28")).any()
rows = []
for feat in ("fo", "vwap", "breadth", "breadth_open", "comp", "gapstate", "vxx_fo", "drive", "prev5"):
    for tgt in ("ROD", "AFT"):
        for C in sorted(F.C.unique()):
            for sp in ("train", "valid"):
                for sym in ("SPY", "QQQ", "IWM"):
                    g = F[(F.C == C) & (F.split == sp) & (F.sym == sym)].dropna(subset=[feat, tgt])
                    x, y = g[feat].to_numpy(float), g[tgt].to_numpy(float)
                    keep = np.argsort(-np.abs(y))[5:]
                    nz = x != 0
                    s = np.sign(x)
                    up, dn = x > 0, x < 0
                    rows.append(dict(feature=feat, target=tgt, C=C, split=sp, sym=sym, n=len(g),
                                     pearson=np.corrcoef(x, y)[0, 1], pearson_ex5=np.corrcoef(x[keep], y[keep])[0, 1],
                                     spearman=pd.Series(x).rank().corr(pd.Series(y).rank()),
                                     hit=(np.sign(y[nz]) == s[nz]).mean(),
                                     cont_up=(y[up] > 0).mean() if up.any() else np.nan,
                                     cont_dn=(y[dn] < 0).mean() if dn.any() else np.nan,
                                     share_up_days=(y > 0).mean(),
                                     mean_bp_up=y[up].mean() * 100 if up.any() else np.nan,
                                     mean_bp_dn=y[dn].mean() * 100 if dn.any() else np.nan))
R = pd.DataFrame(rows)
R.round(4).to_csv(OUT / "predict_summary.csv", index=False)
avg = R.groupby(["feature", "target", "C", "split"])[["pearson", "pearson_ex5", "spearman", "hit", "cont_up", "cont_dn", "share_up_days"]].mean().round(3)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
txt = "Mean over SPY/QQQ/IWM (one observation per day; ~245 train / ~199 valid days)\n" + avg.unstack("split").to_string()
open(OUT / "predict_summary.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
print(txt)
