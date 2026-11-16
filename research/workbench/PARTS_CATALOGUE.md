# Workbench parts catalogue — what each kind of part changes (owner idea 2026-11-16)
Educational only — not financial advice.

Owner: "Like a car — tires change grip, turning, safety, comfort; the engine changes power and torque; the suspension makes it smoother or tighter. If a setup performs badly on long days or stays in trades too long, we should know which part to look at." The Mechanic still inspects EVERY part; this catalogue says where to look first and what to expect. Each Workbench job adds its measured evidence (change → effect, per setup) to the table at the bottom, so the expectations get firmer with every setup.

| Part (car analogy) | Typical knobs | What it mainly changes | Symptom that points here |
|---|---|---|---|
| Intake / prefilter (fuel quality) | gap size, ADV, price, ETF vs stock, earnings blackout | how many trades, quality of names, spread/borrow cost | many trades on illiquid / hard-to-borrow names; cost eats the edge |
| Timer / window (when you drive) | start (≥ 09:50), end time | exposure to the open's chop vs the afternoon; trades/day | losers cluster at one time of day |
| Sensors / trigger (engine timing) | indicator thresholds (RSI, slope, VWAP distance), confirm bars | entry quality: win rate, MAE right after entry | entries at the local extreme, immediate adverse moves |
| Gates (traction control) | SPY/QQQ direction, breadth, Compass state | behaviour by day type (up / down / quiet / long trend days) | great on one day type, bad on the other |
| Entry / sizing (gearbox) | order type, limit offset, size | fill rate, slippage, R per trade size | missed fills, paying the spread, good trades too small |
| Stop (brakes) | width (ATR / % / structure), move-to-breakeven | win rate vs avg loss; how often noise stops you out | many stops followed by the move it predicted |
| Target / scale-out (transmission top gear) | R multiple, partial exits, trailing | avg win vs win rate; give-back from the peak | trades touch the target zone then reverse; big MFE, small R |
| Time exit / max hold (fuel range) | hold minutes, 15:55 flatten | behaviour on long trend days; overnight-like drift; stays in too long | "stays in trades too long", late-day give-back |
| Refire / caps (cruise control & limiter) | re-entry cooldown, concurrent-lot cap, −2R latch | concentration on one day / one name; tail risk; big-day dependence | one day carries the record; stacking in one symbol |

## Evidence log (one row per tested change; the Mechanic appends)
| Date | Setup | Part | Change | Effect in backtests (avg R, win %, avg win/loss, hold, day-type split) | Kept? |
|---|---|---|---|---|---|
| 2026-11-16 | CWT14-failbrk-orl-p10-long | Entry / sizing (1R) + Stop | WB1: 1R 0.25 -> 0.30 x ATR (stop and target 20% wider) | avg R -0.127 -> -0.098 (2y), -0.188 -> -0.102 (replay); win 63.0 -> 63.3%; avg win/loss +0.457/-1.122 -> +0.453/-1.047 (cost drag on thin R shrinks); stop share 33% -> 31%; up/flat/down days -0.009/-0.124/-0.227 -> +0.038/-0.095/-0.213 | passed; folded into WB4 |
| 2026-11-16 | CWT14-failbrk-orl-p10-long | Timer / window | WB2: start 09:50 -> 10:30 | avg R -0.127 -> -0.116 (2y), -0.188 -> -0.179 (replay); trades -41% / -48%; win 63.0 -> 63.6%; median hold 21 -> 27 min; up/flat/down +0.010/-0.105/-0.224; live showed 10:05-10:30 at -0.148R vs later -0.009R but the backtests only half confirm it | passed narrowly; not deployed |
| 2026-11-16 | CWT14-failbrk-orl-p10-long | Intake / prefilter | WB3: extra filter daily ATR >= 2.0% of price | avg R -0.127 -> -0.104 (2y), -0.188 -> -0.125 (replay); trades -23% / -20%; avg win/loss +0.468/-1.092; hold 22 min; up/flat/down +0.010/-0.103/-0.200 (low-ATR names: R too thin for costs) | passed; folded into WB4 |
| 2026-11-16 | CWT14-failbrk-orl-p10-long | Entry/1R + Intake (combo) | WB4 = WB1 + WB3 | avg R -0.127 -> -0.079 (2y), -0.188 -> -0.101 (replay); avg win/loss +0.463/-1.018; up/flat/down +0.056/-0.078/-0.194; still negative overall | passed; recommended for Testing 1 (pending after close) |
| 2026-11-16 | CWT14-failbrk-orl-p10-long | Stop / Target / Time exit / Sensors (train only) | stop x0.8, target 0.4R / 0.6R, scale-out half at +0.35R then BE, flat 13:00, poke >= 0.15 ATR, ADV >= $150M, reclaim <= 0.08 ATR | train avg R vs parent -0.151: -0.211, -0.149, -0.155, -0.172, -0.151, -0.150, -0.147, -0.136 — target / time exit / scale-out do nothing for a 20-minute 0.5R trade; tighter stop hurts | not kept |
