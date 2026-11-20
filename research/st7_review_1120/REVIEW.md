Educational only — not financial advice

# ST7-rsi50dn-long-pm-t1s1-FD (RSI Collapse Dip Buy, all day): review for the Friday 11-20 session

**Summary in 5 lines**
1. **Primary since 10-26:** 42 trades over 13 traded days. Total −7.30R, avg −0.174R, win rate 43%. Avg without the best day is −0.307R, without the top 2 days −0.393R. Day-clustered t is −0.74 and 38% of days were green. The shrunk estimate is −0.116 (the bar is > 0). In dollars it is −$558 after costs, about −2.6 account R.
2. **11-19 explains almost all of it:** −8.66R on 8 lots. Without 11-19, Primary is 34 trades, +1.35R, +0.040R per trade, −0.059R without the best day, t 0.30. The edge is flat, not proven.
3. **Every independent check fails:**
   - It does not beat random entries (p 0.10; Primary-only p 0.33).
   - The 2-year lab shows only +0.045R per trade (t 1.0) and a worst day of −26R.
   - All three ST7 copies lost on the same 11-19 burst: Primary −8.66R, WB1 −6.54R, ST7Q −7.66R, so about −22.9R in one day.
   - The testing record it was promoted on was carried by one day (best day 147% of total R).
4. **Where it loses:** the lots that fire together on the 10:45 bar, in index-like ETFs, on a market reversal. The −2R latch cannot stop this because all the lots open in the same 2 minutes. Since TEAM-6 (11-11) it is the weakest Primary member: −9.45R, −0.45R per trade.
5. **Recommendation:** move it from Primary to On Deck tonight, unchanged, as the Friday epoch change (Epoch 2). This is your decision under WW-ST7. It is stricter than the automatic rules: the −10R demotion line is not crossed yet (2.7R away) and the probation rule would keep it in. No Workbench fix now. Bar to return: at least +15R total on its non-overlap record plus the C3-BAR2 / PRIME-RULES entry tests (section 5).

**Cost basis:** all R is after costs on one LR8 basis (`with_cost_r` → `cost_r_lr8`). The `live_trades.pkl` figures I was given (−6.6R / −0.158 Primary; −11.7R / −0.178 all accounts) keep the flat pre-11-12 cost basis. On LR8 they are −7.30R / −0.174 and −12.9R / −0.196, about −0.03R per pre-11-12 trade. The null study notes the same gap.

**Data:** journals at origin/mcf-data, mcf-data-testing, mcf-data-livelab and mcf-data-explore1 (snapshot 11-20 12:47 ET), live paper run only. ST7 has no trades on 11-20 so far. No lab runs, no MarcoFlow calls, nothing from the locked block, nothing changed.

**What was counted:** about 14 descriptive cuts (account, week, rule period, time-of-day bar, burst days, Compass w60, gate1, SPY since 09:50, SPY after entry, QQQ vs open, ETF vs stock, stop width, giveback). These are after-the-fact cuts, not scored rules.

## 1. Live record

### By account
| Account | n | days | Total R | Avg | Win% | Avg win / loss | w/o best day | w/o top-2 | Best day | Worst day | day t | target / stop / flat at 15:55 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Primary (10-28..11-19) | 42 | 13 | −7.30 | −0.174 | 43% | +0.82 / −0.92 | −0.307 | −0.393 | +2.82 (11-04) | −8.66 (11-19) | −0.74 | 15 / 18 / 9 |
| On Deck = Testing 1 (10-12..10-21, before promotion) | 16 | 6 | +2.68 | +0.168 | 56% | +0.79 / −0.64 | −0.106 | −0.195 | +3.95 (10-12, 147% of total) | −2.80 (10-21) | 0.51 | 3 / 3 / 10 |
| ST7-FD, all accounts | 58 | 19 | −4.62 | −0.080 | 47% | | −0.159 | −0.253 | | −8.66 | −0.42 | 18 / 21 / 19 |
| Family incl. WB1 (66 trades) | 66 | 19 | −12.91 | −0.196 | 41% | | −0.272 | −0.371 | | −15.20 | −0.76 | |
| Primary without 11-19 | 34 | 12 | +1.35 | +0.040 | 53% | | −0.059 | −0.153 | +2.82 (208% of total) | −1.28 | 0.30 | |
| ST7-FD without 11-19 | 50 | 18 | +4.03 | +0.081 | 54% | | +0.002 | −0.074 | 3.95 (98%) | −2.80 | 0.60 | |

- The −2R per-setup latch fired on 1 of 13 days (11-19, where it blocked 2 signals).
- Median hold: 60 minutes to a target, 74 to a stop, 150 to the 15:55 flatten.

### By week (week ending Friday)
| Week | Account | n | Total R | Avg | w/o best day | Exits (target / stop / flat) |
|---|---|---|---|---|---|---|
| 10-16 | Testing 1 | 7 | +4.30 | +0.614 | +0.116 | 1 / 1 / 5 |
| 10-23 | Testing 1 | 9 | −1.62 | −0.180 | −0.311 | 2 / 2 / 5 |
| 10-30 | Primary | 9 | −1.62 | −0.180 | −0.538 | 4 / 5 / 0 |
| 11-06 | Primary | 12 | +3.76 | +0.313 | +0.315 | 9 / 3 / 0 |
| 11-13 | Primary | 6 | +0.44 | +0.073 | −0.109 | 2 / 1 / 3 |
| 11-20 | Primary | 15 | −9.88 | −0.659 | −1.033 | 0 / 9 / 6 |

### Primary by day
| Day | 10-28 | 10-29 | 10-30 | 11-02 | 11-04 | 11-05 | 11-11 | 11-12 | 11-13 | 11-16 | 11-17 | 11-18 | 11-19 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R | −0.34 | −1.28 | −0.01 | −1.11 | +2.82 | +2.06 | +0.98 | −1.07 | +0.53 | +0.45 | −1.12 | −0.56 | −8.66 |

### Rule changes touching it (research/ledger.jsonl, by effective date)
- **10-12:** the FD (full-day) version is born in Testing 1 (owner rule "full-day versions first"; the 13:35-15:00 window is removed).
- **10-13 / 10-14:** per-lot stacking (up to 3 lots) and same-setup re-entry, all accounts.
- **10-21:** promotion is a move; `twin_group` option.
- **10-23:** ST7Q added to Testing 1 ahead of ST7-FD in a twin group (ST7-T1); the per-setup daily latch now latches.
- **10-26:** promoted Testing 1 → Primary.
- **10-27:** GX1 5-minute clock gate for lab setups, all accounts.
- **10-28:** Primary position size ~$5k then ~$4k, per-setup cap 30.
- **10-29:** Primary −2R per-setup latch.
- **10-30:** L3-rsi5hi and L3-fromopen join Primary (setup order).
- **11-11:** TEAM-6 lineup.
- **11-12:** LR1 flatten time, LR3 latch counts after-cost R, LR8 cost model.
- **11-17:** WB1 copy starts in Live Lab; shadow mode; promotion hold.
- **11-19:** NS5 leaves Primary (Epoch 1, BASE1); C3-BAR2 (demotion at −10R); U9-TGT quote check; DQ-P4 fill marks.
- **11-20:** long stops now round down; ST7-A "keep the RSI code" and ST7-B "no window copy" (no setup change); FOOTRACE-EXIT (arena only); consistency over churn; Primary is the scoreboard.
- **Testing copies only:** 10-30 cost filter (Testing 1/2), 11-05 ROLL1 (ST7Q → Explore 1), 11-17 TSZ1 half-size lots.

### Primary split by those changes
| Period | n | Total R | Avg | w/o best day |
|---|---|---|---|---|
| 10-28 (before the latch) | 2 | −0.34 | | |
| 10-29..11-10 (latch on, before TEAM-6) | 19 | +2.48 | +0.130 | −0.034 |
| 11-11 (TEAM-6, before LR8) | 1 | +0.98 | | |
| 11-12..11-18 (LR8 / LR3 / LR1) | 12 | −1.77 | −0.148 | −0.287 |
| 11-19 (NS5 out, U9-TGT) | 8 | −8.66 | | |
| Before 11-12 | 22 | +3.12 | +0.142 | +0.024 |
| 11-12 onward | 20 | −10.43 | −0.521 | |
| 11-12 onward without 11-19 | 12 | −1.77 | −0.148 | |
| Before 11-11 | 21 | +2.14 | | |
| 11-11 onward | 21 | −9.45 | | |

- From 11-12 the exit mix changed: 9 of 12 trades flattened at 15:55 (avg −0.04R), against 0 of 22 before. This is not tied to any rule.
- None of these changes alters the ST7 signal itself.

## 2. Source evidence
- **Promotion (ledger 2026-10-25-promote-st7-fd, owner's direct instruction, effective 10-26):**
  - Testing 1 record at the time: 16 trades, +0.21R, t 0.75. Without the best day −0.09R; the best day (10-12) was 119% of total R.
  - 2-year time-of-day study: +0.033R per trade.
  - The ledger itself warned: "Small sample… watch from day one."
  - It would fail today's C3-BAR2 and PRIME-RULES entry tests (avg w/o best day > 0, best day ≤ 40%, at least 20 sessions).
- **Source rule:** a 13:35-15:00 windowed rule (2-year: n 166, +0.162R, t 2.02), picked from a 120,500-configuration search where the required t was 4.84. The FD copy dropped that window under the 10-09 owner policy, and it was the FD record that got promoted.
- **2-year lab (research/crunch/wave2/st7_fix):**
  - As live (FD): n 1,114, +0.045R, t 1.01, worst day −26.1R. 651 of the fires are on the 10:45 bar.
  - Away from that bar, 10:50-13:30 is −0.033R and 13:35-15:00 is +0.133R (t 1.68, chosen in-sample).
  - Round-5 holdout (2023-24) for FD: −0.016R.
- **Workbench replay / 2-year** (research/workbench/ST7-…/RESULTS.md): parent +0.043 / +0.013R; parent without its best day −0.051 / +0.003.
- **WB1 child** (skip while SPY is up more than +0.10% since 09:50; Live Lab from 11-17):
  - On the bench it beat the parent: replay +0.128R, 2-year +0.077R.
  - Live: 8 trades, −8.28R, 0 winners. It took the same 11-19 burst: 6 lots, −6.54R. Without 11-19: 2 trades, −1.74R.
  - The condition gate did not filter the reversal day.
- **ST7Q** (Nasdaq below VWAP only):
  - Testing 1: 6 trades, +0.68R.
  - Explore 1: 17 trades, −8.83R (−0.52R per trade); without 11-19, −1.17R on 10.
- **Shadow books on 11-17..11-19** agree with live: Primary shadow 10 trades −9.77R; WB1 shadow −7.63R; ST7Q shadow −8.68R.
- **Signals skipped for spread** (28 in Primary): what-if +5.9R, uncorrected. Their spreads were 25-44% of the stop distance, so after their own spread they are not a real missed edge.

## 3. Where it loses
- **Time of day (Primary):**
  - 10:45 artifact bar: 28 trades −3.46R. Without 11-19 it is the only positive part: 21 trades, +4.08R, +0.194R, +0.105 w/o best day, t 1.05.
  - 10:50-13:30: 9 trades −1.47R.
  - The 13:35-15:00 source window: 5 trades −2.38R (11 trades −4.63R across the ST7-FD accounts).
  - This matches the lab: skipping 10:45 or starting at 10:50 failed both tests.
- **Bursts (3 or more lots on the 10:45 bar in one day):**
  - Primary has 3 burst days: 10-30 (5 lots), 11-04 (9), 11-19 (7). Together 23 trades, −5.85R, worst −8.66R.
  - Non-burst trades: 19 trades, −1.46R (−0.077R). Both parts are negative.
  - Mechanism (rootcause_1119): RSI(14) on 5-minute bars drops the overnight change on the 10:45 bar, so every faded gap-up collapses on that bar at once. The owner chose to keep the RSI code (ST7-A).
  - The latch counts realized R, so it is blind to lots opened on one bar. The only limit is the 30-lot cap; the lab's worst burst day was 24 names, −26R.
- **Market direction / Compass:**
  - Entries under a DOWN-confirmed w60: 15 trades −6.94R. Without 11-19: +1.72R on 7, so the Compass does not separate cleanly.
  - QQQ below its open at entry: −10.48R (26 trades) against +3.18R (16) above. Without 11-19 it is −1.82R against +3.18R, the opposite of ST7Q's rule, which lost.
  - SPY up more than 0.10% since 09:50 (the WB1 gate): only 3 Primary trades, −1.37R.
  - The only strong split is hindsight: with SPY rising after entry, +3.41R (15 trades); with SPY falling, −10.71R (27). R correlates 0.40 with SPY's move after entry. It is a market-beta long with nothing at entry that predicts the market.
- **Symbols:**
  - ETFs/ETPs: 7 trades, −7.72R, 0 winners. Six of them are the 11-19 burst (TECL 3x, MUU 2x, SMH, FTEC, ETHA, IWN); the seventh is XHB on 10-28.
  - Stocks: 35 trades, +0.41R (+0.012R).
  - No repeat losers (GPC twice, +0.41R).
  - Stops wider than 1.5% of price: 8 trades, −4.05R (mostly the 11-19 levered ETFs).
- **Stops vs targets:**
  - Targets average +0.82R, stops −1.14R.
  - 7 stopped trades had first been +0.8R or more in profit (−7.73R); 6 of them on 11-19.
  - On 11-19 the fills were above the signal close, which put targets 1.0-1.5R away (median 1.14R against 0.96R on other days), so none filled before the 11:49 index drop.
  - Losers' median best gain before the stop: +0.37R. Winners' median worst dip: −0.48R.

## 4. Against the rest of Primary (since admission, through 11-19, LR8)
| Setup | n | Total R | Avg | w/o best day | Best-day share | day t | shrunk | Without 11-19 | Random-entry null p (pooled / Primary only) |
|---|---|---|---|---|---|---|---|---|---|
| L3-gap-slope-fromopen-FD (since 10-30) | 158 | +37.9 | +0.240 | +0.066 | 82% `1 day` | 1.03 | +0.074 | +0.292 | 0.002 / 0.001 |
| RW3-FD (since 10-15) | 169 | +21.1 | +0.125 | −0.016 | 111% | 0.62 | +0.019 | +0.118 | 0.015 / 0.002 |
| RW5-FD (since 10-15) | 180 | +10.7 | +0.059 | −0.053 | 176% | 0.34 | −0.013 | +0.074 | 0.001 / 0.001 |
| NM-ETF-late-dip (since 11-11) | 15 | +1.1 | +0.075 | +0.034 | 66% | 0.79 | −0.084 | +0.168 | <0.001 / 0.007 |
| **ST7-FD (since 10-26)** | 42 | **−7.3** | **−0.174** | **−0.307** | n/a (net loss) | **−0.74** | **−0.116** | +0.040 | **0.10 / 0.33** |

- Since TEAM-6 (11-11): L3 +34.5R, NM-ETF +1.1R, RW3 −4.5R, RW5 −6.4R, ST7 −9.4R (−0.45R per trade, the worst).
- RW5 has also lost recently: −10.4R since 10-28. It keeps a positive since-admission record and beats random entries; ST7 has neither.
- ST7 is Primary's only long besides NM-ETF. On 11-19 it carried the same long-market risk that L3's inverse-ETF shorts did.

## 5. Recommendation for the Friday review
**Move ST7-FD from Primary to On Deck (key `testing`), unchanged, in tonight's after-close window as Epoch 2.**
- It is a move: switched off in Primary in the same change; `python -m mcf.report.assignments` regenerated in the same commit; ledger entry; `python -m mcf.research.ledger check`.
- It goes to On Deck, never to the Graveyard (PRIME-RULES).
- BASE1 contains ST7, so the BASE1 comparison will measure the effect of removing it directly.
- No twin clash: ST7Q is in Testing B (explore1) and WB1 in Testing C (livelab).

**Why move now:**
- Every source fails: live Primary, the one-day check at promotion, the random-entry null, the thin 2-year lab, and both tuned copies live.
- Without 11-19 its mean is about zero. With 11-19 it carries a burst tail that a near-zero mean does not pay for, and the latch cannot contain it.
- Ten more sessions would add about 20 trades, too few to tell +0.04R from zero.
- It is at its ~20th enabled Primary session, the PRIME-RULES real-decision point, and its whole-record avg w/o best day is −0.31, which meets the "≤ ~0" demotion condition.

**What to tell the owner plainly:**
- The automatic triggers have not fired: C3-BAR2 −10R (it is at −7.3R LR8 / −6.6R booked basis) and PRIME-RULES probation, which would flag it but keep it in for 10 more sessions.
- Moving it now is a discretionary call under WW-ST7, against "consistency over churn".
- **Rules-strict alternative:** keep it on PROBATION (flagged). It moves automatically at −10R, which is 2.7R away, about one burst day.

**Workbench fix: not now.**
- The shared RSI fix failed (31-40 of 45-46 setups worse; owner ST7-A).
- The window copy was declined (ST7-B).
- The SPY gate (WB1) failed on its first reversal day.
- WB1 and ST7Q already serve as its testing tune lane; let them build records.
- **Backlog idea only** (needs a 2-year lab test, both halves, before anything else): leave ETFs/ETPs out of the long dip-buy family. Live this rests on 7 trades and mostly one day, so it is weak evidence. It must be tested across the family, not tailored to ST7.

**Bar to come back to Primary** (C3-BAR2 + PRIME-RULES, all on its non-overlap record, after the promotion hold lifts):
- At least 20 traded sessions, including at least 5 in On Deck, and at least 15 active days.
- At least 30-40 trades after costs.
- Avg R without the best day > 0.
- Best day ≤ 40% of total R.
- At least 50% green days.
- Shrunk estimate > 0, which works out to **total R above +15R** (n × avg > 15; it is −7.3 now).
- Owner's yes.
- **Suggested extra check:** its burst days (3 or more lots on one bar) show a net R ≥ 0 and no burst day worse than about −5R. The lab says a −26R day is possible.

Supporting files are in /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/st7rev/: build.py, an.py, an2.py, an3.py, and paper.pkl (LR8 trade table).
