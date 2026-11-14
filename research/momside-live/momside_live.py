"""MOMSIDE-LIVE scorer (frozen with PLAN.md). Usage (MCF checkout):
  python ../guild/research/momside-live/momside_live.py --selftest       (synthetic data only)
  python ../guild/research/momside-live/momside_live.py <journal dir>    (ONLY after Builder's MOMSIDE lab result)
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
def tag(side, dec):
    if np.isnan(dec): return "untagged"
    if (side > 0 and dec >= 8) or (side < 0 and dec <= 3): return "aligned"
    if (side > 0 and dec <= 3) or (side < 0 and dec >= 8): return "counter"
    return "neutral"
def score(t, draws=1000, seed=7):
    """t: columns date, strategy, r, tag. Returns pooled excess, day-t, per-setup better/worse, best-day share."""
    rng = np.random.default_rng(seed); rows = []
    for (d, s), g in t.groupby(["date", "strategy"]):
        a = g[g.tag == "aligned"].r.to_numpy(); o = g[g.tag != "aligned"].r.to_numpy()
        if len(a) == 0 or len(o) == 0: continue
        k = min(len(a), len(o)); base = np.mean([rng.choice(o, k, replace=False).mean() for _ in range(draws)])
        rows.append(dict(date=d, strategy=s, ex=a.mean() - base, n=len(a)))
    x = pd.DataFrame(rows)
    if x.empty: return None
    day = x.groupby("date").ex.mean(); tt = day.mean() / (day.std(ddof=1) / np.sqrt(len(day))) if len(day) > 2 else np.nan
    per = x.groupby("strategy").ex.agg(["mean", "size"]); per = per[per["size"] >= 5]
    pos = x.groupby("date").ex.sum(); best = pos.max() / pos.sum() if pos.sum() > 0 else np.nan
    return dict(setup_days=len(x), excess=x.ex.mean(), day_t=tt, better=int((per["mean"] > 0).sum()), worse=int((per["mean"] <= 0).sum()), best_day_share=best)
def selftest():
    rng = np.random.default_rng(1); rows = []
    for d in range(30):
        for s in range(20):
            for _ in range(8):
                dec = rng.integers(1, 11); side = rng.choice([-1, 1]); tg = tag(side, dec)
                r = rng.normal(0, 1) + (0.3 if tg == "aligned" else 0.0)
                rows.append(dict(date=d, strategy=s, r=r, tag=tg))
    planted = score(pd.DataFrame(rows))
    null = score(pd.DataFrame(rows).assign(r=lambda z: rng.normal(0, 1, len(z))))
    print("planted +0.30:", {k: round(v, 3) if isinstance(v, float) else v for k, v in planted.items()})
    print("null:        ", {k: round(v, 3) if isinstance(v, float) else v for k, v in null.items()})
    assert 0.2 < planted["excess"] < 0.4 and planted["day_t"] > 3, "planted effect not recovered"
    assert abs(null["day_t"]) < 3, "null shows an effect"
    print("selftest ok")
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest": selftest(); sys.exit()
    sys.exit("live run is gated: run only after Builder's MOMSIDE lab result is posted (PLAN.md). Not implemented past scoring "
             "until then by design: the data fetch + tagging are added in the run commit, unchanged definitions.")
