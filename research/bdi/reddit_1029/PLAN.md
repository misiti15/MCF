# reddit_1029 pre-declared test plan (written before any scoring)

*Educational only — not financial advice.*

Harness: research/bdi/pod1022/score_batch.py (open two-year history, costs in, live earnings blackout removed,
locked block 2024-11-01..2025-02-28 never read, random same-minute control, day-clustered t, regime split).
Universe floor: ADV20 >= $95M (live lab floor). Long only (owner preference; both ideas are long setups as posted).
Frames are 5-minute bars from the 09:50 bar; no 09:35-09:45 rows exist, so neither idea can be tested on the opening
drive (stated limitation).

## RB1 — 3 Bar Play (r/Daytrading 1xhkikg), 8 configs
- Igniting bar j: range (high-low) >= K x 5-min ATR, volumeRatio >= 2, closes in the top 25% of its range,
  close > previous bar close (green proxy; frames have no open column).
- Resting bars: the 1 or 2 bars after j each have high <= igniting high and low >= igniting midpoint.
- Trigger: the next bar closes above the resting bars' high (entry at that close).
- Stop: 1c below the lowest resting-bar low (GEOM S, R = entry - stop).
- Grid: K in {2, 3} x in-play day filter {off, on: gap >= +1% and fromOpen >= +1% at entry}
  x exit {target 2R, hold to 15:55}. Window 09:50-15:00 (bar close).

## RB2 — VWAP 2-SD absorption reversal long (r/Trading 1xcgb79, adapted from ES/NQ), 4 configs
- Session z = vwapDistPct / expanding std of vwapDistPct over the session's bars so far (5m proxy of the VWAP SD band;
  needs >= 6 prior bars).
- Extension: at least one of the previous 3 bars had z <= -2; current bar closes back above -2 (z > -2) and closes
  above the previous bar's high.
- Delta proxy {A: bull_div == 1 on any of the last 3 bars (new low not confirmed by RSI) ; B: flow3 > 0 (signed volume
  turned positive while price sat at the low)}.
- Stop: 1c below the lowest low of the last 4 bars (beyond the absorption wick), GEOM S.
- Exit {target = session VWAP at entry ; hold to 15:55}. Window 10:20-15:00.

Total configurations: **12**. BAR90 (rule 22) = 0.9 x max(1.5, sqrt(2 ln 12)) = 0.9 x 2.229 = **2.01**; walk-forward
positive months >= 54%; positive in Bull and Bear sessions; excess over random > 0; avg R without best day reported.
No post-hoc configs. The locked block is not scored unless a config clears every open-history gate.
