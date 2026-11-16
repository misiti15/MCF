# Workbench: Early Sellers, Mid-High RSI (all day) (`MF2-open-rsimidhi-flowsell-FD`)

Teardown copies of `MF2-open-rsimidhi-flowsell-FD` (On Deck). Each copy is a new setup (new id, parent link); the parent is never edited. Copies are research only until deployed under research/workbench/RULES.md.

## Log
- 2026-11-16 `MF2-open-rsimidhi-flowsell-FD-WB1`: NEW layers — skip a rising 20-SMA (slope > +0.05%/bar) and gap-ups > +2% (module clause). Status: PASS (contained in WB3).
- 2026-11-16 `MF2-open-rsimidhi-flowsell-FD-WB2`: WB1 + RSI(14) top 65 -> 62 (P10) + ADV $95M -> $150M (P2). Status: PASS (contained in WB3).
- 2026-11-16 `MF2-open-rsimidhi-flowsell-FD-WB3`: WB2 + heat floor >= -40 (P9). Status: PASS, recommended for Testing 2 (pending after close, not applied).

Files: DIAGNOSIS.md (every part P1..P26 + new layers, 5 worst + 5 best live trades, all-trades analysis), RESULTS.md (all 48 configurations, side by side, deploy plan), variants.jsonl, modules/, *.yaml stubs (no account loads them), code/ (bench reused from the RW5 / L3 Workbench jobs), results_all.csv, extras.csv, component_analysis.txt (live split), PNGs (engine, worst1-5, best1-5), MF2-open-rsimidhi-flowsell-FD.md (blueprint).

Educational only — not financial advice.
