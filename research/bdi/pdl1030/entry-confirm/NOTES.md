Educational only — not financial advice.

# pdl1030 / entry-confirm — results (TRAIN + VALID only)

- **Configs scored: 19.** 18 were pre-declared in PLAN.md. C19 was added in a disclosed addendum after the first 18 were scored, so it is a post-hoc pick.
- **Lineage N** = 121,459 + 3 x 19 = 121,516. **BAR90:** t >= 4.355.
- **Data:** HOLD months and the locked block were never loaded (the scripts assert this).

**Parent parity passes.** p05 matches swarm15 exactly:
- n 53,326; TRAIN+VALID -0.0677R
- TRAIN -0.0677 / VALID -0.0675
- The generalized simulator `sim2`, given the parent's entries, reproduces top5_1028 `sim` exactly (asserted every month).

**Verdict: nothing passes.** No config has avg R > 0 on TRAIN or VALID, and no config clears 54% positive months.

Full table: results.csv (from report_ec.py). Trades/session use 348 sessions.

| id | rule | /sess | TRAIN | VALID | t TV | months+ | up / down |
|---|---|---|---|---|---|---|---|
| P | parent p05 | 153.2 | -0.068 | -0.068 | -9.5 | 6% | +0.014 / -0.146 |
| C01 | hold1 | 125.7 | -0.071 | -0.057 | -9.1 | 6% | |
| C02 | hold2 | 110.7 | -0.078 | -0.058 | -9.2 | 12% | |
| C03 | hold3 | 100.9 | -0.068 | -0.061 | -8.9 | 6% | |
| C04 | hold6 + no new low | 84.1 | -0.075 | -0.061 | -8.2 | 0% | |
| C05 | hold2, lows stay >= PDL | 78.3 | -0.073 | -0.057 | -8.3 | 18% | |
| C06 | follow-through above the reclaim-bar high | 98.9 | -0.077 | -0.064 | -9.9 | 6% | |
| C07 | retest PDL and hold | 110.3 | -0.074 | -0.059 | -9.6 | 6% | |
| C08 | limit at PDL + 0.02 ATR | 119.3 | -0.126 | -0.115 | -14.9 | 0% | |
| C09 | limit at the midpoint | 122.6 | -0.129 | -0.112 | -14.7 | 0% | |
| C10 | limit at close - 0.25R | 89.6 | -0.122 | -0.096 | -12.4 | 0% | |
| C11 | midpoint limit, else market | 153.0 | -0.120 | -0.104 | -15.2 | 0% | |
| C12 | hold2 + SPY not lower | 75.5 | -0.071 | -0.070 | -7.9 | 12% | |
| C13 | hold1 + SPY not lower | 84.8 | -0.054 | -0.058 | -6.8 | 12% | +0.016 / -0.130 |
| C14 | skip reclaims > 0.15 ATR above PDL | 147.0 | -0.070 | -0.068 | -9.9 | 6% | |
| C15 | C04 + entry cost <= 5% R | 63.6 | -0.033 | -0.033 | -3.8 | 12% | |
| C16 | C12 + cost <= 5% | 55.5 | -0.031 | -0.042 | -3.7 | 29% | |
| C17 | C08 + cost <= 5% | 90.4 | -0.079 | -0.082 | -9.8 | 0% | |
| C18 | C02 + cost <= 5% | 81.3 | -0.035 | -0.031 | -4.2 | 29% | |
| C19 | C13 + cost <= 5% (post hoc) | 62.0 | -0.016 | -0.034 | -2.5 | 18% | +0.047 / -0.096 |

## What was learned
- **Holding above PDL for k bars adds nothing** (-0.066..-0.072 vs -0.068). The re-break that kills these trades usually comes after the first 30 minutes, so a 5-30 minute hold does not screen it out.
- **Pullback limits are clearly worse** (-0.11..-0.12). This is adverse selection: the fills are the reclaims that fail straight back toward PDL. Filling closer to PDL does not help, because R stays 0.25 ATR.
- **The only small lift known at entry is the tape:** SPY not lower over the confirmation bar (C13, +0.012R vs the parent at 85 trades/session).
- **The cost floor is the larger lever, but it belongs to another family.** With the cost floor, rows reach about -0.02..-0.035 at 55-81 trades/session.
- **Down days stay strongly negative in every row.** The loss comes from market beta, not from entry timing. Entry confirmation does not fix this lineage.
- **Best curve:** C19, -0.022 TV, 62/session, t -2.5. Best pure entry-confirm row: C13, -0.056, 84.8/session.

Each condition and when it is known is listed in PLAN.md. Every condition is known at the entry bar's close, or when a limit order is placed.
Up/down = lib.regimes SPY session terciles (same as swarm15). These use SPY daily tercile cut points over the open history, the same as swarm15.
