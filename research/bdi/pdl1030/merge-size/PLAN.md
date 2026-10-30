Educational only — not financial advice.

# pdl1030 / merge-size: PLAN (written before any scoring)

Family: merge the four Failed Prior-Day-Low Break Longs (CWT14-failbrk-pdl-p05-long, -p05-lowvol-long, -p10-long,
-p10-lowvol-long) into ONE setup and use sizing and risk sharing instead of filters.

## Data and rules
- Open frames, TRAIN (<= 2025-12: 2024-10, 2025-03..12) and VALID (2026-01..03, 2026-07..2026-09-15) only. HOLD months
  (2026-04..06, 2026-09-16..10-07) and the locked block (2024-11-01..2025-02-28) are never loaded (asserted at load,
  same loader patch as pdl1030/why/feat.py).
- Kernel S6.b3_any (PD level, long side), same base as swarm15: adv20 >= 95M, atr_d > 0, signal bar 09:50..15:00.
- Simulator: top5_1028 `sim`, unchanged (costs 1c/share + 1 bp per side, entry x time-of-day multiplier, +2c on stop
  exits, x3 on the extended tier). Entry at the signal-bar close.
- Parent parity first: p05, p05-lowvol, p10 TRAIN+VALID must match swarm15 within 0.005R (p10-lowvol is not in swarm15;
  reported only). If parity fails, stop.

## Merged setup (the union)
- Signal: the bar-level OR of the four parent masks (p in {0.05, 0.10} x vr cap in {none, 1.0}); one trade per
  symbol-day at the EARLIEST bar on which any parent fires.
- Exit: the p05 exit (stop 1R = 0.25 ATR, target 0.5R, 25%-of-R scale-out half off with stop to entry, flatten 15:55),
  because the union's earliest bar is almost always the p05 bar.
- Membership flag (known at the signal-bar close): how many of the four parent masks are true on the entry bar.

## Scoring on R per unit of risk
- Each trade gets a weight w > 0 (fraction of the base $ risk). Book avg R = sum(w r) / sum(w).
- Day-clustered t: se = sqrt(sum_d (sum_{i in d} w_i (r_i - mu))^2) / sum(w) (equals gates.summary when w = 1).
- Walk-forward: share of months with sum(w r) > 0. Up/down SPY-day weighted avg R (descriptive). Avg R w/o best day.
- Exposure: trades/session = number of trades with w > 0 per session (no config here sets w = 0, so every config keeps
  the full union count); risk units/session = sum(w)/sessions is reported alongside, honestly.

## Configurations (pre-declared; 16 new + 4 parent re-scores = 20 counted)
| id | risk unit | weight w (all known at the signal-bar close) |
|----|-----------|-----------------------------------------------|
| P05, P05LV, P10, P10LV | parent | parent rows (parity) |
| M0 | 1R = 0.25 ATR | w = 1 (plain merged book) |
| W1 | 1R | w = 0.5 if SPY is below its VWAP at the signal bar, else 1 |
| W2 | 1R | w = 0.5 if breadth < 0.5 at the signal bar, else 1 |
| W3 | 1R | tape score: w = 0.25 + 0.25*[SPY above VWAP] + 0.25*[breadth >= 0.5] + 0.25*[SPY gap <= -0.5%] |
| W4 | 1R | break depth: w = clip(depth / 0.25 ATR, 0.5, 2), depth = PDL - day low so far, in ATR |
| W5 | 1R | cost share: w = clip(0.05 / roundtrip_cost_R, 0.25, 1) (full size when cost <= 5% of R) |
| W6 | 1R | session risk budget: w = min(1, 30 / k), k = number of union signals in the session up to and including this bar |
| W7 | 1R | merge weight: w = number of parent masks firing on the entry bar (1..4) |
| S1 | 3R stop at the same $ risk (stop e - 0.75 ATR; target / scale prices unchanged) | w = 1 |
| C1 | S1 | W5 computed on the S1 risk unit |
| C2 | S1 | W5 x W1 |
| C3 | S1 | W5 x W6 |
| C4 | S1 | W5 x W3 |
| C5 | S1 | W5 x W1 x W6 |
| H1 | 1R, w = 1 | plus an SPY short held entry -> exit, notional = 100 * b * $risk per trade, b = TRAIN OLS slope of r on the SPY % move during the trade (fit on TRAIN only); SPY costs 1c/share + 1 bp per side |
| H2 | S1, W5 (= C1) | plus the same SPY hedge, b fit on TRAIN C1 trades |

No configuration is added after scoring. If any is, it is disclosed as an addendum and counted.

## Bar (rule 22, BAR90)
N = 121512 + 3 * 20 = 121572; bar t >= 0.9 * max(1.5, sqrt(2 ln N)) = 4.355. Also walk-forward >= 54% of months positive,
avg R > 0 on TRAIN and on VALID separately, avg R beats p05 (-0.0677 TRAIN / -0.0675 VALID) on both, and exposure
>= 76.6 trades/session (50% of p05's 153.2) or >= 25/session.
