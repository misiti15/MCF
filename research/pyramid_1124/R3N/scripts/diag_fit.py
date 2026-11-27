"""FIT-only diagnostic (post-selection, information only): best days of near-miss and picked rules. Educational only."""
import json, pandas as pd, numpy as np
import search as S
rules = json.load(open("rules.json")); D = S.build(S.FIT)
for i in (48, 120, 6, 26, 221, 115, 228):
    r = rules[i]; ii = S.first_idx(D, r)
    x = pd.DataFrame({"date": D["date"][ii], "r": D[f"{r['side']}_{r['geom']}"][ii].astype(float)})
    d = x.groupby("date").r.sum().sort_values(ascending=False)
    print(i, S.rule_name(r), "n", len(x), "tot", round(d.sum(),1), "top3", [(k, round(v,1)) for k, v in d.head(3).items()], "worst", round(d.min(),1))
# all gated longs pooled: share of R on 2025-04-09
