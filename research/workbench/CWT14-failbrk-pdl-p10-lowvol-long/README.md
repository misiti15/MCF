# Workbench: Failed Prior-Day-Low Break Long (0.1 ATR, low volume) [fill] (`CWT14-failbrk-pdl-p10-lowvol-long`)
Educational only — not financial advice.

Teardown variants of `CWT14-failbrk-pdl-p10-lowvol-long` (parent runs in Testing D, unchanged). Each copy is a new id with a parent link; the parent is never edited. Research only until applied after the close per research/workbench/RULES.md.

## Log
- 2026-11-16 `CWT14-failbrk-pdl-p10-lowvol-long-WB1`: P19 stop 0.25 -> 0.45 x ATR (target unchanged, +0.125 ATR). PASS.
- 2026-11-16 `CWT14-failbrk-pdl-p10-lowvol-long-WB2`: P1 intake gap <= -0.5%. PASS narrowly.
- 2026-11-16 `CWT14-failbrk-pdl-p10-lowvol-long-WB3`: WB1 + WB2. PASS — recommended (Testing F, first in setup_order; NOT applied — after-close plan in RESULTS.md).
- 104 configurations scored (RESULTS.md). Files: DIAGNOSIS.md, RESULTS.md, results.csv, configs_onepart.csv, configs_combos.csv, code/, modules/, engine + 10 trade PNGs.
