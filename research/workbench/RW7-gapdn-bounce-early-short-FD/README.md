# Workbench: Gap-Down Early Bounce Short (all day) (`RW7-gapdn-bounce-early-short-FD`)

Teardown copies of `RW7-gapdn-bounce-early-short-FD` (Testing F). Each copy is a new setup (new id, parent link); the parent is never edited. Copies are research only until deployed under research/workbench/RULES.md.

## Log
- 2026-11-16 `RW7-gapdn-bounce-early-short-FD-WB1`: P6 `window` [950, 1500] -> [950, 1300] (spawned with `python -m mcf.research.workbench spawn`). Status: PASS (contained in WB3).
- 2026-11-16 `RW7-gapdn-bounce-early-short-FD-WB2`: NEW gate — skip when SPY is up > +0.10% since the 09:50 bar close (module clause, `context: [spy_fo]`). Status: PASS (contained in WB3).
- 2026-11-16 `RW7-gapdn-bounce-early-short-FD-WB3`: SPY since 09:50 <= +0.10% + SPY last 30 min <= +0.20% + gap < -0.5% + window [950, 1300]. Status: PASS, recommended for Testing E (pending after close, not applied).

Files: DIAGNOSIS.md (every part P1..P27, 5 worst + 5 best live trades, all-trades analysis), RESULTS.md (all 65 configurations, side by side, deploy plan), variants.jsonl, modules/, *.yaml stubs (no account loads them), code/ (bench reused from the RW5 / L3 Workbench jobs), results_all.csv, extras.csv, component_analysis.txt, PNGs (engine, worst1-5, best1-5), RW7-gapdn-bounce-early-short-FD.md (blueprint).

Educational only — not financial advice.
