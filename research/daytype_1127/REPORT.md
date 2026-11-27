# DAYTYPE-1127: breadth day-type as ONE index position (SPY / QQQ, 11:30 / 13:00 -> 15:55). Research only. **FAIL**

**Educational only — not financial advice.**

Pre-registered: PREREG.md (commit 42ad438410, pushed before any score). **Configs: 24.** Cumulative N ≈ 9,176 → **≈ 9,200**
(family bar sqrt(2 ln N) ≈ 4.27, reference only). Locked block 2024-11-01..2025-02-28 never read (dropped and asserted in
every script). No change to config/, setups, exits, assignments.json, decisions.json, ledger or backlog.

## In plain words
- **The idea:** the arena's big GEN records were really bets on SPY's afternoon direction spread over 30-100 stocks.
  Could we make the same bet with one SPY or QQQ position: when breadth is extreme at 11:30 or 13:00 (≥ 70% or ≤ 30%
  of 469 names above their open / VWAP), follow it to 15:55, with or without SPY's own afternoon trend agreeing?
- **Answer: no, not after costs.** All 24 configs lose money after LIVE-L costs, in **every** out-of-sample window
  (EARLY 2016-22, T2 2023-24, CHECK 2025-26): about −0.06 to −0.10R per trade, OOS t −3.4 to −12.
- **There is a small real tilt, but it is far too small to pay costs.** Before costs, breadth-above-VWAP at 11:30 points the
  right way: about +0.03R per trade (≈ +3-4 bp of index move, gross t ≈ 2.1, not concentrated: best day 7% of gross).
  It beats random days and random directions (95.6-99.6th pct). But one round trip costs ~0.10R under LIVE-L and ~0.03R
  under LR8, so even the best configs end at −0.06R (LIVE-L) and ≈ 0 (LR8, t ≤ 0.5).
- **The trend confirmation does not supply the direction** (the PREREG's "expect failure unless" condition). Trend alone
  (SPY above VWAP with a rising 60-min slope, or the reverse) is barely positive before costs (+0.004 to +0.016R) and
  clearly negative after (−0.08 to −0.10R, t −8.6 to −12). Adding it to breadth changes almost nothing.
- **Why the arena records looked good:** the stock versions win only on the rare days when SPY runs ≥ 0.5% their way
  (ARENASTARS). As one index trade, those days are too few and the average afternoon follow-through (a few bp) is
  too small to beat even ETF-tight costs at a meaningful t.
- **Optimism / salvage:** the one durable fact is a weak but real *gross* afternoon tilt from 11:30 VWAP breadth
  (both SPY and QQQ, 7 of 11 years positive gross). That is useful as **context** (e.g. a tie-breaker for which side
  of an existing afternoon setup to favour), not as a stand-alone trade. No backlog entry is proposed from a FAIL.

## Method (as pre-registered)
- Breadth rebuilt per arenastars_1127/t2ctx.py (5-min bars, typical-price VWAP from 09:30, value at bar END, so 11:30 is
  known at 11:30:00) over one fixed universe: the 469 T2-cache names, read from the T2 cache and cache_hist (same names)
  for 2022-10..2026-11-04.
- EARLY (2016-22) breadth: 15-min SIP bars (GET-only Alpaca) for a seeded 130-name sample of the same universe.
  Validated on T2 vs the 469-name 5-min version **before** EARLY was scored: correlation 0.983-0.986; same side of
  0.30 / 0.70 on 90-95% of days (early_validation.json). Survivorship disclosed (today's names back to 2016).
- Trade: market at the open of the 11:30 / 13:00 1-min bar, 1R = ATR14 of the ETF (~1.0% of price), stop 1R stop-first
  with gap-through, flat at the 15:55 open (half days: last bar − 4). One position per day.
- Costs: LIVE-L headline (bucket 100+, ≈ 0.10R round trip at a ~100 bp stop), LR8 alongside (≈ 0.03R), ETF-TIGHT
  (1 bp per side, ≈ 0.02R) reported, never used for a pass.
- Controls: 500 size-matched random-day draws (same split counts, same long/short mix, same clock time) and
  500 random-direction draws on the config's own days.
- Stress: +1-minute entry and +2 bp per side.

## All 24 configs (R per trade, LIVE-L unless stated)
Columns: n / mean per split; OOS = EARLY + T2 + CHECK; ctrl = percentile vs the random-day / random-direction control.
(nb) = pre-registered threshold neighbour of the two best-FIT configs.

| Config | EARLY | T2 | CHECK | FIT | OOS (t) | OOS LR8 | OOS gross | OOS ETF-tight | ctrl day / dir pct | Stress | Bars failed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Bopen30/70 1130 noTC SPY | 505 / -0.065 | 122 / -0.112 | 43 / -0.087 | -0.032 | 670 / **-0.075** (t -4.1) | -0.003 | +0.025 | +0.008 | 96 / 83 | -0.112 | pos_splits,t_bar,conc,ctrl_dir,stress |
| Bopen30/70 1130 noTC QQQ | 505 / -0.061 | 122 / -0.082 | 43 / -0.062 | -0.005 | 670 / **-0.065** (t -3.7) | -0.000 | +0.024 | +0.011 | 96 / 90 | -0.093 | pos_splits,t_bar,conc,ctrl_dir,stress |
| Bopen30/70 1130 TC SPY | 430 / -0.065 | 105 / -0.113 | 34 / -0.073 | -0.117 | 569 / **-0.074** (t -3.8) | -0.002 | +0.026 | +0.009 | 98 / 83 | -0.111 | pos_splits,t_bar,conc,ctrl_dir,stress |
| Bopen30/70 1130 TC QQQ | 430 / -0.060 | 105 / -0.080 | 34 / -0.045 | -0.081 | 569 / **-0.063** (t -3.4) | +0.001 | +0.026 | +0.012 | 97 / 89 | -0.093 | pos_splits,t_bar,conc,ctrl_dir,stress |
| Bopen30/70 1300 noTC SPY | 542 / -0.096 | 137 / -0.133 | 50 / -0.082 | +0.029 | 729 / **-0.102** (t -7.2) | -0.029 | -0.001 | -0.019 | 66 / 49 | -0.143 | pos_splits,t_bar,conc,ctrl_day,ctrl_dir,stress |
| Bopen30/70 1300 noTC QQQ | 542 / -0.079 | 137 / -0.104 | 50 / -0.055 | +0.033 | 729 / **-0.082** (t -6.3) | -0.017 | +0.006 | -0.007 | 76 / 71 | -0.111 | pos_splits,t_bar,conc,ctrl_day,ctrl_dir,stress |
| Bopen30/70 1300 TC SPY | 384 / -0.097 | 99 / -0.124 | 40 / -0.048 | +0.010 | 523 / **-0.098** (t -5.7) | -0.025 | +0.003 | -0.014 | 71 / 66 | -0.139 | pos_splits,t_bar,conc,ctrl_day,ctrl_dir,stress |
| Bopen30/70 1300 TC QQQ | 384 / -0.077 | 99 / -0.100 | 40 / -0.030 | +0.028 | 523 / **-0.078** (t -5.0) | -0.013 | +0.010 | -0.003 | 78 / 80 | -0.106 | pos_splits,t_bar,conc,ctrl_day,ctrl_dir,stress |
| Bvwap30/70 1130 noTC SPY | 626 / -0.062 | 158 / -0.091 | 77 / -0.056 | -0.131 | 861 / **-0.067** (t -4.2) | +0.006 | +0.034 | +0.017 | 100 / 97 | -0.107 | pos_splits,t_bar,conc,stress |
| Bvwap30/70 1130 noTC QQQ | 626 / -0.059 | 158 / -0.069 | 77 / -0.020 | -0.101 | 861 / **-0.058** (t -3.9) | +0.007 | +0.031 | +0.018 | 99 / 97 | -0.086 | pos_splits,t_bar,conc,stress |
| Bvwap30/70 1130 TC SPY | 598 / -0.064 | 150 / -0.097 | 74 / -0.060 | -0.125 | 822 / **-0.069** (t -4.2) | +0.004 | +0.032 | +0.015 | 99 / 93 | -0.109 | pos_splits,t_bar,conc,ctrl_dir,stress |
| Bvwap30/70 1130 TC QQQ | 598 / -0.060 | 150 / -0.075 | 74 / -0.021 | -0.093 | 822 / **-0.059** (t -3.9) | +0.006 | +0.029 | +0.016 | 99 / 96 | -0.088 | pos_splits,t_bar,conc,stress |
| Bvwap30/70 1300 noTC SPY | 621 / -0.076 | 175 / -0.093 | 84 / -0.061 | -0.053 | 880 / **-0.078** (t -5.8) | -0.004 | +0.024 | +0.006 | 99 / 98 | -0.119 | pos_splits,t_bar,conc,stress |
| Bvwap30/70 1300 noTC QQQ | 621 / -0.064 | 175 / -0.079 | 84 / -0.035 | -0.034 | 880 / **-0.064** (t -5.3) | +0.001 | +0.025 | +0.011 | 99 / 99 | -0.094 | pos_splits,t_bar,conc,stress |
| Bvwap30/70 1300 TC SPY | 525 / -0.084 | 141 / -0.086 | 71 / -0.063 | -0.043 | 737 / **-0.082** (t -5.5) | -0.008 | +0.021 | +0.003 | 98 / 92 | -0.123 | pos_splits,t_bar,conc,ctrl_dir,stress |
| Bvwap30/70 1300 TC QQQ | 525 / -0.072 | 141 / -0.075 | 71 / -0.044 | -0.023 | 737 / **-0.070** (t -5.2) | -0.004 | +0.019 | +0.006 | 96 / 95 | -0.099 | pos_splits,t_bar,conc,stress |
| TC-only SPY 1130 | 1471 / -0.087 | 361 / -0.087 | 239 / -0.137 | -0.113 | 2071 / **-0.093** (t -9.7) | -0.016 | +0.016 | -0.004 | 93 / 94 | -0.135 | pos_splits,t_bar,conc,ctrl_day,ctrl_dir,stress |
| TC-only QQQ 1130 | 1471 / -0.075 | 361 / -0.068 | 239 / -0.097 | -0.089 | 2071 / **-0.077** (t -8.6) | -0.010 | +0.016 | +0.001 | 95 / 97 | -0.108 | pos_splits,t_bar,conc,ctrl_day,stress |
| TC-only SPY 1300 | 1276 / -0.104 | 327 / -0.123 | 192 / -0.075 | -0.044 | 1795 / **-0.105** (t -12.1) | -0.028 | +0.004 | -0.017 | 63 / 62 | -0.147 | pos_splits,t_bar,conc,ctrl_day,ctrl_dir,stress |
| TC-only QQQ 1300 | 1276 / -0.086 | 327 / -0.110 | 192 / -0.061 | -0.027 | 1795 / **-0.088** (t -10.9) | -0.021 | +0.004 | -0.010 | 66 / 67 | -0.118 | pos_splits,t_bar,conc,ctrl_day,ctrl_dir,stress |
| Bopen25/75 1300 noTC QQQ (nb) | 376 / -0.079 | 80 / -0.132 | 28 / -0.079 | +0.034 | 484 / **-0.087** (t -5.2) | -0.023 | -0.001 | -0.013 | 63 / 51 | -0.116 | pos_splits,n_ok,t_bar,conc,ctrl_day,ctrl_dir,stress |
| Bopen35/65 1300 noTC QQQ (nb) | 776 / -0.082 | 213 / -0.092 | 91 / -0.065 | -0.010 | 1080 / **-0.082** (t -7.7) | -0.017 | +0.007 | -0.006 | 82 / 76 | -0.112 | pos_splits,t_bar,conc,ctrl_day,ctrl_dir,stress |
| Bopen25/75 1300 noTC SPY (nb) | 376 / -0.094 | 80 / -0.166 | 28 / -0.099 | +0.039 | 484 / **-0.106** (t -5.8) | -0.035 | -0.007 | -0.024 | 55 / 38 | -0.145 | pos_splits,n_ok,t_bar,conc,ctrl_day,ctrl_dir,stress |
| Bopen35/65 1300 noTC SPY (nb) | 776 / -0.098 | 213 / -0.111 | 91 / -0.107 | -0.024 | 1080 / **-0.101** (t -8.7) | -0.027 | +0.002 | -0.016 | 72 / 58 | -0.143 | pos_splits,t_bar,conc,ctrl_day,ctrl_dir,stress |

- **Pass bars (PREREG):** every config fails bar 1 (negative on all three OOS splits), bar 2 (t ≥ 2.86; all t are
  negative), bar 3 (no positive total, so no best-day share; avg w/o best day negative everywhere, CHECK included)
  and bar 6 (stress: −0.09 to −0.15R). Best-day share is undefined ("None") because no config has a positive total.
- **Controls:** the 11:30 configs and all breadth-above-VWAP configs sit at the 95.6-99.6th pct of the random-day control
  and 83-99th of the random-direction control. The selection carries a little information, but the controls also pay
  LIVE-L (≈ −0.09R), so beating them does not make a config profitable.
- **Bar 7 (breadth vs trend alone, OOS, same TC days):** breadth-selected TC days beat the other TC days by
  +0.01 to +0.04R (t 0.5-2.1; best Bvwap 13:00 SPY t 2.1). That small gain is credited to breadth, not to the trend
  filter. It is still negative in absolute terms.
- **LR8:** best configs ≈ 0 (Bvwap 11:30 QQQ +0.007R, t 0.5). No LIVE-L / LR8 disagreement on the verdict.

## Descriptive (not configs)
- SPY move from T to 15:55 by breadth_open bucket (OOS days, bp, share up): at 11:30 ≤ 0.20: +9.7 bp (47% up);
  0.20-0.30: −4.7; 0.30-0.70: about 0; 0.70-0.80: +1.0; ≥ 0.80: +9.4 bp (61% up). At 13:00 similar: only the very top
  bucket (≥ 0.80, +10.3 bp, n 116) shows follow-through; the bottom bucket *bounces* (+4.9 bp). So weak-breadth
  afternoons are not reliably weak: that is why the short side (the arena G05/G07 bet) fails.
- Gross R and ETF-TIGHT for the best configs (extra_gross.json, post-hoc look, no selection made from it):
  Bvwap 11:30 noTC QQQ gross +0.031R (t 2.09), ETF-TIGHT +0.018R (t 1.19); SPY gross +0.034 (t 2.16), tight +0.017
  (t 1.05). Gross positive in 7 of 11 years; 2025 is the best year (+0.18R). Even on penny-spread costs, t ≈ 1.

## Rule changes
History replay of fixed rules (today's definitions on every day): no ledger effective date applies. No live trades exist
for this idea. The arena records it came from span 10-23..11-27 with the rule changes listed in arenastars_1127/REPORT.md
(ROT1 11-15/16, TSZ1 11-17, BRAKE-BURST 11-23, ...).

## Verdict and finalists
**FAIL** (0 / 24 pass; no LEAD: no config is positive on any OOS split after LIVE-L).
Finalists listed (every config is above). Best by OOS LIVE-L: Bvwap30/70 11:30 noTC QQQ −0.058R (t −3.9),
Bvwap30/70 11:30 TC QQQ −0.059R, Bvwap30/70 13:00 noTC QQQ −0.064R, Bopen30/70 11:30 TC QQQ −0.063R.
The arena "day-type" lesson stands as context only. Files: PREREG.md, dt_breadth.py, dt_fetch15.py, dt_sim.py, dt_score.py,
results.csv, results.json, early_validation.json, extra_gross.json, breadth_main.csv.gz, breadth_early.csv.gz.

Educational only — not financial advice.
