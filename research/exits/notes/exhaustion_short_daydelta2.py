"""Day-clustered paired delta vs baseline for all finalists, with and without 2026-07-29. Educational only — not financial advice."""
import numpy as np
from research.exits import harness as H
from research.exits.notes.exhaustion_short_daydelta import per_trade
from research.exits.notes.exhaustion_short_valid import F
if __name__ == "__main__":
    sigs = H.load()
    for split in ("train", "valid"):
        b = per_trade(sigs, {}, split); bd = b.groupby("date").r.sum(); n = len(b)
        for v in F:
            dd = per_trade(sigs, v, split).groupby("date").r.sum().reindex(bd.index, fill_value=0) - bd
            t = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd)))
            ex = dd.drop("2026-07-29", errors="ignore"); nex = n - int((b.date == "2026-07-29").sum())
            print(split, v, "delta/trade", round(dd.sum() / n, 4), "day-clustered t", round(t, 2),
                  "ex 07-29 delta/trade", round(ex.sum() / nex, 4), "t", round(ex.mean() / (ex.std(ddof=1) / np.sqrt(len(ex))), 2),
                  "days +/-", int((dd > 0).sum()), int((dd < 0).sum()))
