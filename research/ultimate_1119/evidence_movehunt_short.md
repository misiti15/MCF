# Evidence: movehunt_short (short fade swings, 09:50-15:15 ET), FIT HALF ONLY

Consultant evidence miner, ultimate_1119 overnight job (2026-11-19). Educational only — not financial advice.

## Bottom line
- **No short-fade precursor set passes on the fit half after costs.** 240 configurations were scored (121 in pass 1, 119 in pass 2). Every positive cell is carried by one or two sessions, or is too thin and splits badly between the two sub-halves.
- **The precursors predict *volatility*, not *direction*.** Extension features raise the chance of a ≥1R roll-over 2-5x: the 45-minute swing rate goes from 11.6% at random to 42-53% with run-up from LOD ≥ 2-3 ATR, 45% with run-up from open ≥ 2 ATR, 31% after a failed new high, and 58-83% for gap-down RSI5-pop rows. Adverse excursion grows just as much, so expectancy does not improve on random.
- **The gap-down RSI5-pop family (MCF's best live family) is not reproduced here.** Its whole fit-half total comes from **2025-04-07**, the tariff-crash day with the 10:15 fake-pause spike. Without that day: K5 G5 goes from +0.30 to −0.105 R/trade and K10 G5 from +0.62 to −0.023. My definitions (gap ≤ −2/−2.5%, run-up from open ≥ 1-1.5 ATR, RSI5 ≥ 75) are cruder than the L3 slope module, so this does not contradict L3's live record. It does mean a bare "gap-down + pop" rule has no edge here.
- **Salvageable leads (weak; check-half candidates at most, not promotion material):**
  1. **K6 D45**: gap ≤ −2%, run-up from open ≥ 1 ATR, RSI5 ≥ 75, SPY since 09:50 ≤ +0.15%; short at the next minute's open, pure 45-minute time exit with no stop.
     - n 408 over 105 days (2.4/day); avg +0.094 R (per R0 = 0.25 prior-day ATR); t 0.81.
     - Avg R w/o best day +0.051; best-day share 0.52 (1-day tag).
     - Halves: A +0.07, B +0.13. Trimming the top 1% of trades leaves +0.03.
     - The same rows with a 0.25-dATR stop (g1) lose −0.22.
  2. **K11 D45** (K6 tightened to the L3 window: gap ≤ −2.5%, run-up from open ≥ 1.5 ATR, 10:15-13:00):
     - n 161 over 67 days; avg +0.19; w/o best day +0.07; best-day share 0.67 (1-day tag).
     - Halves A +0.04 / B +0.49, so the sign holds but the size does not. Trim 1% leaves +0.12.
  3. **K9 G5**: flat open (|gap| < 1%), run-up from open ≥ 2 ATR, VWAP z ≥ 2; stop at c + 1 × a15 (today's 15-minute range), 1:1 target.
     - n 259, avg +0.17, but 197 of the 259 trades fall on **2025-04-09** (the pause-rally day).
     - The other 62 trades over 38 days average +0.24, half of that from 2025-07-01. Too thin.
- What survives as a *structural* lesson:
  - The SPY-not-rising filter turns the K5/K10 gap-down pop rows from deeply negative to about flat or slightly positive. With a time exit they stay positive in both sub-halves.
  - Fades need room. A stop scaled to today's realized range (G5/G6) or no stop at all (D-exits) consistently beats the tight 0.25-prior-day-ATR stop on extended names: the move comes, but after the stop.
  - A stop just above HOD (G7) is the worst geometry everywhere, with −0.2 to −1.4 R/trade.

## Data / method
- 2-year 1-minute cache `/home/user/MCF/data/cache_hist/1Min`: 1,183 of 1,226 symbols produced rows. The other 43 had no fit-half sessions passing px ≥ $5 and ADV ≥ $10M.
- **Fit half** = 2024-10-01..10-31 plus 2025-03-01..09-30, 169 sessions. The cache starts 2024-09-16, so September 2024 was used only to warm up prior-day ATR/ADV.
- The locked block 2024-11-01..2025-02-28 and the check half (≥ 2025-10-01) are dropped as each file is loaded, before any feature or statistic is computed. They are never scored.
  - Caveat: the raw cache file holds those rows, so they pass through memory for the instant before the filter.
  - Daily ATR/ADV in early March 2025 is computed on October 2024 bars, which is stale but not look-ahead. The first March session after the gap is skipped.
- Signals: every 5-minute bar close from 09:50 to 15:15.
  - Every feature uses only bars closed by the signal time: prior-day ATR(14) and ADV20, session VWAP ± sd, RSI(5) on 5-minute closes, HOD/LOD so far, minutes since HOD, 30-minute blow-off volume, ret5/ret15, rvol15, SPY since 09:50 and over the last 30 minutes, and a15 (mean range of today's completed 15-minute blocks).
  - Fill at the open of the minute after the signal close.
- Universe U1: price ≥ $5, ADV20 ≥ $20M, R0 = 0.25 × prior-day ATR ≥ 0.40% of price. That is 10.9M signal bars, about 64.5k per session.
- **Costs (LR8 live model, short side)**:
  - Entry: (1c + 1bp) × TOD multiplier + 1bp cushion + SEC + CAT.
  - Exit: stop (1c + 1bp) + max(2c, 4bp); time (1c + 1bp) + max(1c, 1bp); target TAF + CAT. A target fills at the limit, never better.
  - When stop and target hit in the same minute, the stop counts first.
  - No borrow fee is charged (intraday). Hard-to-borrow availability is not modelled. ETB uses today's `universe.csv` flag, which is not point-in-time; almost all of U1 is ETB and the ETB subset matched the full set to within 0.01 R.
- Pass 1 geometries (R per fill-to-stop): g1 t1 s1 cap45 (primary), g2 t1.5, g3 cap30, g4 t0.5. Stop = c + 0.25 dATR.
  - g1c = g1 clipped to [−1.5, 2] is a diagnostic, because fills near the stop inflate R: K9 g1 shows +1.17 but g1c only +0.19.
- Pass 2: pre-declared after pass 1 showed high swing rates but losing stops. Same first-signal-per-symbol-day rows plus a 40k random-bar control.
  - D15/D30/D45: time exits, R per R0.
  - G5: stop c + 1 × a15, 1:1. G6: c + 1.5 × a15, 1:1. G7: max(HOD, c) + 0.1 × a15, 1:1. G8: c + 1 × a15, 2:1. All cap 45 minutes, R per *planned* risk.
  - Each cell also carries a TOD-matched control.
- Sub-halves for sign persistence: A = Oct-2024 + Mar-May 2025, B = Jun-Sep 2025. The SPY up/down-day split is an end-of-day diagnostic, never a filter.

## Baseline (random bars, U1, g1)
- avg −0.137 R/trade with costs; hit 11.3%; swing 11.6%. Random entries lose roughly their cost.
- The random-bar control in pass 2 is −0.12 to −0.22 for every geometry.
- Time of day:
  - The ≥1R swing rate is 24.7% at 09:50-10:30 against 8% after 13:00.
  - a15/R0 falls in step, from 1.48 to 0.65. The early session moves more, but in R terms it is not cheaper to trade: g1 at 09:50-10:30 is −0.18, the worst bucket, because the costs multiplier is 2.1x before 10:30.

## Marginals (U1, g1, all bars; 52 cells)
None is positive. All cells are within about ±0.05 of baseline except those below. A/B is the sub-half split; up/dn is the SPY day split.

| Condition | avg R | A / B | up / dn | Note |
|---|---|---|---|---|
| gap ≥ +3% | −0.005 | +0.05 / −0.13 | −0.16 / +0.15 | Least bad. Sign does not persist; carried by down days. |
| gap ≤ −3% | −0.094 | | | |
| ATR% ≥ 5 | −0.089 | | | |
| SPY since 09:50 ≤ −0.2% | −0.12 | | | |
| price < $10 | −0.41 | | | Costs dominate. Exclude. |
| price $10-20 | −0.26 | | | Costs dominate. Exclude. |
| RSI5 80-90 | −0.19 | | | |
| failed new high | −0.20 | | | |
| VWAP z ≥ 3 | −0.20 | | | |

Each of these overbought precursors is worse than random on g1.

## Combos (first signal per symbol-day)
Pass 1 (g1-g4), n / avg g1 / avg w/o best day:

| Combo | n | avg g1 | w/o best day | Note |
|---|---|---|---|---|
| K1 run-up from open ≥ 1.5 & RSI5 ≥ 80 | 3787 | −0.31 | | |
| K2 VWAP z ≥ 2.5 & RSI5 ≥ 80 | 25978 | −0.18 | | 154/day |
| K3 failed new high & run-up from LOD ≥ 2 | 1556 | −0.31 | | |
| K4 blow-off lower high | 2975 | −0.22 | | |
| K5 gap-down pop | 1701 | −0.58 | | |
| K6 = K5 & SPY ≤ +0.15 | 408 | −0.22 | | |
| K7 = K1 & SPY ≤ +0.15 | 1498 | −0.32 | | |
| K8 = K2 & rolling over | 2502 | −0.15 | | |
| K9 | 259 | +1.17 | −0.11 | Fill-artifact; g1c +0.19 |
| K10 L3-like | 598 | −0.77 | | |
| K11 | 161 | −0.34 | | |
| K12 late extension (≥ 14:00, run-up from open ≥ 1.5, VWAP z ≥ 2) | 808 | −0.01 | −0.05 | g4 +0.23, w/o best −0.05 |
| K13 | 783 | −0.28 | | |
| K14 control: SPY weak | 98k | −0.11 | | |
| K15 gap-up extension | 686 | −0.15 | | |
| K16 gap-up failed new high | 4357 | −0.20 | | 26/day |
| K17 gap-up VWAP stretch rolling over | 549 | −0.12 | | |

Pass 2 (all 119 cells are in `movehunt_short/supp_cells.csv`). The best cell per set, with honest qualifiers:

| Cell | n | avg | w/o best day | Best-day share | Months + | A / B | Note |
|---|---|---|---|---|---|---|---|
| K10 G5 | 598 | +0.62 | −0.023 | 1.01 | 6/8 | | 382 of 598 rows on 2025-04-07 |
| K5 G5 | 1701 | +0.30 | −0.10 | 1.21 | 3/8 | | |
| K12 G6 | 808 | +0.11 | −0.003 | | | | 581 rows on 2025-04-09; −0.003 on the remaining 227 |
| K9 G5 | | +0.17 | | 0.67 | 7/8 | | 197 rows on 2025-04-09 |
| K6 D45 | 408 | +0.094 | +0.051 | 0.52 | | +0.07 / +0.13 | |
| K11 D45 | 161 | +0.19 | +0.07 | 0.67 | | +0.04 / +0.49 | |
| K15 G6 | | +0.001 | | | | | |
| K16 G5-G8 | | −0.02 to −0.05 | | | | | Best of the gap-up group: about flat at 26/day |
| K1, K2, K3, K4, K7, K8, K13, K17 | | | | | | | Negative under every geometry |

## Read-across for the ultimate-setup build
1. A high-volume, any-condition short fade from these precursors is **not supported**. With costs in, the most frequent sets (K2 at 154/day, K16 at 26/day, K1 at 22/day) run from −0.02 to −0.18 R even with the best stop geometry.
2. If a short-fade lane goes forward, build it on the **gap-down pop + SPY-not-rising** context with **wide or time-based exits**: about a 45-minute hold, a stop scaled to today's 15-minute range or a catastrophe stop, never above HOD.
   - Score it once on the check half (2025-10-01 onward).
   - Expect about 2 trades/day and about +0.05 R/trade at best.
   - It is a low-rep lane. It is not the volume engine.
3. Crash/rebound days (2025-04-03..04-09) dominate every extension-fade total. Any fade backtest must report its result with that week removed.
4. Stay above $20 a share. Under $20, costs alone cost 0.1-0.3 R/trade at R0 = 0.25 dATR.

## Configurations tried
- 240 in total.
  - Pass 1, `analyze.py`: 2 baselines, 52 marginal cells, 17 combos × 4 geometries = 121.
  - Pass 2, `supp.py` / `supp_analyze.py`: 17 sets (16 combos + control) × 7 geometries = 119.
- K15-K17 were added after a partial look at the marginals (gap ≥ 3 was the least-bad bucket). They are counted like the rest.
- The pass-2 geometries were declared after pass 1, as a remedy for the stop failure. They are counted too.

## Files
- Scripts: `research/ultimate_1119/movehunt_short/build.py`, `analyze.py`, `supp.py`, `supp_analyze.py`.
- Results: `cells.csv` (pass 1), `supp_cells.csv` (pass 2).
- Pass-2 row table (13 MB, outside the repo): `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mhs_supp_rows.parquet`.
- The per-symbol temp tables (`mhs_tmp`, 1.3 GB) were deleted.

Rule-change context: this is research on historical bars only. No live rule or config change is involved, and nothing here touches live setups. Educational only — not financial advice.
