# Workbench: Late-Day ETF Dip Buy (near-miss) (`NM-ETF-late-dip-di-long`)

Teardown variants of `NM-ETF-late-dip-di-long`: each changes ONE part and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until backtested under docs/RESEARCH_RULES.md and placed in the testing arena with the owner's yes.

## Log

- 2026-11-16 `NM-ETF-late-dip-di-long-WB1`: cond.ret12 (new sensor) -> >= 0.5 - Mechanic: new sensor P10b - 60-min return (ret12, incl. the dip) >= +0.5%: buy the dip only inside an up-hour (pullback in an uptrend).
- 2026-11-16 `NM-ETF-late-dip-di-long-WB2`: cond.ret3 -> -0.9 - Mechanic: P10 deeper 15-min dip only (ret3 <= -0.90%).
- 2026-11-16 `NM-ETF-late-dip-di-long-WB3`: cond.ret3 + cond.ret12 (combo WB1+WB2) -> ret3 <= -0.90 AND ret12 >= 0.5 - Mechanic combo = WB1 + WB2 (each passed alone); counted as its own config; module set by hand.
- 2026-11-16 results: WB1, WB2, WB3 all PASS vs the parent on the replay (20 sessions) and the 2-year backtest (RESULTS.md); all positive after costs. WB1 recommended for Testing B (explore1), first in setup_order, pending after close (NOT applied). 56 configurations counted. Few live trades (21): the verdict leans on the 2-year backtest.
- 2026-11-17 `NM-ETF-late-dip-di-long-WB4` (FREQ job): ret3 <= -0.75, DI >= -5, ret12 >= -1.0 (new), refire cooldown 1 - more trades per session (replay 1.52 -> 2.52, 2-year 1.30 -> 1.92) at a slightly better avg R; PASS (frequency rule + normal rule), 114 configs; FREQ/RESULTS.md. Pending after close (NOT applied).
