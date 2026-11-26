Educational only — not financial advice

# Consultant memo A: a regime-steered Primary book (2026-11-26, research only, nothing changed)

From: outside consultant (multi-strategy intraday book, regime-aware allocation). To: owner. This is an independent view and it
disagrees with part of the brief.
**What I did and what I did not do:** I read the files in the brief. I ran 0 setup or exit configurations. I ran 5 descriptive what-ifs on live trades:
a day-level hedge (1), Primary without L3 (1), and Primary plus an average long sleeve at k = 6, 12 and 24 lots a day (3).
**Sources:** "Live" = `mcf.report.footrace.live_trades()` (run-1 journals of all 10 accounts, LR8 cost-R, identical signals counted
once), 10-06..11-25. Primary = 37 sessions / 1,520 trades. SPY open-to-close comes from the compass data branch `compass/cond_obs.csv`.
11-13 has no row, so day-level joins use 36 sessions. That file holds locked-block rows; I dropped them by date before computing anything,
so no locked value was used. "Bench" = figures quoted from the named reports (engine labels as in those reports).
**Rule changes inside the live window (ledger):**
- 10-28 Primary sizing; 10-29 −2R latch; 11-11 TEAM-6; 11-12 LR8; 11-17 TSZ1; 11-19 C3 Epoch 1; 11-20 stop rounding;
  11-21 cost-basis fix; 11-23 burst brake and ST7 out.
- Primary's lineup changed several times (MF/NS/heat_fade early on, 4 setups now), so live Primary figures mix rule versions and lineups.

## 1. Diagnosis: the puzzle pieces are index beta with a negative remainder, so steering them amounts to forecasting direction
- **Each sleeve is mostly a bet on SPY.** Arena trades (all non-Primary accounts, live), with the daily average R per trade regressed on SPY open-to-close:
  - longs: slope +0.15R per +1% SPY, R² 0.59, intercept **−0.139R/trade (SE 0.026)**; shorts: slope −0.16, R² 0.41, intercept **−0.169R (SE 0.042)**; long vs short daily averages correlate −0.62.
  - Longs averaged −0.173R/trade and were positive on only 7 of 37 days. 11-25 (+256R on 850 long trades, +0.30R/trade) was one of those beta days.
- **Steering by regime means forecasting the rest of the day.**
  - Break-even for the average long ≈ 0.139 / 0.15 ≈ **SPY +0.9% open-to-close**.
  - That happened on 6% of the 2-year sessions (ex-locked); measured from 12:00, on 3%. "Heading" is a coin flip (compass_5m, compass_learn); only "staying" and volume (Hunch) are readable.
  - REGSW: 0 of 74 switches pass. The gains came from trading less of a losing list. Labels repeat at 31% against 32% chance.
  - No amount of switching assembles a profitable book out of pieces that only pay when the index moves their way.
- **Primary is red even when beta helps it.**
  - Up days −13.7R/day, 83% red (12 days); quiet −6.0R, 75% red; down +4.5R, still 50% red (live, 36 sessions). Day-level intercept −6.1R/day (SE 3.1).
  - Bench at LIVE-L costs: L3, RW3 and RW5 lose about 0.09–0.18R/trade in every window (primshorts_1126).
- **Costs are the real enemy, and the diversification the brief proposes doubles them.**
  - Live all-in cost is ~0.122R/trade (primshorts §1), about the same size as both intercepts. The gross edge is close to zero.
  - Buying beta through long setups pays ~0.12R per lot.
  - A SPY/IWM overlay buys the same beta much more cheaply. On 11-25, 1R ≈ $67 (−$2,853.75 / −42.30R), and a net beta of 19.6R per 1% ≈ $131k of SPY. At ~1 bp round trip that is ≈ $13 ≈ **0.2R for the whole day**, against ~5R of costs on 41 lots. This is an estimate, not a fill model.
- **The owner's idea, tested on live data, adds red days.** I added an average arena long sleeve to Primary each day, at that day's arena long average R:

  | Long lots added per day | 0 | 6 | 12 | 24 |
  |---|---|---|---|---|
  | Red days (of 34) | 23 | 25 | 26 | 26 |
  | Mean R/day | −4.7 | −5.8 | −6.8 | −8.8 |
  | 11-25 | −42.3 | −40.5 | −38.7 | −35.1 |

  Breadth_1125 found the same in the bench: PYR4 is worse than Primary, and the long legs are too small and too weak to hedge.
- **Process gaps:** (1) exposure is never a state variable; only squeeze_1125 measures the book's net beta (B8). (2) Rule 26 guards "day-type on/off switches; hedge promotions; sizing tilts"; your brief is the override, flagged here. (3) "Net positive every day" is not attainable: even a +0.5R/lot bench book is red 11% of days (neveragain_1125).
- **Arithmetic you should see:** while the edge per lot is ≤ 0, cutting variance makes red days *more* frequent, though shallower. Red-day count is set by the edge; risk tools set the depth.

## 2. Design: Primary = an alpha sleeve at static weights + a beta overlay + risk-only switches
**State variables** (point-in-time, read at the close of minute m−1, acted on at minute m):

| Variable | Definition | What it drives |
|---|---|---|
| E (the main one) | Net beta-weighted open R per +1% SPY (the B8 meter: 60-session daily beta, shrunk). It describes *our book*, not a market forecast. | Hedge |
| E_IWM | The same against IWM. Gap-down shorts are small/mid caps, and on 11-25 IWM led. | Hedge-leg split |
| RVOL | SPY realised volatility so far vs the median of the prior 20 sessions | Phase-2 hedge band only |
| Own R | Each setup's own closed + open R today (LATCH-OPEN) | Setup switch |
| Account curve | Account closed + open R (SCALED-K4, SHOCK-V) | Account switch |

The direction variables (compass, SPYO, IDX3, GAP, breadth) stay as journal shadows. They are not steering inputs until a forward test passes.
**Switches (on/off): risk-based only, never forecast-based.**
- Per setup: LATCH-OPEN at −2R. Account: SCALED-K4 flatten, SHOCK-V halt, fixed −20R halt (cards open). No setup is switched off on a market reading.
**Weights:** static and set on Fridays.
- Use shrunk expectancy (C3 rule: n/(n+150) × live + 150/(n+150) × −0.10), checked against the bench at LIVE-L costs.
- L3-fromopen goes to On Deck (or half size), per primshorts option (b).
- Weights do not change with regime until a sleeve with a positive intercept exists. Weighting zero-alpha pieces by regime is the same forecast in different clothes.
**Long/short balance: hedge, don't block (B8 → H8).**
- Target hedge h = −sign(E) × max(|E| − 8, 0) R per 1%, traded in SPY/IWM in proportion to E/E_IWM.
- Rebalance when |h − h_now| ≥ 2R per 1%; unwind as E falls; flatten at 15:55 with the book.
- The difference from B8: B8 blocks entries, takes ~29% fewer lots and costs −154R/yr on the zero-expectancy (Z) book in CHECK. The hedge keeps every lot and removes only the beta.
- Hedge P&L is reported as its own line in R, so it can never hide a directional bet.
**Longs enter Primary only with a positive *beta-adjusted* intercept** (alpha R after regressing on the SPY move during the trade). On that bar, most of the 11-25 winners (all `1 day`) do not qualify.
**Overfitting control** (24 Primary sessions and ~1.4 sessions per lineup version is too few to fit anything):
- Parameters fixed in advance: B = 8 (squeeze_1125 grid), beta from the existing squeeze code, band 2R. No live-mined labels (STOP2(2)).
- Score on the 861-session bench with the Z book as the main lens (the hedge's job is depth, not R); live only as a parity replay.

## 3. The minimum test that would convince me: HEDGE-B
**Pre-register before scoring** (sha256 in the PREREG file).
- Engine: the squeeze_1125 / neveragain minute book engine. Lineup P4 under Primary book rules plus LATCH-OPEN; LIVE-L costs on stocks.
- Hedge leg cost: 0.5 bp half-spread + 0.5 bp slippage per side on traded notional + LR8 fees; next-bar fills.
- Configs, N = 2: **H8** (B = 8, SPY/IWM split) and **H4** (B = 4, near-full). References (not counted): LO (base), LO+B8 (block).
- Placebo: H8 with each day's SPY/IWM paths swapped for a random other bench day's (20 draws, seed 1126).
- Cumulative N ≈ 2,271 → 2,273. The family bar is stated descriptively at ≈ 3.9.
- Splits as squeeze_1125: FIT 2024-10 + 2025-03..09 (confirmation only, nothing tuned), CHECK 2025-10-01..2026-11-04, T2 2023-01..2024-09-13.
  The locked block 2024-11-01..2025-02-28 is filtered at load and asserted.
**Pass:** every item must hold on CHECK and on T2 separately.
1. Z book: worst-5 days ≥ 30% shallower than LO, and days ≤ −10R down ≥ 40%.
2. Z book: dR/yr ≥ −15R (the hedge must be close to free; B8 was −154).
3. Book where every lot earns +0.10R: dR/yr ≥ −15R, and red days up by no more than 2 pp.
4. Worst-5 improvement above the placebo's 90th percentile. Hedge-leg P&L on Z within ±1 SE of its costs.
5. Best-day share of the improvement < 50%. Per setup: each setup's hedge P&L, split by its share of E, is reported better / worse.
6. Live replay 10-23..11-25 (Alpaca SIP 1-min): worst-5 improves, and no day is worse by more than 3R.

If it passes: run a 20-session journal-only `hedge_shadow` in Primary (the hedge path priced from real quotes, no orders). Then the Friday epoch, skeptic review, ledger entry and `ledger check`.
Buying power is the binding real-world limit (~$250k gross on 11-25 against ~$336k at 4×). The engine must model it or report it.

## 4. What not to do
- Don't add the 11-25 long winners to Primary as "diversifiers". All are `1 day`; GEN-261023-07 is −0.297R without its best day. On average, longs add red days (table in §1).
- Don't steer by compass or direction. On 11-25 the compass gate would have blocked 0 of 41 Primary trades and −189R across accounts (owner inbox); IDX3-P's +31.6R on 11-25 is 177% of its Primary forward total (+17.9R, 10 sessions; shadow_scoreboard.csv).
- Don't fit per-setup regime labels or weights from live data. REGX labels repeat at 31% against 32% chance.
- Don't present caps that trade less of a losing book as skill. B8: Z −154R/yr, all 3 shorts worse.
- Don't tilt sizing by day type. Size-up tiers lost 33–47R in the test half.
- Don't count red days as the objective while the edge is ≤ 0. Use worst-5, days ≤ −10R and the beta-adjusted intercept.

## 5. Top 3, ranked by expected effect on red days per month
Baseline: live Primary is red on 25 of 36 sessions (≈ 14.6 of 21 per month).
Rough mapping: −0.11R/lot gives ~70% red and break-even gives ~50% (neveragain), so **≈ 0.4 fewer red days a month per +0.01R/lot**.
1. **Raise the edge per lot: L3 → On Deck, with LATCH-OPEN** (open cards).
   - Bench: +0.77R/session on CHECK and +0.36 on T2 (t 3.4 / 3.7). Over the ~29 remaining lots a session that is ≈ +0.03R/lot, so **≈ −1 red day/month** (bench-derived, rough).
   - Live it is noise (without L3: red 27 of 37 vs 26 of 37; worst-5 −51 → −41R). It is the only lever here that moves the count.
2. **Beta overlay H8, replacing the B8 block** (after HEDGE-B passes).
   - Red days ≈ 0 to −1/month now. It could even add one while the edge is below 0.
   - Depth: B8's bench tail cut (worst-5 −47% on CHECK and −22% on T2; days ≤ −10R 38→15 and 21→4) is the ceiling, without B8's lot cost.
   - On 11-25 it would have removed most of the −34.9R market component of the swing (≈ −42 → ≈ −20R at B = 8; estimate, beta error ignored).
   - It is the precondition for any long sleeve: red days fall once the edge is above 0.
3. **Put a beta-adjusted alpha column on every promotion and admit longs only with a positive intercept** (reporting first, 0 configs).
   - Effect: it prevents the +~2 red days/month that a beta-long sleeve adds (live what-if, 12 lots/day: 23 → 26 of 34).
   - It points the GEN restart and Pyramid at residual alpha instead of at the index.

Run HEDGE-B first. It is cheap, it uses existing engine code, and it tells you whether balance can be bought for ~0.2R a day instead of with lots.

Educational only — not financial advice
