# T3: MarcoFlow's heat score, revisited (2026-10-11)

*Educational only - not financial advice. Backtests and replays on historical SIP bars; nothing here is paper or live.*

Owner (2026-10-11): "revisit the heat score from MarcoFlow ... never just a cut-and-dry 5 indicators ... a plethora of
factors. We have to find an edge and use it for setups."

Files (this folder): `heat_lib.py` (three heat variants), `fetch_oct9.py` + `case_oct9.py` (Oct-9 case study),
`validate_db.py` (time handling vs MarcoFlow's DB), `build_v2.py` (as-run heat on the 2-year history), `score_hist.py`
(part 3), `heat2.py` (part 4), `results/` (tables). Data in `data/` (git-ignored).

## 1. What MarcoFlow's heat score is

Source: MarcoFlow `lib/heat-tracker.ts` and `lib/candlestick-patterns.ts` (knowledge pack, `data/marcoflow_export/
Folder1_Knowledge.zip`, guides 08/09; heat-tracker also in `research/heat/marcoflow_heat_tracker.ts.md`).

### 1.1 Formula (per symbol, every scan, on Yahoo 5-minute bars, `range=5d`: the last 5 regular sessions + the bar in progress)

| component | range | input | scoring (piecewise) | reads as |
|---|---|---|---|---|
| volumeHeat | -10..+20 | volumeSurge = mean vol last 5 bars / mean prior 15; volumeRatio = last bar vol / 20-bar mean | surge > 2: +20; else ratio > 1.5: min(20, (ratio-1)x20); ratio < 0.5: -10; else (ratio-1)x15 | unsigned activity, scored as bullish |
| rsiHeat | -25..+25 | RSI(14), simple averages (not Wilder) | >=80: -25; 70-80: -(rsi-70)/10x20; <=20: +25; 20-30: (30-rsi)/10x20; 30-45: (45-rsi)/15x10; 55-70: (55-rsi)/15x10 | contrarian |
| momentumHeat | -20..+20 | 0.6 x ROC(5 bars) + 0.4 x ROC(10 bars), % | x8, clamp | trend-following |
| priceActionHeat | -15..+15 | position of close in the 20-bar high-low range | <=0.2: +15; >=0.8: -15; else (0.5-pos)x20 | contrarian |
| trendHeat | -15..+15 | (EMA9-EMA21)/EMA21 % | x5, clamp | trend-following |
| macdHeat | -10..+10 | (EMA12-EMA26)/price % | x20, clamp | trend-following |
| candlestickHeat | -15..+15 | 12 patterns on the last 5 bars (hammer, engulfing, stars, marubozu, 3 soldiers/crows, ...), strength 1-3 x 5, deduped, summed | clamp | mixed (reversal and continuation patterns) |
| vwapHeat | -12..+12 | session VWAP distance % | x12, clamp | trend-following |
| alignment bonus | +-5,+-5,+-3 | volume>5 & momentum>5; rsi>10 & priceAction>5; candle>5 & trend>3 (and mirrors) | | |

heat = clamp(sum + bonus, -100, 100), rounded. mode BUY if heat > 20, SELL if < -20; "redline" |heat| >= 70.
No normalisation across symbols or volatility: thresholds are in raw %, so the same heat means very different moves on
a 0.5%-ATR name and a 5%-ATR name. No time-of-day term.

**Design defects found while reconstructing it (all observed in code/DB, not inferred):**
1. **The volume component was effectively a constant.** Yahoo's last 5m point is the bar in progress with volume 0, so
   `volumeRatio` = 0 in 108,864 of 108,967 live DB rows. volumeHeat is therefore -10 (79% of live rows) or +20 (when
   volumeSurge > 2, 21%) and never anything else. This built a **-10 bearish bias** into every reading, which is one
   reason the recorded signals are 73% SHORT (80,063 short vs 28,904 long).
2. **rsiHeat is discontinuous**: RSI 30.1 scores +9.9, RSI 29.9 scores +0.2 (and mirror at 70). Oct-9 CAT shows it:
   SIP RSI 30.6 -> V2 heat 27, Yahoo RSI 29.0 -> MarcoFlow 19.
3. **Half the components are contrarian and half trend-following**, so in a strong move they cancel; at an extended top
   the contrarian ones (rsi -25, priceAction -15) dominate and the score goes SELL - i.e. "heat" is not one concept.
   The 2026-10-06 study (research/heat/HEAT_STUDY.md) found all components behave as mean reversion at this horizon.
4. The candlestick component is saturated: |candlestick| = 15 in 57% of live rows (one engulfing bar = +-15).
5. The MACD "signal" line is `macd x 0.9` (a placeholder); only the raw MACD level is used.

### 1.2 Time handling (measured)
- Every scan recomputes from scratch on the last 5 sessions (EMAs SMA-seeded; VWAP resets per ET day). Scans every
  5 minutes (cron); the DB stores signals with |heat| >= 30 only, deduped 90 min per symbol+direction.
- `validate_db.py`: on 2,952 live rows (60 lab symbols, Jun-Oct 2026), V2 recomputed on SIP bars completed by the
  observation time agrees best at **lag 0** (sign agreement 96.5%, corr 0.88, candlestick equal 66%); at an assumed
  15-min lag agreement falls to 78% / 0.37. So the recorded heat describes the bars available at the recording time;
  the "15 min delay" in MARCOFLOW_CONTEXT shows up in entry latency, not in the stored heat. V2 differs from the
  recorded value mostly through the in-progress bar's partial price (|diff| <= 3 in 36% of rows).
- MarcoFlow's own `/api/heat-tracker` snapshot for the Oct-9 close (read 2026-10-11, weekend): V2 on SIP bars
  reproduces it: AAPL 24/24, SPCX -26/-26, TSLA 20/20, SPY 28/27, CAT 27/19 (RSI 30.6 vs 29 across the rsi jump).

### 1.3 How MarcoFlow used it
- **Signal = heat sign.** |heat| >= 30 -> record; heat > 0 -> LONG, < 0 -> SHORT (i.e. the score itself is the direction).
  Outcome tracker: 4 market hours, target +1.0% (before 10:00) / +0.75%, stop -1.5% (fixed %, not volatility-scaled).
- **Review agent** mines rule stacks: one heat layer (heat-40/50/60/70) x session/regime/RSI/flow/volatility layers,
  ranked by Wilson lower bound; alerts at LB >= 60 (58 morning, 68 power hour); "forming" pre-alerts when |heat| is
  within 14 points of a rule's heat floor. Paper LB falls back to |heat| when no rule matches ("heat-proxy").
- **Paper trader** enters alerted signals: $640 portions, longs only as "movers" (momentumHeat <= -5 or >= +5), skip
  ET hours 9 and 12, no shorts at RSI <= 30, skip short rip-fades (momentumHeat >= +5), price >= $3, spread <= 4%;
  exits stop 1.25% (ATR-adjusted later), trail 0.3% after +0.3%, take profit 1.5%, 120-min max hold.
- Result (MARCOFLOW_CONTEXT): 2,123 clean paper trades, -$3,242, 31.8% win; signal level ~0 average return.

### 1.4 How MCF's heat differs
| | MarcoFlow (as run, "V2") | MCF port `mcf/research/heat.py` ("V0", the 2-year frames' `heat`) | MCF setups heat_fade_short / heat_fade_long |
|---|---|---|---|
| bars | Yahoo 5m, 5 sessions + in-progress bar | SIP 5m, completed bars only, continuous history | same as V0 |
| volume | broken: -10 / +20 only | true volumeRatio / surge | not used (weight 0) |
| candlestick | +-15, saturated | omitted (0) | not used |
| direction | sign of heat = trade direction | (study input) | **fade**: weights rsi +1, priceAction +1, momentum -1, vwap -1 (all reversion), plus fromOpen (long) and an ATR cost term |
| gating | |heat| >= 30, rule stacks, LB | - | time window (short 09:50-10:30, stock below open; long 11:05-13:30, gap-up), ADV >= $125M; -FD full-day versions in Testing |
| exits | % stop/trail/TP | - | 1R stop / 1R target, R = 0.25 x daily ATR, flat 15:55 |
On the 2-year history (research/history2y/RESCORE.md) heat_fade_short is +0.017R (t 0.68, fails regime: -0.199R up
sessions / +0.154R down) and heat_fade_long -0.046R (t -1.16). Neither passes the rule-19 gates.

V1 ("formula") = MarcoFlow's formula on completed SIP bars with true volume + candlestick; shown in the Oct-9 tables.

## 2. Pre-declared grid (written before any part-3/4 scoring)

### Data, splits, costs
- MCF open two-year frames via `research/history2y/lib.py` (21 open months 2024-10, 2025-03..2026-10-07; the locked
  block 2024-11..2025-02 is never loaded; the as-run builder drops those dates from the 1-minute cache before any
  computation). Decision bars 09:50-15:00 bar closes. SPY, QQQ, IWM, DIA are market references, not traded.
- **train** = 2024-10 + 2025-03..2025-12; **valid** = 2026-01..2026-10-07. Full open history also reported.
- Trades: first qualifying bar per symbol-day per config (`gates.lab_trades`), t1s1 (1R stop / 1R target, R = 0.25 x
  daily ATR, flat 15:55), production costs with time-of-day entry costs (`gates.prod_r`). Same-time control: the mean
  production R of every symbol at the same date and bar for that side; "excess" = trade R minus that control.
- Gates (rule 19): day-clustered t >= max(1.5, sqrt(2 ln N)), exp > 0 in up AND down sessions (n >= 30 each),
  walk-forward (3-month train / 1-month test) positive share >= 0.6, ex-best-day > 0.

### Turn label (for "does heat anticipate turns")
On 5-minute frame bars within a session, R = 0.25 x daily ATR:
- **top at bar i**: high_i >= max high of bars i-4..i+6, rise into it high_i - min(low_{i-4..i-1}) >= 1R, and drop after
  high_i - min(low_{i+1..i+6}) >= 1R. **bottom**: mirror. Eligible bars: 4 prior and 6 later bars in the session
  (bar closes 10:10..14:30).
- A signal at bar i (decided at its close) **calls** a top/bottom if the turn bar is i or i-1 (the latest a close-based
  signal can still be "at" the turn). Reported: hit rate, tod-matched base rate, lift = hit / base, recall.

### Lineage "heat2-orig" (original heat as-is): N = 100 configurations
Heat variants: V0 (port) and V2 (as-run). Sides scored separately (a config = variant x family x parameter x side).
| family | rule (short side; long is the mirror) | params | configs |
|---|---|---|---|
| H1 level fade | short when heat >= T | T in {20,30,40,50} | 2x4x2 = 16 |
| H2 level follow (MarcoFlow's direction) | short when heat <= -T | T in {20,30,40,50} | 16 |
| H3 change | short when heat_i - heat_{i-3} <= -D | D in {15,25,35} | 12 |
| H4 extreme then roll | short when max(heat_{i-5..i}) >= T and heat_i <= that max - D | (T,D) in {30,40}x{10,20} | 16 |
| H5 component agreement | count of components scoring > +2 (bullish) >= A (V0: 7 comps, V2: 8); fade: short / follow: long | A in {5,6,7} x {fade, follow} | 2x3x2x2 = 24 |
| DB: MarcoFlow's recorded live signals (May 18-Oct 2 2026), joined to the frame bar whose close is the first at/after the record time | |heat| bucket {30-40, 40-50, 50-60, 60+} x {follow, fade} x side | 16 |
t required = sqrt(2 ln 100) = 3.03.

### Lineage "heat2-confluence" (heat 2.0): N = 24 configurations
- Features (all causal, from the frame row and same-bar cross-section): the 7 V0 components, candlestick (V1), V0 and
  V2 heat, heat change over 1 and 3 bars, prior-6-bar heat max/min; raw: rsi, rsi5, momentum, emaDiff, macdPct,
  log volumeRatio, log volumeSurge, pricePosition, vwapDistPct, buyPressure, rsiSlope, atrPct, gap, fromOpen,
  momentum/atrPct, fromOpen/daily-ATR%, dist_pdh/pdl/hod/lod/round_atr, sma20/sma50 distance, sma20 slope, flow3,
  flow9prev, vol_climax, bear_div, bull_div, upper/lower wick, vwapReclaim; time-of-day buckets (5);
  **market block**: SPY heat, SPY fromOpen, SPY momentum, breadth (share of universe above its open), stock minus SPY
  fromOpen and momentum.
- Features clipped at train 0.5/99.5 percentiles, standardised on train. Linear models fitted by ridge
  (lambda = 1e-3 x n) on train only, one per side:
  - M1 target = production R of the t1s1 trade (side);  M2 target = the turn label (bottom for long, top for short).
  - feature sets: **full** and **no-market** (market block removed) - the market-neutral control.
  - entry when score >= the train-score quantile q, q in {99%, 99.5%, 99.8%}.
  2 models x 2 sides x 2 feature sets x 3 thresholds = 24. t required = sqrt(2 ln 24) = 2.52.
- Scored on valid (fit never sees valid). Walk-forward: expanding-window monthly refit over the open history (each
  test month uses only earlier open months), share of positive test months.
- Market-neutral control: (a) full vs no-market features; (b) correlation of the score with the stock's 30-min forward
  return vs with its SPY-residual 30-min return (stock - beta x SPY, beta from train); (c) excess over the same-time
  control.
- Beats original? Compare valid exp and excess vs the best H-config of heat2-orig on valid.
