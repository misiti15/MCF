# LATCH review 2026-11-17 — notes

*Educational only — not financial advice.* Research only. The owner's request (2026-11-17 ~13:45 ET): "LATCH review
yes … certain setups do need certain conditions … a -2R cap across the entire board may be a great safety gate but it
also could hinder some setups if we want to open it slightly."

## How to reproduce
1. Copy journal.db from each state branch to `<dir>/<branch>.db`.
2. `python -I research/latch_review_1117/fetch_opens.py <dir> opens.csv` fetches Alpaca SIP daily bars with GET
   only, using the env keys, which are never printed.
3. `python research/latch_review_1117/analysis.py <dir> opens.csv <out>`.

The run used the journals as of 2026-11-17 after the close (state-branch heads listed in the commit message).

## Method details and choices
- **Blocked signals:** the signals table journals every latch skip twice, so skips are deduplicated on
  (ts, symbol, setup). That leaves 551 skips. The runner's what-if engine (run_id 2,
  `why=setup daily loss limit`) simulated 549 of them. The two without a what-if are On Deck 10-20 signals and are
  left out. No 1-minute bar replay was needed.
- **Costs:**
  - What-if R has the entry slip modelled, but the exits are raw.
  - Each what-if is charged the setup's measured live gap in that account (mean r_raw − R after costs) when the
    setup has at least 10 live trades there, and 0.05R otherwise.
  - Live trades use mcf.costs.cost_r: the LR8 model from 11-12, the flat allowance before.
- **Lot cap:** at most 3 lots per symbol per account. Live lots from every setup count, plus hypothetical lots
  already accepted. A trade on the opposite side of a held lot is refused. 42 of the 549 what-ifs were dropped.
  Today's Primary L3 example: 9 BEZ + 5 AGL what-ifs left 4 BEZ + 3 AGL; the day's R with no latch was +1.95R
  against −1.97R at −2. The brief's rough replay gave +0.4R with the cap, marked at 13:31; this run marks at 15:54.
- **Latch timing:** a stop fill only reaches the journal at the next poll. The replay therefore starts a latch (and
  the account halt) 2 minutes after the exit that triggers it.
  - The 2-minute lag was calibrated on Primary 10-29..11-17 at the −2 level: lags of 0 / 1 / 2 / 3 / 5 / 7 / 10 min
    gave total |sim − real| of 8.0 / 10.3 / 2.1 / 3.8 / 8.1 / 13.4 / 23.7R over 15 days. 2 minutes was best.
  - The remaining gaps: Primary 11-05 −1.1R and 11-10 −1.0R. On Deck / Testing A on 10-22 show +4.5R / +4.0R,
    because before LL-LATCH (effective 10-23) the per-setup stop was not sticky and a setup that recovered could
    trade again.
- **What counts as R for the stops:**
  - Primary from 11-12 counts R after costs (LR3); everything else counts raw R.
  - The account halt is 20R in Primary. In On Deck, Testing and Gen it is 120R before 11-12 and 300R from 11-12
    (60R in On Deck before 10-19).
  - Primary's LR3 open-mark halt is approximated with realized R only.
  - Extra hypothetical lots do not take slots away from other setups.
- **Which days count as A (actual):**
  - Primary from 10-29: the journal has no latch skips in Primary before ST-P.
  - On Deck, Testing A and Gen on 10-20..10-22.
  - Any setup-day that journaled latch skips.
  - Every other crossing of −2R is B (virtual), where post-cross trades are real fills.
- **Remedies:**
  - Tested on live trades only, removal only.
  - REENTRY counts 5-minute decision bars after the stop's exit time. A removed trade's own stop does not extend the
    block.
  - FADEMOVE uses entry / SIP daily open − 1, against the trade direction (2 trades had no open).
  - Removing re-entries on a latch day could delay the latch. That second-order effect is not modelled.
- **Configurations:** 10 in total, as in PLAN.md. No holdout was used: this is a review of live records, not a fit.
  The −2 level is the baseline.

## Rule changes inside the window (research/ledger.jsonl, effective dates)
- 10-19: Setup Generator account opens.
- 10-20: per-setup −2R stop (`2026-10-20-twin-cap-setup-loss`), not sticky; the journal shows it acting in On Deck,
  Testing A and Gen on 10-20..10-22, and not in Primary.
- 10-23: LL-LATCH makes the stop sticky (`2026-10-22-setup-stop-latch`). ST-A turns it off in Testing 1/2 + Gen
  (`2026-10-22-testing-setup-stop-off`).
- 10-28: Primary sizing at ~$4k, 77 slots, per-setup cap 30.
- 10-29: ST-P, −2R latch in Primary only (`2026-10-28-primary-setup-daily-stop-2R`).
- 10-30: Testing cost filter CF. L3-fromopen re-promoted and L3-rsi5hi promoted to Primary.
- 11-04: UNI1, top-500 pool in Testing A; removed 11-12.
- 11-05: Explore 1 / Live Lab (Testing B/C) open.
- 11-11: TEAM-6 lineup in Primary, open-ended from 11-16.
- 11-12:
  - LR3: Primary's stops count R after costs.
  - LR8: live cost model, so R after costs is about −0.04R per trade lower from here on.
  - Halts 120 → 300R outside Primary.
  - Testing D/E/F open.
  - Generic per-setup cap 30 in Testing B–F.
  - On Deck build.
- 11-16: RW7 On Deck → Testing F. RW3S Testing E → Graveyard.
- 11-17:
  - TSZ1 half-size lots in Testing A–F: R is comparable, $ is not.
  - Shadow mode: run 3, not used here.
  - SPYEXIT engine (Live Lab / Testing D WB4 copies).
  - Workbench copies (-WB*) added to Testing A–F.

Setup results that straddle these dates mix rule regimes. The biggest effect: the latch-on/off status per account
decides whether a day is in sample A or B.

## Reading the evidence
- The what-if sample (A) and the real-fill sample (B) disagree. A is +0.09R per post-latch trade; B is −0.15R. A is
  simulated (rule 7: paper/sim labelled apart), smaller (507 trades) and dominated by a few big days: On Deck RW7
  10-22 +50R, MF1 10-20 +17R. B is 2,912 real paper fills. The board-wide conclusion rests on B.
- The −2 latch is net positive overall. It is not positive for every setup: 27 of 153 setups do better with no latch,
  and 35 do better at −3. Most of those gains are small or carried by one day.
- RW7 is the one clear exception:
  - 15 latch days and 12 days with post-latch trades.
  - 1 trade per symbol, top symbol 2% of the post R.
  - It wins without its best day too.
  - It is a short-the-bounce setup whose afternoon trades recover a bad morning.
  - It only matters if RW7 lands in a latched account. The Graveyard review after 3 Testing F sessions
    (11-16..11-18) is exactly that case.
- Optimism check: the L3 BEZ failure mode is real but rare. Re-entry after a stop by the same setup on the same
  symbol is only 44–60 of 16,768 trades. Those re-entries won on average, so blocking them costs more than it saves.
  The more promising lever for L3's squeeze days is outside this review's scope: for example the lot cap per setup
  per symbol (Primary L3 already has the generic 3), or an exit change. Any such idea goes to the backlog.
