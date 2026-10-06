"""Time-in-trade profile for heat_fade_short (train only). Educational only — not financial advice."""
import numpy as np, pandas as pd
from research.exits import harness as H
from mcf.strategies.base import Signal
SETUP = "heat_fade_short"

def trades(sigs, variant, split):
    lo, hi = H.SPLITS[split]; out = []
    for s in sigs:
        if s["sig"]["strategy"] != SETUP or not (lo <= s["date"] <= hi): continue
        d = {k: v for k, v in s["sig"].items() if k in H._SIG_FIELDS}
        bars = H._day(s["symbol"], s["date"])
        if bars.empty or d["bar_index"] >= len(bars): continue
        ref = float(bars["close"].iloc[d["bar_index"]]); r0 = abs(ref - d["stop"])
        if "target_r" in variant:
            d["target"] = None if variant["target_r"] is None else ref + d["side"] * variant["target_r"] * r0
        tr = H.simulate(Signal(**d), bars, H._flat, H._costs)
        if tr is None: continue
        # path: unrealised R (close) at minute m after entry, ignoring exits, gross
        j = bars.index.get_loc(tr.entry_time) if tr.entry_time in bars.index else None
        cl = bars["close"].to_numpy(); risk = abs(tr.entry - tr.stop)
        path = {m: (-1 * (cl[min(j + m, len(cl) - 1)] - tr.entry) / risk) for m in (5, 15, 30, 60, 90, 120, 180, 240, 300)} if j is not None else {}
        out.append(dict(date=s["date"], r=tr.r_multiple, reason=tr.exit_reason, mfe=tr.mfe_r, mae=tr.mae_r,
                        mins=(tr.exit_time - tr.entry_time).total_seconds() / 60, **{f"p{m}": v for m, v in path.items()}))
    return pd.DataFrame(out)

if __name__ == "__main__":
    sigs = H.load()
    df = trades(sigs, {}, "train")
    print("baseline train n", len(df), "exp", df.r.mean().round(4))
    df["bucket"] = pd.cut(df.mins, [0, 15, 30, 60, 120, 240, 400])
    print(df.groupby(["bucket", "reason"]).r.agg(["count", "mean"]).dropna().round(3))
    print("winners (target) minutes quantiles", df[df.reason == "target"].mins.quantile([.25, .5, .75, .9]).round(0).tolist())
    print("losers (stop) minutes quantiles", df[df.reason == "stop"].mins.quantile([.25, .5, .75, .9]).round(0).tolist())
    print("time exits r mean", df[df.reason == "time"].r.mean().round(3))
    # MFE-by-30min conditional outcomes
    nt = trades(sigs, {"target_r": None}, "train")
    print("no-target: n", len(nt), "exp", nt.r.mean().round(4), nt.reason.value_counts().to_dict())
    print("mean unrealised R at minute m (all trades, gross, no exits):")
    print(nt[[c for c in nt.columns if c.startswith("p")]].mean().round(3).to_dict())
