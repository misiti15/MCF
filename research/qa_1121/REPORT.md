Educational only — not financial advice.

# QA report: week 2026-11-16 to 11-20

## 1. Overall verdict

**The headline numbers are right. The system is mostly set up correctly for Monday. Five things need action before the 11-23 09:30 ET open.**

- **Primary's week figures are correct.** I re-derived all of them independently: +4.1R, about +$756, 193 trades. Friday was +3.00R / +$214.16. Since 10-23 it is −66.0R and +$313, with 7 of 21 days green.
- **The main problem is a cost bug in shared code.** The tool that loads live trades charges the old, smaller cost on every trade before 11-12, even though it says it charges the current cost. So any record that starts before 11-12 looks better than it really is. That includes:
  - the per-setup records in the owner inbox;
  - the ST7 figure you are deciding on;
  - the Friday exit list;
  - the promotion candidates in the final1121 study.
- **This week's numbers are not affected**, because every trade this week is after 11-12.
- **No decision you already made flips because of the bug.**
- **Separate from the bug:** one Monday change (the Remedy-Q copies) went further than your conditional approval allowed. And the watchdog you approved for "act" mode is barely running during market hours.

**Rule changes around these dates** (from the ledger):
- **11-12:** the current cost model (LR8) took effect. This is why records that start before 11-12 are mixed.
- **11-23:** these all take effect: BRAKE-BURST, watchdog "act" mode, the BEG-ORB / BEG-GNG setups, the Remedy-Q copies, the 12 Friday exit moves and the 12 retirements.
- **During the week itself:** I found no change to setups or exits.

## 2. Areas

| Area | Result | In one line |
|---|---|---|
| Primary numbers (week, Friday, since 10-23) | **PASS** | Every headline matches. Three wording and labelling slips. |
| Merged changes (PRs #236–#239) | **FAIL** | Code and config match the ledger. But the watchdog hardly runs, and the ledger check required by the rules has not been run. |
| Research: null study, retire rule, brake, NM-ETF | **FAIL** | The null study reproduces exactly. The cost-basis bug affects the retire and NM-ETF reports. The retire rule as you adopted it was never tested on its own. |
| Research: setups (Remedy-Q, ST7, BEG, latepb) | **FAIL** | Remedy-Q is labelled "confirmed" and was built even though your condition was not met. Some figures are on the old cost basis. |
| Decisions card and owner inbox | **FAIL** | Several decision cards are stale or already done. The NM-ETF card shows old positive figures. |
| final1121 (140 configurations, nothing passed) | **FAIL on numbers, PASS on conclusion** | Live figures are overstated by a separate cost bug. "Nothing passed" still holds, and holds more firmly. |

## 3. Confirmed issues, most serious first

### Critical

**C1. The live-trade loader charges the old cost on trades before 11-12.**
- **Where:** `mcf/report/footrace.py:358`. The query leaves out five columns the cost code needs: side, target, exit, exit_reason and meta. The cost code then hits an error, swallows it silently (`mcf/costs.py:194`), and keeps the old cost.
- **Effect on records:**
  - All accounts: −3,703R as shipped, against −4,444R with the correct cost.
  - Your Primary figures change: RW3 +0.175 → **+0.151**, RW5 +0.109 → **+0.078**, L3 +0.200 → **+0.191**, ST7 −0.149 → **−0.165** R per trade.
  - For ST7-MOVE, the ST7 review uses the correct cost (−0.174 through 11-19). The brief and nightly use the old one (−0.149). So you see two different numbers for one decision. The true distance to the −10R line is **2.9R**, not 3.6R.
- **Effect on the Friday exit list:** re-run with the correct cost as of 11-20, the list gets 2 exit candidates instead of 0:
  - CWT05-flush-m05-v3-long
  - GEN-261027-06 (Testing C, −111R)
- **Effect on retirements:** the 12 retirements still hold under the correct cost. I re-checked NS3 and exhaustion_short.
- **Fix:**
  1. Read every column in `live_trades` (`SELECT *`).
  2. Make the cost code raise an error on missing columns instead of skipping them.
  3. Add a test.
  4. Regenerate footrace.json, the nightly and brief Primary records, and the ST7-MOVE card, all on one cost basis.
- **Before the open?** Yes for the code fix and the corrected ST7 numbers. This is housekeeping, and doing it on the weekend is allowed. Any new exit move this produces (the 2 candidates above) is a setup move: it goes through the normal rules, and you decide on it outside market hours.

**C2. The final1121 study's live loader leaves out exit-side costs.**
- **Where:** `research/final1121/scripts/promo-pipe/load_live.py:13`. Trades before 11-12 are overstated by about 0.045R each.
- **Corrected figures:**
  - **P1:** +23.1R, best-day share **79%** (reported +26.3R, share 69%).
  - **P2:** +13.2R, share 100% (reported +16.0R).
  - **RW7 under Primary rules:** **+4.4R** (reported +18.1R).
  - **X1:** **−0.9R** (reported +2.3R).
  - The "costs average only 0.013R per trade" line should read about 0.042R.
- **Decision effect:** none flips. Every candidate gets weaker, so "do not promote" is firmer.
- **Fix:** read every column, re-run `live_stats.py` and `primbook.py`, and restate the FP-A, FP-C, Rank-1 and gap-to-bar text.
- **Before the open?** No, but before you answer FP-A through FP-F.

### Major

**M1. Remedy-Q copies were built although your condition was not met.**
- You said "if all is true, remedy-q yes".
- What the re-check found:
  - The 1pm theory failed the lab check for all 3 setups.
  - Parts (b) and (c) failed.
  - A 12:30 cut-off was substituted. It is labelled "confirmed (weak)", with t 1.94 against a bar of 2.89.
  - In the Testing accounts, where the copies actually run, the pooled lab result is worse than the parents: −14.6R against random removal.
- The 12:30 copies start 11-23 in Testing F, A and B. The inbox still shows the item as "re-asked".
- **Fix:** re-ask with the actual result, or switch the 3 copies off until you answer. Relabel the verdict "not confirmed — live test copy".
- **Before the open?** **Yes.** It is a setup change, so it has to be settled outside market hours.

**M2. The watchdog barely runs during market hours.**
- The "act" approval was based on the watchdog "already running every 10 minutes".
- In fact, GitHub ran it at most once a day from 11-05, and **zero times on 11-16, 11-17, 11-18 and 11-19**. The only run on 11-20 was at 16:01 ET.
- "Act" mode is live, but it protects almost nothing against a dead run, stale data or a failed flatten.
- **Fix:** start the watchdog from the trade job or session guard, the same way the hunch and trade jobs are started. Correct the ledger note.
- **Before the open?** **Yes**: at least tell the owner, and ideally add the dispatch, since it is not a setup change.

**M3. The NM-ETF size decision card shows stale, positive figures.**
- The card shows Primary as 15 trades, +0.075R, and the whole record as 33 trades, +0.21R.
- Actual Primary after Friday: **27 trades, −11.45R (−0.424 per trade)**.
- **Fix:** refresh NMETF-SIZE and OUT-NMETF, and label which figures are all accounts.
- **Before the open?** Before you answer NMETF-SIZE.

**M4. Several open decision cards are already done or overtaken.**
- **M2:** the setup already moved on 11-12.
- **SIP-DEF:** Testing D, E and F have traded since 11-12.
- **MF4-OK:** the setup was retired on 11-20.
- **EXIT-MF5:** it names CWT13-z05-long, which was retired while this card was still open.
- **Fix:** close M2, SIP-DEF and MF4-OK, and re-frame EXIT-MF5.
- **Before the open?** No, but it clears the 50-item card.

**M5. The retire rule as adopted (at least 20 sessions) was never tested on its own.**
- The evidence you approved (746R saved, 1 wrongful kill) is for at least 15 sessions.
- At 20 sessions: 25 retired, **428R saved, 2 wrongful kills**. The rule still separates good from bad setups.
- **Fix:** add these figures to the retire report and the ledger, counted as one more configuration tried.
- **Before the open?** No live change is needed.

**M6. The ledger check required by the research rules has not been run for any 11-23 change.**
- It crashes when there is no bar data (`mcf/research/ledger.py:75`).
- It has been open since 11-12 (LEDGER-CHK-1111).
- It cannot replay per-account changes or the burst brake.
- **Fix:** give it a clear error message, run it as a GitHub job that has bar data, and note in each ledger entry which checks the tool cannot do.
- **Before the open?** Desirable, but not blocking.

### Minor (all can wait)

Owner-facing wording:
1. **Week post:** "+73.4R on 530 trades / everything else −161R" stops at 11-19. Through 11-20 it is **+88.8R on 550 trades / −173R**.
2. **Inbox `:236`:** "33 trades, +0.21R before 11-19" is all accounts, not Primary. Primary before 11-19 was 12 trades, +2.01R.
3. **Consultant line:** NM-ETF was "green 5 of 7 days" before 11-19. It is 5 of 5.
4. **Briefs:** the "Alpaca $" figures are journal fills. Alpaca's own day P/L differs by $2–4 a day.
5. **Consultant:** asks you to close EARN-GO, which you already did on 11-19.
6. **Cards that should be closed or pointed elsewhere:**
   - LATCH-CLOSE and CONS-PMX overlap your GB-NOEXIT answer.
   - ETF-BURST has already been studied in final1121.

Report slips:
7. The brake fired on **17 days**, not 12 (12 better, 5 worse).
8. The null study says "21 of 37 do not beat". It should say 21 do not beat and 3 could not be tested.
9. NM-ETF Primary exits were **4 targets / 11 flattens**, not 5 / 10.
10. Remedy-Q:
    - It ran on partial 11-20 data but is labelled as the full day.
    - Its verdict and its CSV files come from two different lab runs.
    - It dates BRAKE-BURST 11-20; it takes effect 11-23.
    - The "13:15 worse than 13:00" claim is not true for Primary L3 on its own.
    - It does not say that its lab window overlaps the live days that suggested the theory.
    - Its paired t is biased upward when the setups are losing.
11. **ST7 review:** the "since TEAM-6" line mixes in 11-20 morning trades. The through-11-19 figures are L3 +32.9, RW3 −6.3, RW5 −7.1.
12. **latepb report:** quotes +0.21R on the old cost basis. On LR8 it is +0.179.

Code and process:
13. **BEG-GNG:** after a runner restart it loses its 12:00 exit, because that exit is not saved with the position. The risk is small.
14. **Tests:** two tests fail on weekends because they use today's date. Pin a weekday in `tests/test_hk_flat_1113.py`.
15. **Ledger:** there is no ledger line for OUT-NMETF (NM-ETF frozen, plus a size rule), OUT-NULL, OUT-RETIRE or WW-ST7.
16. **L3 Remedy-Q copy:** under Testing rules its lab result is worse than having no cut. Keep this in mind when it is reviewed.

## 4. Numbers that change in owner-facing reports or decisions

| Item | Shown | Correct |
|---|---|---|
| Gap-down shorts since 10-06 (week post) | +73.4R / 530 trades; rest −161R | **+88.8R / 550; rest −173R** |
| ST7 Primary record (brief / nightly) | 43 trades, −0.149, −6.41R | **−0.165, −7.08R**; distance to −10R: **2.9R** |
| RW3 / RW5 / L3 Primary per trade | +0.175 / +0.109 / +0.200 | **+0.151 / +0.078 / +0.191** |
| NM-ETF Primary (NMETF-SIZE card) | 15 trades, +0.075 | **27 trades, −11.45R, −0.424** |
| NM-ETF Primary before 11-19 (inbox `:236`) | "33 trades, +0.21R" | **12 trades, +2.01R** (33 is all accounts) |
| Friday exit list (footrace, as of 11-20) | 0 exit candidates | **2** (CWT05-flush-m05-v3-long, GEN-261027-06) |
| Retire rule evidence | 746R saved, 1 wrongful kill | As adopted: **428R saved, 2 wrongful kills** |
| final1121 P1 | +26.3R, best-day share 69% | **+23.1R, share 79%** |
| final1121 RW7 under Primary rules | +18.1R | **+4.4R** |
| final1121 X1 | +2.3R | **−0.9R** |
| Remedy-Q status | "confirmed (weak)" | **not confirmed**; Testing-account lab result −14.6R against random |
| Brake fired | 12 days | **17 days** |

## 5. Checked and found clean

- **Primary figures:**
  - Week: R, $, trades, win rates and green days.
  - Friday: shorts 20/20 for +15.3R; the NM-ETF burst of 12 lots, −12.57R; the market-direction gate's 13 trades, −12.35R.
  - Since 10-23: R, $ (with the 11-05/06 broker glitch adjusted) and green days.
  - The 3-day nightly line.
  - The one-big-day figures.
- **Monday's code and config:**
  - The burst brake is 30 entries per 10 minutes in all 10 accounts, and it never blocks exits.
  - The Remedy-Q window is wired as the ledger states.
  - BEG-ORB and BEG-GNG match their tested rules, with no look-ahead.
  - No setup is enabled in two accounts.
  - The setups moved to the Graveyard were copied faithfully.
  - assignments.json regenerates identically.
  - Setup changes were merged after the close.
- **Friday review:** the 12 exit moves and 12 retirements reproduce independently. Both retirements I spot-checked (NS3, exhaustion_short) hold on the correct cost basis.
- **Research rules:**
  - No reads of the locked 2024-11 to 2025-02 block, and no look-ahead.
  - The null study reproduces to 4 decimals.
  - Configuration counts are reported: null study, retire 50, brake 288, Remedy-Q 66, final1121 140.
  - One-big-day checks are present.
  - Lab costs are charged once.
  - PROTECTED.md and its tests are correct.
- **Tests:** 913 pass. The 2 failures happen only because today is a weekend.