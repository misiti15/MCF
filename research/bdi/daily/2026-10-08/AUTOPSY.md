# BDI autopsy: primary account, 2026-10-08

*Educational only — not financial advice. These are live **paper** results from one session. They are a diagnosis, not evidence (rule 7). Lab and history numbers are labelled separately below. No locked holdout was scored here.*

Inputs:
- the trade export (48 journal rows) and a read-only copy of `origin/mcf-data:journal.db` / `status.json` (EOD 15:55 ET)
- SIP 1-minute bars fetched read-only for the 39 traded symbols plus SPY/QQQ/IWM (`data/cache/bdi1008/`, git-ignored)
- Alpaca news headlines for the traded symbols (read-only)

The Testing account did not trade today because it was not opened.

Scripts:
- `autopsy.py` produces `trades.csv`, with one row per journal trade and every column used below.
- `tests.py` runs the hypothesis tests and writes the `tests_*.csv` files.

## Failures first
- **The day was red again: the third red day in a row.**
  - Real trades: 39, 16 green (41%), average −0.166R, journal P/L **−$121.03** (cost-adjusted −$141.17).
  - Broker-realized P/L is −$83.72. The $37 gap between journal and broker is **not reconciled** here (see housekeeping H-3).
  - Since the start: 108 journal trades, −$503.
- **exhaustion_short lost $105.68 of the $121.03.** It took 15 trades, 4 green, average −0.44R.
  - 10 of the 15 entries fell between 13:00 and 13:45: −$88.01, average −0.56R.
  - That window was a small-cap rally against a falling Nasdaq: IWM went from −0.51% at 11:00 to +0.40% at 14:00, while QQQ fell to −1.27% at 13:00. The setup shorted names that were up 2–5% from the open into that rally.
  - The 2-year re-score already rates this setup **retire**: −0.010R over 5,973 lab trades, t −0.32, walk-forward share 0.29 (`research/history2y/RESCORE.md`).
- **Every live exit what-if is diagnosis only.** Breakeven at +0.5R would have improved the day by +6.96R against the simulated base (−9.69R → −2.73R), and tp0.5 by +5.4R. But the same exits failed on 44 backtest sessions in the 10-07 autopsy and the 489-configuration EXIT_STUDY. Today's lab check (H3 below) shows the t05s1 geometry losing to each setup's native geometry for most setups on train. This is the hindsight trap; nothing is proposed from it.
- **Hindsight check: the opposite side would have hit +1R first on 17 of 23 losers, but no rule known at entry picks those trades out** (section below).
- **Both nightly-loop hypotheses failed.** The exhaustion entry-rate cap made the kept trades worse on the history, and multi-setup consensus lowers expectancy. 100 configurations were tried; the 2 lab-gate passers failed on the 2-year history. Details in "Tests".

## Versus yesterday (2026-10-07)
| | 10-07 | 10-08 (real trades) | change |
|---|---|---|---|
| trades | 16 | 39 (+9 stacking artifacts) | +23 |
| win rate | 25% | 41% | +16 pp |
| avg R | −0.318 | −0.166 | +0.15R |
| journal P/L | −$262.03 | −$121.03 (broker −$83.72) | +$141 |

- **Better, but not good enough.** The result is still negative, and the improvement is not evidence.
  - The 10 owner-directed setups that went live on 10-08 netted **−$11.6** on 18 real trades: MF1–5 −$53.3, NS2 +$33.3, NS4 +$8.3. The 9 artifacts add +$0.4.
  - orb20_a made +$4.3. heat_fade_long lost $8.0.
  - exhaustion_short alone is the red day.
- **Why the day was not better:** one setup took one correlated cluster of fades into a sector-rotation rally. 10-07's driver was different: news/earnings names in orb20_a and wrong-side fades in heat_fade_long. Different scenarios lose in different ways, which fits a book of fade setups with no edge proven across regimes. The 2-year re-score keeps none of the live setups ("keep 0").
- **What is being tried next:** the two nightly-loop hypotheses (below; both fail as risk/quality rules) and two new backlog items (a material-news filter and the MF4 exit geometry). The re-score's retire list is also recommended to the lead.

## Market context
- SPY: gap −0.30%, open to close −0.13%. QQQ: gap −0.49%, open to close −0.85%; it fell to −1.27% at 13:00, then recovered to −0.76% by 14:00. IWM: gap −0.50%, open to close **+0.45%**.
- This was a rotation day. Large-cap tech fell while small caps rallied from 12:30 on, and the afternoon short-fade book was on the wrong side of that rally.

## Stacking-bug artifacts (excluded from the per-trade stats)
Nine journal rows are duplicate brackets from the stacking bug, now fixed (one position per symbol, #13). Each was flattened within seconds at about $0, and the setup's real trade is kept. EDV, GDXJ and KMI got 3 brackets each; SHW and ARKK got 2.

| id | sym | setup | entry | exit | P/L |
|---|---|---|---|---|---|
| 91 | EDV | MF1-945-flowsell-vwapup | 09:50:30 | 09:50:30 | $+0.00 |
| 92 | EDV | MF4-h40-open-flowsell | 09:50:29 | 09:50:30 | $+0.00 |
| 93 | EDV | MF5-flowsell-vwapup-rsi5hi | 09:50:29 | 09:50:30 | $+0.00 |
| 94 | GDXJ | MF3-open-flowsell-rsi5hi | 10:00:37 | 10:00:41 | $+0.02 |
| 95 | GDXJ | MF5-flowsell-vwapup-rsi5hi | 10:00:38 | 10:00:41 | $+0.19 |
| 96 | KMI | MF3-open-flowsell-rsi5hi | 10:20:38 | 10:20:39 | $+0.00 |
| 97 | KMI | MF5-flowsell-vwapup-rsi5hi | 10:20:39 | 10:20:39 | $+0.00 |
| 100 | SHW | MF5-flowsell-vwapup-rsi5hi | 10:45:42 | 10:45:43 | $+0.00 |
| 101 | ARKK | MF5-flowsell-vwapup-rsi5hi | 10:50:21 | 10:50:21 | $+0.16 |

- They total **+$0.37**.
- The EOD headline (48 trades, WR 39.6%) counts them. Excluding them gives 39 trades and WR 41%.
- Reporting fix: see H-2.

## Per-trade autopsy (39 real trades)
How to read the table:
- **R** = |entry − stop| as executed. For t1s05 setups (MF1, MF2, NS4) the executed R is half the lab R, so their target shows up as about +2R.
- **Rule values** are recomputed the way LabStrategy and HeatStrategy saw them live: 40 prior 5-minute bars plus today's complete bars up to the signal, and ATR(14) from prior days. **All 38 lab/heat signals re-qualify on the recomputation** (`mask_recomputed`). orb20_a is not a lab mask.
- **MFE/MAE**: "held" runs from entry to exit; "day" runs from entry to the 15:55 close.
- **What-ifs** are net of production costs (1c + 1 bps per side, +2c on stops), walked on 1-minute bars, stop first inside a bar, from the minute after entry:
  - **BE0.5**: stop moves to breakeven at +0.5R, live target kept.
  - **trail**: a 0.5R trail starts after +0.5R, no target.
  - **tp0.5 / tp1**: fixed targets with the live stop.
  - **hold 15:55**: live stop, no target.
  - **SAR**: stop-and-reverse at the stop, 1R/1R.
  - **re-entry**: same side again at the first 5-minute close back through the entry after a stop, 1R/1R.
  - **opposite 1R/1R**: the other side from the same entry with the same R.

| id | sym | setup | side | in-out (ET) | exit | r live | rule values at signal (recomputed) | held MFE / MAE (R) | t→MFE held / day (min) | day MFE to 15:55 | BE0.5 | trail | tp0.5 | tp1 | hold 15:55 | SAR | re-entry | opposite 1R/1R | loss type |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 98 | GDXJ | MF1 | S | 10:00-10:31 | stop | -0.99 | heat -35, bp -0.26, vwap +0.47%, rsi5 90, rsi 85 | 0.45 / -1.11 | 11 / 121 | 1.82 | -1.09 | -1.09 | -1.09 | -1.09 | -1.09 | -2.19 | -0.16 | +0.94 (target) | stopped_then_reversed |
| 99 | SCZ | orb | L | 09:52-10:34 | target | +1.38 | OR break, fromOpen +0.3%, rsi 21 | 1.48 / -0.85 | 42 / 42 | 1.48 | +1.04 | -0.27 | +0.23 | +0.73 | -1.42 | +1.04 | +1.04 | -1.42 (stop) | win |
| 102 | SBUX | MF4 | S | 10:45-10:55 | stop | -1.00 | heat -42, bp -0.34, vwap -0.28%, rsi5 34, rsi 35 | 0.04 / -1.03 | 7 / 96 | 4.09 | -1.10 | -1.10 | -1.10 | -1.10 | -1.10 | -2.20 | -0.17 | +0.93 (target) | stopped_then_reversed |
| 103 | EDV | MF3 | S | 09:50-11:00 | target | +0.62 | heat -44, bp -0.58, vwap +0.27%, rsi5 100, rsi 80 | 0.62 / -0.51 | 70 / 73 | 0.86 | +0.51 | +0.20 | +0.40 | -1.17 | -1.17 | +0.51 | +0.51 | +0.90 (target) | win |
| 104 | ITUB | NS2 | S | 10:35-11:06 | target | +0.92 | sma50 x-up (+0.46%), rsi 67, fromOpen +2.5% | 1.07 / -0.51 | 31 / 84 | 1.63 | +0.67 | +0.70 | +0.28 | +0.78 | +0.59 | +0.67 | +0.67 | -1.43 (stop) | win |
| 105 | GLD | MF1 | S | 10:25-11:10 | target | +2.13 | heat -32, bp -0.47, vwap +0.14%, rsi5 62, rsi 76 | 2.20 / -0.85 | 45 / 101 | 3.56 | +1.92 | +0.78 | +0.37 | +0.87 | -1.16 | +1.92 | +1.92 | -1.16 (stop) | win |
| 106 | EWC | MF1 | S | 10:20-11:14 | target | +1.67 | heat -30, bp -0.39, vwap +0.11%, rsi5 58, rsi 68 | 1.78 / -0.56 | 51 / 73 | 2.33 | +1.32 | +1.20 | +0.15 | +0.65 | -1.57 | +1.32 | +1.32 | -1.57 (stop) | win |
| 107 | PG | MF4 | S | 10:45-11:13 | target | +0.65 | heat -48, bp -0.34, vwap +0.37%, rsi5 30, rsi 85 | 0.79 / -0.39 | 28 / 29 | 0.91 | +0.55 | +0.28 | +0.41 | -1.13 | -1.13 | +0.55 | +0.55 | +0.91 (target) | win |
| 108 | NOW | hfl | L | 11:10-11:21 | stop | -1.04 | score 59.5 (>=57.5), gap +1.02%, fromOpen -1.5%, rsi 19 | -0.16 / -1.02 | 1 / 281 | 2.19 | -1.05 | -1.05 | -1.05 | -1.05 | -1.05 | -2.10 | -0.09 | +0.96 (target) | stopped_then_reversed |
| 109 | ARKK | MF3 | S | 10:50-11:32 | target | +0.80 | heat -31, bp -0.41, vwap +0.19%, rsi5 70, rsi 80 | 0.79 / 0.00 | 41 / 157 | 2.24 | +0.74 | +0.55 | +0.44 | +0.94 | +0.85 | +0.74 | +0.74 | -1.09 (stop) | win |
| 110 | XOP | MF4 | S | 10:30-11:46 | stop | -1.00 | heat -41, bp -0.40, vwap +0.12%, rsi5 57, rsi 82 | 0.33 / -1.00 | 5 / 105 | 0.72 | -1.08 | -1.08 | -1.08 | -1.08 | -1.08 | -2.15 | -0.13 | +0.94 (target) | small MFE then failed (0.15-0.5R) |
| 111 | SW | MF2 | S | 10:45-12:03 | stop | -1.01 | heat -32, bp -0.47, vwap -0.49%, rsi5 8, rsi 59 | 1.66 / -1.04 | 40 / 40 | 1.66 | -0.29 | +0.87 | +0.33 | +0.83 | -1.29 | -0.45 | -2.57 | -1.29 (stop) | gave_back_gains |
| 112 | SHW | MF3 | S | 10:45-12:17 | stop | -1.15 | heat -35, bp -0.35, vwap +0.42%, rsi5 79, rsi 83 | 0.78 / -1.26 | 36 / 36 | 0.78 | +0.72 | +0.23 | +0.46 | -1.05 | -1.05 | +0.72 | +0.72 | +0.96 (target) | gave_back_gains |
| 113 | GEV | NS4 | S | 11:30-12:17 | stop | -1.38 | vwap reclaim (+0.04%), rsi 30, fromOpen +2.5% | 0.65 / -1.38 | 19 / 94 | 5.91 | -0.04 | +0.11 | +0.46 | -1.04 | -1.04 | -2.08 | -0.08 | +0.96 (target) | stopped_then_reversed |
| 114 | NET | NS2 | S | 10:30-12:54 | target | +0.63 | sma50 x-up (+0.35%), rsi 62, fromOpen +2.0% | 0.75 / -0.77 | 139 / 272 | 1.76 | +0.59 | +0.41 | +0.48 | +0.98 | +0.91 | +0.59 | +0.59 | -1.02 (stop) | win |
| 115 | CRM | hfl | L | 11:15-12:52 | target | +0.63 | score 64.2 (>=57.5), gap +0.41%, fromOpen -1.8%, rsi 18 | 0.65 / -0.53 | 97 / 271 | 2.36 | +0.57 | +0.98 | +0.47 | +0.97 | +2.16 | +0.57 | +0.57 | -1.03 (stop) | win |
| 116 | BOIL | hfl | L | 12:25-12:55 | target | +1.21 | score 59.8 (>=57.5), gap +2.80%, fromOpen -7.6%, rsi 10 | 1.50 / -0.08 | 30 / 116 | 2.31 | +1.02 | +1.01 | +0.44 | +0.94 | +1.09 | +1.02 | +1.02 | -1.12 (stop) | win |
| 117 | PYPL | MF5 | S | 12:35-12:54 | stop | -0.96 | heat -38, bp -0.30, vwap +0.45%, rsi5 76, rsi 85 | 0.07 / -1.01 | 4 / 4 | 0.07 | -1.14 | -1.14 | -1.14 | -1.14 | -1.14 | -1.07 | -1.48 | +0.92 (target) | never_worked |
| 118 | PATH | MF5 | S | 12:40-13:16 | stop | -0.99 | heat -31, bp -0.27, vwap +0.21%, rsi5 88, rsi 79 | 0.68 / -1.14 | 10 / 10 | 0.68 | -0.32 | -0.14 | +0.33 | -1.32 | -1.32 | -2.65 | -0.50 | +0.83 (target) | gave_back_gains |
| 119 | SQQQ | exh | S | 13:00-13:20 | stop | -1.01 | rsi5 100, sma20 +1.72%, bear_div 1, fromOpen +2.2% | 0.91 / -1.01 | 14 / 88 | 1.04 | -0.25 | -0.11 | +0.36 | -1.25 | -1.25 | -0.39 | -2.50 | +0.86 (target) | stopped_then_reversed |
| 120 | BABA | hfl | L | 11:05-13:23 | stop | -1.01 | score 58.3 (>=57.5), gap +1.18%, fromOpen -2.2%, rsi 16 | 0.55 / -1.03 | 8 / 8 | 0.55 | -0.08 | -0.03 | +0.44 | -1.08 | -1.08 | -2.16 | -0.14 | +0.94 (target) | gave_back_gains |
| 121 | IONQ | hfl | L | 11:35-13:26 | stop | -1.00 | score 62.0 (>=57.5), gap +0.90%, fromOpen -4.6%, rsi 13 | 1.01 / -1.12 | 42 / 42 | 1.01 | -0.08 | +0.44 | +0.46 | +0.96 | -1.08 | -1.64 | -0.70 | -1.08 (stop) | news_earnings |
| 122 | KMI | MF1 | S | 10:20-13:27 | stop | -1.04 | heat -37, bp -0.53, vwap +0.39%, rsi5 79, rsi 80 | 1.00 / -1.04 | 5 / 5 | 1.00 | -0.37 | +0.13 | +0.29 | -1.37 | -1.37 | -2.74 | -0.90 | +0.79 (target) | gave_back_gains |
| 123 | Z | exh | S | 13:35-13:43 | stop | -1.15 | rsi5 93, sma20 +1.28%, bear_div 1, fromOpen +4.8% | -0.04 / -1.61 | 1 / 1 | -0.04 | -1.17 | -1.17 | -1.17 | -1.17 | -1.17 | -0.27 | -0.27 | +0.90 (target) | wrong_side_after_big_swing |
| 124 | LDOS | exh | S | 13:35-13:44 | stop | -1.11 | rsi5 93, sma20 +2.09%, bear_div 1, fromOpen +4.8% | 0.30 / -1.08 | 3 / 3 | 0.30 | -1.07 | -1.07 | -1.07 | -1.07 | -1.07 | -2.13 | -2.13 | +0.96 (target) | news_earnings |
| 125 | AGNC | exh | S | 13:45-14:45 | stop | -0.96 | rsi5 90, sma20 +1.07%, bear_div 1, fromOpen +2.2% | 0.32 / -0.96 | 3 / 3 | 0.32 | -1.67 | -1.67 | -1.67 | -1.67 | -1.67 | -1.65 | -2.42 | +0.65 (target) | small MFE then failed (0.15-0.5R) |
| 126 | NLY | exh | S | 13:45-14:59 | stop | -1.01 | rsi5 95, sma20 +1.06%, bear_div 1, fromOpen +2.2% | 0.29 / -1.01 | 7 / 7 | 0.29 | -1.32 | -1.32 | -1.32 | -1.32 | -1.32 | -1.36 | -1.63 | +0.83 (target) | small MFE then failed (0.15-0.5R) |
| 127 | VTRS | exh | S | 14:20-15:08 | stop | -1.01 | rsi5 96, sma20 +1.07%, bear_div 1, fromOpen +0.5% | 0.19 / -1.04 | 1 / 92 | 0.35 | -1.34 | -1.34 | -1.34 | -1.34 | -1.34 | -2.67 | -0.52 | +0.82 (target) | news_earnings |
| 128 | ACN | exh | S | 13:00-15:11 | stop | -1.04 | rsi5 90, sma20 +1.69%, bear_div 1, fromOpen +2.7% | 0.43 / -1.03 | 9 / 9 | 0.43 | -1.03 | -1.03 | -1.03 | -1.03 | -1.03 | -0.06 | -2.06 | +0.98 (target) | news_earnings |
| 129 | GME | NS4 | S | 14:25-15:15 | target | +1.50 | vwap reclaim (+0.12%), rsi 28, fromOpen +5.0% | 1.60 / -0.75 | 50 / 50 | 1.60 | +1.32 | +0.35 | +0.33 | +0.83 | -1.31 | +1.32 | +1.32 | -1.31 (stop) | win |
| 130 | BBWI | exh | S | 13:30-15:16 | target | +0.96 | rsi5 91, sma20 +1.08%, bear_div 1, fromOpen +0.1% | 1.07 / -0.85 | 106 / 106 | 1.07 | +0.81 | -0.18 | +0.37 | +0.87 | -0.44 | +0.81 | +0.81 | -1.25 (stop) | win |
| 131 | MHK | exh | S | 13:30-15:55 | flatten | -0.20 | rsi5 91, sma20 +1.02%, bear_div 1, fromOpen +2.0% | 0.49 / -0.98 | 108 / 108 | 0.49 | -0.19 | -0.19 | -0.19 | -0.19 | -0.19 | -0.19 | -0.19 | +0.12 (time) | late_hold |
| 132 | IBRX | exh | S | 13:35-15:55 | flatten | -0.16 | rsi5 92, sma20 +1.65%, bear_div 1, fromOpen +2.9% | 0.67 / -0.80 | 85 / 85 | 0.67 | -0.23 | -0.09 | +0.38 | +0.05 | +0.05 | +0.05 | +0.05 | -0.30 (time) | gave_back_gains |
| 133 | BLDR | exh | S | 13:45-15:55 | flatten | +0.13 | rsi5 90, sma20 +1.99%, bear_div 1, fromOpen +2.9% | 0.45 / -0.43 | 94 / 94 | 0.45 | +0.15 | +0.15 | +0.15 | +0.15 | +0.15 | +0.15 | +0.15 | -0.24 (time) | win |
| 134 | BP | MF5 | S | 13:45-15:55 | flatten | +0.57 | heat -36, bp -0.39, vwap +0.52%, rsi5 86, rsi 82 | 0.71 / -0.07 | 125 / 125 | 0.71 | +0.42 | -0.12 | +0.40 | +0.42 | +0.42 | +0.42 | +0.42 | -0.62 (time) | win |
| 135 | ROIV | exh | S | 14:15-15:55 | flatten | +0.09 | rsi5 100, sma20 +1.27%, bear_div 1, fromOpen +0.3% | 0.45 / -0.69 | 10 / 10 | 0.45 | +0.01 | +0.01 | +0.01 | +0.01 | +0.01 | +0.01 | +0.01 | -0.18 (time) | win |
| 136 | ALHC | exh | S | 14:20-15:55 | flatten | -0.17 | rsi5 100, sma20 +1.20%, bear_div 1, fromOpen +1.7% | 0.66 / -0.47 | 33 / 33 | 0.66 | -0.31 | -0.16 | +0.34 | -0.56 | -0.56 | -0.56 | -0.56 | +0.23 (time) | gave_back_gains |
| 137 | SMMT | exh | S | 14:20-15:55 | flatten | +0.23 | rsi5 100, sma20 +1.10%, bear_div 1, fromOpen -1.9% | 0.46 / -0.43 | 94 / 94 | 0.46 | +0.35 | +0.35 | +0.35 | +0.35 | +0.35 | +0.35 | +0.35 | -0.48 (time) | win |
| 138 | FCEL | exh | S | 14:35-15:55 | flatten | -0.19 | rsi5 91, sma20 +2.14%, bear_div 1, fromOpen -3.9% | 0.10 / -0.79 | 3 / 3 | 0.10 | -0.20 | -0.20 | -0.20 | -0.20 | -0.20 | -0.20 | -0.20 | +0.09 (time) | late_hold |

### What-if totals (R, net of costs; diagnosis only: one session)
`wi_base_sim` is the live geometry re-simulated with the same costs. It is the column to compare against, because the live r column is gross.

| setup | n | wi_base_sim | wi_be0.5 | wi_trail0.5 | wi_tp0.5 | wi_tp1 | wi_hold_1555 | r_hold_nostop_1555 | wi_stop_and_reverse | wi_reentry | opp_1r1r | opp_hold_1555 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MF1-945-flowsell-vwapup | 4 | +0.77 | +1.77 | +1.02 | -0.29 | -0.95 | -5.20 | -2.76 | -1.70 | +2.17 | -1.01 | +2.01 |
| MF2-open-rsimidhi-flowsell | 1 | -1.29 | -0.29 | +0.87 | +0.33 | +0.83 | -1.29 | -5.50 | -0.45 | -2.57 | -1.29 | +5.33 |
| MF3-open-flowsell-rsi5hi | 3 | +1.97 | +1.97 | +0.97 | +1.31 | -1.27 | -1.36 | -3.70 | +1.97 | +1.97 | +0.78 | +3.51 |
| MF4-h40-open-flowsell | 3 | -1.63 | -1.63 | -1.90 | -1.77 | -3.31 | -3.31 | -7.31 | -3.81 | +0.25 | +2.78 | +7.09 |
| MF5-flowsell-vwapup-rsi5hi | 3 | -2.04 | -1.04 | -1.40 | -0.41 | -2.04 | -2.04 | -1.97 | -3.30 | -1.56 | +1.12 | +1.62 |
| NS2-sma50break-overbought-short | 2 | +1.26 | +1.26 | +1.11 | +0.76 | +1.76 | +1.50 | +1.50 | +1.26 | +1.26 | -2.45 | -1.74 |
| NS4-pm-vwap-reclaim-oversold-short | 2 | +0.28 | +1.28 | +0.46 | +0.79 | -0.21 | -2.35 | +1.77 | -0.76 | +1.24 | -0.34 | -1.98 |
| exhaustion_short | 15 | -8.42 | -7.46 | -8.01 | -6.04 | -8.37 | -9.68 | -11.53 | -8.13 | -11.12 | +3.99 | +9.82 |
| heat_fade_long | 5 | -1.63 | +0.37 | +1.35 | +0.76 | +0.73 | +0.04 | +4.56 | -4.32 | +0.66 | -1.32 | -4.78 |
| orb20_a | 1 | +1.04 | +1.04 | -0.27 | +0.23 | +0.73 | -1.42 | +0.69 | +1.04 | +1.04 | -1.42 | -0.96 |
| ALL | 39 | -9.69 | -2.73 | -5.79 | -4.33 | -12.09 | -25.10 | -24.26 | -18.20 | -6.66 | +0.85 | +19.91 |


- **Breakeven at +0.5R** would have helped most (+6.96R against base). It helped because 10 losers had first reached +0.5R ("gave back gains").
- **Stop-and-reverse** would have hurt (−8.5R). Nine of the 23 stops kept going in the original direction or chopped.
- **Re-entry** would have been roughly neutral overall (+3.0R), but **−2.7R on exhaustion_short**.
- **Holding to 15:55** would have been the worst choice (−15.4R).
- The median time to MFE while held was 30 minutes; from entry to 15:55 it was 73 minutes.

### Opposite side and the hindsight check
- **The opposite side (1R/1R, same entry) would have hit its target first on 17 of 23 losers, and on 2 of 16 winners.** Over all 39 trades it would have made +0.85R, against −9.69R for the live geometry.
- **No rule known at entry points to the other side.** Four counter-signal flags, each computed at the signal bar:
  - **SPY 30-minute move against the trade:** win rate 44% with the flag (n=18) vs 38% without (n=21).
  - **5-minute SMA20 sloping against the trade:** 41% (n=32) vs 43% (n=7). Almost every trade has it, because these setups are fades by construction.
  - **Fading the day's direction from the open:** 39% (n=33) vs 50% (n=6). Too few unflagged trades to read.
  - **15-minute flow against the trade:** 48% (n=21) vs 33% (n=18), the wrong way round for a warning sign.
- None of the four separates winners from losers. The 10-07 autopsy found the same in the population (no entry-time rule picked out the trades whose opposite side won).
- What "worked" today was the regime, not a rule: small caps up against shorts of up-from-open names. Rule 19's regime gate is the right tool for this, and every live short setup fails it on the 2-year history (up-session expectancy below 0).

## Loss types (one primary type per trade; same precedence as `research/oct7/autopsy/classify.py`)
Precedence: news/earnings, then stopped then reversed, then wrong side after a big swing (≥3% from the open, and the opposite 1R/1R would have won), then gave back gains (MFE ≥ 0.5R), then late hold (flattened red), then never worked (MFE < 0.15R), then small MFE then failed.

| primary type | exh | hfl | MF1 | MF2 | MF3 | MF4 | MF5 | NS2 | NS4 | orb | all |
|---|---|---|---|---|---|---|---|---|---|---|---|
| news / material headline | 3 (ACN, LDOS, VTRS) | 1 (IONQ) | | | | | | | | | **4** |
| stopped then reversed | 1 (SQQQ) | 1 (NOW) | 1 (GDXJ) | | | 1 (SBUX) | | | 1 (GEV) | | **5** |
| wrong side after a big swing | 1 (Z) | | | | | | | | | | **1** |
| gave back gains | 2 (IBRX, ALHC) | 1 (BABA) | 1 (KMI) | 1 (SW) | 1 (SHW) | | 1 (PATH) | | | | **7** |
| late hold (flattened red) | 2 (MHK, FCEL) | | | | | | | | | | **2** |
| never worked | | | | | | | 1 (PYPL) | | | | **1** |
| small MFE then failed | 2 (AGNC, NLY) | | | | | 1 (XOP) | | | | | **3** |
| win | 4 | 2 | 2 | 0 | 2 | 1 | 1 | 2 | 1 | 1 | **16** |

News items (Alpaca headlines; none of them is earnings, so the earnings blackout cannot catch them):
- **VTRS:** $1.65B deal to acquire Pacira, announced 11:47, before the 14:20 short.
- **ACN:** Accenture–Dell business group, announced 12:08, before the 13:00 short. The stock was +2.7% from the open on it.
- **LDOS:** JP Morgan downgrade at 13:39, after the 13:35 short. It was in the trade's favour, but the stock still squeezed up.
- **IONQ:** DARPA headlines the evening before, plus a "what's going on with IonQ" story at 11:16.

### Pattern tally (`research/bdi/patterns.csv`, 3 days, 10-06 and 10-07 backfilled from the 10-07 autopsy)
- **Seen on all 3 days, book-wide:**
  - news/earnings: 11 trades
  - gave back gains: 10
  - late hold: 10
  - stopped then reversed: 8
  - small MFE then failed: 7
- **No single setup × loss type has reached 3 days yet.** The most frequent are orb20_a news (6 trades over 2 days) and exhaustion_short late hold (4 trades over 2 days).
- **Backlog status of each 3-day pattern:**
  - **news/earnings** is a new backlog idea: `bdi-1008-material-news-filter`.
  - **gave back gains** was tested again today as H3 (exit geometries per setup). The breakeven, tp0.5 and trail lineage already failed in EXIT_STUDY and the 10-07 autopsy.
  - **late hold** (an earlier exhaustion exit) and **stopped then reversed** (re-entry after a stop) are already-failed lineages (10-07 autopsy: `exh_timeexit`, `hfs_reentry`). Today's live SAR and re-entry numbers do not reopen them.

## Tests: nightly-loop hypotheses + one pattern check (lab and history only; no locked holdout scored)
Script: `tests.py`. Every configuration was declared in its docstring before any result was seen.

**Configurations tried: 100**
- H1 (rate cap): 30
- H2 (consensus): 44
- H3 (exit geometry): 26

All 100 were scored on lab train (06-30..08-25, 40 sessions) and valid (08-26..09-15, 14 sessions). The same 100 were then re-scored, with no re-selection, on the 2-year history (2024-10..2026-10-07). The history scoring leaves out three blocks:
- the rule-19 locked block 2024-11..2025-02, which is never loaded
- the older holdouts Apr–Jun 2026 and Sep 16–Oct 5 2026, which are dropped

That leaves 340–350 sessions. The history still includes the lab's train/valid dates, so it is not fully out of sample.

How everything is scored:
- **Entries:** as live. Module mask inside the YAML window, point-in-time adv20 ≥ min_adv, first bar per symbol-day.
- **R and exits:** R = 0.25 × daily ATR, exit by 15:55.
- **Costs:** the production haircut of `research/owner1008/scan_fast.py`.
- **Statistics:** day-clustered t.

At p = 0.05, about 5 of the 100 configurations should pass by chance.

**Result: nothing passes. Both nightly-loop hypotheses fail. Two lab-gate passers (MF1 agree≥2 and MF4 on t1s05) fail on the history.**

### H1 `loop-1008-exhaustion-cluster`: cap of k entries per W minutes per setup (30 configurations): FAILED
- **Pre-declared gate:**
  - kept expectancy > 0 and kept − all > 0, on both train and valid
  - random-drop control p < 0.05 on valid (drop the same number of entries per day at random, 1,000 draws)
- **No configuration passes.**
- **Train: the cap hurts every setup.** For exhaustion_short, Δ runs from −0.18 to −0.24R, because the dropped clustered entries made +0.31 to +0.49R on train.
- **Valid: small gains, mostly not significant.**
  - exhaustion_short: Δ from +0.00 to +0.09R, p from 0.03 to 0.43.
  - heat_fade_short: Δ from +0.00 to +0.15R, p ≥ 0.24.
  - heat_fade_long: Δ from +0.03 to +0.10R, p from 0.05 to 0.46.
- **History (t bar 2.61 at N = 30):**

| setup | uncapped exp (n) | capped kept exp, range over 10 caps | dropped exp, range | random-drop p |
|---|---|---|---|---|
| exhaustion_short | −0.040 (4,561) | −0.073 … −0.102 | −0.008 … +0.028 | 1.00 (the cap is worse than random) |
| heat_fade_short | +0.011 (10,513) | −0.019 … +0.008 | +0.013 … +0.016 | 0.71–0.93 |
| heat_fade_long | −0.058 (11,432) | −0.003 … −0.029 | −0.066 … −0.108 | 0.96–1.00 |

- **Reading it:**
  - **For exhaustion_short the hypothesis is backwards.** Clustered entries are not the bad ones; the later entries in a cluster are no worse than the first ones. 10-08's cluster loss was the regime of that afternoon, not the clustering itself.
  - **For heat_fade_long the cap raises the kept expectancy (Δ +0.03 to +0.06), but random dropping matched per day does just as well (p ≥ 0.96).** The gain comes from trading less on heavy days, not from the timing rule, and the kept trades stay negative.
- **Every capped version fails rule 19:** every kept expectancy is ≤ +0.008R, no t reaches 2.61, up-session expectancy stays negative for every short setup, and the best walk-forward share is 0.64 (heat_fade_long W15 k2, which still fails the regime gate).

### H2 `loop-1008-multisetup-consensus`: agreement count among the 13 live masks (44 configurations): FAILED
- **Pooled short book: expectancy falls as more short masks agree, on train and on the history.**

| first bar per symbol-day with ≥ c short masks (t1s1) | train exp (n) | valid exp (n) | history exp (n, t) |
|---|---|---|---|
| c ≥ 1 | +0.070 (4,157) | +0.137 (923) | −0.046 (26,499, −2.71) |
| c ≥ 2 | −0.041 (451) | +0.261 (103) | −0.112 (3,475, −3.53) |
| c ≥ 3 | −0.040 (222) | +0.307 (48) | −0.130 (1,875, −3.33) |
| c ≥ 4 | −0.085 (39) | +0.416 (8) | −0.222 (343, −3.41) |

- Valid rises with c while train and the history fall. Valid is a 14-session down-drift window (rule 19), and the agreeing masks are the MarcoFlow short layers (MF3/MF5 share three conditions). **Consensus is a bigger bet on the same regime, not a quality signal.**
- The t05s1 and t1s05 geometries tell the same story.
- **Long pool:** cl ≥ 2 has n = 15 on train and 6 on valid; history −0.256R (n = 198).
- **Per-setup splits (26 configurations): one lab-gate passer, which fails on the history.**
  - MF1 agree≥2 (t1s05): train +0.022 (n 189), valid +0.371 (n 40, t 3.31). **History −0.109 (n 1,449, t −3.48): FAIL.**
  - heat_fade_short agree≥2: history +0.309 (n 64, t 2.50), but lab n is 7 / 2. NS3 agree≥2: history +0.215 (n 112, t 2.00), lab n 17 / 3.
  - Both fall below the lab n gate and the history t bar (2.75 at N = 44). They are noted as possible follow-ups, not candidates.

### H3 exit geometry per setup (the "gave back gains" pattern, 3 of 3 days; 26 configurations): FAILED
- **Lab gate:** finalist gate, plus beating the native geometry on train and valid.
- **One lab passer:** MF4-h40 on t1s05 instead of its native t05s1. Train +0.016 vs −0.024, valid +0.122 vs +0.046 (n 89, t 1.66). **History −0.124 (n 2,672): FAIL** (native −0.168).
- **The "take profits early" fix (t05s1, i.e. a +0.5R target) is never clearly better on the history.** It is the worst geometry for 6 of 13 setups and the best only for NS1, where it is already the native geometry. The live day's tp0.5/BE0.5 improvement is the hindsight trap again.
- **History, native geometry (diagnosis):** only NS3 (+0.088, t 1.85) and heat_fade_short (+0.011, t 0.40) are positive. The other 11 live lab/heat setups are negative. MF1–5 range from −0.063 to −0.168R: MF2 has t −1.56 (n 455) and the other four t ≤ −3.8.

## Proposed changes
### Housekeeping (no change to which trades are taken or how they exit; can ship after tests pass)
- **H-1. Journal the numeric rule values at entry.** Today `signals.info` holds only the layer text. Store the mask inputs (heat, buyPressure, vwapDistPct, rsi, rsi5, sma20/50 distance, fromOpen, gap, score), so the autopsy does not need to recompute them. Today all 38 recompute cleanly.
- **H-2. Flag stacking-bug artifacts in the EOD stats.** Treat a "flatten" exit less than 60 seconds after entry, on a symbol that already had a position, as an artifact. Exclude those rows from the trade count and WR, and show them separately. The EOD headline said 48 trades / WR 39.6%; the true figures are 39 trades / 41%.
- **H-3. Reconcile journal and broker P/L daily.** Today the journal shows −$121.03 and the broker −$83.72. A per-order fill comparison should be part of the EOD report.
- **H-4. Add a news column to the EOD trade list.** It is display only: any same-day Alpaca headline (M&A, analyst action) before entry. This is reporting, not a filter.

### Setup / strategy (backlog only; gates and the ledger decide; nothing changes during market hours)
- **S-1. exhaustion_short: recommend that the lead act on the re-score verdict "retire".**
  - Evidence: 2-year history −0.010R over 5,973 trades, walk-forward 0.29; 3 live sessions −0.44R over 19 trades. That backtest is what decides; the live sessions only agree with it.
  - A rate cap does not rescue it (H1 failed).
  - Apply it after the close, with a ledger entry.
- **S-2. `bdi-1008-material-news-filter`** (idea): skip a symbol when a same-day material headline (M&A, analyst action, contract) comes before the signal. It needs a news history to test, so it is not tested yet.
- **S-3. H1 / H2 / H3** (see Tests): all failed. They are logged as backlog lines with their numbers (100 configurations). None is proposed.
- **S-4. The other live setups.** On today's history numbers, MF1–MF5 are negative (−0.06 to −0.17R; t ≤ −3.8 except MF2 at −1.56), in line with the re-score (MF1 retire; MF3/MF5 rework). Recommend the lead review their probation when the re-score verdicts are acted on.

## Owner notes
*Reserved for the owner's notes on today's 10 worst trades. Each flagged ticker and time will be turned into a rule using only information known at that minute, and tested across all stocks and days (charter item 3).*

| # | id | ticker | setup | in–out (ET) | P/L | loss type | owner note | rule to test | result |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 121 | IONQ | heat_fade_long | 11:35–13:26 | −$30.24 | news | | | |
| 2 | 128 | ACN | exhaustion_short | 13:00–15:11 | −$23.67 | news | | | |
| 3 | 123 | Z | exhaustion_short | 13:35–13:43 | −$20.10 | wrong side after big swing | | | |
| 4 | 118 | PATH | MF5 | 12:40–13:16 | −$18.98 | gave back gains | | | |
| 5 | 108 | NOW | heat_fade_long | 11:10–11:21 | −$17.94 | stopped then reversed | | | |
| 6 | 124 | LDOS | exhaustion_short | 13:35–13:44 | −$17.28 | news | | | |
| 7 | 112 | SHW | MF3 | 10:45–12:17 | −$15.39 | gave back gains | | | |
| 8 | 126 | NLY | exhaustion_short | 13:45–14:59 | −$14.70 | small MFE then failed | | | |
| 9 | 127 | VTRS | exhaustion_short | 14:20–15:08 | −$14.30 | news | | | |
| 10 | 120 | BABA | heat_fade_long | 11:05–13:23 | −$13.50 | gave back gains | | | |
