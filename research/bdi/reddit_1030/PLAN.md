# reddit_1030 pre-declared test plan (written before any scoring)

*Educational only — not financial advice.*

Harness: research/bdi/pod1022/score_batch.py (same as reddit_1029): open two-year history, costs in (1c + 1 bp per
side, time-of-day multiplier, +2c stop fills, x3 extended tier), live earnings blackout removed, locked block
2024-11-01..2025-02-28 never read, same-minute random-entry control (hold), day-clustered t, regime1022 split,
TRAIN <= 2025-12-31 / VALID 2026. Universe ADV20 >= $95M, long only, GEOM S (structural stop), flat 15:55.
Frames are 5-minute bars from the 09:50 bar (no open / raw volume column; volume = volumeRatio, green = close above
the prior 5-min close).

## RC1 — r/RealDayTrading pullback bounce with volume confirmation (backlog reddit-1029-rdt-volconfirm-bounce;
post 1xi1q9s, 2026-10-28; the poster's reply in the comments confirms: lighter volume on the pullback, the bounce
candle must beat it). 6 configs.
- Context (RS stock): fromOpen - spy_fo > 0, vwapDistPct > 0 at the trigger bar, sma50_dist_pct > 0 (5m SMA50 as the
  "above the SMAs" proxy; daily SMAs are not in the frame).
- Level L: EMA8 of 5-min closes (per symbol) or session VWAP (close / (1 + vwapDistPct/100)).
- Test bar p (1 or 2 bars before the trigger, or the trigger itself with p = trigger is NOT allowed): low <= L x 1.001
  and close >= L x 0.998 (tested the level, did not close through it).
- Volume sequence (V arms): volumeRatio(p) < mean volumeRatio of the 3 bars before p (dry-up); trigger bar
  volumeRatio > mean volumeRatio of the 3 bars before the trigger.
- Trigger: within 2 bars after p, close > prior close and close > L (green, closes in trade direction); entry at that
  close. Stop 1c below the lowest low from p to the trigger. Window 10:00-15:00 (bar close).
- Grid: L in {EMA8, VWAP} x exit {target 2R, hold} with the volume sequence (4) + the no-volume parent
  {EMA8, VWAP} x hold (2), to show whether the volume sequence adds anything (beats-parent).

## RC2 — RS stock while SPY pulls back, reclaiming the opening range high with volume (r/RealDayTrading 1x4yzux,
comment on "A+ setup in each market condition": bull trend -> stocks showing RS while SPY pulls back, holding VWAP and
reclaiming the opening range with volume). 4 configs.
- ORH = high of day as of the 09:50 bar (09:30-09:50 range; close + dist_hod_atr x atr_d on the 950 row).
- SPY pullback: spy_fo at the bar <= (running max of spy_fo today up to the bar) - D.
- RS: fromOpen - spy_fo >= +1.0 and vwapDistPct > 0.
- Trigger: prior bar close <= ORH and this bar close > ORH, volumeRatio >= 1.5. First per symbol-day.
- Stop 1c below the lowest low of the last 3 bars (incl. the trigger). Window 10:00-15:00.
- Grid: D in {0.3, 0.6}% x exit {target 2R, hold}.

Total configurations: **10**. BAR90 (rule 22) = 0.9 x max(1.5, sqrt(2 ln 10)) = 0.9 x 2.146 = **1.93** (full bar 2.15);
walk-forward positive months >= 54%; positive in Bull and Bear sessions; excess over random > 0; avg R without best
day and best-day share reported. No post-hoc configs. The locked block is not scored unless a config clears every
open-history gate.
