# UPDAY Workbench RESULTS — Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD`: up-day copies
Educational only — not financial advice. Mechanic 2026-11-17, built ~02:15-03:00 UTC (after hours). Research files only:
**no config change, no deploy.** Same method as `../L3-gap-slope-fromopen-FD/` (up-day copies of the SHORT setup, not longs).
Compared against BOTH the parent and the previous Workbench copy **WB3** (start 10:30 + skip while SPY > +0.20% since the
09:50 close + 1R ≥ 0.40% of price; `research/workbench/RW3-gapdn-rsi5pop-flowsell-short-FD/RESULTS.md`).

## Verdict
**`RW3-gapdn-rsi5pop-flowsell-short-FD-WB4` (SW1) = WB3 with its SPY-up SKIP gate swapped for the L3-WB5 up-day parts:**
exit at the next 1-min open once SPY has risen +0.30% since entry, and no new entries after 12:00 while SPY is > +0.15% above
its 09:50 close (window 10:30-15:00 and 1R ≥ 0.40% of price kept). **PASS vs the parent AND beats WB3 in both tests** on avg R,
avg R w/o best day and worst day. **WB3 is not the up-day answer:** its skip gate removes the trades taken once the rise is
visible, but the up-day trades it keeps (entered before the rise) are worse per trade (2-year up days −0.253 → −0.357).

| test | config | trades | avg R | w/o best day | worst day | R / session | up days avg R (n / total R) | down days | quiet days |
|---|---|---|---|---|---|---|---|---|---|
| Session replay | parent | 210 | +0.168 | +0.067 | −10.0 | +1.47 | −0.125 (34 / −4.3R) | +0.497 (91 / +45.2R) | −0.066 (85 / −5.6R) |
| Session replay | WB3 | 137 | +0.244 | +0.114 | −8.7 | +1.39 | +0.198 (6 / +1.2R) | +0.478 (76 / +36.3R) | −0.074 (55 / −4.1R) |
| Session replay | **WB4 (SW1)** | 153 | **+0.259** | **+0.160** | **−6.9** | **+1.65** | **+0.462 (10 / +4.6R)** | +0.434 (77 / +33.4R) | +0.024 (66 / +1.6R) |
| 2-year backtest | parent | 4,927 | −0.030 | −0.036 | −19.9 | −0.33 | −0.252 (1,459 / −368.4R) | +0.158 (1,511 / +239.5R) | −0.009 (1,957 / −17.4R) |
| 2-year backtest | WB3 | 3,174 | −0.007 | −0.016 | −19.5 | −0.05 | −0.357 (475 / −169.5R) | +0.155 (1,334 / +207.3R) | −0.044 (1,365 / −59.4R) |
| 2-year backtest | **WB4 (SW1)** | 3,655 | **−0.005** | **−0.013** | **−16.4** | −0.04 | **−0.207 (819 / −169.7R)** | +0.151 (1,349 / +203.3R) | −0.035 (1,487 / −52.1R) |
- Test days: replay 24 sessions (7 up / 7 down / 10 quiet); 2-year 446 (149 up / 121 down / 176 quiet). Day type = SPY 09:50
  close → 16:00, ±0.25% (reporting only; every gate/exit uses only SPY data known at that minute).
- **Trades kept:** vs parent 73% / 74%; vs WB3 112% / 115% (more trades: up-state entries before 12:00 come back).
- **Down-day cost** vs WB3: −0.044 R/trade replay (−2.9R over 7 sessions), −0.004 R/trade 2-year (−4.0R). Up days: +0.264 / +0.150
  R/trade vs WB3 (replay sample is only 6-10 trades — the 2-year carries the evidence).
- 2-year splits (avg R) parent / WB3 / WB4: TRAIN −0.074 / −0.057 / −0.045, VALID −0.002 / +0.016 / +0.011, FWD +0.136 / +0.194 /
  +0.204 (VALID 0.005 below WB3). Paired-by-day t vs WB3: +1.33 replay / +0.07 2-year; vs parent +0.28 / +2.16. Configs counted
  22 (bar 2.49; lineage with the first RW3 run's 45: 67, bar 2.90): nothing clears it — passes on meet-or-exceed.
- The 2-year gain vs WB3 is small (−0.007 → −0.005): the copy is better mainly in the replay, in w/o-best-day / worst-day, and
  on up days; still slightly below zero over 2 years after costs.
- Runner work: the in-trade SPY exit needs the runner hook specified in `../L3-gap-slope-fromopen-FD/RESULTS.md` ("Runner
  spec"). The entry part works today in a lab module from the `spy_fo` context column (as WB3 already does).

Also passing vs WB3 (not chosen): W-Y5 WB3 + SPY exit +0.35% (replay +0.240 meets, 2-year **+0.005**, worst day −17.6R; up days
2-year −0.274, replay unchanged) — positive 2-year, but keeps WB3's skip gate and so lifts up days less; W-Y4 (+0.40%), W-YU, SW2.

## Every configuration (22; pre-declared in `code/declup.py`, ROUND1 then ROUND2, each before its scores)
| config | replay n / avg R / w/o best / worst day | replay up / down / quiet | 2y n / avg R / w/o best / worst day | 2y up / down / quiet | vs parent | vs WB3 |
|---|---|---|---|---|---|---|
| PARENT | 210 / +0.168 / +0.067 / -10.0 | -0.125 / +0.497 / -0.066 | 4927 / -0.030 / -0.036 / -19.9 | -0.253 / +0.159 / -0.009 | — | FAIL (replay avg +0.168<+0.244; replay w/o best +0.067; replay worst day -10.0; 2y avg -0.030<-0.007; 2y w/o best -0.036) |
| WB3 | 137 / +0.244 / +0.114 / -8.7 | +0.198 / +0.478 / -0.074 | 3174 / -0.007 / -0.016 / -19.5 | -0.357 / +0.155 / -0.043 | PASS | — |
| P-Y1 exit if SPY +0.30% since entry | 210 / +0.168 / +0.076 / -8.2 | +0.019 / +0.458 / -0.082 | 4917 / -0.022 / -0.028 / -14.7 | -0.201 / +0.153 / -0.025 | PASS | FAIL (replay avg +0.168<+0.244; replay w/o best +0.076; 2y avg -0.022<-0.007) |
| P-Y2 exit if SPY +0.50% since entry | 210 / +0.176 / +0.076 / -10.3 | -0.056 / +0.497 / -0.074 | 4919 / -0.022 / -0.028 / -22.1 | -0.228 / +0.155 / -0.005 | FAIL (2y worst day -22.1) | FAIL (replay avg +0.176<+0.244; replay w/o best +0.076; replay worst day -10.3; 2y avg -0.022<-0.007; 2y worst day -22.1) |
| P-Y3 exit if SPY +0.20% since entry | 199 / +0.115 / +0.009 / -8.1 | +0.130 / +0.331 / -0.095 | 4922 / -0.024 / -0.031 / -16.3 | -0.168 / +0.121 / -0.031 | FAIL (replay avg +0.115<+0.168; replay w/o best +0.009) | FAIL (replay avg +0.115<+0.244; replay w/o best +0.009; 2y avg -0.024<-0.007) |
| P-Z1 exit if SPY +0.30% & under water | 210 / +0.158 / +0.061 / -8.8 | -0.006 / +0.452 / -0.091 | 4900 / -0.023 / -0.029 / -15.2 | -0.211 / +0.152 / -0.020 | FAIL (replay avg +0.158<+0.168) | FAIL (replay avg +0.158<+0.244; replay w/o best +0.061; 2y avg -0.023<-0.007) |
| P-T1 U15: entries end 12:00 | 178 / +0.241 / +0.132 / -10.0 | -0.064 / +0.497 / -0.020 | 4306 / -0.030 / -0.037 / -19.9 | -0.277 / +0.148 / -0.035 | PASS | FAIL (replay worst day -10.0; 2y avg -0.030<-0.007; 2y w/o best -0.037) |
| P-L3 L3-WB5 recipe (Y1 + U15 end 12:00) | 178 / +0.241 / +0.143 / -8.2 | +0.318 / +0.458 / -0.039 | 4301 / -0.022 / -0.030 / -14.7 | -0.216 / +0.143 / -0.050 | PASS | FAIL (2y avg -0.022<-0.007) |
| P-X1 U15: max hold 60 | 210 / +0.200 / +0.103 / -10.0 | +0.101 / +0.493 / -0.074 | 4960 / -0.023 / -0.029 / -19.9 | -0.183 / +0.147 / -0.033 | PASS | FAIL (replay avg +0.200<+0.244; replay worst day -10.0; 2y avg -0.023<-0.007) |
| P-G3 skip SPY last-30m>+0.20% | 160 / -0.012 / -0.087 / -9.9 | -0.172 / +0.278 / -0.166 | 4083 / -0.007 / -0.014 / -15.2 | -0.213 / +0.166 / +0.010 | FAIL (replay avg -0.012<+0.168; replay w/o best -0.087) | FAIL (replay avg -0.012<+0.244; replay w/o best -0.087; replay worst day -9.9) |
| W-Y1 WB3 + exit if SPY +0.30% since entry | 137 / +0.227 / +0.108 / -6.9 | +0.180 / +0.432 / -0.050 | 3152 / +0.011 / +0.002 / -16.4 | -0.256 / +0.150 / -0.035 | PASS | FAIL (replay avg +0.227<+0.244) |
| W-Y2 WB3 + exit if SPY +0.50% since entry | 137 / +0.239 / +0.107 / -9.1 | +0.198 / +0.478 / -0.087 | 3163 / -0.002 / -0.011 / -22.1 | -0.324 / +0.150 / -0.038 | FAIL (2y worst day -22.1) | FAIL (2y worst day -22.1) |
| W-Y3 WB3 + exit if SPY +0.20% since entry | 126 / +0.111 / -0.045 / -7.0 | +0.498 / +0.255 / -0.108 | 3151 / -0.007 / -0.016 / -16.3 | -0.231 / +0.117 / -0.051 | FAIL (replay avg +0.111<+0.168; replay w/o best -0.045) | FAIL (replay avg +0.111<+0.244; replay w/o best -0.045) |
| W-Z1 WB3 + exit if SPY +0.30% & under water | 137 / +0.218 / +0.092 / -7.6 | +0.198 / +0.424 / -0.064 | 3151 / +0.008 / -0.001 / -16.5 | -0.268 / +0.149 / -0.037 | PASS | FAIL (replay avg +0.218<+0.244; replay w/o best +0.092) |
| W-T1 WB3 + R10: entries end 12:00 | 117 / +0.153 / +0.063 / -8.6 | +0.198 / +0.374 / -0.095 | 2652 / +0.003 / -0.007 / -19.3 | -0.335 / +0.182 / -0.028 | FAIL (replay avg +0.153<+0.168) | FAIL (replay avg +0.153<+0.244; replay w/o best +0.063) |
| W-L3 WB3 + Y1 + R10 end 12:00 | 117 / +0.134 / +0.059 / -6.5 | +0.180 / +0.314 / -0.068 | 2649 / +0.012 / +0.002 / -16.4 | -0.236 / +0.167 / -0.032 | FAIL (replay avg +0.134<+0.168) | FAIL (replay avg +0.134<+0.244; replay w/o best +0.059) |
| W-X1 WB3 + R10: max hold 60 | 137 / +0.183 / +0.053 / -7.9 | +0.198 / +0.399 / -0.116 | 3190 / -0.008 / -0.017 / -21.6 | -0.322 / +0.143 / -0.045 | PASS | FAIL (replay avg +0.183<+0.244; replay w/o best +0.053; 2y worst day -21.6) |
| W-G3 WB3 + skip SPY last-30m>+0.20% | 107 / +0.087 / -0.009 / -8.7 | +0.198 / +0.272 / -0.094 | 2717 / +0.015 / +0.004 / -19.3 | -0.323 / +0.176 / -0.012 | FAIL (replay avg +0.087<+0.168; replay w/o best -0.009) | FAIL (replay avg +0.087<+0.244; replay w/o best -0.009) |
| W-Y4 WB3 + exit if SPY +0.40% since entry | 137 / +0.240 / +0.108 / -8.6 | +0.198 / +0.467 / -0.069 | 3167 / +0.003 / -0.006 / -18.8 | -0.290 / +0.146 / -0.036 | PASS | PASS |
| W-Y5 WB3 + exit if SPY +0.35% since entry | 137 / +0.240 / +0.114 / -8.1 | +0.198 / +0.460 / -0.059 | 3165 / +0.005 / -0.004 / -17.6 | -0.274 / +0.151 / -0.041 | PASS | PASS |
| W-YU WB3 + R10 trades: exit if SPY +0.30% | 137 / +0.239 / +0.107 / -8.6 | +0.198 / +0.478 / -0.087 | 3174 / +0.001 / -0.008 / -19.3 | -0.338 / +0.164 / -0.041 | PASS | PASS |
| SW1 WB3 gate swapped for WB5 recipe (Y1 + U15 end 12:00) | 153 / +0.259 / +0.160 / -6.9 | +0.462 / +0.434 / +0.024 | 3655 / -0.005 / -0.013 / -16.4 | -0.207 / +0.151 / -0.035 | PASS | PASS |
| SW2 SW1 with SPY exit +0.40% | 153 / +0.260 / +0.148 / -8.6 | +0.320 / +0.469 / +0.007 | 3679 / -0.010 / -0.018 / -18.8 | -0.230 / +0.146 / -0.027 | PASS | PASS |
| SW3 WB3 gate 0.20->0.30 + Y1 | 150 / +0.190 / +0.076 / -6.9 | +0.293 / +0.432 / -0.096 | 3479 / +0.001 / -0.008 / -16.4 | -0.242 / +0.155 / -0.035 | PASS | FAIL (replay avg +0.190<+0.244; replay w/o best +0.076) |

Method: the RW3 Workbench bench reused unchanged (`research/workbench/RW3-gapdn-rsi5pop-flowsell-short-FD/code/sim_rw3.py`,
`load.py`; parent 210 / +0.168, 4,927 / −0.030 and WB3 137 / +0.244, 3,174 / −0.007 reproduced exactly) wrapped by the UPDAY
layers (`code/uplayer.py`: up-state entry layers remove U bars before the setup's first-bar rule; exits add the in-trade SPY exit
and U-only holds). LR8 costs, locked block 2024-11-01..2025-02-28 never read, E90 borrow proxy, ADV ≥ $95M, Primary's book
(≤ 30 lots, ≤ 3 per symbol, −2R latch). SPY 1-min = previous cache + read-only SIP GET to 11-16. Rule changes inside the replay
window: as listed in the first RW3 RESULTS (10-21 promotion = move, 10-28 Primary cap 30, 10-29 −2R latch, 10-30 Testing CF,
11-11 TEAM-6, 11-12 LR1/3/5/7/8); the replay applies today's rules to every session.
