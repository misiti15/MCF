# obos_vwap_ma: overbought/oversold + VWAP + moving averages

Educational only — not financial advice.

## Result: no viable setup (0 of 20 finalists passed valid)

Configurations tried: 19,196 (136 single-layer scans, 15,840 three-layer grid
[16 RSI/RSI5 states x 11 VWAP-stretch states x 15 SMA20/SMA50/slope states x 2 sides x 3 geometries],
3,200 fourth-layer extensions of the top 80 triples [40 extras: time windows, volume flip flow3/flow9prev,
wicks, HOD/LOD/PDH/PDL proximity, vol climax, divergence, fromOpen, gap, atrPct, emaDiff, round numbers],
and 20 finalists scored once on valid). VWAP and SMA distances were rescaled to daily-ATR units
(pct * close / 100 / atr_d).

## Baselines (first bar per symbol-day = 09:50 entry)
| | train exp_r | valid exp_r |
|---|---|---|
| long t1s1 | -0.086 | -0.131 |
| long t05s1 | -0.072 (wr .642) | -0.100 (wr .630) |
| short t1s1 | -0.006 | +0.020 |
| short t05s1 | -0.057 (wr .650) | -0.002 (wr .695) |
Breakeven win rate after costs: t1s1 ~0.52, t05s1 ~0.69, t1s05 ~0.35.

## Findings
* Bare extremes carry no edge. RSI<20/RSI5<10 long reversal: exp -0.07..-0.09R (worse than baseline).
  RSI>80 short reversal: -0.03..-0.06R. Win rates come in *below* baseline because the first
  extreme bar often comes later in the day, so more trades end on the 15:55 timed exit.
* VWAP stretch alone (|vwap| > 0.5 daily ATR) and SMA20/SMA50 stretch alone: also flat to negative.
  The only mildly positive single layers were short continuation (price > 0.5 ATR below SMA20/SMA50: +0.03R t1s1).
* On train, the strongest family was **"stretched below SMA50 + short-term momentum turning up" long**
  (e.g. RSI5>90 AND below VWAP AND >0.5 ATR below SMA50: n=908, 22/day, wr .52, +0.165R, PF 1.46, both halves +).
  Fourth layers (flow3>0.3 buyers taking over, fromOpen<-1, 10:30-14:30) pushed it to +0.19..+0.22R.
  High-win t05s1 long version (RSI>70 AND above VWAP AND below SMA20): wr .75, +0.11R on train.
  Short side: overbought on everything (RSI5>95, >0.6 ATR above VWAP, >0.5 ATR above SMA20) +0.09R, wr .54.
* **All of it failed on valid.** Long bounce setups: -0.07..-0.36R (valid). t05s1 longs: wr .44-.62, far below the .69 breakeven.
  Short overbought fade: -0.045R. Best valid result: short RSI5<5 & above VWAP & >0.5 ATR above SMA50 & fromOpen>1,
  +0.023R, n=129, halves +0.13/-0.08: not viable.
* Why: the train P&L was concentrated in a few broad bounce days. For the RSI5>90/VWAP/SMA50 long, the top 5 of
  40 days earned more than the setup's total (160R of 150R total). Signals fire in clusters across hundreds of
  symbols on the same day, so the real sample is about 40 days, not about 900 trades, and the edge was mostly market regime.
  Treat any oversold-bounce result from a single 8-week window as unproven until it holds in a second regime.

## Suggestions for the lead
* Score setups relative to the same-day, same-time-of-day average (market-neutral excess R), or require
  stability over weeks, not halves; the current halves test does not catch day clustering.
* Cap concurrent same-direction entries per day in any live use; these signals are highly correlated.

No candidate files were written (nothing passed the VIABLE bar).
