# Oct-7 exits study: hard max-loss cap and give-back protection

*Educational only — not financial advice. Everything below is a backtest unless it is labelled live.*

**What was asked (owner, after 2026-10-07):**
1. Should every trade have a hard max loss, e.g. −1.5%?
2. Are we leaving profit on the table? NEOG, WHR and RIOT showed gains that disappeared.

**Answer: no change to the stops or exits.**
- None of the 158 configurations passed the pre-declared gate. Every % cap lost money on both train and valid.
- Nothing goes to the locked holdouts. No ledger entry and no backlog promotion follow from this study.

## Failures first

| Family | Configs | Passed | Result (train / valid, Δ against current exits, same entries) |
|---|---|---|---|
| Hard % cap on the stop (portfolio) | 5 | 0 | Every cap lowers $ P/L on valid. Tighter caps cost more: 0.75% −$10,522 / −$1,303; 1.0% −$6,356 / −$907; 1.5% −$3,237 / −$663 (day-clustered t −1.49 / −2.28); 2.0% −$1,251 / −$329; 3.0% +$14 / −$311 |
| Breakeven at +0.5R / +0.75R | 10 | 0 | Win rate falls and expectancy falls (orb20_a −0.08R/trade on valid) |
| Trail 0.5–1R after +0.75–1.5R | 45 | 0 | Flat to negative. Best valid result: heat_fade_short trail 1R after 1R, +0.007R (t 1.0) |
| Scale out half or a third at +0.5R | 10 | 0 | Win rate rises 6–15 points, but expectancy falls on 9 of 10 |
| Give-back lock on closes (peak ≥ x R, fallen to y R) | 40 | 0 | Flat to negative. The best, exhaustion_short (0.5→0), gave +0.017 / −0.004 |
| Give-back lock as a resting stop | 20 | 0 | Flat to negative |
| Late-day profit take (14:30/15:00/15:30 if > 0 or > 0.25R) and a 15:30 control | 28 | 0 | heat_fade_long +0.025 to +0.039R on train (t 1.1–2.0), but −0.048 to +0.002 on valid. On exhaustion_short a 14:30/15:00 profit take costs about −0.17R/trade on train |

**What was counted:**
- 158 configurations in total: 5 caps plus 153 exit rules.
- 29 of them changed nothing (for example, a trail that starts at 1.5R on a setup whose target is closer).
- Across the whole exit lineage there are now 489 + 158 = 647 configurations.

**Expected false positives:**
- At p = 0.05, about 8 lucky passes would be expected among 158 configurations.
- No exit configuration reached +0.03R per trade on valid at all. Only 2 reached it on train, both heat_fade_long 15:30 exits, and both are flat on valid.

**Near-misses, not sent to the holdouts.** Each misses the +0.03R valid bar, the plateau check or both:

| Setup | Rule | Train ΔR / t | Valid ΔR / t |
|---|---|---|---|
| heat_fade_short | cap the stop at 2.0% | +0.028 / 2.28 | +0.002 / 1.88 |
| heat_fade_long | flat at 15:30 | +0.039 / 2.01 | +0.002 / 0.08 |
| exhaustion_short | give-back lock 0.5R→0 | +0.017 / 1.27 | −0.004 / −0.09 |
| intraday_momentum | scale out a third at 0.5R | +0.013 / 1.99 | −0.014 / −1.16 |

Rule 18 lineage look 2 would need t ≥ 1.5 on both holdouts. None of these is close on valid.

## Setup and data (rules 1–8)

**Data and code:**
- Entries are exactly those `Backtester.run` makes for the five live setups. `collect.py` reproduces its loop; 2,241 signals on 2026-07-15..09-15, and the set is identical to `research/exits/data/signals.pkl`.
- Fills, costs and stop-first ordering use `engine.simulate`. `sim.py` is a line-for-line copy plus three research-only rules, and it was verified identical to `engine.simulate` on all 2,241 signals (0 mismatches).
- Sizing uses the production `Backtester.allocate` with config/default.yaml: 160 slots, about $1,930 per slot, 0.25% risk cap.
- Train runs to 08-25 and valid is 08-26..09-15. Locked dates were never loaded.

**Baseline (current exits):**
- Train: 1,626 trades, +0.109R/trade, +$8,770.
- Valid: 437 trades, +0.076R/trade, +$1,209.
- By setup, on valid: orb20_a +0.05R, heat_fade_short +0.18R, heat_fade_long −0.06R, exhaustion_short +0.15R, intraday_momentum +0.03R.

**Units (R-unit trap, see EXIT_STUDY.md):**
- 85% of positions are slot-bound. A tighter stop does not shrink the dollars at risk; it only makes R smaller.
- All deltas are therefore in **original-R units** (`r0`: P/L ÷ shares × the setup's own stop distance) and in $ at the fixed slot size.

**Statistics:**
- t is day-clustered: the paired daily Δ is summed per day, and t = mean / sd × √days.
- "ex-best" removes the day that contributed most to the delta.

**Pre-declared gate:**
- ΔR0 ≥ +0.03 on both train and valid.
- train t ≥ 1.0.
- Δ positive without the best day on both splits.
- Δ$ > 0 on both splits.
- Every neighbouring setting in the grid positive on train (the plateau check).

## Why a hard % cap hurts here, and how this squares with MarcoFlow

**The stops are set by volatility, not by a fixed %.**
- R is 0.25 × daily ATR, or 0.5 × the opening range for orb20_a. Median stop distances: orb20_a 2.2%, heat_fade_short 1.2%, heat_fade_long 1.4%, exhaustion_short 2.0%. The 90th percentiles are 2.6–5%.
- A 1.5% cap puts the stop inside normal noise on volatile names. That turns trades that would have recovered into stop-outs: the win rate drops from 55% to 50% and $ P/L falls.

**Recovery table (`results.json` → `recovery`), all 2,063 baseline trades Jul 15–Sep 15:**

| Down at some point by | Trades | Closed green | Average final return | Holding vs exiting at −x% |
|---|---|---|---|---|
| 1.0% | 814 | 29.9% | −0.61% | +0.39% |
| 1.5% | 478 | 23.6% | −1.09% | +0.41% |
| 2.0% | 285 | 18.6% | −1.60% | +0.40% |

- This matches MarcoFlow's pattern: few trades turn green, but the average one recovers partly.
- On our trades, holding beat cutting at −x% by about 0.4% of notional on average, before the slippage a market cut would also pay.

**The exception is heat_fade_short.**
- Its trades that fall 1% or more keep falling: holding is −0.16% worse than cutting at −1%, and −0.39% worse than cutting at −1.5%.
- That is why it is the only setup where a cap was positive on train (+$1,272 at 1.5%, +$1,119 at 2%).
- It failed on valid: 1.5% gave −$233, and 2% gave +$13 (+0.002R).
- It goes to the backlog as a heat_fade_short-only stop-size idea. It is not a portfolio rule.

**The real max-loss control already exists.**
- Sizing is the lesser of 0.25% of equity ($250) and the slot ($1,930 notional), so no trade can lose much more than about $250 plus gap and slippage.
- The worst live loss on 10-06/07 was HESM at −$71.
- Wide-stop names are not worse per trade. On train, orb20_a trades with a stop above 3% made +0.15R/trade (n = 69), and heat_fade_long +0.28R (n = 78).

## Give-back: what the data says about "leaving profit on the table"

**How often a good start turns into a loss:**
- Trades that reached +0.5R closed at or below zero 11% of the time (exhaustion_short), 21% (heat_fade_short and heat_fade_long) and 27% (orb20_a).
- Those trades kept +0.54 to +0.61R on average.

**Why the protections lose money:**
- Breakeven stops, trails, scale-outs and locks all cut the winners that dip and then go on to the target, and that loss is larger than what they save.
- They raise the **win rate** (scale-out: 54% → 68%) while lowering **$ per trade**. This is the trade-off the owner was worried about ("too many safety nets").

**On WHR-type trades (late-day profit take):**
- exhaustion_short's edge comes late in the day. Taking profit at 14:30 or 15:00 cost about −0.17R/trade on train, and 15:30 cost −0.023 / −0.003.
- So the live WHR case (peak +0.89R near 15:20–15:35, closed −0.64R) cannot be fixed by a time rule without giving up more on other days.

## Live days 2026-10-06/07: diagnosis only, not evidence (2 days)

`live_days.py` replays all 60 live paper trades on SIP 1-minute bars with their live stop and target. The fill is approximated by the open of the entry minute's bar. Output: `live_days.csv`.

**Exit-time bug:**
- On 10-07, live positions were closed at 16:04–16:06, not at the planned 15:55. The planned rule is the `flatten_by` 15:55 setting.
- "Flatten fix, part 2" (#8) was merged at 16:11 ET on 10-07, after that session.
- **Housekeeping check for 10-08:** confirm that every position is flat by 15:56. The backtest assumes 15:55.

**Where a rule would have helped, it was one trade at a time:**
- A 1.5% cap would have cut HESM to −0.21R (instead of −0.52R), PENG to −0.47R (−0.60R), BKV to −0.61R (−1.05R) and CEG to −0.49R (−1.01R).
- Over Jul–Sep the same rule cost −$3,237 (train) and −$663 (valid).
- Give-back rules would have saved ALAB (peak +0.95R, closed −1.02R), the second CHTR trade (peak +0.72R, −1.10R) and NEOG (peak +0.55R, −0.20R).
- The same rules would have cut WDAY, ARM, KLAC and DHR, which went on to their targets. Over Jul–Sep they were net negative.

**Trades no exit could fix:**
- CHTR heat_fade_short (09:50) never moved in our favour: the peak was 0.00R.
- ILMN peaked at +0.32R, RIOT at +0.33R and RDW at +0.04R.
- These are entry or direction questions, which belong to the autopsy and setup agents.

**Live stop slippage was worse than the model:**
- CHTR −1.27R and ILMN −1.16R live, against about −1.03R simulated.
- This is already in the backlog as a stop-slippage calibration item.

## Files
- `collect.py`: signal and bar collection, identical to the Backtester loop.
- `sim.py`: `simulate2`, which is `engine.simulate` plus gb / lock / late rules (research only).
- `study.py`: the pre-declared grid, the cap study, allocation, the gate and the plateau check. Output: `results.json`.
- `live_days.py` and `live_days.csv`: the live-day replay.
- `data/` (gitignored): `sigs.pkl` and `baseline_trades.csv`.
