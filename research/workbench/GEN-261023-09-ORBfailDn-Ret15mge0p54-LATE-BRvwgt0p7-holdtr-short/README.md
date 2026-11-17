# Workbench: Generated: Late Failed-Breakdown Pop Short (`GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short`)

Teardown variants of `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short`: each changes ONE part (WB3/WB4 = counted combos) and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until placed in a testing account after the close (ledger + assignments).

## Log

- 2026-11-17 `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short-WB1`: window -> [1430, 1500] - Mechanic: P6/P7 entry window start 14:00 -> 14:30.
- 2026-11-17 `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short-WB2`: cond.ret3_atr (new sensor) -> >= 0.20 - Mechanic: new sensor P11b - the 15-minute pop must also be >= 0.20 daily ATRs (size relative to the stock's own range, not only 0.54%).
- 2026-11-17 `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short-WB3`: window + cond.ret3_atr (combo WB1+WB2) -> window 1430-1500 AND ret3_atr >= 0.20 - Mechanic combo = WB1 + WB2 (each passed alone); counted as its own config; module set by hand.
- 2026-11-17 `GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short-WB4`: window + cond.ret3_atr + cond.adx7 (combo WB3 + new layer) -> window 1430-1500 AND ret3_atr >= 0.20 AND adx7 >= 44 - Mechanic combo = WB3 + new layer P11c ADX(7) >= 44 (experimental layer; fails alone, helps on top of WB3); counted as its own config; module set by hand.
- 2026-11-17 results: WB1..WB4 all PASS vs the parent on the replay (17 sessions 10-23..11-16) and the 2-year backtest (RESULTS.md); WB4 recommended for Testing 1, first in setup_order, pending after close (NOT applied). 151 configurations counted. Only 10 live trades in 1 session: the verdict rests on the 2-year backtest.

Educational only — not financial advice.
