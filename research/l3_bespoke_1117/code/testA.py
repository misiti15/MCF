"""Test A (engine): latch level grid -1.00..-4.00 step 0.25 + none, replay and 2-year (+ splits)."""
import numpy as np, pandas as pd, pickle
import load4 as L, sim4
LEVELS = [-1.0 - 0.25 * i for i in range(13)] + [None]
name = lambda x: "none" if x is None else f"{x:.2f}"
rows, keep = [], {}
for test, (c, g) in L.TESTS.items():
    raw = sim4.trades(c, sim4.P, g)
    keep[(test, "raw")] = raw
    days = L.DAYS[test]
    books = {name(x): sim4.book(raw, sim4.P, x) for x in LEVELS}
    keep.update({(test, k): b for k, b in books.items()})
    base = books["-2.00"]; nolatch = books["none"]
    prev = None
    for x in LEVELS:
        k = name(x); b = books[k]
        key = lambda t: set(zip(t.date, t.symbol, t.em))
        bd = b.groupby("date").apply(lambda t: frozenset(zip(t.symbol, t.em)))
        nd = nolatch.groupby("date").apply(lambda t: frozenset(zip(t.symbol, t.em)))
        latch_days = int(sum(bd.get(d, frozenset()) != nd.get(d, frozenset()) for d in nd.index))
        diff_prev = None
        if prev is not None:
            pd_ = books[prev].groupby("date").apply(lambda t: frozenset(zip(t.symbol, t.em)))
            diff_prev = int(sum(bd.get(d, frozenset()) != pd_.get(d, frozenset()) for d in set(bd.index) | set(pd_.index)))
        tt, dr = sim4.paired_t(base, b, days)
        segs = [("ALL", b, days)]
        if test == "2y":
            for sp in ("TRAIN", "VALID", "FWD"):
                segs.append((sp, b[b.date.map(L.split) == sp], [d for d in days if L.split(d) == sp]))
        for seg, bb, dd in segs:
            r = dict(test=test, seg=seg, level=k, **sim4.stats(bb, dd), latch_days=latch_days if seg == "ALL" else np.nan,
                     days_differ_vs_next_tighter=diff_prev if seg == "ALL" else np.nan)
            if seg == "ALL":
                r["t_vs_m2"], r["dR_vs_m2"] = tt, dr
            else:
                bs = base[base.date.map(L.split) == seg]
                r["t_vs_m2"], r["dR_vs_m2"] = sim4.paired_t(bs, bb, dd)
            rows.append(r)
        prev = k
    st = raw[raw.kind == "stop"].r
    print(test, "stop-exit R after costs: median %.3f, p10 %.3f, p90 %.3f, n %d" % (st.median(), st.quantile(.1), st.quantile(.9), len(st)))
df = pd.DataFrame(rows)
df.to_csv("A_engine.csv", index=False, float_format="%.4f")
pd.to_pickle(keep, "A_books.pkl")
pd.set_option("display.width", 250)
print(df[["test", "seg", "level", "trades", "avg", "total", "total_wo_best", "avg_wo_best", "best_share", "worst_day", "latch_days", "days_differ_vs_next_tighter", "t_vs_m2", "dR_vs_m2"]].round(3).to_string())
