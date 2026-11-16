# Workbench: Failed Opening-Range-Low Break Long (0.1 ATR) [fill] (`CWT14-failbrk-orl-p10-long`)

Teardown variants of `CWT14-failbrk-orl-p10-long`: each changes ONE part and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until backtested under docs/RESEARCH_RULES.md and placed in the testing arena with the owner's yes.

## Log

- 2026-11-16 `CWT14-failbrk-orl-p10-long-WB1`: `r_atr_frac` 0.25 -> 0.3 - P15 1R 0.25 -> 0.30 x daily ATR (stop and +0.5R target both 20% wider; fewer cost-eaten small-R trades). Status: research only; next: backtest.
- 2026-11-16 `CWT14-failbrk-orl-p10-long-WB2`: `window` [950, 1200] -> [1030, 1200] - P5 window start 09:50 -> 10:30 (skips the 10:05-10:30 reclaim bars). Status: research only; next: backtest.
- 2026-11-16 `CWT14-failbrk-orl-p10-long-WB3`: atr_d / close >= 0.02 - P1 intake: extra filter daily ATR >= 2.0% of price (thin-R names: costs eat the +0.5R target). Status: research only; next: backtest.
- 2026-11-16 `CWT14-failbrk-orl-p10-long-WB4`: r_atr_frac 0.3; ATR% >= 2.0 - combined copy of WB1 + WB3 (each passed alone); counted as its own config. Status: research only; next: backtest.
- 2026-11-16 results: WB1, WB2, WB3, WB4 all PASS vs the parent on the replay and the 2-year backtest (RESULTS.md; all still negative after costs). WB4 recommended for Testing 1, pending after close.
- 2026-11-16 rerun (supervisor standard) `CWT14-failbrk-orl-p10-long-WB5`: WB4 + cost/R <= 0.10 intake + SPY since 09:50 >= -0.20% gate + stop 0.45 ATR / target 0.15 ATR (module GEOM "S"). Replay -0.007R, 2-year -0.027R (parent -0.188 / -0.127, WB4 -0.101 / -0.079). Recommended instead of WB4 (Testing D, normal priority, after close). 60 more configs (76 in all). RESULTS.md "Rerun".
