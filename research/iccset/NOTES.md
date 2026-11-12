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

## ICCSET-2 — shrunk ICC and n_eff for verdicts (Lead lead-20261112-0300-1) — `shrink.py` -> `shrink_out.txt`, `iccset_shrunk.csv`
Empirical Bayes: se of each ICC(1) from the Fisher/Donner approximation (days, trades/day). The between-setup variance is
tau^2 = var(raw ICC) - mean(se^2) = 0.0271 - 0.0093 = 0.0179 (tau 0.134), so the differences are real, not noise. Each setup's
ICC is shrunk toward 0.19 with weight tau^2 / (tau^2 + se^2) (median weight 0.68).
- Shrunk ICC 10th / 25th / 50th / 75th / 90th pct: 0.09 / 0.12 / 0.19 / 0.24 / 0.32. n_eff / n median 0.37.
- Examples (n -> shrunk n_eff): CWT14-failbrk-pdl-p05-long 704 -> 169; CWT12-coil-k4-long 609 -> 138; RW7-FD 315 -> 89;
  MF2-FD 113 -> 39; RW5-FD 141 -> 38; RW3-FD 110 -> 33; exhaustion_short 72 -> 25.
- Setups with < 40 trades or < 8 days: use the prior 0.19 directly (their own ICC is too noisy to move it).
Use: verdict statistics (mean R, t, P(>0)) computed with n_eff_s in place of n. Equivalently, day-clustered standard errors.
The table goes to the owner with REPS3 on 11-18. Refresh it then with the extra sessions.

## ICCSET-3 — a better shrink target: setup group (`family.py` -> `family_out.txt`)
Name-prefix families explain 81% of the weighted ICC variance, but with 29 families for 54 setups that is near-saturated.
The fair test uses 5 coarse groups fixed by setup design. Those explain **40%** (Q_between 68.6 of 172.6, df 4, p < 1e-6),
and the residual between-setup variance drops from tau^2 0.018 to ~0.005.
| Group | Setups | Weighted ICC |
|---|---|---|
| GEN | 4 | 0.07 (few setups; median shrunk 0.17) |
| CWT structure (level breaks, coils, VWAP stretch, flush, gap bounce) | 18 | 0.10 |
| flow / gap-day (RW, MF, NS, L3, ST) | 22 | 0.18 |
| other (NM, LIQ) | 3 | 0.34 |
| heat / exhaustion / momentum | 7 | 0.39 |
Longs vs shorts alone explain 5% (0.12 vs 0.18).
Recommendation for the 11-18 table: shrink each setup toward its GROUP ICC (prior sd ~0.07), not the pooled 0.19.
For a new setup with few days, use its group's value. GEN's own value rests on 4 setups, so use ~0.12 (between its 0.07
and the pooled 0.19) until more Gen setups reach 40 trades / 8 days.
Why it makes sense: structure setups (level breaks, coils) fire on many unrelated names on a given day, so trades are
nearly independent. Flow / gap-day shorts and heat fades share one day-level driver (a gap-down or hot tape), so a
day's trades rise and fall together.
