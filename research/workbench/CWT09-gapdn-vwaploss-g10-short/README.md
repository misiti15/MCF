# Workbench: Gap-Down VWAP Loss Short (10% gap) (`CWT09-gapdn-vwaploss-g10-short`)

Teardown copies of `CWT09-gapdn-vwaploss-g10-short`: each is a brand-new setup (new id, parent link). The original is
never edited. Copies are research only until placed per research/workbench/RULES.md. Educational only — not financial advice.

## Log
- 2026-11-16 `-WB1`: P9 + signal-bar close below the day open (fromOpen < 0). PASS.
- 2026-11-16 `-WB2`: P9 + a 5-minute close above VWAP during 09:35-10:30 (a real bounce, not a wick). PASS.
- 2026-11-16 `-WB3`: WB1 + WB2. PASS.
- 2026-11-16 `-WB4`: WB1 + WB2 + P2 min_adv $1M -> $20M. PASS, recommended (replay -0.139 -> +0.041R, 2-year +0.079 ->
  +0.134R after costs); pending for Testing E after the close, not applied. 54 configs counted. RESULTS.md.
