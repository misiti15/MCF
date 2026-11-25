# capfit PLAN (pre-registered 2026-11-25 before any cap level was scored). Educational only - not financial advice.

Setups: setups.csv (top 20 by avg R/trade without best session, >=20 live trades, >=8 sessions, through 11-24, + NM-ETF; 3 Primary already in top 20) = 21.

Latch semantics (as live / bench10 book): per setup per day, an entry at time e is blocked if closed cost-R (LR8) of that
setup's trades with exit <= e is <= L. Open trades run to their own exits. Day resets. Live: deduped trades (strategy|symbol|date|entry minute).
Grid L in {-1.00,-1.25,...,-4.00} (13) + none.

Descriptive per setup: touch(L) = days whose no-cap closed path reached <= L; P(final day R > L | touch), P(final >= 0 | touch);
gain(L) = sum over days of R(cap L) - R(none).

P1 (main) per-setup bottom-out level, calibration set C: L* = shallowest L with touch_C(L) >= 2, gain_C(L) > 0 and
gain_C(L') >= 0 for every deeper L' with touch_C(L') >= 1. None found -> no cap. Fewer than K=8 sessions in C -> setup-day not scored.
P2: P1 clamped to [-4.0, -1.5]; fewer than K sessions -> -2 (status quo) [scored on the same set as P1, so effectively P1 clamped].
P3 (greedy): L = argmax gain_C(L) if > 0 else none.
Sensitivity: P1 with K=5 (scored on its own larger set, compared to its own baselines).
Walk-forward live: ISO weeks; calibrate on all sessions of the setup before the week (expanding = rolling here, <=7 weeks), apply to the week.
Baselines on the identical setup-day set: none, uniform -2.
Report: total R, portfolio worst day, avg R/trade w/o best day, per-setup improve/worse vs none and vs -2 (count, size),
best-day share, day-clustered t of daily dR.
Live caveat to measure: censoring by the real -2R latch (Primary >=10-29, Graveyard >=10-21, Testing/Testing2 10-19..10-22).

Lab (bench10 candidate lots, LR8 + borrow, home-account book cap/symcap, latch replaced by L) for setups that exist there:
4 Primary (pyramid/L1 trades), GEN-261029-06, GEN-261023-06, ST5 (pyramid/S work). FIT / CHECK / T2(2023-24). Locked block never read.
Lab A (static): L* from FIT by P1/P2/P3 (K irrelevant), scored on CHECK and T2 vs none and -2.
Lab B (rolling): weekly, calibrate on trailing 60 sessions of the setup (min 20), across T2 -> FIT -> CHECK; report L* stability.
MAE angle: P(trade final R >= 0 | MAE <= -x), x in {0.25, 0.5, 0.75}, per setup; lab (1-min bars) and live where bars exist.
Configurations counted: 14 descriptive levels; live WF 3 + 1 sensitivity; lab 3 static + 3 rolling; MAE 3 descriptive.
Bar for "better": day-clustered t >= 2.0 vs both baselines out of sample, and more setups improve than worsen, no setup worse by > 3R.
Wed Nov 25 01:31:50 UTC 2026
