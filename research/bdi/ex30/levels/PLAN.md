Educational only — not financial advice

# ex30 / levels — price levels and magnets (pre-declaration, written 2026-11-03 before any configuration was scored)

Owner 2026-11-03: two new EXPLORATORY paper accounts, 30 new unconventional setups (this lane delivers 5).
Family: price levels and magnets — round numbers, prior close / gap fill, first vs second touch, long and short.

## Data the live runner has (checked before writing the rules)

`LabStrategy.generate` (mcf/strategies/setups.py) gives a mask only today's 5-minute rows of `heat_frame` +
`extra_features`, plus from the daily prior: `gap` (ctx.prev_close), `dist_pdh_atr` / `dist_pdl_atr` (ctx.prev_high /
prev_low), `atr_d`. `mcf.data.priors.Prior` holds prev_close / prev_high / prev_low / atr / adv / avg_volume / sma20 only.

**Not available live, so dropped from this lane:** prior-WEEK high/low, multi-day range edges, 52-week / all-time
highs and lows, prior-day VWAP. The live prior has none of them and the mask sees no prior-day rows (the prior5 tail
is cut off before the mask), so any setup on them would need a new prior field (mcf/ change — out of scope here).
**Also excluded as exhausted / live:** PDH / PDL failed-break and sweep-reclaim (CWT14, LIQ-pdl, pdl1030*), PD break
fades (ST5), gap-down bounce shorts (RW1/RW3/RW5/RW7), ORB / FVG (rdt1030).

Levels used (all known at the bar close, identical in live and offline frames): today's open = close/(1+fromOpen/100);
prior close = open/(1+gap/100); running high of day = close + dist_hod_atr x atr_d (rounded to cents; includes
09:30-09:50 in both frames); session VWAP = close/(1+vwapDistPct/100); round-number grid by price ($10 at >= $200,
$5 at $50-200, $1 at $10-50, $0.50 below $10). Look-backs read only bars with close >= 09:50 (windows start late
enough). Known small live/offline difference: offline `gap` uses the last 5-minute close of the prior day, live uses
the daily bar close (closing auction) — reported, not corrected.

## The 5 setups (primary = the delivered module; fixed now, results do not change the choice)

| id | side / geom | window (bar close) | rule |
|---|---|---|---|
| LV1-round-firsttouch-reject-short | short t05s1 | 10:00-15:00 | R = next grid level above the running high before this bar; this bar's high >= R (first touch today); close <= R - 0.05 ATR and upper_wick >= 0.40 |
| LV2-round-secondtouch-break-long | long t1s1 | 10:30-15:00 | close crosses above grid level R (prev close < R <= close); running high before this bar in [R - 0.05, R + 0.10] ATR (touched, never cleared); lowest low of the previous 6 bars <= R - 0.40 ATR |
| LV3-gapup-halffill-short | short t1s1 | 10:00-14:00 | gap +1.5..+8%; close crosses below the half-gap line (prev close above it); close < VWAP; close - prior close >= 0.30 ATR |
| LV4-gapdn-filled-retest-long | long t05s1 | 10:15-15:00 | gap <= -1.0%; running high before this bar >= prior close (filled); low <= prior close + 0.10 ATR and close >= prior close + 0.02 ATR |
| LV5-flatopen-pclose-stretch-short | short t1s1 | 11:30-15:00 | abs(gap) <= 0.4%; close >= prior close + 1.0 ATR; dist_hod_atr <= 0.05; volumeRatio < 1.0 |

ADV floor 95M (adv20) for all; first signal per symbol-day; R = 0.25 x daily ATR, flat 15:55. Design intent: LV1/LV5
fade a level into a range (quiet-day candidates, the live book's weak spot); LV3/LV4 use the prior close as a magnet /
flipped support; LV2 is the one breakout (second attempt) design.

**Calibration (signal counts only, no outcome column loaded; 2025-06, a TRAIN month):** first-signal symbol-days per
session at the draft thresholds were LV1 11.1, LV2 24.7 (pull 0.30), LV3 5.0, LV4 17.1, LV5 37.2 (stretch 0.75).
LV2's pullback was raised to 0.40 (10.8/session) and LV5's stretch to 1.0 ATR (15.1/session) to land inside the
1.5-25 band. Those counts are frequency checks, not scored configurations.

**Neighbours (plateau check only, never substituted for the primary): two per setup = 10 configs.**
LV1: upper_wick >= 0.30, >= 0.50. LV2: pullback 0.30, 0.50 ATR. LV3: gap min 1.0%, 2.5%. LV4: gap max -0.5%, -2.0%.
LV5: stretch 0.75, 1.25 ATR. **Total configurations scored: 15** (5 primaries + 10 neighbours); nothing else.

## Data, splits, costs, controls (reuse of the ex30/micro = night1102/simple harness)

- history2y open frames (`lib.load_month`). TRAIN = 2024-10, 2025-03..2025-12; VALID = 2026-01..03, 2026-07-01..
  2026-09-15. 2026-04..06 and 2026-09-16.. not scored. **Locked block 2024-11-01..2025-02-28 never loaded** (asserted).
- Trades: `mcf.research.gates.lab_trades` (first qualifying bar per symbol-day; production costs 1c + 1 bps per side,
  +2c on stops, time-of-day entry multiplier).
- Random control: day-matched (trade R minus the mean production R of every eligible bar of the same side / geometry /
  window / ADV on that date); excess and day-clustered t reported.
- Day type: SPY open-to-close (SIP 1-minute cache): up >= +0.25%, down <= -0.25%, else quiet. R by type.
- Light lane gate: avg R >= -0.02 on TRAIN and on VALID, 1.5-25 trades/session (TRAIN+VALID sessions), mask parity
  module vs harness on 2026-09 (the harness re-implements every rule with pandas group shifts / rolling; the modules
  use numpy). No BAR90. A setup failing the gate is still delivered, marked gate_pass = false.
- Also reported: avg R without the best session and that session's share (one-big-day check), configs = 15.
