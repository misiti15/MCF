"""Concentration diagnostics on the already-scored stage-3 near-miss tier (no new configurations, no N added).
ETF trades cluster: on a trigger day many correlated ETFs (SPY/SPXL/UPRO/SSO, QQQ/TQQQ/QLD, ...) fire together.
Per configuration on all open data: best-day share of P/L, exp and day-clustered t without the best day (train, valid),
day-weighted t (every session one observation = its mean R), a 3-trades-per-session cap (first by tod, symbol),
April 2025 removed, share of months positive, valid regime split.
python robust.py <rows_dir>. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from engine import Panel, cond_mat, first_trades, trade_frame  # noqa: E402

from mcf.research import gates  # noqa: E402

P = Panel(sys.argv[1])
cache = {}
R = pd.read_csv(HERE / "results.csv")
F = R[R.near_miss.fillna(False).astype(bool)].copy()
F["key"] = F.conds.map(lambda s: json.dumps(sorted(json.loads(s)))) + F.side + F.geom + F.window
F = F.drop_duplicates("key")
REG = P.regimes_df["regime"]


def summ(t):
    if len(t) < 2:
        return {"n": len(t), "exp": np.nan, "t": np.nan}
    s = gates.summary(t[["date", "r"]])
    return {"n": s["n"], "exp": s["exp_r"], "t": s["t"]}


def tday(t):
    d = t.groupby("date")["r"].mean()
    return float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))) if len(d) > 2 else np.nan


rows = []
for r in F.itertuples():
    cs = [(a, b, tuple(v) if isinstance(v, list) else v) for a, b, v in json.loads(r.conds)]
    w = tuple(int(v) for v in r.window.split("-"))
    M = P.win_mask(w)[None, :]
    for c in cs:
        M = M & cond_mat(P, cache, c)
    t = trade_frame(P, *first_trades(P, M, f"{r.side}_{r.geom}"))
    d = t.groupby("date")["r"].sum()
    best = d.idxmax()
    tb = t[t.date != best]
    cap = t.sort_values(["date", "tod", "symbol"]).groupby("date").head(3)
    noapr = t[pd.to_datetime(t.date).dt.strftime("%Y-%m") != "2025-04"]
    rec = {"idx": r.Index, "conds": r.conds, "side": r.side, "geom": r.geom, "window": r.window,
           "quality_pass": r.quality_pass, "n": len(t), "sessions": t.date.nunique(), "per_day": r.per_day,
           "tr_exp": r.tr_exp, "tr_t": r.tr_t, "va_exp": r.va_exp, "va_t": r.va_t, "wf": r.wf_share,
           "best_day": str(best), "best_day_share": float(d.max() / t.r.sum()) if t.r.sum() > 0 else np.nan}
    for sp in ("train", "valid"):
        x = summ(tb[tb.split == sp]); rec.update({f"xb_{sp}_{k}": v for k, v in x.items()})
        rec[f"dayw_t_{sp}"] = tday(t[t.split == sp])
        x = summ(cap[cap.split == sp]); rec.update({f"cap3_{sp}_{k}": v for k, v in x.items()})
    x = summ(noapr[noapr.split == "train"]); rec.update({f"noapr_train_{k}": v for k, v in x.items()})
    tv = t[t.split == "valid"]
    rv = gates.regime_split(tv[["date", "r"]], P.regimes_df, min_n=1)
    rec["va_up"], rec["va_down"] = rv["up"].get("exp_r"), rv["down"].get("exp_r")
    rb = gates.regime_split(tb[["date", "r"]], P.regimes_df)
    rec["xb_up"], rec["xb_down"] = rb["up"].get("exp_r"), rb["down"].get("exp_r")
    mo = t.groupby(pd.to_datetime(t.date).dt.strftime("%Y-%m"))["r"].mean()
    rec["months_pos_share"] = float((mo > 0).mean())
    rows.append(rec)
X = pd.DataFrame(rows)
X["robust"] = ((X.n >= 200) & (X.xb_train_exp > 0) & (X.xb_valid_exp > 0) & (X.xb_up > 0) & (X.xb_down > 0)
               & (X.cap3_train_exp > 0) & (X.cap3_valid_exp > 0) & (X.best_day_share < 0.25) & (X.noapr_train_exp > 0)
               & (X.wf >= 0.6))
X.sort_values("xb_train_t", ascending=False).to_csv(HERE / "robust.csv", index=False, float_format="%.4g")
print("near-miss unique", len(X), "robust", int(X.robust.sum()))
print("best day counts", X.best_day.value_counts().head(5).to_dict())
pd.set_option("display.width", 300)
pd.set_option("display.max_colwidth", 110)
print(X[X.robust | X.quality_pass].sort_values("xb_train_t", ascending=False)[
    ["conds", "side", "geom", "window", "quality_pass", "n", "per_day", "best_day_share", "xb_train_exp", "xb_train_t",
     "xb_valid_exp", "xb_valid_t", "dayw_t_train", "dayw_t_valid", "cap3_valid_exp", "noapr_train_exp", "va_up", "va_down",
     "wf"]].head(40).to_string())
