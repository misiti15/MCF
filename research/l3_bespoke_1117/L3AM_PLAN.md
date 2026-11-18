# L3-AM: one pre-registered test (plan, written and committed before any scoring)

*Educational only — not financial advice.* Research only. No config, setup, exit or latch change comes from this file.

Owner 2026-11-17 ~19:35 ET: **"L3-AM yes"** (decision L3-AM, docs/live/decisions.json): one pre-registered test of
`L3-gap-slope-fromopen-FD` ("Gap-Down Recovery Fade (all day)", Primary) with **no new entries after 13:00**.

## The one configuration
- **AM**: the parent exactly as in research/l3_bespoke_1117 (`code/sim4.py`, `sim4.P`), entry window
  **09:50-13:00** (`w = (950, 1300)`: the last entry is at the close of the 5-min bar ending 13:00) instead of
  09:50-15:00. Exits, stop, target, flat 15:55, refire chain, Primary book (≤ 30 lots, ≤ 3 per symbol) and the −2R
  latch (running low, as the runner) are unchanged. Open lots still exit by their own rules after 13:00.
- **Parent** = the same engine with `w = (950, 1500)` (the l3_bespoke_1117 baseline: replay 354 / +0.136R, 2-year
  4,242 / −0.052R).
- **Configurations counted: 1.** Lineage: 43 configs in l3_bespoke_1117 + this one = 44 → bar max(1.5, sqrt(2 ln 44))
  = **2.75**. Longer lineage (earlier L3 runs, N = 155) bar 3.18 is reported alongside, not used for pass.
- Not the same as the Testing 2 copy `L3-gap-slope-fromopen-FD-WB4` (window to 13:00 **plus** gap ≤ −3.2%); this test
  isolates the window alone.

## Data (unchanged from PLAN.md; the locked block 2024-11-01..2025-02-28 is never read, asserted in code)
- **2-year** engine test on the stored lab-frame pack, splits TRAIN ≤ 2025-12-31, **VALID 2026-01-02..2026-10-05**,
  FWD 2026-10-06..11-04. **Session replay** 10-12..11-17. **Live** Primary 10-21..11-17 + On Deck 10-13..10-29
  journals with the −2R latch replay of `code/live.py` (R after costs, cost_r; what-ifs as in latch_review_1117).
- Costs in everywhere (LR8 in the engine; cost_r live).

## Pass bar (fixed now)
All of these on the **2-year VALID segment**, AM vs parent:
1. avg R per trade (after costs) AM ≥ parent;
2. total R AM ≥ parent;
3. avg R without its best day AM **>** parent;
4. day-paired t of (AM − parent) day R over the VALID sessions ≥ **2.75**.

**Live consistency** (required too): in live Primary + On Deck (−2R latch replay) AM avg R ≥ parent avg R **and** AM
total R without the best day ≥ parent's. TRAIN, FWD and the session replay are reported, not gates.

If 1-3 and live pass but t < 2.75, the verdict is **"promising, below the bar" = not a pass**.

Honest prior-exposure note: the AM/PM split was already seen descriptively in RESULTS.md Test B (cap on, **no latch**:
VALID AM −0.046R vs PM −0.023R; live AM +0.31R vs PM +0.04R). The pass bar is set strict for that reason (the t on
VALID, not on the full 2 years where the live-era sessions sit), and it was not tuned after seeing these numbers: the
window end 13:00 was fixed by the owner's question.

## Outcome handling
- **Pass** → propose (do not deploy) a Testing copy `L3-gap-slope-fromopen-FD-AM` as DECISION "L3AM-COPY yes" in
  docs/live/decisions.json and the owner inbox; it would go to a testing account other than the parent's and WB4's
  twins rules apply. Primary is not changed either way.
- **Fail** → reported in L3AM_RESULTS.md; no decision code; the parent stays as it is.

Outputs: `code/testAM.py`, `L3AM_RESULTS.md`, `L3AM.csv`.
