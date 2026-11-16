# Workbench: Generated: Late Pullback Buy (MACD rising) (`GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long`)

Teardown variants of `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long`: each changes ONE part and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until backtested under docs/RESEARCH_RULES.md and placed in the testing arena with the owner's yes.

## Log

- 2026-11-16 `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long-WB1`: `window` [1400, 1500] -> [1400, 1430] - Mechanic: P5 entry window end 15:00 -> 14:30 (signals in the first 30 minutes of the late window only). Status: research only; next: backtest.
- 2026-11-16 `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long-WB2`: `min_adv` 20000000 -> 100000000 - Mechanic: P2 liquidity floor 20-day avg dollar volume $20M -> $100M. Status: research only; next: backtest.
- 2026-11-16 `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long-WB3`: new gate: breadth change since 09:50 <= +0.20 - Mechanic: new gate P11b - skip when the share of stocks above VWAP has risen more than 0.20 since the 09:50 bar (broad rally / squeeze afternoons). Status: research only; next: backtest.
- 2026-11-16 `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long-WB4`: combo WB1 + WB3: window 14:00-14:30 AND breadth change since 09:50 <= +0.20 - Mechanic combo = WB1 + WB3 (each passed alone); counted as its own config; module set by hand. Status: research only; next: backtest.
- 2026-11-16 `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long-WB5`: combo WB1 + WB2 + WB3: window 14:00-14:30 AND min_adv $100M AND breadth change since 09:50 <= +0.20 - Mechanic combo = WB1 + WB2 + WB3 (each passed alone); counted as its own config; module set by hand. Status: research only; next: backtest.
- 2026-11-16 results: WB1..WB5 all PASS vs the parent on the replay (14 sessions) and the 2-year backtest (RESULTS.md); WB5 (window 14:00-14:30 + ADV >= $100M + breadth change since 09:50 <= +0.20) recommended for Testing D (testingd), first in setup_order, pending after close (NOT applied). 106 configurations counted. Few live trades (16): the verdict leans on the 2-year backtest.
