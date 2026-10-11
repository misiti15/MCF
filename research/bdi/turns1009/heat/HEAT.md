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

## 3. The five Oct-9 moments (`case_oct9.py`, SIP 1-minute bars via alpaca-py, 5-minute heat)
MarcoFlow stopped recording on 2026-10-05 (`/api/observations`: last row 2026-10-05 19:15 UTC), so it has **no Oct-9
signals**; its `/api/heat-tracker` gives only the end-of-day state, which V2 reproduces (section 1.2). The owner's
10-minute bar = two 5-minute bars; "at the moment" below = the two bar closes inside the marked 10-minute bar.
Full 60-minute windows (every bar, every component) are printed by `case_oct9.py`; data in `data/oct9_heat.csv`.

| moment | V2 as-run at the moment | V0 port | what drove it | would MarcoFlow have fired? (|heat| >= 30, sign = direction) |
|---|---|---|---|---|
| AAPL 13:40 long launch | -26 / -23 (SELL side) | -21 / +5 | priceAction -15 (price at the top of its 20-bar range), rsi -9, volume -10 (as-run bug); V0 flips to +20 one bar later only because true volume surged (+20) | no; and the lean was the wrong way (short) |
| AAPL 15:00 short top | -34 / -29 | -12 / -17 | rsi -25 (RSI >= 80) + priceAction -15 outweigh momentum +4, vwap +12, macd +4 | **yes, SHORT at 15:00 (right)**, but the same -25 to -35 reading had been on since 14:30 while price rose 336.4 -> 338.6 |
| SPCX 10:10 short | -16 / -30 | -3 / -10 | momentum -9, vwap -12, volume -10: it follows the drop after it happened | borderline (-30.0 at the 10:20 close, one bar after the turn); at the ~10:00 high it read +40 / +32 (BUY) at 09:45-09:50 |
| CAT 10:10 long V-bottom | -11 / -14 | -9 / -11 | every component near 0 | no; blind to the V |
| TSLA 10:50 short top | -19 / -22 | +3 / -6 | priceAction -15, candle -15 vs macd +10, trend +3 | no |

**False alarms the same day.** V2 had 35 readings with |heat| >= 30 on the four names (09:50-15:55 closes); with
MarcoFlow's 90-minute dedupe that is **12 signals, 1 at a marked moment (AAPL 15:00)**. Measured 30 minutes later in the
signal's direction: 4 positive (+46, +27, +10, +3 bps), 7 negative (-10 to -48 bps), 1 flat. V0 (MCF port) had 7 deduped
signals, none at a marked moment. SPY read <= -30 in 22 bars of a day it drifted up: the -10 volume bias at work.

**Read:** heat caught 1 of 5 moments (the overbought top, via RSI >= 80), late by design on the trend side
(SPCX), blind on the V-bottom (CAT) and the TSLA top, and leaning the wrong way at the AAPL launch (priceAction scores a
breakout as "near resistance"). This is hindsight on 5 owner-picked bars, not a test.

## 4. Historical check (`score_hist.py`, results/orig_summary.csv; lineage heat2-orig, N = 100, t bar 3.03)

### Failures first
- **99 of 100 configurations lose after costs over the open history; 0 reach the t bar.** The one positive config is
  MarcoFlow's own recorded signals with |heat| 50-60 traded as a *fade short* (n 173, +0.087R, t 0.82, valid-only
  window, up sessions -0.054R, 2 of its months) - a small-sample, regime-flattered cell, not an edge.
- **MarcoFlow's own direction (follow the heat sign) loses everywhere.** On its recorded live signals (May 18 - Oct 2
  2026, entered at the first SIP bar close at/after the record time): |heat| 30-40 follow-long -0.168R (n 2,622,
  t -4.5), 40-50 -0.185R, 50-60 -0.251R; follow-short -0.044 / -0.045 / -0.068R. Recomputed on two years (H2): -0.086
  to -0.154R in all 16 cells. Stronger heat is *worse* when followed.
- The after-cost hurdle is large: a random bar traded t1s1 costs about 0.1R (all-bar baseline: long -0.095R / -0.097R,
  short -0.113R / -0.064R, train / valid). Any heat rule needs > +0.1R of gross edge to break even.

### Turn anticipation (base rate: a top at bar i or i-1 on 1.76% of eligible bars, a bottom 1.95%)
| config (side) | signal bars | hit rate | tod-matched base | lift | trades: exp R (excess vs same-time) |
|---|---|---|---|---|---|
| H5-v2 agree >= 6 fade (short: >= 6 of 8 as-run components bullish) | 23.5k days | 14.6% | 1.47% | **10.0x** | -0.119 (-0.004) |
| H1-v2 heat >= 50 fade (short) | 21.4k | 13.6% | 1.44% | **9.4x** | -0.145 (-0.026) |
| H1-v2 heat >= 30 fade (short) | 167k | 5.6% | 1.56% | 3.6x | -0.110 (-0.013) |
| H1-v0 heat >= 40 fade (short) | 145k | 4.2% | 1.29% | 3.2x | -0.116 (-0.016) |
| H1-v2 heat <= -50 fade (long) | 119k | 4.4% | 2.24% | 1.9x | -0.101 (+0.002) |
| H2 follow (any) | | | | 0.3-1.8x | -0.09 to -0.15 |
| H3 heat change 15-35 pts / 15 min | | | | 0.9-1.5x | -0.09 to -0.11 |
| H4 extreme-then-roll | | | | 1.0-2.0x | -0.10 to -0.12 |
- **Extreme positive heat does flag tops** (lift 9-10x) - largely mechanical: V2 >= 50 needs RSI high and price at
  the top of its 20-bar range, i.e. the bar *is* a local high. But 86% of those bars are not followed by a 1R drop
  inside 30 minutes, recall is ~1% of all tops, and the trade loses -0.12 to -0.15R after costs with ~0 excess over
  same-time controls. Flagging the top bar is not the same as a tradeable edge.
- Bottoms are much weaker (lift <= 3x), as the CAT V showed.

### Best excess (skill net of the same-time control), still negative after costs
| config | n | exp R | t | excess | train / valid excess | up / down sessions |
|---|---|---|---|---|---|---|
| H5-v0 agree >= 6 fade-long (>= 6 of 7 components bearish -> buy) | 5,700 | -0.079 | -2.49 | +0.044 | +0.025 / +0.062 | +0.095 / -0.215 |
| H5-v2 agree >= 6 fade-long | 150,618 | -0.074 | -4.36 | +0.028 | +0.021 / +0.034 | +0.165 / -0.259 |
| H5-v0 agree >= 5 fade-long | 158,487 | -0.082 | -4.82 | +0.020 | +0.011 / +0.028 | +0.164 / -0.274 |
Component *agreement* (all bearish at once) carries a little reversal skill on the long side (+0.02 to +0.04R over
same-time controls in both train and valid) but it is far below costs and lives entirely in up sessions - the same
regime trap as heat_fade_long. Walk-forward positive share for every config <= 0.5 (most 0-0.11). Regime: every
short config is negative in up sessions, every long config negative in down sessions.

## 5. Amendment A1 (owner clarification via the lead, 2026-10-11; recorded BEFORE the amended scoring)
The owner's target is the **move after a turn of >= 0.5% price change**; R units stay as the secondary view. Only entries
at or after 09:50 ET (the frames already start at the 09:50 bar close, so sections 2-4 comply). Context should include the
previous few hours and the previous day. Owner's five marked moves: AAPL +1.18% (13:49), AAPL -0.71% (15:14), SPCX -1.21%
(10:13), CAT +1.29% (10:11), TSLA -2.18% (10:51). T1's case study (`../CASES.md`) found heat added nothing at those moments,
consistent with section 3.

Amended definitions (everything else as section 2):
- **Turn label P**: as section 2 but with the 1R thresholds replaced by **0.5% of the bar's close** (rise into the extreme
  >= 0.5% over the prior 4 bars, move away >= 0.5% within the next 6 bars = 30 min).
- **Trade P**: target 0.5% / stop 0.5% from the signal bar's close, first touch on 5-minute bars (both in one bar = loss),
  else exit at the last frame bar (15:00 close; the frames stop there, a slightly earlier flat than the lab's 15:55),
  production costs with time-of-day entry costs (`gates.prod_r` with R = 0.5% of price), reported in R(=0.5%) units.
- **heat2-orig-P**: the same 100 rules re-scored on turn P / trade P = 100 more configurations; lineage heat2-orig now
  N = 200, t bar sqrt(2 ln 200) = 3.26.
- **heat2-confluence-P**: the 24 heat-2.0 configurations re-fitted with P targets (M1: trade-P R, M2: turn-P label) and the
  context block added: prior-day range/ATR, prior-day close location (closing strength), prior-day open-to-close return,
  5-day return (trend), prior-day high/low distance (already in), overnight gap (already in), return over the prior 60
  and 120 minutes and distance to the prior-2-hour high/low in ATR (both cross into the previous day early in the
  session), counts of earlier tests of the intraday high/low (bars that came within 0.025 ATR of the running extreme
  without breaking it). Lineage N = 48, t bar sqrt(2 ln 48) = 2.78.
- **Not available:** premarket high/low/move. The two-year 1-minute cache is regular-session only (09:30-15:59), so
  premarket features cannot be tested on history; they would need a new download (T1 used them only on Oct 9).

## 6. Heat 2.0, R view (`heat2.py`, lineage heat2-confluence, N = 24, t bar 2.52; results/heat2_*.csv)

### Failures first
- **All 24 configurations lose after costs on valid (2026-01..10-07) and in the walk-forward.** Best valid:
  M1-long-nomkt q99.8 -0.027R (n 10,960, t -1.00); best walk-forward (expanding monthly refit, 18 test months):
  -0.063R with 11% of months positive. No config reaches the t bar, the regime gate (every long config is negative in
  down sessions, every short config negative in up sessions) or the walk-forward share (max 0.22).
- **It does not beat the original heat.** On valid the best original cell, H5-v0 agree >= 6 fade-long (n 2,935),
  is -0.015R / excess +0.062 vs heat 2.0's best -0.027R / excess +0.050. Heat 2.0 trades 4x more at a similar edge.
- **Out-of-sample predictive power is ~0.** Correlation of the score with the stock's 30-min forward return (direction-
  signed): M1-long-full +0.015 on train (in-sample) -> -0.003 on valid; with the SPY-residual return (beta 1.10)
  +0.004 -> +0.002. Part of the in-sample fit was market timing (train corr with SPY's own forward return +0.026, valid
  -0.016). M2 (turn-label) models: |corr| <= 0.007 everywhere.

### What there is
- **Same-time excess is small but consistent for M1:** +0.02 to +0.05R over the same-bar average of all stocks, in
  train, valid and walk-forward (wf excess +0.004 to +0.036), for both full and no-market feature sets - so the little
  skill there is is stock-specific, not market timing. It is about a third to a half of the ~0.1R cost of a t1s1 trade.
- Learned weights (standardised, M1-long-full top): macdPct -0.089, dist_round_atr -0.055, emaDiff/trendHeat +0.041,
  rel_mom +0.037, sma20_dist -0.036, fromOpen +0.026, momentumHeat -0.018. Mixed trend/reversion terms - a "plethora"
  of factors re-learns the same small, mostly reversion-flavoured effect that the original components carry.
- RAM note: the fit/threshold step peaked at 2.9 GB once (over the 2.5 GB guide) before the sample was cut to 2% for
  the amended run.

## 7. Amended A1 results: 0.5% moves (results/P_*.csv)

### 7.1 Original heat, P view (heat2-orig-P, 100 more configs; lineage N = 200, t bar 3.26)
- **Failures first: 94 of 100 lose after costs; 0 reach the t bar (max t 0.93).** The 6 positive cells are tiny or flat:
  H5-v0 agree 7 fade-short n 11; DB |heat| 40-50 fade-short n 763 +0.049R (t 0.75, May-Oct 2026 only, walk-forward 0);
  H5-v2 agree 7 follow-long n 89; H5-v0 agree >= 6 fade-long n 5,700 **+0.006R (t 0.21; train +0.029 / valid -0.015;
  up +0.055 / down -0.056)**; DB 50-60 fade-short n 173; DB 60+ follow-short n 251 (+0.004).
- **MarcoFlow's own direction still loses**: recorded signals followed long -0.06 to -0.18R, followed short -0.007 to
  -0.030R (R = 0.5%), every one negative in up sessions for shorts / down sessions for longs.
- Baseline (random bar, +-0.5% bracket, production costs): long -0.024 / -0.037R, short -0.022 / -0.016R (train / valid).
- Turn base rate (>= 0.5% swing at bar i or i-1): tops 5.6%, bottoms 5.8% of eligible bars. Extreme fade signals again
  sit on tops (H5-v2 agree >= 6 fade-short: hit 24.5% vs 5.2%, lift 4.7x; H1-v2 heat >= 50 fade-short lift 3.9x), but
  the trades lose (-0.096R and -0.121R) because the first 0.5% after the flagged bar is as likely up as down.
