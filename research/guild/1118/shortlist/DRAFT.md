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

 A3 counts (catalogue, non-ETF non-blackout, 11 sessions; per day in brackets). Read as the CEILING a targeted setup could reach
 before precision: these are hindsight-best moves.
 | miss reason | long | short | all |
 |---|---|---|---|
 | caught by Live | 11 (1.0) | 9 (0.8) | 20 (1.8) |
 | traded the name outside the move window | 21 (1.9) | 27 (2.5) | 48 (4.4) |
 | no setup signalled | 16 (1.5) | 22 (2.0) | 38 (3.5) |
 | only the wrong side traded | 9 (0.8) | 11 (1.0) | 20 (1.8) |
 | skipped by a filter (spread / borrow / caps) | 9 (0.8) | 10 (0.9) | 19 (1.7) |
 | total | 66 (6.0) | 79 (7.2) | 145 (13.2) |
 Earnings-blackout moves: 180 long / 161 short (31/day), outside our scope (policy). Median move 1.21 ATR long / 1.13 short.
 Setup-days reading: 'no setup signalled' (3.5/day) and 'traded outside the move' (4.4/day) are the two addressable pools. A
 setup that caught even one type in each on most days would add ~4-5 setup-days/week per slot. That is above REPS2's median slot
 (2.7), before precision.

 **A-WT row ('right name, wrong time', 4.4/day; Lead lead-20261117-0500-2).** Timing look at Live trades on those 48 symbol-days
 (5 catalogue accounts; timing only, no R): only 23 had a SAME-side Live trade; 22 had opposite-side trades only, which is in effect
 'wrong side'. Of the same-side trades, **25 entered AFTER the move's extreme vs 4 before the window**; the moves' median decision
 point is 09:35. Families involved: GEN 10, CWT14 6, RW7 4, heat_fade 3. So 'wrong time' mostly means **Live arrived after an
 early move had finished**. Entering earlier conflicts with the owner's 09:50 anchor, so the fix to test is narrower: how much of
 these early moves REMAINS after 09:50 (A1), and whether the setups that traded them late would have had their signal by then.
 Control: ex-market (beta x SPY over the hold) and the same setups' late entries on non-move days.
 Controls up front: ex-market (beta x SPY over the hold) and a same-minute random-name control, so a 'precursor' is not just
 market direction (MOMSIDE lesson). Family: new; any rule then scored on the 2-year backtest with its own count.
 Owner-facing policy line (not ours to change): the earnings blackout hides ~60% of the day's biggest moves; FAMC is the
 guild's only measured window onto them.

 **A-WT prior work (found 11-17 07:20 ET; it shrinks the row).** The two largest families in the pool already have answers:
 - CWT14 (6 of 48): CWT14SKIP (Builder 11-09, research/cwt14skip) tested 'skip a failed-break long already >= X ATR below the
   open'. It was CLOSED: half its skips were earnings days, and on the blackout-free pool t was 1.05 (lead-20261109-2100-1).
 - GEN (10 of 48): obs-genlate (Observer 11-09) found that GEN's long loss is mostly giveback after +0.5R (49% of its long R).
   Late buying is a slice owned by a few chase-conditioned GEN setups; it is an exits question first.
 What is left that is new: RW7 (4), heat_fade (3) and the general 'entered after the extreme' pattern (25 vs 4).
 So A-WT ranks BELOW A1/A2 unless A1 shows real moves remaining after 09:50.

 **A2 prior work (found 11-17 21:20 ET in the MCF repo; it changes A2).** The main session already ran A2's core:
 research/bdi/moves/precursors.py on the full-denominator decision rows (rows.parquet, non-blackout, tod >= 09:50, 90-min labels;
 days 10-29, 11-09, 11-10). It found that **in-play (vol_exp = 5-min ATR / daily ATR) and time of day predict move SIZE**:
 q5/q1 spread ~40x for vol_exp, and early hours dominate. They do not predict SIDE. Seven Move-Hunt precursor lines were then
 tested on the 2-year history and parked or sent back to rework: mh-1029-inplay-continuation (8 configs, all negative),
 -earnings-sympathy (8, rework), -1030-open-pdh-pop-fade, -1102-open-group-move, -1105-gapup-vs-falling-tape (TRAIN +0.17 /
 VALID -0.18), -1106-defensive-rotation and -1109-inplay-compass-side (precision +2 pts but avg R worse than base).
 So A2 as drafted (6 catalogue features x 2 sides) would mostly repeat that work. The open part is narrower: **the side of the
 move, given in-play**. That needs a feature family not yet tried there. News failed (NEWSMID) and sector peers are in rework,
 so I have no strong candidate yet. **A2 is downgraded to 'only with a new side feature'.**
 Family update for any A2-type rule: MH lineage = the 7 lines above plus the laggard family; N stays >= 104 (BAR90 >= 2.74).

 **A2 side-feature answer (Lead lead-20261117-2315-2).** Side features already tried and closed: options flow (OPTFLOW), news
 direction (NEWSDIR, NEWSMID), premarket direction (D2), new highs (NH1), the 09:50 open-drive set (OD0950), the ORB family
 (t1-orb-exits, 489 configs), gap fade/continuation (many), peer laggard/leader (family 92), and in-play compass side (mh-1109).
 **One untried candidate, with a weak prior:** *yesterday's late-day flow*, meaning the sign of the name's 15:30-15:55 return on
 the PRIOR session, as the side for today's in-play names after 09:50. Why it is a candidate:
 - The HKS950 re-cut shows that the last half-hour carries persistent, name-specific flow (VALID +9.9 bps, t 4.45, mostly before 15:55).
 - Late-day flow is often institutional rebalancing, which can continue the next morning.
 - It is new to every family above.
 Weak prior: I know of no published stock-level result for the next-morning side, and HKS's persistence is same-slot, not next-morning.
 Test shape (plan only): in-play names at 10:00 (30-min range / daily ATR in the top quintile, computable from m30), long if the
 prior 15:30-15:55 return > 0 and short if < 0, hold to 11:00. Gross first and ex-market, with a same-minute random in-play control.
 1-2 configs; MH lineage N >= 104, BAR90 2.74. It is cheap: the cached m30 bars plus the 1-min closes already fetched for HKS950.
 If Lead prefers 'none yet', this stays parked as a backlog idea.

 **Decisions folded in (Lead lead-20261118-0100-1, Skeptic skeptic-20261118-0550-1):** A2 is 'none yet' as a scored candidate.
 A1 gains ONE descriptive line, 0 configs: yesterday's 15:30-15:55 sign vs today's 09:30-09:50 side (the competitor; 09:50
 anchor), side precision against 50% on the full denominator, gross and ex-market, day-clustered, MDE printed. It earns a plan
 only if it beats 'today's early side'. Skeptic's prior: the usual next-morning finding is REVERSAL.
 **A1 data check (descriptive prep, no outcome read):** the catalogue now holds 600 'all' rows; 253 are non-blackout, and 36% of
 those have a decision point >= 09:50. The cached m30 list covers only 28% of the non-blackout catalogue symbols, so A1 needs a
 small guarded 5-min fetch for the catalogue symbol-days (~250). The 512-name m30 list can serve as the full denominator for the
 side line (fixed-list caveat, checklist 32).
 **Owner rules since the draft (11-17):** SRCV1 gives the 2-year history 0 effective sessions, so every guild study informs rules
 only and adds no record. ODPREP: a finding about a specific setup feeds its ONE testing-arena Workbench tune, never On Deck
 directly. Candidate C's ranking must therefore use LIVE reps only; the lab quality is shown beside it, not blended.

 **Side line DROPPED from A1 (Skeptic skeptic-20261118-0750-1, Lead lead-20261118-0300-1).** Scored on hindsight movers, both
 'sides' look good because the move picked the names (checklist 20). A full in-play denominator would need a much larger fetch for
 a weak prior. A1 stays descriptive: of the big moves Live misses, how much is left to capture after 09:50, by side and miss reason.
 **A1 data fetched (11-18 03:15 ET, outside market hours; no outcome read):** research/shortlist/a1/fetch_a1.py (#43 guard), 244
 non-blackout catalogue symbol-days, 19,006 5-min bars, kept in scratch (a1_m5.csv.gz).

## Try-counts and bars (pre-registered here; Lead may reset a family before any look)
BAR90 = max(1.35, 0.9 x max(1.5, sqrt(2 ln N))). MDE stated at score time as nothing above (bar + 0.84) x SE; smaller unknown.
| row | configs | family (lineage) | N | BAR90 |
|---|---|---|---|---|
| A1 remaining move after 09:50, by side and miss reason | 0 (descriptive) | none | - | - |
| A2 09:50 precursors ('none yet'; Lead 11-18) | 0 | Move-Hunt / laggard catch-up 92 (incl. MH4, bdi1028) | 104 | 2.74 |
| A3 setup-days estimate | 0 (descriptive) | none | - | - |
| A-WT 'entered after the extreme' guard, 2 thresholds | 2 | entry-extension guards: CWT14 lineage 10 + obs-extension 4 | 16 | 2.12 |
| C spotlight ranking input | 0 (descriptive) | none | - | - |
Any scored row is checked against a same-minute random-name control and ex-market first, with gross before net.

## Candidate B — DROPPED (Lead lead-20261117-0500-2): stop-charge parity; the price path gains nothing.

## Candidate C — spotlight rotation input (keep only if it adds a ranking input rotation lacks: Lead) (owner arena rule, 2026-11-12; reps priority 1)
For the arena's every-4-session spotlight of the ~15 least-traded setups: rank candidate setups by expected setup-days/week
(REPS2: p_day = 1 - exp(-0.193 x lab trades/day)) x their lab quality (TRAIN / VALID ex-market, MDE). Descriptive, 0 configs;
gives the rotation a list that maximises reps per spotlight slot.

To finalise after 11-18: REPS3's realised setup-days (try-counts and bars above).
