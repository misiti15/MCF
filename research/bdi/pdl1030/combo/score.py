"""pdl1030/combo scoring of the 10 pre-declared rows (PLAN.md). TRAIN+VALID only. Weighted book (w=1 except K4):
avg R = sum(w r)/sum(w), day-clustered t on weighted residuals (= gates.summary when w=1). Educational only - not financial advice."""
import os, sys, math
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).resolve().parent
T = pd.concat([pd.read_parquet(p) for p in sorted((D / "cache").glob("tr_*.parquet"))], ignore_index=True)
d = T["date"].astype(str)
assert (d <= "2026-09-15").all()
assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
T["month"] = d.str[:7]; T["split"] = np.where(d <= "2025-12-31", "train", "valid")
NSESS = T["date"].nunique()
COUNT = 10
N = 121566 + 3 * COUNT
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N))))
PAR = dict(train=-0.0677, valid=-0.0675)
REF = {"PAR-P05": (-0.0677, -0.0675), "PAR-P10": (-0.0861, -0.0912), "PAR-P05S3": (-0.0210, -0.0173), "PAR-TCF": (-0.0392, -0.0498)}


def wsum(dates, r, w):
    W = w.sum(); mu = float((w * r).sum() / W)
    g = pd.Series(w * (r - mu)).groupby(dates).sum()
    se = float(np.sqrt((g ** 2).sum()) / W)
    return mu, (mu / se if se > 0 else np.nan)


def stats(df, r, w):
    r, w = np.asarray(r, float), np.asarray(w, float)
    ok = np.isfinite(r) & (w > 0)
    df, r, w = df[ok], r[ok], w[ok]
    dates = df["date"].astype(str).to_numpy()
    res = {}
    for sp in ("train", "valid"):
        m = (df["split"] == sp).to_numpy()
        mu, t = wsum(dates[m], r[m], w[m]); res[f"avg_{sp}"], res[f"t_{sp}"] = round(mu, 4), round(t, 2)
    mu, t = wsum(dates, r, w); res["avg_tv"], res["t_tv"] = round(mu, 4), round(t, 2)
    day = pd.DataFrame({"d": dates, "wr": w * r, "w": w}).groupby("d").sum()
    b = day["wr"].idxmax()
    res["ex_best"] = round(float((day["wr"].sum() - day.loc[b, "wr"]) / (day["w"].sum() - day.loc[b, "w"])), 4)
    res["best_share"] = round(float(day.loc[b, "wr"] / day["wr"].sum()), 3) if day["wr"].sum() > 0 else None
    mo = pd.Series(w * r).groupby(df["month"].to_numpy()).sum()
    res["wf_pct"] = round(float((mo > 0).mean() * 100), 1)
    up = (df["spy_day"] > 0).to_numpy(); dn = (df["spy_day"] < 0).to_numpy()
    res["up_day_r"] = round(float((w[up] * r[up]).sum() / w[up].sum()), 4)
    res["down_day_r"] = round(float((w[dn] * r[dn]).sum() / w[dn].sum()), 4)
    res["n_tv"] = int(len(r)); res["per_session"] = round(len(r) / NSESS, 1)
    res["risk_units_per_session"] = round(float(w.sum()) / NSESS, 1)
    return res


def passes(st):
    return bool(np.isfinite(st["t_tv"]) and st["t_tv"] >= BAR and st["wf_pct"] >= 54 and st["avg_train"] > 0 and st["avg_valid"] > 0
                and st["avg_train"] > PAR["train"] and st["avg_valid"] > PAR["valid"] and st["per_session"] >= 25)


p05 = T[T.setup == "p05"].reset_index(drop=True); p10 = T[T.setup == "p10"].reset_index(drop=True)
vd, br, sg, cr = (p05[k].to_numpy(float) for k in ("spy_vd", "breadth", "spy_gap", "cost_rt_R"))
c5, c10 = cr <= 0.05, cr <= 0.10
nan = np.full(len(p05), np.nan)
LS3, SS3, LP, SP = (p05[k].to_numpy(float) for k in ("rL_S3", "rS_S3", "rL_P", "rS_P"))
one = np.ones(len(p05))
def flip(up, dn, rl, rs):  # long when tape up, short when tape down, no trade if missing/boundary
    return np.where(up, rl, np.where(dn, rs, np.nan))
w3 = 0.25 + 0.25 * (vd > 0) + 0.25 * (br >= 0.5) + 0.25 * (sg <= -0.5)
CFG = [
    ("PAR-P05", "p05 parent", p05, LP, one),
    ("PAR-P10", "p10 parent", p10, p10.rL_P.to_numpy(float), np.ones(len(p10))),
    ("PAR-P05S3", "p05 S3", p05, LS3, one),
    ("PAR-TCF", "tape-flip TC-F (breadth flip, parent exits)", p05, flip(br > 0.5, br < 0.5, LP, SP), one),
    ("K1", "p05 S3 + cost5 + SPY above VWAP", p05, np.where(c5 & (vd > 0), LS3, nan), one),
    ("K2", "p05 S3 + cost5 + breadth flip", p05, np.where(c5, flip(br > 0.5, br < 0.5, LS3, SS3), nan), one),
    ("K3", "p05 S3 + cost5 + SPY-VWAP flip", p05, np.where(c5, flip(vd > 0, vd < 0, LS3, SS3), nan), one),
    ("K4", "p05 S3 + cost5, tape-score W3 sizing", p05, np.where(c5 & np.isfinite(vd) & np.isfinite(br), LS3, nan), w3),
    ("K5", "p05 S3 + cost10 + breadth flip", p05, np.where(c10, flip(br > 0.5, br < 0.5, LS3, SS3), nan), one),
    ("K6", "p05 S3 + cost5 + (SPY above VWAP or SPY gap<=-0.5%)", p05, np.where(c5 & ((vd > 0) | (sg <= -0.5)), LS3, nan), one),
]
assert len(CFG) == COUNT
rows = []
print(f"sessions {NSESS}  N {N}  BAR {BAR:.3f}")
for id_, rule, df, r, w in CFG:
    st = stats(df, r, w); st.update(id=id_, rule=rule, passes=passes(st))
    if id_ in REF:
        st["parity_ok"] = abs(st["avg_train"] - REF[id_][0]) <= 0.005 and abs(st["avg_valid"] - REF[id_][1]) <= 0.005
    rows.append(st)
R = pd.DataFrame(rows)
cols = ["id", "rule", "avg_train", "avg_valid", "avg_tv", "t_tv", "n_tv", "per_session", "risk_units_per_session", "wf_pct",
        "up_day_r", "down_day_r", "ex_best", "best_share", "passes", "parity_ok"]
R = R[cols]; R["bar_t"], R["N"] = round(BAR, 3), N
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(R.to_string(index=False))
R.to_csv(D / "results.csv", index=False)
