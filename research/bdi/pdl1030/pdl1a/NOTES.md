# PDL-1a: regime-day R2A in Testing 2 (owner exception, 2026-10-30)

*Educational only — not financial advice.*

**Owner exception, NOT a candidate.** R2A did not pass the BAR90 Testing bar: TRAIN +0.0031 / VALID +0.0071 avg R,
t 1.14 vs bar 4.355, 76.5% months positive, 54.3 trades/session; 152 configurations tried in pdl1030, lineage N 121,611.
Owner 2026-10-30 ~08:00 ET: "Move forward with 1a". It runs as a forward observation from 2026-11-02.

## Live form (two setups, one per side; exactly one can fire on a day)
- `CWT14-failbrk-pdl-p05-R2A-long` / `-short` (research/bdi/cwt/live, shared rules in `pdl1a_lib.py`).
- Signal: CWT14-failbrk-pdl-p05 (`cwt_live_lib.b3` PD, p 0.05), the FIRST bar per symbol-day with a bar close in
  09:50-15:00, adv20 >= $95M; skip the day when that bar's cost estimate is > 5% of R1 = 0.25 ATR (as build.py:
  [(1c + 1 bp) x 1.4 before 10:30 + (1c + 1 bp)] x 3 on the extended tier).
- Side: lab context `spy_prng` = SPY (prev_high - prev_low) / ATR from SPY's daily prior; > 0.7956493 long, < short.
- Exits (GEOM "S"): stop 0.75 ATR (3 x R1, same $ risk), target 0.125 ATR (the parent's +0.5 R1 price), half off at
  0.0625 ATR (`scale_out_r` 1/12 of the stop distance, `live_scale_out`), rest to breakeven, flat 15:55.
- New code (opt-in): lab context column `spy_prng` and `DayContext.index_priors`; the runner loads SPY's daily prior
  once per session only when a setup asks (also when SPY is outside the universe; never traded because of it).

## Parity (`parity.py` -> `parity.json`), TRAIN / VALID months only
| month | split | research entries | live entries | matched | side agree |
|---|---|---:|---:|---:|---:|
| 2025-03 | TRAIN | 1,381 | 1,381 | 100% | 100% |
| 2025-06 | TRAIN | 535 | 535 | 100% | 100% |
| 2025-10 | TRAIN | 1,231 | 1,231 | 100% | 100% |
| 2026-02 | VALID | 1,515 | 1,515 | 100% | 100% |
| 2026-08 | VALID | 1,458 | 1,458 | 100% | 100% |
| total | 104 sessions | 6,120 | 6,120 | 100% | 100% |

The live `spy_prng` (mcf.data.priors daily ATR on the history daily bars) equals the research frame PRNG on every
sample session (max abs diff 0). The exits are the scored sim's prices (up 0.5 R1, dn 3 R1, scale-out 0.25 R1 / half)
written as prices; the live entry is the next bar's market fill, as for every lab setup.
