"""Owner request 2026-10-08: 'obvious' metrics right before big moves, layered into new setups (train/valid only).
Indicators on 5-minute bars (lab frame): RSI(14), RSI(5), 5-min SMA20/SMA50 crosses, VWAP reclaim/loss, volume surge,
move from the open. First qualifying bar per symbol-day, lab outcomes (R = 0.25 x daily ATR), production-cost haircut
applied. Educational only - not financial advice."""
import itertools

import numpy as np
import pandas as pd

from mcf.research.setup_lab import load

OUT = ["r_long_t1s1", "r_short_t1s1", "r_long_t05s1", "r_short_t05s1", "r_long_t1s05", "r_short_t1s05"]
COLS = ["symbol", "date", "tod", "rsi", "rsi5", "sma20_dist_pct", "sma50_dist_pct", "vwapDistPct", "volumeRatio", "fromOpen",
        "close", "atr_d"] + OUT


def prep(split):
    df = load(split, columns=COLS).sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    key = (df.symbol.astype(str) + "|" + df.date.astype(str)).to_numpy()
    sid = pd.factorize(key)[0]
    first = np.r_[True, sid[1:] != sid[:-1]]
    for c in ("sma20_dist_pct", "sma50_dist_pct", "vwapDistPct", "rsi"):
        p = np.r_[np.nan, df[c].to_numpy()[:-1]]
        p[first] = np.nan
        df[c + "_prev"] = p
    R = 0.25 * df.atr_d.to_numpy()
    hair = (2 * df.close.to_numpy() * 1e-4 + 0.02) / R   # ~1 bps per side + 2c stop extra vs the lab's flat 1c
    return df, sid, df.date.astype(str).to_numpy(), hair


def conds(df):
    c = {"rsi>=60": df.rsi >= 60, "rsi>=70": df.rsi >= 70, "rsi<=30": df.rsi <= 30, "rsi<=20": df.rsi <= 20,
         "rsi_x60up": (df.rsi >= 60) & (df.rsi_prev < 60), "rsi_x40dn": (df.rsi <= 40) & (df.rsi_prev > 40),
         "rsi5>=80": df.rsi5 >= 80, "rsi5<=20": df.rsi5 <= 20,
         "x_sma20_up": (df.sma20_dist_pct > 0) & (df.sma20_dist_pct_prev <= 0),
         "x_sma20_dn": (df.sma20_dist_pct < 0) & (df.sma20_dist_pct_prev >= 0),
         "x_sma50_up": (df.sma50_dist_pct > 0) & (df.sma50_dist_pct_prev <= 0),
         "x_sma50_dn": (df.sma50_dist_pct < 0) & (df.sma50_dist_pct_prev >= 0),
         "above_sma50": df.sma50_dist_pct > 0, "below_sma50": df.sma50_dist_pct < 0,
         "vwap_reclaim": (df.vwapDistPct > 0) & (df.vwapDistPct_prev <= 0),
         "vwap_loss": (df.vwapDistPct < 0) & (df.vwapDistPct_prev >= 0),
         "vol>=2x": df.volumeRatio >= 2, "vol>=3x": df.volumeRatio >= 3,
         "up_from_open>2%": df.fromOpen > 2, "down_from_open>2%": df.fromOpen < -2}
    return {k: v.to_numpy() for k, v in c.items()}


def score(m, sid, dates, df, hair):
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return None
    _, f = np.unique(sid[idx], return_index=True)
    idx = idx[f]
    res = {}
    for o in OUT:
        r = df[o].to_numpy()[idx]
        ok = np.isfinite(r)
        r = r[ok] - hair[idx][ok]
        if len(r) < 2:
            continue
        d = pd.Series(r).groupby(dates[idx][ok]).agg(["sum", "size"])
        mu = r.mean()
        se = np.sqrt(((d["sum"] - d["size"] * mu) ** 2).sum()) / len(r)
        res[o] = (len(r), mu, mu / se if se > 0 else 0.0, (d["sum"] > 0).mean())
    return res


if __name__ == "__main__":
    tr, sid_t, d_t, h_t = prep("train")
    va, sid_v, d_v, h_v = prep("valid")
    ct, cv = conds(tr), conds(va)
    trig = ["rsi_x60up", "rsi_x40dn", "x_sma20_up", "x_sma20_dn", "x_sma50_up", "x_sma50_dn", "vwap_reclaim", "vwap_loss"]
    state = [k for k in ct if k not in trig]
    combos = ([(a,) for a in trig] + [(a, b) for a in trig for b in state]
              + [(a, b, c) for a in trig for b, c in itertools.combinations(state, 2)])
    W = {"am": (950, 1130), "pm": (1130, 1500), "all": (950, 1500)}
    rows, n = [], 0
    tt, tv = tr.tod.to_numpy(), va.tod.to_numpy()
    for combo in combos:
        for w, (lo, hi) in W.items():
            mt = np.logical_and.reduce([ct[c] for c in combo]) & (tt >= lo) & (tt <= hi)
            if mt.sum() < 60:
                continue
            mv = np.logical_and.reduce([cv[c] for c in combo]) & (tv >= lo) & (tv <= hi)
            a, b = score(mt, sid_t, d_t, tr, h_t), score(mv, sid_v, d_v, va, h_v)
            if not a or not b:
                continue
            for o in OUT:
                n += 1
                if o in a and o in b:
                    rows.append({"layers": "+".join(combo), "window": w, "outcome": o, "tr_n": a[o][0], "tr_exp": a[o][1],
                                 "tr_t": a[o][2], "va_n": b[o][0], "va_exp": b[o][1], "va_t": b[o][2], "va_green": b[o][3]})
    r = pd.DataFrame(rows)
    r.to_csv("research/owner1008/scan.csv", index=False)
    print("configurations scored:", n)
    p = r[(r.tr_n >= 60) & (r.va_n >= 30) & (r.tr_exp > 0) & (r.va_exp > 0)].copy()
    p["score"] = np.minimum(p.tr_t, p.va_t)
    print(len(p), "positive on both splits after the production haircut")
    print(p.sort_values("score", ascending=False).head(30).to_string())
