# Workbench: Generated: Lunch New-Low Short (selling) (`GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short`)

Teardown variants of `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short`: each changes ONE part (WB3 = a counted combo) and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until placed in a testing account after the close (ledger + assignments).

## Log

- 2026-11-16 `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short-WB1`: cond.from_pc_atr (new sensor) -> <= -1.3 - Mechanic: new sensor P11b, short only names already down >= 1.3 daily ATRs vs the prior close (module edited by hand: spawn cannot add a sensor).
- 2026-11-16 `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short-WB2`: window [1130, 1400] -> [1130, 1300] - Mechanic: P6/P7 entry window end 14:00 -> 13:00.
- 2026-11-16 `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short-WB3`: from_pc_atr <= -1.3 AND window 1130-1300 - Mechanic combo = WB1 + WB2; counted as its own config.
- 2026-11-16 results: WB1, WB2, WB3 all PASS vs the parent on the replay (15 sessions 10-26..11-13) and the 2-year backtest (RESULTS.md). WB1 recommended for Testing E, first in setup_order, pending after close (NOT applied). 98 configurations counted. Few live trades (21): the verdict leans on the 2-year backtest.
