# Move-hunt LONG evidence (ultimate_1119, consultant evidence miner)

Educational only - not financial advice.

## What was run
- Builder `movehunt_long_build.py` (2-year 1-min cache, pyarrow row filter: never loads 2024-11-01..2025-02-28 nor >= 2025-10-01).
  Scored sessions: 2024-10 and 2025-03..2025-09 = **165 sessions, 1,181 symbols, 11.93M decision bars** (every 5-min bar
  09:50-15:15, px >= $5, ADV20 >= $20M). Features strictly point-in-time (bars <= T); entry = open of the 1-min bar at T.
- Outcomes: `r_g1` +1R/-1R bracket, 45-min max hold, flat 15:55 (R = 0.25 x prior-session daily ATR14 ~ one 15-min ATR);
  `r_g2` +2R/-1R; `r_t30` timed 30-min exit. Same-minute stop+target = stop; stop gap-through at worse price; target
  fills at the limit, no gap bonus.
- Costs: entry 1bp+$0.01, each exit 1bp+$0.01, stop exits +$0.02, then topped up in the analyzer to at least LR8
  (stop max($0.02, 4bp)) plus ~0.25bp SEC/FINRA per exit; target exits are over-charged vs LR8 (LR8 charges a limit
  fill nothing) -> figures **understate** slightly. Median cost ~0.12R/trade (0.075R in names with cost_r <= 0.10).
- Analyzer `movehunt_long_analyze.py` (pre-declared: baseline, 52 univariate buckets, 28 washout confirmations, 10 combos)
  -> `movehunt_long_out.txt`; then `movehunt_long_stage4.py` (8 combos x 2 outcomes, **declared after reading stages
  1-3**, so selected on fit) -> `movehunt_long_stage4_out.txt`. Day-clustered t; fitA = < 2025-06-01, fitB = after.
- **Configurations counted: 88 (pre-declared) + 16 (stage 4) = 104**, plus 3 ex-April diagnostic re-cuts reported below.
- Pre-declared pass rule: net avgR > 0, t >= 2, both fit sub-halves > 0, avg R w/o best day > 0, best-day share < 50%.
  **0 of 104 pass.**
- Data caveat: the cache holds today's symbol list (survivorship), which flatters longs; random 45-min long bars show
  +0.06R gross. Treat any small positive as at risk.

## Results (net of costs, R per trade)
**Baseline, random bars:** r_g1 -0.100 (gross +0.060, cost 0.117), hit +1R within 45 min 11.7%. By time of day:
09:50-10:30 -0.116 (hit 23.8%), 10:30-12:00 -0.094, 12:00-14:00 -0.107, 14:00-15:15 -0.086. The swing size we want
(>= 1R in 45 min) happens on ~12% of random bars, 24% in the first 40 min.

**Stage 1 (univariate, lift vs time-of-day-matched random):** every bucket is net negative. Precursors raise the *hit
rate* strongly but not the expectancy: drop >= 2 ATR from open hits +1R 42% (vs 12%) yet nets -0.154 (lift -0.056);
ret15 <= -0.5 ATR hits 57%, nets -0.137. Big moves are two-sided - stops hit first as often. RSI2/RSI5 extremes, VWAP
-2/-3 sd, volume spike, OR/VWAP reclaim, at-LOD, higher low: lifts within +/-0.01R (no information). What does move
net R: **volatility/cost** (atr_pct >= 4: -0.052 vs < 2%: -0.164; ADV20 >= $1B: -0.064) and **gap +/-1-3%** (+0.02 lift).

**Stage 2 (inside washout base W = drop >= 1 ATR from open or >= 1.5 ATR off HOD, -0.116):** best lifts are
time of day 10:30-12:00 (+0.041; t30 +0.051 net), tape falling spy_r30 < -0.3% (+0.039; t30 +0.041), cost_r <= 0.10
(+0.047), atr_pct >= 4 (+0.031), vwap_reclaim (+0.018). Worst: 09:50-10:30 (-0.071; washouts at the open keep going),
fast fall ret60 <= -1 ATR (-0.086), gap-up that washes out (-0.072), RSI2<=10 & green bar (-0.038).
**Stage 3 combos (deduped):** all 10 negative; best C5 HOD >= 1.5 ATR & VWAP reclaim -0.033 (hit 53%, gross +0.119).

**Stage 4 (selected, deduped; r_t30 / r_g1):**
| combo | n | t30 | g1 | t(t30) | best-day share | ex-April t30 |
|---|---|---|---|---|---|---|
| S1 W & 10:30-12:00 | 12,782 | +0.129 | -0.037 | 1.10 | 95% | -0.018 |
| S2 S1 & cost<=.10 | 4,850 | +0.248 | +0.037 | 1.56 | 70% | -0.010 |
| S3 S1 & gap<=-1 | 3,878 | +0.486 | +0.039 | 1.76 | 82% | +0.002 |
| **S4 W & SPY 30-min ret < -0.3% & cost<=.10** | 6,417 | +0.188 | +0.072 | 0.94 | 78% | **+0.189** |
| S5 HOD>=1.5 & VWAP reclaim & cost<=.10 | 670 | -0.036 | +0.096 | -0.32 | - | +0.229 (n 292) |
| S6 HOD>=1.5 & VWAP reclaim & 10:30-12:00 | 646 | -0.331 | +0.006 | -1.61 | - | +0.151 (n 291) |
| S7 S1 & atr_pct>=4 | 2,374 | +0.294 | +0.031 | 2.00 | 53% | +0.067 |
| S8 S1 & SPY up from open | 5,042 | +0.257 | +0.023 | 1.01 | 121% | -0.068 |

Every positive full-window number except S4 is the **April 2025 tariff crash/rebound** (e.g. S3: April n 2,531 at
+0.744, the other 7 months +0.002). One-big-day check fails for all of them.

## The one lead: S4 "tape-flush washout" (selected on fit - treat as a hypothesis for the check half)
Long a name that has washed out (>= 1 ATR below open or >= 1.5 ATR off HOD), at a moment when SPY fell >= 0.3% over
the last 30 min, liquid/volatile enough that cost <= 0.10R; exit after 30 min. **Excluding April 2025:** n 1,780 on
63 sessions (~28/session on those days), t30 **+0.189 net, t 2.48**, fitA +0.176 / fitB +0.205, w/o best day +0.142,
best-day share 31%, w/o top-2 days +0.113, positive in **every** ex-April month (+0.14..+0.26), 56% of days positive.
Control (all names at the same moments, no washout): +0.038 -> the washout adds ~+0.15R. Bracket exits are much
weaker (g1 +0.073 with 72% best-day share; g2 +0.112, 63%): the gain is a slow 30-min drift, not a 1R pop.
Honest caveats: (1) it is effectively a leveraged bet on SPY intraday mean reversion - trades on a day are highly
correlated; one trending-down day costs many R at once; (2) it fires only on ~half the sessions (no every-day volume);
(3) with 104 configs a Bonferroni-style bar is t ~3.3, which it does not clear; (4) selected after looking.
Next step: score S4 (frozen exactly as above) once on the check half (2025-10-01 onward), with a per-day position cap
and an SPY-trend kill (e.g. skip when SPY is already < -1% from open and still making lows) declared before scoring.

## Takeaways for the setup builders
1. The long-reversal *hit rate* is easy to raise (12% -> 40-57%); the *expectancy* is not - deep washouts are
   two-sided. Do not rank precursors by hit rate.
2. Cost dominates at R = 0.25 daily ATR (~0.12R/trade vs a gross edge of 0.05-0.12R). Filter to cost_r <= 0.10 /
   atr_pct >= 4 or widen R; a timed exit beats a 1R bracket for washouts.
3. Avoid 09:50-10:30 washout longs (-0.07R lift); 10:30-12:00 is the best window (consistent with Wave 1: time of day
   persists).
4. Classic oscillator triggers (RSI2/5, VWAP -2/-3 sd, volume spike + higher low, OR reclaim) carry no measurable
   edge on this universe after costs.
5. Regime: most apparent long-reversal edge sits in one crash-rebound month; a setup must survive ex-April.
