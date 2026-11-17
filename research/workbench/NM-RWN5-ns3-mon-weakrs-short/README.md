# Workbench: Monday Weak-RS NS3 Short (near-miss) (`NM-RWN5-ns3-mon-weakrs-short`)

Teardown variants of `NM-RWN5-ns3-mon-weakrs-short`: each changes ONE part (WB3 = a counted combo) and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until placed in a testing account after the close (ledger + assignments).

## Log

- 2026-11-16 `NM-RWN5-ns3-mon-weakrs-short-WB1`: cond.volumeRatio (new sensor) -> >= 0.45 - Mechanic: new sensor P9b, the VWAP-reclaim bar's volume >= 0.45 x its 20-bar average (module edited by hand: spawn cannot add a sensor).
- 2026-11-16 `NM-RWN5-ns3-mon-weakrs-short-WB2`: window [950, 1130] -> [1005, 1130] - Mechanic: P6/P14 entry window start 09:50 -> 10:05 (config window and the module's own tod bound edited together).
- 2026-11-16 `NM-RWN5-ns3-mon-weakrs-short-WB3`: volumeRatio >= 0.45 AND window 1005-1130 - Mechanic combo = WB1 + WB2; counted as its own config.
- 2026-11-16 results: WB1, WB2, WB3 all PASS vs the parent on the replay (21 sessions 10-19..11-16; the parent trades the 5 Mondays) and the 2-year backtest (RESULTS.md). WB3 recommended for Testing E, first in setup_order, pending after close (NOT applied). 113 configurations counted. Very few live trades (8 in 3 sessions): the verdict rests on the 2-year backtest.
