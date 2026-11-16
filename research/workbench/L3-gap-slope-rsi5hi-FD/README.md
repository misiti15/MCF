# Workbench: Gap-Down Rebound Overbought Short (all day) (`L3-gap-slope-rsi5hi-FD`)

Teardown variants of `L3-gap-slope-rsi5hi-FD` (On Deck, leaderboard rank 10 at intake: 138 live trades / 20 sessions, +0.111R). Each copy is a
brand-new setup (new id, parent link); the original is never edited. Copies stay research-only until deployed under research/workbench/RULES.md.

## Log
- 2026-11-16 `L3-gap-slope-rsi5hi-FD-WB1`: module clause stop-exit cost <= 0.05 of 1R (P16/P19). Status: PASS (contained in WB4).
- 2026-11-16 `L3-gap-slope-rsi5hi-FD-WB2`: module clause SMA20 slope <= 1.0 (P11 cap). Status: PASS (contained in WB4).
- 2026-11-16 `L3-gap-slope-rsi5hi-FD-WB3`: module clause RSI(5) <= 90 (P9 cap). Status: PASS (contained in WB4).
- 2026-11-16 `L3-gap-slope-rsi5hi-FD-WB4`: WB1 + WB2 + WB3. Status: PASS, recommended for Testing E (pending after close, not applied).

Sibling parts (L3-gap-slope-fromopen-FD WB4: 13:00 cut-off, 75-min max hold) tested here: FAIL on the 2-year. All 55 configurations
(39 pass / 16 fail on meet-or-exceed; none clears the counted t bar 2.83): RESULTS.md. Diagnosis: DIAGNOSIS.md. Educational only — not financial advice.
