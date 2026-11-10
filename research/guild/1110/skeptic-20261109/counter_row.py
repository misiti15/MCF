"""Skeptic: aligned vs counter-to-morning afternoon trades on 'held' days, raw vs ex-market, from Builder's committed
research/rcompass/rcompass_all_family.csv (trade-weighted over family-side rows). Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
F = pd.read_csv(sys.argv[1])
for look in ("F1", "F2", "F3"):
    for al in ("aligned", "counter"):
        g = F[(F.look == look) & (F.aligned == al)]; w = g.n_held_day
        print(look, al, "held n", int(w.sum()), "net", round(np.average(g.net_held.fillna(0), weights=w), 4),
              "gross", round(np.average(g.gross_held.fillna(0), weights=w), 4), "ex-market", round(np.average(g.ex_held.fillna(0), weights=w), 4))
