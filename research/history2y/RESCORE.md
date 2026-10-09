# Re-score on the 2-year history (rule 19)

*Educational only - not financial advice. Lab and backtest results only; nothing here is a live result.*

**Setups scored: 23** of 31 listed (not scored: 8, the 8 BDI video modules, whose structural exit and extra 1-minute features LabStrategy cannot run). Each setup is a fixed rule: nothing was fitted on this history, so the configurations tried on it are the 23 setups themselves; the lineages' own search sizes set each t bar.

Verdicts: keep 0, rework 14, retire 9, not scored 8.

## Data and method
- History: 2024-10-01 .. 2026-10-07, 426 sessions outside the locked block, 1,226 lab symbols (today's list: survivorship bias - names delisted or no longer liquid are missing). The rule-19 locked block 2024-11-01..2025-02-28 is excluded.
- Lab setups: module mask on the setups2-pipeline frames, the YAML window, point-in-time 20-day ADV >= the setup's min_adv, first qualifying bar per symbol-day, R = 0.25 x daily ATR, exit by 15:55, production costs (1c + 1 bps per side, the exit side free on target fills, +2c on stops).
- orb20_a and intraday_momentum: the production backtester (as research/setup_screen.py), entries from 09:50.
- Regimes: universe median open-to-close per session, terciles over the open history: down <= -0.226%, up >= 0.212% (142 up / 142 flat / 142 down sessions).
- Gates (mcf/research/gates.py): exp > 0; day-clustered t >= max(1.5, sqrt(2 ln N)) with N = configurations tried in the lineage; exp > 0 in up AND down sessions (n >= 30 each); walk-forward (3-month train, 1-month test, step 1) positive share >= 0.6 over folds with n >= 10.
- 'Unseen' = sessions before 2026-03-10 (outside the locked block): data no MCF study had loaded before rule 19. Sessions from 2026-03-10 on include every lineage's train/valid and the two old holdouts, so they are in-sample for these setups.

## Results (failures included)

| Setup | Group | Side/geom | n | /day | win | exp R | t | t req | up exp (n) | flat exp | down exp (n) | WF +share | unseen exp (n, t) | Verdict | Failed gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RW1 bdi-rw-gapdn-bounce-flowsell | backlog RW (lab_module) | short/t1s1 | 2489 | 6.38 | 0.5259 | -0.007 | -0.22 | 4.757 | -0.258 (994) | +0.066 | +0.257 (733) | 0.529 | -0.069 (1435, -1.77) | **rework** | exp<=0; t -0.22 < 4.757; regime (up and down must both be > 0); walk-forward share 0.529 < 0.6 |
| RW3 bdi-rw-gapdn-rsi5pop-flowsell | backlog RW (lab_module) | short/t1s1 | 1816 | 5.09 | 0.5039 | -0.041 | -1.22 | 4.757 | -0.294 (765) | +0.108 | +0.192 (436) | 0.353 | -0.113 (1161, -2.82) | **rework** | exp<=0; t -1.22 < 4.757; regime (up and down must both be > 0); walk-forward share 0.353 < 0.6 |
| RW4 bdi-rw-ns3-adv150 | backlog RW (lab_module) | short/t1s1 | 1216 | 4.22 | 0.5502 | +0.054 | 1.13 | 4.756 | -0.107 (285) | -0.024 | +0.239 (451) | 0.5 | +0.090 (566, 1.37) | **rework** | t 1.13 < 4.756; regime (up and down must both be > 0); walk-forward share 0.5 < 0.6 |
| RW5 bdi-rw-heat30-flowsell-rsi5pop-gapdn | backlog RW (lab_module) | short/t1s1 | 1294 | 4.01 | 0.5278 | -0.013 | -0.32 | 4.757 | -0.262 (595) | +0.157 | +0.269 (261) | 0.588 | -0.076 (861, -1.42) | **rework** | exp<=0; t -0.32 < 4.757; regime (up and down must both be > 0); walk-forward share 0.588 < 0.6 |
| RW6 bdi-rw-ns2-up3 | backlog RW (lab_module) | short/t1s1 | 1461 | 5.58 | 0.5428 | +0.057 | 0.77 | 4.756 | +0.028 (897) | +0.045 | +0.156 (292) | 0.471 | +0.040 (974, 0.38) | **rework** | t 0.77 < 4.756; walk-forward share 0.471 < 0.6 |
| RW7 bdi-rw-gapdn-bounce-early | backlog RW (lab_module) | short/t1s1 | 1590 | 4.56 | 0.5132 | -0.029 | -0.94 | 4.757 | -0.252 (677) | +0.066 | +0.230 (390) | 0.412 | -0.073 (1091, -1.96) | **rework** | exp<=0; t -0.94 < 4.757; regime (up and down must both be > 0); walk-forward share 0.412 < 0.6 |
| heat_fade_long | live original | long/t1s1 | 14460 | 33.94 | 0.4924 | -0.046 | -1.16 | 4.441 | +0.076 (2717) | +0.035 | -0.149 (6958) | 0.412 | -0.068 (8518, -1.16) | **rework** | exp<=0; t -1.16 < 4.441; regime (up and down must both be > 0); walk-forward share 0.412 < 0.6 |
| heat_fade_short | live original | short/t1s1 | 14433 | 33.96 | 0.5226 | +0.017 | 0.68 | 4.441 | -0.199 (4544) | +0.082 | +0.154 (4702) | 0.706 | -0.002 (7742, -0.05) | **rework** | t 0.68 < 4.441; regime (up and down must both be > 0) |
| MF3-open-flowsell-rsi5hi | live probation | short/t1s1 | 4136 | 9.87 | 0.5017 | -0.074 | -2.5 | 4.24 | -0.290 (1723) | +0.031 | +0.148 (1011) | 0.353 | -0.122 (2694, -3.31) | **rework** | exp<=0; t -2.5 < 4.24; regime (up and down must both be > 0); walk-forward share 0.353 < 0.6 |
| MF5-flowsell-vwapup-rsi5hi | live probation | short/t1s1 | 6827 | 16.06 | 0.4986 | -0.052 | -2.39 | 4.24 | -0.278 (2743) | +0.054 | +0.163 (1737) | 0.353 | -0.095 (4520, -3.5) | **rework** | exp<=0; t -2.39 < 4.24; regime (up and down must both be > 0); walk-forward share 0.353 < 0.6 |
| NS1-rsidip-rsi5pop-long | live probation | long/t05s1 | 444 | 2.11 | 0.7027 | +0.034 | 0.87 | 4.22 | +0.097 (194) | -0.018 | -0.009 (115) | 0.5 | -0.014 (217, -0.24) | **rework** | t 0.87 < 4.22; regime (up and down must both be > 0); walk-forward share 0.5 < 0.6 |
| NS2-sma50break-overbought-short | live probation | short/t1s1 | 3124 | 8.49 | 0.5202 | +0.006 | 0.11 | 4.22 | -0.057 (1789) | +0.027 | +0.160 (653) | 0.353 | -0.021 (1953, -0.23) | **rework** | t 0.11 < 4.22; regime (up and down must both be > 0); walk-forward share 0.353 < 0.6 |
| NS3-failed-vwap-reclaim-short | live probation | short/t1s1 | 1510 | 4.76 | 0.551 | +0.056 | 1.26 | 4.22 | -0.089 (360) | -0.029 | +0.242 (554) | 0.706 | +0.096 (715, 1.59) | **rework** | t 1.26 < 4.22; regime (up and down must both be > 0) |
| NS4-pm-vwap-reclaim-oversold-short | live probation | short/t1s05 | 1469 | 4.2 | 0.3901 | -0.065 | -2.03 | 4.22 | -0.175 (709) | -0.021 | +0.126 (309) | 0.353 | -0.113 (828, -2.48) | **rework** | exp<=0; t -2.03 < 4.22; regime (up and down must both be > 0); walk-forward share 0.353 < 0.6 |
| RW2 bdi-rw-exhaustion-noon-adv150 | backlog RW (lab_module) | short/t1s1 | 7797 | 18.3 | 0.5144 | -0.009 | -0.35 | 5.244 | -0.078 (3565) | +0.002 | +0.105 (1958) | 0.235 | -0.046 (4680, -1.52) | **retire** | exp<=0; t -0.35 < 5.244; regime (up and down must both be > 0); walk-forward share 0.235 < 0.6 |
| RW8 bdi-rw-sma50up-spikefade | backlog RW (lab_module) | short/t1s1 | 459 | 2.15 | 0.4793 | -0.090 | -1.4 | 4.756 | -0.235 (225) | +0.100 | -0.015 (101) | 0.562 | -0.120 (240, -1.22) | **retire** | exp<=0; t -1.4 < 4.756; regime (up and down must both be > 0); walk-forward share 0.562 < 0.6 |
| exhaustion_short | live original | short/t1s1 | 5973 | 14.36 | 0.5146 | -0.010 | -0.32 | 5.227 | -0.075 (2678) | -0.025 | +0.111 (1626) | 0.294 | -0.058 (3618, -1.79) | **retire** | exp<=0; t -0.32 < 5.227; regime (up and down must both be > 0); walk-forward share 0.294 < 0.6 |
| intraday_momentum | live original | both/bt | 1151 | 2.91 | 0.4448 | -0.067 | -2.7 | 2.327 | -0.068 (401) | -0.022 | -0.111 (373) | 0.294 | -0.092 (740, -2.79) | **retire** | exp<=0; t -2.7 < 2.327; regime (up and down must both be > 0); walk-forward share 0.294 < 0.6 |
| orb20_a | live original | both/bt | 2827 | 6.68 | 0.4535 | -0.000 | -0.0 | 2.327 | +0.051 (956) | -0.039 | -0.013 (950) | 0.529 | +0.018 (1767, 0.7) | **retire** | exp<=0; t 0.0 < 2.327; regime (up and down must both be > 0); walk-forward share 0.529 < 0.6 |
| MF1-945-flowsell-vwapup | live probation | short/t1s05 | 2389 | 6.16 | 0.3784 | -0.058 | -2.1 | 4.24 | -0.228 (924) | +0.035 | +0.068 (621) | 0.235 | -0.117 (1518, -3.47) | **retire** | exp<=0; t -2.1 < 4.24; regime (up and down must both be > 0); walk-forward share 0.235 < 0.6 |
| MF2-open-rsimidhi-flowsell | live probation | short/t1s05 | 610 | 2.52 | 0.3639 | -0.030 | -0.83 | 4.24 | -0.100 (200) | +0.018 | -0.009 (221) | 0.375 | -0.106 (290, -2.1) | **retire** | exp<=0; t -0.83 < 4.24; regime (up and down must both be > 0); walk-forward share 0.375 < 0.6 |
| MF4-h40-open-flowsell | live probation | short/t05s1 | 3318 | 8.0 | 0.6401 | -0.089 | -3.02 | 4.24 | -0.245 (1266) | -0.012 | +0.030 (981) | 0.294 | -0.151 (1993, -3.63) | **retire** | exp<=0; t -3.02 < 4.24; regime (up and down must both be > 0); walk-forward share 0.294 < 0.6 |
| NS5-sma50-flush-oversold-long | live probation | long/t1s1 | 1305 | 4.44 | 0.5011 | -0.038 | -0.47 | 4.22 | +0.101 (204) | +0.134 | -0.201 (652) | 0.529 | -0.122 (791, -1.02) | **retire** | exp<=0; t -0.47 < 4.22; regime (up and down must both be > 0); walk-forward share 0.529 < 0.6 |
| VID1 | BDI video | short/tx | – | – | – | – | – | – | – | – | – | – | – | not scored | structural exit (GEOM None) and extra 1-minute features: LabStrategy cannot run it |
| VID2 | BDI video | short/tx | – | – | – | – | – | – | – | – | – | – | – | not scored | structural exit (GEOM None) and extra 1-minute features: LabStrategy cannot run it |
| VID3 | BDI video | short/tx | – | – | – | – | – | – | – | – | – | – | – | not scored | structural exit (GEOM None) and extra 1-minute features: LabStrategy cannot run it |
| VID4 | BDI video | short/tx | – | – | – | – | – | – | – | – | – | – | – | not scored | structural exit (GEOM None) and extra 1-minute features: LabStrategy cannot run it |
| VID5 | BDI video | short/tx | – | – | – | – | – | – | – | – | – | – | – | not scored | structural exit (GEOM None) and extra 1-minute features: LabStrategy cannot run it |
| VID6 | BDI video | short/tx | – | – | – | – | – | – | – | – | – | – | – | not scored | structural exit (GEOM None) and extra 1-minute features: LabStrategy cannot run it |
| VID7 | BDI video | short/tx | – | – | – | – | – | – | – | – | – | – | – | not scored | structural exit (GEOM None) and extra 1-minute features: LabStrategy cannot run it |
| VID8 | BDI video | short/tx | – | – | – | – | – | – | – | – | – | – | – | not scored | structural exit (GEOM None) and extra 1-minute features: LabStrategy cannot run it |

## How to read this
- A 'rework' verdict that comes from the regime rescue (one of up / down positive with t >= 2) does NOT mean the setup works: the session regime is only known at the close. A rework must find a real-time proxy known at entry (e.g. the index's move from the open, or a prior-day trend) and is a new lineage step whose configurations are counted.
- Most short setups lose in up sessions and win in down sessions: the train/valid/test edge of 2026-06..10 was largely the down-drift regime, as diagnosed on 2026-10-08.
- t bars are high because the lineages searched 7k-935k configurations; sqrt(2 ln N) is what the best of N noise configurations reaches by luck.
- Survivorship: today's 1,226 names applied to 2024-2025. Point-in-time ADV is applied, but names that dropped out of the market are missing.

## Per-quarter expectancy (R after costs)

| Setup | 2024Q4 | 2025Q1 | 2025Q2 | 2025Q3 | 2025Q4 | 2026Q1 | 2026Q2 | 2026Q3 | 2026Q4 |
|---|---|---|---|---|---|---|---|---|---|
| MF1-945-flowsell-vwapup | -0.134 (97) | -0.189 (97) | -0.111 (328) | -0.136 (413) | -0.101 (411) | +0.007 (290) | -0.039 (330) | +0.101 (394) | -0.077 (29) |
| MF2-open-rsimidhi-flowsell | -0.038 (8) | -0.043 (37) | -0.165 (49) | -0.225 (43) | -0.011 (96) | -0.139 (104) | +0.069 (126) | +0.068 (135) | -0.094 (12) |
| MF3-open-flowsell-rsi5hi | -0.179 (150) | -0.016 (188) | -0.127 (548) | -0.126 (688) | -0.102 (808) | -0.085 (502) | -0.014 (568) | +0.027 (634) | -0.091 (50) |
| MF4-h40-open-flowsell | -0.165 (77) | -0.161 (164) | -0.245 (459) | -0.174 (351) | -0.025 (624) | -0.180 (454) | +0.030 (541) | +0.011 (605) | -0.156 (43) |
| MF5-flowsell-vwapup-rsi5hi | -0.093 (285) | -0.109 (320) | -0.078 (980) | -0.115 (1144) | -0.070 (1198) | -0.035 (862) | -0.001 (917) | +0.028 (1027) | +0.014 (94) |
| NS1-rsidip-rsi5pop-long | -0.061 (8) | -0.161 (12) | +0.055 (53) | +0.063 (35) | -0.050 (59) | -0.137 (84) | +0.041 (96) | +0.230 (94) | +0.473 (3) |
| NS2-sma50break-overbought-short | +0.112 (60) | +0.264 (100) | +0.144 (786) | -0.256 (169) | -0.132 (356) | -0.165 (684) | +0.027 (458) | +0.131 (484) | +0.030 (27) |
| NS3-failed-vwap-reclaim-short | +0.118 (19) | +0.103 (43) | +0.116 (232) | -0.072 (119) | +0.133 (160) | +0.152 (194) | -0.119 (429) | +0.185 (304) | +0.433 (10) |
| NS4-pm-vwap-reclaim-oversold-short | -0.057 (26) | +0.118 (46) | -0.222 (233) | -0.153 (152) | -0.029 (172) | -0.064 (263) | -0.090 (272) | +0.090 (292) | -0.336 (13) |
| NS5-sma50-flush-oversold-long | -0.001 (17) | +0.363 (56) | -0.339 (283) | +0.073 (121) | -0.249 (188) | +0.155 (211) | -0.003 (190) | +0.205 (213) | -0.478 (26) |
| RW1 bdi-rw-gapdn-bounce-flowsell | -0.116 (115) | -0.068 (141) | -0.208 (254) | -0.127 (285) | +0.037 (448) | -0.034 (316) | +0.018 (467) | +0.209 (432) | -0.328 (31) |
| RW2 bdi-rw-exhaustion-noon-adv150 | -0.147 (103) | -0.234 (532) | +0.115 (1175) | -0.108 (687) | -0.061 (1112) | -0.047 (1303) | -0.043 (1600) | +0.178 (1204) | -0.081 (81) |
| RW3 bdi-rw-gapdn-rsi5pop-flowsell | +0.031 (92) | +0.069 (112) | -0.159 (178) | -0.155 (256) | -0.079 (374) | -0.151 (252) | -0.071 (246) | +0.230 (283) | +0.127 (23) |
| RW4 bdi-rw-ns3-adv150 | +0.038 (15) | +0.104 (33) | +0.123 (184) | -0.105 (95) | +0.069 (127) | +0.229 (156) | -0.129 (360) | +0.202 (240) | +0.440 (6) |
| RW5 bdi-rw-heat30-flowsell-rsi5pop-gapdn | -0.133 (59) | +0.237 (90) | -0.077 (134) | +0.004 (188) | -0.070 (258) | -0.224 (203) | +0.051 (166) | +0.194 (174) | +0.014 (22) |
| RW6 bdi-rw-ns2-up3 | +0.286 (23) | +0.307 (48) | +0.166 (463) | -0.199 (70) | -0.064 (161) | -0.170 (271) | +0.105 (192) | +0.140 (221) | +0.301 (12) |
| RW7 bdi-rw-gapdn-bounce-early | -0.006 (99) | -0.094 (63) | -0.113 (180) | -0.050 (284) | -0.050 (338) | -0.013 (188) | -0.014 (209) | +0.145 (211) | -0.776 (18) |
| RW8 bdi-rw-sma50up-spikefade | +0.036 (10) | +0.152 (8) | -0.406 (69) | -0.020 (45) | +0.174 (60) | -0.269 (70) | -0.224 (80) | +0.111 (114) | -0.014 (3) |
| exhaustion_short | -0.203 (73) | -0.218 (571) | +0.063 (887) | -0.087 (495) | -0.033 (843) | -0.054 (930) | -0.067 (1218) | +0.259 (873) | -0.016 (83) |
| heat_fade_long | +0.159 (191) | -0.099 (593) | -0.085 (2019) | +0.020 (1430) | -0.109 (2491) | -0.036 (2633) | -0.095 (2570) | +0.038 (2347) | +0.166 (186) |
| heat_fade_short | +0.158 (391) | +0.083 (466) | -0.072 (2564) | +0.028 (1249) | +0.039 (1693) | +0.008 (1995) | -0.015 (3313) | +0.097 (2594) | +0.061 (168) |
| intraday_momentum | -0.071 (57) | -0.069 (62) | -0.129 (198) | -0.044 (135) | -0.076 (165) | -0.070 (179) | -0.083 (163) | +0.011 (177) | -0.054 (15) |
| orb20_a | +0.022 (77) | +0.113 (145) | -0.018 (427) | +0.013 (397) | +0.069 (406) | -0.061 (454) | -0.044 (426) | +0.017 (452) | -0.123 (43) |

Files: `research/history2y/rescore.csv` (all columns incl. deflated Sharpe and the trailing-on walk-forward variant), trades in `research/history2y/data/` (git-ignored).
