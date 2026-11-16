# Workbench: Gap-Down Recovery Fade (all day) (`L3-gap-slope-fromopen-FD`)

Teardown variants of `L3-gap-slope-fromopen-FD`: each changes ONE part and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until backtested under docs/RESEARCH_RULES.md and placed in the testing arena with the owner's yes.

## Log

- 2026-11-16 `L3-gap-slope-fromopen-FD-WB1`: `window` [950, 1500] -> [950, 1300] - Mechanic: entry window ends 13:00 (live entries after 13:00 were 36 trades -13.9R). Status: PASS (RESULTS.md).
- 2026-11-16 `L3-gap-slope-fromopen-FD-WB2`: `cond.gap` -2.6573517322540283 -> -3.2 - Mechanic: deeper gap only; prefilter gap_le set to -3.2 too (kept consistent by hand). Status: PASS (RESULTS.md).
- 2026-11-16 `L3-gap-slope-fromopen-FD-WB3`: `window` [950, 1500] -> [950, 1300] + `cond.gap`/prefilter -> -3.2 - Mechanic combo C1 = WB1 + WB2 (window 13:00 AND gap <= -3.2; module gap and prefilter set by hand). Status: PASS (RESULTS.md).

All 13 configurations tried (incl. 9 failures/not shortlisted): RESULTS.md. Educational only — not financial advice.
- 2026-11-16 `L3-gap-slope-fromopen-FD-WB4`: `window` [950, 1500] -> [950, 1300] - Mechanic RERUN: WB3 + max hold 75 min (time_stop_min 75, time_stop_min_r 99); module gap, prefilter and time stop set by hand. Status: PASS, recommended (RESULTS.md, RERUN section); supersedes WB3.

RERUN 2026-11-16 (supervisor standard): 46 more configurations (round 1-6, `code/decl2.py`), all in RESULTS.md. Educational only — not financial advice.
