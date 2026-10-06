"""Per-day delta vs baseline (train) to check whether gains are concentrated. Educational only — not financial advice."""
import numpy as np, pandas as pd
from research.exits import harness as H
from mcf.strategies.base import Signal
SETUP = "exhaustion_short"

def per_trade(sigs, v, split):
    lo, hi = H.SPLITS[split]; rows = []
    for s in sigs:
        if s["sig"]["strategy"] != SETUP or not (lo <= s["date"] <= hi): continue
        d = {k: x for k, x in s["sig"].items() if k in H._SIG_FIELDS}
        bars = H._day(s["symbol"], s["date"])
        if bars.empty or d["bar_index"] >= len(bars): continue
        ref = d["entry_price"] if d.get("entry_price") is not None else float(bars["close"].iloc[d["bar_index"]])
        r0 = abs(ref - d["stop"])
        if "stop_mult" in v:
            d["stop"] = ref - np.sign(ref - d["stop"]) * r0 * v["stop_mult"]; r0 = abs(ref - d["stop"])
        if "target_r" in v:
            d["target"] = None if v["target_r"] is None else ref + d["side"] * v["target_r"] * r0
        for k in ("be_at_r", "trail_r", "trail_after_r", "time_stop_min", "time_stop_min_r"):
            if k in v: d[k] = v[k]
        tr = H.simulate(Signal(**d), bars, H._flat, H._costs)
        if tr is not None: rows.append((s["date"], s["symbol"], tr.r_multiple * v.get("stop_mult", 1.0)))
    return pd.DataFrame(rows, columns=["date", "sym", "r"])

if __name__ == "__main__":
    import sys
    sigs = H.load(); split = sys.argv[1] if len(sys.argv) > 1 else "train"
    b = per_trade(sigs, {}, split); bd = b.groupby("date").r.sum()
    print(split, "days", len(bd), "trades/day top5", b.groupby("date").size().sort_values().tail(5).to_dict())
    for v in ({"target_r": None}, {"target_r": 2.0}, {"target_r": 1.5}, {"target_r": 1.25}, {"stop_mult": 0.75}, {"target_r": None, "trail_r": 1.0, "trail_after_r": 1.0}):
        x = per_trade(sigs, v, split); xd = x.groupby("date").r.sum(); dd = (xd - bd).sort_values()
        n = len(b)
        print(v, "delta/trade", round(dd.sum() / n, 4), "ex top1 day", round(dd.iloc[:-1].sum() / n, 4),
              "ex top3", round(dd.iloc[:-3].sum() / n, 4), "days better", int((dd > 0).sum()), "worse", int((dd < 0).sum()),
              "top3", dd.tail(3).round(1).to_dict())
