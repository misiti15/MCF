# stoplab A: is -2R the right per-setup daily stop?

*Educational only — not financial advice.* These are live **paper** results (rule 7), 2026-10-06..2026-11-09, with costs in (live R = pnl_adj / risk; what-if R = runner r_multiple with backtest costs). The 2-year lab results are backtests and are labelled separately. This is research only: nothing in config/, mcf/, the setups, exits, docs/live or the ledger was changed. The plan is `../PLAN.md`, written before scoring. The locked block 2024-11-01..2025-02-28 was never read, and the 2-year HOLD months were not loaded.

**How it was replayed.** Each (account, setup, session) is replayed in entry order. The sequence is the live trades plus the run_id=2 what-ifs the per-setup latch blocked (4,959). A trade is blocked once the setup's **realised** R from trades that exited at or before its entry is <= -L, and the block lasts for the rest of the day. Open trades run to their own stops.
- **Trigger basis.** The trigger uses journal r_multiple, as the live runner does (`mcf/execution/runner.py`). Scoring uses R.
- **Parity.** With that trigger, the simulated -2.0 baseline matches what was live: Primary 10-29..11-09 gives -62.3R simulated vs -57.2R actual, and the Graveyard gives -619.7R vs -625.0R. The runner books exits when it reconciles them, a few seconds to minutes after the fill, so it lets a few more trades through than the sim does.
- **Data.** 1,590 setup-days, 22,543 trades (17,584 live). Splits are per setup: the first 60% of its sessions are CHOOSE (1,039 setup-days) and the last 40% are VALIDATE (551).

**Configurations (grid A): 30.** A1 has 12 levels, A2 12, A3 1 rule (12 per setup), A4 1 rule and A5 4. They are part of the study-wide N = 64, with bar t >= 2.88 (per setup >= 2.23).
- One unplanned diagnostic was added after the family table was read: setups split by the sign of their own CHOOSE average R. It is **not** a candidate.
- Sensitivities are not counted: A6a with halt what-ifs included, and A6b on the 2-year lab.

**Rule changes inside the window (from `research/ledger.jsonl`).** These move the sample, not the comparison, because every level replays the same trade sequence.
- The per-setup -2R stop was on in T1/T2/Gen 10-19..10-22: non-latching at first, latched from 10-23 under LL-LATCH. ST-A switched it off in T1/T2/Gen on 10-23.
- The Graveyard has run -2R since 10-21.
- ST-P put the latched -2R on Primary from 10-29.
- Scale-out fixes on 10-16 and 10-20 (SO1). Primary size ~$5k, then ~$4k from 10-28.
- BAR90 on 10-29, the CF cost filter in T1/T2 on 10-30, the R2A cap exemption on 11-03, ROLL1 on 11-05 and EXPO1109 on 11-09.
- Many setup moves 10-20..11-09.

## Answer in one paragraph
**-2R is not a sharp optimum, and no other level passes.** On VALIDATE, every level from -1.25R to -2.01R is the same within noise: +8..+15R vs -2.0, t <= 0.67. So -1.6, -1.75, -1.8 and -2.01 are the same stop as -2.0 on this data.
- **Looser is consistently worse.** At -2.25R the validate change is -91R (t -1.91), and -2.5 / -3 / -4 are worse still. The 2-year lab agrees, at t -2.7 to -4.1 on VALID.
- **Only -1.0R beats -2.0 on validate:** +110R, t 2.39, which is under the 2.88 bar. -1.0R is also the edge of the grid. Its **excess delta is about 0** (+6R), and on 2 years it is -776R (t -2.2). So the gain comes from trading losing setups less, not from better timing. Average R per trade is -0.120 at every level. A tighter daily stop just trades less of a negative-expectancy book; cutting or fixing those setups is the setup-level answer.
- **Per-setup levels do not hold out of sample.**
  - 84 setups had enough sessions to pick their own level on CHOOSE. Of the 56 whose pick differed from -2.0, 24 improved on VALIDATE (+98R) and 15 got worse (-143R), so the net is -45R.
  - Applied as a rule across all setups, per-setup picks score -34R vs uniform -2.0 on VALIDATE (t -0.67).
  - None of the 111 setups with >= 20 trades is robust.
- **The one family-level signal is gap-down shorts with the stop OFF.** It gives +47R on validate (t 2.14) with a plateau, and 5 setups improve vs 2 that worsen. But 58% of the gain is a single day (10-22, RW7-FD in Testing 1), and it is below the bar. On 2 years, positive-expectancy setups lean "off/looser" (+86R VALID, t 2.3, 13 setups up / 4 down), while live it goes the other way (-51R, t -0.9). It goes to the backlog as a forward-shadow idea, not a change.

## (1) Global level: all accounts, all setups (A1 realised latch, A5 give-back)
Totals cover all 25 sessions. "Excess" is the delta minus (change in trades x the setup's own CHOOSE average R): a positive excess means the gain comes from timing, while about 0 means it only comes from trading a losing setup less. The live baseline is Primary -2 from 10-29, Graveyard -2 and the others off. Day-clustered t is taken over dates.

| Level | Total R | Trades | Avg R | Green days /25 | Worst day | R w/o best day | Choose R | Validate R | Validate Δ vs -2.0 (t) | Validate Δ w/o best day | Excess Δ vs -2.0 (choose / validate) | Validate Δ vs live baseline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| off | -2,703 | 22,543 | -0.120 | 4 | -433 | -2,773 | -1,616 | -1,087 | -459.0 (-2.04) | -485.0 | +77.2 / +28.0 | -381.0 |
| -1.0R | -1,546 | 12,886 | -0.120 | 2 | -175 | -1,567 | -1,028 | -518 | +110.1 (2.39) | +69.4 | +2.4 / +6.0 | +188.0 |
| -1.25R | -1,754 | 14,370 | -0.122 | 2 | -228 | -1,804 | -1,138 | -616 | +11.9 (0.44) | -3.1 | +5.4 / -34.7 | +89.9 |
| -1.5R | -1,785 | 14,751 | -0.121 | 1 | -233 | -1,831 | -1,172 | -613 | +14.6 (0.67) | +1.4 | -1.4 / -17.2 | +92.6 |
| -1.6R | -1,793 | 14,865 | -0.121 | 1 | -233 | -1,838 | -1,176 | -617 | +11.1 (0.49) | -1.7 | +1.8 / -9.8 | +89.0 |
| -1.75R | -1,804 | 15,006 | -0.120 | 1 | -233 | -1,850 | -1,191 | -614 | +13.8 (0.62) | +1.1 | -2.9 / -3.1 | +91.8 |
| -1.8R | -1,812 | 15,050 | -0.120 | 1 | -236 | -1,858 | -1,192 | -620 | +8.0 (0.40) | -2.5 | -3.7 / -5.5 | +85.9 |
| -2.0R | -1,850 | 15,363 | -0.120 | 1 | -246 | -1,893 | -1,222 | -628 | +0.0 | +0.0 | +0.0 / +0.0 | +78.0 |
| -2.01R | -1,852 | 15,377 | -0.120 | 1 | -246 | -1,895 | -1,220 | -632 | -4.3 (-1.00) | -4.3 | +4.2 / -1.7 | +73.7 |
| -2.25R | -1,948 | 16,174 | -0.120 | 3 | -262 | -1,996 | -1,230 | -718 | -90.6 (-1.91) | -99.2 | +39.8 / -26.7 | -12.6 |
| -2.5R | -1,979 | 16,612 | -0.119 | 2 | -242 | -2,031 | -1,271 | -707 | -79.6 (-1.43) | -93.8 | +19.3 / +0.8 | -1.7 |
| -3.0R | -1,998 | 17,062 | -0.117 | 1 | -251 | -2,050 | -1,270 | -728 | -100.6 (-1.34) | -110.4 | +53.1 / +4.4 | -22.7 |
| -4.0R | -2,129 | 17,956 | -0.119 | 2 | -254 | -2,185 | -1,332 | -797 | -169.0 (-1.53) | -180.2 | +47.2 / +0.9 | -91.0 |
| give-back 1.5R | -1,620 | 13,412 | -0.121 | 3 | -193 | -1,669 | -1,075 | -545 | +83.0 (1.47) | +36.0 | +15.1 / -26.8 | +161.0 |
| give-back 2.0R | -1,713 | 13,944 | -0.123 | 3 | -210 | -1,758 | -1,134 | -579 | +49.1 (1.28) | +18.8 | +1.3 / -36.6 | +127.1 |
| give-back 2.5R | -1,881 | 15,456 | -0.122 | 4 | -238 | -1,932 | -1,206 | -675 | -47.5 (-0.57) | -96.7 | +26.9 / -32.8 | +30.5 |
| give-back 3.0R | -1,942 | 15,751 | -0.123 | 4 | -242 | -1,992 | -1,242 | -700 | -72.2 (-0.88) | -108.4 | +16.3 / -46.3 | +5.8 |
- **Plateau.** -1.25..-2.01 is one flat plateau: validate change vs -2.0 is -4..+15R, all |t| < 1. The levels the owner named (-1.6, -1.75, -1.8, -2.01) differ from -2.0 by +8..+14R on validate (t 0.4..0.6), and -2.01 by -4R. -2.25 falls off the plateau at once, with validate -91R (t -1.91) and 26 setups worse vs 15 better.
- **Choose split.** Tighter is monotonically better: -1.0 > -1.25 > ... > -2.0 > ... > off. The CHOOSE best is -1.0R (choose -1,028R vs -1,222R at -2.0). It has one neighbour on the grid (-1.25, validate +12R).
- **Green days.** At most 4 of 25 at any level, because the book as a whole loses (avg R -0.12). The worst day goes from -433R (off) to -246R (-2.0) to -175R (-1.0).
- **vs off.** The latch at any level saves R: +459R on validate at -2.0, t 2.04. But the excess vs off is negative at every level: -28R at -2.0, and -22R to -74R across levels. The trades the latch blocks are slightly *better* than the setup's own average, which matches latch_1103 ("by the time the latch fires, the cluster has played out").
- **Give-back stop (A5).** It stops new entries once realised R is G below the day's peak, with the peak floored at 0. G = 1.5 gives +83R on validate vs -2.0, t 1.47. Most of that is the extra tightness (it is at least as tight as -1.5), and the validate excess is -27R. G = 2.5 / 3.0 are worse than -2.0.
- **A2: realised + open (1-min marked) R.** Coverage is 791 setup-days, 5,494 rows: only days <= 11-04 whose symbols all have bars, which favours small days. Adding open R gains on CHOOSE (+51R at -2.0) but loses on VALIDATE (-6R at -2.0, -14..-20R at -2.5..-4.0). No level is better on both splits. See `A2_*.csv`.
- **A6a: halt what-ifs included** (as if there were no account halt). The ordering is the same: -1.0 > the -1.25..-2.01 plateau > looser. -2.0 vs off on validate is +488R (t 2.25), and the excess is negative at every level.
- **A6b: 2-year lab** (backtest, 95 setups, 21,563 setup-days, production costs, caps 3 lots/symbol and 30 open per setup; TRAIN <= 2025-12, VALID 2026-01..03 + 07..09-15).
  - Tighter is monotonically better vs -2.0. -1.0 gives +3,599R TRAIN (t 8.5) and +1,360R VALID (t 3.9); -1.5 gives +713 / +404R; -2.25 gives -868 / -390R; -4.0 gives -3,483 / -1,468R.
  - **The excess shows none of it is timing.** At -1.0 the excess is -36R (t -0.1) on TRAIN and -776R (t -2.2) on VALID; looser levels have positive VALID excess (up to +795R at -4.0).
  - 73 of the 95 lab setups have negative TRAIN average R. For the 22 positive ones, off is +92R TRAIN (t 1.7) and +86R VALID (t 2.3; 13 setups up / 4 down), and -3.0 / -4.0 are also positive on VALID. That is consistent but under the bar (`lab2y_expectancy.txt`).
- **Primary only, since the latch went live (10-29..11-09, 8 sessions).** The -2.0 sim gives -62.3R. -1.0 gives -53.4R (+8.8, t 1.1), -1.5/-1.6 +3.1R, -2.5 +11.1R (t 1.2) and off -5.2R. All of it is noise.

### By account (R per level, all sessions; `A1_by_account_vs_off.csv`)
| Level | Primary | Testing 1 | Testing 2 | Gen | Graveyard | Explore 1 | Live Lab |
|---|---|---|---|---|---|---|---|
| off | -79.5 | -307.1 | -696.7 | -568.3 | -1,037.7 | -12.3 | -1.2 |
| -1.0 | -22.9 | -197.2 | -397.2 | -380.1 | -544.5 | -3.0 | -0.9 |
| -1.5 | -53.2 | -207.7 | -455.5 | -453.0 | -610.7 | -4.0 | -1.0 |
| -1.75 | -54.3 | -209.6 | -475.2 | -453.0 | -607.4 | -4.0 | -1.0 |
| -2.0 | -53.2 | -217.0 | -496.3 | -458.7 | -619.7 | -4.0 | -1.0 |
| -2.25 | -51.2 | -214.6 | -519.5 | -481.5 | -676.3 | -4.0 | -1.0 |
| -2.5 | -45.7 | -215.8 | -540.0 | -477.8 | -691.0 | -7.2 | -1.0 |
| -3.0 | -54.5 | -220.7 | -521.8 | -482.3 | -710.8 | -7.2 | -1.0 |

These are simulated totals, including latch what-ifs, so they are not the accounts' actual P&L. Testing and Gen ran the stop off after 10-23.

## (2) Per setup: best level on CHOOSE, scored on VALIDATE (A3)
The rule: each setup with >= 5 live sessions picks its best A1 level on CHOOSE. Ties go to -2.0, then to the nearest level. Setups with fewer sessions take the global CHOOSE pick, -1.0R. Gains are vs uniform -2.0 for the same setup.
- **Robust** means the choose and validate gains are both > 0, the day-clustered validate t is >= 2.23, both grid neighbours are also positive on validate, the validate excess is > 0, and the setup has >= 5 sessions.
- Setups are pooled across accounts by name.
- "Avg R at -2.0 (w/o best day)" applies the one-big-day rule (owner 2026-10-25).

**Summary for the 111 setups with >= 20 live trades:**
- **Own picks.** 84 setups had >= 5 sessions and picked their own level: -1.0 30 times, -2.0 28, -2.25 5, -1.25 4, -3.0 4, -1.8 3, off 3, -4.0 2, -2.5 2, and -1.6 / -1.5 / -2.01 once each.
- **Tighter picks (39 setups).** They gained +211R on choose and +27R on validate; 19 setups improved and 9 got worse.
- **Looser picks (13 setups).** +61R on choose, then -64R on validate; 3 improved and 5 got worse.
- **Off picks (3 setups).** +60R on choose, then -7R on validate.
- **All 56 own picks that differ from -2.0.** On validate, 24 improve (+98R), 15 get worse (-143R, worst -24.9R for RW4-ns3-adv150-short-FD), and 17 are unchanged. Net -45R.
- **Robust: 0 of 111.** 24 setups keep the sign (choose > 0 and validate > 0), but none reaches t 2.23 together with a plateau and a positive excess. The largest validate gains are +11.0R (CWT13-vwapstretch-z05-long, -1.0), +9.8R (CWT14-failbrk-pdl-p05-long, -1.25) and +9.1R (NS3-failed-vwap-reclaim-short-FD, -1.0), all at t <= 1.4.
- **As a whole-book rule** (`A3_per_setup_all.csv`), the per-setup picks score **-34R** vs uniform -2.0 on VALIDATE (t -0.67, -54R without its best day) and +44R vs the live baseline (t 0.97). That fails.

| Setup | Fam | n live | Sess | R off | R at -2.0 | Avg R at -2.0 (w/o best day) | Best level (choose) | Choose gain | Validate gain | Val t | Excess (val) | Plateau | Robust |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CWT14-failbrk-orl-p05-long | other | 957 | 21 | -270.4 | -127.2 | -0.150 (-0.174) | -1.0R | +15.0 | +1.8 | 1.40 | +1.0 | y | n |
| CWT14-failbrk-pdl-p05-long | other | 868 | 21 | -131.7 | -61.3 | -0.083 (-0.111) | -1.25R | +13.0 | +9.8 | 1.37 | +7.7 | y | n |
| CWT14-failbrk-orl-p05-lowvol-long | other | 848 | 21 | -242.7 | -130.7 | -0.174 (-0.196) | -1.0R | +23.9 | +5.1 | 1.07 | +1.1 | y | n |
| CWT12-coil-k4-long | coils/flags | 718 | 21 | -55.1 | -54.4 | -0.081 (-0.104) | -3.0R | +2.3 | +0.0 |  | +0.0 | n | n |
| heat_fade_short-FD | other | 677 | 21 | -16.6 | -10.1 | -0.018 (-0.059) | -1.0R | +19.5 | +6.9 | 0.35 | +0.5 | n | n |
| CWT14-failbrk-pdl-p05-lowvol-long | other | 611 | 21 | -122.4 | -68.9 | -0.156 (-0.183) | -3.0R | +4.9 | -10.7 | -1.00 | -8.8 | n | n |
| CWT14-failbrk-orl-p10-lowvol-long | other | 556 | 21 | -80.9 | -56.6 | -0.110 (-0.143) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| CWT14-failbrk-orl-p10-long | other | 543 | 21 | -130.5 | -93.7 | -0.177 (-0.199) | -4.0R | +0.3 | -22.5 | -1.16 | -16.2 | n | n |
| CWT14-failbrk-pdl-p10-long | other | 543 | 21 | -46.2 | -18.7 | -0.043 (-0.083) | -3.0R | +7.2 | -5.0 | -1.26 | -4.8 | n | n |
| CWT14-failbrk-pdh-p05-lowvol-short | other | 473 | 21 | -71.2 | -78.4 | -0.179 (-0.189) | -1.0R | +9.2 | +4.4 | 0.47 | -0.9 | y | n |
| CWT14-failbrk-pdh-p10-short | other | 464 | 21 | -101.0 | -71.6 | -0.172 (-0.214) | -1.8R | +0.6 | -6.3 | -1.00 | -10.6 | n | n |
| RW7-gapdn-bounce-early-short-FD | gap-down shorts | 436 | 19 | +78.2 | +18.8 | +0.064 (+0.018) | off | +51.0 | +8.4 | 1.00 | +5.8 | y | n |
| RW2-exhaustion-noon-adv150-short-FD | other | 426 | 21 | -128.5 | -77.0 | -0.224 (-0.278) | -1.0R | +12.6 | -6.8 | -1.14 | -11.1 | n | n |
| heat_fade_short | other | 328 | 23 | -57.3 | -48.0 | -0.162 (-0.272) | -2.25R | +3.5 | -9.5 | -1.12 | -2.9 | n | n |
| CWT14-failbrk-pdl-p10-lowvol-long | other | 306 | 21 | -23.4 | -7.8 | -0.030 (-0.054) | -1.0R | +2.2 | +2.3 | 1.30 | +2.3 | y | n |
| LIQ-orl-sweep-open15-s25-long | other | 299 | 20 | -38.5 | -31.4 | -0.108 (-0.173) | -1.0R | +3.5 | -2.2 | -1.10 | -3.5 | n | n |
| CWT13-vwapstretch-z05-long | other | 272 | 19 | -41.8 | -22.1 | -0.185 (-0.303) | -1.0R | +0.3 | +11.0 | 1.12 | +10.8 | y | n |
| L3-gap-slope-fromopen-FD | other | 267 | 18 | +23.6 | +48.8 | +0.201 (+0.093) | -1.25R | +1.3 | +0.0 |  | +0.0 | n | n |
| ST2-slope20up-long-am-t05s1-FD | other | 256 | 20 | -45.4 | -41.6 | -0.158 (-0.189) | -1.0R | +1.0 | -0.7 | -0.07 | -9.3 | n | n |
| heat_fade_long-FD | other | 243 | 21 | -97.3 | -46.2 | -0.289 (-0.369) | -1.0R | +12.0 | -1.3 | -1.32 | -2.2 | n | n |
| heat_fade_long | other | 235 | 24 | -63.6 | -22.1 | -0.133 (-0.247) | -1.0R | +2.6 | +2.2 | 1.00 | +1.6 | n | n |
| CWT14-failbrk-pdh-p10-lowvol-short | other | 230 | 20 | -38.6 | -37.4 | -0.185 (-0.226) | -1.6R | +6.2 | -3.1 | -1.00 | -4.5 | n | n |
| MF3-open-flowsell-rsi5hi-FD | MF early sellers | 219 | 21 | -27.9 | -31.0 | -0.179 (-0.245) | -2.25R | +12.1 | +2.3 | 0.38 | +3.9 | n | n |
| GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long | GEN | 212 | 4 | +8.5 | +20.0 | +0.106 (-0.153) | -1.0R (global; <5 sess) | -0.8 | +0.0 |  | +0.0 | n | n |
| CWT12-coil-k6-long | coils/flags | 206 | 18 | -29.9 | -5.3 | -0.024 (-0.194) | -1.25R | +6.2 | -13.4 | -1.00 | -18.4 | n | n |
| NS2-sma50break-overbought-short-FD | other | 178 | 20 | -30.5 | -40.7 | -0.257 (-0.300) | -4.0R | +13.9 | +3.3 | 1.00 | +4.8 | y | n |
| NS3-failed-vwap-reclaim-short-FD | other | 175 | 18 | -41.4 | -23.7 | -0.146 (-0.223) | -1.0R | +6.4 | +9.1 | 1.17 | +8.7 | n | n |
| CWT13-vwapstretch-z05-short | other | 173 | 18 | -61.5 | -25.6 | -0.148 (-0.192) | -1.5R | +4.0 | +0.0 |  | +0.0 | n | n |
| exhaustion_short-FD | other | 170 | 19 | -10.1 | -6.8 | -0.044 (-0.129) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long | GEN | 167 | 8 | -42.0 | -30.3 | -0.218 (-0.381) | -1.0R | +4.2 | +5.4 | 1.44 | +1.8 | n | n |
| GEN-261029-08-Ret15mlem0p36-Flow3lem0p54-RSI14ge65-AM-SPYgt0p5-hold-short | GEN | 164 | 4 | -60.9 | -56.2 | -0.469 (-0.855) | -1.0R (global; <5 sess) | -12.3 | +13.8 |  | +10.5 | n | n |
| RW4-ns3-adv150-short-FD | other | 160 | 19 | -47.7 | -29.5 | -0.185 (-0.241) | -2.5R | +0.4 | -24.9 | -1.00 | -12.5 | n | n |
| RW3S-gapdn-flowsell-short-FD | gap-down shorts | 143 | 5 | -39.4 | -45.6 | -0.443 (-0.469) | off | +4.0 | +2.3 | 1.00 | +5.1 | n | n |
| CWT09-gapdn-bounce-g5-lowerhalf-short | gap-down shorts | 141 | 15 | +4.0 | +2.9 | +0.023 (-0.070) | -1.0R | +5.1 | -18.4 | -1.58 | -29.0 | n | n |
| MF4-h40-open-flowsell-FD | MF early sellers | 138 | 21 | -32.9 | -31.3 | -0.227 (-0.281) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | gap-down shorts | 133 | 20 | +47.3 | +44.0 | +0.346 (+0.248) | -2.5R | +4.3 | +0.0 |  | +0.0 | n | n |
| GEN-261020-07-RSIslopege19-LowWickge0p33-ATRdge4p4-AM-BRvwgt0p7-hold-long | GEN | 126 | 6 | -39.0 | -39.0 | -0.309 (-0.487) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| MF2-open-rsimidhi-flowsell-FD | MF early sellers | 125 | 19 | +8.2 | +5.4 | +0.048 (-0.268) | -1.0R | +4.6 | +4.0 | 0.71 | +11.1 | n | n |
| RW3-gapdn-rsi5pop-flowsell-short-FD | gap-down shorts | 123 | 20 | +56.8 | +49.9 | +0.405 (+0.261) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| MF5-flowsell-vwapup-rsi5hi-FD | MF early sellers | 120 | 20 | -30.4 | -24.3 | -0.243 (-0.332) | -3.0R | +2.6 | +2.8 | 1.09 | +4.8 | y | n |
| CWT14-failbrk-pdl-p05-R2A-long | other | 110 | 4 | -12.1 | -11.6 | -0.110 (-0.139) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| MF1-945-flowsell-vwapup-FD | MF early sellers | 110 | 21 | -33.8 | -20.9 | -0.211 (-0.308) | off | +5.0 | -18.0 | -0.46 | -18.1 | n | n |
| RW1-gapdn-bounce-flowsell-short-FD | gap-down shorts | 108 | 20 | +17.0 | +9.5 | +0.091 (+0.051) | -2.25R | +8.1 | +0.0 |  | +0.0 | n | n |
| CWT09-gapdn-vwaploss-g5-short | gap-down shorts | 107 | 14 | +3.9 | -23.1 | -0.259 (-0.413) | -1.0R | +0.2 | +1.7 | 1.00 | +0.5 | y | n |
| exhaustion_short | other | 106 | 19 | -5.1 | -5.6 | -0.061 (-0.205) | -2.01R | +6.8 | +0.0 |  | +0.0 | n | n |
| GEN-261021-07-VWAPxUp-ORBfailUp-AM-SPYgt0p5-hold-long | GEN | 103 | 4 | -10.2 | +9.0 | +0.137 (-0.119) | -1.0R (global; <5 sess) | +6.2 | -4.4 |  | -7.5 | n | n |
| RW6-ns2-up3-short-FD | other | 103 | 18 | -19.4 | -18.4 | -0.194 (-0.303) | -1.0R | +11.6 | +1.1 | 1.00 | +0.7 | n | n |
| L3-gap-slope-rsi5hi-FD | other | 91 | 17 | +18.9 | +6.6 | +0.073 (-0.020) | -1.0R | +0.3 | +1.0 | 1.00 | +1.2 | n | n |
| MF5-flowsell-vwapup-rsi5hi | MF early sellers | 89 | 22 | -2.6 | -0.7 | -0.008 (-0.112) | -2.25R | +1.0 | +0.0 |  | +0.0 | n | n |
| GEN-261022-08-EMAdChglem0p094-Flow3ge1-RVolDayle0p59-AM-SPYgt0p25-holdtr-short | GEN | 83 | 5 | -24.1 | -24.1 | -0.290 (-0.570) | -1.25R | +2.0 | +0.0 |  | +0.0 | n | n |
| NS1-rsidip-rsi5pop-long-FD | other | 82 | 18 | -4.9 | -4.9 | -0.059 (-0.140) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261020-05-ORBfailDn-VWAPcrossesge4-SMA20dlem0p31-LUNCH-SPYgt0p25-holdtr-long | GEN | 75 | 7 | +1.4 | +0.7 | +0.009 (-0.028) | -2.25R | +0.7 | +0.0 |  | +0.0 | n | n |
| GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long | GEN | 73 | 3 | +1.1 | +1.1 | +0.015 (-0.804) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| L3-gap-slope-lowdist-FD | other | 72 | 14 | +4.8 | +4.8 | +0.067 (-0.074) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261026-05-Ret15mATRge0p042-FromPCATRge0p28-ORHdistlem0p38-OPEN-BRopgt0p5-hold-short | GEN | 67 | 6 | -61.9 | -44.7 | -0.859 (-0.913) | -1.0R | +18.8 | +0.0 |  | +0.0 | n | n |
| NS2-sma50break-overbought-short | other | 67 | 9 | -22.2 | -3.0 | -0.078 (-0.133) | -1.0R | +8.1 | +0.0 |  | +0.0 | n | n |
| NS3-failed-vwap-reclaim-short | other | 67 | 10 | -15.3 | -14.5 | -0.238 (-0.438) | -1.0R | +1.8 | +0.0 |  | +0.0 | n | n |
| GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short | GEN | 65 | 3 | -2.7 | -11.6 | -0.208 (-0.215) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| CWT05-flush-m05-v3-long | flush longs | 63 | 15 | -12.3 | -12.4 | -0.238 (-0.342) | -1.0R | +1.1 | +1.4 | 1.00 | +1.3 | y | n |
| NS5-sma50-flush-oversold-long-FD | flush longs | 63 | 20 | -16.8 | -20.9 | -0.332 (-0.438) | -1.0R | +2.9 | +0.9 | 0.82 | +0.2 | n | n |
| GEN-261022-09-Ret15mATRlem0p16-BarRngATRge0p11-ADX7ge64-AM-BRvwlt0p3-hold-short | GEN | 57 | 1 | -42.7 | -27.8 | -0.844 (+0.000) | -1.0R (global; <5 sess) | +3.3 | +0.0 |  | +0.0 | n | n |
| GEN-261022-07-Z12lem1p9-FlowShiftlem0p96-ATRdge3p6-AM-BRopgt0p5-t1s1-short | GEN | 55 | 7 | +10.1 | +10.1 | +0.184 (-0.207) | -1.0R | +0.6 | +0.0 |  | +0.0 | n | n |
| ST1-ordn-long-pm-t05s1-FD | other | 54 | 15 | -16.9 | -11.7 | -0.280 (-0.536) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| NM-AR-AM-gapdown-capitulation-long | other | 54 | 8 | -24.1 | -24.1 | -0.447 (-0.595) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261019-05-RSIslopelem9-PDLdistle0p14-EMAdifflem0p46-OPEN-SPYltm0p5-t1s1-long | GEN | 53 | 2 | -53.2 | -21.0 | -1.052 (-1.052) | -1.0R (global; <5 sess) | +4.4 | +0.0 |  | +0.0 | n | n |
| GEN-261028-08-Ret5mge0p21-SMA20dlem0p16-Compress6le0p11-LUNCH-BRoplt0p35-holdtr-long | GEN | 53 | 2 | -13.9 | -22.2 | -0.517 (-0.679) | -1.0R (global; <5 sess) | +2.1 | +0.0 |  | +0.0 | n | n |
| GEN-261028-09-FlowShiftlem0p65-ADX7le23-AM-BRoplt0p35-t05s1-long | GEN | 53 | 3 | -18.1 | -18.1 | -0.341 (-0.410) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261020-03-MACDhge0p079-BarsSinceLODle5-MID-BRvwlt0p3-t05s05-long | GEN | 52 | 2 | -37.8 | -29.5 | -0.657 (-1.156) | -1.0R (global; <5 sess) | +7.3 | +0.0 |  | +0.0 | n | n |
| RW6G1-ns2-up3-vwap2sd-short-FD | other | 51 | 15 | -1.5 | -1.5 | -0.030 (-0.168) | -1.0R | +2.1 | -0.4 | -1.00 | -0.9 | n | n |
| NM-HL-T75-pm-long | other | 50 | 9 | -1.1 | +6.1 | +0.212 (+0.131) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| intraday_momentum | other | 49 | 19 | -17.3 | -17.3 | -0.352 (-0.383) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short | GEN | 49 | 2 | -28.6 | -29.3 | -0.771 (-1.084) | -1.0R (global; <5 sess) | +7.6 | +0.0 |  | +0.0 | n | n |
| GEN-261019-04-EMAdChgge0p15-RSI14le22-MID-BRoplt0p5-t1s1-long | GEN | 49 | 5 | -6.5 | -6.5 | -0.132 (-0.498) | -1.0R | +2.2 | +7.6 | 1.00 | +5.9 | n | n |
| GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short | GEN | 48 | 4 | -5.0 | -5.0 | -0.105 (-0.197) | -1.0R (global; <5 sess) | +3.8 | +0.0 |  | +0.0 | n | n |
| GEN-261019-10-FlowShiftge0p42-SMA50dge1p7-PM-BRoplt0p5-t1s1-short | GEN | 47 | 7 | -1.4 | +6.6 | +0.175 (-0.148) | -1.8R | +1.1 | +0.0 |  | +0.0 | n | n |
| GEN-261027-05-VolRatioge1p5-ORLdistge0p41-ATRdge6-MID-BRvwgt0p7-t05s1-long | GEN | 47 | 3 | -4.9 | -4.9 | -0.104 (-0.228) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261029-01-ORBfailUp-RSI14le41-ADX7le29-LAM-QQQgt0p3-hold-long | GEN | 45 | 3 | -27.4 | -27.4 | -0.609 (-0.663) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| MF3-open-flowsell-rsi5hi | MF early sellers | 44 | 10 | -0.7 | -0.7 | -0.015 (-0.116) | -1.0R | +0.7 | +2.8 | 1.37 | +3.2 | n | n |
| NS3V1-am-widestop-short | other | 42 | 6 | -11.6 | -11.6 | -0.276 (-0.509) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| CWT13-vwapstretch-z075-long | other | 40 | 9 | -3.5 | +4.8 | +0.252 (+0.134) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261022-01-ORBfailUp-ATRdge7p9-Eff6ge0p55-AM-SPYdn-hold-long | GEN | 40 | 6 | -5.5 | -5.5 | -0.137 (-0.378) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261026-10-ORBfailDn-EMAdChglem0p051-PM-BRopgt0p65-t1s1-long | GEN | 39 | 3 | -7.1 | -7.1 | -0.181 (-0.373) | -1.0R (global; <5 sess) | +0.0 | +0.3 |  | +0.2 | n | n |
| GEN-261027-08-ORBfailDn-FromPCATRlem0p96-LUNCH-QQQltm0p6-hold-short | GEN | 37 | 2 | +7.4 | +5.7 | +0.168 (+0.191) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| ST7-rsi50dn-long-pm-t1s1-FD | other | 37 | 12 | +6.0 | +6.0 | +0.161 (+0.058) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| orb20_a | other | 37 | 17 | -4.5 | -4.5 | -0.121 (-0.296) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| NS4-pm-vwap-reclaim-oversold-short | other | 36 | 13 | -4.1 | -4.1 | -0.114 (-0.179) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| ST4-emadn-long-am-t1s05-FD | other | 35 | 11 | -2.4 | -3.7 | -0.108 (-0.460) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261026-06-NewLOD-SMA20slopelem0p28-LATE-SPYltm0p25-t1s1-long | GEN | 35 | 3 | +1.6 | +1.8 | +0.059 (-0.497) | -1.0R (global; <5 sess) | +4.2 | +0.0 |  | +0.0 | n | n |
| GEN-261027-06-ORBfailUp-BarsSinceLODle5-MID-BRoplt0p35-holdtr-long | GEN | 33 | 3 | -11.4 | -10.4 | -0.414 (-0.587) | -1.0R (global; <5 sess) | -1.4 | +6.4 |  | +5.0 | n | n |
| NS4-pm-vwap-reclaim-oversold-short-FD | other | 32 | 13 | +2.4 | +2.4 | +0.074 (-0.084) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261029-02-RSI2le0-VWAPcrossesge9-DayRngVsPrevle0p52-MID-BRvwlt0p4-hold-long | GEN | 32 | 5 | -7.2 | -7.2 | -0.226 (-0.264) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| NS5-sma50-flush-oversold-long | flush longs | 31 | 12 | -1.4 | +2.0 | +0.064 (-0.004) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261028-02-VWAPxDn-NewLOD-AM-QQQgt0p6-t1s1-long | GEN | 31 | 3 | -4.6 | -4.6 | -0.147 (-0.194) | -1.0R (global; <5 sess) | +0.4 | +0.0 |  | +0.0 | n | n |
| MF1-945-flowsell-vwapup | MF early sellers | 30 | 13 | -10.8 | -10.8 | -0.360 (-0.438) | -1.0R | +1.7 | +0.0 |  | +0.0 | n | n |
| GEN-261029-03-MACDhlem0p12-Ret5mlem0p062-Gapge2-PM-QQQup-hold-long | GEN | 30 | 3 | -0.4 | -0.7 | -0.025 (-0.088) | -1.0R (global; <5 sess) | -1.5 | +0.0 |  | +0.0 | n | n |
| GEN-261027-10-FlowShiftlem1p2-MACDhge0p079-SMA20dge0p59-LUNCH-BRopgt0p65-holdtr-long | GEN | 29 | 3 | -16.8 | -18.0 | -0.644 (-0.828) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| NM-MF3-qqqdn-gapdn-FD | MF early sellers | 26 | 5 | +8.0 | +8.0 | +0.308 (-0.464) | -1.0R | +1.7 | +1.1 | 1.00 | +1.4 | n | n |
| GEN-261019-03-Ret15mATRlem0p12-FromOpenATRlem0p34-SMA20slopege0p29-PM-BRoplt0p5-t05s1-long | GEN | 25 | 6 | +5.6 | +5.6 | +0.223 (-0.090) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261019-01-VWAPxUp-ATRdge3p6-FromPCATRlem0p68-OPEN-BRvwgt0p7-t05s05-long | GEN | 25 | 5 | -6.8 | -5.6 | -0.234 (-0.383) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| CWT13-vwapstretch-z075-short | other | 25 | 7 | -1.0 | -1.0 | -0.042 (-0.198) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261027-09-ORBfailDn-Gapge2-Slope6ge0p03-LAM-BRvwlt0p5-t05s05-short | GEN | 25 | 3 | -15.8 | -10.5 | -0.659 (-0.973) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261023-03-RSI5le13-VWAPatrlem0p34-OPEN-BRvwgt0p6-holdtr-short | GEN | 23 | 4 | -7.0 | -7.0 | -0.306 (-0.475) | -1.0R (global; <5 sess) | +2.2 | +0.0 |  | +0.0 | n | n |
| MF4-h40-open-flowsell | MF early sellers | 22 | 7 | +1.1 | +1.1 | +0.052 (-0.029) | -1.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| NS1-rsidip-rsi5pop-long | other | 22 | 10 | +1.5 | +1.5 | +0.069 (-0.094) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| ST8-volspikedn-long-pm-t1s1-FD | other | 22 | 10 | -4.5 | -4.5 | -0.206 (-0.330) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| CWT14-failbrk-pdl-p05-R2A-short | other | 22 | 2 | -3.6 | -3.6 | -0.165 (-0.238) | -1.0R (global; <5 sess) | -0.0 | +0.0 |  | +0.0 | n | n |
| GEN-261023-04-EMAdChglem0p028-PDHdistle0p074-EMAdifflem0p46-PM-QQQltm0p6-t1s1-long | GEN | 21 | 3 | -6.0 | -5.2 | -0.287 (-0.352) | -1.0R (global; <5 sess) | +0.0 | +2.5 |  | +3.0 | n | n |
| GEN-261022-04-RSI2le0-Eff6ge0p83-SMA20dge0p59-OPEN-BRvwlt0p5-t1s1-short | GEN | 21 | 4 | -16.0 | -16.0 | -0.761 (-0.836) | -1.0R (global; <5 sess) | +0.0 | +0.0 |  | +0.0 | n | n |
| CWT12-flag-s1-long | coils/flags | 21 | 12 | -2.9 | -2.9 | -0.136 (-0.223) | -1.8R | +1.1 | +0.0 |  | +0.0 | n | n |
| GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short | GEN | 21 | 5 | +8.0 | +8.0 | +0.379 (+0.129) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
| CWT05-flush-m075-v3-long | flush longs | 20 | 10 | -4.6 | -4.4 | -0.260 (-0.325) | -2.0R | +0.0 | +0.0 |  | +0.0 | n | n |
## (3) By family (A4: the family picks its best level on CHOOSE, scored on VALIDATE vs -2.0)
The requested families are first (fam5), then the latch_1103 prefix families (fam8). The "Setups up / down" column is the Remedies view: how many setups in the family improve or get worse on VALIDATE under the family's pick vs -2.0, and by how much.

| Scheme | Family | Setups | n live | R off | R -1.0 | R -1.5 | R -2.0 | R -2.5 | R -3.0 | Best (choose) | Choose gain | Validate gain (t) | Plateau | Setups up / down on validate (R) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fam5 | GEN | 85 | 2566 | -573 | -385 | -458 | -463 | -483 | -487 | -1.0R | +51.9 | +26.7 (1.95) | n | 8 (+39.2) / 3 (-12.6) |
| fam5 | MF early sellers | 11 | 939 | -130 | -100 | -114 | -113 | -96 | -98 | -2.5R | +13.0 | +3.7 (0.44) | y | 2 (+5.1) / 2 (-1.4) |
| fam5 | coils/flags | 3 | 945 | -88 | -69 | -71 | -63 | -58 | -54 | -1.0R | +7.5 | -14.3 (-1.07) | n | 0 (+0.0) / 1 (-14.3) |
| fam5 | flush longs | 6 | 194 | -38 | -33 | -37 | -39 | -40 | -40 | -1.0R | +4.1 | +2.1 (1.38) | y | 3 (+3.3) / 1 (-1.2) |
| fam5 | gap-down shorts | 15 | 1236 | +178 | +53 | +69 | +66 | +111 | +110 | off | +64.8 | +46.6 (2.14) | y | 5 (+48.2) / 2 (-1.5) |
| fam5 | other | 73 | 11704 | -2052 | -1012 | -1174 | -1238 | -1412 | -1429 | -1.0R | +126.0 | +100.1 (2.42) | y | 22 (+135.9) / 15 (-35.9) |
| fam8 | CWT | 31 | 8385 | -1480 | -773 | -849 | -912 | -999 | -1004 | -1.0R | +81.8 | +57.0 (1.57) | y | 14 (+108.2) / 6 (-51.2) |
| fam8 | GEN | 85 | 2566 | -573 | -385 | -458 | -463 | -483 | -487 | -1.0R | +51.9 | +26.7 (1.95) | n | 8 (+39.2) / 3 (-12.6) |
| fam8 | L3 | 5 | 433 | +47 | +29 | +59 | +60 | +69 | +69 | -1.25R | +1.3 | +0.9 (1.00) | n | 1 (+0.9) / 0 (+0.0) |
| fam8 | MF | 11 | 939 | -130 | -100 | -114 | -113 | -96 | -98 | -2.5R | +13.0 | +3.7 (0.44) | y | 2 (+5.1) / 2 (-1.4) |
| fam8 | NS | 11 | 795 | -144 | -81 | -118 | -118 | -122 | -121 | -1.0R | +28.4 | +7.7 (0.91) | n | 2 (+10.0) / 3 (-2.3) |
| fam8 | RW | 21 | 1744 | -31 | -29 | -44 | -46 | -63 | -68 | -2.25R | +24.0 | -22.2 (-0.87) | n | 3 (+4.7) / 3 (-26.9) |
| fam8 | ST | 11 | 441 | -59 | -50 | -53 | -51 | -56 | -56 | -1.0R | +1.0 | +0.3 (0.02) | n | 2 (+1.4) / 2 (-1.1) |
| fam8 | other | 18 | 2281 | -333 | -157 | -208 | -207 | -228 | -233 | -1.0R | +41.4 | +8.7 (0.42) | n | 4 (+15.8) / 4 (-7.1) |

- **Gap-down shorts** (RW1/3/3S/5/7, CWT09, NM gap-down shorts) are the only net-positive family: +178R with the stop off vs +66R at -2.0.
  - They pick **off** on CHOOSE: +65R choose and +47R validate (t 2.14), with a plateau (-2.25 .. -4.0 are all about +110R over the window). 5 setups improve and 2 get worse (-1.5R). The excess is positive (+59R choose, +55R validate), so this is not just trading a losing family more.
  - **One-big-day flag.** 10-22 carries 58% of the off-vs-(-2.0) delta (+65 of +112R): RW7-gapdn-bounce-early-short-FD in Testing 1, while T1 had the stop on. Without that day it is +46R, with 8 days up and 6 down. RW7-FD alone is +59R of the +112R.
  - It is under the 2.88 bar and needs more sessions. It is filed as a backlog idea: a forward shadow of "per-setup stop off for positive-expectancy gap-down shorts".
- **MF early sellers** pick -2.5 (+4R validate, t 0.44). **Coils/flags** pick -1.0 (-14R validate). **Flush longs** pick -1.0 (+2R). **GEN** picks -1.0 (+27R, t 1.95, no plateau). **Other**, which is mostly CWT14 failbrk and heat_fade, picks -1.0 (+100R, t 2.42), and its excess is near 0. All fail.
- **fam8:** RW picks -2.25 and gets -22R on validate. CWT picks -1.0 (+57R, t 1.57). L3, NS, ST, MF and other are all within ±10R.

## Remedies table: each level vs uniform -2.0, per setup (all 193 setups; `remedies_vs_m2.csv`)
| Level | Setups better | R gained | Setups worse | R lost | Worst setup | Net (all sessions) | Validate better / worse | Validate net |
|---|---|---|---|---|---|---|---|---|
| off | 28 | +184.1 | 54 | -1,037.0 | -143.2 | -852.9 | 19 / 38 | -459.0 |
| -1.0 | 69 | +416.1 | 30 | -111.9 | -33.0 | +304.2 | 41 / 27 | +110.1 |
| -1.25 | 31 | +139.2 | 22 | -43.4 | -9.6 | +95.8 | 16 / 17 | +11.9 |
| -1.5 | 21 | +103.9 | 19 | -38.9 | -9.9 | +65.0 | 12 / 12 | +14.6 |
| -1.6 | 19 | +90.3 | 19 | -32.8 | -9.9 | +57.5 | 10 / 12 | +11.1 |
| -1.75 | 17 | +66.8 | 17 | -21.2 | -5.7 | +45.6 | 8 / 10 | +13.8 |
| -1.8 | 15 | +63.5 | 18 | -25.3 | -6.8 | +38.2 | 5 / 10 | +8.0 |
| -2.01 | 1 | +6.8 | 3 | -8.7 | -4.3 | -1.9 | 0 / 1 | -4.3 |
| -2.25 | 27 | +101.8 | 37 | -200.0 | -26.9 | -98.1 | 15 / 26 | -90.6 |
| -2.5 | 33 | +144.9 | 39 | -273.5 | -24.5 | -128.6 | 18 / 27 | -79.7 |
| -3.0 | 35 | +169.7 | 37 | -318.1 | -37.5 | -148.4 | 19 / 26 | -100.6 |
| -4.0 | 32 | +156.2 | 46 | -434.8 | -51.1 | -278.6 | 16 / 37 | -169.0 |
| give-back 1.5 | 36 | +275.7 | 18 | -45.5 | -9.7 | +230.2 | 22 / 15 | +83.0 |
| give-back 2.0 | 25 | +165.0 | 15 | -27.7 | -5.4 | +137.3 | 19 / 13 | +49.1 |

Moving from -2.0 to -1.5..-1.8 changes 30-40 setups by a few R each, in both directions. Looser levels hurt about 1.4x as many setups as they help.

## Pass bars (PLAN): no grid-A candidate passes
| Candidate | 1 Sign (choose & validate) | 2 t >= 2.88 | 3 Plateau | 4 Excess > 0 | 5 w/o best day > 0 | Verdict |
|---|---|---|---|---|---|---|
| -1.0R (vs -2.0) | yes (+194 / +110) | **no (2.39)** | edge of grid (one neighbour, +12) | +2 / +6, about 0; 2y VALID -776 | yes (+69) | fail; the gain is from trading losing setups less |
| -1.25..-1.8 | yes | no (<= 0.67) | yes, flat | mixed (-35..+5) | about 0 | no change vs -2.0 (same plateau) |
| -2.01 | no | no | — | — | — | identical to -2.0 |
| -2.25..-4.0 | no (validate -80..-169) | — | — | — | — | worse |
| give-back 1.5R | yes (+147 / +83) | no (1.47) | yes (g2.0 +49) | validate -27 | yes (+36) | fail |
| A3 per-setup picks | choose +, validate -34 | no | — | — | no | fail |
| A4 family picks | best: gap-down shorts off +47 (t 2.14) | no | yes | yes (+59 choose / +55 validate) | yes (+46), but 58% one day | fail; backlog shadow |
| A2 realised + open | choose + / validate - | no | — | — | — | fail |

## Failures and caveats
- **Short window.** The longest per-setup history is 25 sessions, and validate is 6-10 sessions for most setups. Every per-setup t is <= 1.6.
- **What-ifs ignore other blocks.** Latch what-ifs do not check other skips (symbol already held, lot cap) that taking earlier trades would have triggered, so the "off" and looser levels are slightly optimistic.
  - The Graveyard's off sequence is 45% what-ifs (4,466).
  - What-if R uses backtest costs; live R uses pnl_adj.
- **Account halt.** Halt what-ifs (2,880) are excluded from the main run, because a per-setup level does not lift the account halt (A6a includes them; same answer).
- **The sim is a little stricter than live at -2.0** (Primary -62.3 vs -57.2R actual; Graveyard -619.7 vs -625.0R), because live exits are booked at reconciliation.
- **A2 coverage is biased.** Coverage is 35% of rows and favours small setup-days, because a day is dropped if any of its symbols has no bars.
- **The diagnostic was not pre-registered.** The split by the sign of each setup's own CHOOSE average R was added after the family table was read. It is reported only as context:
  - Negative-expectancy setups: -1.0 gives +101R on validate (t 2.47).
  - Positive ones: every level is within ±9R of -2.0, and off is -51R.
- **One-big-day.** At -2.0 the whole book's R without its best day is -1,893R vs -1,850R total. The gap-down-short family's off-vs-(-2.0) delta is flagged above: 58% of it is one day.

## Files
- `replay.py` runs A1/A3/A4/A5, A6a and the diagnostic, and A2 with `--a2`. `a2.py` is the 1-min open-R marking. `lab2y.py` is A6b.
- `out.txt` is the full printed output. `lab2y_out.txt` and `lab2y_expectancy.txt` hold the 2-year results.
- `A1_global_levels_vs_m2.csv`, `A1_global_levels_vs_off.csv`, `A1_global_levels_vs_baseline.csv`, `A1_by_account_vs_off.csv`
- `A2_realised_same_coverage.csv`, `A2_open_marked.csv`
- `A3_per_setup_all.csv` (193 setups; every level's choose/validate R in `c_*` / `v_*`) and `A3_per_setup_n20.csv`
- `A4_family.csv`, `remedies_vs_m2.csv`, `diag_by_expectancy.csv`, `A6_halt_included_vs_off.csv`, `A6_lab2y_levels.csv`
- `units_main.csv.gz` is per (account, setup, date) R and n at every level. `units_a2_*.csv.gz`, `units_lab2y.csv.gz`

*Educational only — not financial advice.*
