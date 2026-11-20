Educational only — not financial advice

# BEG-RULES: session-rule overlay test (pre-registered 2026-11-20, before any scoring)

## What is tested
The beginner's eight session rules S1-S8 (research/beginner_1120/DESIGN.md section B), each as an overlay that
only removes (or halves) trades that the setups would have taken. Every rule is scored on and off against a
no-rules baseline. No rule parameter is tuned: the values are the ones in DESIGN.md, fixed before scoring.

## Books
1. **BEG book** = the 10 BEG setups in their **base** form (the pre-registered design, not the per-setup FIT tweaks,
   so no selection leaks in), booked the normal way (bench10: LR8 costs + borrow, testing-arena book: per-setup cap
   100, <= 3 lots/symbol, ETB >= 90%, cost filter 0.15R). Trade lists are the existing booked files from each
   setup's run (scratchpad beg01w..beg10w, `bk_base_*` / `booked_*_base_*`). All 10 setups form ONE account.
2. **BEG alone** = the same rules with each BEG setup as its own account (per-setup effect without book
   interaction).
3. **Primary live** = MCF Primary journal (origin/mcf-data journal.db, run 1 = live), 2026-10-06..2026-11-19,
   R per trade = LR8 cost-R (mcf.costs.cost_r_lr8). MCF's own rules (-2R per-setup latch from 10-29, -20R halt,
   per-setup cap) are already inside these trades; the overlays act on top.

## Rules as implemented (event simulation per account and day; exits at xm processed before entries at em >= xm)
- S1: realized day R <= -3 -> no new entries.
- S2: <= 6 new entries/account/day, <= 2 per symbol/day; after a stop-out (BEG: r_gross <= -0.9; Primary:
  exit_reason == stop) no re-entry of that symbol by that setup that day.
- S3: entries only 09:50-15:30 (em 590..930); BEG-05/BEG-07 only 15:25-15:30 (em 925..930). Trades exiting after
  15:55 are counted as booked (cannot be re-walked here; count reported).
- S4: <= 4 open positions/account, <= 3 same direction. (Fixed 0.5% 1R = already the R unit; no-op on R.)
- S5: after 3 consecutive cost-in losers (by exit time), no entries for 30 min after the 3rd loser's exit; once
  realized day R >= +4, new trades count at 0.5 weight.
- S6: blackout windows (CPI/NFP 08:30-10:15, ISM 09:55-10:10, FOMC 13:45-14:30) on entry minute; calendar built
  from public schedules (FOMC statements; BLS CPI and Employment Situation incl. the 2025 shutdown shifts; ISM
  manufacturing = 1st and ISM services = 3rd trading day of the month).
- S7: BEG-01/02/03/06/09/10 only: long only if SPY close of bar em-1 > SPY session VWAP through em-1, short only if
  below. On Primary (no momentum/reversal label in MCF) S7 applies to every trade; per-setup effect is shown so
  harm to reversal setups is visible.
- S8: skip if risk/entry < 0.25% or > 3%, or mean close x volume of bars em-5..em-1 < $150k (missing minute = $0).
  Where 1-minute bars are missing (Primary 2026-11-11..11-19) the volume leg passes and S7 passes; coverage reported.
- ALL: S1-S8 together. MCF (comparator, BEG book only): -2R per-setup realized latch + -20R account halt (realized).

## Windows
FIT = 2024-10 + 2025-03-01..2025-09-30 (verdict). CHECK = 2025-10-01..2026-11-04, scored once with the same fixed
rules. T2 = 2023-01-03..2024-09-13 (seen, reference). Primary live window is reference (seen). Locked block
2024-11-01..2025-02-28 never read (asserted on every load).

## Metrics (paired, per rule)
Total R, avg R per session, worst day, green-day % (sessions traded), days helped / hurt vs baseline, paired
day-clustered t of the daily difference, avg R/trade and avg R w/o best day + best-day share, per-setup delta
(improved / worse, by how much). Random control: the same number of trades removed per day at random from the
baseline (200 seeds); report the rule's delta percentile vs that.

## Verdict rule (fixed now)
A rule HELPS on the BEG book if on FIT: delta avg R/session > 0, paired t >= 1.5, beats >= 80% of random-removal
seeds, and setups improved >= setups worsened. CONFIRMED if CHECK delta > 0 and beats >= 60% of random seeds.
Else NEUTRAL (|t| < 1.5) or HURTS (delta < 0 with t <= -1.5).

## Configurations counted
8 rules + ALL = 9 overlays x 3 books (BEG book, BEG alone, Primary) = 27, + MCF comparator on BEG book = 28.
Random controls are controls, not configurations.

## Addendum (written after the main scoring, before this run): tweak T-S2ps
Main results showed S2/S4 cut by arrival time and starve late-firing positive setups. Tweak T-S2ps = S2 counted per
setup (6 entries/setup/day, 2/symbol, no re-entry after a stop-out) instead of per account. On BEG data this is
exactly the BEG_alone S2 row (already scored). One new configuration: T-S2ps on Primary live (reference only, seen
data). Total configurations: 29.
