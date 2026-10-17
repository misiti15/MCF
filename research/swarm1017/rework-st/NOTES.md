# swarm1017 / rework-st — NOTES (2026-10-17)

*Educational only — not financial advice. Research only: no config, ledger or backlog edits. These are backtests on the open
2-year history (rule 7: not live, not paper). Nothing here was scored on any locked holdout.*

## Failures first
- **No configuration clears its lineage bar.** N_study = 148,176 pre-declared (ST 106,704 / L3 41,472), plus 246 robustness
  neighbours, 50 context-filter neighbours and 5 ad-hoc day-of-week looks, for a total of **148,477**.
  - N_lineage ST ~ 227,400, so the bar is **t >= 4.97**.
  - N_lineage L3 ~ 315,800, so the bar is **t >= 5.03**.
  - Best gated day-clustered t: 4.70 (L3a + SPY > +0.5%). Its day-equal-weighted t is 2.86.
- **ST2, ST3, ST5, ST6, ST7, ST8: 0 usable variants.**
  - Their source-window parents have fewer than 150 train trades (57-124), so they fail the n screen.
  - Their full-day versions lose or are flat in train: ST2-FD -0.051, ST3 -0.016, ST5 -0.065, ST6 -0.028, ST7 -0.050,
    ST8 +0.006.
  - Gate passers by parent: ST2 1 (DOW + vwap, t 1.1), ST3 0, ST4 19 (best has plateau 0.2: an isolated point), ST5 0,
    ST6 0, ST7 0, ST8 0.
  - Restoring the source windows is the only thing that helps. Those windows were chosen on the whole open history
    (stack1009), so that is not out-of-sample evidence.
- **The L3 family is dominated by a handful of mass gap-down days.** Across the 28 de-duplicated L3 finalists, the top 3
  sessions carry 73%-163% of total R. The usual cause is 2025-04-07 and its neighbours.
  - The day-clustered t from mcf gates does not penalise a day whose mean is close to the overall mean, so it
    overstates these L3 results.
  - The concentration amendment (below) removed 4 of the 7 finalists that survived the robustness amendment.
- **Opposite side:** flipping the parent rarely helps. The one long L3 finalist that survived is Monday-only, and Tue-Fri
  are negative.
- **Exits:** only the lab geometries were scored (t1s1, t05s1, t1s05). t05s05 is in neither the frames nor
  LabStrategy.GEOMS. Scale-out (live_scale_out) and trailing stops are supported live but need 1-minute paths, which
  the frames do not hold, so they were not scored. Hold-to-close and time exits are not supported live (code needed).
- **Live week 2026-10-12..16** (paper, research/swarm1017/week; n is small, so this is not evidence):
  - L3-fromopen-FD -0.23R/41, L3-rsi5hi-FD -0.14R/22, L3-lowdist-FD -0.25R/16
  - ST1-FD -0.56R/22, ST2-FD -0.15R/63, ST4-FD -0.63R/7, ST7-FD +0.66R/7, ST8-FD -0.17R/4, ST5-FD 1 trade, ST6-FD 2 trades
  - The FD losses match the history: every FD parent is <= ~0 on train.

## Parent reproduction (repro.json; matches published numbers)
- ST1 1335-1500: n 395, +0.091R, t 2.53 (published 395 / +0.091 / 2.53). ST1-FD: -0.056 (published -0.056).
- ST2-ST8 in their source windows reproduce stack1009 exactly.
- L3a-FD -0.042, L3b-FD -0.104, L3c-FD -0.039 (refire1014: -0.042 / -0.104 / -0.039).
- The L3 parents in their 13:00-14:30 window: L3a +0.059 (t 0.60), L3b -0.008, L3c +0.045. The L3 down-regime
  expectancy is negative in that window for L3a and L3c.
- verify_core.json: the parameterised cores equal the FD modules' own masks bar for bar (11 of 11, 2025-06).

## Amendments (made after the gate run; they only remove candidates)
- **A (robust.py):**
  - core tier only (adv20 >= 5M), because L3 runs at min_adv 0 and prod_r has no extended-tier 3x slippage;
  - threshold-neighbour plateau >= 2/3, with the same filters, side, geom, window and refire;
  - halves, and the same configuration without its day-of-week filter.
- **B (concentration.py):** both of these must hold on train and valid:
  - day-equal-weighted expectancy > 0, ex-top-3-days expectancy > 0;
  - a 10-trades-per-day cap (earliest bars) with expectancy > 0.

## Funnel
- Screen (n_tr >= 150, n_va >= 50, n >= 200, exp > 0 on train and valid): 2,341.
- Single gates: regime 743, walk-forward 772, beats same-minute random 1,754, ex-best-day 1,371, Stage-A plateau 2,131.
- **All gates: 252.** By parent: L3c 91, ST1 86, L3a 30, L3b 25, ST4 19, ST2 1.
- De-duplicated (>= 60% trade overlap): 32 finalists (finalists.csv).
- Amendment A: 7 survive. Amendment B: **3 candidates**, all below the bar.
- With about 148k tries, about 7,400 configurations would pass p = 0.05 by chance.

## Candidates (modules/; train = 2024-10 + 2025-03..12, valid = 2026-01..2026-10-07; production cost; day-clustered t)
| module | parent | change | n (/day) | exp | t | train | valid | up / down | WF | excess vs random | day-eq. t | top-3 share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RST1-l3fromopen-spyup-pm-t05s1-short | L3a | + SPY > +0.5% from open, 13:35-15:00, t05s1 [live code: spy_fo] | 1662 (3.9) | +0.176 | 4.70 | +0.175 (1029) | +0.178 (633) | +0.171 / +0.322 | 0.86 | +0.189 (t 8.5) | 2.86 | 0.73 |
| RST3-st1-ordn-notmon-pm-refire-t05s1-long | ST1 | source window 13:35-15:00, skip Mondays, refire cd1 | 346 (0.81) | +0.112 | 2.97 | +0.125 (162) | +0.101 (184) | +0.140 / +0.126 | 0.86 | +0.139 (t 4.2) | 2.43 | 0.34 |
| RST2-l3fromopen-mon-rsi5dip-long-t1s1 | L3a (opposite side) | long, Monday only, RSI5 <= 30, full day | 836 (2.0) | +0.163 | 4.56 | +0.121 (514) | +0.231 (322) | +0.187 / +0.011 | 0.64 | +0.129 (t 3.3) | 1.53 | 0.78 |

Notes on the three candidates:
- **RST1** is the strongest. Its SPY-threshold neighbours (0.25 / 0.75 / 1.0) at 13:35-15:00 are all positive on train
  and valid (t 2.5-4.6), and all 4 half-years are positive. Weak points:
  - with the 10-trades-per-day cap, train is only +0.013;
  - the result depends on mass gap-down days;
  - it needs SPY fromOpen in the live lab frame (code needed). Without it, the module returns no trades (fail-safe).
- **RST3** is essentially the ST1 parent in its own window. Without the Monday skip it is n 409, +0.092, t 2.55. Its
  valid day-equal-weighted t is only 0.51. Running the windowed ST1 (with or without the Monday skip) is the honest
  reading. The FD version should not run.
- **RST2 is not recommended.** 2025-04-07 alone holds 254 of the 408 morning trades. The day-of-week filter has only a
  weekend-gap story behind it, and the rule is negative on Tue-Fri. It is written as a module only so the lead can see
  it, and is flagged as weak in its docstring.

## Live implementability
- All three are type: lab, use only bar-close features (no look-ahead), and load in LabStrategy.
- verify_modules.json: each module's own mask, run over every open month with live-style selection (min_adv, window,
  prefilter, first bar or refire_select cd1), reproduces the scan exactly:
  - RST1 1662 / +0.1764
  - RST2 836 / +0.1632
  - RST3 346 / +0.1119
- The day of week comes from `date` offline and from the live frame's DatetimeIndex.
- RST1 needs `spy_fo` (code needed).
- Offline caveat: the frames start at the 09:50 bar, so crosses at 09:50 are not seen offline.

## Files
- PLAN.md (pre-declared grid)
- stcore.py (cores) and verify_core.py
- build.py (superset; scratch deleted, rebuild takes about 4.5 min)
- common.py
- scan.py (scan_all.csv.gz: all 148,176 configurations)
- gate.py (results.csv: 2,341 screened with gate columns; finalists.csv; gate_summary.json)
- robust.py (robust.json), concentration.py (concentration.json), neigh2.py (neigh2.json), repro.py (repro.json)
- gen_modules.py, modules/ (3 modules + index.json), verify_modules.py (verify_modules.json)
