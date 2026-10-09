"""EXPLORATORY: is 09:35-09:45 tradeable after costs? (NOTES.md 0.6). Uses data/open (build_open.py): lab-pipeline
rows at bar closes 09:35..10:30 on the open history, adv20 >= 95M, exit t1s1 (R = 0.25 x daily ATR, by 15:55).
10 simple opening-range-free rules x decision bars 09:35 / 09:40 / 09:45 (= 30 configurations), plus the same rules'
first bar in 09:50-10:30 for reference, and the random-bar baselines. Cost multiplier 1x / 2x / 3x on every per-side
cost. Output: open_results.csv. Educational only - not financial advice.
    python research/bdi/timeofday/open_study.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
from lib import regimes  # noqa: E402
from mcf.research import gates as G  # noqa: E402

RULES = {
    "O1 gap-go long": ("long", lambda d: (d.gap > 1) & (d.fromOpen > 0)),
    "O2 gap-go short": ("short", lambda d: (d.gap < -1) & (d.fromOpen < 0)),
    "O3 gap-fail short": ("short", lambda d: (d.gap > 1) & (d.fromOpen < 0)),
    "O4 gap-fail long": ("long", lambda d: (d.gap < -1) & (d.fromOpen > 0)),
    "O5 vwap-with long": ("long", lambda d: (d.vwapDistPct > 0) & (d.fromOpen > 0)),
    "O6 vwap-with short": ("short", lambda d: (d.vwapDistPct < 0) & (d.fromOpen < 0)),
    "O7 rsi5 fade short": ("short", lambda d: d.rsi5 >= 90),
    "O8 rsi5 fade long": ("long", lambda d: d.rsi5 <= 10),
    "O9 rsi5 mom long": ("long", lambda d: d.rsi5 >= 90),
    "O10 rsi5 mom short": ("short", lambda d: d.rsi5 <= 10),
    "random long": ("long", lambda d: np.isfinite(d.close)),
    "random short": ("short", lambda d: np.isfinite(d.close)),
}
BARS = {"09:35": (935, 935), "09:40": (940, 940), "09:45": (945, 945), "B1 09:50-10:30": (950, 1030)}


def prod_r_mult(lab_r, win, close, atr_d, mult: float) -> np.ndarray:
    """gates.prod_r (t1s1) with every per-side cost x mult (spread-width sensitivity at the open)."""
    R = 0.25 * np.asarray(atr_d, float)
    px = np.asarray(close, float)
    won = np.asarray(win, float) == 1
    gross = np.asarray(lab_r, float) + 2 * G.SLIP_PS / R
    stop = (~won) & (gross <= -1 + 1e-6)
    side = G.SLIP_PS + px * G.SLIP_BPS
    cost = mult * (side + np.where(won, 0.0, side) + np.where(stop, G.STOP_EXTRA, 0.0))
    return gross - cost / R


def main():
    reg = regimes()
    sessions = sorted(reg.index)
    post = [d for d in sessions if str(d) >= "2025-03-01"][:10]          # warm-up across the locked gap: dropped
    keep = set(sessions) - set(post)
    med = sessions[(len(sessions) - 1) // 2]
    x = pd.concat([pd.read_parquet(p) for p in sorted((HERE / "data/open").glob("*.parquet"))], ignore_index=True)
    x["date"] = pd.to_datetime(x["date"]).dt.date
    x = x[x["date"].isin(keep) & (x["adv20"] >= 95e6) & (x["atr_d"] > 0)]
    x = x.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    n_sess = x["date"].nunique()
    rows = []
    for rule, (side, fn) in RULES.items():
        m = np.asarray(fn(x), bool) & np.isfinite(x[f"r_{side}_t1s1"].to_numpy(float))
        for bl, (a, b) in BARS.items():
            mk = m & (x["tod"].to_numpy() >= a) & (x["tod"].to_numpy() <= b)
            idx = G.first_per_symbol_day(x["symbol"].to_numpy(), x["date"].to_numpy(), mk)
            t = x.iloc[idx]
            for mult in (1.0, 2.0, 3.0):
                r = prod_r_mult(t[f"r_{side}_t1s1"], t[f"win_{side}_t1s1"], t["close"], t["atr_d"], mult)
                tr = pd.DataFrame({"date": t["date"].to_numpy(), "r": r})
                o = G.summary(tr)
                rg = tr["date"].map(reg["regime"]).to_numpy()
                up, dn = G.summary(tr[rg == "up"]), G.summary(tr[rg == "down"])
                h1, h2 = G.summary(tr[tr["date"] <= med]), G.summary(tr[tr["date"] > med])
                rows.append({"rule": rule, "side": side, "bar": bl, "cost_mult": mult, "n": o.get("n", 0),
                             "per_day": round(o.get("n", 0) / n_sess, 2), "win_rate": o.get("win_rate"),
                             "exp_r": o.get("exp_r"), "t": o.get("t"), "ex_best_day": o.get("ex_best_day"),
                             "up_n": up.get("n", 0), "up_exp": up.get("exp_r"), "down_n": dn.get("n", 0), "down_exp": dn.get("exp_r"),
                             "h1_exp": h1.get("exp_r"), "h1_t": h1.get("t"), "h2_exp": h2.get("exp_r"), "h2_t": h2.get("t"),
                             "cost_r_mean": round(float(np.mean(t[f"r_{side}_t1s1"].to_numpy(float) + 2 * G.SLIP_PS / (0.25 * t["atr_d"].to_numpy(float)) - r)), 4) if len(t) else None})
    out = pd.DataFrame(rows)
    # excess over the same side's random bar at the same decision time and cost
    rb = out[out.rule.str.startswith("random")].set_index(["side", "bar", "cost_mult"])["exp_r"]
    out["excess_vs_random"] = [round(r.exp_r - rb.get((r.side, r.bar, r.cost_mult), np.nan), 4) if r.exp_r is not None else None
                               for r in out.itertuples()]
    out.to_csv(HERE / "open_results.csv", index=False)
    print(f"sessions {n_sess}; rows {len(x)}")
    with pd.option_context("display.width", 250, "display.max_rows", 200):
        print(out[out.cost_mult == 1][["rule", "bar", "n", "per_day", "exp_r", "t", "up_exp", "down_exp", "h1_exp", "h2_exp", "excess_vs_random"]])


if __name__ == "__main__":
    main()
