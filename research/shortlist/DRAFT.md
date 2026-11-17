# Scout shortlist for Lead (lead-20261116-2300-4) — DRAFT 2026-11-16 23:30 ET; final after the 11-18 REPS3 / ICCSET run
Educational only — not financial advice. Plans only; nothing is scored until Lead picks. Every candidate must show an ex-market
control up front (MOMSIDE lesson: its 'edge' was market direction).
Backlog scan (1,088 lines): parked 439, rework 303, idea 210; near-live: finalist 14 (mostly the live RW family + 2 daily-bar swing
items outside the intraday scope), lane-candidate 26 (ex30, all negative after costs), probation 14 (live MF/NS), forward_wait 4.

## Candidate A (LEAD) — Move-Hunt capture gap, in owner terms (charter north star; Lead lead-20261117-0100-3)
Source: the Move Hunt catalogue research/bdi/moves/moves.csv (Live capture; 11 sessions 10-29..11-12; top 25 long + 25 short
moves per day from a 5-min decision point over the next 90 minutes, in daily ATR). Structural look only (no rule scored):
- 550 catalogued moves: **62% are earnings-blackout names** (341). Live does not trade them by rule (+-4 days), so the biggest
  uncaught move type is a POLICY gap, not a missing setup. The FAMC Shadow already measures one slice (after-close reporters).
- 14% are ETFs; index-ETF clusters (VOO / IVV / SPXL ... on one market move) count one move many times, so dedupe by underlying.
- The rest, **non-ETF non-blackout: ~13 moves/day; Live catches 14%** (20/145). Misses: traded outside the move 48, no setup
  signalled 38, wrong side only 20, skipped 17 (spread 10, borrow 4, caps 3).
- **80% of those moves start at a 09:35-10:00 decision point**. Under the owner's anchor rule (no 09:30 entries; reference ~09:50),
  the question is how much of each move is LEFT after 09:50, and whether it is foreseeable then.
Plan (descriptive first, 0 configs; nothing scored until Lead picks):
 A1. Re-measure each catalogued move from the first decision point >= 09:50 (owner anchor), dedupe ETF clusters, and split by
     side and by type: gap-continuation, gap-reversal, no-gap breakout, midday. Report what remains in ATR and how many per day.
 A2. For the 2-3 biggest uncaught types: are they flagged at 09:50 by features already in the catalogue rows (gap, fromOpen, rvol,
     dist to HOD/LOD, spy_fo, breadth)? This needs the per-decision rows (moves.py writes <scratch>/mh/<day>/rows.parquet) for
     the precision denominator (all names at that decision, not only the movers: checklist 20). It needs the main session's
     mh frames, or a Session replay over the Live session bar store from 10-06.
 A3. Setup-days estimate for a targeted setup: signal days per week x the Live parity from REPS2 (p_day = 1 - exp(-0.193 x lab
     trades/day)). A type that shows up most days could add ~3-5 setup-days/week per setup slot.
 Controls up front: ex-market (beta x SPY over the hold) and a same-minute random-name control, so a 'precursor' is not just
 market direction (MOMSIDE lesson). Family: new; any rule then scored on the 2-year backtest with its own count.
 Owner-facing policy line (not ours to change): the earnings blackout hides ~60% of the day's biggest moves; FAMC is the
 guild's only measured window onto them.

## Candidate B — cost-per-R remedy (depends on Builder's gross-R print for SIZESTOP / STOPW, Lead lead-20261116-2300-2)
If widening is a cost artefact (gross ~0), the honest remedy is per-share cost relative to R: a minimum stop distance in bps
(STOPW, 77-config family) or the proposed hf1027-costfloor-halfR skip (7 configs). It must be scored against a random same-share
skip / size-cut control (checklist 9) and in gross beside net. Value: loss reduction on tight-stop setups; MDE expected ~0.01R
per changed trade (STOPW had ~1.3M trades).

## Candidate C — spotlight rotation input (keep only if it adds a ranking input rotation lacks: Lead) (owner arena rule, 2026-11-12; reps priority 1)
For the arena's every-4-session spotlight of the ~15 least-traded setups: rank candidate setups by expected setup-days/week
(REPS2: p_day = 1 - exp(-0.193 x lab trades/day)) x their lab quality (TRAIN / VALID ex-market, MDE). Descriptive, 0 configs;
gives the rotation a list that maximises reps per spotlight slot.

To finalise after 11-18: family try-counts and BAR90 per candidate, expected MDE, and REPS3's realised setup-days.
