# Diagnosis: Failed Prior-Day-Low Break Long (0.1 ATR, low volume) [fill] (`CWT14-failbrk-pdl-p10-lowvol-long`)
Mechanic, 2026-11-16 (built after the close; research files only, no config touched). Educational only — not financial advice.

Leaderboard rank 26. The parent runs in **Testing D** (since session 2026-11-12). Its live record is used here **for diagnosis only**.
The owner's rule (2026-11-16) is that the pass decision uses the identical backtests, never the parent's live stats.
- **Live record:** 408 closed trades over 26 sessions (2026-10-12..11-16), avg -0.020R after costs, win 67%, avg R w/o best day -0.050R. The brief's 389 / 25 / -0.012R is the same record one session earlier.
- **By account:** Testing 2 / Testing A 240 trades at -0.09R, Primary 78 trades at -0.01R, Testing D 90 trades at +0.16R.
- **Exit mix:** target 267, stop 120, flatten 21.

**Rule changes inside the window (CLAUDE.md rule-change context):**
- 10-21: moved Testing 2 -> Primary.
- 10-23: testing-account per-setup latches off.
- 10-28: Primary -> Testing 2, Primary size ~$5,000 / ~$4,000.
- 10-29: Primary -2R latch.
- 11-12: LR1 flatten time, LR3 R-after-costs halts, LR5 position check and LR7 flatten retries; LR8 live cost model; moved to Testing D (D/E/F fill).

So the record mixes three accounts with different sizing and latches. Testing D (+0.16R, 4 sessions) is too short to read on its own.

Engine: `CWT14-failbrk-pdl-p10-lowvol-long_engine.png` shows parts P1..P22, with the full blueprint in `CWT14-failbrk-pdl-p10-lowvol-long.md`. Catalogue parts are named in [brackets].

## The 5 worst and 5 best live trades
Charts: `..._worst{1-5}_*.png` and `..._best{1-5}_*.png`. Each chart prints the entry and exit prices and times, the stop, the target, MFE / MAE and lettered part callouts.
- **Backtest rows:** found for 7 of the 10 trades. BRX, MGY and BTDR have no backtest signal on that day: the stored lab frame did not flag the bar (frame / volume-ratio difference). They cannot be scored.
- **Columns in the tables below:** "sim" is the backtest engine on the same signal. "WB1" is the wider stop. "WB3" is the wider stop plus the gap <= -0.5% intake.

### Worst trades
| Trade | What happened | Part responsible [catalogue] | What a small tweak does to THIS trade |
|---|---|---|---|
| 1 RIG 10-22 -1.33R | $5.83, ATR $0.23 (3.9%). 1R was $0.07 and costs were 0.72 of 1R. MFE +0.29R at 10:21 crossed the +0.26R target level but the target **did not fill** live, then the stop hit at 10:32. The backtest engine takes the target (+0.03R). | P16 1R / P13 cost filter [Entry/sizing]; live target fill | WB1 sim +0.02R (target). WB3 skips it (gap -0.17%). The sibling's cost/R <= 0.10 would skip it. |
| 2 NTNX 10-14 -1.27R | Gap -0.77%. Reclaim of only 0.043 ATR. SPY was -0.40% since 09:50. The price never rose (day MFE 0.01 ATR, MAE 1.62 ATR): a real failed reclaim. | P8 sensor [Sensors]; market state [Gates] | WB1 / WB3 -1.11R instead of -1.23R (sim). The sibling's SPY >= -0.20% gate would skip it. |
| 3 BRX 10-14 -1.25R | No backtest signal (frame difference) | — | not scorable |
| 4 TSLG 10-22 -1.24R | $5.12, ATR 6.3%, gap -6.2%. The close was only 0.002 ATR above the prior-day low (a barely-there reclaim). Costs 0.51 of 1R. | P8 reclaim [Sensors] + P13 cost [Intake] | WB1 / WB3 -1.31R instead of -1.59R (sim). A reclaim >= 0.05 ATR or cost/R <= 0.10 would skip it. |
| 5 MGY 10-15 -1.23R | No backtest signal | — | not scorable |

### Best trades
| Trade | What happened | Part | Tweak effect |
|---|---|---|---|
| 1 TEVA 10-20 +3.74R | Filled 43 bps under the signal close, which left a live 1R of $0.09 against $0.27 from the ATR. **R is inflated by the fill**: the same trade is +1.26R in sim. | P16 1R definition | WB1 +0.55R (bigger denominator). WB3 skips it (gap +0.47%). |
| 2 BTDR 10-15 +1.49R | no backtest signal | — | — |
| 3 PPL 10-27 +1.07R | Normal target hit after 55 minutes | — | WB1 +0.44R. WB3 skips it (gap +0.11%). |
| 4 UBER 10-12 +1.07R | Normal target hit | — | WB1 +0.24R. WB3 skips it (gap -0.48%, just short of -0.5%). |
| 5 IP 10-21 +1.06R | Normal target hit; SPY -0.31% since 09:50 | — | WB1 +0.53R. WB3 skips it (gap +0.34%). The SPY gate would also skip it. |

**Reading the 10 trades:**
- 2 of the 5 worst are thin-R cheap names, the same fault the sibling found: RIG and TSLG, both near $5, with costs at 50-70% of 1R.
- 1 is a real failed reclaim on a falling market: NTNX.
- The best trades are ordinary 0.5R targets. Live R is stretched by fills under the signal close.
- **WB3's gap intake skips 4 of the 5 best live trades and only 1 of the 3 scorable worst trades.** On this evidence the live top-5 is not where the gap filter earns. Across all 293 live trades that match a backtest signal, the gap <= -0.5% group was -0.079R against -0.104R for the rest: better, but both negative.

## All live trades (component analysis, 408 trades)
- **Time of day:** 10:00-10:30 entries made +0.118R (173 trades). Entries after 12:00 lost -15.3R over 47 trades (-0.33R). The 2-year test does **not** confirm the afternoon: end 12:00 gives -0.116R and end 13:00 gives -0.114R, against the parent's -0.114R.
- **Hold time:** holds over 60 minutes lost 34R over 148 trades. The 2-year test with max hold 60 / 120 min is -0.113R / -0.113R, so nothing is gained.
- **Stops:** 29 of the 120 live stops had first reached at least +0.3R. In the 2-year test, 38% of the 8,271 stopped trades reach the target level later the same day. **The stop sits inside the noise.**
- **Cost / ATR:** live, low-ATR names did better (+0.4R) and high cost/R did better. Both are distorted by the fill-shrunk R denominator. The 2-year test shows the opposite: cost/R in its top fifth is -0.219R and in its bottom fifth -0.026R. Low daily ATR% is the worst bucket in R terms.

## All backtest trades: which part is responsible (2-year, parent, 25,439 trades)
The signal has no strong edge anywhere. Every fifth of reclaim, poke, RSI(5), flow, buy pressure, VWAP distance, SMA20 distance, volume ratio and SPY state is negative (between -0.06R and -0.16R). The levers that move it:
1. **P19 stop (brakes): the main fault.** A 0.25 ATR stop under the signal close catches 33% of trades, and 38% of those later reach the target.
   - Widening the stop to 0.45 ATR (target unchanged in price) lifts avg R -0.114 -> -0.058 (2-year) and -0.079 -> -0.047 (replay).
   - Per dollar traded the gain is small: 2-year -7.4 -> -6.8 bps, and the replay is worse (-5.4 -> -8.0 bps). Much of the R gain is the bigger denominator, as the sibling also found.
2. **P1 intake: cost and thin R.** The cheapest-to-trade fifth by cost/R loses only -0.026R (-4.7 bps).
   - Cost/R <= 0.10 (the sibling's part) gives 2-year -0.080R but replay -0.083R (no gain).
   - On the wider stop it hurts the replay: -0.047 -> -0.068R.
3. **Gap (stock-level intake).** Names that gapped down >= 1% lose least: -0.070R and -4.9 bps.
   - Measured honestly, the gain is **day mix**: gap-down names that reclaim yesterday's low cluster on up days. Within each day type the gap filter is no better (paired by day vs WB1: -0.009R).
   - It is a stock intake known at the open, not a market-state gate. Still, its effect works like a market-regime tilt.
4. **Market-state gates measured after 09:50** (owner direction rule):
   - SPY since 09:50 >= -0.20%: 2-year flat (-0.116R), replay better (-0.064R).
   - SPY in the upper 70% of its 09:30-09:50 range, or above VWAP: 2-year -0.108 / -0.107R, replay -0.048 / -0.052R.
   - Stacked on the wider stop and the gap intake, they all hurt the 2-year test (-0.052 / -0.053R against -0.046R). Not used.

## Candidate tweaks picked (one part each, then the combination)
- **WB1, P19 stop:** 0.45 x ATR, target unchanged. This is the sibling's wider-stop part, without its target change.
- **WB2, P1 intake:** gap <= -0.5%.
- **WB3:** WB1 + WB2.

Sibling (`CWT14-failbrk-orl-p10-long` WB5) parts tested here as the brief asked:
- **Cost/R <= 0.10:** not kept, because the replay gets worse.
- **SPY since 09:50 >= -0.20%:** not kept; flat over 2 years and replay-worse inside combinations.
- **Stop 0.45 ATR:** kept, as WB1. The +0.15 ATR target is not needed: -0.060 vs -0.058R over 2 years.
- **The whole WB5 bundle here:** -0.046R over 2 years (matches WB3) but -0.070R on the replay (WB3 -0.034R).
