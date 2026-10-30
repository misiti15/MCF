"""pdl1030/regime-day scoring of the 17 pre-declared rows (method copied from combo/score.py) (PLAN.md). TRAIN+VALID only. Weighted book (w=1 except K4):
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
COUNT = 17
N = 121566 + 3 * COUNT
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N))))
PAR = dict(train=-0.0677, valid=-0.0675)
REF = {"PAR-P05": (-0.0677, -0.0675), "PAR-P05S3": (-0.0210, -0.0173), "REF-K3": (0.0062, -0.0003)}


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



DAY = pd.concat([pd.read_parquet(p) for p in sorted((D / "cache").glob("day_*.parquet"))], ignore_index=True).sort_values("date").reset_index(drop=True)
dd = DAY["date"]
assert not ((dd >= "2024-11-01") & (dd <= "2025-02-28")).any() and not dd.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any() and (dd <= "2026-09-15").all()
# prior-day return only across consecutive loaded sessions (no skipped month in between)
prev_m = DAY["date"].shift(1).str[:7]; cur_m = DAY["date"].str[:7]
def mnext(m):
    y, k = int(m[:4]), int(m[5:]); return f"{y + (k == 12)}-{(k % 12) + 1:02d}"
consec = (prev_m == cur_m) | (prev_m.fillna("0000-01").map(mnext) == cur_m)
DAY["pret"] = np.where(consec, (DAY["pc"] / DAY["pc"].shift(1) - 1) * 100, np.nan)
assert DAY["first_tod"].max() <= 950  # first bar (09:45-09:50); features reconstructed from it are pre-open identities
TRD = DAY["date"] <= "2025-12-31"
FEAT = {"R1": "gap", "R2": "prng", "R3": "pclv", "R4": "atrp", "R5": "pret"}
CUT = {k: float(DAY.loc[TRD, v].median()) for k, v in FEAT.items()}
p05 = T[T.setup == "p05"].reset_index(drop=True)
p05 = p05.merge(DAY[["date"] + list(FEAT.values())], on="date", how="left", validate="m:1")
vd, cr = p05["spy_vd"].to_numpy(float), p05["cost_rt_R"].to_numpy(float)
c5, c10 = cr <= 0.05, cr <= 0.10
nan = np.full(len(p05), np.nan); one = np.ones(len(p05))
LS3, SS3, LP, SP = (p05[k].to_numpy(float) for k in ("rL_S3", "rS_S3", "rL_P", "rS_P"))
def flip(up, dn, rl, rs):
    return np.where(up, rl, np.where(dn, rs, np.nan))
def sides(k, orient):
    f = p05[FEAT[k]].to_numpy(float); hi, lo = f > CUT[k], f < CUT[k]
    return (hi, lo) if orient == "A" else (lo, hi)
CFG = [("PAR-P05", "p05 parent", LP), ("PAR-P05S3", "p05 S3", LS3),
       ("REF-K3", "S3 + cost5 + intraday SPY-VWAP flip", np.where(c5, flip(vd > 0, vd < 0, LS3, SS3), nan))]
for k, v in FEAT.items():
    for o in "AB":
        up, dn = sides(k, o)
        CFG.append((k + o, f"S3 + cost5; {v} {'>' if o == 'A' else '<'} {CUT[k]:.4g} long, other side short", np.where(c5, flip(up, dn, LS3, SS3), nan)))
rows = []
for cid, rule, r in CFG:
    st = stats(p05, r, one); rows.append(dict(id=cid, rule=rule, **st))
rr = [x for x in rows if x["id"][:2] in FEAT and len(x["id"]) == 3]
best = max(rr, key=lambda x: x["avg_train"])["id"]
up, dn = sides(best[:2], best[2])
tape_up, tape_dn = vd > 0, vd < 0
EXTRA = [("G1", f"S3 + cost5; long only on {best} long side, skip other", np.where(c5 & up, LS3, nan)),
         ("C1", f"{best} only when intraday SPY-VWAP side agrees", np.where(c5, flip(up & tape_up, dn & tape_dn, LS3, SS3), nan)),
         ("C2", f"{best} with cost10", np.where(c10, flip(up, dn, LS3, SS3), nan)),
         ("C3", f"{best} on parent exits, no cost floor", flip(up, dn, LP, SP))]
for cid, rule, r in EXTRA:
    st = stats(p05, r, one); rows.append(dict(id=cid, rule=rule, **st))
assert len(rows) == COUNT
for x in rows:
    x["passes"] = passes(x)
    if x["id"] in REF:
        a, b = REF[x["id"]]; x["parity_ok"] = abs(x["avg_train"] - a) <= 0.005 and abs(x["avg_valid"] - b) <= 0.005
    x["bar_t"] = round(BAR, 3); x["N"] = N
R = pd.DataFrame(rows)
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 70)
print(f"sessions {NSESS}  N {N}  BAR {BAR:.3f}  TRAIN-best R-row {best}  cuts {CUT}")
print(R.to_string(index=False))
R.to_csv(D / "results.csv", index=False)
# daily regime predictive check (descriptive, same rows): corr of feature with SPY session return, TRAIN / VALID
for k, v in FEAT.items():
    print(k, v, "corr(feature, spy_day) train %.3f valid %.3f" % (DAY.loc[TRD, v].corr(DAY.loc[TRD, "spy_day"]), DAY.loc[~TRD, v].corr(DAY.loc[~TRD, "spy_day"])))
