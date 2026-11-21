Educational only — not financial advice.

# Give-back remedy test (BD&I 1121), pre-registration

Written 2026-11-21 ~16:25 UTC, after the week's give-back table (giveback_week.csv) and **before any remedy was
scored**. Research only.

## Failure mode (this week, Primary)
Primary gave back 44.3R from intraday peaks (5 sessions). The largest single piece of "entries after the peak" was
11-20: NM-ETF-late-dip-di-long opened 12 lots in 14:11-14:16 ET (QLD, SPXL, UPRO, SMH, TECL, TNA, TQQQ, SOXX, SOXL,
GDXJ, NUGT, SILJ) — about three bets (US index / semis / gold miners) taken twelve times — and all 12 stopped
(−12.6R). The open-winner part (11-19 ST7 −13.4R, L3 −9.3R after the 11:50 index drop) belongs to the exit classes
that failed on 11-19 (research/giveback_1119) and ST7 leaves Primary 11-23, so it is not re-tested.

## Remedy (targeted at the failure mode; not a setup-specific tailor, not an account brake)
**Correlated-group lot cap:** within a setup's book, symbols whose daily returns correlate >= 0.85 (FIT-period daily
closes 2024-10 + 2025-03..09 only; average-linkage clusters) count as one "symbol" for the existing <= 3-lots cap
(live.max_lots_per_symbol). Uncorrelated names are their own group, so the cap only binds on near-duplicates.
- **GC1:** <= 1 open lot per correlated group. **GC2:** <= 2 open lots per correlated group. (2 configs.)
- Applied to all 11 bench10 setups (Primary lineup after 11-23: NM-ETF, RW5, RW3, L3-fromopen; plus the rest) so the
  per-setup better/worse count covers every family (remedy rule).

## Engine and scoring
bench10 normal way (research/ultimate_1119/top10/bench10.py `add_r` + `book`, the home-account rules: Primary cap 30
+ −2R latch; testing cost filter 0.15R), on the saved T1 signal/exit file of the 11-19 top-10 benchmark (same frames,
1-minute exits). FIT 2024-10 + 2025-03..09, CHECK 2025-10-01..2026-11-04 (scored once per config). Locked block
never read. Label E4-normal-way.
- Pass (proposal) only if, for the setups where the cap binds: CHECK Δ total R > 0 AND FIT Δ total R > 0, trades kept
  >= 90% per affected setup, top-decile winners kept >= 90%, avg R w/o best day not lower, and the gain beats removing
  the same number of trades at random from the same setup-days (>= 95th percentile of 500 draws, CHECK).
- Live week replay (descriptive only, not a pass leg): the same cap on Primary's 11-16..11-20 journal in entry order.
- Lineage N: give-back / burst lineage 40 (sat1114) + 3,836 (giveback_1119) counted as reported there; +2 here.
