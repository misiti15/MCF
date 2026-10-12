# Playing time per setup: capacity analysis (2026-10-12)

*Educational only - not financial advice. Live numbers are paper trading. Lab numbers are entry counts on the open
two-year history. No R, P/L, or holdout was used, so no look was spent on any setup.*

Owner (2026-10-12): "We need to monitor all accounts to make sure all setups are getting enough playing time and
frequency with testing; our setup counts may be too high per account."

The monitor is built and reports per account at EOD, in `scorecard.json` (`playing_time`) and on the live page.
These notes answer the capacity question with the data we have so far.

## What failed / limits first
- **Little live data.**
  - Primary: 4 sessions (Oct 6-9). The current 11 primary setups ran only 2 of them (MF/NS from Oct 8, RW6G1 Oct 9).
  - Testing: 1 session (Oct 9), in its old windowed form. The 37-setup full-day Testing 1 starts today, so nothing
    live describes it yet.
- **Lab rates overstate live counts.**
  - Live signals/day divided by lab expected/day: 0.61 (primary) and 0.82 (Testing, Oct 9).
  - The live universe is narrower. ETB and spread checks also remove signals before they could ever collide.
  - The lab replay below is therefore an upper bound on crowding.
- **Holding time is an assumption.** Live mean hold is 118 min (primary, n 178) and 137 min (Testing, n 46).
  The replay uses 120 min and also shows two bounds: same-bar collisions only, and holding to 15:55.
- **Some setups are not in the lab data.** L3 x3, orb20_a and intraday_momentum are missing, so the Testing 1
  replay covers 32 of 37 setups.
- **Lab rates can be concentrated in a few days.**
  - RW6G1 put 226 of its 424 two-year signals on 2025-04-07. Its typical rate is 0.40/day, not 1.0/day.
  - The monitor's expected rates therefore leave out each setup's 5 busiest sessions (`expected_rates.json`).

## 1. Live: what each setup got (journals on mcf-data / mcf-data-testing)

### Primary, Oct 6-9
- **Overall:** 269 signals, 176 taken. **11 lost (4.1%)** because another setup held the symbol.
- **Other skips:** 55 spread/quote, 26 not shortable/ETB, 1 missed trigger.
- **Before the pending-entry fix (Oct 7-8),** 10 extra entries stacked on symbols already being entered. Under
  today's rule those would also have been losses, which puts preemption at about 8%.
- **Slots never bound:** the peak was 34 open of 160.

| Setup (current primary) | Sessions | Signals / taken | Taken/day | Expected/day* | Lost to others (who) | Verdict |
|---|---|---|---|---|---|---|
| RW6G1 | 1 | 0 / 0 | 0 | 0.40 | 0 | quiet - wait |
| NS1 | 2 | 4 / 3 | 1.5 | 0.92 | 0 | slow (7.5/wk) |
| MF2 | 2 | 2 / 1 | 0.5 | 1.30 | 0 | slow |
| NS5 | 2 | 4 / 4 | 2.0 | 2.41 | 0 | slow (10/wk) |
| NS4 | 2 | 2 / 2 | 1.0 | 3.05 | 0 | slow |
| NS3 | 2 | 14 / 8 | 4.0 | 3.03 | 1 (heat_fade_short) | ok |
| MF1 | 2 | 13 / 6 | 3.0 | 5.33 | 0 (took 4 from others) | ok |
| NS2 | 2 | 6 / 2 | 1.0 | 5.74 | 0 | watch (low vs expected) |
| MF4 | 2 | 9 / 6 | 3.0 | 7.24 | 1 (MF5) | ok |
| MF3 | 2 | 16 / 8 | 4.0 | 9.19 | 3 (MF1 2, MF4 1) | ok |
| MF5 | 2 | 25 / 13 | 6.5 | 15.47 | 5 (MF3 3, MF1 2) | ok |

\*Two-year lab rate, 5 busiest days left out. It assumes no competition and the lab universe.

**Former primary setups (now in Testing 1):**
- **intraday_momentum is silent:** 0 signals in 3 sessions, against about 7 expected (2.4/day in the Apr-Jun
  backtest). It probably never reaches the scan, because the index ETFs it trades may fail the universe's
  1% ATR filter. This is not verified; it needs a look before its 10-session Testing review.
- orb20_a: 2.0 entries/day against 6.8 expected.

### Testing, Oct 9 (29 windowed setups)
- **Overall:** 86 signals, 46 taken. **12 lost (14%)** to other setups.
- **RW4 (NS3 restricted to ADV >= 150M) is crowded out:** 5 of its 9 signals went to NS3, its own superset, and it
  got 0 entries.
- **Other losses within the same family:** RW7 lost 2 to RW1, MF5 lost 2 to MF3, MF2 lost 1 to MF3, ST8 lost 1 to
  ST2, and L3-fromopen lost 1 to RW2.
- **Silent that day:** 14 setups had no signal at all. That is consistent with their lab rates, which are 1 a day
  or less for the 8 ST setups, RW6G1 and L3.

## 2. Lab replay: crowding with today's setup lists (`analyze.py`, `tables/`)

### How the replay works
- **Rule:** the live one-position-per-symbol rule.
  - The earlier signal wins; on the same bar, `setup_order` decides.
  - A skipped setup does not retry that symbol that day.
  - Each account's slots and per-setup cap apply.
- **Data:** 426 sessions, first qualifying bar per symbol-day.

### Primary (11 setups)

| Hold | Signals/day (lab) | Taken/day | Lost share | Setups losing >= 25% | Setups below 15/week |
|---|---|---|---|---|---|
| same bar | 60.0 | 44.9 | 25.1% | 2 | 3 |
| 120 min | 60.0 | 41.5 | 30.9% | 3 | 4 |
| to 15:55 | 60.0 | 41.3 | 31.2% | 3 | 4 |

- **The loss is almost all inside the MarcoFlow flow-sell family:**
  - MF3 loses 55% (41% of its signals to MF1).
  - MF5 loses 55% (25% to MF1, 23% to MF3).
  - MF4 loses 29% (19% to MF1).
  - Every other setup loses 17% or less. RW6G1's 17% goes to MF4 and NS2.
- **Most of the MF loss is on the same bar** (MF3 49%, MF5 54%). These are near-duplicate rules firing together.
- **Slots full** on 2 of 426 sessions (1.1 signals/day lost on average).
- **Live, the same family lost 9 of 65 MF signals (14%) in 2 sessions,** plus 9 stacked MF entries on Oct 8 before
  the fix. The live direction matches the lab.

### Testing 1 (37 setups from today; 32 in the lab)

| Hold | Signals/day (lab) | Taken/day | Lost share | Setups losing >= 25% | Setups below 15/week |
|---|---|---|---|---|---|
| same bar | 764 | 535 | 30.0% | 10 | 5 |
| 120 min | 764 | 406 | 46.9% | 27 | 9 |
| to 15:55 | 764 | 354 | 53.6% | 31 | 13 |

**Caps:**
- At a 120 min hold, the peak was 590 positions open at once against 400 slots. Slots filled on 6 of 426 sessions.
- Losses to the caps are small: 2.3 signals/day to slots and 3.5/day to the per-setup cap of 150.
- **Symbol overlap, not slots, is what crowds setups out.** Even without the 6 busiest setups, the other 26 still
  lose 42%.

**Worst losses (120 min hold):**
- MF3-FD 88% (36% to MF5-FD).
- NS3-FD 88% (35% to RW4-FD, its own ADV >= 150M subset).
- exhaustion_short-FD 83% (63% to RW2-FD).
- exhaustion_short 75% (47% to RW2-FD).
- MF1-FD 75%.
- ST8/ST6/ST4/ST3-FD 64-67%.
- MF4-FD 62%.
- RW6-FD 60% (40% to RW6G1-FD).
- RW4-FD 56%.
- ST5-FD 50%.

**The narrow ST setups sit at the top of `setup_order` and still lose 50-67%:**
- Their same-bar loss is close to 0%.
- They lose because a full-day setup entered the symbol earlier in the session: ST2-FD, heat_fade_short (-FD) or
  heat_fade_long-FD.
- Priority only breaks ties on the same bar. It cannot protect a rare setup from full-day setups that fire earlier.

**Biggest pairwise conflicts** (signals lost per week, lab):

| Pair | Lost/week |
|---|---|
| RW2-FD / exhaustion_short-FD | 211 |
| heat_fade_short / heat_fade_short-FD | 162 |
| heat_fade_long / heat_fade_long-FD | 123 |
| RW1-FD / RW7-FD | 55 |
| heat_fade_long-FD / heat_fade_short-FD | 53 |
| MF1-FD / MF5-FD | 48 |
| MF3-FD / MF5-FD | 46 |
| NS3-FD / RW4-FD | 42 |

The windowed + full-day pairs exist because rule 20 requires former primary setups to run in their primary form
next to their -FD copy.

### How crowding grows with the number of setups
Random subsets of the Testing 1 lab setups, 20 draws each, 120 min hold:

| Setups | Account lost share | Worst setup lost share (mean) |
|---|---|---|
| 3 | 2.4% | 10% |
| 5 | 7.0% | 25% |
| 8 | 17.8% | 57% |
| 11 | 21.6% | 65% |
| 15 | 26.5% | 72% |
| 20 | 35.5% | 82% |
| 25 | 40.2% | 86% |
| 30 | 45.0% | 88% |
| 32 (all) | 46.9% | 88% |

Primary's own 11 setups lose 30.9%. Its MF family is more overlapping than a random draw.

### Rotation (Testing 1, 120 min hold)
- **Method:** groups were built greedily so that the pairs that conflict most land in different groups. Group
  members run on alternate sessions.

| Scheme | Setups losing >= 25% | Setups below 15/week |
|---|---|---|
| all 32 every session | 27 | 9 |
| 2 groups, alternate sessions | 21 | 12 |
| 3 groups, rotating | 12 | 13 |
| 11 rare setups (<= 40/week standalone) every session, busy setups in 2 alternating groups | 20 | 9 |

- **Rotation cleans up each setup's sample:** 3 groups cut the setups losing a quarter or more from 27 to 12.
- **It costs playing time:**
  - Each setup runs 1/3 of the sessions, so the rare ones fall to 1-5 trades/week.
  - The ST setups already reach only 2-11/week, even uncontested at 5-19/week, with RW6G1 at about 2/week typical.
  - No arrangement gets them to 15/week, because they are rare by construction.
  - At their standalone rates, 60 trades takes 3-12 weeks for most rare setups; RW6G1 needs ~30 weeks at its
    typical 0.4/day.

## 3. Recommendations
These are proposals to the owner. Changing which setups run on which day changes which trades are taken, so it goes
through the backlog and ledger and is merged after the close. Nothing here was shipped.

1. **Primary: 11 is not too many for capacity.**
   - Slots peaked at 34 of 160, and the slot cap bound on only 2 of 426 lab sessions.
   - The problem is the four MarcoFlow flow-sell variants (MF1/MF3/MF4/MF5), which overlap heavily: MF3 and MF5
     lose about 55% in the lab.
   - Proposal: run at most 2 of MF1/MF3/MF4/MF5 in primary at a time and move the other 2 to Testing. Or keep all 4
     but judge MF3/MF5 on taken + what-if trades: skipped signals are already simulated by the runner's what-if pass.
   - Rule of thumb: **no more than 2 variants of one family per account**.
2. **Testing 1: 37 is too many for clean per-setup samples.**
   - Lab estimate: 47% of signals lost, and 27 of 32 setups lose at least a quarter of their population.
   - Recommended: **3 rotation groups of about 12 setups**, built from family conflicts (`results.json` ->
     `lab.testing.rotation.3.groups`).
     - Each pair in the table above goes into different groups: windowed/FD, NS3/RW4, NS2/RW6/RW6G1,
       MF1/MF3/MF5, RW1/RW7, RW2/exhaustion.
     - That cuts the setups losing a quarter or more from 27 to 12.
     - Each group still has about 12 setups, the size where account-level loss is about 22% (curve above).
   - Trade-off: rare setups then get only 1-5 trades/week. If volume matters more, keep the 11 rare setups every
     session and rotate only the busy ones (row 4 of the rotation table).
3. **Max setups per account:** about **12 for a random mix**, for an account-level loss of 25% or less. Fewer when
   setups come from one family. More only if their symbol overlap is checked with `analyze.py` first.
4. **Judge rare setups by time, not by setup count.** RW6G1, NS1, MF2 and the ST setups expect at most about 1 entry
   a day in the lab (less live). They need several weeks to reach 60 trades whatever else runs, so the scorecard's
   4-session window will show them as "too few trades" for a long time. The monitor marks them "slow" with the weeks
   needed, instead of "starved".
5. **Testing 2 (~30 CWT setups) and the S6 long-hold account:**
   - The monitor works per account with no change. Each account's EOD writes its own `playing_time`, and the page
     reads `?account=<name>` -> branch `mcf-data-<name>`.
   - Before Testing 2 goes live, add its CWT setups to the lab trade set and run this replay. At about 30 setups,
     expect about 45% loss unless the families are split.
6. **intraday_momentum** produced no signal in 3 live sessions against about 7 expected. Check whether its ETFs
   reach the scan (universe filters) before its 10-session Testing review.

## Files
- `analyze.py` reproduces everything.
  ```
  python research/bdi/playingtime/analyze.py --primary <journal.db> --testing <journal.db> --state-primary <dir> --state-testing <dir>
  ```
  The journals come from `git show origin/mcf-data:journal.db`. The state dirs hold `setups/<date>.json` from the
  same branches.
- `results.json` has the live reports, the lab scenarios, the conflicts, the curve and the rotation groups.
- `tables/*.csv` has per-setup tables for each scenario.
- `expected_rates.json` holds the expected entries/day the monitor uses (5 busiest sessions left out).
- The monitor itself:
  - `mcf/report/playing_time.py` builds the report.
  - It appears in the EOD section "Playing time", in `scorecard.json` -> `playing_time`, and in the
    `docs/live/index.html` card.
  - The runner logs `held_by` on "already in symbol" skips. This is logging only.

**Configurations tried:**
- 3 holding assumptions x 2 accounts.
- 9 subset sizes x 20 random draws.
- 4 rotation schemes for each account.
- Plus one check that leaves out the 6 busiest Testing 1 setups.

These were entry-count replays only; no setup was scored.
