# Day-level profit lock (giveback_1119/day_lock) — pre-registered plan

*Educational only — not financial advice.* Written 2026-11-20 before any day-lock score was computed. Research only:
no setup, exit or config change. Builds on research/giveback_1119/map (account-day finding 5: 83 account-days peaked
>= +5R, 48 closed red; the open-at-peak majority-side lots carry -1,029R of the giveback).

## Question
When an account's marked-to-market (MTM) R for the day reaches +X and then gives back Y% of the peak, does acting
at that moment improve the account's R after costs?

## Data
- **Live (scoring sample):** run 1 of all 10 journals (Primary, Testing1, Testing2, LiveLab, Explore1, Graveyard,
  TestingD/E/F, Gen), 2026-10-06..11-19, from the map's live_paths.parquet (LR8 R on every row, lots kept per account,
  no cross-account de-dup because the lock is an account-level rule). Minute bars: 1-minute SIP o/h/l/c 09:30-16:00
  re-fetched read-only from Alpaca (same script as the map), scratch only, deleted after.
- MTM curve per account-day exactly as the map: realized net R of closed lots from their exit minute + open lots marked
  at the minute close in R (|entry - stop| unit, equal weight per lot).
- **Fit = sessions 2026-10-06..10-31 (19), check = 2026-11-02..11-19 (14).** Primary is reported first.
- **2-year book replay:** research/replay2y is NOT calibrated (79% match vs >= 98% bar, weight 0, 7 sessions), so it
  is not used for scoring. Reference only: a synthetic lab book (bt_lab1104 first-signal trades from the map's
  lab_paths.parquet; per session 3 seeded draws of 40 trades; marks linearly interpolated between the 5..120-minute
  checkpoints and the exit; extra exit cost 0.05 stop units). Fit <= 2025-09-30, check later. Locked block
  2024-11-01..2025-02-28 absent (asserted). Screening weight only, never a pass input.

## Trigger (evaluated at each minute close t, no look-ahead)
peak_t = max MTM up to t. Armed once peak_t >= X. Fires the first minute MTM_t <= peak_t x (1 - Y). Acts on the next
minute (t+1) bar open. One fire per account-day.

## Actions
- **A1 block:** no new entries in the dominant direction (net side by count of lots open at t; if tied/none, the side
  of the most recent entry) for the rest of the day. Blocked lots score 0 R (freed capacity not re-used: noted).
- **A2 tighten:** each lot open at t with mark > 0 gets a stop at 50% of its mark at t; walk bars t+1..exit minute,
  exit at the lock level (or the bar open if it gaps through) when touched (touch in the exit minute counts as the lock
  first: conservative). Lots at or below 0 unchanged.
- **A3 half:** every lot open at t exits half its size at the t+1 open.
- **A4 flatten:** every open lot exits at the t+1 open and no new entries (either side) for the rest of the day.
Early-exit R = original LR8 R + side x (new exit px - original exit px) / |entry - stop| - extra exit cost, extra =
(half spread [journal spread_bps, 5 bps if missing] + $0.01/share + 1 bp of price) / |entry - stop| (the exit already
paid by LR8 is kept; this is a conservative extra).

## Grid (configs counted)
X in {+5R, +8R} x Y in {30%, 50%} x action in {A1..A4} = **16 configs** (N_class = 16). Lineage N for the bar:
the map scored 0 exit configs; sibling classes of this investigation run in parallel and their counts are not known
here, so the bar is reported at N = 16 (sqrt(2 ln 16) = 2.35) and at a conservative N = 200 (3.26).

## Pass rule (every item, on the CHECK half, all accounts pooled; Primary reported alongside)
1. total R and avg R per account-day improve after costs;
2. avg R per trade w/o the best day not worse than base;
3. not carried by one day: best day's share of the total paired improvement < 50%;
4. more families (and setups) better than worse (delta attributed to the lots it changed);
5. paired t of the per-date improvement (sum over accounts per session, t over sessions) >= max(1.5, sqrt(2 ln N)).
The fit half must have the same sign. Also reported: days fired, helped vs hurt, R lost on fired days that kept
running up (MTM after the fire made a new high above the fire-time peak), per account.

## Addendum A (2026-11-20, after the first full-sample pooled totals, BEFORE any check-half, per-family or Primary score)
The first pooled totals showed the block/flatten gains could simply be "fewer trades in a book whose average trade is
negative" (live avg -0.151R). A stricter control is added; it can only make passing harder, the grid is unchanged:
- **Time-matched placebo:** for each fired account-day, the same action at the same clock minute applied to every
  non-fired day of the same account; its mean delta is the placebo. **Excess = actual delta - placebo.**
- Pass item 6 (added): the check-half excess must be > 0 in total, and the paired t of the per-date excess must also
  clear the bar. A lock that only beats "doing nothing" by trading less is reported as a trade-less effect, not a lock.
