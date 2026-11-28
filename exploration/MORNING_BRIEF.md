# Morning brief: exploration night 2026-11-27 → 11-28

Educational only — not financial advice.

**In one line:** tonight found no setup that makes money after costs. It did find that Primary's losses come mostly from a few "basket" days, and it built a Monday plan that makes those days much smaller. The plan is ready to apply on your word, and nothing has been applied.

The basis for every number below:
- **Live data:** journals 10-23..11-27, 25 sessions, R after LR8 costs.
- **Bench:** two years of 1-minute bars with LIVE-L costs.
- **Locked holdout** (2024-11-01..2025-02-28): never read.
- **Configurations tried:** about 9,680 so far (about 317 tonight).
- **Rule changes inside the window** (full list at the top of DECISIONS.md):
  - 10-28: size
  - 10-29: closed-R latch
  - 11-12: LR8 costs and the half-day flatten
  - 11-17: TSZ1
  - 11-19: Epoch 1
  - 11-20: stop rounding
  - 11-21: cost-basis fix
  - 11-23: ST7 out and the burst brake
- **Next rule change:** 11-30, AV50 for NM-ETF plus the Friday-review arena moves.

## Your 1-minute reply (everything else stays as is)
Copy, edit and send in the chat:
```
LATCH-OPEN monday | L3-OUT out monday | B8 shadow monday | TAGS2 go | REPORTS go | GOAL-STAGES yes | ARENA-LATCH-F no (or ARENA-LATCH-ONDECK yes) | FROZEN-BLOCKS discuss
```
This short line is my final recommendation. It differs from the full line in DECISIONS.md on two items, because of the later reviews: ARENA-LATCH-F already failed its random-cut control and breaks the playing-time rule, and FROZEN-BLOCKS clashes with your 11-20 "no freeze" rule. The routine cards (HS-SCALE, T1X2, PRIM-ADD3, ODP2/ODB3, CRYPTO) are in the full line in DECISIONS.md. Write `friday` instead of `monday` to wait for the 12-04 window. Each item is explained in [DECISIONS.md](DECISIONS.md), D1-D13. Your three earlier desk taps (LATCH-OPEN *friday*, L3-OUT *out*, B8 *shadow*) are still **provisional**. Nothing changes until you confirm here.

## Top 5 findings
1. **Losses come in clumps, and they are short "baskets".**
   - Primary's worst 5 days are 64% of all its losing-day R (−151.5 of −235.6).
   - All 5 were one short setup firing many lots that one broad move stopped out together. Example: 11-25, L3, 35 lots, 32 stopped, −35R.
   - Costs are only 11% of those days ([loss_anatomy](findings/loss_anatomy.md)).
2. **No positive edge after costs, on either side, in any condition tested.**
   - Before costs the edge is about −0.02 to +0.03R per lot. Costs are about 0.13R per lot.
   - Tonight's edge hunt (wide stops only, hold to the close) passed 0 of 20 cells ([edgehunt](findings/edgehunt.md)).
   - "Shorts underperform" holds only mildly: −0.170 vs −0.160R per lot. Mostly it is exposure: Primary is 80% short.
3. **Every lever that helps works by trading less on bad days, not by picking better trades.**
   - Removing any one short helps by about the same amount (L3, RW3, RW5 each about +0.9R/day on the bench).
   - The gap-up short switch (0 of 5, best p 0.42) and the RW 1.25x target (+0.007 / +0.003R per lot) both failed under today's costs ([gapswitch](findings/gapswitch.md), [rw_target](findings/rw_target.md)).
4. **LATCH-OPEN still helps on the Monday lineup without L3, as insurance.** On RW3, RW5 and NM-ETF ([latchopen_monday](findings/latchopen_monday.md)):

   | | CHECK | T2 | Live |
   |---|---|---|---|
   | Days at −20R or worse | 9 → 2 | 1 → 0 | 2 → 0 |
   | Worst 5 days | −148 → −97R | −105 → −63R | −67 → −41R |

   - Red days do not fall.
   - Against a random cut of the same number of trades on the same days it ranks at only the 16th / 0th / 20th percentile. It finds the bad days but does not pick better trades inside them.
5. **"Green every day" is not reachable at today's edge** ([metrics](findings/metrics.md)).
   - Even a book making +0.5R per lot is red about 11% of days.
   - Today's book is red about 55-65% of days, whatever filter is added.
   - The honest first stage:
     - no day worse than about −20R;
     - a 20-session floor no worse than −40R;
     - at least one measured verdict every day ("a winning day in some way").
   - Green weeks need a setup that makes money after costs first.

## Top 3 proposals (by effect on weekly R, honest ranges)
1. **LATCH-OPEN for Monday 11-30 (D1).**
   - About +1 to +4R/week on the Monday lineup, all from trading less.
   - It makes a −20R day rare (about 1.8 a year on CHECK).
   - The prepared change passes the full test suite.
   - Applying it Monday overrides the Friday-only rule.
2. **L3-OUT, L3 moves to On Deck (D2).**
   - Live total R is about unchanged.
   - The size of daily swings falls by about 42%, and the worst 5 days go from −108 to −69R.
   - Together with LATCH-OPEN: +2.9 to +8.8R/week vs today's book on the bench. The book is still about −6R/week.
   - Overrides L3's probation step and the Friday rule.
   - assignments.json is regenerated in the same commit.
   - Caveat: On Deck has no per-setup stop. On 11-25 it lost −391R. Hence the new option ARENA-LATCH-ONDECK.
3. **Start the search for a real edge as frozen forward tests (D4, D7).**
   - These don't trade, so they can't fool us:
     - TAGS2: 7 would-skip rules, scored once on 12-29.
     - PAIRED-CARD: 1 report on 12-11.
     - LONG-SURVIVORS: GEN-261020-09 and CWT14, scored 12-28.
     - A weekly Stage-1 scorecard.
   - 0R now. They are the only route to green weeks.

## Surprises
- **None of the prepared changes applied as written.** Their diff headers were wrong, and each broke 1-12 tests. All were fixed overnight; `apply_draft.py` now applies any of them and stops instead of half-applying.
- **The RW 1.25x target looked like the one exit change that had passed.** It came from a falling-market window and disappears under today's costs.
- **The gap-up short switch "added" R on every split,** but random day-skips of the same size did as well. That is the size effect again.
- **Three proposals conflict with your own rules** (DECISIONS.md, Reviewer notes cycle 2):
  - ARENA-LATCH-F is in-session throttling in a testing account (playing-time rule), and it already failed its random-cut control.
  - FROZEN-BLOCKS clashes with your 11-20 "no freeze" rule.
  - LATCH-OPEN blocks about 20% of Primary's trades inside a session. Please confirm loss stops sit outside the playing-time rule.
- **A free paired test was sitting unused.** Since 11-17 / 11-23, the WB4 and RQa copies of L3, RW3 and RW5 have traded the same signals as Primary with different exits. It is next week's first study ([critic](findings/critic.md)).

## What I would do next week (research only)
1. Paired reads of each Primary setup against its WB4 / RQa copy.
2. A "gross first" search across the 3,000+ names: a fixed wide stop and hold to the close, ranked on at least 0.15R per lot before costs on FIT, then scored once each on CHECK and T2.
3. Match B8's beta to the bench version before its shadow starts (the betas file is still missing).
4. A capture-rate study: how much of each day's real movers the system catches.
5. Build the controls for LATCH-OPEN and L3-OUT before their forward reads begin.

## Confirmation: nothing existing was touched
- All work is on the new branch `explore/2026-11-27`, inside `/exploration/` only. `git diff be8e648c04..explore/2026-11-27 -- . ':!exploration'` is empty.
- No commits from this session went to any other branch. The only new commit on `claude/intraday-trading-system-witis4` overnight is the scheduled 00:00 ET tags1 job (f5a2626587).
- No config, account, order, deploy, restart or scheduled job was changed. Alpaca was read only (GET).
- The prepared changes were test-applied only in throwaway copies, which were deleted. Nothing was committed or merged.
- The owner's checkout `/home/user/MCF` is clean.
- One process note: a few merge commits on the explore branch carry git's default message without the session trailer lines. They were already pushed, so they were not rewritten.

Files: [PRIOR_RESEARCH](PRIOR_RESEARCH.md) · [PROPOSALS](PROPOSALS.md) · [DECISIONS](DECISIONS.md) · [MONDAY_PLAN](MONDAY_PLAN.md) · [PROGRESS](PROGRESS.md) · findings/ (loss_anatomy, shorts_autopsy, long_edge, metrics, regime_filters, outside, dev_tactics, gapswitch, rw_target, edgehunt, critic, latchopen_monday).

Educational only — not financial advice.
