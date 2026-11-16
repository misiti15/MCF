# Workbench: Gap-Down Bounce-off-Low Fade (all day) (`L3-gap-slope-lowdist-FD`)

Teardown variants of `L3-gap-slope-lowdist-FD`: each changes ONE part and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until backtested under docs/RESEARCH_RULES.md and placed in the testing arena with the owner's yes.

## Log

- 2026-11-16 `L3-gap-slope-lowdist-FD-WB1`: `cond.dist_lod_atr` 0.7816761255264282 -> 0.82 - Mechanic: bounce must be > 0.82 daily ATR off the low (was 0.78). Status: PASS (RESULTS.md); not deployed (in WB4).
- 2026-11-16 `L3-gap-slope-lowdist-FD-WB2`: `time_stop_min` None -> 75 - Mechanic: max hold 75 min (P26), set by hand. Status: PASS (RESULTS.md); not deployed (in WB4).
- 2026-11-16 `L3-gap-slope-lowdist-FD-WB3`: `cond.rsi5` (new layer) -> >= 50 - Mechanic: new entry layer, set by hand. Status: PASS (RESULTS.md); not deployed (in WB4).
- 2026-11-16 `L3-gap-slope-lowdist-FD-WB4`: `cond.dist_lod_atr` 0.7816761255264282 -> 0.82 - Mechanic combo R08 = WB1 + WB2 + WB3 (dist_lod > 0.82 AND rsi5 >= 50 AND max hold 75 min; rsi5 layer and time stop set by hand). Status: PASS, recommended for Testing F (pending after close; RESULTS.md).

All 54 configurations tried (incl. failures): RESULTS.md. Educational only — not financial advice.
