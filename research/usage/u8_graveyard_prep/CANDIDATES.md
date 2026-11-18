Educational only — not financial advice

# U8 — Graveyard revival candidates (for tonight's Graveyard deep dive)

Source: research/usage/u8_graveyard_prep (PLAN.md pre-registered; RESULTS.md; u8_ranking.csv; u8_tunes.csv). Live journals
run_id 1, 10-06..11-17, after-cost R, identical signals across accounts counted once. 1,100 configurations tried; bar 3.74.
Nothing here deletes, switches or moves anything (rule 20); every line below is input for the deep dive, and anything it
wants to act on is a proposal for the owner (promotion hold stays on).

**Rule changes inside the window:** Graveyard -2R per-setup latch since 10-21 (home accounts latch-free 10-22/23..10-29);
10-27 slot cut; 11-12 LR8 and REPV-11/12 (300 smaller Graveyard slots); 11-13 RW6 → Testing C, ST4 → Testing B; 11-16
RW3S in; 11-18 GY-BENCH (18 residents rest 11-18..11-24, 20 guests in). Records straddle these.

## Bottom line for the deep dive

- **No revival tune passed** (0 PASS / 0 LEAD of 10). No Testing-copy proposal, no decision code from U8.
- **No resident is positive w/o its best day over its whole record.** Revival on present evidence = more Graveyard reps,
  not a tune.
- One resident to watch for a transfer case: **RW6G1** (below). Two families with a pending outside test: MF (C3-WB5 #3),
  NS3 (C3-WB5 #2). Everything else: no revival path found.

## Tiers

| Tier | Setup | Why | Suggested handling (deep dive decides) |
|---|---|---|---|
| A — raw revival watch | RW6G1-ns2-up3-vwap2sd-short-FD | CHECK 39 trades +0.229R, w/o best day +0.234R, best day 45%; Graveyard 36 trades +0.179R; FIT -0.277R; whole record 66 trades +1.5R, -0.053R w/o best day; overextension-from-VWAP short (mechanism 2); rho with Primary 0.26. The FIT-chosen tune (X1+T3) cut CHECK R by 5.4R (t -2.78) | Keep untouched in the Graveyard and let it collect reps; transfer review once its whole record is positive w/o best day with best day < 50% and >= 15 active days. Twin of RW6 (now in Testing C): never the same account |
| A (already out) | RW6-ns2-up3-short-FD, ST4-emadn-long-am-t1s05-FD | Left for Testing C / Testing B on 11-13. RW6: Graveyard 144 trades +0.268R but +0.008 w/o best day (CHECK best day 87%) — one-day record; its tune FAILED (-39.1R) | Nothing for the Graveyard; RW6's one-day record should be called out wherever it is reviewed |
| B — family test pending | MF1-945-flowsell-vwapup-FD, MF3-open-flowsell-rsi5hi-FD | FIT gates (MF1 K2 stock gap < 0; MF3 T3 >= 11:30 + V2 below VWAP) lifted CHECK avg R +0.41R / +0.15R, 92nd random percentile, but tuned CHECK records are one-day (w/o best day -0.068 / -0.113) and t 1.66 / 0.70 < 3.74 | Wait for C3-WB5 item 3 (MF2-FD / MF4-FD with NM-MF3's gate). If that passes, the same gate on MF1/MF3 is the natural single-change revival test (pre-register then; fresh sessions only) |
| B — family test pending | NS3-failed-vwap-reclaim-short-FD (and RW4-ns3-adv150-short-FD, same mechanism) | Clear mechanism; FIT tunes did not carry (NS3 w/o best day -0.326R worse on CHECK; RW4 flat) | C3-WB5 item 2 (NS3 09:50-10:30 + SPY/QQQ up) is the one revival test for the family; no second copy |
| C — gap mechanism, not yet scorable | RW3S-gapdn-flowsell-short-FD | No FIT sessions (first trade 11-03); 352 trades -0.216R, -0.259R w/o best day; Graveyard-only 55 trades +0.178R (+0.022 w/o best day); rho 0.30 and a sibling of Primary's RW3 | Re-score after 15 Graveyard active days; a revival would duplicate RW3 exposure in Primary's book |
| D — no revival path found | CWT09-gapdn-bounce-g5-lowerhalf-short, CWT13-vwapstretch-z05-short, LIQ-orl-sweep-open15-s25-long, heat_fade_long | Tunes FAILED on CHECK; LIQ's day-type gate picked the worst trades (0.6th random percentile); CWT09-bounce and heat_fade_long gains are one-day | Stay as they are; the deep dive's lifecycle rule decides |
| D — not tuned (lower rank) | MF5, heat_fade_short(-FD), heat_fade_long-FD, NS5-FD, CWT09-vwaploss-g5, ST1-FD, ST2-FD, RW2-FD, NS2 (both) | Negative w/o best day in every period scored; FIT diagnosis found no <= 2-change fix with a positive w/o-best-day FIT record | Same |
| E — closed by guardrail | 11 CWT12 / CWT14 residents | 8,973 trades, -1,211.5R; negative w/o best day in every period (whole, FIT, CHECK, Graveyard); new variants closed (Part 3) | No revival work. Retirement, if any, is the owner's decision (rule 20) |

## Full ranking (score per PLAN.md; CWT12/14 listed last regardless of score)

| Rank | Setup | n | avg R | w/o best day | FIT w/o best | CHECK w/o best | Graveyard n, avg / w/o best | Positive periods | Mech | rho vs Primary | FIT best tune (avg / w/o best) | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | RW6G1-ns2-up3-vwap2sd-short-FD | 66 | +0.022 | -0.053 | -0.317 | +0.234 | 36, +0.179 / +0.133 | CHECK+GY | 2 | +0.256 | X1+T3 (-0.104 / -0.156) | 6 |
| 2 | NS3-failed-vwap-reclaim-short-FD | 258 | -0.145 | -0.191 | -0.270 | -0.242 | 146, -0.143 / -0.242 | — | 2 | +0.198 | G2+V1 (+0.118 / +0.022) | 5 |
| 3 | RW6-ns2-up3-short-FD | 196 | +0.075 | -0.195 | -0.481 | +0.112 | 144, +0.268 / +0.008 | CHECK+GY | 2 | +0.446 | T3+G2 (-0.121 / -0.157) | 5 |
| 4 | CWT09-gapdn-bounce-g5-lowerhalf-short | 188 | -0.141 | -0.205 | -0.431 | -0.138 | 146, -0.009 / -0.091 | — | 2 | -0.016 | S2+G2 (+0.269 / +0.185) | 5 |
| 5 | RW4-ns3-adv150-short-FD | 205 | -0.181 | -0.223 | -0.354 | -0.208 | 101, -0.114 / -0.208 | — | 2 | -0.023 | S1+X1 (+0.060 / +0.041) | 5 |
| 6 | CWT13-vwapstretch-z05-short | 203 | -0.146 | -0.183 | -0.228 | -0.213 | 142, -0.036 / -0.080 | — | 1 | +0.015 | X1+G1 (+0.102 / +0.025) | 4 |
| 7 | RW3S-gapdn-flowsell-short-FD | 352 | -0.216 | -0.259 |  | -0.259 | 55, +0.178 / +0.022 | GY | 2 | +0.302 | — | 3.5 |
| 8 | MF3-open-flowsell-rsi5hi-FD | 291 | -0.146 | -0.187 | -0.250 | -0.165 | 148, -0.062 / -0.137 | — | 1 | +0.325 | T3+V2 (+0.234 / +0.141) | 3 |
| 9 | LIQ-orl-sweep-open15-s25-long | 393 | -0.174 | -0.226 | -0.252 | -0.370 | 248, -0.214 / -0.304 | — | 2 | -0.528 | S1+G2 (+0.197 / +0.093) | 3 |
| 10 | heat_fade_long | 263 | -0.160 | -0.230 | -0.288 | -0.165 | 125, +0.046 / -0.060 | — | 1 | +0.030 | C1+S1 (-0.041 / -0.105) | 3 |
| 11 | MF1-945-flowsell-vwapup-FD | 147 | -0.187 | -0.250 | -0.184 | -0.426 | 107, -0.128 / -0.213 | — | 1 | +0.295 | K2 (+0.364 / +0.202) | 3 |
| 12 | heat_fade_short | 395 | -0.206 | -0.290 | -0.343 | -0.271 | 254, -0.189 / -0.324 | — | 1 | +0.176 | M1+X1 (-0.101 / -0.201) | 3 |
| 13 | NS5-sma50-flush-oversold-long-FD | 80 | -0.311 | -0.389 | -0.388 | -0.501 | 34, -0.220 / -0.408 | — | 1 | +0.165 | X3+C1 (-0.161 / -0.251) | 3 |
| 14 | heat_fade_long-FD | 315 | -0.369 | -0.412 | -0.386 | -0.519 | 165, -0.349 / -0.397 | — | 1 | +0.056 | X1+S2 (-0.114 / -0.143) | 3 |
| 15 | CWT09-gapdn-vwaploss-g5-short | 172 | -0.366 | -0.617 | -0.577 | -0.664 | 139, -0.287 / -0.594 | — | 2 | -0.263 | X3+M2 (-0.324 / -0.445) | 3 |
| 16 | ST2-slope20up-long-am-t05s1-FD | 348 | -0.103 | -0.166 | -0.158 | -0.226 | 267, -0.067 / -0.145 | — | 0 | -0.168 | G2+C1 (+0.021 / -0.031) | 2 |
| 17 | MF5-flowsell-vwapup-rsi5hi-FD | 171 | -0.190 | -0.242 | -0.361 | -0.206 | 89, -0.097 / -0.190 | — | 1 | +0.347 | T3 (+0.048 / -0.040) | 2 |
| 18 | RW2-exhaustion-noon-adv150-short-FD | 472 | -0.245 | -0.285 | -0.390 | -0.197 | 321, -0.285 / -0.351 | — | 1 | -0.071 | X3 (-0.251 / -0.307) | 2 |
| 19 | NS2-sma50break-overbought-short | 67 | -0.332 | -0.371 | -0.412 |  | 8, +0.416 / +0.249 | — | 1 | +0.369 | X3 (-0.192 / -0.228) | 2 |
| 20 | ST4-emadn-long-am-t1s05-FD | 48 | -0.017 | -0.201 | -0.687 | -0.028 | 23, +0.293 / +0.027 | GY | 0 | -0.411 | — | 1.5 |
| 21 | heat_fade_short-FD | 848 | -0.100 | -0.141 | -0.168 | -0.184 | 496, -0.120 / -0.194 | — | 1 | +0.436 | K2+T3 (+0.043 / -0.015) | 1 |
| 22 | NS2-sma50break-overbought-short-FD | 285 | -0.028 | -0.233 | -0.434 | -0.068 | 216, +0.116 / -0.114 | — | 1 | +0.486 | X3+T3 (-0.209 / -0.274) | 1 |
| 23 | ST1-ordn-long-pm-t05s1-FD | 70 | -0.242 | -0.370 | -0.542 | -0.242 | 46, -0.070 / -0.231 | — | 0 | -0.070 | X3 (-0.407 / -0.450) | 1 |
| 24 | CWT14-failbrk-orl-p10-lowvol-long (CWT12/14 closed) | 816 | -0.086 | -0.113 | -0.125 | -0.122 | 639, -0.061 / -0.093 | — | 1 | -0.116 | G1 (-0.005 / -0.042) | 2 |
| 25 | CWT14-failbrk-orl-p05-long (CWT12/14 closed) | 1390 | -0.104 | -0.130 | -0.141 | -0.149 | 1027, -0.081 / -0.114 | — | 1 | -0.498 | G1+T2 (+0.059 / +0.004) | 2 |
| 26 | CWT14-failbrk-orl-p10-long (CWT12/14 closed) | 811 | -0.125 | -0.147 | -0.147 | -0.174 | 618, -0.102 / -0.131 | — | 1 | -0.101 | G1 (-0.018 / -0.054) | 3 |
| 27 | CWT12-coil-k4-long (CWT12/14 closed) | 972 | -0.135 | -0.153 | -0.121 | -0.217 | 545, -0.169 / -0.205 | — | 1 | -0.262 | X3 (-0.062 / -0.083) | 1 |
| 28 | CWT14-failbrk-pdl-p05-long (CWT12/14 closed) | 1077 | -0.146 | -0.167 | -0.121 | -0.297 | 402, -0.248 / -0.299 | — | 1 | -0.218 | S2+X1 (-0.019 / -0.041) | 1 |
| 29 | CWT14-failbrk-pdh-p05-lowvol-short (CWT12/14 closed) | 649 | -0.152 | -0.168 | -0.189 | -0.161 | 417, -0.141 / -0.166 | — | 1 | +0.118 | K2 (-0.060 / -0.080) | 3 |
| 30 | CWT14-failbrk-pdl-p05-lowvol-long (CWT12/14 closed) | 765 | -0.147 | -0.171 | -0.148 | -0.253 | 332, -0.189 / -0.255 | — | 1 | +0.017 | K1+X3 (+0.040 / -0.003) | 3 |
| 31 | CWT14-failbrk-orl-p05-lowvol-long (CWT12/14 closed) | 1305 | -0.144 | -0.180 | -0.196 | -0.192 | 954, -0.099 / -0.144 | — | 1 | -0.367 | G1 (-0.031 / -0.071) | 2 |
| 32 | CWT14-failbrk-pdh-p10-short (CWT12/14 closed) | 602 | -0.165 | -0.194 | -0.255 | -0.159 | 369, -0.181 / -0.213 | — | 1 | +0.031 | G2+M1 (+0.058 / -0.016) | 3 |
| 33 | CWT14-failbrk-pdh-p10-lowvol-short (CWT12/14 closed) | 315 | -0.183 | -0.208 | -0.168 | -0.299 | 213, -0.177 / -0.200 | — | 1 | +0.064 | K2+T2 (+0.173 / +0.133) | 4 |
| 34 | CWT12-coil-k6-long (CWT12/14 closed) | 271 | -0.181 | -0.259 | -0.338 | -0.264 | 181, -0.136 / -0.251 | — | 1 | -0.348 | K1+X2 (+0.023 / -0.037) | 2 |

Score = 2 if positive w/o best day in any period (>= 10 trades) + 0.5 per such period + mechanism (0-2) + fixability
(2 = FIT best <= 2-change tune positive w/o best day, 1 = lifts FIT avg >= 0.10R) + correlation (+1 |rho| < 0.2, 0 < 0.4,
-1 otherwise or a Primary sibling). The FIT fixability column is in-sample by design; the CHECK verdicts in RESULTS.md
show it did not carry for any of the ten tuned setups.
