Educational only — not financial advice

# BEG-09 Midday range -> high/low-of-day break (long and short): results

Research only. Nothing was changed in any setup, exit, config, account or ledger. **Configurations tried: 4** (the base
plus 3 pre-registered one-part tweaks). The two random controls count as 0 fitted configurations. The locked block
2024-11-01..2025-02-28 was never read. PLAN.md was written before any scoring, and its "Tweaks" section was written
before any tweak was scored.

**Verdict: base = FAIL (and REALLY BAD on leg 1); tweak `stopx15` = FAIL.** The tweak misses NEAR by 0.002R on the
T1-check avg-R leg. Every other Tier A leg passes.

## 1. What was tested
- **Spec** (DESIGN.md B09, as written):
  - universe: U0 + prior close >= $10 + rank_rvol20 <= 30;
  - side: the day's return at 11:30 is >= +3% (long) or <= −3% (short);
  - setup: the first 30-minute window inside 11:30-14:30 whose range is <= 0.35 x ATR, with every close above VWAP
    (short: below);
  - entry: a buy-stop at HOD + $0.01 (short: sell-stop at LOD − $0.01, easy to borrow only), valid until 15:00;
  - stop: the consolidation low − $0.02 (short: high + $0.02);
  - exit: 2R target, otherwise 15:55.
- **Plainest readings** are marked [R] in `beg09.py`:
  - the side comes from the 11:29 bar close;
  - "at least 30 minutes" is met by the first window of 30 contiguous bars;
  - the order is armed from the next bar and is not cancelled if price leaves the range;
  - the fill is max(open, trigger);
  - the 2R target is measured from the order price, and the booked R uses the real fill;
  - the stop is checked first, including on the fill bar.
- **Engine**: the bench10 "normal way". LR8 costs plus 1.2 bp borrow on shorts, and the testing-arena book (cap 100,
  <= 3 lots per symbol, ETB >= 90%, stop-cost filter 0.15R). rank_rvol20 and the point-in-time day context are reused
  read-only from the BEG-02 day tables.
- **Windows**:
  - FIT: 2024-10 + 2025-03..09 (170 sessions);
  - CHECK: 2025-10-01..2026-11-04 (276 sessions), scored once for the base and once for the pick;
  - T2: 2023-01..2024-09 (427 sessions, 469-symbol cache, seen before; reference only).
- **Files**:
  - `beg09.py`: the module, with the live `Strategy` interface (one stop-order Signal on the bar that completes the
    window, `entry_valid_bars` until 15:00);
  - `smoke_test.py`: passes. It checks the live class against the backtest helpers and `mcf.backtest.engine.simulate`;
  - `run.py`, `diag.py`, `variants.json`, `results.json`;
  - trade lists in the session scratchpad `beg09w/` (~110 MB), which `run.py` can regenerate.

## 2. Base (as written)
| test | trades | /session | win | avg R | gross | avg R w/o best day | best-day share | R/session | worst day | day-t | SPY up / flat / down |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 fit | 481 | 2.83 | 0.453 | −0.024 | +0.030 | −0.041 | n/a (total < 0) | −0.068 | −10.7 | −0.45 | +0.088 / −0.014 / −0.181 |
| T1 check | 1034 | 3.75 | 0.424 | **−0.077** | −0.027 | −0.086 | n/a | −0.289 | −8.5 | −2.11 | −0.001 / −0.187 / −0.020 |
| T1 combined | 1515 | 3.40 | 0.433 | **−0.060** | −0.009 | −0.066 | n/a | −0.205 | −10.7 | −2.01 | +0.028 / −0.134 / −0.073 |
| T2 (ref) | 1065 | 2.49 | 0.445 | −0.037 | +0.021 | −0.044 | n/a | −0.092 | −9.4 | −1.04 | +0.007 / −0.112 / −0.006 |

- **By side:** shorts lose in every test (avg R fit −0.057, check −0.103, T2 −0.145). Longs are near flat (+0.005,
  −0.055, +0.046).
- **Costs:** about 0.05R a trade.
- **By exit type:**
  - stops: 34% of trades, about −1.08R each;
  - targets: 11%, +1.96R each;
  - 15:55 time exits: 55%, +0.21..+0.29R each.

## 3. Tweaks (FIT only, pre-registered after diagnosing the worst FIT losers)
**Diagnosis (diag.py, FIT):**
- All 40 worst trades are stop-outs. Their median hold is 54 minutes and their median risk is 0.31 x ATR.
- Stops tighter than 0.3 x ATR averaged −0.15R. Stops wider than 0.5 x ATR averaged +0.14R.
- Windows that complete in the first 15 minutes possible (11:59-12:15) lost −28.8R. Later windows made +17.2R.
- Only 11% of trades reached 2R, while the 15:55 exits were positive.

| tweak (one part) | FIT trades | FIT avg R | w/o best day | R/session | day-t |
|---|---|---|---|---|---|
| base | 481 | −0.024 | −0.041 | −0.068 | −0.45 |
| **T1 `stopx15`: stop distance x 1.5 (target scales)** | 550 | **−0.005** | −0.019 | −0.016 | −0.12 |
| T2 `win1200`: window starts 12:00 or later | 424 | −0.049 | −0.062 | −0.121 | −0.95 |
| T3 `notgt`: no 2R target, hold to 15:55 | 481 | −0.023 | −0.043 | −0.064 | −0.39 |

The pick is `stopx15`. The "later window" pattern did not hold up once applied as a rule: T2 made the setup worse.

**The pick, scored once on CHECK and on T2:**
| test | trades | /session | win | avg R | gross | avg R w/o best day | best-day share | R/session | worst day | day-t | SPY up / flat / down |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 fit | 550 | 3.24 | 0.478 | −0.005 | +0.036 | −0.019 | n/a | −0.016 | −8.6 | −0.12 | +0.112 / −0.046 / −0.105 |
| T1 check | 1104 | 4.00 | 0.454 | **−0.069** | −0.033 | −0.074 | n/a | −0.274 | −7.9 | −2.44 | −0.021 / −0.151 / −0.014 |
| T1 combined | 1654 | 3.71 | 0.462 | **−0.047** | −0.010 | −0.052 | n/a | −0.176 | −8.6 | −2.03 | +0.023 / −0.117 / −0.044 |
| T2 (ref) | 1219 | 2.85 | 0.477 | −0.017 | +0.025 | −0.024 | n/a | −0.049 | −8.1 | −0.61 | −0.002 / −0.075 / +0.036 |

**Effect of the tweak by side** (the remedy-reporting rule):
- Longs improve on FIT (+0.005 → +0.043) and CHECK (−0.055 → −0.023), and get worse on T2 (+0.046 → +0.017).
- Shorts are about flat on FIT (−0.057 → −0.062), worse on CHECK (−0.103 → −0.124) and better on T2 (−0.145 → −0.062).
- With the wider stop, costs fall from ~0.05R to ~0.04R a trade. Stop-outs fall from 34% to 23% of trades.

## 4. Controls (5 seeds each, booked the same way; mean avg R, with the range)
| control | T1 fit | T1 check | T1 combined | T2 |
|---|---|---|---|---|
| base, pre-registered (same filled days, entry 12:00-14:59) | +0.181 | +0.146 | +0.157 | +0.148 |
| base, **fair: every armed day, entry after arming** | −0.008 (−0.031..+0.019) | −0.048 (−0.056..−0.033) | −0.035 | −0.066 |
| stopx15, pre-registered | +0.136 | +0.093 | +0.108 | +0.095 |
| stopx15, **fair** | +0.003 (−0.009..+0.012) | −0.047 (−0.056..−0.034) | −0.031 | −0.051 |

- **The pre-registered control is look-ahead biased.** It buys at random from 12:00 on days that are already known to
  break the HOD later. Treat it as an upper bound, not a baseline. The fair control was added and documented in
  PLAN.md before any tweak was scored.
- **Against the fair control, the HOD-break trigger adds no edge on T1.**
  - Base: check −0.077 vs −0.048; fit −0.024 vs −0.008.
  - stopx15: check −0.069 vs −0.047.
- It does beat the fair control on T2: −0.037 vs −0.066, and −0.017 vs −0.051.

## 5. Against the top-10 benchmark (research/ultimate_1119/top10/PLAN.md Tier A, testing-arena book)
| leg | threshold | base | stopx15 |
|---|---|---|---|
| T1 combined avg R | >= −0.0383 | −0.0603 ✗ (−0.022) | −0.0474 ✗ (−0.009) |
| T1 check avg R | >= −0.0464 | −0.0772 ✗ (−0.031) | −0.0686 ✗ (−0.022) |
| w/o best day, combined / check | >= −0.0674 / −0.0781 | −0.0664 ✓ / −0.0862 ✗ | −0.0523 ✓ / −0.0743 ✓ |
| R/session, combined / check | >= −0.4862 / −0.5218 | −0.205 ✓ / −0.289 ✓ | −0.176 ✓ / −0.274 ✓ |
| T2 avg R | >= −0.1048 | −0.037 ✓ | −0.017 ✓ |
| >= 20 trades on check and T2 | | ✓ | ✓ |
| **tier** | | **FAIL** | **FAIL** (misses NEAR by 0.002R on check) |
| REALLY BAD | combined <= −0.05 with t <= −2.0, or < −0.03 on all of fit, check and T2 | **yes** (−0.060, t −2.01) | no |

- The benchmark medians are T1 combined −0.0283, T1 check −0.0364 and T2 −0.0848.
- On T2, stopx15 (−0.017) is better than the median and than 9 of the 10 benchmark setups. Only RW6 (+0.034) is
  better.
- On the scored T1 check it sits ~0.03R below the median.
- All the medians are negative. "Meets" would only mean "backtests no worse than the setups winning live". It would
  not mean profitable.

## 6. Reading it (honest, costs in)
- **Shorts cause most of the loss.**
  - In every test, both versions, longs are about zero to slightly positive. The best is stopx15 longs on FIT,
    +0.043.
  - Shorts are −0.06 to −0.15.
  - "Strong stocks resting above VWAP then breaking the high" is at best weakly supported on the long side. The
    weak-stock mirror does not work here.
- **Wider stops help.**
  - The structural stop under a tight midday range is close enough for ordinary afternoon noise to hit within an
    hour.
  - x1.5 cuts stop-outs from 34% to 23% and lowers costs per trade. It lifted every test except T2 longs.
- **The time of day carries the payoff, not the trigger.**
  - 15:55 exits are consistently positive, but random entries after arming do about as well as the HOD break.
  - So the information is in the "trending day + midday rest" selection, not in the breakout order.
- **Next step (backlog idea, not scored here; it would be configuration 5 and needs its own pre-registration):** a
  long-only `stopx15` version, possibly with an entry at a fixed time after arming instead of the HOD stop.
  - The FIT/CHECK/T2 side splits above are the evidence for it.
  - They come from runs already made. No new configuration was scored to produce them.
- **Rule-change context:**
  - Every backtest applies one fixed rule set (today's LR8 costs and testing-arena book) to every session, so no
    rule change falls inside the test windows.
  - The live benchmark figures come from 2026-10-06..11-18. That window spans the rule changes listed in
    research/ultimate_1119/top10/BENCHMARK.md §1: refire option B 10-14, cost filter 0.15R 10-30, LR8 cost model
    11-12, half-size Testing A-F lots 11-17, and others.
- **Known biases (inherited from bench10):**
  - the lab universe is ~1,200 names (survivorship);
  - T2 ranks rvol among only 469 symbols, so top-30 is a looser cut there;
  - there is no earnings blackout, and no spread or quote checks;
  - ETB uses today's flags.
