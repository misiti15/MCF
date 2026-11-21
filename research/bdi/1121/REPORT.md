Educational only — not financial advice.

# BD&I Saturday deep run 2026-11-21 (week 11-16..11-20)

Live numbers are **paper** trades (engine label: Live), R after costs on the single LR8 basis (rule 32). Every trade
this week is after 11-12, so the figure equals the journal's booked R. Each backtest number carries its engine label.
The locked block 2024-11-01..2025-02-28 was never read. No config, setup, exit, assignment, decisions.json or ledger
change was made, and nothing was committed. The 7 new backlog lines (and the re-rendered BACKLOG.md) are the only
edits outside this folder. Scratch data was deleted at the end.

**Configurations tried tonight: 18** (16 rework + 2 give-back remedy). **0 pass**, so there is no Testing admission
and no live change. 4 Move Hunt ideas were filed as backlog candidates (untested).

**Today's win:** two failure modes are now closed by evidence rather than guesses.
1. The beginner batch's two near misses (BEG-06, BEG-04) do not survive a rule-18 rework. Their edge, if any, lies
   in the choice of day, not in the trigger, stop or target.
2. The 11-20 NM-ETF stack (12 correlated ETF lots, −12.6R) is the price of that setup's best two-year trades.
   Capping the stack costs NM-ETF −38.6R on FIT.

Neither needs more time next week.

## Rule changes around these dates (research/ledger.jsonl): read every figure with these in mind
- **11-12 LR8:** new live cost model, about −0.04R per trade against the old basis. Primary's −2R latch and −20R halt
  count R after costs. On Deck was built, Testing D/E/F went live, and the account halt outside Primary became 300R.
- **11-16:** TEAM6 made open-ended in Primary. RW3S → Graveyard. RW7 On Deck → Testing F. Arena rotation block 1
  ran to 11-19.
- **11-17 TSZ1:** Testing A-F trade half-size lots with 2x slots, so R is comparable across the change but $ is not.
  Also the SPYEXIT engine, 15 Workbench copies in Testing A-F, and the promotion hold.
- **11-18/11-19:**
  - GY-BENCH (18 Graveyard setups benched to 11-24) plus guests.
  - **C3-NS5: NS5 moved Primary → On Deck from session 11-19, so Primary runs 5 setups from 11-19.**
  - C3 epoch 1 / BASE1, GY-ARCHIVE-20, the U9 quote checks, TAGS1.
- **11-20:** arena rotation block 2; FOOTRACE / GY foot race; the ultimate_1119 admissions in Testing A-F.
- **Effective 11-23, after this window:**
  - ST7 Primary → On Deck, so Primary = NM-ETF, RW5, RW3, L3-fromopen.
  - BRAKE-BURST: at most 30 new entries per setup in any rolling 10 minutes, in every account.
  - Watchdog "act" mode.
  - FOOTRACE-EXIT moves 12 setups to the Graveyard; RETIRE-R3 retires 12.
  - BEG-ORB / BEG-GNG go to testing; Remedy-Q testing copies start.
  - LATCH-CLOSE was answered no.

## 1. Weekly discover workflow (bar cache refresh + backlog re-test)
- **This week's run has not happened yet.** The `discover` workflow is scheduled for Sat 14:17 UTC, and no run for
  11-21 was listed at 15:49 or at 16:25 UTC (the last check).
  - GitHub's cron has been late before: last week's scheduled run started at 19:13 UTC, about 5 hours late.
  - Until it runs, the bar cache and the backlog re-test stay as of 11-14.
  - **Re-check on Sunday. If there is still no run, dispatch it by hand.** That is the owner's call; this run is
    read-only on GitHub.
- **Last completed run: 11-14 scheduled run [43630905330](https://github.com/misiti15/MCF/actions/runs/43630905330),
  success, 25 minutes.**
  - Steps: Mine ✓; "Refresh bars to the last session" ✓ (lab cache: 1,226 symbols, 107 sessions 2026-06-15..2026-11-13,
    locked block excluded); "Re-test the strategy backlog" ✓ (success, 120 s).
  - **Caveat:** of 380 runnable entries it scored 66 and skipped 314. Of those, 312 have no lab module, 1 failed to
    import (mh-1029-earnings-sympathy: module path), and 1 failed on a missing column (`rsis_3` in
    rw-vf2_rsis3_fast10). The weekly re-test therefore covers about 17% of the runnable backlog. The two named
    failures are housekeeping fixes.
  - The same day's workflow_dispatch run [43613211159](https://github.com/misiti15/MCF/actions/runs/43613211159) also
    succeeded.
- **store-bars:** the nightly runs this week all succeeded. The latest is the 11-21 02:50 UTC scheduled run
  [44857993793](https://github.com/misiti15/MCF/actions/runs/44857993793); the 11-19/11-20 chained runs 26-32 were
  all successful.

## 2. Rule-18 rework round (pre-registered in `rework/PLAN.md` before any scoring)
**Choice.** I excluded everything on the final1121 do-not-re-run list and every give-back exit class from 11-19.
Among the remaining failed ideas, the two closest to the bar on the normal-way engine are the beginner batch's NEAR
misses: BEG-06 `notrail` and BEG-04 `gap25` (research/beginner_1120). Each gets 8 configs, aimed at the failure mode
its RESULTS.md names.

**Engine.** E4-normal-way, using the beginner runners and their bench10 book unchanged: LR8 costs plus 1.2 bp
borrow; the testing-arena book (cap 100, at most 3 lots per symbol, ETB, 0.15R stop-cost filter); 1-minute signals
and exits.
- FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..2026-11-04.
- The FIT pick was chosen mechanically and scored on CHECK once. This was look 3 for each lineage, so the bar is
  t ≥ 2.0.
- The BEG-04 day table was rebuilt with BEG-02's own build code. The base FIT matches exactly: 1,860 trades, +0.1062.
- T2 was not run.

**BEG-06 noise-area breakout (SPY/QQQ). Failure mode: costs (~0.10R a trade) eat a real pre-cost edge.**

| config | change | FIT n | FIT avg R | FIT w/o best day |
|---|---|---|---|---|
| base | beginner base | 265 | −0.095 | −0.152 |
| notrail | beginner pick (CHECK −0.013 already seen) | 217 | −0.083 | −0.152 |
| R6a | stop 0.375 ATR | 197 | −0.095 | −0.146 |
| R6b | stop 0.50 ATR | 187 | −0.061 | −0.122 |
| R6c | stop 0.375 + trail | 259 | −0.080 | −0.118 |
| R6d | band ×1.25 | 176 | −0.096 | −0.177 |
| R6e | band ×0.75 | 271 | −0.073 | −0.149 |
| **R6f** | **hourly checks (FIT pick)** | 166 | **+0.003** | −0.092 |
| R6g | one entry a day | 171 | −0.162 | −0.194 |
| R6h | stop 0.375 + band 1.25 | 157 | −0.069 | −0.134 |

- **R6f on CHECK: −0.088R** (n 331, t −0.93). W/o best day −0.127, w/o top 2 days −0.159. QQQ −0.008, SPY −0.162.
  Flat-SPY days −0.90. **FAIL**, worse than the beginner's own pick.
- Wider stops did not cut cost per unit of edge: gross R fell with them (R6a gross −0.021 against notrail +0.029).
- Lineage: 12 configs, 3 CHECK looks used. Parked.

**BEG-04 quiet gap fade. Failure mode: the trigger is late, and the day choice carries the edge.**

| config | change | FIT n | FIT avg R | FIT w/o best day |
|---|---|---|---|---|
| base | beginner base | 1,860 | +0.106 | −0.001 (2025-04-08 = 100% of FIT R) |
| R4a | target 0.5 × gap | 319 | −0.043 | −0.138 |
| R4b | target 0.75 × gap | 1,082 | +0.132 | +0.023 (fails plateau: R4a) |
| R4c | 1.2R test → 0.8R | 2,947 | +0.033 | −0.031 |
| R4d | stop ×1.5 | 981 | +0.039 | −0.070 |
| R4e | ATR cap 0.50 | 1,467 | +0.060 | −0.055 |
| R4f | rvol / rank filter removed | 3,091 | +0.106 | −0.004 |
| **R4g** | **gap ≥ 2.0% (FIT pick)** | 1,409 | **+0.185** | +0.046 |
| R4h | target 0.5 + stop ×1.5 | 111 | −0.222 | −0.295 |

- **R4g on CHECK: −0.034R** (n 3,375, t −0.42). W/o best day −0.087, w/o top 2 days −0.124. Shorts −0.082,
  longs +0.007. The best days were 2026-04-02 (+170R) and 2025-11-20 (+111R).
- **FAIL** on the pass. Against the top-10 standard it is NEAR: CHECK w/o best day misses −0.078 by 0.009, the same
  place gap25 landed.
- Every FIT figure is the April-2025 tariff week (`1 day` on all of them).
- Lineage: 12 configs, 3 CHECK looks used. Parked.

**Salvage (looking for the next step, not a proposal):**
- Both ideas agree with the beginner and final1121 finding: the profitable pockets are a handful of trend or
  gap-fill days.
- What would be worth testing is a pre-09:50 day-type condition that picks those days, which is a C3-MECH item.
  Another trigger, stop or target tweak would not help.
- The only stable fact here is that QQQ beat SPY in every BEG-06 window. It was seen on CHECK, so it is not usable
  as a rule without a fresh holdout.

## 3. Move Hunt scan: new setup ideas (`scan/NOTES.md`; backlog status "idea", untested)
**Capture, 11-17..11-20** (moves.csv, top 25 per side per day; 11-16 is missing from the library):
- Long side: 1 of 100 big moves caught (+0.2R).
- Short side: 10 of 100 caught (+19.4R).
- Misses: no setup signalled 74; traded the name outside the move 57; earnings blackout 31; wrong side only 14;
  spread or cost filter 10. 103 of the 200 moves decided by 09:45.

The ideas, each with its evidence:

1. **mh-1121-peer-cluster-laggard.** Managed care moved as one group on 11-18 (UNH, HUM, ELV, MOH, CNC, CVS, all
   top-25 shorts) and again on 11-19 (CI, UNH), with 4 earlier sessions in the library. The setup trades the group
   members that have not moved yet. It must report its overlap with parked mh-1102.
2. **mh-1121-crypto-complex-follow.** On 11-20, 5 spot-crypto ETFs were top-25 shorts and 2 inverse crypto ETPs
   were top-25 longs. The library has 12 rows on 5 days, 33% of them caught against 5% for all moves. It is not the
   cap-etp family.
3. **mh-1121-defensive-rs-weak-open.** Long capture was 1/100. Several of the long movers were defensives on weak
   opens (CPB, EIX on 11-17; EGP, CTRE on 11-18). This is the mirror of mh-1106.
4. **mh-1121-spread-skip-execution.** 10 of the 200 big movers were skipped on spread or the stop-cost check. The
   idea is a limit-at-mid entry, scored as a paired what-if on the recorded quotes.

Not filed:
- Vol-ETP longs (UVXY/UVIX/VXX on 11-17 and 11-20) are on the cap-etp do-not-re-run list.
- Single-name news pops (GPN, WING, CPRT) share no precursor.

## 4. Week scorecard 11-16..11-20 (`week.py` → `week_out.txt`, `week_scorecard.csv`)
**Primary is the scoreboard. The other account totals are context only** (owner 2026-11-20). Live engine; R after
costs, LR8 basis. Account R = Alpaca $ ÷ 0.25% of equity (display only).

| account | R | trades | avg R | w/o best day | green days | R by day 16 / 17 / 18 / 19 / 20 | Alpaca $ (account R) |
|---|---|---|---|---|---|---|---|
| **Primary** | **+4.1** | 193 | +0.021 | −0.156 | 2/5 | +25.3 / −2.5 / −5.5 / −16.2 / +3.0 | **+$766.61 (+3.6)** |
| On Deck | −45.5 | 313 | −0.145 | −0.192 | 2/5 | +4.7 / −39.8 / −7.6 / −13.0 / +10.2 | −$419.45 (−1.8) |
| Testing A | −66.5 | 1,212 | −0.055 | −0.137 | 1/5 | −20.3 / −51.9 / −56.8 / −5.3 / +67.9 | −$833.54 (−3.6) |
| Testing B | +41.3 | 514 | +0.080 | −0.151 | 1/5 | −7.4 / −3.7 / −6.6 / −31.4 / +90.4 | +$647.11 (+2.5) |
| Testing C | −157.6 | 458 | −0.344 | −0.384 | 0/5 | −7.7 / −5.5 / −12.4 / −11.8 / −120.3 | −$888.73 (−3.6) |
| Testing D | −41.1 | 513 | −0.080 | −0.092 | 2/5 | +0.4 / −33.1 / −0.6 / +1.6 / −9.4 | +$128.01 (+0.5) |
| Testing E | −13.5 | 262 | −0.051 | −0.122 | 1/5 | −6.4 / −5.0 / −10.4 / −0.3 / +8.6 | +$262.14 (+1.1) |
| Testing F | +9.5 | 604 | +0.016 | −0.008 | 2/5 | +13.4 / −10.5 / −2.5 / −3.9 / +13.0 | +$313.24 (+1.3) |
| Gen | −211.8 | 602 | −0.352 | −0.427 | 1/5 | +17.0 / −128.7 / −8.2 / −16.4 / −75.4 | −$2,122.88 (−9.6) |
| Graveyard | −575.5 | 2,048 | −0.281 | −0.296 | 0/5 | −104.6 / −177.4 / −23.0 / −79.5 / −191.0 | −$2,858.75 (−12.7) |

**Primary**
- The week is +4.1R / 193 trades and +$766.61, matching the QA 11-21 re-derivation (+4.1R, about +$756, 193).
- **It is a `1 day` week:** 11-16 made +25.3R, and without it the week averages −0.156. It is better than the
  prior week (−37.5R / 266, mixed cost basis).
- Per setup (one-big-day check):
  - **L3-gap-slope-fromopen-FD** (Gap-Down Recovery Fade, all day): +11.5R / 70, avg +0.164, w/o best day −0.126,
    `1 day` 143% (11-16 +16.4R).
  - **RW5-heat30-flowsell-rsi5pop-gapdn-short-FD** (Gap-Down Pop Fade, all day): +8.2R / 34, +0.242, w/o best day
    +0.136, `1 day` 52%.
  - **RW3-gapdn-rsi5pop-flowsell-short-FD** (Gap-Down Pop Fade, Heavy Selling): +6.3R / 43, +0.147, w/o best day
    +0.023, `1 day` 87%. RW3 and RW5 count as about one bet (CORR1, daily corr 0.76).
  - **NM-ETF-late-dip-di-long** (Late-Day ETF Dip Buy): −12.1R / 24, −0.504. All of the loss is 11-20 (−12.6R:
    12 lots stopped together).
  - **ST7-rsi50dn-long-pm-t1s1-FD** (RSI Collapse Dip Buy): −9.7R / 16, of which 11-19 was −8.7R. It leaves Primary
    11-23.
  - **NS5** (Big Loser Flush Buy): −0.2R / 6, in Primary to 11-18.

**Other accounts (context only)**
- Testing B (+90.4R) and Testing A (+67.9R) on 11-20 came almost entirely from two GEN PM short setups:
  GEN-261022-05 +133.2R (`1 day` 91%) and GEN-261026-07 +100.6R (`1 day` 94%).
- The biggest losses were GEN-261027-06 in Testing C (−132.3R, 11-20 alone −120R) and the Gen / Graveyard GEN long
  setups.
- Testing F's best was RW7 (+74.1R / 305, w/o best day +0.135).

## 5. Weekly give-back review (`giveback.py` → `giveback/giveback_week.csv`, `giveback_setups.csv`, `caps_week.csv`, `giveback_out.txt`)
**Method.**
- The curve is the runner's per-poll mtm snapshots: realised R plus the open lots' marks, after costs.
- Peak is the day's highest marked total; give-back = peak − close.
- The peak→close move is split into: lots open at the peak (final booked R − mark at the peak), entries after the
  peak, twins (same symbol and side entered by another setup ≤ 3 min earlier), and late flatten.
- Live engine; descriptive.

**Primary in detail (total give-back 44.3R)**

| day | peak (time) → close | give-back | open lots at peak | entries after peak | what gave it back | max entries in 10 min |
|---|---|---|---|---|---|---|
| 11-16 | +26.9 (15:44) → +25.3 | 1.6 | −2.0 | 0 | L3 lots −3.0 | 8 |
| 11-17 | never above 0 → −2.5 | 2.5 | 0 | −2.5 (22 entries) | RW3 −2.5, NS5 −1.9, L3 −2.0; RW5 +4.3 | 5 |
| 11-18 | +6.9 (14:40) → −5.5 | 12.4 | −11.6 | −0.8 | open RW3 −4.9, L3 −3.0, RW5 −1.2 | 9 |
| 11-19 | +8.1 (11:42) → −16.2 | **24.3** | **−19.6** (winners −22.0) | −4.8 | open ST7 −13.4 and L3 −9.3 stopped after the 11:50 index drop; RW5 −3.0 after | 7 |
| 11-20 | +6.5 (13:49) → +3.0 | 3.5 | +8.0 | **−11.6** | **NM-ETF: 12 lots 14:11-14:16 ET, all stopped (−12.6R)** | 13 |

- **What gave it back:**
  - Open winners stopped: −25.2R of the 44.3, mostly 11-19 ST7 and L3.
  - New entries after the peak: −19.6R, mostly the 11-20 NM-ETF stack.
  - Twins: −0.5R.
  - Late flatten in the tail: +6.9R (it helped).
- **Timing / bursts:** Primary never exceeded 13 entries in any 10 minutes, across all setups. **BRAKE-BURST (30 per
  setup per 10 min, from 11-23) would not have bound in Primary this week.** It is aimed at the testing / Gen bursts:
  Gen 11-17 had 154 entries in 10 minutes; Graveyard 11-16 had 138 and 11-20 had 143; On Deck 11-17 had 49.
- **Per-setup −2R latch (Primary).** 62 signals were blocked. Their engine what-if R (run 2, costs in) is +2.8R
  net, so **the latch cost about 2.8R this week**:
  - it saved 19.6R on 11-19 (L3 would have lost a further 20.6R);
  - it cost 14.3R on 11-17 (L3 +8.3, RW3 +6.0), 6.1R on 11-18 and 2.0R on 11-20.
  - In the Graveyard it blocked 2,171 signals worth −257.9R, so it saved 257.9R there.
- **Twin-exposure cap:** no Primary block this week. In the Graveyard, 40 signals were blocked; they would have made
  +19.7R, so the cap cost 19.7R there (heat_fade_short-FD +13.3R on 11-17). It neither helped nor hurt Primary.
- **Other accounts (week give-back):** On Deck 98.5R (open winners −70.1R: MF2-FD −27.6R, RW1-FD −17.2R);
  Testing C 185.7R (GEN-261027-06 −84.6R open plus −38.0R after); Gen 322.7R; Graveyard 599.1R. Most of the testing
  give-back sits in setups that already lose (GEN longs, CWT14-pdl, MF2-FD). Exits and moves address those; a book
  rule does not.

**Proposals: tested remedy (pre-registered `giveback/PLAN.md`, `groupcap.py` → `groupcap_results.csv`, `groupcap_out.txt`).**
- **The remedy:** a correlated-group lot cap aimed at the 11-20 failure mode, a stack of near-duplicate ETF lots.
  Symbols whose FIT-period daily returns correlate ≥ 0.85 count as one symbol for the per-setup lot cap.
  GC1 allows 1 lot per group; GC2 allows 2.
- **Engine:** E4-normal-way, using the bench10 book on the 11-19 top-10 benchmark T1 signals (home-account rules,
  FIT/CHECK).
- **Result: both FAIL.**

| config | target setup NM-ETF FIT / CHECK ΔR | trades kept (NM-ETF) | all 11 setups CHECK: better / worse | total CHECK ΔR | vs random removal | live week Primary (descriptive) |
|---|---|---|---|---|---|---|
| GC1 (1 per group) | **−38.6 / −6.6** | 54% / 82% | 5 (+109.4R) / 6 (−49.3R) | +60.2R, almost all from cutting 40% of L3-fromopen (top-decile winners kept 44%) | L3 gain below every random draw | 57 lots blocked, +4.0R |
| GC2 (2 per group) | **−31.6 / −0.6** | 68% / 95% | 2 (+25.5R) / 9 (−40.0R) | −14.5R | — | 26 lots blocked, +6.4R (11-20 NM-ETF +6.2R) |

- **Why it fails:** NM-ETF's simultaneous late dips are its best two-year trades. A cap that would have saved about
  6R on 11-20 costs that setup 31-39R on FIT.
- This is the same verdict as BURST1/2, sat1114 G1-G4 and giveback_1119: trading less of a stack is not an edge.
- **No give-back proposal survives this week**, so there are 0 of the allowed 2.
- The 11-19 open-winner loss belongs to the exit classes that failed on 11-19 (chandelier, trail, clock, SPY-turn),
  and ST7 leaves Primary on 11-23. It was not re-tested.

## 6. Plan for next week
- **Discover:** confirm today's scheduled run, or dispatch it if it has not run by Sunday. Fix the 2 broken backlog
  entries (mh-1029 module path, `rsis_3` column) as housekeeping. Scope a lab-module path for the 312 skipped
  entries, since the weekly re-test sees only about 17% of the runnable backlog.
- **New lineup from 11-23:** read Primary (NM-ETF, RW5, RW3, L3-fromopen) daily against BASE1 (c3score). Watch
  NM-ETF's stacked-lot days: they are its edge on two years, so the job is to watch them, not cap them.
- **BRAKE-BURST:** after 5 sessions, count how often it bound per account. This week it would have bound only in
  Gen, Graveyard and On Deck.
- **Move Hunt ideas:** pre-register and screen (E2 2-year) mh-1121-crypto-complex-follow and
  mh-1121-peer-cluster-laggard first. Both are C3-MECH day-type candidates, and long-side capture (1/100) is the
  week's clearest gap.
- **Day-type selection for the near misses:** the rework says the edge of BEG-04 / BEG-06 is in which days, not the
  trigger. A 09:50 day-type gate built as a new setup, not a filter on a live one, is the only follow-up worth a slot.
- **Give-back:** no new book rules. Keep logging the latch / twin-cap what-ifs weekly. The 11-19 GB-GENTRAIL (GEN
  hold-setup trail) remains the one untested exit pocket, pending lab GEN hold lists.
- **Saturday 11-28 (holiday week):** the half-day 11-27 flatten is at 12:55 (LR1). The week scorecard will have
  4.5 sessions.

Scripts: `week.py`, `giveback.py`, `giveback/groupcap.py`, `rework/rw06.py`, `rework/rw04.py`,
`rework/build04days.py`, `add_backlog.py` (+ `backlog_new.json`). Pre-registrations: `rework/PLAN.md`,
`giveback/PLAN.md`. Picks: `rework/beg06/pick.txt`, `rework/beg04/pick.txt`.

Educational only — not financial advice.
