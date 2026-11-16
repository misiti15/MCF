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
