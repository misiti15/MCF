# TOP-10 benchmark: pre-registered admission rule (ultimate_1119, owner 2026-11-19)

*Educational only — not financial advice. Written 2026-11-19 after the top-10 benchmark was scored
(BENCHMARK.md, benchmark.json) and **before any variant was scored** against it. Nothing here changes a setup, exit,
config or account. Changes that follow from it take effect 2026-11-20 at the earliest and are merged only after the
16:00 ET close.*

## Owner instructions this follows
- (2) "Go through our top 10 setups ... backtest them in our normal filter way and use that as the benchmark for any of
  the variations that you just discovered. If the new setups meet or exceed those benchmark standards, then let's add
  them to the testing arenas."
- Admission policy (~08:00 ET): a setup that is "debatable in back testing or the data is unclear ... but it was
  deviated from or derived from a promising setup" still gets exposure when slots allow; only "really, really bad" back
  tests are dropped.
- (1) The late-afternoon ETF dip gated to high cross-sectional dispersion days goes to testing as a NEW setup by owner
  decision. It is not judged by this rule. It is still scored here and reported.

## Engine: identical for the benchmark and every variant
`research/ultimate_1119/top10/bench10.py` is the "normal filter way":
- the live module mask, YAML window, `min_adv` on point-in-time ADV20, gap prefilter and refire chain (or first hit);
- entry at the decision-bar close and exits on 1-minute bars (stop first; a target fills only when traded through by
  at least $0.01; flat at 15:55);
- LR8 research-basis costs, plus 1.2 bp borrow on shorts;
- the live account book: per-setup lot cap, at most 3 lots per symbol, price at least $5, shorts must be easy to borrow
  (>= 90% of snapshots), the Primary -2R latch and the Testing cost filter of 0.15R.

The tests are T1 (lab frames: fit 2024-10 + 2025-03..09, check 2025-10-01..2026-11-04, combined) and T2 (2023-01-03..
2024-09-13, the 469-symbol `data/cache_fresh`). The locked block 2024-11-01..2025-02-28 is never read.

A variant is booked under the rules of its **destination testing account**: cap 100 (150 in Testing 1), cost filter
0.15R, no latch. The standard is the median of the top 10 booked in their **home** accounts (the official numbers
below). The testing-rules medians are reported beside them for information.

## The standard (median of the top 10, home-account view; benchmark.json "standard")
| test | avg R | avg R w/o best day | total R / session |
|---|---|---|---|
| T1 combined (446 sessions) | −0.0283 | −0.0474 | −0.4862 |
| T1 check (276 sessions) | −0.0364 | −0.0581 | −0.5218 |
| T2 (427 sessions) | −0.0848 | −0.1072 | −0.1242 |

**All the medians are negative.** In this engine the top 10 lose money after costs. On T1 combined 3 of the 10 are
positive (NM-ETF-late-dip +0.140, NM-RWN4 +0.070, CWT09 +0.054); on T2 1 of the 10 is (RW6 +0.034). So "meets the
standard" means "backtests no worse than the setups that are winning live". It does **not** mean "profitable in
backtest". Every report must say so.

## TIER A: MEETS OR EXCEEDS (all must hold; thresholds fixed now)
1. **T1 combined avg R >= −0.0383** and **T1 check avg R >= −0.0464**. This is the median minus the Workbench "meets"
   tolerance, max(0.01R, 5% of |median|). Because the medians are negative, the 0.01R leg binds.
2. **avg R w/o best day >= median − 0.02R** on both: **>= −0.0674** (T1 combined) and **>= −0.0781** (T1 check).
3. **total R / session >= median** on both: **>= −0.4862** (T1 combined) and **>= −0.5218** (T1 check).
4. **T2 avg R >= −0.1048** (median − 0.02R).
5. Enough data to judge: **>= 20 trades on T1 check and >= 20 on T2.** Below that, Tier A is "not scorable", and the
   variant can only be Tier B.
6. T3 (the recorded-quote replay, 2026-11-18 only) is reported when the variant's account is covered. It is never a
   pass condition.

## REALLY BAD (pre-registered, binding): never admitted
- T1 combined avg R <= −0.05 **with** day-clustered t <= −2.0, **or**
- avg R < −0.03 on **all three** of T1 fit, T1 check and T2.

T2 counts toward the second leg only when it has at least 20 trades. With fewer, the second leg needs T1 fit and T1
check both < −0.03.

## TIER B: DEBATABLE / DERIVED (admitted only if slots allow)
- **Derived:** the mechanism comes from a promising parent. A promising parent is any of the 10 setups in
  BENCHMARK.md, or any setup with live avg R > 0 **and** live avg R w/o best day > 0. The live figures (avg R / w/o
  best day) of the parents that meet the second test: NM-ETF-late-dip (+0.248 / +0.235), L3-fromopen (+0.204 /
  +0.156), CWT09-g10 (+0.218 / +0.141), L3-lowdist (+0.231 / +0.091), RW3-FD (+0.139 / +0.025), RW5-FD (+0.110 /
  +0.022), L3-rsi5hi (+0.089 / +0.007), ST7-FD (+0.081 / +0.002). The WB4 ETF dip also counts. RW6-FD, NM-RWN4 and
  CWT14-orl-WB5 count only because they are in the top 10: their live w/o-best-day figure is negative (one-day
  records).
- **Debatable:** fails Tier A and is not REALLY BAD.
- Labelled "debatable / derived from <parent>" everywhere: ledger, assignments note, reports.

## Both tiers
- **No duplicates.** If at least 70% of a variant's T1 symbol-sessions are also traded by an existing live setup, or
  by another admitted variant, admit only the one with the better T1 combined avg R.
- **Slots.** Tier B admissions are capped at what fits the free testing-arena slots without crowding. Tier A goes
  first.
- Configs are counted (job cumulative N ~1,882 before this step; the benchmark adds no fitted config). Every finalist
  is reported, pass or fail, with costs in.
