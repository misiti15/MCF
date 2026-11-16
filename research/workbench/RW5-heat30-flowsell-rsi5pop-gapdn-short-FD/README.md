# Workbench: Gap-Down Pop Fade (all day) (`RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`)

Teardown copies of `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` (Primary). Each copy is a new setup (new id, parent link); the parent is never edited. Copies are research only until deployed under research/workbench/RULES.md.

## Log
- 2026-11-16 `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB1`: NEW gate — skip when SPY is up > +0.30% since the 09:50 bar close (module clause, `context: [spy_fo]`). Status: PASS (contained in WB3).
- 2026-11-16 `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB2`: P20/intake — stop-exit cost (2 x (1c + 1 bp) + 2c) <= 0.15 of 1R (module clause). Status: PASS (contained in WB3).
- 2026-11-16 `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3`: SPY-since-09:50 gate 0.20% + cost/R <= 0.15 + window [1015, 1500]. Status: PASS, recommended for Testing D (pending after close, not applied).

Files: DIAGNOSIS.md (every part P1..P26, 5 worst + 5 best live trades, all-trades analysis), RESULTS.md (all 38 configurations, side by side, deploy plan), variants.jsonl, modules/, *.yaml stubs (no account loads them), code/ (bench reused from the L3 Workbench job), results_all.csv, extras.csv, component_analysis.txt, PNGs (engine, worst1-5, best1-5).

Educational only — not financial advice.
