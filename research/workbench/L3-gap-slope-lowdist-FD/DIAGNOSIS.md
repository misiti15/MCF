# Diagnosis — Gap-Down Bounce-off-Low Fade (all day) `L3-gap-slope-lowdist-FD` (On Deck)
Educational only — not financial advice. Mechanic 2026-11-16 (built after the close; research files only, no config change).

Engine (teardown, `L3-gap-slope-lowdist-FD_engine.png`, full table in `BLUEPRINT_worst5.md`): P1 universe (ADV ≥ $5M core) · P2 price ≥ $5 ·
P3 earnings blackout · P4 prefilter gap ≤ −2.66% · P5 shortable + ETB · P6 window 09:50-15:00 · P7 no entry before 09:50 · P8 refire OFF
(first qualifying bar per symbol-day) · P9 gap ≤ −2.657% · P10 SMA20 slope > 0.372% · P11 dist from low of day > 0.782 daily ATR ·
P12 dist ≤ 0.976 ATR · P13 150 open lots per setup · P14 3 lots per symbol · P15 setup latch off · P16 account stop −300R · P17 cost
filter stop-exit cost ≤ 0.15R · P18 spread/quote checks · P19 short at the signal-bar close · P20 1R = 0.25 × daily ATR · P21/P22 sizing ·
P23 stop 1R · P24 target 1R · P25 no scale-out · P26 flat 15:55.

Live record (diagnosis only — NOT used in the pass decision): 105 trades / 16 sessions 10-13..11-12, +0.227R after costs, win 63%,
avg R w/o best day +0.077R; best day 11-12 = 76% of R (**1-day record**). Exit mix target 55 / stop 25 / time 25. Of 462 live signals
170 were blocked by borrow (P5), 72 by the account halt (P16, old 120R stop), 50 by the split-tape gate (off since 11-12), 43 by quotes.
Rule changes inside the record window (ledger): 10-20 twin-held block + Testing −2R setup latch; 10-23 latch off (ST-A); 10-30 cost
filter 0.15R (CF, P17); 11-11 TEAM-6 moves; 11-12 LR1 flatten rule, LR5 position check, LR8 cost model, account stop 300R, split-tape
gate off (ODX-1). The backtests below apply today's rules to every session, so these do not mix into the comparison.

## The 5 worst live trades (PNG `_worst1.._worst5`; prices/times on the charts)
| trade | what happened | part responsible | small tweak → effect on THIS trade |
|---|---|---|---|
| UGP 10-26 −1.30R | short 12:25:51 @ 6.40 (1R $0.07), MFE +0.14R, stop 12:34:46 @ 6.47 (9 min) | P9 gap −19.4% (a collapse, not a fade); P5/P20 thin $R; rsi5 0 at entry (bar still falling) | rsi5 ≥ 50: skipped. gap ≥ −10%: skipped |
| ITUB 10-26 −1.27R | short 12:05:43 @ 7.49 (1R $0.08), MFE +0.38R, stop 12:50:48 @ 7.57 | P9 gap −22.8%; rsi5 29 | rsi5 ≥ 50: skipped. gap ≥ −10%: skipped |
| SNAP 10-22 −1.24R | short 11:01:27 @ 6.45, MFE +0.43R, stop 11:35:29 @ 6.55 | P10 slope just turned (0.40); P11 dist 0.83 | dist > 0.82 keeps it (0.834); none of the copies remove it |
| TIGO 11-12 −1.22R | short 12:25:48 @ 81.71, MFE +0.34R, stop 12:50:41 @ 82.34 | entered below the open (fromOpen −3.9%) | rsi5 55 / dist 0.848: kept by every copy |
| NG 10-29 −1.20R | short 11:35:35 @ 6.19, MFE +0.24R, drifted, stop 13:08:35 @ 6.27 (93 min) | P26 no clock; P11 dist 0.807 | dist > 0.82: skipped. max hold 75: out 12:50 @ 6.24 ≈ −0.60R |

## The 5 best live trades (PNG `_best1.._best5`)
| trade | what happened | effect of the recommended copy (WB4) |
|---|---|---|
| PENG 10-13 +1.86R | 12:31:35 @ 79.83 → target 13:03:00 @ 78.13 (31 min) | dist 0.81 ≤ 0.82: **not taken** (gives this one back) |
| CART 10-26 +1.56R | 10:40:37 @ 54.73 → target 11:02:14 @ 54.11 | kept (rsi5 100, dist 0.85) |
| NTSK 11-05 +1.39R | 11:51:04 @ 22.45 → target 12:45:13 @ 21.94 | rsi5 12: **not taken** |
| CLSK 10-20 +1.37R | 10:41:06 @ 8.79 → target 11:14:17 @ 8.55 | kept (dist 0.824, rsi5 83); same exit |
| APLD 10-20 +1.35R | 10:40:52 @ 19.97 → target 11:14:04 @ 19.46 | kept; same exit (33 min) |
All 5 best hit target inside 55 minutes, so the 75-minute clock does not touch them; the entry parts drop 2 of them.

## All-trades component analysis
Live (105 trades, journal R): losers are mostly FAST stops (worst 5 held 9-93 min); rsi5 < 50 at entry 20 trades −0.07R vs +0.30R
otherwise; gap deeper than −10% 5 trades −0.49R; fromOpen < 0 11 trades −0.23R; 12:00-13:00 22 trades −0.16R. Two live parts point the
other way: dist ≤ 0.82 trades averaged +0.33R live (36 trades) and the 75-min clock would have cut live R (11-12: +18.8R → +7.6R).
Parent replay of the live sessions (195 trades, LR8 costs): **two days decide it** — 10-15 49 trades −19.7R (signals 11:15-11:50,
median MFE +0.8R, then a 2-4 h drift to the stop) and 11-12 57 trades +38.5R; avg R w/o best day −0.027. Stops: 63, median hold 126 min,
mean MFE +0.47R; trades held > 120 min average +0.02R vs +0.31R for those out in 75 min.
Parent 2-year (3,035 trades, −0.085R; TRAIN −0.075 / VALID −0.084 / FWD −0.193): worst day **2025-04-07 308 trades −164R** (tariff
reversal day — every gap-down stock bounced and kept going); 44% of trades stopped; up-market days −0.277R, down days +0.181R.

Which part is most often responsible:
1. **P26 time exit** — losers drift for hours after being green (10-15 in the replay: 36 of 63 replay stops and 433 of 1,347 2-year stops came after more than 75 min; 337 of those 2-year stops had been +0.5R first). A fixed 75-min clock
   wins in the replay (+0.178 → +0.257) and over 2 years (−0.085 → −0.068; FWD −0.193 → +0.089), but gives back long winners on trend
   days (replay 11-12 +38.5 → +22.7R). 60/90/120 min are close neighbours (all pass).
2. **Missing momentum check (new layer)** — entries while the 5-min bar is still falling (rsi5 < 50) are the mass-reversal losers: rsi5 ≥ 50
   takes the 2y worst day from −164R to −45R and the 2y avg from −0.085 to −0.018 (replay unchanged, +0.178). Honest: most of the 2y gain
   is April 2025; ex-April it is −0.086 → −0.076.
3. **P11 lower dist bound** — the first 0.78-0.82 ATR of the bounce is the weakest band in both backtests (2y VALID −0.084 → −0.057,
   replay w/o best day −0.027 → −0.001); live disagrees on 36 trades (+0.33R), noted.
Not responsible / tried and failed: window (end 13:00/14:00 lower the 2y), gap −3.2 (the sibling part: replay falls to +0.121), slope,
fromOpen gates (replay up, 2y down), price/1R floors, refire (worst day −73R), stop 1.25R, cost filter 0.10, SPY gate after 09:50
(cuts 60% of replay trades). P1/P3/P5/P18/P21/P22 are account parts the backtest cannot vary on identical terms (P5 modelled by the
E90 borrow proxy; ADV not in the replay frames).

Candidate tweaks picked (one part each): WB1 dist > 0.82 (P11) · WB2 max hold 75 min (P26) · WB3 rsi5 ≥ 50 (new layer); combo WB4.
Sibling parts (L3-gap-slope-fromopen-FD WB4: 13:00 end + gap −3.2 + 75-min hold): **only the 75-min hold transfers**; 13:00 end and
gap −3.2 hurt this setup (V01, V04, V26/V27 in RESULTS.md).
