"""Tables for NOTES section 2: turn statistics, baselines, diagnosis (lift) and trade results.
Writes results_summary.csv (top lines) and prints markdown. Educational only - not financial advice."""
import numpy as np
import pandas as pd

from common import DATA, HERE, KS
from score import baselines

pd.set_option("display.width", 250)


def md(df, floatfmt=3):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append("" if not np.isfinite(v) else f"{v:+.{floatfmt}f}" if c.endswith("exp") or c.startswith("exp") else f"{v:.{floatfmt}f}" if abs(v) < 1000 else f"{v:,.0f}")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def turn_tables():
    t = np.load(DATA / "turnstats.npz")
    hb = t["hb"]
    mids = (hb[:-1] + hb[1:]) / 2
    sd = float(t["stock_days"])
    nses = (t["stock_days_by_date"] > 0).sum()
    rows = []
    for k in KS:
        for side in ("long", "short"):
            for w in ("all", "win"):
                n = float(t[f"n_{side}_{k}_{w}"])
                h = t[f"hist_{side}_{k}_{w}"]
                cdf = np.cumsum(h) / max(h.sum(), 1)
                q = lambda p: float(mids[np.searchsorted(cdf, p)])
                rows.append({"k (R)": k, "side": side, "window": "09:35-15:55" if w == "all" else "09:50-15:00",
                             "turns": int(n), "per stock-day": n / sd, "per session (population)": n / nses,
                             "size median R": q(.5), "size p75": q(.75), "size p90": q(.9),
                             "SPY same-side +-10 min": float(t[f"coin_{side}_{k}_{w}"]) / n,
                             "chance": float(t[f"chance_{side}_{k}_{w}"]) / n})
    return pd.DataFrame(rows), sd, nses


if __name__ == "__main__":
    tt, sd, nses = turn_tables()
    print(f"stock-days {sd:,.0f}, sessions {nses}")
    print(md(tt))
    print()
    print(md(baselines("A")[["side", "baseline", "line", "n", "exp", "t", "up_exp", "down_exp", "train_exp", "valid_exp"]]))
