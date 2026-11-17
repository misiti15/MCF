"""Live journals: L3-gap-slope-fromopen-FD in Primary (10-21..11-17) and On Deck (10-13..10-29); live fills + post-latch
what-ifs (latch_review_1117 loader, lot cap, cost haircut). Setup-only latch replay at each level / time rule."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt_l3b/research/latch_review_1117")
import analysis as A
import load4 as L
ST = "L3-gap-slope-fromopen-FD"
live, wi, sig = A.load("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/latch/j")
live = live[live.strategy == ST]; wi = wi[wi.strategy == ST]
wi = A.lot_cap(live, wi); wi = wi[wi.taken_cap]
cols = ["acct", "date", "symbol", "side", "et", "xt", "exit_reason", "rr", "rc"]
T = pd.concat([live.assign(src="live")[cols + ["src"]], wi.assign(src="whatif")[cols + ["src"]]], ignore_index=True)
T = T[T.acct.isin(["Primary", "On Deck"])].reset_index(drop=True)
T["em"] = T.et.dt.hour * 60 + T.et.dt.minute
T["tod"] = T.et.dt.hour * 100 + T.et.dt.minute
LAG = A.LAG


def replay(T, limit):
    """limit: number, None, or f(date, em) -> number/None. Running LOW of realized R after costs (latched)."""
    taken = pd.Series(False, index=T.index)
    for (acct, day), d in T.groupby(["acct", "date"]):
        real, low, ev = 0.0, 0.0, []
        d = d.sort_values("et")
        exits = []          # (xt+lag, rc) of taken trades
        for i, r in d.iterrows():
            # realized up to this entry
            real = sum(x for (t, x) in exits if t <= r.et)
            # low-water: min over the running sums at each exit time <= entry
            seq = sorted([(t, x) for (t, x) in exits if t <= r.et])
            run, low = 0.0, 0.0
            for t, x in seq:
                run += x; low = min(low, run)
            lim = limit(day, r.em) if callable(limit) else limit
            if lim is not None and low <= lim + 1e-9:
                continue
            taken[i] = True
            exits.append((r.xt + LAG, r.rc))
    return taken


def stats(x, by="date"):
    d = x.groupby(["acct", by]).rc.sum() if by == "date" else None
    d = x.groupby("date").rc.sum()
    tot = d.sum(); b = d.max() if len(d) else 0
    n_b = (x.date == d.idxmax()).sum() if len(d) else 0
    w = x.rc[x.rc > 0]; l = x.rc[x.rc <= 0]
    return dict(trades=len(x), live_fills=int((x.src == "live").sum()), whatifs=int((x.src == "whatif").sum()), total=tot,
                avg=x.rc.mean(), total_wo_best=tot - b, avg_wo_best=(tot - b) / max(1, len(x) - n_b), best_day=b,
                best_share=b / tot if tot > 0 else np.nan, worst_day=d.min(), green_days=int((d > 0).sum()), days=len(d),
                wl=w.mean() / -l.mean() if len(l) else np.nan, pf=w.sum() / -l.sum() if l.sum() < 0 else np.nan)
