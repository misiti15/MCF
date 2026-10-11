"""OF-A diagnostic (amendment A2, not a counted try): the GROSS mid-price move after the strongest flow readings
(feature >= prior-session p99 -> long, <= p1 -> short; follow direction) at 2 s latency, vs the quoted spread the trade
must cross. Answers "is there a move, and is it bigger than the cost?". -> gross.csv. Educational only."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import of_lib as L

HERE = Path(__file__).resolve().parent
FEATS = ["dlt10", "dlt60", "dlt300", "ofi10", "ofi60", "qimb10", "sweep30", "big60", "burst10", "absorb60", "cvd_div300",
         "fp_stack", "r10", "r60", "r300"]
HOR = (10, 60, 300, 900)


def main():
    acc = []
    for sym in L.SYMBOLS:
        feats, mids, sprs, stats = {}, {}, {}, []
        for d in L.DAYS:
            raw = L.load_day(sym, d)
            st = L.day_stats(raw)
            feats[d] = L.features(raw, L.ref_stats(stats if stats else [st]))[FEATS]
            mids[d] = raw.mid.to_numpy()
            sprs[d] = ((raw.ask - raw.bid) / raw.mid).to_numpy()
            stats.append(st)
        for i, d in enumerate(L.DAYS[1:], start=1):
            prior = pd.concat([feats[x].iloc[L.W0:L.W1 + 1] for x in L.DAYS[:i]])
            lm = np.log(mids[d])
            for f in FEATS:
                v = feats[d][f].to_numpy()
                hi, lo = prior[f].quantile([0.99, 0.01]).to_numpy()
                for side, m in ((1, v >= hi), (-1, v <= lo)):
                    idx = np.flatnonzero(m)
                    idx = idx[(idx >= L.W0) & (idx <= L.W1)] + 2          # 2 s latency
                    if not len(idx):
                        continue
                    row = dict(symbol=sym, date=d, feature=f, side=side, n=len(idx),
                               spread_bps=float(np.nanmean(sprs[d][idx]) * 1e4))
                    for h in HOR:
                        row[f"g{h}"] = float(np.nanmean(side * (lm[idx + h] - lm[idx])) * 1e4)
                    acc.append(row)
        print(sym, flush=True)
    r = pd.DataFrame(acc)
    out = []
    for f, g in r.groupby("feature"):
        w = g.n
        row = dict(feature=f, flagged_seconds=int(w.sum()), spread_bps=round(np.average(g.spread_bps, weights=w), 2))
        for h in HOR:
            day = g.groupby("date").apply(lambda x: np.average(x[f"g{h}"], weights=x.n))
            row[f"gross_{h}s_bps"] = round(np.average(g[f"g{h}"], weights=w), 2)
            row[f"t_{h}s"] = round(day.mean() / (day.std(ddof=1) / np.sqrt(len(day))), 2)
        out.append(row)
    o = pd.DataFrame(out)
    o.to_csv(HERE / "gross.csv", index=False)
    print(o.to_string(index=False))


if __name__ == "__main__":
    main()
