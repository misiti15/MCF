"""pdl1030b scoring of the 23 pre-declared rows (PLAN.md). TRAIN+VALID only (cache built by build.py).
Pair R = stock r + beta x hedge leg (per-unit-beta P/L, costs in, R of the stock's risk). Day-clustered t as combo/score.py.
Educational only - not financial advice.

    python research/bdi/pdl1030b/score.py
"""
import os, math
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).resolve().parent
C = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030b/cache")
T = pd.concat([pd.read_parquet(p) for p in sorted(C.glob("tr_*.parquet"))], ignore_index=True)
DC = pd.concat([pd.read_parquet(p) for p in sorted(C.glob("dc_*.parquet"))], ignore_index=True)
for df in (T, DC):
    d = df["date"].astype(str)
    assert (d <= "2026-09-15").all()
    assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
d = T["date"].astype(str)
T["month"] = d.str[:7]; T["split"] = np.where(d <= "2025-12-31", "train", "valid")
NSESS = T.loc[T.set == "p05", "date"].nunique()
COUNT = 23
N = 121611 + COUNT
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N))))
PAR = dict(train=-0.0677, valid=-0.0675)


# ---- prior-20-session beta (daily close-to-close; no returns across gaps > 5 calendar days)
def betas(etf):
    px = DC.pivot_table(index="date", columns="symbol", values="close", aggfunc="last").sort_index()
    dt = pd.to_datetime(px.index)
    ok = np.r_[False, (dt[1:] - dt[:-1]).days <= 5]
    ret = px.pct_change(fill_method=None)
    ret.loc[~ok] = np.nan
    m = ret[etf]
    out = {}
    X = ret
    Y = pd.DataFrame(np.repeat(m.to_numpy()[:, None], X.shape[1], 1), index=X.index, columns=X.columns)
    v = X.notna() & Y.notna()
    Xv, Yv = X.where(v), Y.where(v)
    r20 = lambda z: z.rolling(20, min_periods=15).sum()
    n = r20(v.astype(float))
    sx, sy, sxy, syy = r20(Xv.fillna(0)), r20(Yv.fillna(0)), r20((Xv * Yv).fillna(0)), r20((Yv * Yv).fillna(0))
    n = n.where(v.astype(float).rolling(20, min_periods=1).sum() >= 15)
    cov = sxy / n - sx * sy / n ** 2
    var = syy / n - (sy / n) ** 2
    b = (cov / var).shift(1)  # known before the session: returns up to the prior close only
    b = b.clip(0, 3)
    s = b.stack().rename("b").reset_index()
    return s


for etf, col in (("SPY", "b20spy"), ("QQQ", "b20qqq")):
    s = betas(etf).rename(columns={"b": col})
    T = T.merge(s, on=["date", "symbol"], how="left")
    T[col] = T[col].fillna(1.0)


def wsum(dates, r):
    mu = float(r.mean())
    g = pd.Series(r - mu).groupby(dates).sum()
    se = float(np.sqrt((g ** 2).sum()) / len(r))
    return mu, (mu / se if se > 0 else np.nan)


def stats(df, r):
    r = np.asarray(r, float)
    ok = np.isfinite(r)
    df, r = df[ok], r[ok]
    dates = df["date"].astype(str).to_numpy()
    res = {}
    for sp in ("train", "valid"):
        m = (df["split"] == sp).to_numpy()
        mu, t = wsum(dates[m], r[m]); res[f"avg_{sp}"], res[f"t_{sp}"] = round(mu, 4), round(t, 2)
    mu, t = wsum(dates, r); res["avg_tv"], res["t_tv"] = round(mu, 4), round(t, 2)
    day = pd.Series(r).groupby(dates).agg(["sum", "size"])
    b = day["sum"].idxmax()
    res["ex_best"] = round(float((day["sum"].sum() - day.loc[b, "sum"]) / (day["size"].sum() - day.loc[b, "size"])), 4)
    res["best_share"] = round(float(day.loc[b, "sum"] / day["sum"].sum()), 3) if day["sum"].sum() > 0 else None
    mo = pd.Series(r).groupby(df["month"].to_numpy()).sum()
    res["wf_pct"] = round(float((mo > 0).mean() * 100), 1)
    up = (df["spy_day"] > 0).to_numpy(); dn = (df["spy_day"] < 0).to_numpy()
    res["up_day_r"] = round(float(r[up].mean()), 4); res["down_day_r"] = round(float(r[dn].mean()), 4)
    res["n_tv"] = int(len(r)); res["per_session"] = round(len(r) / NSESS, 1)
    res["sd_r"] = round(float(r.std()), 3)
    return res


def passes(st):
    return bool(np.isfinite(st["t_tv"]) and st["t_tv"] >= BAR and st["wf_pct"] >= 54 and st["avg_train"] > 0 and st["avg_valid"] > 0
                and st["up_day_r"] > 0 and st["down_day_r"] > 0 and st["per_session"] >= 25)


def S(name):
    return T[T.set == name].reset_index(drop=True)


p05, p10, er5, er10, ec5, ec10, ec5a = (S(k) for k in ("p05", "p10", "e_rec05", "e_rec10", "e_con05", "e_con10", "e_con05any"))
nan = np.nan
def c5(df):
    return df["cost_rt_R"].to_numpy(float) <= 0.05
def v(df, k):
    return df[k].to_numpy(float)
CFG = [
    ("A0", "p05 parent, no hedge (parity)", p05, v(p05, "r_P")),
    ("A1", "p05 parent + SPY beta1", p05, v(p05, "r_P") + v(p05, "hSPY_P")),
    ("A2", "p05 parent + SPY beta20", p05, v(p05, "r_P") + v(p05, "b20spy") * v(p05, "hSPY_P")),
    ("A3", "p05 S3 + cost5, no hedge", p05, np.where(c5(p05), v(p05, "r_S3"), nan)),
    ("A4", "p05 S3 + cost5 + SPY beta1", p05, np.where(c5(p05), v(p05, "r_S3") + v(p05, "hSPY_S3"), nan)),
    ("A5", "p05 S3 + cost5 + SPY beta20", p05, np.where(c5(p05), v(p05, "r_S3") + v(p05, "b20spy") * v(p05, "hSPY_S3"), nan)),
    ("A6", "p05 S3 + SPY beta20", p05, v(p05, "r_S3") + v(p05, "b20spy") * v(p05, "hSPY_S3")),
    ("A7", "p05 parent + cost5 + SPY beta20", p05, np.where(c5(p05), v(p05, "r_P") + v(p05, "b20spy") * v(p05, "hSPY_P"), nan)),
    ("A8", "p05 S3 + cost5 + QQQ beta1", p05, np.where(c5(p05), v(p05, "r_S3") + v(p05, "hQQQ_S3"), nan)),
    ("A9", "p05 S3 + cost5 + QQQ beta20", p05, np.where(c5(p05), v(p05, "r_S3") + v(p05, "b20qqq") * v(p05, "hQQQ_S3"), nan)),
    ("A10", "p10 S3 + cost5 + SPY beta20", p10, np.where(c5(p10), v(p10, "r_S3") + v(p10, "b20spy") * v(p10, "hSPY_S3"), nan)),
    ("B1", "early reclaim long p05 exits", er5, v(er5, "r_P")),
    ("B2", "early reclaim long S3 + cost5", er5, np.where(c5(er5), v(er5, "r_S3"), nan)),
    ("B3", "early reclaim long S3 + cost5 + SPY beta20", er5, np.where(c5(er5), v(er5, "r_S3") + v(er5, "b20spy") * v(er5, "hSPY_S3"), nan)),
    ("B4", "early reclaim long target 1R", er5, v(er5, "r_T1")),
    ("B5", "early continuation short 0.05 (opened above PDL)", ec5, v(ec5, "r_P")),
    ("B6", "early continuation short 0.10", ec10, v(ec10, "r_P")),
    ("B7", "early continuation short S3 + cost5", ec5, np.where(c5(ec5), v(ec5, "r_S3"), nan)),
    ("B8", "early continuation short S3 + cost5 + SPY beta20 (long SPY)", ec5, np.where(c5(ec5), v(ec5, "r_S3") + v(ec5, "b20spy") * v(ec5, "hSPY_S3"), nan)),
    ("B9", "early continuation short target 1R", ec5, v(ec5, "r_T1")),
    ("B10", "early continuation short 0.05, any open", ec5a, v(ec5a, "r_P")),
    ("B11", "early reclaim long p10 exits", er10, v(er10, "r_P10")),
    ("B12", "early continuation short 0.05 + SPY below VWAP", ec5, np.where(v(ec5, "spy_vd") < 0, v(ec5, "r_P"), nan)),
]
assert len(CFG) == COUNT
if __name__ == "__main__":
    rows = []
    print(f"sessions {NSESS}  N {N}  BAR {BAR:.3f}  beta20 fallback share p05 {(T.loc[T.set=='p05','b20spy']==1.0).mean():.3f}")
    print("beta20 SPY (p05) quantiles", p05["b20spy"].quantile([.1, .25, .5, .75, .9]).round(2).to_dict())
    for id_, rule, df, r in CFG:
        st = stats(df, r); st.update(id=id_, rule=rule, passes=passes(st))
        rows.append(st)
    R = pd.DataFrame(rows)
    cols = ["id", "rule", "avg_train", "avg_valid", "avg_tv", "t_tv", "n_tv", "per_session", "wf_pct", "up_day_r", "down_day_r",
            "ex_best", "best_share", "sd_r", "passes"]
    R = R[cols]; R["bar_t"], R["N"] = round(BAR, 3), N
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 48)
    print(R.to_string(index=False))
    R.to_csv(D / "results.csv", index=False)
