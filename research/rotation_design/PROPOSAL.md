# Testing rotation plan (ROT) — design proposal, 2026-11-11

*Educational only — not financial advice. Research and proposal only: **no config, setup, assignment or ledger change is made
here.** Nothing moves until the owner says yes, and any move is applied after the close (never 09:30-16:00 ET). All records are
live **paper** results (rule 7); R is after costs (`pnl_adj / (|entry − stop| × shares)`).*

Owner request (2026-11-10 ~21:40 ET): *"redo all testing accounts except for generator and graveyard so that there is a
continuous rotation of setups getting exposure. I'm not sure what the bars would be but we need to really separate the best
candidates for future primary promotion."* In scope: **Testing 1, Testing 2, Explore 1, Live Lab**. Gen and Graveyard are out.

Built on the **TEAM-6 state from Wed 11-11** (owner "Team yes"): MF2-FD, MF4-FD and L3-rsi5hi-FD go to Testing 1; MF4 and NS1 go to
Testing 2; NM-ETF goes from Live Lab to Primary. When this was written, that switch was not yet merged (assignments.json still showed
the 11-10 homes), so the TEAM-6 homes were applied here by hand.

## The short version (plain English)

1. **No setup in the four testing accounts is close to Primary today.** With 26 live sessions, none of the 72 setups passes the
   strict or balanced bar. The lenient bar lets in 2 as Candidates (RW1-FD and CWT09-vwaploss-g10), and none as On deck. **None of
   today's six Primary setups would pass the balanced On-deck bar either.** Our records are still too short to be sure of anything.
2. **The walk-forward check is sobering.** At 8 checkpoints (every 2 sessions from session 10), we compared setups that passed a
   bar with the rest of the pool over the next 5 sessions:
   - setups that passed the Candidate bar did better: balanced **+0.098R** per trade vs pool **−0.107R** (249 trades), lenient
     +0.042R vs −0.114R;
   - they beat the pool at 5 of the 7 balanced checkpoints that had any Candidates (and the lenient ones at 4 of 8),
     but lost at the two November checkpoints (11-04, 11-06);
   - **over the whole rest of the record, they did not stay ahead** (−0.158R vs −0.098R);
   - **lenient "On deck" was a false alarm 4 times out of 7** (next 5 sessions negative);
   - the owner's 10 real promotions since 10-16: **4 stayed positive afterwards and 6 turned negative.**
   So a bar on 2-4 weeks of live data separates setups only a little, and mostly in the short run. That is why the design leans on
   **more sessions per setup** (continuous exposure), **a Primary-rules replay**, and **a two-key promotion** (bar + owner yes),
   instead of a hair-trigger.
3. **Recommended design (ROT-A + BARS balanced + ROT-B):**
   - **Four tiers:** Reps (Explore 1 / Live Lab, under 20 trades or under 5 traded sessions) → Contender (Testing 1 / Testing 2)
     → Candidate → On deck → Primary.
   - **Experience is measured in traded sessions** (sessions with 1+ closed trade), then trades (owner input 21:55 ET, §2).
     Recommended Candidate minimum: **8 traded sessions / 30 trades** ("REPS-MIN 8/30"); On deck 15 / 60. The live history is
     too short to prove that pair (§2.2). Rotation priority goes to the setups with the fewest traded sessions.
   - **Down-moves:** each tier steps down after failing its bar at 2 re-tiers in a row. A Graveyard *proposal* comes at 40+ trades
     with clearly negative numbers (owner decides).
   - **Re-tier every 2 sessions after the close.** The nightly loop computes everything. Moves inside the testing pool are
     pre-approved by fixed rules (ROT-B, if the owner wants it). Graveyard moves and promotions to Primary always need an explicit yes.
   - **Migration (ROT-A):**
     - 4 setups that now have 20+ trades graduate from Explore 1 / Live Lab to Testing 1 / Testing 2;
     - the 2 setups that run as copies in both Testing 1 and Testing 2 (MF5, exhaustion_short-FD) get one home each;
     - Testing 1 and Testing 2 end up at 17 / 18 setups, Explore 1 / Live Lab at 19 / 18.
   - **Graveyard proposals (ROT-GY):** 4 more, alongside the pending RW3S-GY. All are owner decisions.
4. **Exposure is not limited by slots today.** Across the four accounts, 0% of signals were skipped because slots were full or a
   setup cap was hit. Testing 1's peak was 207 open of 400. Lost exposure comes from borrow, the split-tape short gate, spread/quote
   checks and same-symbol crowding inside a family. So the rotation guarantees exposure by **keeping every setup on every session**.
   Whole-session benching (owner rule) is used only where a family crowds itself out (25%+ of signals lost to a sibling) or where an
   account runs near full.

## Rule / config context inside the 10-06 → 11-10 window (owner rule 2026-11-02)
Records quoted here span changes in the rules. From `research/ledger.jsonl` (effective dates):
- **Primary:**
  - MF2-FD / MF4-FD / NS3-FD promoted 10-20/21; ST7-FD and CWT13-z05-long 10-26 (CWT13 demoted 10-27);
  - CWT14-p10-lowvol / NS4 / MF2 rotated out 10-28; L3 pair 10-30;
  - ~$4,000 lot 10-28; **−2R per-setup latch 10-29 (Primary only)**;
  - TEAM-6 from 11-11.
- **Testing:**
  - twin cap 10-20; per-setup −2R stop **off in Testing** from 10-23 (ST-A);
  - GX1 5-minute clock 10-27; **CF cost filter (0.15R) in T1/T2 from 10-30**;
  - **UNI1 top-500 pool in Testing 2 from 11-04**; ROLL1 (Explore 1 / Live Lab at ~$1,000 lots, 10 lots per setup, no scale-out)
    from 11-05;
  - EXPO1109 temporary GEN moves 11-09/11-10 (reverted 11-11).
- So a setup's record mixes accounts with different sizing, caps, universes and stop rules. The inventory shows a
  **Primary-rules proxy** column for that reason (§3.5).

## 1. Inventory — all 72 setups in T1 / T2 / Explore 1 / Live Lab after the TEAM-6 switch

**How to read the table:**
- **Source:** `inventory.py` on the 11-10 nightly journals (all 7 accounts, closed run_id=1 trades). Records are merged by setup id
  across accounts, as the dashboard does.
- **Shrunk** = avg R × n/(n+20) (dashboard ranking).
- **W/o best day** = avg R without the setup's best session, with that session's share of total R; **1 day** = 50% or more.
- **Day-t** = day-clustered t.
- **Ex-mkt** = BETA1 avg R with SPY's move taken out (merged scorecard sums).
- **Last-5 R** = avg R over the setup's last 5 traded sessions.
- **2y R:**
  - first choice: bt_lab1104 two-year lab, open part, locked block out, to 10-05;
  - else preval_1107, else the screen expectancy (validation.json / CWT scored / scorecard expectations);
  - for an -FD setup with no -FD list, the base setup's 2y.
- **Primary-rules R** = the record with Primary's −2R per-setup latch applied after the fact. This is a proxy: it ignores lot size
  and crowding. The Team engine gives the real replay.
- **Playing time** = cumulative scorecard playing time in the setup's accounts:
  - signals per session and entries per session, with the two-year lab expected rate in brackets;
  - the verdict (ok / slow / starved / silent / crowded-out / watch);
  - slots-full + setup-cap skips were **0% for every setup**, so they are not shown as a column.
- **Tier** = the balanced bar today (strict / lenient in brackets). `gy?` = meets the Graveyard-proposal floor; `ex-P` = ex-primary.

| Setup | Now | After ROT-A | Side | **Traded sessions** (of live sessions) / trades | Avg R | Shrunk | W/o best day (share) | Day-t | Ex-mkt | Last-5 R (n) | 2y R | Primary-rules R | Signals / entries per session (expected) | Playing time | Tier balanced (strict / lenient) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD` ex-P | T1 | T1 | short | **22** (22) / 158 | -0.231 | -0.205 | -0.278 | -1.62 | -0.184 | -0.549 (78) | -0.085 | -0.245 | 15.5 / 6.87 (16.45) | crowded-out/ok | gy? (gy? / gy?) |
| Gap-Down Early Bounce Short (all day) `RW7-gapdn-bounce-early-short-FD` | T1 | T1 | short | **20** (22) / 493 | -0.004 | -0.004 | -0.036 | -0.04 | -0.089 | -0.003 (164) | -0.060 | -0.012 | 45.1 / 22.41 (59.92) | ok | pool (pool / pool) |
| Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD` ex-P | T1 | T1 | short | **20** (22) / 134 | +0.055 | +0.048 | -0.197 (396%, **1 day**) | +0.18 | -0.120 | -0.557 (67) | -0.088 | -0.008 | 12.5 / 5.83 (10.09) | ok | pool (pool / pool) |
| Afternoon Blow-off Short `exhaustion_short` | T1 | T1 | short | **20** (26) / 112 | -0.087 | -0.074 | -0.204 | -0.57 | -0.109 | -0.202 (36) | -0.020 | -0.101 | 8.3 / 4.31 (12.12) | ok | pool (pool / pool) |
| Index Last-Half-Hour Momentum `intraday_momentum` | T1 | T1 | both | **20** (21) / 52 | -0.352 | -0.254 | -0.381 | -3.03 | -0.347 | -0.513 (18) | -0.091 | -0.352 | 2.1 / 2.08 (2.37) | silent/slow | gy? (gy? / gy?) |
| NS1-rsidip-rsi5pop-long-FD `NS1-rsidip-rsi5pop-long-FD` | T1 | T1 | long | **19** (22) / 90 | -0.074 | -0.061 | -0.151 | -1.04 | -0.112 | -0.017 (45) | -0.071 | -0.079 | 5.8 / 4.09 (5.39) | ok | pool (pool / pool) |
| Gap-Down Rebound Overbought Short (all day) `L3-gap-slope-rsi5hi-FD` ex-P | T1 | T1 | short | **18** (21) / 98 | +0.032 | +0.027 | -0.061 (254%, **1 day**) | +0.24 | -0.040 | -0.437 (19) | -0.040 | +0.037 | 42.8 / 4.45 (13.41) | ok/slow | pool (pool / pool) |
| 20-Minute Opening Range Breakout `orb20_a` | T1 | T1 | both | **18** (26) / 40 | -0.029 | -0.019 | -0.172 | -0.14 | +0.019 | +0.222 (10) | -0.040 | -0.029 | 4.0 / 1.50 (6.79) | slow/starved | pool (pool / pool) |
| Panic Flush Reversal (3x volume) `CWT05-flush-m05-v3-long` | T1 | T1 | long | **16** (22) / 70 | -0.124 | -0.096 | -0.185 | -0.91 | -0.022 | -0.159 (34) | -0.130 | -0.153 | 5.6 / 3.14 (0.00) | ok/slow | pool (pool / pool) |
| L3-gap-slope-lowdist-FD `L3-gap-slope-lowdist-FD` | T1 | T1 | short | **15** (21) / 73 | +0.077 | +0.060 | -0.060 (166%, **1 day**) | +0.47 | -0.096 | +0.108 (24) | -0.127 | +0.077 | 17.0 / 3.32 (9.76) | ok | pool (pool / pool) |
| NS4-pm-vwap-reclaim-oversold-short-FD `NS4-pm-vwap-reclaim-oversold-short-FD` | T1 | T1 | short | **14** (20) / 33 | +0.042 | +0.026 | -0.115 (332%, **1 day**) | +0.22 | -0.090 | -0.562 (8) | -0.119 | +0.042 | 3.9 / 1.50 (3.57) | slow | pool (pool / pool) |
| Early Sellers Above VWAP `MF1-945-flowsell-vwapup` ex-P | T1 | T1 | short | **13** (24) / 30 | -0.360 | -0.216 | -0.438 | -1.58 | -0.236 | -0.982 (7) | -0.050 | -0.360 | 4.5 / 1.20 (5.33) | slow/starved | pool (pool / pool) |
| Big Loser VWAP Reclaim Fade `NS3-failed-vwap-reclaim-short` | T1 | T1 | short | **10** (23) / 67 | -0.229 | -0.176 | -0.403 | -1.48 | -0.202 | -0.423 (22) | -0.136 | -0.271 | 5.6 / 2.68 (3.03) | slow | gy? (gy? / gy?) |
| Early Sellers into a Pop `MF3-open-flowsell-rsi5hi` ex-P | T1 | T1 | short | **10** (24) / 44 | -0.015 | -0.011 | -0.116 | -0.09 | -0.038 | -0.051 (24) | -0.034 | -0.015 | 6.5 / 1.76 (9.19) | crowded-out | pool (pool / pool) |
| Sellers into Strength (all day) `MF5-flowsell-vwapup-rsi5hi` | T1+T2 | T2 | short | **23** (24) / 99 | -0.084 | -0.070 | -0.185 | -0.64 | -0.052 | -0.005 (18) | -0.010 | -0.063 | 6.1 / 2.48 (15.47) | crowded-out/starved | pool (pool / pool) |
| exhaustion_short-FD `exhaustion_short-FD` | T1+T2 | T2 | short | **20** (22) / 175 | -0.061 | -0.055 | -0.137 | -0.50 | -0.197 | -0.081 (32) | -0.067 | -0.056 | 11.2 / 4.73 (64.64) | starved | pool (pool / pool) |
| Failed Prior-Day-Low Break Long `CWT14-failbrk-pdl-p10-long` | T2 | T2 | long | **22** (22) / 562 | -0.087 | -0.084 | -0.120 | -1.11 | -0.064 | -0.225 (120) | -0.088 | -0.043 | 41.2 / 25.55 (0.00) | ok | pool (pool / pool) |
| Failed Prior-Day-Low Break Long (0.1 ATR, low volume) [fill] `CWT14-failbrk-pdl-p10-lowvol-long` ex-P | T2 | T2 | long | **22** (22) / 315 | -0.077 | -0.072 | -0.097 | -1.32 | -0.068 | -0.237 (70) | -0.090 | -0.026 | 22.3 / 14.32 (0.00) | ok | pool (pool / pool) |
| Gap-Down Bounce Short, Heavy Selling (all day) `RW1-gapdn-bounce-flowsell-short-FD` | T2 | T2 | short | **21** (22) / 116 | +0.078 | +0.066 | +0.036 (59%, **1 day**) | +0.76 | -0.086 | +0.193 (32) | -0.047 | +0.084 | 9.3 / 5.27 (17.10) | ok | pool (pool / cand) |
| Stretched Below VWAP Bounce `CWT13-vwapstretch-z05-long` ex-P | T2 | T2 | long | **20** (22) / 275 | -0.147 | -0.137 | -0.189 | -1.45 | -0.006 | -0.203 (124) | -0.080 | -0.218 | 24.5 / 12.50 (0.00) | ok | gy? (gy? / gy?) |
| Afternoon VWAP Reclaim Fade `NS4-pm-vwap-reclaim-oversold-short` ex-P | T2 | T2 | short | **13** (24) / 36 | -0.114 | -0.073 | -0.179 | -0.62 | -0.117 | -0.288 (16) | -0.080 | -0.114 | 2.4 / 1.44 (3.05) | slow/watch | pool (pool / pool) |
| Big Gainer Dip-and-Pop `NS1-rsidip-rsi5pop-long` ex-P | T2 | T2 | long | **11** (23) / 26 | +0.049 | +0.028 | -0.087 (237%, **1 day**) | +0.34 | +0.060 | -0.067 (14) | +0.028 | +0.049 | 1.4 / 1.04 (0.92) | ok/slow | pool (pool / pool) |
| Afternoon Higher-Low Long (near-miss) `NM-HL-T75-pm-long` | T2 | T2 | long | **10** (17) / 52 | -0.002 | -0.002 | -0.071 | -0.01 | +0.072 | -0.069 (40) | +0.044 | +0.230 | 3.6 / 3.06 (0.00) | ok | pool (pool / pool) |
| Gap-Down Capitulation Buy (near-miss) `NM-AR-AM-gapdown-capitulation-long` | T2 | T2 | long | **9** (15) / 58 | -0.460 | -0.342 | -0.598 | -2.27 | -0.448 | -0.564 (20) | +0.257 | -0.460 | 5.2 / 3.41 (0.00) | ok | gy? (gy? / gy?) |
| Stretched Above VWAP Fade (far) `CWT13-vwapstretch-z075-short` | T2 | T2 | short | **7** (19) / 25 | -0.042 | -0.023 | -0.198 | -0.27 | -0.034 | +0.031 (22) | -0.081 | -0.042 | 2.1 / 1.14 (0.00) | slow | pool (pool / pool) |
| Early Sellers, Strong Heat `MF4-h40-open-flowsell` ex-P | T2 | T2 | short | **7** (24) / 22 | +0.052 | +0.027 | -0.029 (148%, **1 day**) | +0.32 | +0.061 | +0.258 (15) | -0.099 | +0.052 | 6.0 / 0.88 (7.24) | crowded-out/watch | pool (pool / pool) |
| Gap-Down Heavy-Selling Short, no RSI condition (all day) `RW3S-gapdn-flowsell-short-FD` | T2 | T2 | short | **6** (6) / 204 | -0.281 | -0.256 | -0.291 | -1.88 | -0.175 | -0.312 (180) | -0.054 | -0.387 | 71.0 / 34.00 (0.00) | ok | gy? (gy? / gy?) |
| Big Loser VWAP Reclaim Fade, Morning, Wide Stop `NS3V1-am-widestop-short` | T2 | T2 | short | **6** (10) / 42 | -0.276 | -0.187 | -0.509 | -0.90 | -0.363 | +0.022 (29) | +0.009 | -0.276 | 7.2 / 3.23 (5.30) | ok | pool (pool / pool) |
| Early Sellers into a Pop (index down, no gap up) (near-miss) `NM-MF3-qqqdn-gapdn-FD` | T2 | T2 | short | **6** (14) / 34 | +0.098 | +0.062 | -0.524 (351%, **1 day**) | +0.23 | +0.001 | -0.524 (16) | -0.010 | +0.098 | 3.9 / 2.27 (4.90) | slow | pool (pool / pool) |
| Failed Prior-Day-Low Break, SPY-Range Regime (long leg) `CWT14-failbrk-pdl-p05-R2A-long` | T2 | T2 | long | **5** (7) / 136 | -0.091 | -0.080 | -0.110 | -1.48 | +0.020 | -0.091 (136) | – | -0.091 | 28.7 / 19.43 (0.00) | ok | pool (pool / pool) |
| Failed Prior-Day-Low Break, SPY-Range Regime (short leg) `CWT14-failbrk-pdl-p05-R2A-short` | T2 | T2 | short | **2** (5) / 22 | -0.165 | -0.087 | -0.238 | – | -0.085 | -0.165 (22) | – | -0.165 | 7.7 / 3.14 (0.00) | crowded-out | pool (pool / pool) |
| ST8-volspikedn-long-pm-t1s1-FD `ST8-volspikedn-long-pm-t1s1-FD` | EX1 | T1 | long | **11** (22) / 25 | -0.150 | -0.083 | -0.253 | -0.56 | +0.007 | -0.378 (15) | – | -0.150 | 1.6 / 1.14 (1.05) | ok/slow | pool (pool / pool) |
| Stretched Below VWAP Bounce (far) `CWT13-vwapstretch-z075-long` | EX1 | T1 | long | **9** (21) / 40 | -0.088 | -0.059 | -0.175 | -0.29 | +0.198 | -0.157 (32) | -0.046 | +0.252 | 7.7 / 1.82 (0.00) | ok/slow | pool (pool / pool) |
| Panic Flush Reversal (5x volume) `CWT05-flush-m05-v5-long` | EX1 | EX1 | long | **8** (21) / 14 | +0.006 | +0.003 | -0.139 (1901%, **1 day**) | +0.02 | +0.116 | +0.153 (8) | -0.111 | +0.006 | 1.0 / 0.64 (0.00) | slow | pool (pool / pool) |
| Gap-Down Bounce Rejection Short (10% gap) `CWT09-gapdn-bounce-g10-lowerhalf-short` | EX1 | EX1 | short | **7** (22) / 19 | +0.087 | +0.043 | -0.158 (243%, **1 day**) | +0.30 | -0.106 | +0.163 (16) | +0.141 | +0.087 | 8.9 / 0.86 (0.00) | slow | pool (pool / pool) |
| Early Sellers, Mid-High RSI `MF2-open-rsimidhi-flowsell` | EX1 | EX1 | short | **6** (24) / 16 | -0.493 | -0.219 | -0.453 | -10.75 | -0.580 | -0.451 (15) | +0.046 | -0.493 | 2.8 / 0.64 (1.30) | slow/starved | pool (pool / pool) |
| Early NS3 Short While SPY Up (near-miss) `NM-RWN3-ns3-spyup-early-short` | EX1 | EX1 | short | **5** (17) / 12 | +0.279 | +0.105 | -0.450 (181%, **1 day**) | +0.47 | -0.206 | +0.279 (12) | – | +0.279 | 2.2 / 0.71 (0.00) | slow | pool (pool / pool) |
| RSI Collapse Dip Buy, Nasdaq-below-VWAP only (all day) `ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD` | EX1 | EX1 | long | **5** (10) / 9 | +0.133 | +0.041 | -0.181 (191%, **1 day**) | +0.41 | +0.348 | +0.133 (9) | – | +0.133 | 1.8 / 0.69 (1.25) | slow | pool (pool / pool) |
| NS2 Up-3 Short, QQQ Up, Slope Down (near-miss) `NM-RWR4-ns2-up3-qqqup-slopedn-short` | EX1 | EX1 | short | **3** (12) / 8 | -0.205 | -0.059 | -0.369 | -0.70 | -0.759 | -0.205 (8) | – | -0.205 | 0.8 / 0.47 (0.00) | slow | pool (pool / pool) |
| Gap-Down VWAP Loss Short, Slope Filter (near-miss) `NM1-cwt09-g10-vwaploss-short` | EX1 | EX1 | short | **3** (12) / 5 | +0.274 | +0.055 | -0.059 (113%, **1 day**) | +0.65 | +0.174 | +0.274 (5) | – | +0.274 | 5.6 / 0.29 (0.00) | slow | pool (pool / pool) |
| Backside Lower-High Short `CWT04-backside-lh-a15-short` | EX1 | EX1 | short | **3** (22) / 4 | -0.079 | -0.013 | -0.318 | -0.27 | – | -0.079 (4) | +0.142 | -0.079 | 0.5 / 0.18 (0.00) | slow | pool (pool / pool) |
| Monday Weak-RS NS3 Short (near-miss) `NM-RWN5-ns3-mon-weakrs-short` | EX1 | EX1 | short | **2** (17) / 7 | +0.479 | +0.124 | +0.832 (50%, **1 day**) | – | +0.103 | +0.479 (7) | – | +0.479 | 1.2 / 0.41 (0.00) | slow | pool (pool / pool) |
| Big Gainer Fade with VWAP Band Guard `RW6G1-ns2-up3-vwap2sd-short` | EX1 | EX1 | short | **2** (19) / 4 | -0.718 | -0.120 | -1.069 | – | – | -0.718 (4) | – | -0.718 | 0.3 / 0.17 (0.40) | slow/starved | pool (pool / pool) |
| Quiet Downtrend Bounce Short (near-miss) `NM-AMS-N1-quiet-morning-short` | EX1 | EX1 | short | **2** (9) / 2 | -1.123 | -0.102 | -1.150 | – | – | -1.123 (2) | – | -1.123 | 0.4 / 0.12 (0.00) | slow | pool (pool / pool) |
| * Oversold Pop with Breadth Turning Up (near-miss) `LD1-ns1-breadthup-t05s1-long` | EX1 | EX1 | long | **1** (1) / 1 | -0.993 | -0.047 | – | – | – | -0.993 (1) | – | -0.993 | 0.1 / 0.07 (0.00) | silent/slow | pool (pool / pool) |
| Backside VWAP-Test Short (big runner) `CWT04-backside-vwaptest-a25-short` | EX1 | EX1 | short | **0** (0) / 0 | – | – | – | – | – | – (0) | -0.171 | – | 0.1 / 0.00 (0.00) | silent/slow | pool (pool / pool) |
| Index Dip Bounce 1 TQQQ (hold) `IDX1-qqq100-0955-TQQQ-hold` | EX1 | EX1 | ? | **0** (0) / 0 | – | – | – | – | – | – (0) | – | – | 0.0 / 0.00 (0.00) | silent | pool (pool / pool) |
| Index Dip Bounce 2 3x S&P `IDX2-spy075-0945-3x-trail` | EX1 | EX1 | ? | **0** (0) / 0 | – | – | – | – | – | – (0) | – | – | 0.0 / 0.00 (0.00) | silent | pool (pool / pool) |
| Index Dip Bounce 5 3x S&P `IDX5-spy050-0945-3x-trail` | EX1 | EX1 | ? | **0** (0) / 0 | – | – | – | – | – | – (0) | – | – | 0.0 / 0.00 (0.00) | silent | pool (pool / pool) |
| * Oversold Slope Turn after an SPY Dip-Turn (near-miss) `LD3-st2-idxturn-t05s1-long` | EX1 | EX1 | long | **0** (0) / 0 | – | – | – | – | – | – (0) | – | – | 0.1 / 0.00 (0.00) | silent/slow | pool (pool / pool) |
| * Oversold EMA Cross-Down with Breadth Turning Up (near-miss) `LD4-st4-breadthup-t1s05-long` | EX1 | EX1 | long | **0** (0) / 0 | – | – | – | – | – | – (0) | – | – | 0.0 / 0.00 (0.00) | silent | pool (pool / pool) |
| * SPY Dip of 0.30%, Breadth Turn (SPXL, trailing) (near-miss) `LD8-spy-dip030-breadthturn-spxl-holdtr-long` | EX1 | EX1 | long | **0** (0) / 0 | – | – | – | – | – | – (0) | – | – | 0.0 / 0.00 (0.00) | silent | pool (pool / pool) |
| Spike-Pullback Flag Breakout `CWT12-flag-s1-long` | LL | T1 | long | **13** (21) / 22 | -0.093 | -0.049 | -0.168 | -0.51 | -0.082 | +0.163 (7) | -0.074 | -0.047 | 1.4 / 1.00 (0.00) | slow | pool (pool / pool) |
| Panic Flush Reversal (deep, 3x volume) `CWT05-flush-m075-v3-long` | LL | T2 | long | **11** (22) / 23 | -0.153 | -0.082 | -0.232 | -0.72 | +0.056 | -0.395 (13) | -0.154 | -0.166 | 1.7 / 1.05 (0.00) | slow | pool (pool / pool) |
| Gap-Down VWAP Loss Short (10% gap) `CWT09-gapdn-vwaploss-g10-short` | LL | LL | short | **8** (21) / 15 | +0.327 | +0.140 | +0.227 (54%, **1 day**) | +1.35 | +0.272 | +0.390 (11) | +0.041 | +0.327 | 9.6 / 0.68 (0.00) | slow | pool (pool / cand) |
| ST6-volspikeup-short-mid-t1s1-FD `ST6-volspikeup-short-mid-t1s1-FD` | LL | LL | short | **6** (21) / 15 | -0.029 | -0.012 | -0.112 | -0.11 | -0.172 | -0.112 (13) | – | -0.029 | 2.1 / 0.68 (1.24) | slow | pool (pool / pool) |
| Backside VWAP-Test Short `CWT04-backside-vwaptest-a15-short` | LL | LL | short | **5** (19) / 8 | -0.690 | -0.197 | -1.247 | -2.24 | -0.467 | -0.690 (8) | -0.172 | -0.690 | 1.0 / 0.36 (0.00) | slow | pool (pool / pool) |
| * Shallow Nasdaq Dip, Breadth Turn (TQQQ) (near-miss) `LD2-qqq-dip015-breadthturn-tqqq-t05s1-long` | LL | LL | long | **5** (11) / 5 | -0.324 | -0.065 | -0.666 | -0.75 | -0.123 | -0.324 (5) | – | -0.324 | 0.3 / 0.33 (0.00) | slow | pool (pool / pool) |
| Early NS3 Short While QQQ Up (near-miss) `NM-RWR3-ns3-qqqup-early-short` | LL | LL | short | **4** (17) / 7 | +0.404 | +0.105 | -0.155 (122%, **1 day**) | +0.71 | -0.273 | +0.404 (7) | – | +0.404 | 1.5 / 0.41 (0.00) | slow | pool (pool / pool) |
| ST5-pdbrkup-short-mid-t05s1-FD `ST5-pdbrkup-short-mid-t05s1-FD` | LL | LL | short | **4** (21) / 5 | +0.888 | +0.178 | +0.270 (76%, **1 day**) | +1.46 | +1.346 | +0.888 (5) | – | +0.888 | 1.5 / 0.23 (0.78) | slow/starved | pool (pool / pool) |
| ST3-rsi5up-short-pm-t1s1-FD `ST3-rsi5up-short-pm-t1s1-FD` | LL | LL | short | **4** (14) / 4 | +0.002 | +0.000 | -0.306 (15710%, **1 day**) | +0.00 | – | +0.002 (4) | – | +0.002 | 1.6 / 0.18 (1.35) | slow/starved | pool (pool / pool) |
| Panic Flush Reversal (deep, 5x volume) `CWT05-flush-m075-v5-long` | LL | LL | long | **3** (21) / 5 | -0.343 | -0.069 | -0.617 | -0.86 | +0.071 | -0.343 (5) | -0.088 | -0.343 | 0.5 / 0.23 (0.00) | slow | pool (pool / pool) |
| Gap-Down Reclaim Fade, Afternoon (near-miss) `NM-PM-gapdn-above-pdh-rvol-short` | LL | LL | short | **3** (14) / 3 | +0.573 | +0.075 | +0.388 (55%, **1 day**) | +2.18 | – | +0.573 (3) | – | +0.573 | 0.2 / 0.18 (0.00) | slow | pool (pool / pool) |
| Prior-Day Low Sweep Reversal to VWAP `LIQ-pdl-sweep-open15-vwap-long` | LL | LL | long | **2** (18) / 3 | -0.771 | -0.101 | -0.607 | – | – | -0.771 (3) | – | -0.771 | 0.1 / 0.14 (0.38) | slow/starved | pool (pool / pool) |
| * SPY Dip of 0.2 ATR, Breadth Turn (SPXL, trailing) (near-miss) `LD6-spy-dip020atr-breadthturn-spxl-holdtr-long` | LL | LL | long | **2** (11) / 2 | +0.877 | +0.080 | +0.272 (84%, **1 day**) | – | – | +0.877 (2) | – | +0.877 | 0.1 / 0.13 (0.00) | silent/slow | pool (pool / pool) |
| NS2 Short, SPY Up 0.5%, Not Friday (near-miss) `NM-RWN4-ns2-spyup05-notfri-short` | LL | LL | short | **1** (12) / 8 | -0.043 | -0.012 | – | – | -0.640 | -0.043 (8) | – | -0.226 | 0.6 / 0.47 (0.00) | silent/slow | pool (pool / pool) |
| * Oversold Pop after an SPY Dip-Turn (trailing) (near-miss) `LD7-ns1-idxturn-holdtr-long` | LL | LL | long | **1** (11) / 1 | +0.006 | +0.000 | – | – | – | +0.006 (1) | – | +0.006 | 0.1 / 0.07 (0.00) | silent/slow | pool (pool / pool) |
| Afternoon Exhaustion Short, Gap-Down, SPY Up (near-miss) `NM-RWR1-exh150-gapdn-spyup-pm-short` | LL | LL | short | **1** (5) / 1 | +0.551 | +0.026 | – | – | – | +0.551 (1) | – | +0.551 | 0.1 / 0.06 (0.00) | silent/slow | pool (pool / pool) |
| Backside Lower-High Short (big runner) `CWT04-backside-lh-a25-short` | LL | LL | short | **0** (0) / 0 | – | – | – | – | – | – (0) | +0.186 | – | 0.0 / 0.00 (0.00) | silent/slow | pool (pool / pool) |
| Index Dip Bounce 1 TQQQ `IDX1-qqq100-0955-TQQQ-trail` | LL | LL | ? | **0** (0) / 0 | – | – | – | – | – | – (0) | – | – | 0.0 / 0.00 (0.00) | silent | pool (pool / pool) |
| Index Dip Bounce 3 3x S&P `IDX3-spy075-0955-3x-trail` | LL | LL | ? | **0** (0) / 0 | – | – | – | – | – | – (0) | – | – | 0.0 / 0.00 (0.00) | silent | pool (pool / pool) |
| * Oversold Slope Turn with Breadth Turning Up (near-miss) `LD5-st2-breadthup-t05s1-long` | LL | LL | long | **0** (0) / 0 | – | – | – | – | – | – (0) | – | – | 0.1 / 0.00 (0.00) | silent/slow | pool (pool / pool) |

**Inventory takeaways:**
- **Testing 1 / Testing 2 (33 setups after TEAM-6):** every one has 20+ trades.
  - 8 have a positive avg R: RW1-FD, NM-MF3-FD, L3-lowdist-FD, MF2-FD, MF4, NS1, L3-rsi5hi-FD, NS4-FD.
  - Only **RW1-FD** is still positive without its best day (+0.036R), but its ex-market R is −0.086.
- **Explore 1 / Live Lab (39 setups after NM-ETF leaves):** 37 have fewer than 20 trades, and 11 have none.
  - The 11 with no trades are the IDX / LD index-gated longs, which wait for a specific index dip. They are "dormant" under rule 21.
  - The best low-rep records are CWT09-vwaploss-g10 (15 trades, +0.327R, +0.227R w/o best day, ex-market +0.272) and
    ST5-pdbrkup-FD (5, +0.888R). These are tiny samples.
- **Starvation is not from slots:**
  - slots-full + setup-cap skips are 0% of signals for all 72 setups;
  - the "starved" verdicts (MF1, MF5, exhaustion_short-FD, orb20_a, LIQ, ST3, ST5, RW6G1) come from borrow / split-tape gate /
    spread checks and the live-vs-lab rate gap (LAB-RATE-PARITY);
  - the "crowded-out" ones (MF3, MF4, MF5, CWT14-R2A-short) lose signals to **their own family**.

## 2. Experience = traded sessions (owner input 2026-11-10 ~21:55 ET)

> "organize setups to be tested by traded sessions — not session counts but actual sessions where setups have been traded in —
> then maybe trade count; unsure what figure makes sense."

**Definition.** A **traded session** is a session in which the setup has at least 1 closed live trade, in any account. Sessions
where it was benched, had no signal, or had every signal skipped do **not** count. Traded sessions are the primary experience
measure everywhere in this design: the inventory, tiers, bars, rotation priority and the dashboard. Trade count comes second.

### 2.1 Why the session, not the trade, is the unit (variance)
- Trades on the same day move together: same tape, same flip, same latch. So day-level R is the noisy unit.
- `minimums.py` compares two standard errors of avg R for the 56 non-GEN setups with 40+ trades and 8+ traded sessions:
  clustered by day, and treating every trade as independent.
- **The median design effect is 3.8.** In other words, a typical setup's trades carry about a quarter of the information they
  seem to.

| setup | trades | traded sessions | trades / session | design effect | effective trades | best day share |
|---|---|---|---|---|---|---|
| RW3-FD (Primary) | 140 | 21 | 6.7 | **8.5** | 17 | 59% |
| L3-gap-slope-fromopen-FD (Primary) | 285 | 19 | 15.0 | **7.4** | 38 | 69% |
| RW7-gapdn-bounce-early-short-FD (T1) | 493 | 20 | 24.7 | 4.8 | 102 | – (total < 0) |
| CWT14-failbrk-pdl-p10-long (T2) | 562 | 22 | 25.5 | 4.8 | 118 | – |
| RW1-FD (T2) | 116 | 21 | 5.5 | 1.6 | 74 | 60% |
| NS1-FD (T1) | 90 | 19 | 4.7 | 1.3 | 69 | – |

- L3-fromopen's 285 trades are worth about **38 independent trades**, because 69% of its R came on one day (10-20). The owner's
  77% figure is from a different cut; this record, after costs, gives 69%.
- RW1-FD's 116 trades are worth 74, because its days are less alike.
- So a trade-count bar alone flatters setups that pile many trades into one day. The traded-session bar does not.

### 2.2 Which minimum makes the record predictive? (20 pairs tested)
**Method:**
- **Grid:** traded sessions S ∈ {5, 8, 10, 15, 20} × trades N ∈ {15, 20, 30, 50}, giving **20 configurations**, all reported.
- **Sample:** every non-GEN setup with a live record, from any account.
- **Date D:** the session on which the setup first has at least S traded sessions *and* at least N trades. Only its record so far
  (up to D) is used.
- **Forward test:** its avg R over its **next 5 traded sessions**; a setup needs at least 3 of them to be scored.
- **Measures:**
  - Pearson correlation, with a permutation p-value from 2,000 shuffles;
  - sign hit rate;
  - the share of setups that were positive at D and stayed positive;
  - the forward avg R of setups that were positive at D vs negative at D.
- **Base rate:** only about 30% of setups are positive over their next 5 traded sessions. So "predict negative" alone scores a hit
  rate of about 70%. The hit rate must be read against that base rate.

| S / N | reached | scored | corr (perm p) | sign hit | base: fwd > 0 | positive at D → still positive | fwd avg R: positive at D vs negative at D | median live sessions to reach |
|---|---|---|---|---|---|---|---|---|
| 5 / 15 | 77 | 64 | **+0.24 (0.02)** | 0.64 | 0.33 | 9 of 20 (45%) | −0.010 vs −0.128 | 6 |
| 5 / 20 | 72 | 62 | **+0.27 (0.02)** | 0.63 | 0.32 | 8 of 19 (42%) | −0.029 vs −0.142 | 6 |
| 5 / 30 | 66 | 54 | **+0.28 (0.02)** | 0.63 | 0.33 | 6 of 14 (43%) | −0.034 vs −0.106 | 6 |
| 5 / 50 | 55 | 48 | +0.11 (0.22) | 0.69 | 0.38 | 8 of 13 (62%) | +0.034 vs −0.103 | 8 |
| 8 / 15 | 68 | 59 | +0.04 (0.39) | 0.70 | 0.27 | 6 of 14 (43%) | +0.015 vs −0.151 | 9 |
| 8 / 20 | 66 | 57 | +0.03 (0.38) | 0.70 | 0.26 | 6 of 14 (43%) | −0.033 vs −0.164 | 9 |
| **8 / 30** | 62 | 50 | +0.06 (0.34) | 0.70 | 0.30 | **5 of 10 (50%)** | **+0.032 vs −0.125** | 9 |
| 8 / 50 | 53 | 46 | +0.09 (0.26) | 0.72 | 0.35 | 7 of 11 (64%) | +0.086 vs −0.118 | 9 |
| 10 / 15 | 63 | 55 | −0.11 (0.79) | 0.65 | 0.33 | 6 of 13 (46%) | −0.103 vs −0.156 | 11 |
| 10 / 20 | 63 | 54 | −0.11 (0.80) | 0.67 | 0.30 | 6 of 14 (43%) | −0.135 vs −0.175 | 11 |
| 10 / 30 | 59 | 50 | −0.05 (0.63) | 0.70 | 0.34 | 6 of 10 (60%) | +0.015 vs −0.137 | 11 |
| 10 / 50 | 51 | 46 | −0.09 (0.72) | 0.67 | 0.35 | 6 of 11 (55%) | −0.009 vs −0.094 | 10 |
| 15 / 15-30 | 50 | 44 | +0.10 (0.26) | 0.75 | 0.27 | 4 of 7 (57%) | +0.025 vs −0.136 | 16 |
| 15 / 50 | 49 | 42 | +0.05 (0.38) | 0.76 | 0.26 | 4 of 7 (57%) | +0.025 vs −0.132 | 16 |
| 20 / any | 36 | **3** | – | – | – | – | – | 20 |

**What the grid says, plainly:**
- **The live history is too short to pin the number down.** No pair gives a correlation that is clearly above zero once
  S ≥ 8. The S = 5 pairs do (p ≈ 0.02), but mostly because setups that are bad early stay bad.
- The 20-traded-session pairs cannot be tested yet: only 3 setups have 5 traded sessions after reaching 20.
- **One effect is consistent across every pair:** setups positive at D did better over the next 5 traded sessions than setups
  negative at D, by **+0.04 to +0.20R per trade**. "Positive so far" is a weak but real ranking signal. It is not proof.
- **The smallest pair where "positive so far" was still positive afterwards on average is 8 traded sessions / 30 trades:**
  - 5 of 10 positive setups stayed positive, vs a 30% base rate;
  - forward avg R +0.032 vs −0.125;
  - it takes a median of 9 live sessions to reach.
  - 5 / 50 and 8 / 50 look better, but they gate on trade count, which favours bursty setups (§2.1).
  - 10 / x was weaker than 8 / x. With 50 scored setups that difference is noise, not a reason to prefer 8.
- **Recommendation:**
  - **Candidate minimum = 8 traded sessions and 30 trades** ("REPS-MIN 8/30").
  - **On-deck minimum = 15 traded sessions and 60 trades.**
  - Revisit at 40 live sessions, when the 15 / x and 20 / x pairs can be scored.
- (The owner's example code was "REPS 10/30". "REPS" is already the 10-28 replay-filter decision, so the reply code here is
  **REPS-MIN**.)

### 2.3 Time to reach at current exposure (72 in-scope setups, each at its own traded-session and trade rate)
| minimum | already there | within 10 more sessions | within 20 | never at the current rate (0 trades) | median more sessions for the rest |
|---|---|---|---|---|---|
| 5 / 15 | 38 | 42 | 46 | 11 | 38 |
| 8 / 20 | 28 | 39 | 44 | 11 | 29 |
| **8 / 30** | **24** | **34** | **36** | 11 | **29** |
| 10 / 30 | 22 | 33 | 36 | 11 | 26 |
| 15 / 30 | 16 | 26 | 31 | 11 | 29 |
| 15 / 50 | 15 | 20 | 27 | 11 | 49 |
| 20 / 50 | 11 | 16 | 22 | 11 | 45 |

- 24 setups have 8 / 30 now, and 34 will within 10 more sessions.
- The slow tail is the low-rep pool. Many Explore 1 / Live Lab setups trade on 1 session in 3-5, so 8 traded sessions takes them
  25-40 live sessions.
- That is why rotation priority goes to the fewest traded sessions (§4.3), and why dormant index-gated setups go through the rule-21
  replay filter instead of waiting.

## 3. Tiered pipeline with numeric bars

```
 Reps (Explore 1 / Live Lab)  ->  Contender (T1 / T2)  ->  Candidate (T1 / T2, tagged)  ->  On deck (T1 / T2 + Team replay)  ->  Primary
   < 20 trades                   >= 20 trades and           Candidate bar                   On-deck bar, 2 re-tiers running,     owner yes
   or < 5 traded sessions        >= 5 traded sessions                                          Primary-rules replay > 0
        ^                              |   ^                       |                              |
        |                              v   |                       v                              v
        +---- (never down to Reps) ---- Graveyard PROPOSAL <--- fails Candidate bar 2 re-tiers running ... fails On-deck bar 2 re-tiers running
```

**Tiers:**
- **Reps** (Explore 1 / Live Lab): fewer than 20 live trades or fewer than 5 traded sessions. This keeps the owner's ROLL1 rule
  (< 20 trades) and adds the traded-session floor.
- **Contender** (T1 / T2): has the reps and is not yet a Candidate.
- **Candidate** and **On deck** stay in T1 / T2. There is no separate account: a move would break the record segment. They get a
  tag on the dashboard, and On deck adds the Team-engine Primary-rules replay.

**Down-moves:**
- On deck → Candidate, or Candidate → Contender, after failing that tier's bar at **2 re-tiers in a row** (hysteresis: one bad day
  cannot flip a tier).
- **Graveyard proposal floor (all options):** 40+ trades, shrunk avg R ≤ −0.10, avg R without the best day < 0, and last-5 R < 0.
  - The owner decides every Graveyard move.
  - Ex-primary setups are protected for 10 Testing sessions (rule 20): MF2-FD, MF4-FD, L3-rsi5hi-FD, MF4 and NS1 from 11-11, so
    until about 11-25.
- The walk-forward found that the floor does **not** pick setups that do worse afterwards (next-5 −0.090R vs pool −0.107R). It frees
  seats; it does not avoid losses. Graveyard setups keep trading, so nothing is lost.

### 3.1 The three bar options (v2: traded sessions first)
"t bar" is multiple-testing aware: a multiple of m = √(2 ln N), where N = the number of setups screened with at least the minimum
trades. Today N ≈ 50-78, so m ≈ 2.8-2.95.

| bar | **strict** Candidate | **strict** On deck | **balanced** Candidate | **balanced** On deck | **lenient** Candidate | **lenient** On deck |
|---|---|---|---|---|---|---|
| min **traded sessions** / trades | **10 / 50** | **20 / 80** | **8 / 30** | **15 / 60** | **5 / 15** | **10 / 40** |
| shrunk avg R ≥ | +0.05 | +0.10 | +0.03 | +0.07 | > 0 | +0.05 |
| avg R w/o best day > | 0 | +0.05 | 0 | +0.03 | 0 | 0 |
| best-day share ≤ | 50% | 35% | 60% | 50% | 75% | 60% |
| day-t ≥ (× m; today's value) | 0.35m (1.0) | 0.70m (1.93) | 0.25m (0.73) | 0.50m (1.40) | – | 0.35m (1.0) |
| ex-market R > | 0 | 0 | 0 | 0 | – | 0 |
| last-5 R > (not collapsing) | −0.10 | 0 | −0.15 | −0.05 | −0.25 | −0.10 |
| 2y backtest ≥ (not strongly negative) | −0.05 | 0 | −0.10 | −0.05 | −0.15 | −0.10 |
| On deck also needs | | Primary-rules replay > 0 over its last 10 traded sessions, and no other On-deck setup from the same family | | same | | same |

### 3.2 How many setups sit in each tier today (72 in scope)
| option | Reps (EX1 / LL) | Contender | Candidate | On deck | Graveyard-proposal floor |
|---|---|---|---|---|---|
| strict | 38 | 28 | 0 | 0 | 6 |
| **balanced** | 38 | 28 | **0** | **0** | 6 |
| lenient | 38 | 27 | 2 (RW1-FD; CWT09-vwaploss-g10 is still in Reps at 15 trades) | 0 | 6 |

- Reps = 37 Explore 1 / Live Lab setups, plus CWT14-R2A-short (Testing 2, 2 traded sessions; it stays put as the owner's PDL-1a
  observation).
- The floor catches 6 setups: MF4-FD (protected until about 11-25), RW3S-FD, CWT13-z05-long, NM-AR-AM, NS3 and intraday_momentum.

**Today's TEAM-6 Primary against the same bars (for scale):**
- under balanced, only RW3-FD reaches Candidate, and **none reaches On deck**;
- under lenient, RW3-FD is On deck, and L3-fromopen, ST7-FD and NM-ETF are Candidates;
- RW5-FD (last-5 −0.315) and NS5 (w/o best day −0.046) fail even lenient.

The balanced bar is higher than anything we have promoted so far. That is the point of "really separate", and it costs time
(§3.4).

### 3.3 Walk-forward check of the bars (26 live sessions)
**Setup of the check:**
- Checkpoints after sessions 10, 12, …, 24 (every 2 sessions, the proposed cadence).
- At each checkpoint, setups are tiered on their records up to that date only.
- Forward R after costs is measured over the next 5 sessions, and over everything after.

| option / tier | setup-dates | next 5 sessions: trades, avg R | everything after: trades, avg R | checkpoints where the tier beat the pool (next 5) |
|---|---|---|---|---|
| balanced Candidate | 10 (3 setups: RW3-FD, RW5-FD, MF4-FD) | 249, **+0.098** | 620, −0.153 | **5 of 7** |
| balanced pool | 607 | 12,428, −0.107 | 25,584, −0.098 | |
| lenient Candidate | 31 (15 setups) | 730, +0.042 | 1,801, −0.138 | 4 of 8 |
| lenient On deck | 7 (MF4-FD, RW5-FD, RW3-FD) | 174, −0.004 | 344, **−0.229** | **4 of 7 checks negative next 5 = false alarm** |
| lenient pool | 579 | 11,773, −0.114 | 24,059, −0.095 | |
| strict | nothing reached Candidate or On deck in 26 sessions | | | |
| Graveyard floor | 187 (42 setups) | 11,539, −0.090 | 24,043, −0.078 | no worse than the pool |

**Past real moves vs the bars, at the move date (record up to the session before):**

| setup | move | trades before | avg R before | t before | strict / balanced / lenient | avg R after (trades) |
|---|---|---|---|---|---|---|
| RW3-FD | T1 → P 10-16 | 28 | +0.305 | 1.67 | pool / pool / pool | **+0.290** (112) |
| RW5-FD | T1 → P 10-16 | 27 | +0.416 | 1.45 | pool / pool / pool | **+0.175** (128) |
| MF2-FD | T1 → P 10-21 | 25 | +0.477 | 1.18 | pool / pool / cand | −0.042 (109) |
| MF4-FD | T1 → P 10-21 | 40 | +0.238 | 1.87 | pool / pool / cand | −0.391 (118) |
| NS3-FD | T1 → P 10-21 | 58 | +0.118 | 0.83 | pool / pool / pool | −0.272 (121) |
| L3-fromopen-FD | T1 → P 10-22 | 133 | +0.147 | 0.50 | pool / pool / pool | **+0.190** (152) |
| CWT14-p10-lowvol | T2 → P 10-22 | 100 | +0.088 | 1.05 | pool / pool / cand | −0.153 (215) |
| ST7-FD | T1 → P 10-26 | 16 | +0.199 | 0.61 | pool / pool / pool | **+0.133** (21) |
| CWT13-z05-long | T2 → P 10-26 | 53 | +0.091 | 0.47 | pool / pool / pool | −0.204 (222) |
| L3-rsi5hi-FD | T2 → P 10-30 | 76 | +0.173 | 1.14 | pool / pool / cand | −0.455 (22) |
| MF3 | P → T1 10-20 | 32 | −0.153 | −0.74 | pool | +0.351 (12) |
| MF1 | P → T1 10-26 | 25 | −0.190 | −0.80 | pool | −1.210 (5) |
| NS4 | P → T2 10-28 | 20 | +0.025 | 0.13 | pool | −0.288 (16) |
| MF2 | P → T2 10-28 | 4 | −1.210 | – | pool | −0.254 (12) |

**What this means for the owner's trade-off:**
- **False-promotion risk:**
  - real promotions so far: 6 of 10 negative afterwards;
  - lenient On deck: 4 of 7 checks negative;
  - balanced Candidate: led the pool at 5 of 7 checkpoints, but the sample is tiny (1-2 setups at a time, one family of gap-down
    shorts);
  - the 4 setups the lenient bar would have tagged Candidate at their promotion date (MF2-FD, MF4-FD, CWT14-p10-lowvol, L3-rsi5hi)
    **all turned negative**, while the 4 winners (RW3, RW5, L3-fromopen, ST7) were promoted *before* any bar could see them.
  - No bar on this much live data would have picked the winners. Either the winners were lucky early, or the edge shows only on
    larger samples.
- **Time to promotion** (from day-t growing with √sessions, using today's best Primary records, t ≈ 1.2-1.3 at 21 traded sessions):
  - balanced On deck (t ≥ 1.40, 15 traded sessions): **about 25-28 traded sessions**, i.e. 1-2 more weeks for the best current
    records, if their edge holds;
  - strict On deck (t ≥ 1.93, 20 traded sessions): **about 45-55 traded sessions**, i.e. 2+ months;
  - lenient: today, but with a false-alarm rate of about 57%.

### 3.4 Recommendation
- **BARS balanced**, with the v2 minimums (Candidate 8 / 30, On deck 15 / 60), plus two extra keys for Primary:
  1. a Primary-rules Team replay over the last 10 traded sessions that is greater than 0;
  2. the owner's yes.
- Strict is the safer choice if the owner prefers fewer, later promotions. Lenient is close to how promotions were made so far, and
  that record is 4 of 10.

## 4. Continuous rotation mechanics

### 4.1 Which account holds which tier
- **Testing 1 and Testing 2 (equal weight):** Contenders + Candidates + On deck, kept balanced:
  - same number of setups (± 1);
  - long / short mixed;
  - twins and family members split across the two accounts;
  - the ex-primary mix spread across both.
- **Explore 1 and Live Lab:** the Reps pool, split the same way (ROLL1 method: balance expected trades per session, twins apart).

### 4.2 How many setups per account
- Slots are not the limit:
  - T1 / T2 have 400 slots each at 3.8× buying power (about $950 lots). T1's cumulative peak was 207 open; T2 runs 130-140
    entries a session; 0% of signals were lost to slots.
  - Explore 1 / Live Lab have 200 slots at 2.0× (about $1,000 lots) and 10 lots per setup, with about 5-8 entries a session.
- The real limits are **family crowding** (same-symbol signals inside one family) and **readability**.
- **Target: 15-18 setups in each of T1 / T2, and 18-21 in each of Explore 1 / Live Lab.**
  - That is 66-78 seats, which covers today's 72.
  - When the pool grows beyond that, use whole-session benching (§4.3) rather than adding setups.

### 4.3 Cadence, priority and benching
- **Re-tier every 2 sessions after the close**, inside the nightly loop (step 6). Moves apply only from the next session, never
  during 09:30-16:00 (setup-freeze).
- **Rotation priority = fewest traded sessions first** (owner input):
  - Inside each account, `setup_order` is sorted by traded sessions ascending, so the least-experienced setup gets the first claim on
    a contested symbol. This is re-sorted at each re-tier.
  - Within a family, the sibling with fewer traded sessions goes first.
  - Graduation and seat assignment use the same order: when a T1 / T2 seat opens, the Reps setup with the most trades among those
    at the minimum moves up. When seats are short, the setup with the most traded sessions in the last 10 is benched first.
- **Whole-session benching (owner playing-time rule), only when needed.** Triggers:
  - (a) an account's peak open lots are at 85% of its slots or more on 2 of the last 3 sessions; or
  - (b) a family pair is crowded-out (25% or more of a setup's signals lost to a sibling, with 3+ signals).
  - Then the crowding siblings alternate whole sessions; the one with more traded sessions sits out first.
  - Benched sessions are logged as benched, excluded from per-session stats, and never counted as traded sessions.
  - There is **no in-session throttling** in Primary / Testing.
- **Today's watch: the Early Sellers family in Testing 1** (MF1, MF2-FD, MF3, MF4-FD). MF3 was crowded-out (lost 35 of 113 signals
  to MF3-FD, 13 to MF5); MF4-FD lost signals to MF5-FD and MF1-FD. ROT-A sends MF5 to Testing 2, and benching starts if
  trigger (b) fires again.

### 4.4 Exposure guarantee
- **Every setup is on at least 4 of every 5 sessions** (at most 1 benched session in 5), and **on every session while it has fewer
  than 8 traded sessions**.
- The nightly loop reports any setup with 0 traded sessions in its last 5 on-sessions:
  - "silent" if it gets no signals;
  - "blocked" if its signals are skipped. Blocked by an owner-controlled block (place in line, caps, buying power, cost filter) →
    a DECISION; other blocks → housekeeping.
- Dormant setups (0 trades after 10 sessions, e.g. the IDX / LD index-gated longs) get the rule-21 replay filter instead of more
  waiting.

### 4.5 Keeping results comparable
| | Primary (TEAM-6) | Testing 1 | Testing 2 | Explore 1 / Live Lab |
|---|---|---|---|---|
| lot | ~$4,000 (77 slots × 3.2) | ~$950 (400 × 3.8) | ~$950 (400 × 3.8) | ~$1,000 (200 × 2.0) |
| per-setup cap | 30 | 150 | 50 | 10 |
| −2R per-setup latch | **ON** | off | off | off |
| cost filter 0.15R | off | on | on | on |
| universe | full | full + split-tape short gate | **top-500 pool (UNI1)** | full |
| scale-out | on | on (2 a day) | on (2 a day) | off |

- Every record is shown in **R after costs** (never $), with its account segment and the ledger rule changes inside its window.
- **Primary-rules column:**
  - nightly, for every setup: the post-hoc −2R latch proxy (inventory column);
  - for Candidates and On deck: a real **Team-engine replay** (`python -m mcf.report.team` with a picks file of the setup alone,
    on Primary's universe, sizing, caps, latch and costs) over its last 10 traded sessions. This costs about 1 replay per session
    per setup, so it is limited to Candidates and On deck at 4 jobs or fewer.
- Testing 2's top-500 universe means its setups see fewer, more liquid names than Testing 1. Open question Q2 asks whether to align
  them, because Testing 1 = Testing 2 should mean the same conditions.

### 4.6 What is automated and what is a DECISION
**The nightly loop computes (report only, housekeeping, rule 15):**
- per setup: traded sessions, trades, shrunk avg R, w/o best day + share, day-t vs the bar, ex-market R, last-5 R, 2y R,
  Primary-rules proxy, playing time;
- the tier under the chosen bar, with the 2-re-tier hysteresis;
- the proposed moves list.

**What becomes a DECISION depends on ROT-B (owner choice):**
- **ROT-B yes:** the owner pre-approves fixed-rule moves *inside the testing pool*:
  - Reps → Contender graduation (EX1 / LL → T1 / T2 at ≥ 20 trades and ≥ 5 traded sessions);
  - T1 ↔ T2 balancing;
  - priority re-sorting;
  - whole-session benching.

  Each such move still gets a ledger entry, regenerated assignments in the same commit, an inbox FYI line, and is applied after
  the close only.
- **Always an owner yes, ROT-B or not:**
  - promotion to Primary;
  - any Primary demotion;
  - any Graveyard move or retirement;
  - changing the bars.
- **ROT-B no:** every move is a DECISION line in the nightly brief, as today.

## 5. "Primary candidates" leaderboard spec (dashboard)
**One table**, sorted by tier (On deck → Candidate → Contender → Reps), then by shrunk avg R.

**Columns:**
1. rank;
2. setup name + id;
3. tier badge;
4. account tag (T1 / T2 / EX1 / LL);
5. side;
6. family;
7. **traded sessions** (of on-sessions; benched count);
8. trades;
9. shrunk avg R;
10. avg R;
11. **avg R w/o best day** + best-day share;
12. day-t / t bar;
13. ex-market R (beta);
14. last-5 R;
15. **Primary-rules R** (proxy; Team replay for Candidate / On deck);
16. 2y R;
17. playing time (signals and entries per session vs expected; verdict);
18. a **bar checklist** of 8 ticks (min sessions / trades, shrunk, w/o best day, share, t, ex-market, last-5, 2y);
19. "next step" (e.g. "needs 3 more traded sessions", "fails w/o best day", "2 of 2 re-tiers to On deck");
20. rule-change flags from the ledger inside its window.

**Tags:** `ON DECK`, `CANDIDATE`, `CONTENDER`, `REPS`, `GY?` (floor met, owner decides), `1 day` (best day ≥ 50% of R), `ex-primary`,
`protected to <date>` (rule 20), `benched today`, `crowded`, `starved`, `dormant`, `testing-bar`, `family: <name>`.

**Footer:**
- the bar in force (strict / balanced / lenient + REPS-MIN);
- the number of setups screened (N) and the t-bar multiple;
- "Paper results" and "Educational only — not financial advice".
- Reps-tier setups from the Graveyard stay off the board (as today). Explore 1 / Live Lab account totals stay out of the daily post.

## 6. Migration plan (ROT-A) — from the post-TEAM-6 state, applied after a close, effective the next session after the owner's yes
**Moves:**
1. `CWT13-vwapstretch-z075-long`: Explore 1 → **Testing 1** (graduates: 40 trades / 9 traded sessions; its twin z05-long is in T2).
2. `ST8-volspikedn-long-pm-t1s1-FD`: Explore 1 → **Testing 1** (25 / 11).
3. `CWT12-flag-s1-long`: Live Lab → **Testing 1** (22 / 13).
4. `CWT05-flush-m075-v3-long`: Live Lab → **Testing 2** (23 / 11; its sibling m05-v3 is in T1).
5. `MF5-flowsell-vwapup-rsi5hi`: off in Testing 1 → **Testing 2 only**. It runs in both today; this gives one home and eases
   Early Sellers crowding in T1. Its T2 record: 19 trades, +0.349.
6. `exhaustion_short-FD`: off in Testing 1 → **Testing 2 only**. Its twin `exhaustion_short` stays in T1.

**Re-sort:** `setup_order` in all four accounts, by traded sessions ascending (§4.3).

**Result:**

| account | setups | entries / session (cumulative playing time) | long / short / both |
|---|---|---|---|
| Testing 1 | 17 | 69 | 5 / 10 / 2 |
| Testing 2 | 18 (17 if RW3S-GY yes) | 139 | 8 / 10 / 0 |
| Explore 1 | 19 | 5 | 6 / 10 (+3 with no trades yet) |
| Live Lab | 18 | 4 | 6 / 10 (+2 with no trades yet) |

**ROT-GY (separate, per-setup owner decisions; recommend yes, all moves rather than removals):**

| setup | account | trades / traded sessions | avg R | w/o best day | last-5 |
|---|---|---|---|---|---|
| RW3S-FD (already open as RW3S-GY) | T2 | 204 / 6 | −0.281 | −0.291 | −0.312 |
| CWT13-vwapstretch-z05-long (ex-P, past its 10 sessions) | T2 | 275 / 20 | −0.147 | −0.189 | −0.203 |
| NM-AR-AM-gapdown-capitulation-long | T2 | 58 / 9 | −0.460 | −0.598 | −0.564 |
| NS3-failed-vwap-reclaim-short | T1 | 67 / 10 | −0.229 | −0.403 | −0.423 |
| intraday_momentum | T1 | 52 / 20 | −0.352 | −0.381 | −0.513 |

- NM-AR-AM's 2y is +0.257; nothing else is better than −0.08.
- With all five: T1 15 / T2 15.
- MF4-FD also meets the floor (−0.231R) but is protected until about 11-25 (rule 20).

**Ledger / assignments:**
- One ledger entry `2026-11-1x-rot-a-layout`:
  - config before / after, the evidence (this folder), metrics at approval;
  - effective = the first session after the yes;
  - a new record segment for each moved setup (rule 22 versioning).
- One entry per ROT-GY yes.
- `docs/live/assignments.json` is regenerated in the same commit (`python -m mcf.report.assignments`; `tests/test_assignments.py`).
- `former_primary` markers unchanged; `python -m mcf.research.ledger check` re-run after merge.
- The dashboard tier and leaderboard code is housekeeping (report only) and can ship separately once tests pass.

## 7. Risks and open questions
**Risks:**
- **Too-short history.** 26 live sessions; the minimum grid cannot test 20 traded sessions yet. Every number here should be revisited
  at about 40 sessions.
- **One family dominates.** Every Candidate the walk-forward found was a gap-down / heavy-selling short (RW3, RW5, MF4). The bar
  measures the tape as much as the setup. The leaderboard shows family, and On deck allows one setup per family at a time.
- **Moving a setup starts a new segment** (sizing, universe, caps). ROT-A moves only graduates and the two dual-home copies, and
  leaves busy records where they are.
- **Hysteresis delays demotion** by 2 sessions. Graveyard protection (rule 20) delays it more for ex-primary setups.
- **Benching reduces the per-session sample** of the benched setup. It is used only on crowding triggers.

**Open questions:**
- Q1: bars strict, balanced or lenient?
- Q2: align Testing 2's universe with Testing 1 (end UNI1), so T1 = T2 in conditions too?
- Q3: should Explore 1 / Live Lab keep the 10-lots-per-setup cap? It holds back busy graduates; under ROT-A they move up anyway.
- Q4: should Candidates get a Team replay every night, or only at On deck (CPU)?

**Reply codes:**
- **"ROT-A yes" / "ROT-A no"**: the layout and migration in §6, the tier and account roles, re-tier every 2 sessions, priority by
  fewest traded sessions.
- **"ROT-B yes" / "ROT-B no"**: pre-approve fixed-rule moves inside the testing pool; promotions, demotions from Primary and
  Graveyard moves still need a yes.
- **"BARS strict" / "BARS balanced" / "BARS lenient"**: the bar option (recommend balanced).
- **"REPS-MIN 8/30 yes"** (or another pair, e.g. "REPS-MIN 10/30"): the Candidate minimum in traded sessions / trades (On deck = 15/60).
- **"ROT-GY yes" / "ROT-GY no"** (or per setup, e.g. "ROT-GY NS3 yes"): the 4 Graveyard proposals beyond RW3S-GY.
- **"ROT-UNI yes"**: Q2, align Testing 2's universe with Testing 1.

## Configurations tried and files
**Configurations tried:** 32 in all, every one reported:
- 6 bar rule sets in v1 (first draft, minimums 40/10, 25/8, 15/5 and 80/15, 60/12, 40/10). Its tier counts today were identical to
  v2; the walk-forward Candidate result was +0.082R next-5 over 253 trades; results are in `bars_out_v1.json` / `tiers_today_v1.csv`;
- the same 6 with traded-session minimums in v2, after the owner's input (only the minimums changed);
- 20 minimum pairs.

No setup, exit or config was changed.

**Files:**
- `inventory.py`: inventory, Primary-rules proxy → `inventory.csv`;
- `bars.py`: bars, today's tiers, walk-forward, past moves → `bars_out.json`, `tiers_today.csv`, `walkforward_rows.csv`,
  `past_moves.csv`;
- `minimums.py`: traded-session grid, time to reach, design effect → `minimums.csv`, `minimums_out.json`, `traded_sessions.csv`,
  `variance.csv`;
- `layout.py`: ROT-A layout → `layout.csv`.

**Inputs:** the 7 accounts' journals and scorecards from the 11-10 nightly (read-only copies), and SPY 1-minute SIP bars (read-only
market data). `trades_all.parquet` is not committed (it is rebuilt by `inventory.py`).

*Paper results. Educational only — not financial advice.*
