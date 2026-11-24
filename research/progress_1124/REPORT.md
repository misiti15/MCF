Educational only — not financial advice

# progress_1124: are we better off than 4 weeks ago (week of 10-26)?

Research only. No trading or config change. Paper accounts. R is after costs on one basis (LR8, `live_trades()` / `cost_r_lr8`). $ is Alpaca day P/L. Weeks run Mon-Fri: the requested "10-27..10-31" week is the 10-26 trading week, and the first green week is 11-16..11-20. Chart: `weekly.png`.

## Failures first

1. **Primary still loses.** It is −99.0R over the 27 sessions since 10-23 and was green in only 1 of 5 full weeks. The median day is still negative (−1.95R over 10 sessions), and 11-24 was −11.7R.
2. **The one green week is thin.** The 11-16 week made +4.1R, but without its best day (11-16, +25.3R) it is −21.2R. 11-24 erased it.
3. **The current 4-setup lineup has a weak long history.** In hardstop_1123, the bench book for these 4 setups is −1,701R over 873 sessions (−0.086R per lot). The recent live record covers 3-4 weeks.
4. **Every testing-account week lost** on all-accounts R per trade (−0.03 to −0.19). No trend.
5. **R and $ disagree.** The 11-09 week was −44.7R but +$1,769. Two things cause the gap:
   - Positions were resized on 10-28, to about $4k from about $1.9k.
   - Big winners were large in dollars while many small losers were small in dollars.

   Do not read $ alone.

## Week by week, Primary (LR8 R after costs)

| Week | Days | Trades | R | Alpaca $ | Green days | Worst day | Days ≤ −10R | Med 10-day R* | R w/o best day | R/trade | Win % vs break-even % | Cost/trade (R) | Skipped signals (top reasons) | All-acct reps / R per trade | Setups clearly + ** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10-23 (Fri) | 1 | 32 | −3.3 | −82 | 0/1 | −3.3 | 0 | −6.06 | — | −0.10 | 53 vs 62 | 0.053 | 16 (ETB, spread, twin) | 635 / −0.033 | 0 |
| **10-26** | 5 | 125 | −10.1 | −85 | 2/5 | −11.8 | 1 | −3.69 | −15.1 | −0.08 | 57 vs 62 | 0.061 | 159 (ETB 87, spread) | 4,081 / −0.186 | 0 |
| 11-02 | 5 | 222 | −33.9 | −13,685 (−2,039 ex-MTUM) | 2/5 | −26.1 | 2 | −3.52 | −42.6 | −0.15 | 47 vs 55 | 0.063 | 1,425 (ETB 1,029, −2R latch 130, halt 92) | 5,161 / −0.176 | 3 |
| 11-09 | 5 | 266 | −44.7 | +1,769 | 1/5 | −34.8 | 3 | −9.48 | −84.6 | −0.17 | 46 vs 57 | 0.050 | 1,935 (ETB 1,069, per-setup cap 648, latch 63) | 6,248 / −0.089 | 5 |
| 11-16 | 5 | 193 | **+4.1** | **+753** | 2/5 | −16.2 | 1 | −3.99 | −21.2 | **+0.02** | **58.5 vs 57.1** | **0.040** | 567 (ETB 330, latch 62, lot cap 33) | 6,719 / −0.157 | 7 |
| 11-23 (2 d) | 2 | 49 | −11.2 | −416 | 1/2 | −11.7 | 1 | **−1.95** | −11.7 | −0.23 | 43 vs 59 | 0.047 | 163 (latch 86, ETB 57) | 2,505 / −0.045 | 6 |

\* Median day R over the trailing 10 Primary sessions, at the week's last day.

\*\* Setups with 17+ sessions and 40+ live trades, all accounts, with avg ≥ +0.05R and total ≥ +10R. Now 6 setups: L3-fromopen, L3-lowdist, L3-rsi5hi, RW3, RW5, RW6.

**Skip counts after 11-19 are not comparable.** U9-ETB writes 1 ETB row per setup/symbol, which shrinks the ETB counts.

**Rolling 10-session Primary totals:**

| | Best point | 11-24 |
|---|---|---|
| R | +37.6R on 11-04 (helped by the +61R day on 10-22) | +3.1R, first positive since 11-05 |
| Journal $ | +$2,911 on 11-23, best since the start | +$2,420 |

The 10-19 week (+24.8R) is still the best R week, but one day carried it: 10-22, +61.1R.

## Operations, per week

| Week | Problems | Automation added |
|---|---|---|
| 10-23 | Primary job crash at 10:47 (a stock listed on the new Texas exchange; PR #117) | — |
| 10-26 | 10-26 started 10:38 (scheduler outage); Gen crash (numba) | session guard (10-27); a bad setup module is skipped instead of crashing |
| 11-02 | 11-05 MTUM: Alpaca booked a bogus split, −$11.5k in a broker-side phantom position; T1 phantom SOXX short; Gen crash on a dropped connection; 11-06 Primary −20R halt at 10:55 | read-only broker retries |
| 11-09 | 11-11 usage limit, 2 checks missed; T1 SOXX phantom closed | LR1-LR8 on 11-12: kill switch, broker-vs-journal lot check every poll, flatten retries, after-cost halt incl. open marks, 15:55 flatten |
| 11-16 | watchdog cron fired 0 times 11-16..11-19; compass push crash; adopted lots in GY/Gen (KILL-FLAT) | shadow mode; U9-ETB/U9-TGT guards; stop rounding fix |
| 11-23 | none. All glitch checks OK on 11-23/24: no mismatch, no flatten fail, no halt | watchdog dispatched by trade jobs (45 runs 11-23, all success); watchdog 'act' in all accounts; burst brake everywhere (293 runaway entries skipped 11-23); no-human-loss rule |

There have been no manual position interventions since the MTUM/SOXX cleanup.

## Rule changes in the window (ledger effective dates)

**Primary lineup:**
- 10-26: MF1 out, ST7 in, CWT13-z05-long in (out again 10-27).
- 10-28: MF2-open and NS4 rotated out.
- 10-30: L3-rsi5hi and L3-fromopen in.
- 11-11: TEAM-6 frozen at 6 setups: RW3, RW5, L3-fromopen, ST7, NS5, NM-ETF. MF2-FD, MF4-FD, MF4, NS1 and L3-rsi5hi went out.
- 11-19: NS5 out, leaving 5 setups.
- 11-23: ST7 out, leaving 4 setups: L3-fromopen, RW3, RW5, NM-ETF.

Primary ran 14-15 setups before 10-26 and 9-11 from 10-26 to 11-10.

**Sizing and risk:**
- 10-23: per-setup daily stop latches.
- 10-28: Primary positions go to about $4k (77 slots).
- 10-29: −2R per-setup latch in Primary.
- 11-12: LR3 halt and latch count costs; LR1 flatten; LR7 flatten retries; LR5 lot check.
- 11-17: TSZ1 half-size lots in testing.
- 11-23: burst brake.

**Filters and timing:**
- 10-30: CF cost filter in T1/T2.
- 11-04 to 11-12: UNI1 top-500 pool in Testing 2.
- 11-12: LR8 cost model; account halts in testing go to 300R.
- 11-19: U9-ETB and U9-TGT guards.
- 11-20: stop-rounding fix.

**Pipeline:**
- 11-05: ROLL1 low-rep homes.
- 11-12: On Deck and Testing D/E/F built.
- 11-17: promotion hold (no On Deck → Primary).
- 11-20 and 11-23: FOOTRACE-EXIT moved 12 setups to the Graveyard; RETIRE-R3 retired 12.

Each week's results are mixed with these changes. The 11-16 week is the first under TEAM-6 with 5-6 setups. The 11-23 week is the first under the burst brake and with 4 setups.

## Verdicts vs the 10-26 week

| Area | Verdict | Why |
|---|---|---|
| Profitability | **Same to slightly better, not proven** | **Per week:** R/trade was −0.08 in the 10-26 week and +0.02 in the 11-16 week, but the 11-23 week (2 days) is −0.23. **Trend:** the median 10-day R is the best yet (−1.95 vs −3.69). **Totals:** the 10-session $ total is the best yet (+$2.4-2.9k). **Two dips:** the 11-02 and 11-09 weeks were much worse (−79R together). **Still losing:** 1 green week in 5 and a negative median day. |
| Efficiency | **Better** | **Cost:** cost per trade fell from 0.061R to 0.040-0.047R. **Win rate:** reached break-even in the 11-16 week only. **Setups:** clearly positive setups went from 0 to 6. **Lineup:** Primary is now its most-proven 4 setups. **Reps:** all-accounts reps are up (about 4.1k to 6.7k a week). **Caveat:** all-accounts R/trade is still negative, and the pipeline is on hold, so On Deck feeds nothing for now. |
| Operations | **Better, clearly** | **10-26 to 11-11:** a missed start, crashes, the MTUM/SOXX phantom positions, a halt and missed checks. **Since 11-12:** lot checks, flatten retries, a kill switch and after-cost halts. **Since 11-23:** watchdog in all accounts and the burst brake. **Last two sessions:** clean. |

**Is this the best point so far?**
- **Operations:** yes.
- **Efficiency and setup quality:** yes.
- **Profitability:** only on smoothed measures — the median day and the 10-session $ total.
- **Best R week:** still 10-19, carried by one +61R day.
- **Sample size:** the current 4-setup lineup has 2 live sessions, and the green week is 1 week whose total depends on one +25R day.
- **Long history:** these 4 setups lose in hardstop_1123's long replay (−0.086R/lot).

Better plumbing and better setup selection are real. Better profit is not proven yet.
