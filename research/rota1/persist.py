"""ROTA1 step 1: persistence. Does trailing R (wob / green / worst / S1) rank next 3/5/7 sessions' R?
Spearman rho and top-minus-bottom quintile spread of forward sum R per review date; t over dates.
2-year lab lists (TRAIN / VALID / FWD) and live (W=10, h=3/5). Educational only — not financial advice.

    python research/rota1/persist.py <scratch_dir>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import s1, split_of, tstat, window_metrics  # noqa: E402

S = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent


def run(R, N, windows, hs, minn, label):
    dates = R.index.to_numpy()
    Rv, Nv = R.to_numpy(), N.to_numpy()
    rows = []
    for W in windows:
        for h in hs:
            per = []
            for i in range(W, len(dates) - h + 1, h):
                m = window_metrics(Rv, Nv, i, W)
                q = m["n"] >= minn[W]
                if q.sum() < 10:
                    continue
                fwd = Rv[i:i + h].sum(0)
                fn = Nv[i:i + h].sum(0)
                fpt = np.where(fn > 0, fwd / np.maximum(fn, 1), np.nan)
                actr = pd.Series(m["n"].astype(float)).rank().to_numpy()
                m["S1"] = s1(m, q)
                sp = split_of(dates[i]) if label == "bt" else "LIVE"
                for k in ("wob", "green", "worst", "S1"):
                    x = m[k][q]
                    f = fwd[q]
                    ok = np.isfinite(x)
                    x, f = x[ok], f[ok]
                    rho = spearmanr(x, f).correlation
                    o = np.argsort(x)
                    nq = max(2, len(x) // 5)
                    spread = f[o[-nq:]].mean() - f[o[:nq]].mean()
                    # added after the first run (activity confound, see NOTES): per-trade forward R and
                    # partial rho controlling for trailing trade count (rank-residual)
                    fp = fpt[q][ok]
                    okp = np.isfinite(fp)
                    rho_pt = spearmanr(x[okp], fp[okp]).correlation if okp.sum() > 10 else np.nan
                    a = actr[q][ok]
                    rx = pd.Series(x).rank().to_numpy(); rf = pd.Series(f).rank().to_numpy()
                    bx = np.polyfit(a, rx, 1); bf = np.polyfit(a, rf, 1)
                    rho_part = np.corrcoef(rx - np.polyval(bx, a), rf - np.polyval(bf, a))[0, 1]
                    per.append({"W": W, "h": h, "metric": k, "split": sp, "date": dates[i], "rho": rho,
                                "spread": spread, "nset": len(x), "rho_pt": rho_pt, "rho_part": rho_part})
            p = pd.DataFrame(per)
            for (k, sp), g in p.groupby(["metric", "split"]):
                rows.append({"data": label, "W": W, "h": h, "metric": k, "split": sp, "dates": len(g),
                             "setups": round(g.nset.mean(), 1), "rho": g.rho.mean(), "t_rho": tstat(g.rho),
                             "spread_R": g.spread.mean(), "t_spread": tstat(g.spread),
                             "rho_pertrade": g.rho_pt.mean(), "t_pt": tstat(g.rho_pt),
                             "rho_partial_activity": g.rho_part.mean(), "t_part": tstat(g.rho_part)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    R, N = pd.read_parquet(S / "bt_R.parquet"), pd.read_parquet(S / "bt_N.parquet")
    a = run(R, N, [60, 20], [3, 5, 7], {60: 30, 20: 10}, "bt")
    R, N = pd.read_parquet(S / "live_R.parquet"), pd.read_parquet(S / "live_N.parquet")
    b = run(R, N, [10], [3, 5], {10: 10}, "live")
    out = pd.concat([a, b])
    out.round(4).to_csv(OUT / "persist.csv", index=False)
    pd.set_option("display.width", 200)
    print(out.round(3).to_string(index=False))
