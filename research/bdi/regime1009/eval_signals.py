"""Regime study step 2 (NOTES.md 1.3): how well each market-context signal at 10:00 / 10:30 predicts the rest-of-day
direction (ROD) and the session regime. Descriptive; no gate is chosen here. Output: signals.csv, signals_by_bar.csv.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
ctx = pd.read_parquet(HERE / "data" / "ctx.parquet")
DIR = ["S1_brd_fo", "S2_brd_vwap", "S3_med_fo", "S4_spy_fo", "S5_qqq_fo", "S6_iwm_fo", "S7_spy_z", "S8_spy_vwslope",
       "S9_spy_gap", "S10_med_gap", "S11_prior_o2c"]
NDIR = ["S12_gap_disp", "S13_spy_atrpct", "S14_spy_orw", "S15_med_rvol", "S16_sect_disp"]
NEUTRAL = {"S1_brd_fo": 0.5, "S2_brd_vwap": 0.5}


def folds(months):
    P = [pd.Period(m, "M") for m in months]
    out = []
    for i in range(3, len(P)):
        w = P[i - 3:i + 1]
        if all((b - a).n == 1 for a, b in zip(w, w[1:])):
            out.append((set(map(str, w[:3])), str(w[3])))
    return out


def wf_class(x, y_reg, y_rod, mon):
    """Walk-forward tercile classification: cut points of the signal (and of ROD) fitted on the 3 previous months."""
    hit_r, hit_d, per = [], [], []
    for tr, te in folds(sorted(set(mon))):
        a = np.isin(mon, list(tr)) & np.isfinite(x)
        b = (mon == te) & np.isfinite(x)
        if a.sum() < 30 or b.sum() < 5:
            continue
        lo, hi = np.quantile(x[a], [1 / 3, 2 / 3])
        rlo, rhi = np.quantile(y_rod[a], [1 / 3, 2 / 3])
        pred = np.where(x[b] <= lo, -1, np.where(x[b] >= hi, 1, 0))
        reg = y_reg[b]
        rodc = np.where(y_rod[b] <= rlo, -1, np.where(y_rod[b] >= rhi, 1, 0))
        hit_r += list(pred == reg)
        hit_d += list(pred == rodc)
        per.append(np.mean(pred == rodc))
    return np.mean(hit_r), np.mean(hit_d), np.mean(np.array(per) > 1 / 3), len(per)


rows = []
for bar in (1000, 1030):
    c = ctx[ctx.tod == bar].sort_values("day")
    mon = pd.to_datetime(c["date"]).dt.strftime("%Y-%m").to_numpy()
    rod = c["ROD"].to_numpy(float)
    reg = c["regime"].map({"up": 1, "flat": 0, "down": -1}).to_numpy()
    med = c["med_o2c"].to_numpy(float)
    for s in DIR + NDIR:
        x = c[s].to_numpy(float)
        ok = np.isfinite(x) & np.isfinite(rod)
        row = {"bar": bar, "signal": s, "kind": "dir" if s in DIR else "magnitude", "n_days": int(ok.sum())}
        if not ok.sum():
            rows.append(row)
            continue
        if s in DIR:
            row["rho_ROD"] = spearmanr(x[ok], rod[ok])[0]
            row["p_ROD"] = spearmanr(x[ok], rod[ok])[1]
            row["rho_o2c"] = spearmanr(x[ok], med[ok])[0]
            nz = x[ok] - NEUTRAL.get(s, 0.0)
            m = nz != 0
            row["sign_acc_ROD"] = float(np.mean(np.sign(nz[m]) == np.sign(rod[ok][m])))
            row["base_rate_up_ROD"] = float(np.mean(rod[ok] > 0))
            # top / bottom tercile of the signal: mean ROD (%)
            lo, hi = np.quantile(x[ok], [1 / 3, 2 / 3])
            row["ROD_top3"] = float(rod[ok][x[ok] >= hi].mean())
            row["ROD_bot3"] = float(rod[ok][x[ok] <= lo].mean())
            row["ROD_top3_med"] = float(np.median(rod[ok][x[ok] >= hi]))
            row["ROD_bot3_med"] = float(np.median(rod[ok][x[ok] <= lo]))
            acc_r, acc_d, share, nf = wf_class(x, reg, rod, mon)
            row.update(wf_acc_regime=acc_r, wf_acc_RODclass=acc_d, wf_share_months_gt_third=share, wf_folds=nf)
        else:
            row["rho_absROD"] = spearmanr(x[ok], np.abs(rod[ok]))[0]
            row["p_absROD"] = spearmanr(x[ok], np.abs(rod[ok]))[1]
            row["rho_ROD"] = spearmanr(x[ok], rod[ok])[0]
            row["p_ROD"] = spearmanr(x[ok], rod[ok])[1]
        rows.append(row)
T = pd.DataFrame(rows)
T.round(4).to_csv(HERE / "signals.csv", index=False)
pd.set_option("display.width", 250)
print(T.round(3).to_string())

# per decision bar (descriptive): S1 and S4 vs ROD from that bar
rows = []
for bar, c in ctx.groupby("tod"):
    for s in ("S1_brd_fo", "S4_spy_fo", "S3_med_fo"):
        ok = np.isfinite(c[s]) & np.isfinite(c["ROD"])
        if ok.sum() < 50:
            continue
        x, y = c.loc[ok, s].to_numpy(float), c.loc[ok, "ROD"].to_numpy(float)
        nz = x - NEUTRAL.get(s, 0.0)
        rows.append({"tod": bar, "signal": s, "n": int(ok.sum()), "rho_ROD": spearmanr(x, y)[0],
                     "sign_acc": float(np.mean(np.sign(nz[nz != 0]) == np.sign(y[nz != 0]))),
                     "ROD_when_up": float(np.mean(y[nz > 0])), "ROD_when_down": float(np.mean(y[nz < 0]))})
P = pd.DataFrame(rows)
P.round(4).to_csv(HERE / "signals_by_bar.csv", index=False)
print(P[P.tod.isin([950, 1000, 1030, 1100, 1200, 1300, 1400, 1500])].round(3).to_string())
