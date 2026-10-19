# giveback1019: why intraday gains are given back into the close (Primary, Testing 1, Testing 2)

*Educational only - not financial advice. Live **paper** results (rule 7), in-sample, 5-9 sessions per account: everything
below is a hypothesis, not proof. No locked block or holdout was touched.*

Sample: every complete live session through 2026-10-16. Primary 10-06..10-16 (9 sessions, 313 trades), Testing 1
10-09..10-16 (6, 1,495), Testing 2 10-12..10-16 (5, 2,281). 10-19 was mid-session (12:06 ET) when this ran and is used
only as a case study from the runner's intraday snapshots. Data: `journal.db` and `intraday/*.jsonl` from
`origin/mcf-data`, `mcf-data-testing`, `mcf-data-testing2`; SIP 1-min bars (Alpaca market data, read-only) for every
traded symbol plus SPY/QQQ/IWM (36 MB scratch, deleted). Costs are in everywhere: realized = journal `pnl_adj`; open
lots marked at the 1-min close less 1 bps + $0.01/sh; replay stops pay an extra $0.02/sh.
Configurations tried: **63** live replays + **8** long-history checks = **71**; bar max(1.5, sqrt(2 ln 71)) = **2.92**
(2.88 for the 63 live rows).

## Plain-English answer to the owner
The pattern is real but it is mostly **not** "big winners given back". Once costs are in, the intraday peaks are small:
Primary's median peak is $41 and only one day in nine got above $100 (10-12, +$133, and it kept +$116). What looks like
giving back is mostly the book continuing to trade after a small early high and losing: of the money lost between each
day's peak and the close, **65% (Primary), 83% (Testing 1) and 98% (Testing 2) came from new entries taken after the
peak**, and 95% / >100% / 84% came from trades on the wrong side of the index's move over that window (the book is one
correlated bet: mostly shorts in Primary/T1, longs in T2, all entered 10:00-11:59). Open winners reverting into stops is
the second cause in Primary (28%) and minor in T1 (11%) and T2 (1%). **Stops** are not generally too tight (median 6-7x
the 1-min ATR), but the tightest quarter of stops (< about 4x 1-min ATR) loses 0.3-0.4R per trade in every account, and
only 8-18% of stopped trades went on to reach their target. **Timing**: the 10-11 am entries carry the losses; from about 12:00 (Primary,
Testing 2) or 13:00 (Testing 1) the books are about flat. **Entries** are the main problem: 39% / 46% / 54% of losers never got +0.2R. **Exits**: no
exit change survives the history check - trailing stops did nothing or hurt, breakeven helped Primary live but **hurt**
on two years of history (valid -0.021R/trade, t -3.1), wider stops and time stops helped on 2025 but not on 2026. The
best-supported idea is stopping new entries after 11:00 (history train +0.042R/trade t 3.2, valid +0.028R t 2.1), but it
is below the bar, negative in down sessions, and it works mainly because the Primary book's expectancy is negative
everywhere, so trading less loses less. Recommendation: do not change stops or exits now; work on entry quality and on
not adding same-direction risk after the day has turned (backlog items below).

## Failures first
- **No rule passes.** On the long history 0 of 8 rules meet the pre-declared "supports" test (train and valid > 0, valid
  t >= 2.92, positive in up and down sessions). On the live sample, 3 per-account rows clear 2.88, all in Testing 2
  (5 sessions): WIDE125 t 5.56, SO05 t 4.20, WIDE150 t 3.89; with 5 days a t is very unstable, and WIDE did not hold
  on the Primary history (valid t 0.37 / 0.14). Pooled over 20 account-days, NOISE4 (t 3.14, post-hoc) and WIDE125
  (t 3.09) clear 2.88, but the three accounts share the same market days, so that is not independent evidence.
- **NOISE4 is post-hoc** (added to the plan after `diag.py` showed the pattern); its live numbers are partly fitted.
- **Primary's account-lock rules never fired** (Primary never reached 5U = $99 and then gave back 30%); the lock rows
  are 0 there by construction.
- **RW6G1 produced no entries** on the history2y 5-min frames, so the history check covers 11 of 12 Primary setups.
  Setups demoted from Primary (NS2, heat_fade_*, orb20_a, exhaustion_short) and the T1/T2 families were not checked on
  history (outside this task's scope).
- **The Primary book is negative on history in this harness:** baseline -0.118R/trade train (22,692 trades), -0.034R
  valid (19,963). Several "improvements" below are just less exposure to a negative book.
- Dropped trades in replays are not replaced by other signals (lot caps, T2's daily-loss halt and capital are not
  re-simulated). Replays start on the bar after the entry minute; simulator fidelity is 97-99% exit-reason match.

## 1. Per-day peak / trough / close (marked, costs in) - `daily_peaks.csv`
| account | date | trades | peak $ (time) | trough $ (time) | close $ | giveback $ | trades after peak | open at peak | SPY peak→close | QQQ peak→close |
|---|---|---|---|---|---|---|---|---|---|---|
| Primary | 10-06 | 44 | +51 (11:12) | -259 (15:26) | -128 | 179 | 18 | 18 | -0.22% | -0.41% |
| Primary | 10-07 | 16 | +41 (10:21) | -243 (14:21) | -265 | 306 | 10 | 5 | +0.31% | +0.45% |
| Primary | 10-08 | 48 | +30 (11:16) | -179 (15:25) | -141 | 171 | 22 | 9 | -0.07% | -0.82% |
| Primary | 10-09 | 70 | +0 (09:31) | -440 (10:57) | -254 | 254 | 70 | 0 | +0.27% | -0.09% |
| Primary | 10-12 | 22 | +133 (14:51) | -17 (11:41) | +116 | 17 | 0 | 3 | +0.10% | +0.11% |
| Primary | 10-13 | 18 | +81 (11:40) | -109 (14:32) | -102 | 183 | 3 | 10 | +0.24% | +0.47% |
| Primary | 10-14 | 11 | +81 (11:28) | -13 (10:48) | +60 | 21 | 2 | 1 | -0.29% | -0.77% |
| Primary | 10-15 | 48 | +14 (09:54) | -957 (15:43) | -927 | 941 | 47 | 1 | +0.87% | +1.65% |
| Primary | 10-16 | 36 | +25 (10:19) | -142 (11:29) | -14 | 40 | 24 | 11 | -1.01% | -1.64% |
| Testing 1 | 10-09 | 46 | +0 (10:09) | -108 (11:20) | -36 | 36 | 45 | 1 | +0.29% | +0.17% |
| Testing 1 | 10-12 | 204 | +145 (13:46) | -156 (12:08) | +18 | 127 | 40 | 109 | +0.04% | +0.02% |
| Testing 1 | 10-13 | 371 | +80 (11:39) | -753 (15:44) | -677 | 757 | 241 | 104 | +0.25% | +0.49% |
| Testing 1 | 10-14 | 326 | +274 (15:06) | -314 (13:04) | +8 | 266 | 2 | 125 | +0.33% | +0.33% |
| Testing 1 | 10-15 | 225 | +0 (09:31) | -1777 (11:16) | -1774 | 1774 | 225 | 0 | +0.75% | +1.44% |
| Testing 1 | 10-16 | 323 | +0 (09:31) | -342 (13:20) | -78 | 78 | 323 | 0 | -1.25% | -2.12% |
| Testing 2 | 10-12 | 360 | +5 (10:09) | -917 (14:53) | -809 | 814 | 303 | 27 | +0.02% | -0.02% |
| Testing 2 | 10-13 | 647 | +111 (10:12) | -453 (11:47) | -183 | 295 | 498 | 94 | +0.05% | -0.01% |
| Testing 2 | 10-14 | 353 | +0 (09:31) | -882 (12:25) | -865 | 865 | 353 | 0 | -0.67% | -1.27% |
| Testing 2 | 10-15 | 533 | +20 (10:12) | -1214 (15:43) | -1193 | 1212 | 439 | 41 | +0.51% | +0.96% |
| Testing 2 | 10-16 | 388 | +4 (09:54) | -1087 (15:16) | -1085 | 1089 | 364 | 22 | -1.06% | -1.56% |

| account | days | peak >= $50 | of those red at close | gave back > 50% | peak >= $100 | red | > 50% | sum of peaks | sum of closes | sum giveback | median giveback |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Primary | 9 | 4 | 2 | 2 | 1 | 0 | 0 | $457 | -$1,654 | $2,111 | $179 |
| Testing 1 | 6 | 3 | 1 | 3 | 2 | 0 | 2 | $499 | -$2,540 | $3,039 | $196 |
| Testing 2 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | $141 | -$4,134 | $4,275 | $865 |

- Only Testing 1 had a peak >= $250 (10-14, +$274 at 15:06 -> +$8). 9 of 20 account-days peaked at or below +$20,
  i.e. they were never meaningfully green. Of the total "giveback" only $1,097 is peak-to-zero; the rest is losses below zero.
- My curves match the runner's own intraday snapshot totals (e.g. Primary 10-12 peak +$133 vs snapshot +$136 at 14:49;
  T1 10-14 +$274 vs +$317; the gap is the cost haircut).

### Case study 10-19 (partial, runner snapshots to ~12:05 ET; not in any statistic)
- **Testing 1: +$685 at 10:03 -> -$501 at 11:50** (-$261 at 12:05). heat_fade_short and heat_fade_short-FD took the
  **same ~20 semiconductor shorts twice** at 09:50-09:52 (AEHR, AMD, CRDO, AAOI, ALAB, KLAC, LITE, NBIS, SOXL, SMH ...);
  36 hit targets by 10:04 (+$438), then QQQ rallied from -0.23% (10:00) to +0.64% (11:30) and the other 42 stopped
  (-$362): the pair's mark went +$317 -> +$3. After the peak, NS3, NS3-FD and RW4 (the same signal three times) shorted
  into the rally 10:17-10:51: 17 trades, all stopped, -$364. That is causes (a) + (b) + (c) together, doubled by
  duplicate setups.
- Primary: +$78 at 10:39 -> -$92 at 11:29 (MF3 + MF3-FD -$106 on the same 10:00-10:40 shorts as QQQ rose).
- Testing 2: +$67 at 10:20 -> -$87 at 12:03 (NM-RWN/RWR ns3 shorts and CWT14 longs).

## 2. Attribution of the peak -> close change - `giveback_attr.csv`, `giveback_attr_out.txt`
Each trade's contribution = its marked value at the close minus at the day's peak minute.

| account | total | (b) entered after peak | (a) open winners at peak | open losers at peak | (c) against SPY's peak->close move | (d) late flatten exits (>= 15:50) | worst entry hours | worst setups |
|---|---|---|---|---|---|---|---|---|
| Primary | -$2,078 | **-$1,346 (65%)**, 196 trades | -$588 (28%): 21 stopped -$583, 6 flattened -$125, 12 targets +$120 | -$145 | **-$1,979** (with: -$100) | -$381 (58 trades) | 10h -$1,026, 11h -$989 | NS2 -$1,006, orb20_a -$233, heat_fade_long -$229 |
| Testing 1 | -$3,058 | **-$2,531 (83%)**, 876 | -$344 (11%) | -$183 | **-$4,097** (with: +$1,039) | -$314 (446) | 10h -$1,039, 11h -$936, 12h -$567 | NS2-FD -$531, RW6-FD -$355, heat_fade_short-FD -$335 |
| Testing 2 | -$4,218 | **-$4,128 (98%)**, 1,957 | -$56 (1%) | -$35 | **-$3,529** (with: -$689) | -$118 (132) | 10h -$3,346 | CWT09-g5-lowerhalf -$661, CWT14 orl/pdl longs -$2,042 |

- Sides: Primary shorts -$1,640 vs longs -$439; T1 shorts -$2,482 / longs -$577; T2 longs -$2,807 / shorts -$1,411.
- (c) is the biggest single label: on 10-15 (SPY +0.87% from Primary's 09:54 peak) Primary's shorts lost -$962;
  on 10-16 (SPY -1.0%) T1/T2 longs lost. The book is one same-direction bet entered in the 10:00-11:59 polls.
- (d) late-day EOD flatten exits are a small part (-$118 to -$381); late holds are not the main leak.
- Holding period: losses are spread across holds; T1's are concentrated in trades held <= 30 min (-$1,806).

## 3. Per-trade diagnosis - `trades_diag.csv`, `diag_out.txt`
| | Primary | Testing 1 | Testing 2 |
|---|---|---|---|
| trades / win% / avg R (costs in) | 313 / 42% / -0.190 | 1,495 / 45% / -0.145 | 2,281 / 57% / -0.180 |
| target distance (median) | 0.91R | 0.93R | 0.46R |
| losers: median MFE | 0.30R | 0.22R | 0.18R |
| losers reaching >= 0.5R / >= 1R | 49 (27%) / 11 | 200 (24%) / 26 | 144 (15%) / 39 |
| losers never worked (MFE < 0.2R) | **71 (39%), -$1,718** | **376 (46%), -$4,071** | **525 (54%), -$5,515** |
| winners: MFE / realized / giveback (median) | 0.90 / 0.80 / 0.08R | 0.90 / 0.77 / 0.11R | 0.51 / 0.41 / 0.08R |
| time to MFE: winners / losers (median) | 75 / 6 min | 74 / 9 min | 15 / 3 min |
| stop / 1-min ATR(14) at entry (median, IQR) | 5.9 (4.2-8.3) | 7.4 (5.1-10.1) | 5.0 (3.7-6.9) |
| tightest stop quartile vs widest: avg R / stop rate | **-0.43R / 67%** vs +0.05R / 21% | **-0.37R / 64%** vs 0.00R / 18% | **-0.31R / 54%** vs -0.11R / 27% |
| stops that came back to entry / went on to the target | 35% / 12% | 30% / 8% | 37% / 18% |
| entry hour P/L | 10h -$748, 11h -$813, 12-14h +$91 | 9-10h -$1,352, 11h -$731, 13-14h -$70 | 10h -$3,322 (1,569 trades) |
| latency signal->fill (median / p90) | 1.5 / 3.2 s | 1.2 / 2.8 s | 1.3 / 3.0 s |
| entry slippage vs reference (mean) | 4.3 bps = 0.054R | 3.3 bps = 0.042R | 3.9 bps = 0.063R |

- Winners keep their peak (giveback 0.08-0.11R median); exits on winners are not the leak.
- Losers peak within minutes (3-9 min) and then fail; most never work at all -> entry selection/direction.
- Stopped-then-reversed is limited: only 8-18% of stops would have reached the target later.
- Latency and slippage are small and do not separate winners from losers (slippage terciles show no monotone pattern).

## 4. Counterfactual replays on the actual live trades (21 x 3 = 63, PLAN.md) - `replay_results.csv`, `replay_daily.csv`
Per cell: trades / win% / avg R / total $ / change vs actual $ / sessions better-worse / day-clustered t. Bar 2.88.

| config | Primary: trades / win% / avg R / total $ / chg $ / days better-worse / t | Testing 1: same | Testing 2: same | pooled 20 acct-days: chg $ / better-worse / t |
|---|---|---|---|---|
| ACTUAL | 313 / 42% / -0.190 / -1654 / +0 / 0-0 | 1495 / 45% / -0.145 / -2540 / +0 / 0-0 | 2281 / 57% / -0.180 / -4134 / +0 / 0-0 |  |
| BE050 | 313 / 36% / -0.146 / -1357 / +296 / 6-2 / t 2.00 | 1495 / 38% / -0.147 / -2495 / +45 / 3-3 / t 0.10 | 2281 / 55% / -0.181 / -4106 / +28 / 2-3 / t 0.30 | +370 / 11-8 / t 0.80 |
| BE075 | 313 / 39% / -0.163 / -1433 / +221 / 5-3 / t 1.57 | 1495 / 43% / -0.143 / -2526 / +14 / 2-4 / t 0.08 | 2281 / 56% / -0.183 / -4195 / -61 / 2-3 / t -0.87 | +174 / 9-10 / t 0.77 |
| BE100 | 313 / 41% / -0.182 / -1575 / +79 / 5-2 / t 1.09 | 1495 / 44% / -0.147 / -2557 / -17 / 3-2 / t -0.36 | 2281 / 57% / -0.171 / -4062 / +72 / 4-0 / t 1.44 | +135 / 12-4 / t 1.36 |
| TR1-05 | 313 / 44% / -0.176 / -1526 / +128 / 5-3 / t 1.50 | 1495 / 46% / -0.157 / -2707 / -167 / 2-3 / t -1.74 | 2281 / 58% / -0.176 / -4122 / +12 / 2-3 / t 0.16 | -27 / 9-9 / t -0.17 |
| TR1-10 | 313 / 42% / -0.188 / -1589 / +65 / 5-2 / t 1.03 | 1495 / 45% / -0.154 / -2653 / -113 / 2-3 / t -1.47 | 2281 / 58% / -0.174 / -4097 / +38 / 1-4 / t 0.39 | -10 / 8-9 / t -0.07 |
| LKG30-H | 313 / 42% / -0.190 / -1654 / +0 / 0-0 | 934 / 44% / -0.195 / -2019 / +521 / 2-1 / t 0.92 | 1717 / 54% / -0.235 / -3877 / +257 / 1-0 / t 1.00 | +778 / 3-1 / t 1.29 |
| LKG50-H | 313 / 42% / -0.190 / -1654 / +0 / 0-0 | 949 / 44% / -0.193 / -2072 / +468 / 2-1 / t 0.83 | 1717 / 54% / -0.235 / -3877 / +257 / 1-0 / t 1.00 | +726 / 3-1 / t 1.21 |
| LKG30-F | 313 / 42% / -0.190 / -1654 / +0 / 0-0 | 934 / 44% / -0.193 / -1733 / +807 / 3-0 / t 1.12 | 1717 / 54% / -0.234 / -3916 / +218 / 1-0 / t 1.00 | +1025 / 4-0 / t 1.36 |
| LKG50-F | 313 / 42% / -0.190 / -1654 / +0 / 0-0 | 949 / 44% / -0.188 / -1764 / +776 / 3-0 / t 1.10 | 1717 / 54% / -0.234 / -3916 / +218 / 1-0 / t 1.00 | +994 / 4-0 / t 1.35 |
| LKZ5-H | 312 / 42% / -0.190 / -1654 / +0 / 0-0 | 906 / 44% / -0.185 / -1843 / +697 / 3-0 / t 1.34 | 1681 / 54% / -0.236 / -3841 / +293 / 1-0 / t 1.00 | +990 / 4-0 / t 1.65 |
| LKZ10-H | 313 / 42% / -0.190 / -1654 / +0 / 0-0 | 1402 / 45% / -0.150 / -2391 / +149 / 2-0 / t 1.51 | 1689 / 54% / -0.236 / -3841 / +293 / 1-0 / t 1.00 | +443 / 3-0 / t 1.45 |
| CUT1100 | 168 / 44% / -0.183 / -932 / +721 / 6-3 / t 1.16 | 507 / 40% / -0.269 / -1352 / +1188 / 3-3 / t 1.41 | 1793 / 57% / -0.208 / -3814 / +320 / 3-1 / t 1.27 | +2230 / 12-7 / t 2.12 |
| CUT1200 | 243 / 41% / -0.229 / -1745 / -92 / 2-5 / t -0.61 | 809 / 43% / -0.222 / -2083 / +457 / 2-3 / t 0.82 | 2050 / 57% / -0.196 / -4019 / +115 / 3-0 / t 1.20 | +481 / 7-8 / t 0.84 |
| CUT1330 | 290 / 41% / -0.207 / -1685 / -31 / 1-4 / t -0.38 | 1220 / 44% / -0.179 / -2410 / +130 / 3-2 / t 0.53 | 2178 / 57% / -0.187 / -4107 / +27 / 2-0 / t 1.44 | +126 / 6-6 / t 0.51 |
| TS30 | 313 / 38% / -0.151 / -1375 / +279 / 5-4 / t 0.86 | 1495 / 39% / -0.156 / -2456 / +84 / 2-4 / t 0.22 | 2281 / 50% / -0.144 / -3058 / +1076 / 4-1 / t 2.74 | +1438 / 11-9 / t 2.04 |
| TS60 | 313 / 36% / -0.209 / -1593 / +61 / 6-3 / t 0.22 | 1495 / 40% / -0.143 / -2200 / +340 / 2-4 / t 1.00 | 2281 / 53% / -0.157 / -3532 / +602 / 5-0 / t 2.66 | +1003 / 13-7 / t 1.96 |
| WIDE125 | 313 / 46% / -0.180 / -1545 / +108 / 5-4 / t 1.22 | 1495 / 47% / -0.132 / -2329 / +211 / 5-1 / t 1.23 | 2281 / 60% / -0.155 / -3765 / +370 / 5-0 / t 5.56 | +689 / 15-5 / t 3.09 |
| WIDE150 | 313 / 48% / -0.165 / -1453 / +201 / 5-4 / t 1.25 | 1495 / 48% / -0.134 / -2293 / +247 / 5-1 / t 0.82 | 2281 / 62% / -0.134 / -3312 / +822 / 5-0 / t 3.89 | +1270 / 15-5 / t 2.74 |
| SO05 | 313 / 44% / -0.156 / -1467 / +187 / 7-2 / t 1.60 | 1495 / 48% / -0.140 / -2416 / +124 / 3-3 / t 0.33 | 2281 / 58% / -0.169 / -3972 / +163 / 5-0 / t 4.20 | +473 / 15-5 / t 1.27 |
| SO05BE | 313 / 55% / -0.134 / -1319 / +335 / 6-3 / t 1.85 | 1495 / 56% / -0.140 / -2393 / +147 / 3-3 / t 0.25 | 2281 / 61% / -0.170 / -3958 / +177 / 4-1 / t 2.23 | +658 / 13-7 / t 1.11 |
| NOISE4 | 242 / 45% / -0.139 / -1021 / +633 / 6-3 / t 2.15 | 1289 / 47% / -0.098 / -1754 / +786 / 5-1 / t 1.36 | 1566 / 61% / -0.140 / -2971 / +1163 / 5-0 / t 2.30 | +2582 / 16-4 / t 3.14 |

Without the best day: Primary CUT1100 +$136 (from +$721), BE050 +$182, NOISE4 +$386; T1 CUT1100 +$488, LKG30-F +$72;
T2 WIDE125 +$272, WIDE150 +$523, SO05 +$104, TS30 +$719. Lock triggers: `replay_lock_triggers.csv` (6 account-days).

Reading: trailing stops (TR1) never help; breakeven helps only Primary; account profit locks help on the few days they
fire (T1 3-0, T2 1-0) but they fire on 6 of 20 account-days, too few to judge; the cut-off and time-stop rows reduce
exposure to a negative book; wider stops (same $ risk) helped in all three accounts live (15 of 20 account-days), so some
stops do sit inside the noise - but that effect did not hold on the 2026 history (section 5).

## 5. Long-history check (Primary lab setups, open history only) - `hist_results.csv`, `hist_by_setup.csv`, `hist_out.txt`
42,655 entries of 11 Primary setups (history2y 5-min frames via `lib.load_month`; locked block absent and asserted),
exits replayed on `data/cache_hist` 1-min bars with the same simulator. Baseline fidelity: corr 0.97 with the frames'
production R, mean -0.079 vs -0.069R. Delta = rule minus baseline, original R per trade.

| rule | train delta (t, months +) | valid delta (t, months +) | valid up / down sessions | verdict |
|---|---|---|---|---|
| WIDE125 | +0.014 (2.95, 10/11) | +0.002 (0.37, 6/10) | +0.026 / -0.007 | not supported |
| WIDE150 | +0.022 (3.09, 9/11) | +0.001 (0.14, 6/10) | +0.047 / -0.025 | not supported |
| TS30 | +0.006 (0.40, 8/11) | -0.010 (-0.73, 5/10) | +0.073 / -0.078 | not supported |
| TS60 | +0.011 (0.86, 7/11) | -0.013 (-1.35, 3/10) | +0.035 / -0.054 | not supported |
| BE050 | -0.007 (-0.87, 3/11) | **-0.021 (-3.09, 2/10)** | +0.020 / -0.054 | not supported (harmful) |
| SO05BE | +0.004 (0.41, 7/11) | -0.018 (-2.11, 4/10) | +0.045 / -0.068 | not supported |
| NOISE4 | +0.023 (2.69, 10/11) | +0.004 (0.66, 5/10) | +0.044 / -0.016 | not supported |
| CUT1100 | **+0.042 (3.23, 10/11)** | **+0.028 (2.06, 7/10)** | +0.106 / -0.054 | not supported (t < 2.92, down < 0) |

Baselines: train -0.118R (22,692 trades, 234 days), valid -0.034R (19,963, 192 days). With CUT1100 valid is still
-0.007R/trade. Every exit rule's effect flips sign between up and down sessions: exits are a regime bet, not an edge.

## Multiple-testing verdict
71 configurations, bar 2.92 (2.88 for the 63 live rows). Live: only Testing 2's WIDE125 / SO05 / WIDE150 clear it, on 5
sessions, and the same rule family (WIDE) did not hold on the Primary history. History: 0 of 8 supported; the best
(CUT1100, valid t 2.06) is below the bar and fails the down-session gate. Nothing here justifies a stop or exit change.

## Proposed backlog items (not added; for the lead)
1. `gb-1019-noise-floor-stop` - Trades whose stop is < 4x the 1-min ATR(14) at entry lose (tightest quartile -0.31..-0.43R
   in all 3 accounts); test on history per live setup: skip vs widen-to-floor at the same $ risk, train/valid, regime
   gate (post-hoc origin; history so far: train +0.023 t 2.7, valid +0.004 t 0.7 for Primary).
2. `gb-1019-wide-stop-t05` - For t05s1 setups (T2 CWT families, target 0.46R) a 1.25x stop at the same $ risk with the
   target price unchanged raised win rate 57% -> 60% and P/L +$370 on 5/5 sessions (t 5.56); test on the CWT modules'
   history (not done here), train/valid/regime.
3. `gb-1019-cut-1100-fd` - No new entries after 11:00 for the Primary full-day (-FD, MF5, NS4) setups; history train
   +0.042R t 3.2, valid +0.028R t 2.1 but negative in down sessions; test a regime-aware version (e.g. cut only when SPY's
   from-open move is against the setup's side) before anything else.
4. `gb-1019-post-peak-index-guard` - After the account's intraday peak, block new entries whose side is against SPY/QQQ's
   move since the open (cause (c): 84-100%+ of the post-peak loss was against the index); test on history with the
   spy_fo/qqq_fo context columns for entries after 10:30 (related: `nightly-1016-trend-day-long-reversal-veto`).
5. `gb-1019-twin-setup-exposure` - Cap same-symbol, same-side exposure across a setup and its -FD / sibling twins
   (10-19 T1: heat_fade_short + -FD doubled ~20 semis shorts; NS3 + NS3-FD + RW4 tripled 17 losing shorts); risk/sizing
   item, parent `nightly-1016-primary-one-lot-per-symbol`; test by de-duplicating the live trade logs and on history.

Related prior backlog results: `sw-w4-book-exits` and `t6-exit-overlay` (book-level exit overlays) failed;
`nightly-1014-fd-short-late-giveback` is still an idea; `nl-1007-late-holds` failed.

## Files
PLAN.md (pre-declared, step-5 addendum written before the history run), common.py (loaders, marking, simulator),
fetch.py, curves.py, diag.py, replay.py, hist_entries.py, hist_replay.py; outputs daily_peaks.csv, giveback_attr.csv,
giveback_attr_out.txt, trades_diag.csv, diag_out.txt, replay_trades.csv, replay_daily.csv, replay_results.csv,
replay_lock_triggers.csv, replay_out.txt, hist_results.csv, hist_by_setup.csv, hist_out.txt. Scratch (bars, journals,
history sims) is outside the repo and deleted.

Educational only - not financial advice.
