Educational only — not financial advice

# Root cause of Primary's -14.4R on 2026-11-19: lead consultant findings

## Summary for the owner (5 lines)
1. **The setups caused this, not stacking and not execution.** Two rule-level defects turned the book into one big long-Nasdaq bet: ST7-FD fired 7 tech longs on one bar because of an RSI warm-up artifact (-7.53R), and L3 shorted inverse ETFs (SPXS/SQQQ), which made it a long-market trade, the opposite of what L3 is meant to be (-6.49R).
2. **Conditions only pulled the trigger.** A 1.6% index drop at 11:49-12:05 stopped all 14 lots within 27 minutes. Nothing known at entry (Compass, SPY trend, range) would have warned of it. Over the record a Compass gate removes trades that are no worse than the ones it keeps.
3. **Execution cost about -1.1R and the system rules saved about +43R.** Fills were on time. Stops were not too tight and nothing gapped. The ETB skips (+33R) and the -2R latch (+10R) cut the loss. One broker rounding bug cost about -0.9R on ETHA.
4. **Stacking is not the problem.** It scaled a wrong call. On the record, stacking is where the winners make their money: L3's days with 5+ lots made +92.8R, its other days -11.5R. Every stacking cap tested cuts L3/RW3/RW5 by 13-21R each. Your instinct holds: the cap of 30 bound once (L3, 11-12) and left an estimated +97R on the table.
5. **Best fixes (research and shadow only, no change today):** (a) short setups never short market-inverse products; (b) review ST7-FD as built. The FD copy dropped the 13:35-15:00 window that earned its promotion, and 64% of its live trades come from the artifact bar. (c) Keep the shadow test, and add the inverse-short guard to it.

## 1. Where the -14.4R came from (the parts add up)

| Rank | Part | R | What it was | Root-cause class |
|---|---|---|---|---|
| 1 | ST7-FD 10:44-10:46 burst (ASML, ETHA, FTEC, MUU, SMH, TER, TECL) | -7.53 | One correlated long-tech bet. All 7 fired because RSI(14) uses prior-session 5-min bars, so the overnight gap drops out of the 14-change window on the 10:45 bar. RSI then collapses at once in every gap-up name that has faded. | Setup rule (trigger artifact), with condition (index leg) |
| 2 | L3 shorts of SPXS/SQQQ, 6 lots (3+3), 11:16-11:46 | -6.49 | A short of a 3x inverse index ETF is a long-index bet. L3 has no product-type filter. On 11-19, all 42 symbols L3 qualified in Primary were inverse products (0 stocks). ETB blocked 40 of them; SPXS and SQQQ were easy to borrow, so they got through. | Setup universe leak (setup/system), with condition |
| 3 | ST7-FD IWN, 11:55 | -1.12 | An ordinary loss in the same down-leg. The latch line (-2R) was crossed only at 12:00. | Condition |
| 4 | RW3 | +0.71 | | |
| | Total | -14.43 | Matches the -14.4R realized | |

**Cross-cutting overlays (inside rows 1-3, not added on top):**
- **Execution: about -1.1R in total.** Entry slip was -0.86R and stop-exit slip -0.50R, partly offset by fills better than the signal. Orders went in about 1.25 min after the bar closed, with 2-28 bps spreads. With perfect fills the day would still be about -13.3R.
- **Broker stop rounding: about -0.9R, inside row 1 (ETHA).** alpaca_broker.py:91 sends `round(stop, 2)`, so 39.5366 became 39.54, and the low was exactly 39.540. ETHA then rallied. This is 1 of 89 live stops.
- **Same-symbol lots: about -4.4R of row 2** (3 lots against 1). Moot, because with the inverse guard none of the 6 lots exist.
- **Common driver:** 13 of 14 losing lots were effectively long Nasdaq/S&P beta. SPY went from 728.9 to 717.9 and QQQ from 660.1 to 647.4 between 11:51 and 12:05. 10 of 14 trades had been at least +0.8R in profit before the reversal. After the stops, price went a further 1.4-4.5R against: the stops were real and the trade ideas failed.

## 2. The owner's question, answered directly
- **Setup: yes, the main cause (about 14R of 14.4R sits in rows 1-2 as defects of the rules).** For L3, the defect is universe definition. For ST7-FD, it is the trigger artifact plus the way the FD copy is built (see section 4).
- **Conditions: the trigger, not a fixable cause.** The R of both setups correlates about 0.40 with the SPY move *after* entry (live and lab). No state known at entry separates winners from losers. Entries against a confirmed Compass are ST7's best lab bucket (+0.123R) and L3's best live bucket (+0.306R). After DOWN-confirmed, the Compass called SPY's next 60 minutes right only 48.9% of the time.
- **Rules: not a cause; they helped.** ETB skips saved about +33R today (40 L3 inverse/vol shorts). The latch saved about +10R (24 blocked L3 signals would have made -10.0R; data to 13:51, provisional). No R-based latch could have acted first: open MTM was +4.5R at 11:50 and the 6 L3 stops filled within 14 seconds. The 0.15R cost filter, sizing, setup_order and the -20R halt played no part.
- **Entry/exit: minor** (about -1.1R, plus the ETHA rounding bug). Wider stops were tested at k = 1.25/1.5/2.0 and are worse at every k (this agrees with stoplab B). Re-anchoring the target to the fill is +12R today but -1.7R on all other days, a one-big-day artifact, so it is rejected.
- **System: one structural gap.** Every rule (ETB, exposure, stacking) treats symbols as if all of them were plain longs. A short in SQQQ is counted as a short. ETB catches most inverse shorts only by accident.
- **Stacking: amplifier, not cause.** Capping bursts (1/sqrt(k)) lowers day-t for 102 of 115 setups and costs L3 Testing 1 -21.3R, L3 Primary -17.4R, RW3 -15.7R and RW5 -13.3R. Later L3 lots are not worse than first lots (live: 1st +0.205R, 2nd +0.220R, 3rd +0.166R). Same-stop stacks are L3's best class (+0.311R). The owner's premise does not fit ST7-FD, though, because it was never a 100% setup. ST7-FD in Primary: 42 trades, -6.6R, avg -0.158R, avg w/o best day -0.296R. 2-year lab: +0.045R, day-t 1.0. The 100% clusters (RW3 21/21 and RW5 24/24 on 10-22, L3 80 lots +33.6R on 10-20) are where stacking paid.

## 3. Do the same causes drive the losing days across the live record?
Run-1 (live paper) trades only, my own check on the journals (UTC times, so the 10:45 bucket is approximate):
- **L3-fromopen-FD, Primary (181 trades, +31.7R):** the inverse-short leak accounts for 2 of its 4 worst days: 11-02 SOXS -4.09R (all 4 trades inverse) and 11-19 -6.49R. Those two days are -10.6R of the about -26.9R lost on its 8 red days (39%). The other red days (10-21 -5.75R, 11-11 -3.5R, 11-18 -2.5R) are ordinary stock fades on days the market went the wrong way. Testing 1's worst day (10-15, -13.5R) had no inverse trades. Across all accounts, L3 inverse trades: 17, -9.0R, -0.53R/trade (w/o best day -0.67R). L3 stocks: 336 trades, +0.247R (w/o best day +0.196R, best day 39% of total). All short setups shorting inverse products, all accounts: about 127-200 trades depending on the definition, -55 to -65R, red on 16 of 22 days. So the same cause recurs: yes, for the inverse leak.
- **ST7-FD, Primary (42 trades, -6.6R):** today is -8.66R of it; the other 12 days net +2.1R. Its 10:45-bucket trades outside today net about +4.6R (11-04: 9 trades +3.1R; 10-30: 5 trades +1.25R). Its other red days are single -1.1R losers. Lab 10:45 bucket: +0.052R, t 0.77, worst day -26.1R (2025-04-08, 24 names). The burst is a fat-tailed one-direction bet that pays small most days and loses large on a reversal day. Today was that tail, not a new failure. Its per-trade edge is thin either way.
- **One-big-day check:** L3-fromopen Primary since 10-30: +0.245R/trade, but 11-12 is 80% of its R (`1 day` tag), +0.073R without it. L3 across all live: +0.202R, w/o best day +0.148R (best day 41%). ST7-FD Primary: -0.158R, w/o best day -0.296R.

**Rule changes inside the live window (research/ledger.jsonl):** stacking and refire rules 10-13/10-14 (lab refire 10-14). L3-fromopen promoted to Primary 10-20, demoted 10-22, re-promoted 10-30. Per-setup latch made latching 10-23. ST7-FD promoted to Primary 10-26. GX1 5-min clock fix 10-27 (as reported by the setup_logic investigator; not re-verified). Primary size changed twice on 10-28 (~$5k with slots 160→61 and per-setup cap 100→30; then ~$4k with slots 61→77). Primary -2R latch 10-29. L3-rsi5hi to Primary 10-30. ROLL1 low-rep homes 11-05. Stats above that span these dates mix rule regimes.

## 4. Remedies (targeted; none applied; no market-hours change)

### R1. Short setups do not trade market-inverse products (inverse/levered-inverse ETFs and ETNs, long-VIX)
Four investigators found this independently; their versions are A', G4, R-A and R1.
- **What changes:** before entry, a short skips a symbol that is on the frozen inverse list (or has 2-year SPY beta <= -1). Long setups are untouched. The same exposure sign should feed any cross-setup exposure check, so that a short in SQQQ counts as long the market.
- **Evidence:** live, all accounts, beta <= -1 version: 59 setup-accounts affected, 42 improve (+79.4R), 17 get worse (-14.6R), net +64.8R; +47.6R excluding 11-19. Largest worsenings: heat_fade_short-FD in the Graveyard -2.7R, NM-RWR3 in Live Lab -2.1R, MF2-FD -3.9R in the A' version. All 5 L3 variants improve (L3-fromopen Primary +10.6R, L3-lowdist T1 +4.1R, L3-WB4 T2 +4.0R, L3-rsi5hi Primary +3.1R). 2-year lab (A'): 60 setups affected, 31 better / 29 worse, net +529R; unseen half 35/24, later half 31/28. The lab is mixed by count because it cannot apply ETB. Counter-evidence: ETB-skipped what-ifs in the same class made +12.6R over 126 trades. On 11-19 it would have saved +6.49R.
- **Conflicts with standing rules:** it is a setup/filter change, so it goes through the backlog (RESEARCH_RULES 15-17) and can only take effect outside market hours, and for Primary only in the Friday epoch window. The -2R latch is untouched (owner 11-17). Playing time: it removes about 0.7% of trades. Before going live, check that no low-rep setup in Explore 1 / Live Lab loses so much activity that its rotation stalls.
- **Test before live:** (1) a lab re-run with an ETB proxy, both halves, reporting every affected setup (better/worse and by how much); (2) forward shadow from 11-20. This costs nothing: research/forward/compass_gate/forward.csv already carries inst_class and exposure, so add a blocked_inverse_short column. Pass bar: at least 10 sessions, net positive, at least 60% of affected setups not worse, and no setup worse by more than 3R. (3) Locked holdout scored once. (4) Ledger entry and `python -m mcf.research.ledger check`.

### R2. Review ST7-FD as built (the "way we have it" finding)
- **What changes (candidates to test, not decided):** (i) fix the indicator at its source by computing RSI on intraday changes only, dropping the prior-close-to-first-bar change, for every RSI setup; or (ii) return ST7 to its windowed source form. The promotion record came from the 13:35-15:00 rule (n 176, +0.133R, t 1.69). The FD copy removed that window, and now 58% of its lab fires and 64% of its live trades come from the 10:45 artifact bar.
- **What not to do:** do not just skip the 10:45 bar. That remedy (B) makes ST7 worse by -35.6R and ST7Q by -62.6R in the lab, because the bucket is positive on average and only fat-tailed. Weighting artifact-bar bursts at 1/sqrt(k) (C2) improves ST7's t from 1.01 to 1.37 and its worst day from -7.9 to -2.3 day-units. It is a weak candidate: across the 36 RSI setups it affects, 17 improve and 15 get worse.
- **Conflicts:** if the review ends in a demotion, it is a move, regenerating docs/live/assignments.json in the same commit, never a switch-off (trimmed and low-activity rules), and it happens in the Friday epoch window. The one-big-day figures above must be shown.
- **Test:** the intraday-only RSI needs a 1-minute frame rebuild after hours. Report all RSI setups (better/worse counts and R), both halves, and the locked holdout once.

### R3. Answer "capitalize on every opportunity" with data: a shadow, not a cap
- **What changes:** nothing live. Run the existing Compass-gate shadow, add the R1 column to it, and add a shadow of raising the per-setup cap of 30 for setups that hit it. Only L3 ever has: on 11-12 it skipped 648 signals, an estimated +97R net. That is a single day, the fill model is optimistic, and the L3LEASH lab shows both tails grow.
- **Prior for the Compass shadow:** on the record, the Compass gate removes trades that are no worse than the ones it keeps (it would cost L3 -57R live and ST7 -32R in VALID). Read its forward results against that prior.
- **Housekeeping (backlog, outside market hours, touches orders):** round broker stops away from entry, floor for long stops and ceil for short stops, instead of round(). Worth about +0.9R today; no other live stop affected.

Configs considered across the swarm: execution 7, setup_logic 6, conditions 5, stacking 8, system_rules 8 (34 in total), plus 1 for the frozen Compass-gate rule. No locked block (2024-11-01..2025-02-28) was read. Costs are in (LR8). Figures are rounded down where the investigators disagreed. No config, setup, exit or order was changed, and nothing was committed.

Supporting files from the investigators (in /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/rootcause_1119/): execution.md, setup_logic.md, conditions.md, stacking.md, system_rules.md. My own check on the losing days used the journal copies in /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/rootcause_1119/exec_data/ (journal.db, j_testing.db), with run_id=1 (live paper) only.

## Skeptic (adversarial review, 2026-11-19 ~14:00 ET; checked against the journals at origin/mcf-data, mcf-data-testing, mcf-data-testing2, mcf-data-livelab and research/ledger.jsonl)

Configurations tried: 4. (1) A re-sum of the R on Primary run 1 for 11-19. (2) The live record of inverse shorts, using a beta <= -1 list from cond_work/beta.csv. (3) A check of the ST7 and L3 copies in the other accounts today. (4) A latch counterfactual from the L3-WB4 copy. No lab runs, no reads of the locked block, no Alpaca calls.

### S1. Arithmetic: the day is -16.8R, not -14.4R. DOWNGRADED (table incomplete)
- Formula: R = pnl_adj / (|entry - stop| x shares), on run 1 of the Primary journal.
- The lead's rows match the journal:
  - ST7-FD: -8.66R (burst -7.53R, IWN -1.12R).
  - L3-fromopen: -6.49R.
  - RW3: +0.70R (EWT +0.77R, IBRX -1.14R, NUGT +1.08R).
- One row is missing: RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, -2.39R.
  - OGE entered 12:30 and stopped 13:03 (-1.19R).
  - ADC entered 12:45 and stopped 13:35 (-1.20R).
  - Their MFE was +0.05R and +0.06R. These were ordinary short losses into the bounce after the flush.
- Primary realized so far: -16.84R. The parts add up only for the morning. "About 14R of 14.4R" should read "about 14R of 16.8R".
- Execution check: across the 14 stopped lots, the loss beyond -1.00R per lot (costs plus slip) is -1.15R. The lead's -1.1R holds.
- The lead's "10 of 14 lots reached MFE >= +0.8R" holds. The four that did not: ETHA +0.43R, SPXS 11:35 +0.67R, SQQQ 11:45 +0.27R, IWN -0.12R.
- No ST7 or L3 lot reached its target. Targets were set from the signal price and sat 1.0-1.6R away from the fill.

### S2. Line 1, the L3 inverse-short leak as a setup/universe defect. UPHELD (the strongest finding)
- Signals journal: L3-fromopen evaluated 42 symbols today, all inverse or long-volatility products.
  - 40 were skipped as "not shortable/ETB".
  - SPXS and SQQQ went through.
  - The latch then blocked 24 more signals.
- This is built into the setup. On a morning when the index gaps up and then fades, the products that gap down and recover are the inverse ETFs. That is exactly what L3 looks for.
- The same leak hit the other L3 copies today:
  - L3-lowdist (Testing 1): 2 lots, -2.15R.
  - L3-rsi5hi (Testing 1): 3 lots, -2.21R net.
  - L3-rsi5hi-WB5 (Live Lab): -2.15R.
  - L3-fromopen-WB4 (Testing 2): 10 lots of SQQQ.
- My own count on the live record (run 1, all accounts I had, beta <= -1 list of 20 symbols):
  - 140 short trades of inverse products, -62.6R, -0.45R/trade, red on 17 of 24 days.
  - Without 11-19: -48.8R.
  - This sits inside the lead's range (127-200 trades, -55 to -65R).
- It is not a market-trend artifact. A short of an inverse ETF is a long-market position, and these trades still lost.
- Remaining caveats:
  - The 2-year lab is mixed by count (31 better / 29 worse), so its +529R net is not the evidence to lean on. The live split (42 setups better / 17 worse) is.
  - The ETB-blocked inverse what-ifs were positive (+12.6R over 126 trades). The losses sit in the liquid index inverse ETFs: SOXS, SQQQ and SPXS make up about -56R.
  - A narrower guard covering only index-inverse ETFs and long-volatility products should also be tested, as the more targeted form.

### S3. Line 1, the ST7-FD RSI warm-up artifact. UPHELD as mechanism; the claim that "the FD copy dropped the window that earned its promotion" is WRONG
- The mechanism holds. At the 10:40 bar close (signal at 10:45), the 14-change RSI window first drops the prior-close-to-09:30 change. 58% of lab fires and 64% of live trades sit on that bar.
- The ledger entry 2026-10-25-promote-st7-fd shows something different from the lead's claim. The owner promoted the all-day FD version on its own Testing 1 record:
  - 16 trades, +0.21R, t 0.75.
  - Avg w/o best day -0.09R; best day 10-12 was 119% of the total.
  - 2-year full-day result: +0.033R/trade.
  - The ledger itself warned: "Small sample: its record without its best day is negative; watch from day one."
- Removing the window was owner policy from 2026-10-09 ("full-day versions first"), long before the promotion. So the 13:35-15:00 record (n 176, +0.133R) never earned this promotion.
- Correct framing: ST7-FD was promoted on a thin record carried by one day, and its live record confirms the thin edge (42 trades, -0.158R, -0.296R w/o best day).
- Today's condition-filtered copy did not help. ST7-FD-WB1 in Live Lab skips while SPY is up more than +0.10% since 09:50. It still took the same burst (FTEC, TECL, SMH, MUU, ETHA, IWN), and all 6 lots stopped. So fix the trigger (R2-i) or restore the window (R2-ii); do not add a condition filter.

### S4. Line 2, conditions as the trigger only. UPHELD, with a hindsight warning
- I found no state known at entry that would have warned of the drop. The WB1 SPY filter in S3 is one more live failure of a condition filter.
- The Compass 48.9% figure comes from a short live window (11-06 onward). Read it as "no evidence the Compass helps", not as proof that it cannot.
- None of the proposed remedies uses the 1.6% drop itself, so there is no look-ahead in them.

### S5. Line 3, "the system rules saved about +43R". DOWNGRADED
- The ETB +33R is not a rule saving.
  - The 40 skipped symbols could not be shorted at all, so there was no decision to save.
  - It is the mirror image of the inverse leak: shorting inverse products on a down day loses.
  - On the record, this blocked class was positive (+12.6R over 126 what-ifs).
- The latch +10R is overstated.
  - The closest live evidence is L3-fromopen-WB4 in Testing 2, which has no Primary latch and kept shorting SQQQ after 11:52.
  - Its 7 lots from 11:55 to 12:55 made -0.26R in total: two targets (+2.35R and +1.63R) as the market bounced, and five stops.
  - The lead's 24 blocked signals at -10.0R used data only to 13:51.
  - My read: the latch saved somewhere between 0 and +10R today, probably a small amount. The latch decision itself (owner 11-17) is not in question.
- Rule change in effect today: U9-ETB took effect on 2026-11-19. It uses one bulk shortable/ETB list per session, refreshed every 60 minutes, and writes one skip row per setup/symbol/day. The "40 of 42 blocked" count comes from this new mechanism, so earlier days are not counted the same way.
- ETHA rounding bug: UPHELD as a real bug.
  - The code sends StopLossRequest(stop_price=round(sig.stop, 2)). For a long, 39.5366 became 39.54, which moved the stop up.
  - Long stops should round down and short stops round up.
  - The -0.9R is one trade on one day, and I did not re-check ETHA's path after the stop. Report it as a bug worth about one trade's loss today.

### S6. Line 4, "stacking is not the problem; your instinct holds; +97R left on the table". PARTLY UPHELD (not the cause), PARTLY DOWNGRADED (not proven to be the edge)
- Upheld:
  - No stacking cap tested fixes today without cutting the winners by more. The R-B burst sizing fails setup by setup. The R-C exposure caps are not targeted.
  - Later L3 lots are no worse than first lots.
  - Same-symbol lots added about -4.4R today, but with the inverse guard those lots would not exist.
- Downgraded, for three reasons:
  1. Selection bias in "days with 5+ lots made +92.8R, other days -11.5R". Since 10-29 the -2R latch stops a setup after about two losers, so a losing day cannot reach 5 lots. Days with 5+ lots are partly selected by how they went early. This number cannot be used as evidence that stacking earns money.
  2. The stacking investigator's own one-big-day table shows each winner's record rests on one day:
     - L3 Primary: +0.005R/trade without its best day (11-12 = 98% of total R).
     - RW3-FD: -0.002R (10-22 = 101%).
     - RW5-FD: -0.023R (10-22 = 121%).
     - Clusters of 5+ made +151.2R when SPY moved with the trade and -154.4R when it moved against. So stacked clusters are mostly a bet on market direction.
  3. The "+97R on the table" (the day the cap of 30 bound, 11-12) is one day, 100% share, with an optimistic fill model. The L3LEASH 2-year lab shows L3's mass-signal days on SPY-up closes cost -242R (train) and -177R (valid). "Your instinct holds" should read "the shadow test of a higher cap is the right instrument; one day is not proof".
- The owner's premise: no Primary setup is 100% on its record. The 100% clusters (RW3 21/21 and RW5 24/24 on 10-22, L3 on 10-20) are single days, and the setups did take every opportunity on those days. Today the problem was two setups whose signals were the wrong trade (inverse shorts) or a thin-edge artifact (ST7), not the fact that stacking is allowed.

### S7. Section 3 rule-change context is incomplete. DOWNGRADED
These changes took effect inside the live window and are missing from the lead's list (research/ledger.jsonl):
- 11-17: shadow mode in the live runner.
- 11-17: TSZ1 testing sizing.
- 11-17: the 15 Workbench copies, including ST7-WB1, L3-fromopen-WB4 and L3-rsi5hi-WB5, all used above.
- 11-17: SPYEXIT engine (default off).
- 11-18: GY-BENCH.
- 11-19 (today):
  - U9-ETB borrow list.
  - C3-EPOCH/BASE1: Primary changes only in the Friday window; BASE1 runs as a shadow book.
  - C3-EXIT100: 20 setups moved to the Graveyard.
  - DQ-P3: one LR8 cost basis for every record spanning 11-12, which changes the reported R of those records.
  - UNIT1: account R (display only).
- Dates check: ST7-FD was approved 10-25 and took effect 10-26, so the lead's date is correct. stacking.md's 10-27 is wrong.

### S8. Remedies. R1 UPHELD for the backlog and shadow; R2 UPHELD with the corrected reason; no look-ahead found
- R1 (no shorts of inverse products) uses only a frozen symbol list or a 2-year beta, both known at entry, so there is no look-ahead.
  - It makes 17 setup-accounts worse, by -14.6R in total.
  - MF2-FD is worse by -3.9R in the A' version. That would fail the proposed pass bar (no setup worse by more than 3R), so check the beta version before the shadow test.
- R2-i (RSI on intraday changes only) touches every RSI setup. The better/worse report for each setup must come before any decision, and the lead's text for that test was cut off.
- R2's "do not just skip the 10:45 bar" stands, because the lab bucket is positive on average.

Key evidence paths:
- Primary journal: git show origin/mcf-data:journal.db, run_id 1 = live, run_id 3 = shadow/BASE1.
- Ledger entries: research/ledger.jsonl ids 2026-10-25-promote-st7-fd, 2026-11-19-u9-etb-borrow-list, 2026-11-16-wb-st7-wb1.
- ST7 FD module: /home/user/MCF/research/bdi/fullday/ST7-rsi50dn-long-pm-t1s1-FD.py (the header records the window removal).
- Broker code: /home/user/MCF/mcf/execution/alpaca_broker.py, line 91.
- Stacking notes: /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/rootcause_1119/stacking.md (one-big-day table and the L3LEASH caveat).
