"""One-time locked-holdout scoring of vf_lowvol_div (lead, 2026-10-06). Lineage volume_flip: look 2 -> needs t >= 1.5.
Lab outcomes (t1s1, R = 0.25 x daily ATR) restated at production costs: entry 1c + 1 bps; exit 1c + 1 bps (+2c on stops,
none on target fills). Same frames also score the live exhaustion_short mask and the same-side 13:00-15:00 window baseline.
Educational only - not financial advice."""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from research.rework.lab_families import vf_lowvol_div as V

LOCK = sys.argv[1]
COLS = ["close", "rsi5", "tod", "atr_d", "sma20_dist_pct", "vol_climax", "bear_div", "win_short_t1s1", "r_short_t1s1", "symbol", "date"]


def prod_r(df):
    R = 0.25 * df["atr_d"].to_numpy()
    px = df["close"].to_numpy()
    gross = df["r_short_t1s1"].to_numpy() + 0.02 / R            # undo the lab's flat 2c
    win = df["win_short_t1s1"].to_numpy() == 1
    stop = (~win) & (gross <= -0.999)
    cost = (0.01 + px * 1e-4) + np.where(win, 0.0, 0.01 + px * 1e-4) + np.where(stop, 0.02, 0.0)
    return gross - cost / R


def stats(df, r):
    d = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "r": r})
    if not len(d):
        return {"n": 0}
    g = d.groupby("date")["r"].agg(["sum", "size"])
    mu = d.r.mean()
    se = np.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(d)
    best = g["sum"].idxmax()
    return {"n": len(d), "days": len(g), "win_rate": round(float((d.r > 0).mean()), 3), "exp_r": round(float(mu), 4),
            "t_day_clustered": round(float(mu / se), 2) if se > 0 else None, "green_days": round(float((g["sum"] > 0).mean()), 3),
            "exp_r_ex_best_day": round(float((g["sum"].sum() - g.loc[best, "sum"]) / max(1, len(d) - g.loc[best, "size"])), 4),
            "best_day": best, "best_day_share": round(float(g["sum"].max() / g["sum"].sum()), 2) if g["sum"].sum() > 0 else None}


def first(df, m):
    x = df[m].sort_values(["symbol", "date", "tod"])
    return x.drop_duplicates(["symbol", "date"])


out = {}
for split in ("test", "holdout_q2"):
    df = pd.read_parquet(f"{LOCK}/{split}.parquet", columns=COLS)
    df = df[np.isfinite(df["r_short_t1s1"])]
    cand = first(df, V.mask(df, "base"))
    live = first(df, (df.rsi5 > 90) & (df.sma20_dist_pct > 1.0) & (df.bear_div > 0) & (df.tod >= 1300) & (df.tod <= 1500))
    win = df[(df.tod >= 1300) & (df.tod <= 1500)]
    out[split] = {"vf_lowvol_div": stats(cand, prod_r(cand)), "vf_lowvol_div_labcost": stats(cand, cand["r_short_t1s1"].to_numpy()),
                  "live_exhaustion_short_same_frame": stats(live, prod_r(live)),
                  "window_baseline_short_13_15": {"n": len(win), "exp_r": round(float(prod_r(win).mean()), 4)}}
print(json.dumps(out, indent=1, default=str))
json.dump(out, open("research/rework/holdout/vf_lowvol_div.json", "w"), indent=1, default=str)
