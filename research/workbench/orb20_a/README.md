# Workbench: 20-Minute Opening Range Breakout (`orb20_a`)

Teardown variants of `orb20_a`: each changes ONE part and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until backtested under docs/RESEARCH_RULES.md and placed in the testing arena with the owner's yes.

## Log

- 2026-11-16 `orb20_a-WB1`: `top_n` 20 -> 10 - P4 stocks in play: top 20 -> top 10 by 09:30-09:49 rvol. Status: research only; next: backtest.
- 2026-11-16 `orb20_a-WB2`: `min_price` 5.0 -> 20.0 - P2 price floor: prior close >= 20 USD (class floor 5). Module copy modules/orb20_wb.py (builtin class + min_price). Status: research only; next: backtest.
- 2026-11-16 `orb20_a-WB3`: `top_n+min_price` [20, 5.0] -> [10, 20.0] - combo of WB1 (top 10) + WB2 (price >= 20); own config. Module copy modules/orb20_wb.py (builtin class + min_price). Status: research only; next: backtest.
- 2026-11-16 results: WB1, WB2, WB3 all PASS vs the parent on the replay (26 sessions) and the 2-year backtest; WB3 (top 10 + price >= $20) recommended for Testing A, pending after close: replay +0.072 -> +0.118R, 2-year -0.031 -> +0.015R. 70 configs. RESULTS.md.
