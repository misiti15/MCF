from combo import *
t = trades(c, **CB["K-b C1 + X7 + G3"])
t["rel"] = t.fromOpen - t.spy_fo1
t["vw_stock"] = t.vwapDistPct
t["atrp"] = t.atr_d / t.close
F = ["poke", "reclaim", "vwapd", "rsi5", "rsi", "gap", "fromOpen", "rel", "volumeRatio", "dist_pdl_atr", "dist_pdh_atr", "sma20_dist_pct", "sma50_dist_pct", "flow3", "buyPressure", "vol_climax",
     "spy_d950", "spy_vw", "breadth", "breadth_open", "br_d950", "tod", "ccr", "atrp", "close", "adv20", "dist_hod_atr"]
for nm, rng in [("train", (TWO_Y[0], TRAIN_END)), ("valid", ("2026-01-01", TWO_Y[1]))]:
    x = period(t, rng); print("====", nm, len(x), round(x.R.mean(), 3))
    for f in F:
        try:
            q = pd.qcut(x[f], 5, duplicates="drop")
            g = x.groupby(q, observed=True).R.mean().round(3).tolist()
            edges = [round(e, 3) for e in q.cat.categories.right[:-1]]
            print(f"{f:16s} {g}  cuts {edges}")
        except Exception as e: print(f, e)
