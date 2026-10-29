Educational only — not financial advice.

# p1_1029: asymmetric book and the long side (owner Prompt 1), 2026-10-29

**Result: nothing passed. 0 finalists out of 367 configurations, so the locked block (2024-11-01..2025-02-28) was not
scored. Lineage looks used: 0.** No config, setup, exit, engine or ledger file was changed, and nothing was committed.
Proposed backlog lines are in `backlog_proposed.jsonl` and were not appended to research/backlog.jsonl.

- **Live** numbers are paper trades (rule 7) from the Primary, Testing 1 and Testing 2 journals (run 1, 2026-10-06..10-28,
  complete sessions only; 10-29 is in progress and left out). They come from `git show origin/mcf-data*:journal.db`,
  which is the same read-only route nightly1028 used.
- **Two-year** numbers are backtests on the open history (2024-09..2026-10-07, locked block never loaded). Costs are in:
  1c + 1 bp per side with the time-of-day entry multiplier, +2c on stop exits, x3 on the extended tier.
  - TRAIN is up to 2025-12-31; VALID is open 2026.
  - All R is in live units (1R = the stop distance). The cache's t1s05 R, which is in 0.25-ATR units, is divided by 0.5.
- **`PLAN.md` was written before any history configuration was scored** and was not changed afterwards.
- **Configurations scored (`counts.json`): 367.**
  - Long gates: 144, bar 3.15. The gates1021/regime1022 gate lineage is about 1,400, so the bar there would be 3.8.
  - Vol switch: 196, bar 3.25.
  - Exit sweep: 27. Per-setup lineage bars are 2.55-2.57 (N 26-27, which includes top5_1023 and top5_1026).
  - Study-wide bar: sqrt(2 ln 367) = 3.44.
  - Zero-trade rows are counted: ST7Q has 0 two-year signals in the cache.
- **Pre-open inputs only (G1 lesson).**
  - Every regime value for session d comes from daily bars through d-1. The one exception is the SPY overnight gap, which
    uses d's 09:30 open; that open is known before any entry, since entries start at 09:50 or later.
  - Rolling windows never span the locked gap.
  - The cache's `spy_prev` column, which has the gates1021 lookahead, is **not** used.
- **Not testable:**
  - Pre-market relative volume: the bar cache is RTH only (09:30-16:00). The study says so and does not test it.
  - VIX: not in the data. VXX was used as the proxy.
  - CWT05, CWT12-flag, CWT13, LIQ, LD2/6/7/8 (holdtr / ETF), orb20_a and intraday_momentum have no kernel in this harness.

## Failures first
1. **Task 2, pre-open long gate: 0 of 144 are finalists.** The pooled long book loses -0.074R/trade over 182k trades,
   and no gate turns it positive: the gated book runs -0.076 to -0.089R/trade.
   - The large "improvement" t-values (L6 prior-day SPY up: t 5.8) are an artefact of thinning a losing book: removing
     about half the days removes about half the losses.
   - Against random removal of the same share of days, L6 sits at the 34th percentile. Every pooled gate is below the
     95th; L3 / L5 / L8 are at 0-0.3%, which means they keep *worse* days.
   - Two gates clear "beats parent" on CWT14-p10-lowvol: L6 and L7, at t 6.1 / 5.6. Both still lose (-0.089 / -0.093R)
     and are no better than random (rand pct 0.71 / 0.60).
2. **Task 4, vol switch: 0 of 196 are finalists, and the hypothesis is not supported.**
   - Pooled fade book (28 setups, 367k trades, -0.061R): V1 (ATR > p70) gives -0.064R and V7 (VXX) gives -0.060R. Both
     are no better per trade, and both are below random removal (rand pct 0.18 / 0.59).
   - There is no 70/80/90 plateau: V1 has d +0.009, V2 +0.004, V3 -0.000. V4-V6 are flat.
   - The momentum control loses with the switch on every row (d -0.009..-0.026R). High-vol days are *good* for the
     momentum book, so the asymmetry the article suggests does not show up as a fade-book edge here.
   - **Limitation:** trailing percentiles need 60 prior sessions. As a result Oct 2024 and Mar to about mid-May 2025,
     including the April 2025 crash, are ungated: 21-24% of sessions (`regime_days.py`).
3. **Task 3, Primary shorts: no variant is positive.** Wider stops beat the parent at the bar on RW3-FD and RW5-FD, but
   every variant still loses in TRAIN and in VALID. Scale-out is worse than the parent everywhere except at +0.8R, where
   it is marginal.
4. **The one-big-day check is moot for the gates.** No modified row is positive pooled. Where a setup is positive, the
   best-day share is shown in `eval_out.txt`.

## 1. Long-book audit (live paper; `live_audit.py` -> `live_longs.csv`, `live_audit_out.txt`)
Records are merged across P/T1/T2 by setup name, as the dashboard does. Shrunk = avgR x n/(n+20). The 2-yr column is the
cache / kernel parent from this study (costs in).

**Long setups with n >= 15 live trades and shrunk avg R < 0: 9.** NS5-FD appears in both T1 and T2.

| setup (acct) | live n / sess | live avgR | shrunk | live t | net $ (paper) | w/o best day | 2-yr avg R (n) |
|---|---|---|---|---|---|---|---|
| NM-AR-AM-gapdown-capitulation-long (T2) | 25 / 2 | -0.534 | -0.296 | -6.79 | -238 | -0.470 | **+0.262** (1,588; NM-mined on this history: in-sample) |
| NS5-sma50-flush-oversold-long-FD (T1+T2) | 35 / 12 | -0.350 | -0.223 | -2.33 | -219 | -0.454 | -0.046 (3,139) |
| CWT14-failbrk-pdl-p05-lowvol-long (T2) | 384 / 13 | -0.118 | -0.112 | -1.68 | -415 | -0.148 | -0.096 (44,026) |
| CWT14-failbrk-pdl-p05-long (T1) | 618 / 13 | -0.077 | -0.074 | -0.90 | -346 | -0.111 | -0.065 (66,875) |
| NS1-rsidip-rsi5pop-long-FD (T1) | 34 / 10 | -0.087 | -0.055 | -0.81 | -84 | -0.156 | -0.070 (2,490) |
| CWT14-failbrk-pdl-p10-long (T2) | 349 / 13 | -0.029 | -0.028 | -0.27 | -34 | -0.080 | -0.086 (37,499) |
| CWT05-flush-m05-v3-long (T1) | 27 / 8 | -0.037 | -0.021 | -0.22 | -23 | -0.202 | not in harness |
| CWT13-vwapstretch-z05-long (T2) | 69 / 11 | -0.021 | -0.016 | -0.13 | -79 | -0.190 | not in harness |
| orb20_a (T1, long trades only) | 17 / 10 | -0.026 | -0.012 | -0.10 | -52 | -0.145 | not in harness |

- Just outside the n cutoff: ST4-emadn-FD (T1), 13 trades at -0.507R (2-yr +0.034R, best-day share 102%, so a one-day
  record); CWT12-flag-s1 (T2), 13 trades at -0.171.
- **Primary longs are all positive live, and none of them survives the one-big-day check.**
  - NS1: 12 trades, +0.184; without the best day -0.135 (share 137%, **1 day**).
  - ST7-FD: 18 trades, +0.162; without the best day -0.081 (share 139%, **1 day**).
  - NS5: 20 trades, +0.149; without the best day +0.046 (share 71%, **1 day**).
  - 2-yr: NS1 +0.031R (best day 53%: **1 day**), NS5 -0.042R, ST7-FD +0.024R (40%).
- **Whole live book:** longs 4,025 trades at -0.143R/trade (t -2.40); shorts 3,539 at -0.097R (t -1.11). The long side
  is the larger live loss, mostly from CWT14 volume. CWT14 runs about 157 two-year signals a day; live is capped by slots.

## 2. Ranked table: Baseline vs Modified (two-year, costs in; $ at ~$15/R, Primary's median live risk)
Ranked by the paired day-clustered improvement t. "Pass" means finalist; see PLAN for the rules.

| # | setup | modified | N | avg R base -> mod | shrunk base -> mod | win base -> mod | total net R (mod) / $ | t (mod) | t improve (bar) | rand pct | w/o best day | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | RW3-FD | stop x2.5 same $ | 5,995 | -0.071 -> -0.021 | -0.071 -> -0.021 | 48.3 -> 53.5% | -126R / -$1,887 | -1.83 | 3.79 (2.55) | n/a | -0.024 | **fail** (loses TRAIN -0.026 / VALID -0.015) |
| 2 | RW3-FD | stop x2.0 / x3.0 / x3.5 | 5,995 | -0.071 -> -0.030 / -0.018 / -0.015 | same | 53.2-53.7% | -178 / -107 / -89R | -2.2..-1.7 | 3.60-3.66 | n/a | <0 | fail (plateau, all negative) |
| 3 | RW5-FD | stop x2.0 same $ | 5,598 | -0.060 -> -0.029 | -0.060 -> -0.029 | 49.1 -> 53.0% | -162R / -$2,423 | -2.05 | 2.82 (2.57) | n/a | -0.031 | **fail** (negative) |
| 4 | RW5-FD | stop x1.5 / 2.5 / 3.0 / 3.5 | 5,598 | -> -0.039 / -0.023 / -0.019 / -0.017 | same | 52-53% | -220..-94R | -2.2..-1.9 | 2.71-2.80 | n/a | <0 | fail |
| 5 | RW3-FD | scale half +0.8R, BE | 5,995 | -0.071 -> -0.059 | same | 48.3 -> 52.1% | -353R | -2.92 | 3.13 (2.55) | n/a | -0.064 | fail |
| 6 | RW5-FD | scale half +0.8R, BE | 5,598 | -0.060 -> -0.051 | same | -> 52.4% | -283R | -2.30 | 2.60 (2.57) | n/a | -0.056 | fail |
| 7 | MF2-FD | stop x3.5 same $ | 5,235 | -0.087 -> -0.028 | -0.087 -> -0.028 | 38.0 -> 52.8% | -146R / -$2,194 | -1.38 | 2.12 (2.55) | n/a | -0.035 | fail (below bar; TRAIN +0.004, VALID -0.051) |
| 8 | LONG BOOK pooled | L6 prior-day SPY > 0 | 182,421 | -0.074 -> -0.076 | -0.074 -> -0.076 | 65.9 -> 65.5% | -6,854R | -7.29 | 5.83 (3.15) | 0.34 | -0.078 | fail (thinning artefact) |
| 9 | CWT14-p10-lowvol | L6 prior-day SPY > 0 | 20,080 | -0.095 -> -0.089 | -0.095 -> -0.089 | 64.0 -> 64.2% | -847R | -6.25 | 6.09 (3.15) | 0.71 | -0.092 | fail |
| 10 | NS5 (Primary) | L1 SPY prior close > SMA20 | 1,305 | -0.042 -> **+0.095** | -0.042 -> +0.093 | 50.0 -> 56.6% | +62R / +$930 | 1.62 | 1.25 (3.15) | **0.976** | +0.066 | fail (below bar) -> backlog rework |
| 11 | FADE BOOK pooled | V1 SPY ATR14 > p70 skip | 367,323 | -0.061 -> -0.064 | same | | | | 2.94 (3.25) | 0.18 | -0.067 | fail |
| 12 | FADE BOOK pooled | V7 VXX 5d > p80 skip | 367,323 | -0.061 -> -0.060 | same | | | | 2.73 (3.25) | 0.59 | -0.063 | fail |
| 13 | NS1-FD | V6 RV20 > p90 skip | 2,490 | -0.070 -> -0.055 | | | | | 2.59 (3.25) | 0.999 | -0.062 | fail (negative) |
| 14 | MOMENTUM pooled (control) | V1..V7 | 2,112 | +0.062 -> +0.045..+0.059 | | | | | -2.4..-1.3 | | | worse on every row |

All 367 rows, including every failure, are in `results.csv` and `eval_out.txt`. Parent parity: the simulated parents
match the cache R (mean |d| 0.0000 / 0.0000 / 0.0001R for RW5 / RW3 / MF2).

## 3. Task 3 readout (top5_1028 "wider stops help shorts", checked)
- **Confirmed on the Primary families.** The stop curve at the same $ risk rises monotonically from x1.0 to x3.5:
  - RW3-FD: -0.071, -0.042, -0.030, -0.021, -0.018, -0.015.
  - RW5-FD: -0.060, -0.039, -0.029, -0.023, -0.019, -0.017.
  - MF2-FD: -0.087, -0.068, -0.053, -0.040, -0.032, -0.028.
- It approaches zero from below and **does not cross it** in VALID on any setup, and in TRAIN only on MF2 at x2.5-x3.5
  (+0.002..+0.006). This is the same as top5_1022, 1023 and 1028 on the other shorts.
- Wider stops raise the win rate by 4-15 points, and the break-even win rate rises with them.
- Scale-out (half off at +0.25 / 0.40 / 0.60R, rest to breakeven) is worse than the parent on all three. At +0.8R it is
  only slightly better on RW3 and RW5.
- Caveat: refire chains are taken from the production-exit cache, so a wider stop does not re-time MF2-FD's refires.

## 4. Fade vs momentum (explicit, used in task 4)
- **Fade** means the entry goes against the last move.
  - Shorts into a bounce, pop or failed reclaim: MF2-FD, MF4, MF4-FD, MF3-FD (flow-sell into an RSI pop), RW1/RW3/RW5/
    RW7-FD (gap-down bounce or pop short), RW4-FD and NS3-FD (failed VWAP reclaim), exhaustion_short-FD, and
    L3-fromopen/lowdist/rsi5hi-FD (gap-slope fade).
  - Longs into a dip, flush, capitulation or failed breakdown: NS1, NS1-FD (RSI dip), NS5, NS5-FD (SMA50 flush), ST7-FD,
    ST7Q-FD (RSI50 down), ST8-FD (volume-spike down), ST4-FD (EMA down, morning), NM-AR-AM (gap-down capitulation), and
    the four CWT14 failed-PDL-break longs.
- **Momentum** means the entry comes on a confirmed turn or trend: LD1, LD3, LD4, LD5 (breadth-up / index-turn
  confirmation) and NM-HL-T75 (afternoon higher-low).
- Almost the whole live book is fade. Momentum is 5 setups and 2,112 two-year trades.

## Recommended DECISION items for the owner
1. **No promotion, demotion or gate from this study** (0 finalists, no locked look).
2. Decide whether to keep or Graveyard the live long losers with clear two-year support for the loss:
   - CWT14-pdl-p05-lowvol: live -0.118 on 384 trades, 2-yr -0.096.
   - CWT14-pdl-p05: live -0.077 on 618, 2-yr -0.065.
   - CWT14-pdl-p10: live -0.029 on 349, 2-yr -0.086.
   - NS1-FD: live -0.087 on 34, 2-yr -0.070.
   - NS5-FD: live -0.350 on 35, 2-yr -0.046.

   Per rule 20, routines may only propose this; the decision is the owner's. NM-AR-AM's live -0.53 comes from 2 sessions
   against an in-sample two-year +0.26, so it needs more sessions, not a decision.
3. Backlog (proposed, not appended):
   - NS5 + "SPY above SMA20" as a rework: it beats random but is below the bar.
   - Wide stop on RW3-FD / RW5-FD as a rework: it beats the parent but is still negative.
   - Mark regime1029-preopen-vol-regime as first-test failed, with the rework idea of a longer daily history so the
     April 2025 regime is gated.
4. The Primary longs' positive live records are each carried by 1 day (share 71-139%). Read them with that in mind.

## Files
- `live_audit.py`: task 1 (journals in scratch).
- `build_cache.py`: gates1021 cache for 28 setups, in scratch.
- `regime_days.py` -> `regime_days.csv`: pre-open inputs.
- `scan_p1.py`: CWT14 kernels and the task 3 exit grid.
- `evaluate.py` -> `results.csv`, `eval_out.txt`, `counts.json`.
- `PLAN.md`, `backlog_proposed.jsonl`.

Educational only — not financial advice.
