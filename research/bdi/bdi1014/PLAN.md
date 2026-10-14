# BDI 2026-10-14 pre-declaration (written before any history configuration was scored)

*Educational only - not financial advice.*

## Part A: per-trade analysis of 2026-10-14 (descriptive, not gated)
`analyse_1014.py` re-uses `research/bdi/nightly1014/trades.csv` (681 real trades) and the nightly's SIP 1-minute bars.
It computes rule values at entry, MFE/MAE, what-if exits (be05, tr05, t05, t1, eod), stop-and-reverse, re-entry, the
opposite side with a hindsight pointer, and the loss type. Losers are merged into `research/bdi/patterns.csv`.
One session: a diagnosis, not evidence (rule 7).

## Part B: CWT14 stop-and-reverse ("failed fail-break continuation"), new setup + managed-trade rework
**Motivation (one session, not evidence).** On 2026-10-14 Testing 2's CWT14 fail-break trades were stopped 180
times. Reversing at the stop with 1R/1R would have added +0.318R per stop (+57R). CWT14 loses -0.09R after costs on
history, and its losers recur as never_worked or small-MFE (3 of 3 Testing 2 sessions, patterns.csv). The idea:
when a reclaimed level fails again and the bracket stop fills, the breakout was real, so trade the breakout.

**Data.** research/history2y open months only. The locked block 2024-11-01..2025-02-28 is refused by the loader, and
MCF_HIST_ALLOW_LOCKED is never set. No other holdout is scored here. The signals are the CWT14 qualifying bars
from `research/bdi/nightly1014`'s scan (`bt_hits.parquet`, live semantics: the first qualifying bar per setup,
symbol and day). The paths are the 5-minute frame bars plus the 15:05-15:55 tail rows (`refire1014/scan.tail_rows`).

**Base leg** (re-simulated): entry at the signal bar close, R = 0.25 x daily ATR, t05s1, stop-first, flat 15:55.
**SAR leg**, only when the base leg stopped (its target not hit first):
- side = opposite of the base, R = 0.25 x ATR.
- Entry E1 = a resting stop-entry at the base stop price. It costs a stop fill plus 2c. Conservatively, if the stop
  bar's other extreme already reached the leg's stop, the leg counts as stopped, and no target is credited inside
  the stop bar.
- Entry E2 = a market order at the close of the stop bar (the next poll), with the time-of-day entry cost.
- Geometry G in {t05s1, t1s1, t2s1, t1s05, eod-s1 (1R stop, no target, flat 15:55)}.
- Costs: production (1c + 1 bps per side, target side free, +2c on stops), with the tod multiplier on the E2 entry
  and x3 on the extended tier (|gap| >= 20% or price < $5), as in cwt/test_b/score.py.

**Configurations.** 2 entries x 5 geometries x 12 books (the 11 live CWT14 setups plus a pooled book) = 120 SAR-leg
configurations. The pooled book is de-duplicated on symbol, day, side and stop bar.
- The managed trade (base + SAR on the same signal, R per base signal) is reported for every one of them, which is
  another 120. **N = 240.**
- Study bar: sqrt(2 ln 240) = 3.31.
- **Lineage bar.** The lineage is cwt-b-b3 with its overlap (N 120,599), plus nightly-1014-cwt14-skip-first-bar
  (10), plus these 240, for N = 120,849. That makes **t >= 4.84**, and this bar is binding.

**Bars (fixed now).**
- **Research / Primary gate:** `gates.verdict` == keep at the lineage N (exp > 0, t >= 4.84, up and down > 0,
  WF >= 0.6). In addition: excess over the same-time control > 0, ex-best-day > 0, both halves (<= 2025-12 and
  2026) > 0, and a plateau (the neighbouring geometries with the same entry, and the other entry with the same
  geometry, all > 0). A pass would only make it a finalist for the lead's single locked-block score.
- **Testing bar (experimental):** exp > 0 with day-clustered t >= 2.0; both halves > 0; up and down > 0; WF >= 0.6;
  ex-best-day > 0; plateau as above. Testing 2 is the natural home, beside its CWT14 parents.
- **Same-time control (rule 6):** the mean production R of every universe bar (adv20 >= $95M) at the same date and
  the same tod as the leg's entry bar, on the leg's side.
  - It uses the frame geometry where one exists (t05s1, t1s1, t1s05), and t1s1 for t2s1 and eod-s1.
  - It uses the frame's own outcome columns, which start at that bar's close.
- **Managed-trade read:** base + SAR must beat the base alone in both halves and in up and down sessions. This is
  reported only; it is not a gate on its own.

## Part C: no tuning of the top-5 setups (a separate run at 18:07 ET handles that)

## Part B2 (added 2026-10-14 after Part B's results, before B2 was scored): index-aligned SAR, a rule-18 rework
Part B failed (0 of 240). Its regime split shows the reversal leg pays only when the session's direction agrees
with it: long legs win in up sessions, short legs in down sessions. The session regime is only known after the
close. The rework adds one condition that is known at the stop bar.
- **Condition:** take the SAR leg only when SPY's fromOpen at the stop bar's tod is on the leg's side, with
  leg_side x SPY fromOpen > k and k in {0, 0.25%}.
- **Scope:** entry E2 only (E1 was dominated in every book), 5 geometries, 12 books.
- **Configurations:** 2 x 5 x 12 = 120, plus 120 managed-trade reads = 240 more.
  - Study N = 480, so its bar is 3.51.
  - Lineage N = 120,599 + 10 + 480 = 121,089, so the bar is t >= 4.84.
- The bars, the control, the plateau (the other k and the neighbouring geometries) and the halves are the same as
  in Part B.
