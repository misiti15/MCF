Educational only — not financial advice

# Wave 2 packet: Friday review packet (W2 rerun, LR8 basis, 11-19 added) + Primary red days in account R

This is research and proposals only. No config, runtime, ledger, assignments or setup change was made, and no final decision is taken without the owner. The plan was pre-registered in [PLAN.md](PLAN.md) before scoring. Every live setup is listed one line each in [TABLE.md](TABLE.md), and all columns are in [scores.csv](scores.csv). Supporting files: [epoch1_base1.csv](epoch1_base1.csv), [primary_days.csv](primary_days.csv), [pbo.json](pbo.json), with code in `code/` (elig.py, packet.py, table.py).

**Data.** Live journals (run 1) of all ten accounts at the 11-19 close, covering 10-06..**11-19**. 11-20 is tomorrow and is not included.
- R is on the **LR8 basis**: `mcf.costs.cost_r_lr8` (DQ-P3, approved 11-19).
- **Account R (UNIT1)** = LR8 $ ÷ 0.25% of equity. Primary uses the prior close for each day. Other accounts use their 11-19 equity.
- Identical signals across accounts are counted once.
- Active days = sessions on which the setup was enabled in that day's snapshot, or emitted a signal. This matches `arena_reps.json` to within ±1 day.
- The locked block was not read. L3-gap-slope-fromopen-FD was scored, and no proposal touches it.

**Configurations: 7.** (1) C3-BAR2 plan view, with a CSCV PBO line for its ranking. (2) BAR2 strict non-overlap view. (3) Primary −10R demotion. (4) FOOTRACE-EXIT. (5) GY-LIFE graduation. (6) Epoch 1 vs BASE1, descriptive. (7) UNIT1 red-day decomposition, descriptive.
- Setups scored: **190 with trades** and 25 with none.
- Try-count bar max(1.5, √(2 ln 190)) = **3.24**. Lineage try-counts are not recorded per setup, so the pool N is used.

**Rule changes inside the window (ledger):**
- 10-20 promotion = move
- 10-23 per-setup latch rules
- 10-28 Primary sizing ≈$5k → ≈$4k
- 10-29 Primary −2R latch
- 10-30 L3-fromopen re-promoted
- 11-05 ROLL1
- 11-11 TEAM-6
- 11-12 LR1-LR8 (journal cost basis changes here; this packet re-costs everything before it to LR8)
- 11-16 ROT1
- 11-17 TSZ1 half-size testing lots, 15 WB copies, promotion hold, shadow run 3
- 11-18 GY-BENCH plus guests, SRCV1
- **11-19:** Epoch 1 / BASE1, C3-NS5 (Primary runs 5), C3-EXIT100 (20 moves), GY-ARCHIVE-20, GY-LIFE, C3-ROT/ROT2, C3-BAR2, C3-WB/WB5, DQ-P3, DQ-P4, UNIT1, U9-TGT, U9-ETB, RT-UNCAL, TAGS1, REPS2-LANE
- **From 11-20:** FOOTRACE-EXIT (replaces the EXIT100 thresholds), GY-FOOTRACE, 9 ultimate_1119 admissions (11 entries; 0 trades yet)

Every record that spans these dates mixes rule regimes.

## Headline
- **Primary: no member is at −10R.** ST7-FD is the nearest at **−7.3R** since 10-28 (−8.7R of it on 11-19), −0.307 w/o best day, −2.7 account R. The current five made +63.5 trade R / **+18.7 account R** (+$4,029) in Primary since admission. Without its best day (11-12), L3-fromopen is +0.066/trade (best-day share 82%, `1 day`).
- **Nothing passes C3-BAR2.** The L3 twins in On Deck again fail only the best-day check (lowdist 79%, rsi5hi 60%). 11-19 cost each of them about −2.1 to −2.4R, the L3 inverse-ETF leak (see the root cause).
- **FOOTRACE-EXIT on the 11-19 data flags 8 arena setups**: 543 trades, −184.8R, −9.4 account R. This is preliminary; the Friday run adds 11-20. No Graveyard resident graduates.
- **PBO (CSCV, 136 setups, 70 splits):** shrunk ranking 0.40, total R 0.51, raw avg R 0.61. With 4 more weeks of data, total R no longer beats the shrunk estimate (W6 had 0.24); raw avg R is still the worst. **0 setups with ≥ 30 trades reach the try-count bar.** The 2 that do have n = 6 and 8.
- **Epoch 1, session 1 (descriptive):** live-book shadow −16.15R / −4.18 account R vs BASE1 −25.34R / −9.13 account R. The whole difference is NS5: +9.19R / +4.95 account R avoided by the C3-NS5 move. This is one session, and the C3-EPOCH verdict needs ~2 SE.
- **Primary in account R, 33 sessions:** −133.4 trade R but only **−10.0 account R** (−$2,563). Trade R and account R disagree in sign on **3 days**: 10-26 and 11-18 were trade-red but account-green, and 11-05 was trade-green but account-red. On 78% of account-red days a **single setup** decides the sign.

## (a) Primary: keep / demote (C3-BAR2 demotion −10R since admission)

| Setup | Since | n | Act. days | Trade R | Avg R | Avg R w/o best day | Best-day share | Day t (bar 3.24) | Account R | $ (LR8) | 11-19 R | Fit / check | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L3-gap-slope-fromopen-FD | 10-30 | 158 | 15 | +37.9 | +0.240 | **+0.066** | 82% `1 day` (11-12) | −0.08 | **+15.98** | +3,208 | −6.49 | +0.126 / +0.279 | Keep (protected) |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 10-16 | 169 | 25 | +21.1 | +0.125 | −0.016 | 111% `1 day` (10-22) | +0.14 | +3.91 | +981 | +2.03 | +0.331 / +0.012 | Keep, watch |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 10-16 | 180 | 25 | +10.7 | +0.059 | −0.053 | 176% `1 day` (10-22) | +0.46 | +0.92 | +282 | −2.21 | +0.288 / −0.090 | Keep, watch |
| NM-ETF-late-dip-di-long | 11-11 | 15 | 7 | +1.1 | +0.075 | +0.034 | 66% `1 day` | +1.18 | +0.66 | +137 | −0.90 | +0.239 / −0.007 | Keep (too early) |
| ST7-rsi50dn-long-pm-t1s1-FD | 10-28 | 42 | 17 | −7.3 | −0.174 | −0.307 | n/a | −1.32 | −2.72 | −578 | −8.66 | +0.102 / −0.450 | Keep by rule (−7.3 > −10); see root-cause R2 |

- The LR8 basis lowers the booked totals: L3 38.7 → 37.9, RW3 25.3 → 21.1, RW5 16.5 → 10.7 (DQ-P3).
- RW3 and RW5 are still one-day records (10-22), and both are negative without that day.
- Trade R and $ differ in weight. Primary risk per lot since 10-28 has a median of **L3 $78**, RW3 $31, RW5 $25, ST7 $30. One L3 R is therefore ≈ 3 RW5 R in dollars. RW3 since 10-28 is −4.1 trade R but **+$362**.
- NS5 (moved 11-19) has a whole live record of 60 trades, −7.6R, −0.162 w/o best day. On 11-19 in On Deck it took 20 trades, −6.5R.

## (b) On Deck / arena → Primary (C3-BAR2): none ready (the promotion hold stands anyway)

| Setup | Account | n | Act. days | Trade R | Avg R | Avg R w/o best day | Best-day share | Shrunk | Non-overlap w/o best (plan / strict) | Account R | 11-19 R | Fails (plan; strict) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L3-gap-slope-lowdist-FD | On Deck | 111 | 29 | +23.1 | +0.208 | +0.062 | 79% `1 day` | +0.031 | +0.124 / +0.042 | +1.79 | −2.13 | best day; best day + shrunk |
| L3-gap-slope-rsi5hi-FD | On Deck | 141 | 21 | +22.0 | +0.156 | +0.086 | 60% `1 day` | +0.024 | +0.095 / +0.098 | +1.54 | −2.38 | best day; best day + shrunk |
| GEN-261020-09 (…MID-QQQltm0p3-holdtr-long) | Setup Gen. | 205 | 23 | +49.4 | +0.241 | −0.180 | 147% `1 day` | +0.097 | <0 | +3.47 | — | w/o best, green %, best day |
| CWT09-gapdn-vwaploss-g10-short | On Deck | 24 | 29 | +5.2 | +0.218 | +0.141 | 49% | −0.056 | +0.082 / +0.160 | +2.03 | — | n < 30, shrunk |

- Since W2 on 11-18: L3-lowdist w/o best day went from +0.120 to +0.062 and L3-rsi5hi from +0.098 to +0.086. This comes from LR8 plus 11-19.
- Every arena setup is in TABLE.md: 159 candidates scored, 0 READY, 0 NEAR.

## (c) FOOTRACE-EXIT (approved 11-20; preliminary on 11-19 data; the Friday run decides with 11-20)

| Setup | Account | n | Act. days (reps) | Trade R | Avg R | W/o best day | Day t | Account R | 11-19 R |
|---|---|---|---|---|---|---|---|---|---|
| GEN-261020-03-MACDhge0p079-BarsSinceLODle5-MID… | Testing B | 64 | 23 (22) | −50.1 | −0.782 | −0.798 | −3.89 | −2.92 | −1.37 |
| GEN-261022-08-EMAdChglem0p094-Flow3ge1…short | Testing E | 92 | 21 (20) | −26.6 | −0.290 | −0.526 | −1.66 | −2.50 | — |
| intraday_momentum | Testing F | 71 | 29 (31) | −22.9 | −0.323 | −0.343 | −2.47 | −0.25 | +0.38 |
| GEN-261029-02-RSI2le0-VWAPcrossesge9…long | Testing B | 73 | 16 (15) | −22.3 | −0.305 | −0.352 | −2.30 | −0.68 | −6.57 |
| GEN-261027-09-ORBfailDn-Gapge2…short | Testing C | 45 | 18 (17) | −20.2 | −0.448 | −0.636 | −1.71 | −0.34 | +3.36 |
| GEN-261020-01-MACDhge0p12-RSI5le25-PM…long | Setup Gen. | 55 | 23 (22) | −16.1 | −0.292 | −0.308 | −1.86 | −0.90 | — |
| GEN-261026-10-ORBfailDn-EMAdChglem0p051…long | Testing C | 41 | 19 (18) | −10.5 | −0.256 | −0.459 | −1.73 | −0.80 | — |
| GEN-261022-06-NewLOD-ORBfailUp…long | Testing F | 42 | 21 (20) | −9.7 | −0.230 | −0.333 | −2.13 | −0.18 | −1.12 |

- None of the 8 is rare (≥ 0.5 signals per active day), an 11-20 admission or a young WB copy.
- 16 WB copies are exempt as young (3 active days). Among them, MF2-FD-WB3 is at −24.9R on 27 trades and CWT14-pdl-WB3 at −26.7R on 64 trades. They become eligible once they reach 15 active days.
- GEN-261029-02 sits exactly on the 15-active-day line in `arena_reps`, so it may drop out if the official count differs.
- No Graveyard resident meets GY-LIFE graduation. The closest is RW6G1-FD: 37 Graveyard trades, 9 of the 15 days needed.

## (d) Epoch 1 vs BASE1: first read (descriptive, 1 session)

| 11-19 | n | Trade R | Account R | $ |
|---|---|---|---|---|
| Live (run 1) | 32 | −16.21 | −3.89 | −825 |
| Live book in shadow (run 3) | 32 | −16.15 | −4.18 | −888 |
| BASE1 (11-18 book incl. NS5, run 3) | 50 | −25.34 | −9.13 | −1,938 |
| **Epoch 1 − BASE1 (shadow pair)** | | **+9.19** | **+4.95** | **+1,050** |

- The pair differs only by NS5. All 18 of its shadow lots entered between 10:50 and 11:10, 12 of them on the 10:50 bar, so the −2R latch could not have acted: realized R was 0 until 11:24.
- NS5's rule is RSI(14) ≤ 30 on 5-min bars. A 10:50 burst fits the RSI warm-up class found in ST7-FD (root cause R2-i). I have not verified this.
- The live and shadow books agree within 0.06R, so the shadow is a usable control.
- 11-17 and 11-18 come before the epoch and only show shadow vs live agreement (shadow −5.72 vs live −2.46 on 11-17, −3.63 vs −5.52 on 11-18; those gaps were not examined here).

## (e) UNIT1: Primary's red days in account R (33 sessions, 10-06..11-19)

| | Sessions | Trade R | Account R | Trade-R green | Account-R green |
|---|---|---|---|---|---|
| Before 10-28 (≈$5k lots) | 16 | −46.3 | −5.89 | 4 | 5 |
| From 10-28 (≈$4k lots) | 17 | −87.1 | −4.14 | 5 | 5 |
| Since TEAM-6 (11-11) | 7 | +11.3 | **+10.7** | 2 | 3 |
| All | 33 | −133.4 | −10.0 (−23.7 w/o 11-12) | 9 | 10 |

**Sign agreement.**
- 24 trade-R red days. **2 of them were account-R green:**
  - 10-26: −4.1 trade R / +0.10 account R. Nineteen lots under $25 lost −6.9R; three $25-75 MF2 lots won.
  - 11-18: −5.5 trade R / +1.01 account R. L3 was −2.46 trade R but +1.33 account R, because its $75-150 lots won while its small lots lost.
- 1 trade-R green day was account-R red:
  - 11-05: +2.4 trade R / −2.12 account R. RW3 made +16.1 trade R on small lots, and MF4 lost −5.5 account R on ≥ $150 lots.

**Lot size decides the gap between the units.**

| Lot risk $ | Lots | Trade R | Account R |
|---|---|---|---|
| < $25 | 722 | −80.7 | −5.8 |
| $25-75 | 497 | −62.8 | −8.8 |
| $75-150 | 152 | +17.0 | **+9.0** |
| ≥ $150 | 26 | −6.9 | −4.5 |

- Lots under $25 carry 61% of the trade-R loss but only a small share of the dollars.
- On account-red days, the $25-75 lots are the largest account-R loss: −19.1 of −39.1.

**Which setups decide the sign on account-red days (23 days).**
- Deciders by number of days: MF4-FD 4, RW5 4, RW3 3; then 2 each for NS2, NS5, MF3, L3-fromopen, MF2-FD, L3-rsi5hi.
- Account R lost on red days: MF4-FD −11.1, MF2-FD −4.7, NS2 −3.9, L3-fromopen −3.6, L3-rsi5hi −3.3, RW5 −2.6, ST7 −2.3.
- MF2/MF4/NS2 are gone, so of today's five the red-day sign is decided mainly by **L3-fromopen** (11-02, 11-17) and **ST7** (11-19).
- Since 11-11, L3-fromopen sets the sign on 4 of 7 sessions (11-12, 11-16, 11-17, 11-18). Primary's account R is effectively "L3's day ± ST7".

## Proposals (reply codes; nothing applied)

| Code | Proposal | Evidence | Effect per setup | Conflict check | Rec |
|---|---|---|---|---|---|
| **PKT-FX** | At the Friday review, run the approved FOOTRACE-EXIT on data that includes 11-20 and move what it flags. The preliminary list is the 8 in (c). | −184.8R / −9.4 account R across 543 trades. Each setup's day t ≤ −1.5. | 8 setups → Graveyard (each listed in (c)); no other setup touched. | None with the trimmed-setup rule: these are approved-rule exits, not low-activity trims. GY-FOOTRACE rotation gives them playing time there. | Yes |
| **PKT-RSI** | Add NS5 (and every RSI(14) setup) to root-cause R2-i's intraday-only RSI test list. This is research only, with no setup change. | Its 11-19 BASE1 lots were a 12-lot 10:50 burst, −9.19R. | Research only; affects none now. | None. A setup change, if any, goes through the backlog and outside market hours, and for Primary only in the epoch window. | Yes |
| **PKT-LOT** | Friday review shows "$ per trade R" (median lot risk $) per setup beside trade R and account R. Display only. | L3 lot ≈ $78 vs RW3/RW5 $25-31. Sign flips on 3 days and for RW3 since 10-28. | 0 (display). | Keeps UNIT1's owner rule that setups are judged by trade R. Any sizing change would be a Primary change for the Friday epoch window and is **not** proposed. | Optional |
| **PKT-EPOCH** | No action on Epoch 1 after one session. Re-read at the Friday close with 11-20 (2 sessions; still descriptive). | +9.19R / +4.95 account R for the live book vs BASE1 (NS5 only). | — | None. | FYI |

Educational only — not financial advice
