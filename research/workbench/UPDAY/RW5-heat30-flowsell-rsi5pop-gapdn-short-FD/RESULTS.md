# UPDAY Workbench RESULTS — Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`: up-day copies
Educational only — not financial advice. Mechanic 2026-11-17, built ~02:15-03:00 UTC (after hours). Research files only:
**no config change, no deploy.** Same method as `../L3-gap-slope-fromopen-FD/` (up-day copies of the SHORT setup, not longs).
Compared against BOTH the parent and the previous Workbench copy **WB3** (skip while SPY > +0.20% since the 09:50 close +
stop-exit cost ≤ 15% of 1R + entries from 10:15; `research/workbench/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD/RESULTS.md`).

## Verdict
**`RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB4` (W-Y4) = WB3 + exit at the next 1-min open once SPY has risen +0.40% since
entry.** PASS vs the parent and **beats WB3 in both tests** on avg R, avg R w/o best day and worst day — but by a small margin.
**For RW5, WB3 already is most of the up-day answer:** its SPY-up skip gate is needed (swapping it for the L3-WB5 recipe, SW1/
SW2/SW4, is worse than WB3 in both tests), and the SPY exit adds a small extra up-day lift on top (2-year up days −0.240 → −0.207).

| test | config | trades | avg R | w/o best day | worst day | R / session | up days avg R (n / total R) | down days | quiet days |
|---|---|---|---|---|---|---|---|---|---|
| Session replay | parent | 205 | +0.117 | +0.036 | −13.4 | +0.96 | −0.140 (49 / −6.9R) | +0.425 (65 / +27.7R) | +0.036 (91 / +3.2R) |
| Session replay | WB3 | 100 | +0.191 | +0.072 | −10.3 | +0.77 | +0.559 (8 / +4.5R) | +0.531 (48 / +25.5R) | −0.246 (44 / −10.8R) |
| Session replay | **WB4 (W-Y4)** | 100 | **+0.200** | **+0.083** | **−9.8** | +0.80 | +0.559 (8 / +4.5R) | +0.531 (48 / +25.5R) | −0.225 (44 / −9.9R) |
| 2-year backtest | parent | 4,633 | −0.031 | −0.037 | −25.3 | −0.33 | −0.311 (1,461 / −454.5R) | +0.196 (1,276 / +250.7R) | +0.031 (1,896 / +58.4R) |
| 2-year backtest | WB3 | 2,435 | +0.017 | +0.009 | −15.9 | +0.10 | −0.240 (392 / −94.1R) | +0.181 (948 / +171.7R) | −0.032 (1,095 / −35.1R) |
| 2-year backtest | **WB4 (W-Y4)** | 2,439 | **+0.023** | **+0.014** | **−15.8** | **+0.13** | **−0.207 (392 / −81.1R)** | +0.177 (948 / +168.2R) | −0.028 (1,099 / −31.3R) |
- Test days: replay 25 sessions (8 up / 7 down / 10 quiet); 2-year 446 (149 up / 121 down / 176 quiet). Day type = SPY 09:50
  close → 16:00, ±0.25% (reporting only; the exit uses only SPY data known at that minute).
- **Trades kept:** 100% of WB3's (100 / 2,439 vs 100 / 2,435); vs parent 49% / 53% (WB3's gate and filters).
- **Down-day cost** vs WB3: 0 in the replay; −0.004 R/trade in the 2-year (−3.5R). Up days +13.1R (2-year); replay up days
  unchanged (the 8 replay up-day trades never saw SPY +0.40% after entry). Quiet days +0.9R / +3.8R.
- 2-year splits (avg R) parent / WB3 / WB4: TRAIN −0.047 / −0.011 / +0.004, VALID −0.035 / +0.020 / +0.018, FWD +0.129 / +0.221 /
  +0.215 (VALID / FWD a hair below WB3). Paired-by-day t vs WB3: +1.44 replay / +0.85 2-year; vs parent −0.20 / +2.60. Configs
  counted 22 (bar 2.49; lineage with the first RW5 run's 38: 60, bar 2.86): the 2-year t vs parent clears 2.49, not 2.86.
- Positive after costs in both tests (+0.200 / +0.023R), as WB3 was; the gain over WB3 is small (+0.009 / +0.006R per trade).
- Runner work: the SPY-since-entry exit (`spy_exit_pct: 0.40`) — spec in `../L3-gap-slope-fromopen-FD/RESULTS.md` ("Runner spec").

Also passing vs WB3 (not chosen): W-Z2 (+0.40% only while under water: +0.202 / +0.023, up days −0.214 — same result, needs the
extra flag), W-Z1 (under water +0.30%: replay +0.182 meets, 2-year +0.024), W-Y2 (+0.50%), W-Y5 (+0.35%).

## Every configuration (22; pre-declared in `code/declup.py`, ROUND1 then ROUND2, each before its scores)
| config | replay n / avg R / w/o best / worst day | replay up / down / quiet | 2y n / avg R / w/o best / worst day | 2y up / down / quiet | vs parent | vs WB3 |
|---|---|---|---|---|---|---|
| PARENT | 205 / +0.117 / +0.036 / -13.4 | -0.140 / +0.425 / +0.035 | 4633 / -0.031 / -0.037 / -25.3 | -0.311 / +0.196 / +0.031 | — | FAIL (replay avg +0.117<+0.191; replay w/o best +0.036; replay worst day -13.4; 2y avg -0.031<+0.017; 2y w/o best -0.037; 2y worst day -25.3) |
| WB3 | 100 / +0.191 / +0.072 / -10.3 | +0.559 / +0.531 / -0.246 | 2435 / +0.017 / +0.009 / -15.9 | -0.240 / +0.181 / -0.032 | PASS | — |
| P-Y1 exit if SPY +0.30% since entry | 201 / +0.165 / +0.091 / -10.3 | +0.067 / +0.411 / +0.039 | 4637 / -0.024 / -0.029 / -23.6 | -0.259 / +0.176 / +0.025 | PASS | FAIL (replay avg +0.165<+0.191; 2y avg -0.024<+0.017; 2y w/o best -0.029; 2y worst day -23.6) |
| P-Y2 exit if SPY +0.50% since entry | 200 / +0.136 / +0.055 / -13.0 | -0.073 / +0.425 / +0.030 | 4632 / -0.024 / -0.030 / -25.2 | -0.294 / +0.194 / +0.036 | PASS | FAIL (replay avg +0.136<+0.191; replay worst day -13.0; 2y avg -0.024<+0.017; 2y w/o best -0.030; 2y worst day -25.2) |
| P-Y3 exit if SPY +0.20% since entry | 200 / +0.146 / +0.068 / -10.0 | +0.046 / +0.382 / +0.030 | 4572 / -0.018 / -0.023 / -19.6 | -0.225 / +0.158 / +0.027 | PASS | FAIL (replay avg +0.146<+0.191; 2y avg -0.018<+0.017; 2y w/o best -0.023; 2y worst day -19.6) |
| P-Z1 exit if SPY +0.30% & under water | 201 / +0.168 / +0.095 / -10.8 | +0.094 / +0.411 / +0.032 | 4614 / -0.025 / -0.030 / -23.3 | -0.269 / +0.180 / +0.026 | PASS | FAIL (replay avg +0.168<+0.191; 2y avg -0.025<+0.017; 2y w/o best -0.030; 2y worst day -23.3) |
| P-T1 U15: entries end 12:00 | 170 / +0.140 / +0.043 / -12.5 | -0.292 / +0.425 / +0.048 | 3827 / -0.021 / -0.028 / -25.3 | -0.359 / +0.197 / +0.003 | PASS | FAIL (replay avg +0.140<+0.191; replay w/o best +0.043; replay worst day -12.5; 2y avg -0.021<+0.017; 2y w/o best -0.028; 2y worst day -25.3) |
| P-L3 L3-WB5 recipe (Y1 + U15 end 12:00) | 171 / +0.157 / +0.064 / -10.3 | -0.148 / +0.411 / +0.052 | 3823 / -0.014 / -0.021 / -23.6 | -0.292 / +0.177 / -0.002 | PASS | FAIL (replay avg +0.157<+0.191; 2y avg -0.014<+0.017; 2y w/o best -0.021; 2y worst day -23.6) |
| P-X1 U15: max hold 60 | 195 / +0.134 / +0.051 / -12.5 | +0.104 / +0.425 / -0.061 | 4689 / -0.023 / -0.029 / -25.3 | -0.209 / +0.176 / -0.010 | PASS | FAIL (replay avg +0.134<+0.191; replay w/o best +0.051; replay worst day -12.5; 2y avg -0.023<+0.017; 2y w/o best -0.029; 2y worst day -25.3) |
| P-G3 skip SPY last-30m>+0.20% | 156 / +0.018 / -0.042 / -12.5 | -0.032 / +0.227 / -0.049 | 3911 / -0.019 / -0.026 / -16.6 | -0.288 / +0.193 / +0.034 | FAIL (replay avg +0.018<+0.117; replay w/o best -0.042) | FAIL (replay avg +0.018<+0.191; replay w/o best -0.042; replay worst day -12.5; 2y avg -0.019<+0.017; 2y w/o best -0.026) |
| W-Y1 WB3 + exit if SPY +0.30% since entry | 100 / +0.177 / +0.054 / -9.0 | +0.441 / +0.511 / -0.234 | 2422 / +0.023 / +0.014 / -14.9 | -0.178 / +0.162 / -0.027 | PASS | FAIL (replay avg +0.177<+0.191) |
| W-Y2 WB3 + exit if SPY +0.50% since entry | 100 / +0.187 / +0.066 / -10.7 | +0.559 / +0.531 / -0.256 | 2435 / +0.021 / +0.012 / -15.8 | -0.225 / +0.179 / -0.029 | PASS | PASS |
| W-Y3 WB3 + exit if SPY +0.20% since entry | 100 / +0.155 / +0.026 / -8.7 | +0.321 / +0.496 / -0.246 | 2412 / +0.026 / +0.017 / -10.9 | -0.138 / +0.157 / -0.031 | PASS | FAIL (replay avg +0.155<+0.191; replay w/o best +0.026) |
| W-Z1 WB3 + exit if SPY +0.30% & under water | 100 / +0.182 / +0.060 / -9.3 | +0.559 / +0.511 / -0.245 | 2421 / +0.024 / +0.015 / -14.1 | -0.181 / +0.165 / -0.025 | PASS | PASS |
| W-T1 WB3 + R10: entries end 12:00 | 73 / +0.026 / -0.059 / -10.3 | +0.559 / +0.380 / -0.254 | 1954 / +0.030 / +0.019 / -10.9 | -0.214 / +0.192 / -0.007 | FAIL (replay avg +0.026<+0.117; replay w/o best -0.059) | FAIL (replay avg +0.026<+0.191; replay w/o best -0.059) |
| W-L3 WB3 + Y1 + R10 end 12:00 | 73 / +0.026 / -0.060 / -8.5 | +0.441 / +0.380 / -0.233 | 1944 / +0.034 / +0.023 / -8.0 | -0.146 / +0.162 / -0.001 | FAIL (replay avg +0.026<+0.117; replay w/o best -0.060) | FAIL (replay avg +0.026<+0.191; replay w/o best -0.060) |
| W-X1 WB3 + R10: max hold 60 | 100 / +0.162 / +0.062 / -8.7 | +0.559 / +0.484 / -0.262 | 2450 / +0.018 / +0.009 / -13.3 | -0.186 / +0.154 / -0.028 | PASS | FAIL (replay avg +0.162<+0.191) |
| W-G3 WB3 + skip SPY last-30m>+0.20% | 76 / +0.081 / -0.024 / -10.3 | +0.559 / +0.478 / -0.257 | 2143 / +0.027 / +0.017 / -14.0 | -0.242 / +0.176 / +0.002 | FAIL (replay avg +0.081<+0.117; replay w/o best -0.024) | FAIL (replay avg +0.081<+0.191; replay w/o best -0.024) |
| W-Y4 WB3 + exit if SPY +0.40% since entry | 100 / +0.201 / +0.083 / -9.8 | +0.559 / +0.531 / -0.225 | 2439 / +0.023 / +0.014 / -15.8 | -0.207 / +0.177 / -0.029 | PASS | PASS |
| W-Y5 WB3 + exit if SPY +0.35% since entry | 100 / +0.189 / +0.069 / -9.7 | +0.559 / +0.531 / -0.250 | 2433 / +0.023 / +0.014 / -15.5 | -0.197 / +0.170 / -0.028 | PASS | PASS |
| W-Z2 WB3 + exit if SPY +0.40% & under water | 100 / +0.202 / +0.086 / -9.6 | +0.559 / +0.531 / -0.220 | 2438 / +0.023 / +0.015 / -15.8 | -0.214 / +0.178 / -0.025 | PASS | PASS |
| SW1 WB3 gate swapped for WB5 recipe (Y1 + U15 end 12:00) | 119 / +0.153 / +0.048 / -9.0 | -0.045 / +0.511 / -0.102 | 2861 / +0.008 / +0.001 / -14.9 | -0.245 / +0.187 / +0.004 | PASS | FAIL (replay avg +0.153<+0.191; replay w/o best +0.048) |
| SW2 SW1 with SPY exit +0.40% | 119 / +0.165 / +0.063 / -9.8 | -0.038 / +0.531 / -0.095 | 2871 / +0.010 / +0.002 / -15.8 | -0.272 / +0.202 / +0.009 | PASS | FAIL (replay avg +0.165<+0.191) |
| SW4 WB3 gate swapped for under-water exit +0.30% + U15 end 12:00 | 119 / +0.152 / +0.047 / -9.3 | -0.023 / +0.511 / -0.111 | 2860 / +0.008 / +0.000 / -14.1 | -0.256 / +0.190 / +0.007 | PASS | FAIL (replay avg +0.152<+0.191; replay w/o best +0.047) |

Method: the RW5 Workbench bench reused unchanged (`research/workbench/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD/code/sim2.py`,
`load.py`, L3 `sim.py` book; parent 205 / +0.117, 4,633 / −0.031 and WB3 100 / +0.191, 2,435 / +0.017 reproduced exactly; the
2-year 1-min path file was rebuilt with the same `paths2y.py`) wrapped by the UPDAY layers (`code/uplayer.py`). LR8 costs, locked
block 2024-11-01..2025-02-28 never read, E90 borrow proxy, ADV ≥ $95M, Primary's book (≤ 30 lots, ≤ 3 per symbol, −2R latch).
SPY 1-min = previous cache + read-only SIP GET to 11-16. Rule changes inside the replay window: as in the first RW5 RESULTS (10-15
promotion, 10-20 twin rule, 10-21 promotion = move, 10-28 Primary cap 30, 10-29 −2R latch, 10-30 Testing CF, 11-11 TEAM-6, 11-12
LR1/3/5/7/8); the replay applies today's rules to every session.
