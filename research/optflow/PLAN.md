# OPTFLOW — does first-30-minute option flow predict the rest-of-day stock move? (Scout, FROZEN 2026-11-10 17:40 ET, before any outcome)

*Educational only — not financial advice. A NEW data source for direction (Lead day-3 plan: fresh direction sources only).
Descriptive pilot first, 0 configs scored as rules.*

## Outside evidence
Bergsma, Fodor, Singal & Tayal (Financial Management 2020): a signed option-to-stock trading score over the first 30 minutes
predicts the rest-of-day stock return; stronger for smaller / high-idio-vol / wider-spread stocks and after overnight earnings.
Our data: Alpaca historical option minute bars (verified 2026-11-10 for AAPL / AMD / SOFI near-ATM weeklies) - UNSIGNED, so the
pilot uses a call-vs-put premium proxy, not the paper's signed score (stated limit).

## Pilot (phase 1)
- **Names:** the 60 highest-adv20 single-stock lab names (no ETPs) as of 2026-07-31. **Days:** 2026-08-03 .. 2026-11-06 (open
  window; far from the locked block). Option bars are fetched only for 09:30-10:00 (features); stock bars 09:30-15:55.
- **Contracts:** nearest Friday expiry >= the day (weekly) and the next one; strikes on $1 / $2.5 / $5 grids within +-6% of the
  09:30 open (contracts without bars simply return nothing).
- **Features at 10:00 (bars ending <= 10:00):** C = call premium $ (sum close x volume x 100), P = put premium $; call share
  cs = C / (C + P); **abnormal call share acs = cs minus the name's mean cs over its prior <= 20 pilot sessions (>= 10 needed)**;
  opt/stock = (C + P) / stock $ volume 09:30-10:00, vs its own prior mean (size, reported only).
- **Outcome:** stock return from the 10:00 one-minute open to the 15:55 close, in ATR14 units, gross; ex-market = minus beta1 x
  SPY over the same window (beta 1 stated); day-demeaned across the pilot names.
- **The one look:** acs quintiles -> day-demeaned outcome; Q5 - Q1 per day (day-clustered t, sign count). Control: the same
  within terciles of the stock's own 09:30-10:00 return (does option flow add over the stock's own first half hour?).
- **Kill line:** Q5 - Q1 <= 0, or day-t < 2, or it vanishes inside the stock-return terciles -> close OPTFLOW. Pass -> phase 2:
  2-year sample (open block only) with a frozen plan, family N stated (new data; nearest family = first-30-min momentum, pod).
