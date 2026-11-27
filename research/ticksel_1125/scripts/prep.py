"""TICKSEL prep: trade lists -> R (LR8 research) + R_adj -> home-account book -> traits attached. Educational only."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel")
import tk
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/"
T = S + "ticksel/"
HOME = {"L3-gap-slope-fromopen-FD": "primary", "RW3-gapdn-rsi5pop-flowsell-short-FD": "primary",
        "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "primary", "NM-ETF-late-dip-di-long": "primary",
        "L3-gap-slope-lowdist-FD": "testing", "L3-gap-slope-rsi5hi-FD": "testing",
        "RW7-gapdn-bounce-early-short-FD": "testingf", "RW6-ns2-up3-short-FD": "livelab",
        "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short": "testingd"}
FAM = {"L3-gap-slope-fromopen-FD": "L3", "L3-gap-slope-lowdist-FD": "L3", "L3-gap-slope-rsi5hi-FD": "L3",
       "RW3-gapdn-rsi5pop-flowsell-short-FD": "GDS", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "GDS",
       "RW7-gapdn-bounce-early-short-FD": "GDS", "RW6-ns2-up3-short-FD": "RW6", "NM-ETF-late-dip-di-long": "NMETF",
       "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short": "GEN06"}
REUSE = ["L3-gap-slope-fromopen-FD", "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short"]

def load(which):
    a = pd.read_parquet(T + f"work/trades_{which}.parquet")
    b = pd.read_parquet(S + f"pyramid/S/work/trades_{which}.parquet")
    b = b[b.setup.str.split("|").str[0].isin(REUSE)]
    t = pd.concat([a, b], ignore_index=True)
    tk.no_locked(t.date.unique())
    return t

def costed(t):
    t = tk.add_r(t)
    cost = (t.r_gross - t.r)
    t["cost_r"] = cost
    t["r_adj"] = t.r + np.where(t.entry < 20, 0.5 * cost, 0.0)
    return t

def booked(t, etb):
    out = []
    for s, g in t.groupby("setup"):
        base = s.split("|")[0]
        b = tk.book(g, tk.BOOK[HOME[base]], etb)
        out.append(b)
    return pd.concat(out, ignore_index=True)

def attach(t, which):
    tr = pd.read_parquet(T + f"tr_{'t1' if which == 't1' else 't2'}.parquet")
    st = pd.read_parquet(T + "static.parquet")
    t = t.merge(tr.drop(columns=["gap"]), on=["symbol", "date"], how="left").merge(st, on="symbol", how="left")
    t["base"] = t.setup.str.split("|").str[0]
    t["rnd"] = t.setup.str.contains(r"\|RND")
    t["fam"] = t.base.map(FAM)
    return t

if __name__ == "__main__":
    etb = pd.read_parquet(T + "etb_rate.parquet").rate
    for w in sys.argv[1:] or ("t1", "t2"):
        t = costed(load(w))
        raw = attach(t[~t.setup.str.contains(r"\|RND")].copy(), w)
        raw["half"] = tk.half(raw.date) if w == "t1" else "t2"
        raw.to_parquet(T + f"raw_{w}.parquet")
        b = booked(t, etb)
        b = attach(b, w)
        b["half"] = tk.half(b.date) if w == "t1" else "t2"
        b.to_parquet(T + f"bk_{w}.parquet")
        print(w, b.groupby(["half", "setup"]).size().unstack(0).fillna(0).astype(int).to_string())
