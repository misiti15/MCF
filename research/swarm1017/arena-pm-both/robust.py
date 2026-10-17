"""Concentration re-check of every stage-3 configuration (valid-positive, excess > 0) - rule 5 ("report without the
best day"). Added AFTER the 3 quality passes turned out to sit on 2025-04-10 (464 of 677 trades of pass #1); this is a
diagnostic on already-scored configurations, not a new search (no N added). Per configuration, on all open data:
  best-day share of P/L, exp and day-clustered t with the best day removed (train, valid), day-weighted t (every session
  one observation = its mean R), per-day cap (max 10 trades/session, first by tod then symbol) exp/t, months positive.
python research/swarm1017/arena-pm-both/robust.py <rows dir>. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search as S  # noqa: E402

from mcf.research import gates  # noqa: E402
from mcf.research.arena.combine import trades  # noqa: E402

S.ROWS = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
E = json.load(open(HERE / "stage3.json"))
names = sorted({c[0] for e in E for c in e["conds"]})
cols = ["symbol", "date", "tod"] + [f"{p}_{sd}_{g}" for p in ("r", "c") for sd in ("long", "short") for g in S.GEOMS] + names
A = S.load_rows(cols)
REG = S.REG


def tday(t):
    d = t.groupby("date")["r"].mean()
    return (d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))) if len(d) > 2 else np.nan


def summ(t):
    if len(t) < 2:
        return {"n": len(t), "exp": np.nan, "t": np.nan}
    s = gates.summary(t[["date", "r"]])
    return {"n": s["n"], "exp": s["exp_r"], "t": s["t"]}


rows = []
for e in E:
    cs = [(c[0], c[1], tuple(c[2]) if isinstance(c[2], list) else c[2]) for c in e["conds"]]
    t = trades(A, cs, e["side"], e["geom"], tuple(e["window"]))
    d = t.groupby("date")["r"].sum()
    best = d.idxmax()
    tb = t[t.date != best]
    cap = t.sort_values(["date", "tod", "symbol"]).groupby("date").head(10)
    rec = {"key": e["key"], "side": e["side"], "geom": e["geom"], "window": f"{e['window'][0]}-{e['window'][1]}",
           "branch": e["branch"], "quality_pass": e["quality_pass"], "live": e["live_supported"],
           "n": len(t), "sessions": t.date.nunique(), "per_day": e["per_day"], "best_day": str(best),
           "best_day_n": int((t.date == best).sum()), "best_day_share": d.max() / t.r.sum() if t.r.sum() > 0 else np.nan,
           "tr_exp": e["train"].get("exp_r"), "tr_t": e["train"].get("t"), "va_exp": e["valid"].get("exp_r"),
           "va_t": e["valid"].get("t"), "va_n": e["valid"].get("n"), "wf": e["walk_forward"]["share_positive"],
           "up": e["regime"].get("up", {}).get("exp_r"), "down": e["regime"].get("down", {}).get("exp_r")}
    for sp in ("train", "valid"):
        s = summ(tb[tb.split == sp])
        rec.update({f"xb_{sp}_{k}": v for k, v in s.items()})
        rec[f"dayw_t_{sp}"] = tday(t[t.split == sp])
        s = summ(cap[cap.split == sp])
        rec.update({f"cap10_{sp}_{k}": v for k, v in s.items()})
    rb = gates.regime_split(tb[["date", "r"]], S.LIBREG)
    rec["xb_up"], rec["xb_down"] = rb.get("up", {}).get("exp_r"), rb.get("down", {}).get("exp_r")
    mo = t.groupby(pd.to_datetime(t.date).dt.strftime("%Y-%m"))["r"].mean()
    rec["months_pos_share"] = float((mo > 0).mean())
    rows.append(rec)
R = pd.DataFrame(rows)
R["robust"] = ((R.n >= 200) & (R.xb_train_exp > 0) & (R.xb_valid_exp > 0) & (R.xb_up > 0) & (R.xb_down > 0)
               & (R.cap10_train_exp > 0) & (R.cap10_valid_exp > 0) & (R.best_day_share < 0.25) & (R.wf >= 0.6))
R.sort_values("xb_train_t", ascending=False).to_csv(HERE / "robust.csv", index=False, float_format="%.4g")
print("stage3", len(R), "robust", int(R.robust.sum()), "robust live", int((R.robust & R.live).sum()))
print("best_day 2025-04-10 share of configs:", float((R.best_day == "2025-04-10").mean()))
pd.set_option("display.width", 250)
print(R[R.robust].sort_values("xb_train_t", ascending=False)[["side", "branch", "geom", "window", "key", "n", "per_day",
      "best_day_share", "xb_train_exp", "xb_train_t", "xb_valid_exp", "xb_valid_t", "dayw_t_train", "cap10_train_t",
      "xb_up", "xb_down", "wf"]].head(30).to_string())
