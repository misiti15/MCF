"""PYRAMID L2 scoring. python score.py fit | check. Educational only - not financial advice."""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
import l2
B = l2.B
W = l2.W
CANDS = {"C1": ["C1a", "C1b", "C1c"], "C2": ["C2a", "C2b", "C2c", "C2d"], "C3": ["C3a", "C3b", "C3c", "C3d"], "C4": ["C4a"]}
TEST = dict(cap=100, latch=None, cf=0.15, symcap=3)
etb = pd.read_parquet(Path(__file__).parent / "etb_rate.parquet").rate


def load():
    T1 = B.add_r(pd.read_parquet(W / "trades_t1.parquet")); T1["half"] = B.half(T1.date)
    T2 = B.add_r(pd.read_parquet(W / "trades_t2.parquet")) if (W / "trades_t2.parquet").exists() else None
    return T1, T2


def sessions():
    spy1 = B.spy_t1(); d = pd.Series(spy1.index); d = d[d <= "2026-11-04"]
    h = B.half(d)
    spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet"); spy2.index = spy2.index.astype(str)
    spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
    return spy1, {"fit": list(d[h == "fit"]), "check": list(d[h == "check"])}, spy2


def booked(T, name, rules=TEST):
    return B.book(T[T.setup == name], rules, etb)


def st(t, days, spy):
    o = B.stats(t, len(days), spy)
    if len(t):
        w = t[t.r > 0].r.mean(); l = -t[t.r <= 0].r.mean()
        o["be_win"] = round(float(l / (w + l)), 3) if w == w and l == l else None
        crash = t.date.between("2025-04-03", "2025-04-09")
        o["avg_r_wo_0403_0409"] = round(float(t[~crash].r.mean()), 4) if (~crash).any() else None
    return o


if __name__ == "__main__":
    T1, T2 = load()
    spy1, D, spy2 = sessions()
    if sys.argv[1] == "fit":
        out, sel = {}, {}
        for c, cfgs in CANDS.items():
            best = None
            for k in cfgs + (["C4bench"] if c == "C4" else []):
                b = booked(T1, k); f = st(b[b.half == "fit"], D["fit"], spy1)
                out[k] = f
                print(k, {x: f.get(x) for x in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "best_day_share", "t_day_clustered", "win", "be_win", "avg_r_wo_0403_0409")})
                if k == "C4bench":
                    continue
                if f["trades"] >= 60 and (best is None or f["avg_r_wo_best_day"] > out[best]["avg_r_wo_best_day"]):
                    best = k
            sel[c] = best
        sel["frozen_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        json.dump({"selection": sel, "fit": out}, open(Path(__file__).parent / "fitsel.json", "w"), indent=1, default=float)
        print("SELECTED", sel)
