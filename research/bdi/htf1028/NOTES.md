Educational only — not financial advice. Configurations tried in this study: **21** (16 mss-pullback + 5 coil-k4 trend filters).

# BDI 2026-10-28: HTF-aligned setups (backlog `htf1028-mss-pullback`, `htf1028-coil-k4-trendfilter`)

**Scope.** Two-year backtest on the open history, 2024-10-01..2026-10-07 (lab universe, 5-minute RTH path = lab frames
plus head/tail rows). **The locked block 2024-11-01..2025-02-28 was never loaded** (`lib.months()` / `lib.load_month`
guards, the daily and head/tail files are read with a date filter that excludes it, `MCF_HIST_ALLOW_LOCKED` asserted
unset). **No holdout was scored. No config, setup, exit or engine file was changed.** Costs are in everywhere, using the
lab harness cost model (entry 1c + 1 bp × time-of-day multiplier, stop exits +1c + 1 bp + 2c, clock exits 1c + 1 bp,
target exits free). Split: train 2024-10..2025-12, valid 2026-01..2026-10-07. Regimes: `lib.regimes()` (universe median
open-to-close terciles, 142 sessions each). t = day-clustered. Bar = `max(1.5, sqrt(2 ln N))` (rule 19), plus positive
results in both up and down sessions.
- mss-pullback is a new lineage: N = 16, so the bar is **t ≥ 2.35**.
- coil-k4-trendfilter is in the coil-k4 lineage: N = 247 (hf1027) + 5 = 252, so the bar is **t ≥ 3.33**.

## Failures first

1. **Nothing clears its bar. 0 of 21 configurations.**
2. **All 8 long mss-pullback variants are negative** (−0.049 to −0.103R per trade, t −0.68 to −2.52).
   - They win in up sessions (+0.06 to +0.30R) and lose in down sessions (−0.25 to −0.40R).
   - So the HTF filter does not remove the market-direction bet. It is the same up-day / down-day split as coil-k4.
3. **The short side is the mirror image.**
   - The 4 swing-k=2 short variants are negative (−0.027 to −0.041R).
   - The 4 swing-k=3 short variants are positive (+0.033 to +0.089R), but have t 0.40-1.16 on only 158-218 trades.
   - The k=3 shorts lose in up sessions (−0.09 to −0.21R) and make everything in down sessions (+0.25 to +0.37R).
   - Their best day carries 41-118% of total R. Without the best day: +0.016 / +0.055 / +0.027 / −0.006R.
4. **The coil-k4 trend filters keep the loss.**
   - All 5 filters stay at about −0.056 to −0.061R per trade, against −0.061R for the parent.
   - Down sessions stay at −0.18 to −0.27R.
   - The trades each filter drops are no worse than the ones it keeps (−0.062 to −0.069R).
   - The HTF state and market state at the 10:15 signal do not predict how the session ends.

## 1. `htf1028-mss-pullback` (16 configurations, `results_mss.csv`)

Definitions were fixed before the run (full detail is in the `scan_htf.py` docstring):
- **HTF filter (long):** prior-day close > SMA20 of daily closes, and the last two confirmed 60-minute pivot lows are
  rising (k = 1, completed hourly bars only).
- **Shift (long):** a 30-minute close (bar closes 10:30-15:00) above the last confirmed 30-minute swing high, after the
  low since that swing high has undercut the swing low before it. The swing high can sit in the prior session.
- **Entry:** limit at 38.2% / 50% of the shift leg, measured from the shift low to the shift-bar close.
- **Location:** the limit is ≤ the midpoint of today's range so far, or ≤ the prior day's midpoint.
- **Exits:** stop at the shift low − 1c, target 1.5R / 2R, flat at 15:55.
- **Fills:** a trade-through is required to fill, and the order is valid until 15:00. The fill bar is checked for the
  stop only. Stops are checked first in later bars.
- **Universe:** first signal per symbol-day-side, ADV ≥ $95M.
- **Short:** the mirror.

| side | k | tgt | entry | signals | fill | trades | days | win | avg R | t | train | valid | up | flat | down | ex-best | best share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| long | 2 | 1.5 | 38% | 1765 | 40% | 706 | 284 | 47.5% | −0.060 | −1.44 | −0.061 | −0.059 | +0.216 | −0.072 | −0.288 | −0.071 | total < 0 |
| long | 2 | 1.5 | 50% | 3498 | 26% | 922 | 307 | 44.5% | −0.103 | −2.52 | −0.054 | −0.149 | +0.062 | −0.046 | −0.270 | −0.115 | total < 0 |
| long | 2 | 2.0 | 38% | 1765 | 40% | 706 | 284 | 47.0% | −0.059 | −1.36 | −0.045 | −0.070 | +0.253 | −0.071 | −0.320 | −0.072 | total < 0 |
| long | 2 | 2.0 | 50% | 3498 | 26% | 922 | 307 | 44.1% | −0.082 | −1.87 | −0.039 | −0.124 | +0.082 | −0.025 | −0.250 | −0.098 | total < 0 |
| long | 3 | 1.5 | 38% | 605 | 36% | 217 | 145 | 48.4% | −0.074 | −1.19 | −0.054 | −0.093 | +0.255 | −0.172 | −0.362 | −0.097 | total < 0 |
| long | 3 | 1.5 | 50% | 1038 | 24% | 253 | 157 | 47.8% | −0.052 | −0.76 | +0.027 | −0.116 | +0.176 | −0.008 | −0.286 | −0.067 | total < 0 |
| long | 3 | 2.0 | 38% | 605 | 36% | 217 | 145 | 48.4% | −0.072 | −1.09 | −0.039 | −0.102 | +0.303 | −0.178 | −0.403 | −0.097 | total < 0 |
| long | 3 | 2.0 | 50% | 1038 | 24% | 253 | 157 | 47.0% | −0.049 | −0.68 | +0.008 | −0.095 | +0.163 | +0.005 | −0.279 | −0.070 | total < 0 |
| short | 2 | 1.5 | 38% | 1621 | 37% | 604 | 257 | 48.2% | −0.027 | −0.65 | −0.100 | +0.033 | −0.163 | −0.125 | +0.190 | −0.040 | total < 0 |
| short | 2 | 1.5 | 50% | 3094 | 26% | 810 | 276 | 47.8% | −0.036 | −0.78 | −0.123 | +0.036 | −0.265 | −0.111 | +0.244 | −0.055 | total < 0 |
| short | 2 | 2.0 | 38% | 1621 | 37% | 604 | 257 | 48.0% | −0.030 | −0.68 | −0.106 | +0.033 | −0.177 | −0.124 | +0.194 | −0.046 | total < 0 |
| short | 2 | 2.0 | 50% | 3094 | 26% | 810 | 276 | 46.8% | −0.041 | −0.76 | −0.130 | +0.034 | −0.264 | −0.165 | +0.283 | −0.065 | total < 0 |
| short | 3 | 1.5 | 38% | 461 | 34% | 158 | 106 | 53.8% | +0.052 | 0.72 | −0.008 | +0.096 | −0.128 | −0.127 | +0.250 | +0.016 | 70% **1 day** |
| short | 3 | 1.5 | 50% | 854 | 26% | 218 | 130 | 54.1% | +0.089 | 1.16 | +0.091 | +0.088 | −0.184 | −0.022 | +0.370 | +0.055 | 41% |
| short | 3 | 2.0 | 38% | 461 | 34% | 158 | 106 | 53.8% | +0.063 | 0.83 | −0.034 | +0.134 | −0.094 | −0.150 | +0.276 | +0.027 | 58% **1 day** |
| short | 3 | 2.0 | 50% | 854 | 26% | 218 | 130 | 51.8% | +0.033 | 0.40 | +0.018 | +0.044 | −0.210 | −0.131 | +0.348 | −0.006 | 118% **1 day** |

**Notes**
- **Fills.** Only 24-40% of signals fill. 27-35% of filled longs hit the stop, and only 4-15% reach the target. Most
  trades end flat at 15:55.
- **Cost share.** The median entry-side cost is 2-2.5% of R. Even the cheapest bucket loses: long k2/2R/50% with cost/R
  ≤ 3% makes −0.029R (n 521). Above 3% it is −0.14 to −0.22R.
- **Time and months** (long k2/2R/50%). Most trades come from the 10:30-11:30 shifts (824 of 922), which make −0.06 /
  −0.14R. 8 of 21 months are positive (shorts: 6 of 21).
- **No random control was run** for this entry (rule 6). With every variant failing the bar, it would not change the
  verdict.
- **March 2025 is thin.** The SMA20 needs 20 sessions after the locked gap, so 2025-03 has almost no signals.

## 2. `htf1028-coil-k4-trendfilter` (5 configurations, `results_coil.csv`)

- **Parent:** `CWT12-coil-k4-long` as live (0.5R target, 0.35R scale-out, 09:50-11:30, first signal per symbol-day).
  The trades come from `hf1027/scan_hf.py` (var P), the same harness as top5_1021.
- **Filters:** evaluated at the signal bar with point-in-time features.
  - Stock HTF up: same definition as in section 1.
  - Market up: QQQ above its session VWAP (the frame `vwapDistPct`, i.e. the `qqq_vwap` context column) or
    `breadth_open` > 0.5.
- **t vs parent:** the day-clustered t of the change in total R per day. It is mechanically positive whenever a filter
  drops a negative-expectancy setup's trades, so it is not evidence of an edge.

| config | keep | trades | avg R | t | train | valid | up | flat | down | ex-best | excess vs random | dropped avg R | t vs parent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | 100% | 44,505 | −0.061 | −6.00 | −0.057 | −0.065 | +0.045 | −0.108 | −0.182 | −0.063 | +0.005 | – | – |
| (a) stock HTF up | 32.9% | 14,629 | −0.058 | −4.67 | −0.056 | −0.060 | +0.047 | −0.101 | −0.176 | −0.060 | +0.010 | −0.063 | +5.48 |
| (b) market up (qqq_vwap>0 or breadth_open>0.5) | 84.2% | 37,456 | −0.060 | −5.15 | −0.055 | −0.065 | +0.043 | −0.122 | −0.224 | −0.062 | +0.005 | −0.068 | +4.07 |
| (c) both | 27.8% | 12,379 | −0.056 | −4.01 | −0.053 | −0.059 | +0.047 | −0.114 | −0.217 | −0.058 | +0.008 | −0.063 | +5.79 |
| (b1) qqq_vwap > 0 only | 69.9% | 31,122 | −0.058 | −4.46 | −0.057 | −0.059 | +0.045 | −0.120 | −0.223 | −0.061 | +0.005 | −0.069 | +4.96 |
| (b2) breadth_open > 0.5 only | 67.9% | 30,234 | −0.061 | −4.52 | −0.057 | −0.065 | +0.039 | −0.169 | −0.274 | −0.064 | +0.003 | −0.062 | +4.67 |

The per-trade result moves by at most 0.005R. The up-session edge (+0.04-0.05R) and the down-session loss (−0.18 to
−0.27R) both survive every filter. The market filters make down-session trades *worse*: a market that is up at 10:15
and closes down is the coil's worst case. Feature coverage: SMA20 is known for 93.9% of trades, the 60-minute HL holds
on 58.3%, and qqq_vwap is known for 100%.

## Recommendation

- **`htf1028-coil-k4-trendfilter`: mark failed** (configs_tried 5; lineage N 252).
  - The stock / market state at signal time does not separate the coil's up-day trades from its down-day trades.
  - Nothing here argues for keeping coil-k4.
- **`htf1028-mss-pullback`: failed as specified** (configs_tried 16, look 0, no holdout).
  - Long and short are each other's regime mirror, so the HTF alignment does not neutralise market direction.
  - The only positive cells (short, k=3) are small-sample, have t ≤ 1.16, depend on down sessions, and are partly
    carried by one day.
  - Under rule 18, one rework round is allowed before dropping, searched on train and chosen on valid. Candidates:
    - require the 30-minute shift within the same session;
    - an ATR floor on R;
    - replace an unfilled order with a newer signal.
  - **Expectation is low.** The long side loses in every cost bucket and every hour except a 45-trade noon cell.
  - **Lead's call: drop now, or run one rework round with the count carried forward (N ≥ 16).**

Suggested backlog updates (for the lead; not written to `research/backlog.jsonl`):
- `htf1028-mss-pullback`: status `failed`, configs_tried 16. Notes: "2y open history, costs in: long 8/8 negative
  (−0.049..−0.103R, t −0.68..−2.52; up +0.06..+0.30, down −0.25..−0.40); short k2 4/4 negative, k3 +0.033..+0.089R
  (t ≤ 1.16, n 158-218, up sessions negative, best-day share 41-118%). Bar 2.35 not met; no holdout scored."
- `htf1028-coil-k4-trendfilter`: status `failed`, configs_tried 5. Notes: "Stock-HTF / market / both / qqq_vwap /
  breadth_open: −0.056..−0.061R vs parent −0.061 (t −4.0..−5.2); down sessions −0.18..−0.27R in all. Bar 3.33 not met."

## Files

- `scan_htf.py`: two-year scan. Writes `<scratch>/htf1028/mss.parquet` (16 variants) and `coilfeat.parquet` (coil-k4
  parent trades plus features). Needs `<scratch>/hf/coil2y.parquet` from `../hf1027/scan_hf.py`.
- `eval_htf.py`: scoring. Writes `eval_out.txt`, `results_mss.csv` and `results_coil.csv`.
- Run: `python scan_htf.py` (about 8 min, 3 processes), then `python eval_htf.py`. `python scan_htf.py one 2025-06`
  runs a single month as a smoke test.
- **Spot check:** the logic was traced by hand on AMT 2025-06-27, long k2/2R/50%. The swing high is 219.44 (06-26
  13:00), the prior swing low 218.04, the lower low 215.82, and the 12:30 shift close 219.84. That gives a limit of
  217.83 (filled at 14:30), R = 2.02, flat at 15:55 for −0.11R after costs. The scan matches.

Educational only — not financial advice.
