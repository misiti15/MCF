# Layered-setup swarm (2026-10-06)

*Educational only — not financial advice.*

Owner request: find high-value layered setups that indicate a move, with a high win rate and enough margin to survive slippage and system delays. Basic starts were in scope: overbought/oversold with VWAP and moving averages, levels, and volume turning the other way.

**Data:** SIP 5-minute bars for the 1,226 most liquid names, 68 sessions, 5.2M decision bars (09:50–15:00).

**Splits by date:**

| Split | Dates | Used for |
|---|---|---|
| Train | to 2026-08-25 | fitting |
| Valid | 2026-08-26 to 2026-09-15 | choosing finalists |
| Test | after 2026-09-15 | locked; scored once on all finalists |

**Exits:** three geometries, all after costs, with R = 0.25 × daily ATR:
- +1R target / −1R stop
- +0.5R / −1R (high win rate; breakeven win rate about 69%)
- +1R / −0.5R

**Search:** five families of miners tried about 855,600 configurations in total. An auditor reproduced every finalist and stress-tested it.

| Family | Result |
|---|---|
| Overbought/oversold + VWAP + MAs | Nothing survived validation. Train winners came from a few broad bounce days. |
| Overbought/oversold at levels (PDH/PDL/HOD/round numbers) | Nothing. Fading levels has no edge after costs. |
| Volume flip / divergence | `volume_flip_1` survived (below). |
| Dips/rips within a trend | Passed train and valid, failed the test. |
| High-win-rate geometry search | Every candidate failed or was marginal. High win rates come from the geometry itself, not the signal. |

## Locked test (Sep 16 – Oct 5), scored once

| Candidate | Side / exit | Train | Valid | Test |
|---|---|---|---|---|
| **volume_flip_1** | short, ±1R | +0.204R | +0.174R | **+0.138R** (n 245, win 43%, PF 1.40, green days 71%) |
| volume_flip_2 (same mask) | short, +0.5/−1R | +0.111R | +0.084R | +0.030R (win 67%, below breakeven) |
| trend_pullback_1 | short, +0.5/−1R | +0.097R | +0.115R | +0.015R (win 70%) |
| trend_pullback_2 | short, +1/−0.5R | +0.168R | +0.141R | −0.028R |
| trend_pullback_3 | short, ±1R | +0.185R | +0.127R | −0.001R |
| obos_levels_1 | short, ±1R | +0.147R | +0.060R | −0.070R |
| win_geometry_1/2/3 | – | +0.17 to +0.26R | +0.02 to +0.19R | +0.02R each |

## Decision
- **exhaustion_short** (volume_flip_1) goes to paper only.
- Rule: 5-minute RSI5 > 90, price more than 1% above the 5-minute SMA20, and a bearish RSI divergence (price at a 20-bar high while RSI is not), 13:00–15:00 ET. Short at the bar close; stop 1R, target 1R, exit 15:55.

## Lesson for the owner's floor
High win rates on their own do not carry margin. trend_pullback_1 won 70% of trades on the test and made +0.015R, which is gone after slippage. The setup that survived wins 43% and makes +0.14R. The gates therefore judge expectancy after costs first, and win rate second.
