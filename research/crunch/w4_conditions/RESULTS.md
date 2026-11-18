# W4-conditions: per-setup conditions map and one bespoke rule each — results

*Educational only — not financial advice.* Research and proposals only (crunch, owner 2026-11-18). No config, setup,
exit, latch or runtime change; nothing merged that affects trading. Plan fixed before scoring: PLAN.md (commit 62ae42d78).

**Configurations tried: 2,176** candidate rules scored on the fit halves (68 per setup x 32 setups that had enough
trades), 31 chosen rules scored once on the check halves. Pre-registered bar t ≥ max(1.5, sqrt(2 ln 2,380)) = **3.94**
(N = 68 x 35 setups); per-setup "lead" bar sqrt(2 ln 68) = **2.90**. Extra checks (not configs): a random-removal
baseline for each chosen rule (2,000 draws), a fit-vs-check stability test of 351 setup x condition effects, and a pooled
view. Locked block 2024-11-01..2025-02-28 not read (no 2-year data used at all).

Data: live run (run_id 1) of all ten `mcf-data*` journals, **10-06..11-17** (11-18 left out: no bar pack yet).
R = pnl_adj / initial risk, after costs. Conditions are point-in-time at the signal from the `bars-2026-10/11` 1-minute
and 1-day release packs (25,918 of 25,921 trades matched; the 1,131 trades of 11-18 are left out). Twin-copy de-duplication (same setup/symbol/day, < 5 min,
other account) removed only 48 trades (MF3 24, RW3 10, RW5 6, NS3 4, NS5 4) — the top-30 counts are effectively raw.

## Failures first
- **0 PASS, 0 LEAD.** The best check t is 1.94 (CWT14-failbrk-orl-p10-long, a closed family); the best t of the
  excess over random removal is 1.63. Nothing comes near 2.90, let alone 3.94.
- **8 of 31 rules made their setup worse on unseen sessions** (-58.2R in total), incl. the protected L3-fromopen
  (-18.2R), NS2 (-15.3R) and GEN-261021-02 (-10.6R). 11 more improved R only by cutting > 30% of trades or > 10% of
  the top-decile winners (e.g. RW2: keep 33%, NS3: 81% of winners kept); 3 had no plateau.
- **Most of the "improvement" is just removing trades from losing setups.** Raw check Δ was positive for 23 of 31
  (+225.4R improve / -58.2R worse, net +167.1R), but removing the same number of *random* trades would have given
  +135.3R. The excess is **+31.8R over 31 setups** (17 beat random, 14 did not; 5 at the 95th percentile, ~1.5 expected
  by chance). Fit gain was +550.5R: only ~6% of the fit-half gain is real excess on unseen sessions.
- **Condition effects mostly do not persist at this sample size.** Across 351 setup x condition high-vs-low tercile
  spreads, the fit and check halves agree in sign 56% of the time (50% = coin), correlation 0.21; the top-quartile fit
  effects shrink to 0.23x in the check half. Persistence by condition: tod 0.49, gap 0.44, open 0.39, atr_pct 0.36,
  withday 0.35, pday 0.26, or30 0.13, price 0.07, spy10 -0.06, vwap -0.06, adv -0.20 (stability.csv).
  → With 5-14 sessions per half, a live per-setup condition filter is ~4/5 noise. SPY-at-10:00 and VWAP-distance
  filters, the most popular gates in the arena, have **zero** setup-level persistence here.

## Rule changes inside the window (research/ledger.jsonl)
10-20 twin-symbol block; 10-22/23 per-setup latch off in Testing 1/2; 10-27 slots 160 → 77; 10-28 Primary sizing
~$4k; 10-29 Primary -2R per-setup latch and BAR90; 10-30 L3 re-promoted to Primary; 11-05 Explore 1 / Live Lab (ROLL1);
11-09..11-10 EXPO1109 temporary moves; 11-11 TEAM-6; 11-12 LR1-LR8 (after-cost R, live cost model), Testing D/E/F,
halts 300R, Gen/Graveyard sizing, GEN-GRAD, On Deck build; 11-13 RW6/ST4 to arena; 11-16 ROT1 rotation, RW3S → Graveyard,
RW7 → Testing F; 11-17 TSZ1 half-size testing lots, 15 WB copies, SPYEXIT engine, promotion hold. The fit halves end
10-27..10-29 for most setups, so **the check halves sit after the 10-29 latch/BAR90 and include LR8 (11-12) and ROT1
(11-16)**: part of any fit→check change is rule-epoch, not condition. R is per unit of risk, so sizing changes do not
distort it; the latch and LR8 change which trades exist and their net R.

## Per-setup results (top 30 by live trades + the 4 Primary setups outside it; every setup reported)
Columns: check = the later half of each setup's own sessions; "random-removal Δ" = mean gain from removing the same
number of random check trades; excess = rule Δ minus that; t = day-clustered paired t of the daily Δ (excess t in
brackets); plateau = the same condition/tail at the other two cut levels also positive on check. "1 day" = best day ≥
50% of total R.

| # | Setup | Trades (raw / dedup) | Sessions | Total R | Avg R | Avg R w/o best day (share) | Rule chosen on fit (failure mode) | Fit gain R | Check: Δ R / random-removal Δ / excess | Keep % / top-decile kept % | Check t (excess t) | Plateau | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CWT14-failbrk-orl-p05-long [CWT12/14 closed] | 1390 / 1390 | 27 | -145.1 | -0.104 | -0.130 | skip if gap < -2.04 | +20.6 | +13.4 / +6.4 / +7.0 | 90 / 90 | 1.72 (0.90) | yes [13.6;6.8] | below bar (Δ>0, limits + plateau ok) |
| 2 | CWT14-failbrk-orl-p05-lowvol-long [CWT12/14 closed] | 1305 / 1305 | 27 | -188.4 | -0.144 | -0.180 | skip if or30 > 0.673 | +40.6 | +24.0 / +10.9 / +13.1 | 87 / 87 | 1.47 (0.95) | yes [13.9;32.8] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 3 | CWT14-failbrk-pdl-p05-long [CWT12/14 closed] | 1077 / 1077 | 27 | -157.3 | -0.146 | -0.167 | skip if tod < 20.8 | +22.6 | +13.2 / +13.4 / -0.2 | 88 / 91 | 1.33 (-0.03) | yes [45.8;64.5] | below bar (Δ>0, limits + plateau ok) |
| 4 | CWT12-coil-k4-long [CWT12/14 closed] | 972 / 972 | 27 | -131.5 | -0.135 | -0.153 | skip if vwap > 0.264 | +24.8 | +2.3 / +11.6 / -9.3 | 87 / 91 | 0.48 (-1.91) | yes [2.6;8.0] | below bar (Δ>0, limits + plateau ok) |
| 5 | heat_fade_short-FD | 848 / 848 | 26 | -85.0 | -0.100 | -0.141 | skip if or30 > 0.724 | +29.0 | -2.1 / +3.7 / -5.8 | 83 / 76 | -0.19 (-0.60) | no [-2.5;-3.8] | FAIL (worse on check) |
| 6 | CWT14-failbrk-orl-p10-lowvol-long [CWT12/14 closed] | 816 / 816 | 27 | -70.5 | -0.086 | -0.113 | skip if open < -0.518 | +23.6 | +11.0 / +4.9 / +6.1 | 88 / 84 | 1.16 (0.80) | yes [9.1;9.8] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 7 | CWT14-failbrk-orl-p10-long [CWT12/14 closed] | 811 / 811 | 27 | -101.1 | -0.125 | -0.147 | skip if vwap < -0.233 | +22.7 | +21.2 / +5.5 / +15.6 | 91 / 91 | 1.94 (1.63) | yes [21.4;23.1] | below bar (Δ>0, limits + plateau ok) |
| 8 | CWT14-failbrk-pdl-p10-long [CWT12/14 closed] | 809 / 809 | 27 | -93.9 | -0.116 | -0.140 | skip if or30 > 0.848 | +7.0 | +8.4 / +6.9 / +1.5 | 92 / 91 | 0.98 (0.20) | yes [16.8;29.1] | below bar (Δ>0, limits + plateau ok) |
| 9 | CWT14-failbrk-pdl-p05-lowvol-long [CWT12/14 closed] | 765 / 765 | 27 | -112.6 | -0.147 | -0.171 | skip if tod < 31 | +16.0 | +18.4 / +12.3 / +6.1 | 82 / 85 | 1.41 (0.71) | yes [38.5;44.0] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 10 | RW7-gapdn-bounce-early-short-FD | 715 / 715 | 25 | +18.8 | +0.026 | +0.005 (83% 1 day) | skip if open < -0.328 | +8.2 | +1.6 / -2.7 / +4.2 | 92 / 96 | 0.26 (0.62) | no [-15.9;-23.6] | FAIL (Δ>0, no plateau) |
| 11 | CWT14-failbrk-pdh-p05-lowvol-short [CWT12/14 closed] | 649 / 649 | 27 | -98.7 | -0.152 | -0.168 | skip if gap > 0.801 | +35.7 | +20.6 / +12.1 / +8.6 | 66 / 76 | 1.94 (1.59) | yes [9.0;12.1] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 12 | CWT14-failbrk-pdh-p10-short [CWT12/14 closed] | 602 / 602 | 27 | -99.6 | -0.165 | -0.194 | skip if or30 < 0.352 | +37.0 | -4.8 / +3.3 / -8.1 | 84 / 79 | -0.69 (-1.52) | no [-2.2;0.8] | FAIL (worse on check) |
| 13 | RW2-exhaustion-noon-adv150-short-FD | 472 / 472 | 27 | -115.5 | -0.245 | -0.285 | skip if spy10 > 0.0965 | +32.5 | +25.6 / +17.7 / +7.9 | 33 / 55 | 0.97 (0.67) | yes [36.1;23.5] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 14 | CWT14-failbrk-pdl-p10-lowvol-long [CWT12/14 closed] | 470 / 470 | 27 | -38.1 | -0.081 | -0.111 | skip if pday > 2.09 | +10.1 | +1.1 / +6.7 / -5.5 | 83 / 70 | 0.11 (-0.62) | no [-0.2;3.3] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 15 | heat_fade_short | 395 / 395 | 28 | -81.5 | -0.206 | -0.290 | skip if withday < 0.0243 | +22.7 | +0.8 / +2.8 / -2.0 | 87 / 68 | 0.11 (-0.32) | yes [1.7;4.2] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 16 | LIQ-orl-sweep-open15-s25-long | 393 / 393 | 26 | -68.5 | -0.174 | -0.226 | skip if atr_pct > 4.41 | +21.9 | +12.1 / +6.5 / +5.6 | 81 / 82 | 1.44 (0.93) | yes [6.2;10.2] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 17 | L3-gap-slope-fromopen-FD (Primary, protected) | 378 / 378 | 23 | +90.3 | +0.239 | +0.190 (37%) | skip if withday > -4.22 | +9.6 | -18.2 / -19.6 / +1.4 | 69 / 78 | -1.17 (0.11) | no [-8.6;-13.3] | FAIL (worse on check) |
| 18 | RW3S-gapdn-flowsell-short-FD | 352 / 352 | 11 | -76.2 | -0.216 | -0.259 | skip if vwap > 0.479 | +23.5 | +3.2 / +0.5 / +2.7 | 99 / 100 | 1.46 (1.30) | yes [1.1;4.3] | below bar (Δ>0, limits + plateau ok) |
| 19 | ST2-slope20up-long-am-t05s1-FD | 348 / 348 | 25 | -36.0 | -0.103 | -0.166 | skip if open > -0.473 | +9.2 | -1.4 / +3.2 / -4.6 | 75 / 86 | -0.19 (-1.39) | no [1.3;-0.4] | FAIL (worse on check) |
| 20 | CWT13-vwapstretch-z05-long | 332 / 332 | 24 | -37.2 | -0.112 | -0.145 | skip if tod < 116 | +5.7 | -4.9 / +6.7 / -11.7 | 82 / 92 | -0.58 (-1.47) | no [-1.8;4.8] | FAIL (worse on check) |
| 21 | CWT14-failbrk-pdh-p10-lowvol-short [CWT12/14 closed] | 315 / 315 | 26 | -57.5 | -0.183 | -0.208 | skip if spy10 < -0.11 | +12.0 | +2.4 / +6.6 / -4.2 | 79 / 80 | 0.63 (-0.90) | yes [3.1;3.1] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 22 | heat_fade_long-FD | 315 / 315 | 27 | -116.3 | -0.369 | -0.412 | skip if open > -0.336 | +15.7 | +12.0 / +11.0 / +1.0 | 80 / 93 | 1.59 (0.20) | yes [0.9;26.5] | below bar (Δ>0, limits + plateau ok) |
| 23 | CWT14-failbrk-pdl-p05-R2A-long [CWT12/14 closed] | 313 / 313 | 7 | -37.5 | -0.120 | -0.129 | skip if withday < -3.42 | +4.6 | +0.1 / +1.6 / -1.5 | 94 / 92 | 0.55 (-1.86) | no [-0.1;0.2] | FAIL (Δ>0, no plateau) |
| 24 | GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long | 305 / 305 | 6 | +26.9 | +0.088 | -0.041 (133% 1 day) | skip if adv > 9.03 | +13.6 | -10.6 / -2.0 / -8.6 | 87 / 69 | -0.94 (-1.32) | no [-1.8;-14.6] | FAIL (worse on check) |
| 25 | MF3-open-flowsell-rsi5hi-FD | 297 / 273 | 27 | -35.7 | -0.131 | -0.174 | skip if adv < 8.08 | +8.7 | +1.7 / +4.0 / -2.3 | 80 / 94 | 0.27 (-0.62) | no [-0.0;5.3] | FAIL (Δ>0, no plateau) |
| 26 | NS2-sma50break-overbought-short-FD | 285 / 285 | 26 | -8.0 | -0.028 | -0.233 | skip if vwap < -0.394 | +21.4 | -15.3 / -5.7 / -9.6 | 84 / 53 | -0.96 (-1.05) | no [-6.0;-25.9] | FAIL (worse on check) |
| 27 | CWT12-coil-k6-long [CWT12/14 closed] | 271 / 271 | 24 | -49.1 | -0.181 | -0.259 | skip if or30 < 0.368 | +9.0 | +7.3 / +2.5 / +4.8 | 79 / 86 | 0.74 (0.80) | yes [9.0;11.8] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 28 | heat_fade_long | 263 / 263 | 28 | -42.2 | -0.160 | -0.230 | skip if vwap > -0.209 | +16.5 | +6.1 / -0.6 / +6.8 | 79 / 100 | 0.62 (1.16) | yes [4.6;0.3] | below bar (Δ>0, limits + plateau ok) |
| 29 | NS3-failed-vwap-reclaim-short-FD | 258 / 254 | 23 | -37.6 | -0.148 | -0.195 | skip if pday > 1.36 | +7.4 | +17.8 / +6.5 / +11.4 | 80 / 81 | 1.73 (1.27) | yes [14.3;18.0] | FAIL (Δ>0 but cuts > 30% of trades or > 10% of winners) |
| 30 | exhaustion_short-FD | 218 / 218 | 25 | -2.4 | -0.011 | -0.065 | skip if spy10 < -0.11 | +14.2 | +0.9 / -2.0 / +2.9 | 82 / 91 | 0.26 (0.75) | yes [0.9;0.9] | below bar (Δ>0, limits + plateau ok) |
| 31 | NM-ETF-late-dip-di-long (Primary) | 27 / 27 | 13 | +7.8 | +0.289 | +0.265 (19%) | no rule (too few trades) | — | — | — | — | — | no rule |
| 32 | NS5-sma50-flush-oversold-long (Primary) | 41 / 37 | 16 | -2.2 | -0.060 | -0.120 | no rule (too few trades) | — | — | — | — | — | no rule |
| 33 | RW3-gapdn-rsi5pop-flowsell-short-FD (Primary) | 185 / 175 | 26 | +35.8 | +0.205 | +0.077 (68% 1 day) | no rule (no eligible tail on fit) | — | — | — | — | — | no rule |
| 34 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (Primary) | 198 / 192 | 26 | +30.2 | +0.157 | +0.065 (65% 1 day) | skip if price < 29.5 | +4.4 | -0.8 / +0.6 / -1.3 | 90 / 90 | -0.28 (-0.68) | no [-0.6;0.7] | FAIL (worse on check) |
| 35 | ST7-rsi50dn-long-pm-t1s1-FD (Primary) | 49 / 49 | 17 | +5.8 | +0.118 | +0.038 (70% 1 day) | no rule (too few trades) | — | — | — | — | — | no rule |

Per-setup improve/worsen on check: 23 improve / 8 worse (raw); 17 / 14 against the random-removal baseline.
NM-ETF (27 trades), NS5 (37) and ST7 (49) had too few trades for a split; RW3's fit half had no eligible losing tail.

## Conditions map — what it does show (descriptive, data/map.csv.gz, data/pooled.csv)
- **First hour is the board's weakest time** in both halves (pooled over the 35 setups, setup-relative): 09:30-10:00
  -0.195 / -0.150R, 10:00-10:30 -0.166 / -0.152R, versus 10:30-15:00 -0.025 to -0.125R. But per setup only 5 of 12
  setups with ≥ 10 open-bucket trades per half are worse at the open in both halves (3 are better in both), so this is
  a family/mechanism fact (CWT14 long failed-break lines carry it), not a bespoke rule. It supports C3-MECH's
  09:35-09:45 harness and the first-hour Move Hunt rather than a filter.
- **L3-gap-slope-fromopen-FD (protected; record only):** 13:30-15:00 entries -0.36R (n 32) vs +0.27..+0.36R in
  10:00-13:30 (same as l3_bespoke_1117's AM/PM split; the WB4 copy in Testing A already tests a 13:00 window end);
  low ATR% tercile (2.0-6.8%) -0.08R vs +0.46/+0.33R; widest first-30-min range tercile -0.01R. Its fit-chosen rule
  (skip if the stock is already down > 4.2% at entry) **failed** on check (-18.2R). Nothing here touches L3.
- **RW3 (Primary):** deep gap-downs (gap < -2.0%) +0.62R/trade (n 59) vs ~0 for shallower gaps; SPY weak at 10:00
  +0.50R vs -0.05R strong. No eligible losing tail on fit, and "gates on proven setups" is on the Stop list: record only.
- **RW5 (Primary):** flat across conditions; its fit rule (skip price < $29.5) failed on check (-0.8R).
- **NM-ETF / NS5 / ST7:** 27-49 trades — maps in map.csv.gz are descriptive only. ST7's 13:30-15:00 entries -0.32R (n 12).

## What survives as leads (none at the bar; for the watch list only)
Rules that held on check with limits + plateau and beat random removal at ≥ 95th percentile, outside the closed
CWT12/14 families: **heat_fade_long "skip if price > VWAP - 0.21 ATR"** (excess +6.8R, t 1.16; Graveyard) and
RW3S "skip if > 0.48 ATR above VWAP" (3 trades removed — trivial). NS3 "skip if prior day > +1.36%" beat random
(+11.4R, 100th pct, t 1.27) but kept only 81% of top-decile winners, so it fails the pre-registered limits.
CWT14-orl-p10 (VWAP) and CWT14-orl-p05-lowvol (first-30-min range) are the strongest numbers but those families are
closed to variants (P3 Stop list); reported for the record only.

## Proposals (owner decides; nothing changes without a yes)
See FRAMEWORK.md for the Primary bespoke-rule framework.

| Code | Proposal | Evidence | Expected effect | Owner? |
|---|---|---|---|---|
| W4-NOFILTER | No live per-setup condition filter (any account) from this run; do not build bespoke entry filters from < 15 active sessions per half of live data | 0/31 at bar; excess +31.8R vs +550.5R fit gain; 56% sign agreement, 0.23x shrink | Avoids ~58R of check-half damage seen here and churn; no R claimed | yes (confirms a stop) |
| W4-FRAME | Adopt the bespoke-rule framework for Primary (FRAMEWORK.md): shadow-tag first, judged on excess over random removal and paired day Δ, ≥ 15 active days per half, lineage-counted bar, one rule ≤ 2 parts per setup | This run + l3_bespoke_1117 + P3/P4 (60/60 in-sample WB passes) | Fewer false bespoke rules; a real one shows up in ~4-6 weeks of shadow tags | yes |
| W4-TAGS | Housekeeping (reporting only): write the 12 point-in-time conditions into each journaled decision (trades + skipped + shadow signals) so the map rebuilds nightly and the framework's shadow tags cost nothing | Building them here took one bar pack per session; RECORD-LIVE (11-18) already stores quotes | No R; makes every future condition study point-in-time and cheap | housekeeping (yes as courtesy) |
| W4-WATCH | Pre-registered watch list scored once after 15 more active days, journal-only, no live change: heat_fade_long VWAP rule; NS3 prior-day rule; L3 13:30-15:00 (record, via WB4); RW3 gap < -2% split (record) | Rows above; frozen thresholds in data/results.csv | No live change; a pass would enter FRAMEWORK step 2 | yes |
