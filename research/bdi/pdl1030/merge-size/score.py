"""pdl1030/merge-size step 2: score the PLAN.md rows (TRAIN / VALID only) on the cached merged-union trades.
Weighted book: avg R = sum(w r) / sum(w); day-clustered t with the weighted residuals. Educational only - not financial advice.
"""
import os, sys, math, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
sys.path[:0] = ["/home/user/MCF"]
from mcf.research import gates  # noqa
HERE = Path(__file__).resolve().parent
C = HERE / "cache"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
N_PRIOR, N_ME = 121512, 20
N_CUM = N_PRIOR + 3 * N_ME
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N_CUM))))
SW15 = {"p05": -0.0677, "p05lv": -0.0950, "p10": -0.0880}
PAR_P05 = dict(train=-0.0677, valid=-0.0675)


def load(prefix):
    T = pd.concat([pd.read_parquet(C / f"{prefix}_{m}.parquet") for m in MONTHS], ignore_index=True)
    d = T["date"].astype(str)
    assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not ((d >= "2026-04-01") & (d <= "2026-06-30")).any()
    assert (d <= "2026-09-15").all()
    T["split"] = np.where(d <= "2025-12-31", "train", "valid")
    T["month"] = d.str[:7]
    return T


def wsum(df, r, w):
    """weighted mean and day-clustered t."""
    W = w.sum()
    mu = float((w * r).sum() / W)
    g = pd.DataFrame({"d": df["date"].to_numpy(), "x": w * (r - mu)}).groupby("d")["x"].sum()
    se = float(np.sqrt((g ** 2).sum()) / W)
    return mu, (mu / se if se > 0 else np.nan)


def stats(df, r, w, nsess):
    r, w = np.asarray(r, float), np.asarray(w, float)
    ok = np.isfinite(r) & (w > 0)
    df, r, w = df[ok], r[ok], w[ok]
    res = {}
    for sp in ("train", "valid"):
        m = (df["split"] == sp).to_numpy()
        res[f"avg_{sp}"], res[f"t_{sp}"] = (round(v, 4) for v in wsum(df[m], r[m], w[m]))
    mu, t = wsum(df, r, w)
    res["avg_tv"], res["t_tv"] = round(mu, 4), round(t, 2)
    day = pd.DataFrame({"d": df["date"].to_numpy(), "wr": w * r, "w": w}).groupby("d").sum()
    b = day["wr"].idxmax()
    res["ex_best"] = round(float((day["wr"].sum() - day.loc[b, "wr"]) / (day["w"].sum() - day.loc[b, "w"])), 4)
    res["best_share"] = round(float(day.loc[b, "wr"] / day["wr"].sum()), 3) if day["wr"].sum() > 0 else None
    mo = pd.DataFrame({"m": df["month"].to_numpy(), "wr": w * r}).groupby("m")["wr"].sum()
    res["wf_pct"] = round(float((mo > 0).mean() * 100), 1)
    up = (df["spy_day"] > 0).to_numpy(); dn = (df["spy_day"] < 0).to_numpy()
    res["up_day_r"] = round(float((w[up] * r[up]).sum() / w[up].sum()), 4)
    res["down_day_r"] = round(float((w[dn] * r[dn]).sum() / w[dn].sum()), 4)
    res["n_tv"] = int(len(r))
    res["per_session"] = round(len(r) / nsess, 1)
    res["risk_units_per_session"] = round(float(w.sum()) / nsess, 1)
    return res


def verdict(st):
    return bool(np.isfinite(st["t_tv"]) and st["t_tv"] >= BAR and st["wf_pct"] >= 54 and st["avg_train"] > 0 and st["avg_valid"] > 0
                and st["avg_train"] > PAR_P05["train"] and st["avg_valid"] > PAR_P05["valid"]
                and (st["per_session"] >= 76.6 or st["per_session"] >= 25))


def beta_train(U, r, mv, w):
    m = (U["split"] == "train").to_numpy() & np.isfinite(r) & np.isfinite(mv)
    X = np.c_[np.ones(m.sum()), mv[m]]
    coef = np.linalg.lstsq(X * np.sqrt(w[m])[:, None], r[m] * np.sqrt(w[m]), rcond=None)[0]
    return float(coef[1])


def hedge_r(U, r, mv, b):
    """SPY short, notional = 100 b $risk -> P/L in R = -b * mv; costs 1c/share + 1 bp per side on that notional."""
    px = U["spy_px"].to_numpy(float)
    cost = 2 * 100 * b * (1e-4 + 0.01 / px)
    return r - b * mv - cost


def main():
    count = 0
    rows = []
    PAR = load("par")
    U = load("u")
    nsess = U["date"].nunique()
    print("sessions", nsess, "union n", len(U), "per session", round(len(U) / nsess, 1), "share p05 bar", round(U.is_p05.mean(), 3))

    def score(id_, rule, df, r, w, known):
        nonlocal count
        count += 1
        st = stats(df, r, w, nsess)
        st.update(id=id_, rule=rule, known_at_entry=known, passes=verdict(st))
        rows.append(st)
        print(id_, {k: st[k] for k in ("avg_train", "avg_valid", "avg_tv", "t_tv", "wf_pct", "per_session", "risk_units_per_session",
                                        "up_day_r", "down_day_r", "ex_best", "passes")}, flush=True)
        return st

    par = {}
    for s in ("p05", "p05lv", "p10", "p10lv"):
        d = PAR[PAR.setup == s].copy()
        d["spy_day"] = 0.0
        d = d.merge(U[["date", "symbol", "spy_day"]].drop_duplicates(["date", "symbol"]), on=["date", "symbol"], how="left", suffixes=("_x", ""))
        d["spy_day"] = d["spy_day"].fillna(0.0)
        par[s] = score(s.upper(), f"parent {s}", d, d["r"].to_numpy(), np.ones(len(d)), "parent")
    par_ok = all(abs(par[s]["avg_tv"] - v) <= 0.005 for s, v in SW15.items())
    print("PARITY", par_ok, {s: (par[s]["avg_tv"], v) for s, v in SW15.items()}, flush=True)
    if not par_ok:
        pd.DataFrame(rows).to_csv(HERE / "results.csv", index=False)
        return

    r1, r3 = U["r1"].to_numpy(float), U["r3"].to_numpy(float)
    one = np.ones(len(U))
    spy_below = (U["spy_vd"].to_numpy(float) < 0)
    br = U["breadth"].to_numpy(float)
    w1 = np.where(spy_below, 0.5, 1.0)
    w2 = np.where(br < 0.5, 0.5, 1.0)
    w3 = 0.25 + 0.25 * (U["spy_vd"].to_numpy(float) > 0) + 0.25 * (br >= 0.5) + 0.25 * (U["spy_gap"].to_numpy(float) <= -0.5)
    w4 = np.clip(U["depth"].to_numpy(float) / 0.25, 0.5, 2.0)
    w5 = np.clip(0.05 / U["cost_R1"].to_numpy(float), 0.25, 1.0)
    w5_3 = np.clip(0.05 / U["cost_R3"].to_numpy(float), 0.25, 1.0)
    # k = union signals in the session up to and including this bar (same-bar signals all counted: known at bar close)
    k = U.groupby("date")["tod"].rank(method="max").to_numpy(float)
    w6 = np.minimum(1.0, 30.0 / k)
    w7 = U["nmem"].to_numpy(float)

    K_TAPE = "SPY VWAP dist and breadth at the signal-bar close; SPY gap at the open"
    score("M0", "merged union, p05 exit, w=1", U, r1, one, "signal-bar close")
    score("W1", "w=0.5 if SPY below VWAP", U, r1, w1, K_TAPE)
    score("W2", "w=0.5 if breadth<0.5", U, r1, w2, K_TAPE)
    score("W3", "tape score 0.25..1", U, r1, w3, K_TAPE)
    score("W4", "w=clip(depth/0.25ATR,0.5,2)", U, r1, w4, "day low so far, signal-bar close")
    score("W5", "w=clip(0.05/cost_R,0.25,1)", U, r1, w5, "entry price, ATR, tier, time of day")
    score("W6", "w=min(1,30/k) session budget", U, r1, w6, "count of earlier/same-bar union signals")
    score("W7", "w=#parents firing on bar", U, r1, w7, "signal-bar close")
    score("S1", "3R stop at same $ (target/scale prices kept), w=1", U, r3, one, "signal-bar close")
    score("C1", "S1 + W5(3R)", U, r3, w5_3, "entry price, ATR, tier, time of day")
    score("C2", "S1 + W5(3R) x W1", U, r3, w5_3 * w1, K_TAPE)
    score("C3", "S1 + W5(3R) x W6", U, r3, w5_3 * w6, "as W5 + signal count")
    score("C4", "S1 + W5(3R) x W3", U, r3, w5_3 * w3, K_TAPE)
    score("C5", "S1 + W5(3R) x W1 x W6", U, r3, w5_3 * w1 * w6, K_TAPE + "; signal count")
    mv1, mv3 = U["spy_mv1"].to_numpy(float), U["spy_mv3"].to_numpy(float)
    b1 = beta_train(U, r1, mv1, one)
    b3 = beta_train(U, r3, mv3, w5_3)
    print("hedge betas (TRAIN fit)", round(b1, 3), round(b3, 3))
    score("H1", f"M0 + SPY short hedge b={b1:.3f} (TRAIN fit)", U, hedge_r(U, r1, mv1, b1), one, "b fit on TRAIN; hedge opened at entry")
    score("H2", f"C1 + SPY short hedge b={b3:.3f} (TRAIN fit)", U, hedge_r(U, r3, mv3, b3), w5_3, "b fit on TRAIN; hedge opened at entry")
    print("count", count, "N_cum", N_CUM, "bar", round(BAR, 3), flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(HERE / "results.csv", index=False)
    print(R[["id", "avg_train", "avg_valid", "t_tv", "wf_pct", "per_session", "risk_units_per_session", "up_day_r", "down_day_r",
             "ex_best", "best_share", "passes"]].to_string())


if __name__ == "__main__":
    main()
