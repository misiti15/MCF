"""Part 4: "heat 2.0" - a multi-factor confluence score (lineage heat2-confluence, N = 24 pre-declared configs, HEAT.md
section 2). Linear ridge models on standardised, train-clipped features; fit on train only (2024-10, 2025-03..2025-12),
scored on valid (2026-01..2026-10-07); expanding-window monthly walk-forward refit over the open history; market-neutral
controls (no-market feature set, SPY-residual forward-return correlation, same-time excess).
Passes: (1) clip quantiles from a train sample, (2) accumulate normal equations per month + a 4% score sample per month,
(3) score every month, trade, correlate. One process, month by month; the locked block is never loaded.
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import score_hist as sh  # noqa: E402
from score_hist import COMP, RES, TRAIN_END, Acc, months, prep, regimes, summarise  # noqa: E402

RAWC = ["rsi", "rsi5", "momentum", "emaDiff", "macdPct", "volumeRatio", "volumeSurge", "pricePosition", "vwapDistPct",
        "buyPressure", "rsiSlope", "atrPct", "gap", "fromOpen", "dist_pdh_atr", "dist_pdl_atr", "dist_hod_atr",
        "dist_lod_atr", "dist_round_atr", "sma20_dist_pct", "sma50_dist_pct", "sma20_slope_pct", "flow3", "flow9prev",
        "vol_climax", "bear_div", "bull_div", "upper_wick", "lower_wick", "vwapReclaim"]
BASE_F = (COMP + ["candleHeat", "heat", "heat_v2", "dh1", "d3_v0", "max6_v0", "min6_v0"]
          + [c for c in RAWC if c not in ("volumeRatio", "volumeSurge")]
          + ["lvr", "lvs", "mom_atr", "fo_atr", "tod1", "tod2", "tod3", "tod4", "tod5"])
MKT_F = ["spy_heat", "spy_fo", "spy_mom", "breadth", "rel_fo", "rel_mom"]
FEATS = BASE_F + MKT_F
NO_MKT = [FEATS.index(f) for f in BASE_F]
TARGETS = {"A": ["pr_long", "pr_short"], "B": ["bot_c", "top_c"]}   # A: tradeable rows, B: + turn-eligible rows
MODELS = [(m, side, fs) for m in ("M1", "M2") for side in ("long", "short") for fs in ("full", "nomkt")]
QS = (0.99, 0.995, 0.998)
LAM = 1e-3
STATE = HERE / "data" / "heat2_state.npz"


def features(month: str):
    df = prep(month, RAWC)
    g = df.groupby(["symbol", "date"], sort=False)
    df["dh1"] = (df.heat - g.heat.shift(1)).astype("float32")
    df["lvr"] = np.log(df.volumeRatio.clip(0.05, 20)).astype("float32")
    df["lvs"] = np.log(df.volumeSurge.clip(0.05, 20)).astype("float32")
    df["mom_atr"] = (df.momentum / df.atrPct.replace(0, np.nan)).astype("float32")
    df["fo_atr"] = (df.fromOpen / (100 * df.atr_d / df.close)).astype("float32")
    for k, (a, b) in enumerate(((0, 1030), (1031, 1130), (1131, 1330), (1331, 1430), (1431, 2400)), 1):
        df[f"tod{k}"] = ((df.tod >= a) & (df.tod <= b)).astype("float32")
    spy = df[df.symbol == "SPY"].set_index(["date", "tod"])
    m = spy[["heat", "fromOpen", "momentum", "close"]].rename(columns={"heat": "spy_heat", "fromOpen": "spy_fo",
                                                                     "momentum": "spy_mom", "close": "spy_close"})
    df = df.merge(m, left_on=["date", "tod"], right_index=True, how="left")
    br = df[df.trade_ok].groupby(["date", "tod"]).fromOpen.apply(lambda x: (x > 0).mean()).rename("breadth")
    df = df.merge(br, left_on=["date", "tod"], right_index=True, how="left")
    df["rel_fo"] = (df.fromOpen - df.spy_fo).astype("float32")
    df["rel_mom"] = (df.momentum - df.spy_mom).astype("float32")
    g = df.groupby(["symbol", "date"], sort=False)
    df["fwd6"] = (g.close.shift(-6) / df.close - 1).astype("float32")
    df["spy_fwd6"] = (df.groupby(["symbol", "date"], sort=False).spy_close.shift(-6) / df.spy_close - 1).astype("float32")
    X = df[FEATS].to_numpy(np.float32)
    return df, X


def clip_std(X, lo, hi):
    X = np.clip(X, lo, hi)
    return np.where(np.isfinite(X), X, 0.0).astype(np.float32)


def gram(Zm, ys):
    """Chunked float64 sums: (sum x, X'X, [X'y])."""
    P = Zm.shape[1]
    sx, xx, xy = np.zeros(P), np.zeros((P, P)), [np.zeros(P) for _ in ys]
    for a in range(0, len(Zm), 200_000):
        z = Zm[a:a + 200_000].astype(np.float64)
        sx += z.sum(0)
        xx += z.T @ z
        for k, y in enumerate(ys):
            xy[k] += z.T @ y[a:a + 200_000]
    return sx, xx, xy


def solve(S, cols, tname):
    """Ridge on standardised features from accumulated sums S (dict of arrays) restricted to feature columns `cols`."""
    n, sx, xx = S["n"], S["sx"][cols], S["xx"][np.ix_(cols, cols)]
    sy, xy = S[f"sy_{tname}"], S[f"xy_{tname}"][cols]
    mu = sx / n
    cov = xx / n - np.outer(mu, mu)
    sd = np.sqrt(np.clip(np.diag(cov), 1e-12, None))
    corr = cov / np.outer(sd, sd)
    cxy = (xy / n - mu * sy / n) / sd
    w = np.linalg.solve(corr + LAM * np.eye(len(cols)), cxy)
    return w / sd, mu, w     # score = (x - mu) @ (w / sd); w = standardised weights


def main():
    RES.mkdir(exist_ok=True)
    ms = months()
    t0 = time.time()
    # ---------------- pass 1: clip quantiles from a train sample
    rng = np.random.default_rng(20261011)
    samp = []
    for m in ("2025-03", "2025-07", "2025-11"):
        df, X = features(m)
        ok = df.trade_ok.to_numpy()
        X = X[ok]
        samp.append(X[rng.random(len(X)) < 0.05])
        print("pass1", m, f"{time.time() - t0:.0f}s", flush=True)
    samp = np.concatenate(samp)
    lo = np.nanpercentile(samp, 0.5, axis=0)
    hi = np.nanpercentile(samp, 99.5, axis=0)
    del samp
    # ---------------- pass 2: per-month normal equations + 4% sample
    P = len(FEATS)
    acc = {}
    smp = {}
    beta_num = beta_den = 0.0
    for m in ms:
        df, X = features(m)
        Z = clip_std(X, lo, hi)
        del X
        A = df.trade_ok.to_numpy() & np.isfinite(df.pr_long.to_numpy()) & np.isfinite(df.pr_short.to_numpy())
        B = A & df.elig.to_numpy()
        for key, mask in (("A", A), ("B", B)):
            Zm = Z[mask]
            ys = [df[t].to_numpy(np.float64)[mask] for t in TARGETS[key]]
            sx, xx, xy = gram(Zm, ys)
            S = {"n": float(mask.sum()), "sx": sx, "xx": xx}
            for t, y, v in zip(TARGETS[key], ys, xy):
                S[f"sy_{t}"], S[f"xy_{t}"] = y.sum(), v
            acc[(m, key)] = S
            del Zm
        smp[m] = Z[A][rng.random(A.sum()) < 0.04].astype(np.float32)
        if m <= TRAIN_END:
            f, s = df.fwd6.to_numpy(float), df.spy_fwd6.to_numpy(float)
            ok = A & np.isfinite(f) & np.isfinite(s)
            beta_num += (f[ok] * s[ok]).sum()
            beta_den += (s[ok] ** 2).sum()
        print("pass2", m, f"{time.time() - t0:.0f}s", flush=True)
        del df, Z
    beta = beta_num / beta_den

    def summed(mlist, key):
        S = None
        for m in mlist:
            a = acc[(m, key)]
            S = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in a.items()} if S is None else \
                {k: S[k] + a[k] for k in S}
        return S

    def fit(mlist):
        out = {}
        SA, SB = summed(mlist, "A"), summed(mlist, "B")
        for (mod, side, fs) in MODELS:
            cols = list(range(P)) if fs == "full" else NO_MKT
            S, t = (SA, f"pr_{side}") if mod == "M1" else (SB, "bot_c" if side == "long" else "top_c")
            w, mu, wz = solve(S, cols, t)
            out[(mod, side, fs)] = (cols, w, mu, wz)
        return out

    def scores(models, Z):
        return {k: (Z[:, c] - mu.astype(np.float32)) @ w.astype(np.float32) for k, (c, w, mu, _) in models.items()}

    def thresholds(models, mlist):
        Zs = np.concatenate([smp[m] for m in mlist]).astype(np.float64)
        sc = scores(models, Zs)
        return {k: {q: float(np.quantile(v, q)) for q in QS} for k, v in sc.items()}

    train_ms = [m for m in ms if m <= TRAIN_END]
    M_train = fit(train_ms)
    thr_train = thresholds(M_train, train_ms)
    wf = {}
    for i, m in enumerate(ms):
        if i >= 3:
            mods = fit(ms[:i])
            wf[m] = (mods, thresholds(mods, ms[:i]))
    # weights report
    wrep = {}
    for k, (c, w, mu, wz) in M_train.items():
        names = [FEATS[j] for j in c]
        top = np.argsort(-np.abs(wz))[:12]
        wrep["-".join(k)] = [(names[j], round(float(wz[j]), 5)) for j in top]
    json.dump({"weights_std_top12": wrep, "beta_spy": beta, "lo": lo.tolist(), "hi": hi.tolist(), "feats": FEATS},
              open(RES / "heat2_model.json", "w"), indent=1)
    # ---------------- pass 3: score, trade, correlate
    accT, accW = Acc(), Acc()
    corr_rows = []
    for m in ms:
        df, X = features(m)
        Z = clip_std(X, lo, hi)
        del X
        sc = scores(M_train, Z)
        f, s = df.fwd6.to_numpy(float), df.spy_fwd6.to_numpy(float)
        res = f - beta * s
        okc = df.trade_ok.to_numpy() & np.isfinite(f) & np.isfinite(s)
        extra = {("orig", "long", "v0fade"): -df.heat.to_numpy(float), ("orig", "short", "v0fade"): df.heat.to_numpy(float),
                 ("orig", "long", "v2follow"): df.heat_v2.to_numpy(float), ("orig", "short", "v2follow"): -df.heat_v2.to_numpy(float)}
        for k, v in list(sc.items()) + list(extra.items()):
            sgn = 1.0 if k[1] == "long" else -1.0
            x = v[okc]
            for lab, y in (("raw", sgn * f[okc]), ("resid", sgn * res[okc]), ("spy", sgn * s[okc])):
                corr_rows.append({"month": m, "model": "-".join(k), "y": lab, "n": len(x), "sx": x.sum(), "sy": y.sum(),
                                  "sxx": (x * x).sum(), "syy": (y * y).sum(), "sxy": (x * y).sum()})
        for k, v in sc.items():
            mod, side, fs = k
            for q in QS:
                name = f"{mod}-{side}-{fs}-q{q}"
                accT.add_trades(name, df, v >= thr_train[k][q], side)
                accT.add_turns(name, m, df, v >= thr_train[k][q], side)
        if m in wf:
            mods, thr = wf[m]
            sw = scores(mods, Z)
            for k, v in sw.items():
                mod, side, fs = k
                for q in QS:
                    accW.add_trades(f"{mod}-{side}-{fs}-q{q}", df, v >= thr[k][q], side)
        print("pass3", m, f"{time.time() - t0:.0f}s", flush=True)
        del df, Z
    pd.concat(accT.days).to_csv(RES / "heat2_days.csv.gz", index=False)
    pd.concat(accT.turns).to_csv(RES / "heat2_turns.csv", index=False)
    pd.concat(accW.days).to_csv(RES / "heat2_wf_days.csv.gz", index=False)
    pd.DataFrame(corr_rows).to_csv(RES / "heat2_corr.csv", index=False)
    report()


def report():
    reg = regimes()
    days = pd.read_csv(RES / "heat2_days.csv.gz")
    wfd = pd.read_csv(RES / "heat2_wf_days.csv.gz")
    for d in (days, wfd):
        d["date"] = pd.to_datetime(d.date).dt.date
        d["split"] = np.where(pd.to_datetime(d.date).dt.strftime("%Y-%m") <= TRAIN_END, "train", "valid")
    rows = []
    for cfg, d in days.groupby("config"):
        rec = {"config": cfg}
        for sp, dd in d.groupby("split"):
            s = summarise(dd.reset_index(drop=True), reg)
            rec.update({f"{sp}_{k}": v for k, v in s.items() if k in ("n", "exp_r", "t", "excess", "exp_up", "exp_down",
                                                                         "n_up", "n_down", "ex_best_day", "win", "days")})
        w = wfd[wfd.config == cfg]
        if len(w):
            s = summarise(w.reset_index(drop=True), reg)
            mon = pd.to_datetime(w.date).dt.strftime("%Y-%m")
            mm = w.groupby(mon)[["sum_r", "n"]].sum()
            mm = mm[mm.n >= 10]
            rec.update({"wf_n": s["n"], "wf_exp_r": s["exp_r"], "wf_t": s["t"], "wf_excess": s["excess"],
                        "wf_share_pos": round(float((mm.sum_r > 0).mean()), 3), "wf_months": len(mm),
                        "wf_exp_up": s.get("exp_up"), "wf_exp_down": s.get("exp_down")})
        rows.append(rec)
    out = pd.DataFrame(rows).sort_values("valid_exp_r", ascending=False)
    out.to_csv(RES / "heat2_summary.csv", index=False)
    c = pd.read_csv(RES / "heat2_corr.csv")
    c["split"] = np.where(c.month <= TRAIN_END, "train", "valid")
    g = c.groupby(["model", "y", "split"])[["n", "sx", "sy", "sxx", "syy", "sxy"]].sum()
    cor = (g.sxy / g.n - g.sx * g.sy / g.n ** 2) / np.sqrt((g.sxx / g.n - (g.sx / g.n) ** 2) * (g.syy / g.n - (g.sy / g.n) ** 2))
    cor = cor.unstack(["split", "y"]).round(4)
    cor.to_csv(RES / "heat2_corr_summary.csv")
    with pd.option_context("display.width", 250, "display.max_rows", 100, "display.max_columns", 40):
        print(out.to_string(index=False))
        print(cor.to_string())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        report()
    else:
        main()
