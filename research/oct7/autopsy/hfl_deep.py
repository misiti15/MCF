"""heat_fade_long restricted to deep drops (fromOpen <= -x% at the signal bar). Train/valid only.
Counted as 4 configurations (x = 3, 4, 5, 6). Educational only - not financial advice."""
import numpy as np
import pandas as pd

OUT = "research/oct7/autopsy/"
X = pd.read_parquet(OUT + "base_with_features.parquet")
H = X[X.setup == "heat_fade_long"].copy()
H["r0"] = H.pnl / (H.shares * H.entry * H.risk_pct / 100)
rng = np.random.default_rng(5)


def t_day(s):
    d = s.groupby("date").pnl.sum()
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 2 else np.nan


rows = []
for x in (3, 4, 5, 6):
    for split in ("train", "valid"):
        s = H[H.split == split]
        k = s[s.fromOpen <= -x]
        frac = len(k) / len(s)
        sims = np.array([s.pnl.to_numpy()[rng.random(len(s)) < frac].sum() for _ in range(4000)])
        dk = k.groupby("date").pnl.sum()
        rows.append(dict(config=f"hfl_keep_fromOpen<=-{x}", split=split, n=len(k), days=k.date.nunique(), base_n=len(s),
                         usd_total=round(k.pnl.sum(), 1), base_total=round(s.pnl.sum(), 1),
                         usd_pt=round(k.pnl.mean(), 2), base_pt=round(s.pnl.mean(), 2), r0_pt=round(k.r0.mean(), 3),
                         base_r0_pt=round(s.r0.mean(), 3), win=round((k.pnl > 0).mean(), 3), t_day_kept=round(t_day(k), 2),
                         ex_best_total=round(dk.sum() - dk.max(), 1), best_day_share=round(dk.max() / dk.sum(), 2) if dk.sum() > 0 else None,
                         p_random_subset_better=round(float((sims >= k.pnl.sum()).mean()), 3)))
D = pd.DataFrame(rows)
D.to_csv(OUT + "hfl_deep.csv", index=False)
print(D.to_string())
