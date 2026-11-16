# Workbench: Gap-Down Pop Fade, Heavy Selling (all day) (`RW3-gapdn-rsi5pop-flowsell-short-FD`)

Teardown variants of `RW3-gapdn-rsi5pop-flowsell-short-FD`: each changes ONE part and is a brand-new setup (new id, parent link). The original is never edited. Variants are research only until backtested under docs/RESEARCH_RULES.md and placed in the testing arena with the owner's yes.

## Log

- 2026-11-16 `RW3-gapdn-rsi5pop-flowsell-short-FD-WB1`: `window` [950, 1500] -> [1030, 1500] - Mechanic: entry window starts 10:30 (live 10:00-10:30 entries -0.19R; replay 10:00-10:30 -0.47R). Status: PASS (RESULTS.md); folded into WB3.
- 2026-11-16 `RW3-gapdn-rsi5pop-flowsell-short-FD-WB2`: new gate (module, `context: [spy_fo]`) skip while SPY > +0.20% since the 09:50 bar close - set by hand. Status: PASS (RESULTS.md); folded into WB3.
- 2026-11-16 `RW3-gapdn-rsi5pop-flowsell-short-FD-WB3`: `window` [950, 1500] -> [1030, 1500] + WB2 gate + daily ATR >= 1.6% (1R >= 0.40% of price) - Mechanic combo D1, set by hand. Status: PASS, recommended (RESULTS.md).

All 42 configurations tried (incl. failures): RESULTS.md. Educational only — not financial advice.
