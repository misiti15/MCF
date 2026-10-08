"""Owner request 2026-10-08: 'obvious' metrics right before big moves, layered into new setups (train/valid only).
Indicators are on 5-minute bars (the lab frame): RSI(14), RSI(5), 5-min SMA20/SMA50 crosses, VWAP reclaim/loss,
volume surge, move from the open. Educational only - not financial advice."""
import itertools, json
import numpy as np, pandas as pd
from mcf.research.setup_lab import load, evaluate

COLS = ["symbol", "date", "tod", "rsi", "rsi5", "sma20_dist_pct", "sma50_dist_pct", "vwapDistPct", "volumeRatio", "fromOpen", "close",
        "atr_d"] + [f"{a}_{s}_{g}" for a in ("r", "win") for s in ("long", "short") for g in ("t1s1", "t05s1", "t1s05")]


def feats(df):
    df = df.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    g = df.groupby(["symbol", "date"])
    for c in ("sma20_dist_pct", "sma50_dist_pct", "vwapDistPct", "rsi"):
        df[c + "_prev"] = g[c].shift(1)
    return df


def conds(df):
    c = {}
    c["rsi>=60"] = df.rsi >= 60; c["rsi>=70"] = df.rsi >= 70; c["rsi<=30"] = df.rsi <= 30; c["rsi<=20"] = df.rsi <= 20
    c["rsi_x60up"] = (df.rsi >= 60) & (df.rsi_prev < 60); c["rsi_x40dn"] = (df.rsi <= 40) & (df.rsi_prev > 40)
    c["rsi5>=80"] = df.rsi5 >= 80; c["rsi5<=20"] = df.rsi5 <= 20
    c["x_sma20_up"] = (df.sma20_dist_pct > 0) & (df.sma20_dist_pct_prev <= 0); c["x_sma20_dn"] = (df.sma20_dist_pct < 0) & (df.sma20_dist_pct_prev >= 0)
    c["x_sma50_up"] = (df.sma50_dist_pct > 0) & (df.sma50_dist_pct_prev <= 0); c["x_sma50_dn"] = (df.sma50_dist_pct < 0) & (df.sma50_dist_pct_prev >= 0)
    c["above_sma50"] = df.sma50_dist_pct > 0; c["below_sma50"] = df.sma50_dist_pct < 0
    c["vwap_reclaim"] = (df.vwapDistPct > 0) & (df.vwapDistPct_prev <= 0); c["vwap_loss"] = (df.vwapDistPct < 0) & (df.vwapDistPct_prev >= 0)
    c["vol>=2x"] = df.volumeRatio >= 2; c["vol>=3x"] = df.volumeRatio >= 3
    c["up_from_open>2%"] = df.fromOpen > 2; c["down_from_open>2%"] = df.fromOpen < -2
    return {k: v.to_numpy() for k, v in c.items()}


WINDOWS = {"am": (950, 1130), "pm": (1130, 1500), "all": (950, 1500)}
out = []
tr, va = feats(load("train", columns=COLS)), feats(load("valid", columns=COLS))
ct, cv = conds(tr), conds(va)
names = list(ct)
combos = [c for k in (2, 3) for c in itertools.combinations(names, k)]
for combo in combos:
    for wname, (lo, hi) in WINDOWS.items():
        mt = np.logical_and.reduce([ct[c] for c in combo]) & (tr.tod.to_numpy() >= lo) & (tr.tod.to_numpy() <= hi)
        if mt.sum() < 80:
            continue
        mv = np.logical_and.reduce([cv[c] for c in combo]) & (va.tod.to_numpy() >= lo) & (va.tod.to_numpy() <= hi)
        for side in ("long", "short"):
            for geom in ("t1s1", "t05s1", "t1s05"):
                a, b = evaluate(tr, mt, side, geom), evaluate(va, mv, side, geom)
                if a.get("n", 0) < 60 or b.get("n", 0) < 30:
                    continue
                out.append({"layers": "+".join(combo), "window": wname, "side": side, "geom": geom,
                            "tr_n": a["n"], "tr_exp": a["exp_r"], "tr_se": a["exp_r_se"], "tr_h1": a["exp_r_half1"], "tr_h2": a["exp_r_half2"],
                            "va_n": b["n"], "va_exp": b["exp_r"], "va_se": b["exp_r_se"], "va_green": b["green_days"]})
r = pd.DataFrame(out)
r.to_csv("research/owner1008/scan.csv", index=False)
print("configs evaluated", len(r), "of", len(combos) * 3 * 2 * 3)
# pre-declared pick: positive on both splits and both train halves; production cost ~0.03R harsher; rank by min(train, valid)
p = r[(r.tr_exp > 0.03) & (r.va_exp > 0.03) & (r.tr_h1 > 0) & (r.tr_h2 > 0)].copy()
p["score"] = p[["tr_exp", "va_exp"]].min(axis=1)
print(p.sort_values("score", ascending=False).head(25).to_string())
