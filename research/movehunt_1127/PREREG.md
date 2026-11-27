Educational only — not financial advice.

# MOVEHUNT_1127 pre-registration (written 2026-11-27, before any feature, ranker or setup below was built or scored)

North star (owner 2026-10-29): identify the day's big intraday movers beforehand, in numbers, long and short, and turn
that into setups. Question: which features observable at the **09:50 decision time** (owner direction anchor 11-14:
never enter at 09:30; reference = the 09:50 state and the 09:30-09:50 range) rank the names that make the biggest
REMAINING move of the day, and does the best ranker carry a tradeable edge after costs?
Research only: no config, setup, exit, assignments, decisions or ledger change.

## Data and universe
1-minute RTH bars: data/cache_hist/1Min (1,226 symbols, 2024-09-16..2026-11-04) for FIT/CHECK; data/cache_fresh/1Min
(469 symbols, 2022-10-03..2024-09-13) for T2. No premarket bars exist in either cache, so "premarket gap" = the 09:30
open vs the prior RTH close. The locked block 2024-11-01..2025-02-28 is NEVER read (pyarrow filter + assert in code).
Daily bars (RTH OHLCV) are built from the minute bars; rolling stats reset at any >7-calendar-day hole (so no value
straddles the locked block; the first 20 sessions after the hole are warm-up only).
Eligible symbol-day: P50 (close of the 09:49 bar) >= $5; adv20 (mean RTH dollar volume over the prior 20 sessions)
>= $20M; ATR14 (prior 14 sessions, RTH true range) available; >= 15 of the 20 bars 09:30-09:49 present; the 15:55 (or
last bar of a half day) present. Shorts additionally need easy_to_borrow in data/universe.csv (current snapshot;
disclosed caveat: not point-in-time).
Splits: FIT 2024-10 + 2025-03..2025-09; CHECK 2025-10-01..2026-11-04; T2 2023-01-03..2024-09-13.
Universe size differs (T1 ~1,000 eligible/day, T2 ~430), so capture is always shown against its own base rate (lift).

## Target (what a "top mover" is)
Primary (scored): M = |C_last − P50| / ATR14$, the move still available after 09:50 to the close (15:59 bar close, or
last bar of a half day). Top movers = the top 2% of that day's eligible names by M (at least 1). Direction = sign.
Reported, not scored: (a) |close − open| / ATR (the task's open-to-close definition; partly observed by 09:50, so it
flatters any first-20-minute feature); (b) max excursion after 09:50, max(H − P50, P50 − L) / ATR.

## Features at 09:50 (all from bars closed by 09:49 and prior days)
gap = |open/prev_close − 1| / atr_pct · rvol = volume 09:30-09:49 / median of the same window over the prior 20 sessions
· rng = (high − low, 09:30-09:49) / ATR · mv = |P50 − open| / ATR · idio = |r20 − SPY r20| / atr_pct (r20 = P50/open − 1;
market/sector-relative proxy, no sector map exists in the repo) · pdr = prior-day (H − L) / ATR · dv = log adv20 ·
atrp = atr_pct. Earnings dates are only available from 2024-08 (no T2), so no earnings feature; a large gap with high
rvol is the proxy and is reported as such.

## Rankers (8 configurations)
K1 rvol · K2 gap · K3 rng · K4 pdr · K5 COMBO = mean of the day's cross-sectional percentile ranks of rvol, gap, rng
(fixed equal weights, no fitting) · K6 LOGIT = logistic regression of is_top_mover on the 8 features (log1p transforms,
standardised), fit on FIT only, frozen, then applied to CHECK and T2 · K7 dv (control: "just liquid names") · K8 atrp
(control: "just volatile names"). Random base rate = N / n_eligible per day (analytic) with a 200-draw empirical check.

## Capture metrics (per period)
capture@N = share of the day's top movers that are in the ranker's top-N list, N = 20 / 50 / 100, averaged over days;
lift = capture / base; day-clustered t of (capture − base) over days. Direction hit-rate on the top-N list:
continuation rule D = sign(P50 − open) vs sign(C_last − P50), for all top-N names and for the captured movers; gap
direction reported alongside.
Ranker bar (descriptive, "strong ranker"): capture@50 lift >= 2.0 on CHECK and on T2 with day t >= 3.0 on both.

## Setups (6 configurations = 3 rules × long/short scored separately)
Ranker for setups chosen BEFORE any setup is scored = the K1-K6 ranker with the highest FIT capture@50 (ties → K5).
List = that ranker's top 20 eligible names each day. Entry at the open of the 09:50 bar; stop checked on 1-min high/low
from the 09:50 bar on (stop-first; a bar opening through the stop fills at its open); time exit at the 15:55 bar close
(last bar on half days). 1R = |entry − stop|; risk must be >= 0.10% of price (else no trade). Side = direction taken.
S1 CONT: D = sign(P50 − open); stop = the opposite extreme of the 09:30-09:49 range ∓ $0.01.
S2 FADE: −D; stop = the 09:30-09:49 extreme on the first move's side ± 0.10 × ATR (risk floored at 0.10 × ATR).
S3 ORB: wait 09:50-11:30 for a 1-min close beyond the 09:30-09:49 range in direction D; enter at the next bar's open;
stop = range midpoint; one entry per name per day.
Costs always in: LIVE-L (research/primshorts_1126 cells_live.json, predict_R by price bucket × exit kind; preferred)
and LR8 research (bench10 add_r formula: 1c + 1bp per side × tod multiplier, 3× tier for price < $5 or |gap| >= 20%, 2c
extra on stops, 1.2 bp borrow on shorts). Both are reported; LIVE-L is the scored basis.

## Pass bar (per setup-side; all must hold)
1. avg R > 0 on CHECK and on T2 at LIVE-L and at LR8.
2. Day-clustered t >= 3.0 on CHECK (Bonferroni over this study's 14 configurations, one-sided 0.05/14 → z ≈ 2.7,
   rounded up) and >= 2.0 on T2. A lineage claim (cumulative N ≈ 8,966 after this study) needs t >= 4.3.
3. One-big-day: avg R without the best day > 0 and best-day share of total R < 50%, on CHECK and on T2.
4. Selection control: 50 random size-matched draws per day (same day, same number of trades, eligible names NOT in
   the list, same direction and stop rule): setup avg R − control mean avg R > 0 on CHECK and T2, with day-clustered
   paired t >= 2.0 on CHECK. Without this, any positive result is the rule, not the ranker.
5. Effect report (remedy rule analogue): results split by family (gap >= 1 ATR-pct vs not; long vs short; price
   bucket) — how many cells positive / negative and by how much.
FIT is reported, never used to tune after this file. A strong ranker with no setup passing = LEAD. Live window: no live
trades of these rules exist; ledger rule changes are noted only if a live window is reported.

## Count
Configurations this study: 8 rankers + 6 setup-sides = 14. Cumulative ≈ 8,952 → ≈ 8,966.
