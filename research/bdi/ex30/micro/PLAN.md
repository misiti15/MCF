Educational only — not financial advice

# ex30 / micro — microstructure / bar-shape setups (pre-declaration, written 2026-11-03 before any configuration was scored)

Owner 2026-11-03: two new EXPLORATORY paper accounts, 30 new unconventional setups (this lane delivers 5).
Family: 5-minute bar microstructure — range compression then expansion, volume dry-up then surge, body / wick shape,
same-colour runs, time spent at VWAP, first-hour range break on fading volume. Each rule is 2-3 conditions.

## Data the live runner has (checked before writing the rules)

- `LabStrategy.generate` builds the frame with `heat_frame` + `extra_features` on today's 5-minute bars (with prior
  5-minute history for rolling columns). Columns used here: close, high, low, atr_d, tod, vwapDistPct, volumeRatio
  (bar volume / 20-bar mean), volumeSurge (5-bar mean volume / prior 15-bar mean), upper_wick, lower_wick
  (wick share of the bar range), dist_hod_atr (running high of day incl. 09:30-09:50). No context columns, no new data.
- The frames carry no bar `open`; body colour is recovered exactly from the wick columns: a green bar closes at the top
  of its body, so (close - low) / range = 1 - upper_wick; a red bar has (close - low) / range = lower_wick. Bars whose
  body is < 5% of the range count as neither colour.
- **Live/offline frame difference handled up front:** the offline frames start at the 09:50 bar; the live frame holds
  09:35-09:45 too. Every look-back (lags, counts, shares) therefore counts only bars with bar close >= 09:50, and each
  window starts late enough that every lag it reads is a >= 09:50 bar. The first-hour high is the running high of day
  at the 10:30 bar (09:30-10:30 range; dist_hod_atr includes the first 20 minutes in both frames).

## The 5 setups (primary = the delivered module; fixed now, results do not change the choice)

Notation: rng = (high - low) / atr_d; VWAP = close / (1 + vwapDistPct / 100); straddle = low <= VWAP <= high.

| id | side / geom | window (bar close) | rule (all known at the bar close) |
|---|---|---|---|
| MC1-nr7-expansion-volburst-long | long t1s1 | 10:45-15:00 | previous bar is the narrowest (rng) of the last 7 bars (NR7) AND this bar closes above the previous bar's high with upper_wick <= 0.25 AND volumeRatio >= 1.5 |
| MC2-dryup-surge-wickreject-short | short t1s1 | 10:15-15:00 | each of the 3 previous bars has volumeRatio < 0.7 (dry-up) AND this bar volumeRatio >= 2.0 (surge) AND upper_wick >= 0.5 (rejected) |
| MC3-vwap-glued-stretch-long | long t05s1 | 11:00-15:00 | share of today's bars (since 09:50, incl. this one) whose range straddled VWAP >= 0.60 AND close <= VWAP - 0.30 ATR AND lower_wick >= 0.5 |
| MC4-redrun-outside-reversal-long | long t05s1 | 10:30-15:00 | the 6 previous bars are all red bodies AND this bar is green and closes above the previous bar's high |
| MC5-firsthour-break-voldecay-short | short t1s1 | 10:35-14:00 | close crosses above the first-hour high (09:30-10:30; previous close <= it) AND volumeRatio < 0.8 AND volumeSurge < 1.0 |

ADV floor 95M (adv20) for all. Design intent: MC3/MC4 are mean-reversion designs for range / quiet tapes (the live
book's weak spot); MC2/MC5 fade weak or rejected pushes; MC1 is the one momentum (compression -> expansion) design.

**Neighbours (plateau check only, never substituted for the primary): two per setup = 10 configs.**
MC1: NR5, NR10. MC2: surge volumeRatio >= 1.5, >= 3.0. MC3: VWAP share >= 0.50, >= 0.70. MC4: red run 5, 8.
MC5: volumeRatio < 0.6, < 1.0. **Total configurations scored: 15** (5 primaries + 10 neighbours); nothing else.

## Data, splits, costs, controls (reuse of night1102/simple and ex30/xsec harness)

- history2y open frames (`lib.load_month`). TRAIN = 2024-10, 2025-03..2025-12; VALID = 2026-01..03, 2026-07-01..
  2026-09-15. 2026-04..06 and 2026-09-16.. not scored. **Locked block 2024-11-01..2025-02-28 never loaded** (asserted).
- Trades: `mcf.research.gates.lab_trades` (first qualifying bar per symbol-day; production costs 1c + 1 bps per side,
  +2c on stops, time-of-day entry multiplier). R = 0.25 x daily ATR, flat 15:55.
- Random control: day-matched (trade R minus the mean production R of every eligible bar of the same side / geometry /
  window / ADV on that date); excess and day-clustered t reported.
- Day type: SPY open-to-close (SIP 1-minute cache): up >= +0.25%, down <= -0.25%, else quiet. R by type, TRAIN and VALID.
- Light lane gate: avg R >= -0.02 on TRAIN and on VALID, 1.5-25 trades/session (TRAIN+VALID sessions), mask parity
  module vs harness on 2026-09 (the harness re-implements every rule independently with pandas group shifts; the
  module uses numpy). No BAR90. A setup failing the gate is still delivered, marked gate_pass = false.
- Also reported: avg R without the best session and that session's share (one-big-day check), configs = 15.
