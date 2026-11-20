Educational only — not financial advice

# BEG-06 Noise-area breakout on index ETFs (SPY, QQQ; long and short): results

*Research only. No setup, exit, config, account or ledger change.*
- Configurations tried: **4**. That is the base plus 3 one-part tweaks, all pre-registered in PLAN.md before they were
  scored. The random control fits nothing.
- The locked block 2024-11-01..2025-02-28 was never read. CHECK was scored once for the base and once for the FIT pick.
- R is after LR8 costs, plus 1.2 bp borrow on shorts. Trades are booked under the testing-arena rules: cap 100, at most
  3 lots per symbol, price >= $5, ETB >= 90%, and the 0.15R stop-cost filter. This is bench10's "normal way".
- Rule-change context: the backtest applies one fixed rule set to every session. No live rule change from
  `research/ledger.jsonl` is mixed into these figures.
- Overlap: MCF already has `noise_band_momentum`, built on the same paper. This version was written independently from
  the beginner spec, and the two were not compared.

**Verdict**
- **Base: FAIL, but only just. It is not REALLY BAD.**
  - It fails on one threshold only: T1 combined avg R w/o best day is −0.0880 against a threshold of −0.0674, a miss
    of 0.0206R. The NEAR limit is 0.02R.
  - T1 combined avg R is −0.054 (t −0.86).
  - CHECK is −0.031, but its best day (2025-10-10) supplies +25R against a check total of −14R.
- **Tweak `notrail` (FIT pick; it drops the check-time trailing exit): NEAR. It is not REALLY BAD.**
  - It misses one threshold: T1 combined w/o best day is −0.0797 against −0.0674, a miss of 0.012R.
  - It passes two others by a hair: T1 combined avg R is −0.0380 (threshold −0.0383), and CHECK w/o best day is
    −0.0779 (threshold −0.0781).
  - T2 (2023-24, seen data) is positive: +0.087, t 1.15.
- **Honest reading:**
  - Before costs the entries have a real directional edge. They beat random sides on every test: the 69th-100th
    percentile for the base and the 73rd-100th for `notrail`. Random sides lose −0.07 to −0.13R.
  - With costs in (about 0.10R a trade), the edge is about zero on T1 and positive only on T2.
  - On T1 the record leans on big trend days (2025-04-09, 2025-10-10). SPY-flat days lose heavily (about −0.6 to −0.9R
    a trade), so this is a trend-day setup that pays for chop.

## Scores (booked trades, testing-arena rules)
| | trades | /session | win | avg R | gross | w/o best day | best day (R) | total R | total R/session | t (day) | worst day |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base FIT (170 s) | 265 | 1.56 | 0.34 | −0.095 | +0.011 | −0.152 | 04-09 (+14.3) | −25.2 | −0.149 | −0.99 | −9.6 |
| base CHECK (276 s) | 471 | 1.71 | 0.35 | −0.031 | +0.071 | −0.084 | 25-10-10 (+25.0) | −14.4 | −0.052 | −0.37 | −4.7 |
| base T1 combined (446 s) | 736 | 1.65 | 0.35 | **−0.054** | +0.049 | −0.088 | 25-10-10 | −39.6 | −0.089 | −0.86 | −9.6 |
| base T2 2023-24 (427 s, ref) | 714 | 1.67 | 0.40 | +0.078 | +0.185 | +0.064 | 24-09-03 (+10.2, share 0.18) | +55.8 | +0.131 | 1.40 | −4.4 |
| notrail FIT | 217 | 1.28 | 0.42 | −0.083 | +0.029 | −0.152 | 04-09 (+14.4) | −18.0 | −0.106 | −0.66 | −9.6 |
| notrail CHECK | 388 | 1.41 | 0.39 | −0.013 | +0.090 | −0.078 | 25-10-10 (+25.0) | −5.0 | −0.018 | −0.12 | −4.5 |
| notrail T1 combined | 605 | 1.36 | 0.40 | **−0.038** | +0.069 | −0.080 | 25-10-10 | −23.0 | −0.052 | −0.47 | −9.6 |
| notrail T2 (ref) | 584 | 1.37 | 0.44 | +0.087 | +0.199 | +0.069 | 24-09-03 (+10.2, share 0.20) | +50.6 | +0.118 | 1.15 | −3.8 |
| stop125 FIT (not picked) | 263 | 1.55 | 0.34 | −0.094 | −0.010 | −0.140 | | | −0.146 | −1.19 | −8.1 |
| late1030 FIT (not picked) | 238 | 1.40 | 0.34 | −0.102 | −0.000 | −0.166 | | | −0.143 | −1.02 | −7.2 |

- **One-big-day check.** On T1 the total R is negative, so best-day share is not defined. Even so, CHECK depends on one
  day.
  - 2025-10-10 (the tariff sell-off) is +25.0R. Without it, CHECK avg R falls from −0.031 to −0.084 (base) and from
    −0.013 to −0.078 (`notrail`).
  - On FIT, 2025-04-09 is +14.3R.
  - On T2 no day carries the record: the best day is 18-20% of total R.
- **By side and symbol, base.**
  - Shorts −0.298 on FIT, but −0.006 on CHECK and −0.015 on T2.
  - Longs +0.083 on FIT, −0.053 on CHECK and +0.154 on T2.
  - QQQ beats SPY in every test: FIT −0.07 vs −0.12, CHECK +0.05 vs −0.10, T2 +0.11 vs +0.05.
- **By SPY day type, base T1 combined:** up +0.159, flat −0.645, down +0.122.
- **Cost filter.** The 0.25 × ATR stop is about 29 bp of price, so the 0.15R filter removes only 3-20 signals per test.
  Costs are about 0.10-0.11R a trade.

## Random-entry control
Same entries, fills and stop distance, held to the setup's exit time; side from a fair coin; 200 seeds.

| | setup avg R | random mean | random 5-95% | setup percentile |
|---|---|---|---|---|
| base FIT | −0.095 | −0.121 | −0.209..−0.032 | 69 |
| base CHECK | −0.031 | −0.068 | −0.138..+0.010 | 76 |
| base T2 | +0.078 | −0.079 | −0.144..−0.012 | 100 |
| notrail FIT | −0.083 | −0.126 | −0.253..−0.011 | 73 |
| notrail CHECK | −0.013 | −0.081 | −0.173..+0.006 | 88 |
| notrail T2 | +0.087 | −0.086 | −0.163..−0.014 | 100 |

- On T2 the direction is clearly informative. On T1 it is better than a coin, but it is not significant on its own:
  the setup sits at the 69th-88th percentile.

## Comparison with the top-10 benchmark
Thresholds are the research/ultimate_1119/top10/PLAN.md Tier A rules, built from the home-account medians. Those
medians are negative, so meeting them means "no worse than the live winners in this engine". It does not mean
profitable.

| test / rule | threshold | base | notrail |
|---|---|---|---|
| T1 combined avg R | >= −0.0383 | −0.0538 FAIL (−0.016) | −0.0380 pass |
| T1 check avg R | >= −0.0464 | −0.0305 pass | −0.0130 pass |
| T1 combined w/o best day | >= −0.0674 | −0.0880 FAIL (−0.021) | −0.0797 FAIL (−0.012) |
| T1 check w/o best day | >= −0.0781 | −0.0840 FAIL (−0.006) | −0.0779 pass |
| T1 combined total R/session | >= −0.4862 | −0.089 pass | −0.052 pass |
| T1 check total R/session | >= −0.5218 | −0.052 pass | −0.018 pass |
| T2 avg R | >= −0.1048 | +0.078 pass | +0.087 pass |
| >= 20 trades on check / T2 | | 471 / 714 | 388 / 584 |
| **Tier** | | **FAIL** (worst miss 0.0206R, just over the 0.02 NEAR limit) | **NEAR** (one miss, 0.012R) |
| REALLY BAD | | no (t −0.86; T2 is positive) | no |

- Against the medians themselves, the results are better than the top 10's avg R:
  - T1 combined: base −0.054 and `notrail` −0.038, against the top-10 median −0.028.
  - T1 check: −0.031 and −0.013, against −0.036.
  - T2: +0.078 and +0.087, against −0.085. Only RW6 (+0.034) has a positive T2 among the top 10.
- Against the best of the top 10, NM-ETF-late-dip (+0.140 combined), these results are far behind.

## FIT diagnosis of the worst losers (diag.py)
- **Exits are the leak.** Held to 15:55 with no stops at all, the same FIT entries are worth +0.227R gross, against the
  setup's +0.011.
  - Check-time trailing exits: 119 trades at −0.175R gross. Held to 15:55 they would have made +0.080R, and 53% would
    have finished on the right side. The trail cuts trades on noise around VWAP and the band.
  - Hard stops: 63 at −1R. Held, these trades would average −0.571R, and only 29% would end on the right side. Most of
    the stops are correct.
- **Entry timing.**
  - The 10:00 check is the worst bucket (72 trades, −0.166R).
  - The first entry of a symbol-day loses (−0.184), while the second and third entries are positive.
  - The worst 15 losers are mostly 10:00 shorts in the rising 2025-07..09 market, stopped within minutes.
- **Tweaks scored on FIT:**
  - `notrail` −0.083 is the pick.
  - `stop125` −0.094 (stop x1.25): it barely moves.
  - `late1030` −0.102 (first check 10:30): worse. Skipping the 10:00 check moves the first, losing entry to a later
    check instead of avoiding it.

## Next step (if pursued; not scored here, would count as new configs)
- `notrail` on QQQ only, or with a trend-day filter. The loss sits on SPY-flat days, so an early chop filter is the
  natural one-part test. Both would need fresh pre-registration, and nothing here is fitted to them.
- Live interface caveat: MCF's engine has no check-time trailing exit (`beg06.BEG06` carries it in meta). `notrail`
  needs only a hard stop and `exit_by` 15:55, so it runs in the engine as it stands.

Files:
- `beg06.py` (module and live interface) and `smoke_test.py`;
- `run.py` (engine, imports bench10), `diag.py`, `PLAN.md`, `variants.json` and `results.json`;
- trade lists in the session scratchpad `beg06w/` (~0.9 MB).
