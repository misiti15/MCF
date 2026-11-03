"""eu1103/preopen: score the pre-declared pre-open gates (PLAN.md) — chosen on TRAIN, judged once on VALID and live.
    python gates.py <scratch>  -> research/bdi/eu1103/preopen/{all_gates.csv, chosen.csv, results.json}
Educational only - not financial advice."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1])
OUT = Path("/home/user/MCF/research/bdi/eu1103/preopen")
MIN_ADV = {"CWT14-failbrk-orl-p05-long": 95e6, "CWT14-failbrk-pdl-p05-long": 95e6, "CWT12-coil-k4-long": 95e6,
           "CWT14-failbrk-pdh-p10-short": 95e6, "heat_fade_short-FD": 125e6, "RW7-gapdn-bounce-early-short-FD": 95e6,
           "RW2-exhaustion-noon-adv150-short-FD": 150e6, "L3-gap-slope-fromopen-FD": 0.0}
SYM_F = ["pm_rvol", "pm_share", "pm_gap_atr", "pm_gap_side", "pm_range_atr", "pcl", "news_n", "o5_rvol", "o5_ret_side"]
MKT_F = ["spy_pm_side", "qqq_spy_side", "pm_breadth_side", "pm_disp", "sec_pm_side"]
FEATS = SYM_F + MKT_F
CUTS = [("lo", 0.1), ("lo", 0.2), ("lo", 0.3), ("hi", 0.9), ("hi", 0.8), ("hi", 0.7)]


def add_side(x, sgn):
    x = x.copy()
    x["pm_gap_side"] = x.pm_gap_atrs * sgn
    x["o5_ret_side"] = x.o5_ret_atrs * sgn
    x["spy_pm_side"] = x.SPY_pm * sgn
    x["qqq_spy_side"] = x.qqq_spy_pm * sgn
    x["pm_breadth_side"] = x.pm_breadth * sgn
    x["sec_pm_side"] = x.sec_pm * sgn
    return x


def cl_t(r, k, day):
    """Day-clustered t of b in r = a + b*k (b = mean kept - mean dropped)."""
    k = k.astype(float)
    if k.all() or not k.any():
        return np.nan
    X = np.column_stack([np.ones_like(k), k])
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ r
    e = r - X @ b
    u = pd.DataFrame(X * e[:, None]).groupby(day).sum().to_numpy()
    V = XtX_inv @ (u.T @ u) @ XtX_inv
    return b[1] / np.sqrt(V[1, 1])


def evaluate(r, k, day, top, rc=None):
    n = len(r)
    o = {"n": n, "kept": int(k.sum()), "keep_share": k.mean(), "avg_all": r.mean(), "avg_kept": r[k].mean() if k.any() else np.nan,
         "lift": (r[k].mean() - r.mean()) if k.any() else np.nan, "t_kd": cl_t(r, k, day),
         "top_keep": k[top].mean() if top.any() else np.nan,
         "days_all": len(np.unique(day)), "days_kept": len(np.unique(day[k]))}
    if rc is not None:
        ok = np.isfinite(rc)
        o["ctrl_lift"] = rc[ok & k].mean() - rc[ok].mean() if (ok & k).any() else np.nan
    return o


def day_green(r, day):
    s = pd.Series(r).groupby(day).agg(["sum", "mean"])
    return {"sessions": len(s), "green_total": float((s["sum"] > 0).mean()), "green_avg": float((s["mean"] > 0).mean())}


def wo_best(r, day):
    s = pd.Series(r).groupby(day).sum()
    if len(s) < 2:
        return np.nan, np.nan
    b = s.idxmax()
    m = day != b
    return r[m].mean(), s.max() / s.sum() if s.sum() > 0 else np.nan


def load_2y():
    fs = [f for f in sorted((S / "t2y").glob("*.parquet")) if not f.stem.endswith("_ctrl")]
    t = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    t["date"] = t["date"].astype(str)
    t = t[t.adv20.astype(float) >= t.setup.map(MIN_ADV)]
    c = pd.concat([pd.read_parquet(f) for f in sorted((S / "t2y").glob("*_ctrl.parquet"))], ignore_index=True)
    c["date"] = c["date"].astype(str)
    c["symbol"] = c["symbol"].astype(str)
    t = t.merge(c, on=["date", "symbol", "side", "geom"], how="left")
    assert not ((t.date >= "2024-11-01") & (t.date <= "2025-02-28")).any()
    f = pd.read_parquet(S / "feat_hist.parquet")
    t = t.merge(f, on=["symbol", "date"], how="left")
    t["sgn"] = np.where(t.side == "long", 1.0, -1.0)
    return add_side(t, t.sgn.to_numpy())


def load_live():
    L = []
    for b in ("mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard", "mcf-data-gen"):
        c = sqlite3.connect(S / "j" / f"{b}.db")
        x = pd.read_sql("select symbol, strategy, side, date, entry, stop, shares, pnl_adj from trades where run_id=1", c)
        x["acct"] = b
        L.append(x)
    t = pd.concat(L, ignore_index=True)
    t = t[(t.date >= "2026-10-06") & (t.date <= "2026-11-02")]
    t["r"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares)
    t = t[np.isfinite(t.r)]
    t["sgn"] = np.where(t.side > 0, 1.0, -1.0)
    f = pd.read_parquet(S / "feat_live.parquet")
    t = t.merge(f, on=["symbol", "date"], how="left")
    return add_side(t, t.sgn.to_numpy()).rename(columns={"strategy": "setup"})


def main():
    T = load_2y()
    LV = load_live()
    rows, chosen = [], []
    groups = list(MIN_ADV) + ["POOLED"]
    for g in groups:
        tr = T[(T.split == "TRAIN")] if g == "POOLED" else T[(T.split == "TRAIN") & (T.setup == g)]
        va = T[(T.split == "VALID")] if g == "POOLED" else T[(T.split == "VALID") & (T.setup == g)]
        lv = LV if g == "POOLED" else LV[LV.setup == g]
        q90 = {s: tr.r.quantile(0.9) for s in ["x"]}["x"]
        best = None
        for fe in FEATS:
            v = tr[fe].to_numpy(float)
            if np.isfinite(v).mean() < 0.5:
                continue
            for side, q in CUTS:
                thr = np.nanquantile(v, q)
                def keep(df):
                    w = df[fe].to_numpy(float)
                    return ~(w < thr) if side == "lo" else ~(w > thr)
                k = keep(tr)
                top = tr.r.to_numpy() >= q90 if g != "POOLED" else (tr.r >= tr.groupby("setup").r.transform(lambda s: s.quantile(0.9))).to_numpy()
                e = evaluate(tr.r.to_numpy(), k, tr.date.to_numpy(), top, tr.rc.to_numpy(float))
                e.update(group=g, feature=fe, cut=f"{side}{int(q * 100)}", thr=thr, level="mkt" if fe in MKT_F else "sym",
                         split="TRAIN", admissible=bool(e["keep_share"] >= 0.7 and e["top_keep"] >= 0.9),
                         charter80=bool(e["keep_share"] >= 0.8 and e["top_keep"] >= 0.9))
                rows.append(e)
                if e["admissible"] and e["lift"] > 0 and np.isfinite(e["t_kd"]) and e["t_kd"] >= 1.0:
                    if best is None or e["lift"] > best[0]["lift"]:
                        best = (e, keep)
        if best is None:
            chosen.append({"group": g, "feature": None})
            continue
        e0, keep = best
        out = {"group": g, "feature": e0["feature"], "cut": e0["cut"], "thr": e0["thr"], "level": e0["level"],
               **{f"train_{k}": v for k, v in e0.items() if k in ("n", "keep_share", "avg_all", "avg_kept", "lift", "t_kd", "top_keep", "ctrl_lift")}}
        for nm, df in (("valid", va), ("live", lv)):
            if df.empty or e0["feature"] not in df:
                continue
            r = df.r.to_numpy(float); d = df.date.to_numpy(); k = keep(df)
            if g == "POOLED":
                top = (df.r >= df.groupby("setup").r.transform(lambda s: s.quantile(0.9))).to_numpy()
            else:
                top = r >= np.quantile(r, 0.9)
            e = evaluate(r, k, d, top, df.rc.to_numpy(float) if "rc" in df else None)
            e["feat_cov"] = float(np.isfinite(df[e0["feature"]].to_numpy(float)).mean())
            wa, sa = wo_best(r, d); wk, sk = wo_best(r[k], d[k])
            e.update(wobest_all=wa, wobest_kept=wk, bestshare_all=sa, bestshare_kept=sk)
            ga, gk = day_green(r, d), day_green(r[k], d[k])
            e.update(green_total_all=ga["green_total"], green_total_kept=gk["green_total"],
                     green_avg_all=ga["green_avg"], green_avg_kept=gk["green_avg"])
            out.update({f"{nm}_{kk}": vv for kk, vv in e.items()})
        out["pass"] = bool(out.get("valid_lift", -1) > 0 and out.get("live_lift", -1) > 0 and out.get("valid_t_kd", 0) >= 1.0
                           and out.get("valid_keep_share", 0) >= 0.7 and out.get("valid_top_keep", 0) >= 0.9
                           and out.get("live_keep_share", 0) >= 0.7 and out.get("live_top_keep", 0) >= 0.9)
        chosen.append(out)
    A = pd.DataFrame(rows)
    A.to_csv(OUT / "all_gates.csv", index=False, float_format="%.4f")
    C = pd.DataFrame(chosen)
    C.to_csv(OUT / "chosen.csv", index=False, float_format="%.4f")
    # descriptive (not configs): VALID + live avg R by tercile of each feature, pooled, for the notes
    desc = {}
    for nm, df in (("TRAIN", T[T.split == "TRAIN"]), ("VALID", T[T.split == "VALID"]), ("live", LV)):
        dd = {}
        for fe in FEATS:
            v = df[fe].to_numpy(float)
            if np.isfinite(v).mean() < 0.3:
                continue
            qs = np.nanquantile(T.loc[T.split == "TRAIN", fe].to_numpy(float), [1 / 3, 2 / 3])
            b = np.digitize(v, qs).astype(float); b[~np.isfinite(v)] = np.nan
            dd[fe] = {str(int(i)): [round(float(df.r.to_numpy()[b == i].mean()), 4), int((b == i).sum())] for i in (0, 1, 2)}
        desc[nm] = dd
    res = {"configs": int(len(A)), "admissible_train": int(A.admissible.sum()), "charter80_train": int(A.charter80.sum()),
           "chosen": C.to_dict(orient="records"), "terciles_pooled": desc,
           "n_trades": {"TRAIN": int((T.split == "TRAIN").sum()), "VALID": int((T.split == "VALID").sum()), "live_all": len(LV),
                        "live_8": int(LV.setup.isin(MIN_ADV).sum())},
           "feat_coverage": {nm: {fe: round(float(np.isfinite(df[fe].to_numpy(float)).mean()), 3) for fe in FEATS}
                             for nm, df in (("hist", T), ("live", LV))}}
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=lambda o: None if (isinstance(o, float) and not np.isfinite(o)) else (float(o) if isinstance(o, (np.floating,)) else str(o))))
    pd.set_option("display.width", 250)
    print(C.T.to_string())


if __name__ == "__main__":
    main()
