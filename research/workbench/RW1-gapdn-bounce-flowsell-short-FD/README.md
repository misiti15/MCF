# Workbench: Gap-Down Bounce Short, Heavy Selling (all day) (`RW1-gapdn-bounce-flowsell-short-FD`)

Teardown variants of `RW1-gapdn-bounce-flowsell-short-FD`: each changes ONE part and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until backtested under docs/RESEARCH_RULES.md and placed in the testing arena with the owner's yes.

## Log

- 2026-11-16 `RW1-gapdn-bounce-flowsell-short-FD-WB1`: `window` [950, 1500] -> [950, 1300] - Mechanic: P6 entry window ends 13:00 (replay 13:00-15:00 entries -0.27R/trade; live 13:00-15:00 ~0R). Status: see below.
- 2026-11-16 `RW1-gapdn-bounce-flowsell-short-FD-WB2`: P11 RSI(14) band 55-65 -> 55-60 (module clause, by hand). Status: see below.
- 2026-11-16 `RW1-gapdn-bounce-flowsell-short-FD-WB3`: `window` [950, 1500] -> [950, 1300] - Mechanic combo D8: window end 13:00 + RSI(14) 55-60 + 1R >= 0.40% of price (daily ATR >= 1.6%) + skip when SPY > +0.20% since 09:50; module clauses + context: [spy_fo] set by hand. Status: see below.

Results 2026-11-16 (Mechanic, 48 configurations, RESULTS.md): WB1 PASS (in WB3), WB2 PASS (in WB3), **WB3 PASS — recommended for Testing E (pending after close, not applied)**: replay +0.013 -> +0.185R, 2-year -0.018 -> +0.026R.

Files: DIAGNOSIS.md, RESULTS.md, variants.jsonl, modules/, *.yaml stubs (no account loads them), code/, results.csv, extras.csv, component_analysis.txt, PNGs (engine, worst1-5, best1-5).

Educational only - not financial advice.
