Educational only — not financial advice

**Owner summary**
- I tested 5 kinds of permanent RETIRED rule (25 threshold sets, each at Friday and at daily cadence = 50 configurations) on the live record, walk-forward. Each past review used only the trades known by that date.
- No rule would have retired a setup that later reached Primary, and none retired a setup whose whole record later turned positive. No rule touches Primary R. This is partly because the window is short: 7 weeks, and the first retirement was only possible on 11-02.
- Most rules pick setups that lose no faster afterwards than the other mature losers do. Their "R saved" mostly reflects that nearly every mature arena setup loses. Two exceptions: R3 at -0.10 (below), and R4-FRx3, which stands on only 2 sessions of data afterwards.
- Recommended: **RETIRE-R3**, applied at the Friday-after-close review only. Retire when trades ≥ 150, active days ≥ 15, avg R w/o best day ≤ -0.10, and total R over the last 10 active sessions ≤ 0. Keep the two Compass exemptions. Walk-forward it would have retired 26 setups (28 before the exemptions). Those setups later lost -0.129R per trade, against -0.073 for the mature setups it kept. 1 borderline wrongful kill, 0 graduates killed.
- Because Primary is the scoreboard, the real benefit is freed slots and buying power for low-rep setups, not "R saved". The R saved is research-arena spend.

## Method
- **Data.** `live_trades.pkl`: 28,097 closed live trades, 2026-10-06..11-19. R is after costs on the LR8 basis. Identical signals across accounts are counted once.
- **Review dates.**
  - Friday cadence: 10-09, 10-16, 10-23, 10-30, 11-06, 11-13. This matches how moves are actually made.
  - Daily cadence (each session close) is run as a sensitivity check.
  - A retirement takes effect from the next session.
- **Scope.**
  - Every non-Primary setup: Testing A-F, Gen, Graveyard, Explore1, Live Lab.
  - A setup counts as being in Primary between its first and last Primary trade, and is exempt during that time.
  - The decision uses the setup's whole live record (all accounts, deduplicated).
- **Statistics.**
  - avg R w/o best day: the best session by total R is removed.
  - Day t: the t-statistic of the per-day mean R, as in FOOTRACE.
  - UB95: trade mean + z × the day-clustered standard error.
- **Measures per retirement.**
  - Trades and R after the retirement date. "R saved" is minus that R; it is mostly Graveyard and testing spend.
  - Primary R after the date.
  - Saved R with the single largest-saving setup removed (the one-big-day check at setup level).
- **Discrimination null.** At the same review dates I took the average R per trade afterwards of eligible setups the rule did not retire (non-Primary, ≥ 15 days, ≥ 60 trades). A rule only discriminates if its retired setups do worse than that.
- **Wrongful kill.** Any of:
  - (a) the setup traded in Primary after its retirement date;
  - (b) its whole record at 11-19 has avg R w/o best day > 0;
  - (c) it made positive R afterwards on ≥ 10 trades (loose definition).
  - The strict version of (c) also requires avg R w/o best day afterwards > 0.

**Candidate rules**

| Family | Rule | Grid |
|---|---|---|
| R1 UB95 | n ≥ N, days ≥ 15, mean + z·SE_cluster < 0 | N 60/100/150 × z 1.645/1.96 |
| R2 hard floor (outsider) | n ≥ N, days ≥ 15, wo ≤ x, day t ≤ y | N 100/150 × x -0.05/-0.10 × y -2.0/-2.5 |
| R3 wo + last10 | n ≥ N, days ≥ 15, wo ≤ x, last-10-session R ≤ 0 | N 100/150 × x -0.10/-0.15 |
| R4 repeat FOOTRACE | the FOOTRACE-EXIT test holds at k Friday reviews | k 2/3 |
| R5 try-scaled | n ≥ N, days ≥ 15, wo ≤ 0, day t ≤ -c | N 30/60 × c sqrt(2 ln 220) = 3.28 / 2.5 |
| R6 composite | R2 (150, -0.10, -2.5) + days ≥ 20 + last10 ≤ 0, Compass exempt | 1 |

## Results (Friday cadence)

| Config | Retired | Trades after | R saved | Avg R after | Kept null avg | Saved w/o best setup | Pos after (loose) | Strict wrongful | Later Primary | Final positive |
|---|---|---|---|---|---|---|---|---|---|---|
| R1 z1.645 n60 | 27 | 4959 | 462.4 | -0.093 | -0.154 | 391.2 | 7 | 3 | 0 | 0 |
| R1 z1.96 n100 | 17 | 3996 | 387.1 | -0.097 | -0.143 | 315.9 | 4 | 1 | 0 | 0 |
| R1 z1.645 n150 | 23 | 4592 | 456.0 | -0.099 | -0.146 | 384.8 | 6 | 2 | 0 | 0 |
| R2 t-2.0 (all N/x) | 14 | 3349 | 383.9 | -0.115 | -0.117 | 301.5 | 2 | 0 | 0 | 0 |
| R2 t-2.5 (all N/x) | 11 | 2277 | 227.4 | -0.100 | -0.126 | 156.2 | 4 | 2 | 0 | 0 |
| **R3 n150 wo-0.10** | **28** | **6138** | **746.2** | **-0.122** | **-0.073** | **650.3** | 5 | 1 | 0 | 0 |
| R3 n100 wo-0.10 | 32 | 6456 | 822.8 | -0.127 | -0.053 | 726.9 | 6 | 1 | 0 | 0 |
| R3 n150 wo-0.15 | 24 | 4258 | 356.1 | -0.084 | -0.148 | 284.9 | 5 | 1 | 0 | 0 |
| R3 n100 wo-0.15 | 28 | 4576 | 432.7 | -0.095 | -0.146 | 361.5 | 6 | 1 | 0 | 0 |
| R4 FRx2 | 17 | 2347 | 227.6 | -0.097 | -0.121 | 145.2 | 6 | 3 | 0 | 0 |
| R4 FRx3 | 9 | 601 | 206.4 | -0.343 | -0.137 | 141.3 | 3 | 3 | 0 | 0 |
| R5 t3.28 | 3 | 524 | 9.8 | -0.019 | -0.144 | -15.1 | 2 | 2 | 0 | 0 |
| R5 t2.5 | 13 | 2324 | 230.8 | -0.099 | -0.129 | 159.6 | 4 | 2 | 0 | 0 |
| R6 composite | 9 | 1083 | 91.5 | -0.085 | -0.135 | 26.5 | 5 | 5 | 0 | 0 |

**Daily cadence.** It retires earlier and saves more R: R3 n150 wo-0.10 retires 34 setups and saves 855.6R; R2 t-2.5 saves 311.6R; R6 saves 132.0R with 0 strict wrongful kills. The wrongful-kill picture is the same: 0 later-Primary, 0 final-positive. I still recommend Friday cadence, because moves are made at the Friday review.

**What the table says**
- **Wrongful kills of Primary graduates: 0 in all 50 configurations.**
  - Every graduate in the window reached Primary before it had 15 active days, so no rule could have reached it: RW3/RW5 on 10-16, L3-fromopen on 10-21, ST7 on 10-28, NM-ETF on 11-12.
  - Hypothetical check on the current Primary setups as of 11-19: none meets R3, R2 or R6.
    - RW3: wo +0.048. RW5: wo +0.035. L3-fromopen: wo +0.148.
    - ST7 (58 trades) and NS5 (60 trades) are below the trade minimum.
- **Final-positive kills: 0 in all configurations.** No setup that met any rule finished 11-19 with avg R w/o best day > 0.
- **Loose wrongful kills are short big-day rebounds.**
  - NS2-sma50break-overbought-short-FD: +35.7R on 133 trades afterwards, but -0.096 avg w/o best day.
  - CWT13-vwapstretch-z05-long: +3.5R afterwards.
  - ST2-slope20up-long-am-t05s1-FD: +9.5R afterwards, -0.085 w/o best day.
  - exhaustion_short-FD: +6.8R afterwards, -0.024 w/o best day.
  - MF5-flowsell-vwapup-rsi5hi-FD: +11.4R on 29 trades over 4 days. This is R3's one strict wrongful kill.
  - In R2/R4/R6: CWT14-failbrk-pdh-p10-short (+13.7R on 43 trades over 2 days), heat_fade_short (+11.3R on 23 trades over 2 days), RW2-exhaustion-noon-adv150-short-FD (+10.3R on 16 trades over 2 days).
- **Discrimination.** Among Friday rules with more than one week of data afterwards, only R3 at wo -0.10 retires setups that do worse afterwards than the mature setups it keeps:
  - n150: -0.122 retired vs -0.073 kept. n100: -0.127 vs -0.053.
  - R1, R2, R5 and R6 retire setups that do no worse than the ones they keep.
  - R4-FRx3 shows the biggest gap (-0.343 vs -0.137), but on 601 trades over 2 sessions.
  - Plateau check: N = 100 and 150 agree. wo -0.15 does **not** agree (it retires different and fewer setups, and loses the edge). R3 is therefore sensitive to the wo threshold. That is a reason to adopt it conservatively and recheck it.
- **Saved R is concentrated.** In R3 n150 wo-0.10, the 11-02 batch (14 setups) accounts for -634R of the -746R. Later batches had only 2-7 sessions of data afterwards. CWT14 setups make up 11 of the 28 retirements.
- **The Compass exemptions conflict with R3.** R3 retires both owner Compass exemptions (CWT14-failbrk-orl-p05-long and heat_fade_short-FD). Removing them afterwards (a post-hoc step on the same results, not a separate run): 26 retired, 5,216 trades afterwards, -671.6R (-0.129 per trade), 575.8R saved without the largest-saving setup.

## Recommendation: RETIRE-R3 (a proposal for the owner; no config change made)
- **Rule.** At the Friday-after-close review, a non-Primary setup in Testing A-F, Gen, Graveyard, Explore1 or Live Lab becomes **RETIRED** (terminal) when all hold:
  - ≥ 150 live trades and ≥ 15 active days (whole record, identical signals once);
  - avg R w/o best day ≤ -0.10;
  - total R over its last 10 active sessions ≤ 0.
- **Exempt:**
  - the GY-LIFE Compass exemptions (CWT14-failbrk-orl-p05-long, heat_fade_short-FD);
  - any setup in Primary;
  - low-activity setups. They cannot reach 150 trades, so the 11-03 trim-to-testing rule is untouched.
- **Retirement is retirement of that exact setup only.** A pre-registered, mechanism-tagged tune is a new setup under the existing rules.
- **Why R3:**
  - It is the only rule family with real discrimination: -0.12 to -0.13 afterwards vs -0.05 to -0.07 for the kept mature setups.
  - It has 0 graduate kills and 0 final-positive kills.
  - It frees the most slots: 26-28 setups, about 6,100 trades of capacity over the window.
  - It fits "give rules a chance": 150 trades and 15 days is far above the guardrail against early-kill verdicts (15 days / 30 trades), and it acts only at the Friday review.
- **Cautions:**
  - The data window is 7 weeks, with only 2-12 sessions of data after each retirement.
  - The wo threshold is not a plateau (-0.15 breaks it), so keep -0.10 and recheck after 4 more Fridays with fresh data.
  - The value is capacity for low-rep setups, not Primary R. Primary R is unaffected (0.0 in every configuration).
  - Optional, untested: cap retirements per Friday (e.g. 4) for consistency.

## Rule-change context in the window (2026-10-06..11-19)
- All rows are re-costed to the LR8 basis (DQ-P3, 11-19).
- 11-12:
  - Gen and Graveyard buying power cut, slots raised to 300 (REPV).
  - Per-setup caps raised.
  - Arena and Gen daily halts raised to 300R.
  - These raise trades per day, so later retirements cover more trades.
- 11-12: Testing D/E/F filled.
- 11-17: TSZ1 half-size testing lots (R comparable, $ not); KILL-FLAT.
- 11-19: GY-LIFE archive rule.
- Many promotions, demotions and moves happened in the window, which is why Primary membership is taken from trade dates.
- FOOTRACE-EXIT is effective 11-20, after the window. R4 simulates it backwards.

## Configurations counted
- 25 rule configurations × 2 cadences = **50**, plus 1 post-hoc variant (R3 with the Compass exemptions removed).
- Not all 50 differ in practice:
  - The 8 R2 threshold sets collapse to 2 distinct results, because the trade and wo gates never bind once days ≥ 15 and t ≤ -2.5.
  - R5 n30 = n60.
- The discrimination null was computed for all 25 Friday configurations.

## Files
- Evaluation, one row per configuration and cadence, with wrongful kills named: /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/retire/retire_eval.csv
- Every retirement event (setup, dates, stats when retired, R afterwards, wrongful flags): /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/retire/retire_kills.csv
- Script: /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/retire/retire_study.py
  - Reads live_trades.pkl only; no market data, no MarcoFlow, no locked block.
  - Runs a full pass in about 5 minutes, most of it the null computation.
- Run log: /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/retire/run.log
- Scratch used: under 1 MB. Nothing committed.
