Educational only — not financial advice

# cov-long: long setups aimed at the days Primary loses (overnight 2026-11-21)

## Result
- **No new long setup passes.**
  - Tested: 9 mechanism finalists, 24 configurations in total. Costs are in (LR8 + time-of-day multiplier). Exits on 1-minute bars. Testing book: cap 100, 3 lots per symbol, 0.15R cost filter.
  - Each finalist was picked on FIT by a rule written down before any score. CHECK (2025-10-01..2026-11-04) and T2 (2023-01..2024-09) were then scored once per finalist.
  - The locked block 2024-11..2025-02 was never read.
- **All 9 finalists are net negative on CHECK.**
  - They are positive on SPY-up days, but only by about the market move.
  - They are negative on quiet days, on flat and down days, and (7 of 9) on gap-up days.
- **Most finalists do no better than random long entries.** The comparison is a matched null: a random eligible symbol at the same date and bar time, with the same exits and costs.
- **What can be salvaged:**
  - N1, a narrow-range day then opening-range breakout (Crabel), beats the null in all 3 tests. It is a near-miss on the top-10 bar.
  - M7, a trend-day VWAP pullback, passes every top-10 avg-R bar but fails R per session.
  - E2, late-day ETF momentum, meets the top-10 Tier A bar but has no edge over the null.
  - None is good enough to admit. Owner rule: don't force weak setups.

## Why Primary loses on these days (backtest proxy = today's 5 Primary setups on the Primary book)
| test | corr(Primary proxy, SPY open→close) | proxy R per session: SPY up / flat / down | quiet days | SPY gap-up days |
|---|---|---|---|---|
| FIT | -0.26 | -9.1 / -2.0 / +1.3 | -3.3 | -2.0 |
| CHECK | -0.36 | -7.9 / -0.5 / +4.0 | -0.8 | -1.7 |
| T2 | -0.35 | -4.1 / -0.9 / +1.2 | -1.1 | -0.4 |
| live, 22 days | -0.23 | -8.1 / -3.7 / +10.8 | -1.9 | -7.5 |

## Finalists (testing book; avg R per trade after costs)
| id | mechanism | FIT | CHECK (t) | T2 | FIT+CHECK w/o best / w/o top-2 | null CHECK / T2 | CHECK R per session: up / quiet / gap-up | corr with Primary proxy (CHECK) / live | top-10 bar |
|---|---|---|---|---|---|---|---|---|---|
| N1-nrorb-06 | narrow range → opening-range breakout | +0.005 | -0.057 (-1.86) | -0.030 | -0.043 / -0.048 | -0.083 / -0.034 | +2.25 / -1.83 / -0.43 | -0.19 / -0.03 | NEAR: fails CHECK avg R |
| E2-etfmom-own-spy | late-day ETF intraday momentum | -0.026 | -0.039 (-0.82) | -0.070 | -0.047 / -0.056 | -0.036 / -0.061 | +0.90 / -1.03 / -0.86 | -0.02 / +0.16 | MEETS Tier A, no edge over null |
| M7-vwappb-spy0 | trend-day VWAP pullback reclaim | -0.022 | -0.034 (-1.32) | -0.064 | -0.038 / -0.043 | -0.044 / -0.013 | +2.20 / -1.08 / +0.23 | -0.03 / -0.10 | NEAR: fails R per session |
| M6-riskon-sg02 | SPY gap-up open, in-play new high early | +0.054 | -0.077 (-1.78) | -0.032 | -0.042 / -0.055 | -0.095 / -0.106 | +0.19 / -0.49 / -0.49 | 0.00 / -0.01 | FAIL |
| M2-pdhbrk-spy03 | intraday prior-day-high breakout, green tape | +0.026 | -0.074 (-2.18) | -0.015 | -0.060 / -0.070 | -0.054 / -0.005 | +1.03 / -1.55 / -0.73 | -0.17 / +0.05 | FAIL |
| M3-rshod-k3 | relative-strength leader, new high after midday | -0.012 | -0.061 (-3.17) | -0.049 | -0.053 / -0.056 | -0.054 / -0.023 | +6.55 / -3.77 / -0.82 | -0.32 / -0.03 | FAIL |
| M5-quiet-r08 | idiosyncratic leader on a quiet tape | -0.017 | -0.088 (-3.60) | -0.056 | -0.076 / -0.081 | -0.108 / -0.055 | +2.51 / -2.75 / -1.54 | -0.24 / +0.03 | FAIL, REALLY BAD |
| M4-imom-f15 | late-day stock momentum | -0.045 | -0.062 (-3.45) | -0.064 | -0.059 / -0.062 | -0.073 / -0.055 | +2.26 / -4.38 / -4.09 | -0.16 / +0.21 | FAIL, REALLY BAD |
| M1-gapgo-g2 | gap-up continuation | -0.103 | -0.077 (-2.24) | -0.075 | -0.093 / -0.101 | -0.098 / -0.047 | +0.31 / -0.04 / -0.84 | +0.03 / +0.19 | FAIL, REALLY BAD |

- **Trade counts:**
  - CHECK: N1 4,194; E2 2,799; M7 5,278; M6 876; M2 4,146; M3 13,730; M5 6,053; M4 21,376; M1 1,997.
  - T2: 462-11,757 trades per finalist.
- **Live correlation is weak evidence.** The backtest data ends 2026-11-04, so only 22 live Primary sessions overlap (16 of them red).
  - Over that overlap, M7's backtest made +35R, and +2.3R per session on Primary's red days.
  - N1 made +1.2R. Every other finalist made between +10R and -108R.

## Combined with Primary (Primary-book rules: cap 30, -2R latch)
- **No finalist raises Primary's green-day share in any test.** Every one turns more green days red than red days green.
  - Example, M7 on CHECK: 14 days red→green, 25 green→red.
  - Example, M6 on CHECK: 7 days red→green, 11 green→red.
- **The Primary book makes the longs worse by 0.03-0.06R per trade.** Without the 0.15R cost filter, low-volatility names with high cost per R get in.
- So if a long is ever trialled, it should be in a testing arena under the cost filter.

## What this says (looking for the next step)
1. **Covering up days with stock-level longs is mostly market exposure.** After costs it is about random-entry R, so it cannot pay for itself.
   - Primary's up-day loss per session is 3-40x larger than any finalist's up-day gain.
   - The lever is on the short side, at the source of the up-day loss. This track cannot add a cover long that fixes it.
2. **Quiet days and gap-up days are not covered by any long mechanism tried.** Even M5, built only for quiet tapes, loses on them.
3. **N1 is the one with a consistent edge over random entries:** +0.06 (FIT), +0.026 (CHECK), +0.005 (T2).
   - It is the best lead for a future derived variant.
   - CHECK has now been used for N1, so any refinement needs a fresh window.
   - It is not derived from a promising parent, so it is not admissible today.

## Rule-change context
- This is backtest only. Today's rules are applied to every session, so no rule change falls inside the backtest windows.
- The live Primary window 10-06..11-04 contains these changes (research/ledger.jsonl):
  - L3-fromopen moves (10-20, 10-22, 10-30);
  - per-setup latch (10-23);
  - Primary sizing ~$4k and per-setup cap 30 (10-28);
  - -2R latch (10-29);
  - Testing cost filter 0.15R (10-30).

## Method and files
- **Engine:** `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/cov-long/eng.py`. It reuses `research/ultimate_1119/top10/bench10.py`: signals, 1-minute walk, LR8 add_r, book.
- **Scoring:** `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/cov-long/score.py`.
- **Masks:**
  - `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/cov-long/cands.py` (M1-M7)
  - `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/cov-long/cands2.py` (E1-E3)
  - `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/cov-long/cands3.py` (N1-N2)
- **Pre-declared selection and fit picks, with timestamps:** `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/cov-long/SELECTION_RULE.txt`.
- **Results:** `final.json`, `r2_final.json`, `r3_final.json` and `combo.json` in the same folder.
- **Decision-time inputs only:**
  - SPY gap, SPY return from open and SPY range so far, computed from SPY 1-minute bars up to the bar close;
  - frame columns at the bar close.
  - Day-type labels (SPY open→close ±0.3%; gap-up >= +0.3%; quiet = bottom third of SPY day range) are used only for reporting.
- **Universe:** lab ~1,200 symbols for T1 and 469 symbols for T2. Survivorship bias is stated, not fixed. No earnings blackout or spread skips are modelled.
- **Configurations tried:** 24.

## Robustness

null