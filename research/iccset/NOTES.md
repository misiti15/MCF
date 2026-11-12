# ICCSET — same-day correlation per setup, and what a record is really worth (descriptive, 0 configs)
Educational only — not financial advice. Builds on Observer's pooled ICC ~0.19 (setup-day is the unit). Source: live paper trades
10-20..11-11 (7 journals), net R clipped to [-3, 6]; 54 setups with >= 40 trades on >= 8 days. `iccset.py` -> `iccset_out.txt`, `iccset_setups.csv`.

- Median ICC 0.196 (matches Observer). Spread is wide: 10th / 25th / 75th / 90th pct 0.07 / 0.10 / 0.28 / 0.45.
  Null (R shuffled across days within setup): median -0.005, 90th pct +0.087. So the low end is near zero day-clustering, and
  the high end is real.
- n_eff = n / (1 + (m - 1) ICC): median 0.35 of the raw trade count.
- High-ICC records are worth ~2 independent trades a day: RW3-gapdn-rsi5pop-flowsell-short-FD 110 trades -> n_eff 26
  (ICC 0.54), RW5 141 -> 31 (0.48), CWT09-g5 107 -> 30 (0.36), MF2-FD 113 -> 34 (0.36). These are the live 'survivors' of WHATWORKS.
  Their records are thinner than their trade counts suggest, which fits their 2-year lab results being negative.
- Low-ICC records carry much more per trade: CWT14-failbrk-pdl-p05-long 704 -> 180 (ICC 0.07), CWT13-vwapstretch-z05-long 250 -> 121,
  CWT14-pdh-p10-lowvol-short 175 -> 106.
- ICC is not market beta (corr with |beta| -0.01). It is the setup's own day factor (e.g. gap-down mornings cluster). Shorts run higher
  (median 0.21 vs longs 0.14). Busier setups have lower ICC (corr with trades/day -0.33).
- Caveat: with 8-17 days per setup, each ICC estimate is noisy (se roughly 0.08-0.12). Use a family or shrunk ICC, not the raw value.

For the reps / verdict work (Observer item 3): a fixed '20 sessions' or 'n trades' bar treats unequal records as equal.
Verdict stats should use each setup's n_eff (shrunk ICC), or day-level statistics, which are robust to ICC by construction.
High-ICC setups need about as many DAYS as trades/2.4 to match a low-ICC setup's evidence. The setup-day currency already
handles this. The new point is that the per-trade discount ranges from ~1x to ~4x by setup.
