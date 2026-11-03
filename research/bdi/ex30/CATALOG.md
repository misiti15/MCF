# ex30 — 30 exploratory setups: catalog and draft allocation

*Educational only — not financial advice.* Backtest only: none of these 30 setups has a paper or live record.

Owner request 2026-11-03: three new paper accounts (Live Lab, Explore 1, Explore 2) and 30 new, unconventional setups
for the exploratory accounts; allocation is the owner's call. Six family agents each pre-declared a PLAN.md (committed
before scoring), scored 5 primaries plus neighbours, and checked module-vs-harness mask parity (exact for all 30).

**Common harness.** history2y open 5-minute frames; TRAIN = 2024-10 + 2025-03..12 (234 sessions), VALID = 2026-01..03 +
2026-07-01..09-15 (114 sessions); the locked block 2024-11-01..2025-02-28 was never loaded (asserted in code). Costs always
in (gates.lab_trades / prod_r: production costs + time-of-day entry multiplier), first signal per symbol-day, ADV >= $95M,
R = 0.25 x daily ATR, flat 15:55, day-matched random-entry control. Day type = SPY open-to-close at +-0.25%.

**Configurations tried: 18,618** (xsec 39, peer 15, micro 15, time 15, levels 15, gen2 18,519). **Light lane gate
(avg R >= -0.02 on TRAIN and VALID, 1.5-25 trades/session, parity): 0 of 18,618 pass; 0 of the 30 delivered pass.**
All 30 are delivered anyway, as exploration, with gate pass = no.

## The 30 setups (sorted by family)

Up / down / quiet R: TRAIN+VALID pooled for xsec, micro and levels; gen2 is VALID only; peer and time as reported by
those agents (per-split values in each family's results.csv). Geometry: t1s1 = target 1R / stop 1R, t05s1 = 0.5R / 1R,
t1s05 = 1R / 0.5R.

| id | name | side | family | rule (bar close, ET) | TRAIN avg R | VALID avg R | trades/session | up / down / quiet R | gate | draft account |
|---|---|---|---|---|---|---|---|---|---|---|
| XS1-laggard-greentape-short | Laggard on a green tape | short | xsec | 10:00-14:00: breadth_open >= 0.65 and SPY above open, stock >= 0.75 ATR below its open and below VWAP; t1s1 | -0.164 | -0.145 | 13.09 | -0.210 / -0.013 / -0.079 | no | Explore 2 |
| XS2-leader-redtape-long | Leader on a red tape | long | xsec | 10:00-14:00: breadth_open <= 0.35 and SPY below open, stock >= 0.75 ATR above its open and above VWAP; t1s1 | -0.167 | -0.126 | 14.11 | +0.122 / -0.219 / -0.052 | no | Explore 1 |
| XS3-quiet-topoutlier-fade-short | Quiet-tape top-outlier fade | short | xsec | 10:30-14:30: SPY within +-0.25% of open, breadth 35-65%, stock's move beats SPY's by >= 1.0 ATR%; first down bar; t1s1 | -0.127 | -0.089 | 20.41 | -0.247 / +0.084 / -0.152 | no | Explore 2 |
| XS4-quiet-bottomoutlier-fade-long | Quiet-tape bottom-outlier fade | long | xsec | 10:30-14:30: SPY within +-0.25% of open, breadth 35-65%, stock trails SPY by >= 1.0 ATR%; first up bar; t1s1 | -0.119 | -0.039 | 16.57 | +0.123 / -0.284 / -0.106 | no | Explore 2 |
| XS5-rankclimb-fallingtape-long | Rank climb against a falling tape | long | xsec | 10:00-15:00: breadth fell >= 0.15 over 3 bars while stock's VWAP distance rose, and it reclaims VWAP this bar; t05s1 | -0.114 | -0.154 | 36.28 | -0.016 / -0.220 / -0.124 | no | Explore 1 |
| PR1-sympathy-laggard-long | Sympathy laggard catch-up | long | peer | 10:30-13:30: SPY >= +0.30% from open, running corr/beta to SPY >= 0.5, residual move <= -0.5 ATR, close above prior close | -0.039 | -0.052 | 27.11 | +0.099 / -0.740 / -0.346 | no | Explore 1 |
| PR2-decoupled-quiet-breakdown-short | Decoupled breakdown on a quiet tape | short | peer | 10:30-14:30: SPY within +-0.25%, corr to SPY within +-0.15, stock <= -1.0 ATR from open, below VWAP, at lowest close since 09:50 | -0.123 | -0.094 | 7.46 | -0.232 / +0.015 / -0.111 | no | Explore 1 |
| PR3-narrow-rally-laggard-short | Narrow-rally component short | short | peer | 10:30-14:30: SPY >= +0.30% but breadth_open <= 0.45 and qqq_fo >= spy_fo; stock >= 0.5 ATR below open and below VWAP | -0.192 | +0.142 | 4.13 | -0.136 / +0.471 / +0.205 | no | Explore 2 |
| PR4-qqq-residual-stretch-revert-short | QQQ pair-spread stretch reversion | short | peer | 11:00-15:00: corr to QQQ >= 0.40, residual vs beta x QQQ >= +1.25 ATR and falling, close below prior close | -0.098 | -0.080 | 6.48 | -0.185 / -0.001 / -0.147 | no | Explore 1 |
| PR5-qqq-impulse-leadlag-long | QQQ impulse lead-lag follower | long | peer | 10:20-15:00: QQQ up >= 0.20% over 2 bars, corr >= 0.5 and beta >= 0.8, stock's 2-bar return <= 0.25 x beta x QQQ's | -0.006 | -0.017 | 76.47 | +0.113 / -0.140 / -0.006 | no | Explore 2 |
| MC1-nr7-expansion-volburst-long | NR7 compression then volume expansion | long | micro | 10:45-15:00: prior bar narrowest of 7, this bar closes above its high, upper wick <= 0.25, volumeRatio >= 1.5; t1s1 | -0.093 | -0.090 | 176.79 | +0.065 / -0.238 / -0.143 | no | Explore 2 |
| MC2-dryup-surge-wickreject-short | Volume dry-up, surge into wick rejection | short | micro | 10:15-15:00: 3 prior bars volumeRatio < 0.7, this bar >= 2.0 with upper wick >= 0.5; t1s1 | -0.141 | -0.079 | 28.34 | -0.304 / +0.037 / -0.058 | no | Explore 2 |
| MC3-vwap-glued-stretch-long | Time-at-VWAP balance snap-back | long | micro | 11:00-15:00: >= 60% of bars since 09:50 straddled VWAP, close <= VWAP - 0.30 ATR, lower wick >= 0.5; t05s1 | -0.258 | -0.260 | 0.35 | -0.292 / -0.333 / -0.033 | no | Held back |
| MC4-redrun-outside-reversal-long | Six red bodies then outside green reversal | long | micro | 10:30-15:00: 6 prior red bodies, this bar green and closes above prior high; t05s1 | -0.066 | -0.092 | 74.42 | +0.030 / -0.152 / -0.083 | no | Explore 1 |
| MC5-firsthour-break-voldecay-short | First-hour high break on fading volume | short | micro | 10:35-14:00: close crosses above the 09:30-10:30 high with volumeRatio < 0.8 and volumeSurge < 1.0; t1s1 | -0.104 | -0.052 | 226.49 | -0.286 / +0.161 / +0.033 | no | Explore 1 |
| TM1-lunch-stalled-high-fade-quiet-short | Lunch stalled-high fade on a quiet tape | short | time | 11:30-13:30: SPY within +-0.25%, stock >= 0.75 ATR above open, >= 0.40 ATR off HOD, no new high 30 min, down bar; t05s1 | -0.088 | -0.028 | 6.35 | -0.151 / +0.070 / -0.091 | no | Explore 1 |
| TM2-quiet-tape-range-floor-fade-long | Quiet-tape range-floor fade | long | time | 12:00-15:00: SPY within +-0.20%, spy_prng <= 1.0, day range >= 0.75 ATR, in bottom 15% of range, up bar; t05s1 | -0.094 | -0.121 | 43.30 | +0.069 / -0.305 / -0.089 | no | Explore 1 |
| TM3-gapup-drift-powerhour-short | Gap-up drifted to the low, power-hour short | short | time | 14:30-15:00: gap >= +1.0%, >= 0.75 ATR below open, within 0.15 ATR of LOD, below VWAP; t05s1 | -0.174 | -0.093 | 9.93 | -0.195 / -0.146 / -0.103 | no | Held back |
| TM4-ten-oclock-reversal-long | 10:00 reversal | long | time | 10:00-10:15 only: >= 0.75 ATR below open, new LOD in last 2 bars, closes above prior high, still under VWAP; t1s1 | -0.019 | -0.217 | 4.49 | -0.103 / -0.199 / +0.018 | no | Explore 1 |
| TM5-turn-of-month-vwap-pullback-long | Turn-of-month VWAP pullback | long | time | Days 28-3 only, 10:30-14:00: >= 0.50 ATR above open, within 0.15 ATR above VWAP, up bar; t05s1 | -0.055 | -0.051 | 20.38 | +0.055 / -0.137 / -0.116 | no | Explore 2 |
| LV1-round-firsttouch-reject-short | Round-number first-touch rejection | short | levels | 10:00-15:00: first touch today of the round level above the prior HOD, close >= 0.05 ATR below it, upper wick >= 40%; t05s1 | -0.142 | -0.069 | 16.08 | -0.167 / -0.011 / -0.115 | no | Explore 2 |
| LV2-round-secondtouch-break-long | Round-number second-touch break | long | levels | 10:30-15:00: close crosses a round level touched earlier but never cleared, after a >= 0.40 ATR pullback in 6 bars; t1s1 | +0.007 | -0.076 | 13.56 | +0.099 / -0.150 / -0.107 | no | Explore 2 |
| LV3-gapup-halffill-short | Gap-up half-fill magnet | short | levels | 10:00-14:00: gap +1.5..+8%, close crosses below the half-gap line, below VWAP, >= 0.30 ATR left to the fill; t1s1 | +0.040 | -0.157 | 8.14 | -0.302 / +0.172 / -0.182 | no | Explore 2 |
| LV4-gapdn-filled-retest-long | Gap-down filled, prior-close retest | long | levels | 10:15-15:00: gap <= -1.0%, gap already filled, this bar tests and holds the prior close; t05s1 | -0.058 | -0.038 | 37.66 | +0.026 / -0.129 / -0.124 | no | Explore 1 |
| LV5-flatopen-pclose-stretch-short | Flat-open prior-close stretch | short | levels | 11:30-15:00: abs(gap) <= 0.4%, close >= prior close + 1.0 ATR, at HOD on volumeRatio < 1.0; t1s1 | -0.130 | -0.064 | 14.14 | -0.184 / +0.069 / -0.098 | no | Explore 2 |
| G2-1-macdup-vrlo-vwup-W1-t1s1-short | MACD zero-cross fade on dry volume | short | gen2 | 10:00-11:30: MACD% crosses above 0 on volumeRatio <= 0.6 while close >= 0.5 ATR above VWAP; t1s1 | +0.148 | -0.024 | 1.67 | +0.013 / -0.046 / -0.032 | no | Explore 1 |
| G2-2-lwick-brlo-heatlo-W2-t1s05-long | Midday wick buy on a collapsing tape | long | gen2 | 11:30-14:00: lower wick >= 60% of range >= 0.10 ATR, breadth <= 30%, heat <= -25; t1s05 | +0.182 | -0.180 | 2.22 | +0.286 / -0.248 / -0.079 | no | Held back |
| G2-3-uwick-brhi-d20hi-W2-t1s1-long | Upper-wick absorption on a green tape | long | gen2 | 11:30-14:00: upper wick >= 60% of range >= 0.10 ATR, breadth >= 70%, close >= 0.8% above SMA20; t1s1 | +0.371 | -0.046 | 7.68 | +0.139 / -0.924 / -0.362 | no | Held back |
| G2-4-round-foup-slopedn-W2-t05s1-long | Round-number dip inside an up day | long | gen2 | 11:30-14:00: close within 0.02 ATR of a round number, >= 0.5 ATR up on the day, SMA20 down >= 0.3% over 5 bars; t05s1 | +0.089 | -0.022 | 2.76 | +0.097 / -0.162 / -0.015 | no | Explore 2 |
| G2-5-bulldiv-vrlo-vwdn-W1-t1s1-long | Quiet-volume bullish RSI divergence | long | gen2 | 10:00-11:30: new 20-bar low with RSI > its 20-bar min + 5, volumeRatio <= 0.6, close >= 0.5 ATR below VWAP; t1s1 | +0.063 | -0.050 | 6.05 | +0.175 / -0.151 / -0.059 | no | Explore 1 |

Modules: `research/bdi/ex30/<family>/modules/<id>.py` (SIDE, GEOM, WINDOW, mask(df); context columns only from
mcf/strategies/lab_context.py). Family write-ups: `research/bdi/ex30/<family>/NOTES.md`.

## What the 30 say

- **Every setup is negative on VALID except PR3** (+0.14R, but 83% of it is one day, 2026-08-28; TRAIN -0.19R).
- **The book's quiet-day hole is not fixed.** Every design built for quiet days (XS3, XS4, PR2, PR4, TM1, TM2, MC3)
  loses on quiet days. Longs still win only on up days and shorts only on down days, across all six families.
- **Closest to the gate:** G2-4 (-0.023 VALID, quiet -0.015, beats random both splits), G2-1 (-0.024 VALID; TRAIN carried
  by one session), PR5 (-0.006 / -0.017, beats random both splits, but 76 trades/session).
- **One-big-day check:** carried by one session on TRAIN: G2-1 (share 1.37), G2-2 (1.38), LV2 (6.75), LV3 (3.04); PR3 on
  VALID (83%). The other primaries have avg R w/o best day within ~0.02R of avg R (uniformly negative).
- **Data the live runner lacks (ideas dropped or proxied):** a true universe rank (needs a lab_context percentile column),
  per-symbol peer groups / sector ETFs / pair legs, qqq_vwap in history, prior-week / multi-day / 52-week levels, prior-day
  VWAP, SPY prior-day direction, a holiday calendar. Each would be an mcf/ change (lead / owner decision).

## The new generator method (gen2) in 5 lines

1. A typed grammar: one TRIGGER (19 bar-close events) + 0-2 CONTEXTS (35 states incl. spy_fo / breadth), x side x exit
   geometry (t1s1 / t05s1 / t1s05) x window (10:00-11:30, 11:30-14:00, 10:00-15:00), at most 3 conditions.
2. Fitness = regime maximin on TRAIN only: the WORST of avg R on SPY up, down and quiet days, minus 0.01 per condition and
   0.02 for overlap with live GEN tokens; >= 30 trades per day type and 1.5-25 trades/session required.
3. Near-duplicates of live setups and exhausted families are excluded before scoring; search = all 1-2-condition rules,
   then a beam of the top 300 extended by one context (18,519 configs).
4. Shortlist = top 30 by fitness with Jaccard < 0.30 on TRAIN trade sets; the 5 delivered are the first 5 distinct
   triggers, chosen on TRAIN only, VALID used once as a check.
5. Result: maximin did not carry over (all 5 positive on all three day types on TRAIN, none positive on quiet days on VALID).
   Lead for exposure: MACD-zero-cross-up fade shorts (5 of 6 in the shortlist beat random on VALID).

## DRAFT allocation — the owner decides

**Live Lab: none of the 30 (DRAFT).** The Live Lab lane's own pre-declared entry gate (avg R >= -0.02 on TRAIN and VALID,
1.5-25 trades/session) admits 0 of them, and no quiet-day / both-ways design here is positive on quiet days. Its first
setups come from the livelab backlog supply (research/bdi/night1102/livelab/NOTES.md), not from ex30. If the owner wants
ex30 names there anyway, the least bad are G2-4, G2-1 and PR5 (PR5 only with a throttle, which is a new, unscored config).

**Explore 1 (DRAFT)** — 13 setups, 8 long / 5 short, 492 trades/session raw, 197 with each setup capped at 25: XS2, XS5, PR1, PR2, PR4, MC4, MC5, TM1, TM2, TM4, LV4, G2-1, G2-5.

**Explore 2 (DRAFT)** — 13 setups, 6 long / 7 short, 411 trades/session raw, 204 with each setup capped at 25: XS1, XS3, XS4, PR3, PR5, MC1, MC2, TM5, LV1, LV2, LV3, LV5, G2-4.

**Held back (DRAFT): MC3-vwap-glued-stretch-long, TM3-gapup-drift-powerhour-short, G2-2-lwick-brlo-heatlo-W2-t1s05-long, G2-3-uwick-brhi-d20hi-W2-t1s1-long.** MC3 almost never fires (0.35/session); TM3 is below random in both
splits; G2-2 and G2-3 are tape-direction bets (G2-3 -0.92R on VALID down days) that the generator agent said should not
get seats. They stay in the backlog as ideas.

Balancing rules used: mirror and basket legs kept together where they form a pair (XS3 + XS4 in Explore 2), each family in
both accounts, long/short mix in both, and exposure balanced on trades/session capped at 25 per setup (MC5 226, MC1 177,
PR5 76, MC4 74 are split across accounts; live they are limited by the 10-lots-per-setup cap anyway, so their live trade
count will be far below the backtest count). Live verdicts follow the livelab fail-fast rule (>= 5 sessions and >= 45
trades with avg R <= -0.30, or cumulative <= -15R) and are split by SPY up / down / quiet day.

**Rule-change context.** The numbers above are backtests on fixed frames, so no ledger rule change applies inside them. Live
R in the new accounts would carry the 10-27 GX1 lab clock and the 10-30 Testing cost filter (`max_stop_cost_r` 0.15, which
the accounts branch turns on in all three new accounts — it may be wanted off in Explore 1 / 2; one line each).

## Capacity risks (from the accounts agent, branch `claude/accounts-3new`, commit f46163cb3, not yet merged)

The branch touches config/, workflows and mcf/execution, so it merges outside 09:30-16:00 ET. Each account: 200 slots,
buying power x2.0 (~$1,000 lots on $100k), up to 10 lots per setup, per-setup daily stop off, account daily stop 120R
(the Live Lab draft had 60R). Six secrets are needed (ALPACA_LIVELAB / EXPLORE1 / EXPLORE2 _API_KEY and _SECRET_KEY, each
a separate paper account); jobs skip an account until both secrets exist and it has an enabled setup.

1. **GitHub Actions concurrent jobs (main risk).** 8 accounts → ~18-19 jobs at once in session (8 trade jobs, watchdog
   bursts up to 8, guard, long-hold snapshot) vs a cap of 20 (Free) / 40 (Pro). Worst case: a delayed trade handover at
   ~14:30 (355-minute job limit) loses late-day polls. Fixes: GitHub Pro, a single combined watchdog, staggered crons.
2. **Alpaca market data on the one shared key.** ~100-150 bar requests/minute across 8 jobs: fine on Algo Trader Plus
   (10,000/min), would break the free 200/min tier. Bursts at pre-open prep and restarts (~150 per job). A rate-limit
   error silently loses one batch of bars.
3. **Poll coverage.** Testing 2, Graveyard and Gen reach only 76-80% of polls; new accounts with many setups using
   context columns will likely land there too — check poll counts after the first session before filling 20 seats.
   Several ex30 setups use context columns (breadth, breadth_open, spy_fo, qqq_fo, spy_prng).
4. **Trading API and buying power are fine** (limits are per account key; 200 x $1,000 = $200k inside paper buying power).

Not yet built for Live Lab: the cross-setup symbol-lock switch, shadow-track tagging, the Live Lab report, the lane gate and
automatic fail-fast.
