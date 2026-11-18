# L3 bespoke review 2026-11-17: plan (written before any scoring)

*Educational only — not financial advice.* Research only. Nothing in config, setups or exits changes here. The owner
said "leave the −2R latch for now".

Owner, 2026-11-17 ~18:10 ET, on `L3-gap-slope-fromopen-FD` ("Gap-Down Recovery Fade (all day)", Primary's top setup):
(1) find a per-setup daily stop more precise than the blanket −2R, one that "still lets it flex enough to produce the
big gains"; (2) check whether it does better in the mornings or the afternoons, e.g. latch in the morning and lift it in
the afternoon, depending on the day or market; (3) take L3 back to the Workbench for fewer losses and bigger gains.
Also: draft a design note for bespoke per-setup rules in Primary (BESPOKE_RULES.md). It is a draft only and nothing
is implemented.

Already known, not redone here: research/latch_review_1117 (loosening the latch hurt board-wide; L3 post-latch
−0.19R/trade over 9 latch days), research/workbench/L3-gap-slope-fromopen-FD (first run + RERUN → WB4) and
research/workbench/UPDAY/L3-gap-slope-fromopen-FD (WB5).

## Data (the locked block 2024-11-01..2025-02-28 is never read; asserted in code)
1. **Live journals** (journal.db copies of the mcf-data* state branches as of the 11-17 close). `L3-gap-slope-fromopen-FD`
   in Primary (10-21..11-17) and On Deck (10-13..10-29). Live trades = run_id 1, R after costs = mcf.costs.cost_r. The
   post-latch blocked signals are the what-ifs (run_id 2, `why=setup daily loss limit`). Their cost haircut is the
   setup's measured live gap, as in latch_review_1117, with the 3-lots-per-symbol cap. The Testing A copy
   `-WB4` (1 session) is reported only as a description.
2. **Session replay** (backtest, not live): the Workbench engine (`sim.py`/`sim2.py`/`sim3.py`, unchanged) on every ETB
   symbol-day where the parent signalled live. The Workbench pack covers 10-12..11-12 and is **extended to 11-17** with
   the same fetch (read-only SIP GET) for 11-13..11-17, so that 11-17 (BEZ) is included.
3. **2-year backtest**: the same engine on the stored lab-frame pack (2024-10..2026-11-04, open months only, E90 borrow
   proxy). Splits: **TRAIN** ≤ 2025-12-31, **VALID** 2026-01-02..2026-10-05, **FWD** 2026-10-06..11-04.
- Costs: LR8 everywhere in the engine (entry 1 bp + SEC + TAF + CAT; stop max($0.02, 4 bps); time exit max($0.01, 1 bp);
  target at the limit). The book is Primary's (≤ 30 open lots, ≤ 3 per symbol). The latch is the variable under test.
- SPY 1-min (cached + read-only GET to 11-17) is used for the day types and the point-in-time gates.

## Test A: latch level grid
Levels L ∈ {−1.00, −1.25, …, −4.00} (13) plus none: **14 configurations** (−2.00 is the baseline). The latch works as
in the runner: realized net R after costs for the setup today, checked at each exit, blocks entries after the exit
that takes it to ≤ L, and stays latched for the day.
Report for each test (live, replay, 2-year with splits):
- trades, total R, avg R/trade, day-level R, R without the best day, best-day share, worst day, latch days;
- **distinctness**: the number of setup-days whose latch trip differs from the next tighter level. Levels with
  identical trade sets are merged into one step, which shows which thresholds are actually distinct;
- **plateau check**: a level L* other than −2 is called a real improvement only if (a) it beats −2 on R without the
  best day in the 2-year TRAIN **and** VALID and in the live record, (b) both of its neighbours (±0.25) also beat −2,
  each by at least half of L*'s gain (a stable region, not a spike), and (c) the day-paired t vs −2 over the 2 years
  is ≥ the bar.
- Mechanics: the step size (loss per full stop in R) is shown from the data.

## Test B: time and day-type split
Descriptive (not configs): R by entry half-hour; morning (entries 09:50-11:59) vs afternoon (12:00-15:00); SPY day
type open→close (up > +0.25%, down < −0.25%, else quiet); SPY at 10:00 vs its 09:30 open (point-in-time). Reported in
live, replay and 2-year.
Latch variants (configs). The running day R is cumulative over the whole day; only the limit that applies to an
entry depends on the entry's time or on the state known at that time:
- B1 AM −2 / PM none · B2 AM −2 / PM −3 · B3 AM −2 / PM −4 · B4 AM none / PM −2 · B5 AM −3 / PM −2
  (AM = entries before 12:00).
- B6 limit −3 when SPY at 10:00 < its open (a weak start, which suits shorts), −2 otherwise · B7 limit −1 when SPY at
  10:00 ≥ +0.25% above its open (a strong start), −2 otherwise · B8 no limit when SPY at 10:00 < its open, −2
  otherwise. Before 10:00 these use −2: SPY at 10:00 is not known yet.
**8 configurations.**

## Test C: Workbench Mechanic pass (parent `L3-gap-slope-fromopen-FD`, one knob each, parent never edited)
Aim: a better loss:gain ratio (avg win / |avg loss|, profit factor) without killing the big days.
- Target: C01 1.25R · C02 1.5R · C03 2.0R
- Stop: C04 0.8R · C05 1.25R
- Breakeven: C06 stop → entry after +0.5R · C07 stop → entry after +0.75R · C08 stop → entry +0.5R (half risk)
  after +0.5R
- Time: C09 exit at 60 min if MFE < 0.25R · C10 max hold 75 min (WB4's exit part alone) · C11 exit at 30 min if
  MFE < 0.25R
- Scale-out / runner: C12 half at +1R, half to 2R with the stop at entry after +1R · C13 half at +0.5R, half to 1.5R
  with the stop at entry after +0.5R · C14 no fixed target: trail 0.75R behind the best low once MFE ≥ 1R, cap 3R
- Entry quality, with thresholds fixed from the **TRAIN** signal distribution only (quantiles, no peeking at
  outcomes): C15 fromOpen ≤ TRAIN p80 (chase guard) · C16 vwapDistPct ≤ TRAIN p80 · C17 volumeRatio ≤ TRAIN p80 (no
  shorting into volume squeezes) · C18 rsi5 ≥ TRAIN p20 · C19 1R ≥ 0.5% of price (cost floor)
- Symbol: C20 no re-entry on a symbol after a stop on it that day (BEZ 11-17: 4 shorts stopped) · C21 ≤ 2 lots per symbol
**21 configurations.**
Guards (BDI charter): a variant must keep ≥ 70% of the parent's trades and ≥ 90% of the parent's top-decile winners
(2-year; a winner is "kept" when the variant still takes that entry). Variants that fail a guard are reported and not
eligible.

## Validation (same for every config)
- Total **N = 14 + 8 + 21 = 43** (42 non-baseline). Bar = max(1.5, sqrt(2 ln 43)) = **2.74** on the day-paired t of
  the improvement vs the parent (−2R latch) over the full 2 years. Lineage note: the earlier L3 Workbench runs tried
  more (first run 13, RERUN 46, UPDAY 42, latch review 10). The lineage bar is reported too.
- Selection on **TRAIN only**: any C or B config that beats the parent on TRAIN avg R (and passes the guards) is then
  scored once on VALID, FWD and the session replay. **Pass** = better than the parent in TRAIN, VALID and the replay;
  not worse on R without the best day or on best-day share; full 2-year day-paired t ≥ 2.74. A config that passes
  everything except the t bar is reported as "promising, below the bar". It does not pass.
- Workbench RULES.md (meet-or-exceed in both tests, guards on w/o best day and worst day) is reported alongside for
  the C configs.
- **Random-entry comparison**: for the parent and the best variant, every taken trade's entry is moved to a random
  5-minute bar close in the window (09:50-15:00) on the same symbol-day (5 seeded draws), with the same exits and
  costs. This shows whether the signal timing beats chance on those names.

## Rule changes inside the windows (ledger effective dates)
Primary sizing ~$4-5k (10-28), Primary −2R latch ST-P (10-29), L3 re-promoted Testing 1 → Primary (10-30), TEAM-6 in
Primary (11-11), LR3 (latch/halt on R after costs) and LR8 cost model (11-12), SPYEXIT engine (11-17, not used by L3).
The engine applies today's rules to every session, so engine comparisons are not mixed up with these. The live
record is mixed: there was no latch in Primary before 10-29, and On Deck latched only 10-20..10-22.

## Outputs
NOTES.md (method details, deviations), RESULTS.md, CSVs, `latch_curve.png`, BESPOKE_RULES.md (draft design note).
Decision codes go in research/owner_inbox/2026-11-17.md and docs/live/decisions.json only if a config passes. They are
always a Testing copy or a Primary rule *proposal*, never applied.
