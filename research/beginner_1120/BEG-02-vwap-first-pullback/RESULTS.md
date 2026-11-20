Educational only — not financial advice

# BEG-02 VWAP first pullback in a trend (long and short): results

*Research only. No setup, exit, config, account or ledger change.*
- Configurations tried: **4** (the base plus 3 pre-registered one-part tweaks). The random control fits nothing.
- The locked block 2024-11-01..2025-02-28 was never read.
- CHECK was scored once for the base and once for the FIT pick.
- R is after LR8 costs, plus 1.2 bp borrow on shorts.
- The trades are booked under the testing-arena rules: cap 100, <= 3 lots per symbol, price >= $5, ETB >= 90%, the
  0.15R stop-cost filter.

**Verdict:**
- **Base: FAIL, and REALLY BAD.** T1 combined avg R is −0.107 with a day-clustered t of −3.02. Every test is below
  −0.03 except T2, which is just below at −0.097.
- **Tweak `win1000` (entries from 10:00): FAIL, and REALLY BAD.** T1 combined is −0.084 (t −2.18).
- Neither should go to a testing arena.

## Files
- `beg02.py`: the module.
  - It uses the live `Strategy.generate(ctx)` interface on 1-minute bars, plus the pure functions `find_signal` and
    `walk` that the backtest uses.
  - The [R] notes in its docstring are the plainest readings of the ambiguous parts of the spec.
- `smoke_test.py`: tests the module (passes). It runs a synthetic trend day through the module and through
  `mcf.backtest.engine.simulate`.
- `run.py`: the engine.
  - Signals and exits use 1-minute bars, because the setup is defined on 1-minute bars. Entry is at the next bar's
    open.
  - Costs, the book and `stats()` are imported unchanged from `research/ultimate_1119/top10/bench10.py`.
- `PLAN.md`: the pre-registration. It covers the base and verdict rule, and the tweaks, which were written after the
  FIT diagnosis and before they were scored.
- `diag.py`: the FIT-only diagnosis of the losers.
- `summarize.py` writes `results.json`, which holds every figure below.
- Trade lists (~220 MB, in the session scratchpad `beg02w/`) are not in the repo. They can be regenerated with
  `run.py build1|build2|score`.

## Implementation notes (plainest readings)
- **Universe.**
  - U0 = prior close >= $5 and ADV20 >= $20M.
  - Price >= $10 is checked on the prior close.
  - rank_rvol20 uses `mcf.backtest.engine`'s definition: the 09:30-09:49 volume / the mean of the prior 14 sessions
    (min 5), ranked among the day's U0 names. The cut is rank <= 50.
  - T1 daily context (ATR, ADV20, prev close from the gap) comes from the lab frames, point in time. The rolling
    volume mean never spans the locked gap, so the first ~4 sessions of 2025-03 have no rank and no trades.
  - T2 ranks among only the 469 cache_fresh names, so top-50 is a wider cut there.
- **Setup.** "Price at 09:50" is the 09:49 close. Every 1-minute close present from 09:35 to 09:49 must be on the
  trend side of session VWAP (typical-price VWAP, as `mcf.features.vwap`).
- **Trigger.**
  - One look per symbol-day: the first bar from 09:50 that touches within 0.10% of VWAP and closes back on the trend
    side.
  - If that bar fails the 1.5R target-room test, there is no trade that day.
  - Signal bars run 09:50..12:59, so the last entry is 13:00.
- **Stop.**
  - The bar's low − $0.02 (high + $0.02 for a short), widened to 0.15 x ATR if closer.
  - R and the 2R/1.5R target tests use the trigger-bar close, the price known at the decision. The booked R uses the
    real next-bar fill.
- **Exits.**
  - Stop first. A gap-through fills at the worse of open/stop.
  - The target fills only when traded through by $0.01.
  - Time stop: after 60 minutes, exit at the next open if +0.5R was never reached.
  - Max hold 120 minutes. Flat at 15:55.

## Step 2: base scores (testing-arena book)
| test | trades | /session | win | avg R | gross | avg R w/o best day | best day (R) | total R/session | worst day | t (day-clustered) |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 FIT (170 sessions) | 505 | 2.97 | 34.7% | −0.146 | −0.048 | −0.170 | 2025-04-10 (+10.8) | −0.432 | −7.6 | −2.32 |
| T1 CHECK (276) | 1,149 | 4.16 | 35.6% | −0.089 | −0.005 | −0.100 | 2026-03-25 (+11.2) | −0.372 | −6.7 | −2.10 |
| T1 combined (446) | 1,654 | 3.71 | 35.3% | **−0.107** | −0.018 | −0.114 | 2026-03-25 (+11.2) | −0.395 | −7.6 | −3.02 |
| T2 2023-24, reference (427) | 902 | 2.11 | 36.7% | −0.097 | +0.004 | −0.106 | 2023-07-20 (+7.7) | −0.205 | −8.2 | −1.97 |

- Total R is negative in every test, so the best-day share is not defined. The best day is +10.8 to +11.2R against
  totals of −73 to −176R, so the record is not carried by one day: it is uniformly negative.
- About half of the raw trades fail the 0.15R stop-cost filter: FIT 996 raw → 505 booked.
- By side (T1 combined): longs −0.122, shorts −0.089.
  - Longs on SPY-down days are −0.37; on SPY-up days they are +0.00.
  - Shorts on SPY-up days are −0.20; on SPY-down days they are −0.02.
- **Vs random entries.** These are on the same symbol-days, with the same side, $ stop and target multiple, and a
  random entry minute, over 5 seeds:
  - T1 combined: random −0.096 / −0.099 / −0.099 / −0.144 / −0.175 (mean −0.123), against the setup's −0.107;
  - T2: random −0.193 / −0.151 / −0.140, against −0.097.
  - **On T1 the VWAP-touch trigger is no better than a random minute on the same trend days.** On T2 it is somewhat
    better.

## Step 3: tweaks (FIT diagnosis → 3 pre-registered one-part tweaks → pick on FIT → scored once)
**Diagnosis (FIT only).**
- **The stop is the failure.** 86% of trades (434/505) sit on the 0.15 x ATR floor, because the pullback bar is tiny.
- 167 trades are stopped within 5 minutes, for −113.7R. That is more than the whole −73.5R loss. Trades held
  15+ minutes average +0.2R.
- Costs take ~0.10R a trade.
- Timing: 09:50-10:00 signals −0.20; 10:00-10:30 −0.06; 10:30-12:00 −0.21 / −0.28.
- The 25 worst losers are all stops at about −1.2 to −1.7R. Nearly all are on the 0.15 ATR floor, and most are shorts
  stopped within minutes of entry.

| tweak (part) | FIT booked (raw) | FIT avg R | gross | w/o best day | total R/session | t |
|---|---|---|---|---|---|---|
| base | 505 (996) | −0.146 | −0.048 | −0.170 | −0.432 | −2.32 |
| `stop030`: stop floor 0.30 x ATR (stop) | 402 (510) | −0.139 | −0.066 | −0.158 | −0.330 | −2.20 |
| `stopx15`: stop distance x 1.5 (stop) | 496 (726) | −0.203 | −0.121 | −0.223 | −0.591 | −3.63 |
| **`win1000`: entries from 10:00 (window)** | 489 (967) | **−0.131** | −0.032 | −0.155 | −0.376 | −2.01 |

- Wider stops did not rescue it. They cut the cost drag, but the gross edge got worse: more room just meant bigger
  losers.
- **Pick on FIT: `win1000`.**

**The picked tweak, scored once:**

| test | trades | avg R | gross | w/o best day | best day (R) | total R/session | worst day | t |
|---|---|---|---|---|---|---|---|---|
| T1 FIT | 489 | −0.131 | −0.032 | −0.155 | +10.8 | −0.376 | −6.8 | −2.01 |
| T1 CHECK | 1,152 | −0.064 | +0.020 | −0.077 | 2026-02-24 (+14.3) | −0.268 | −7.3 | −1.35 |
| T1 combined | 1,641 | **−0.084** | +0.004 | −0.093 | +14.3 | −0.309 | −7.3 | −2.18 |
| T2 (reference) | 863 | −0.121 | −0.021 | −0.132 | +8.8 | −0.245 | −9.2 | −2.27 |

- Random control with the 10:00 window (T1 combined, 5 seeds): −0.129 / −0.163 / −0.135 / −0.156 / −0.130 (mean
  −0.142). **The tweak beats all five seeds by ~0.06R.** This is the only sign of a real timing edge.
- The tweak's gross is about zero (+0.004), so after costs it still loses.
- By side and tape (T1 combined):
  - longs on SPY-up days +0.133 (vs −0.316 on SPY-down days);
  - shorts on SPY-down days +0.005 (vs −0.164 on SPY-up days).
  - This was observed and **not tested**: it would be a further configuration.

## Step 4: against the top-10 benchmark (research/ultimate_1119/top10/PLAN.md)
Reminder: the benchmark medians are themselves negative. "Meets" would mean "no worse than the setups winning live".
It would not mean profitable in backtest.

| Tier A leg | threshold | base | gap | `win1000` | gap |
|---|---|---|---|---|---|
| T1 combined avg R | >= −0.0383 (median −0.0283) | −0.1065 | −0.068 FAIL | −0.0840 | −0.046 FAIL |
| T1 check avg R | >= −0.0464 (median −0.0364) | −0.0894 | −0.043 FAIL | −0.0642 | −0.018 FAIL |
| T1 combined w/o best day | >= −0.0674 | −0.1138 | −0.046 FAIL | −0.0932 | −0.026 FAIL |
| T1 check w/o best day | >= −0.0781 | −0.0998 | −0.022 FAIL | −0.0772 | pass |
| T1 combined total R/session | >= −0.4862 | −0.395 | pass | −0.309 | pass |
| T1 check total R/session | >= −0.5218 | −0.372 | pass | −0.268 | pass |
| T2 avg R | >= −0.1048 (median −0.0848) | −0.0969 | pass | −0.1212 | −0.016 FAIL |
| trades check / T2 >= 20 | | 1,149 / 902 | pass | 1,152 / 863 | pass |
| **Tier** | | **FAIL** | | **FAIL** | |
| REALLY BAD (T1 comb <= −0.05 with t <= −2, or all three < −0.03) | | **yes** (−0.107, t −3.02; all three) | | **yes** (−0.084, t −2.18; all three) | |

NEAR needs every failing avg-R leg within 0.02R. Both versions miss T1 combined by more than 0.02R, so neither is NEAR.

**Rule-change context.** The backtests apply today's rule set (the LR8 cost basis, the testing-arena book of 11-17,
the ETB proxy) to every session. No rule change falls inside the scored windows. No live record exists for this setup.

## What can be salvaged (optimistic next steps; all go to `research/backlog.jsonl`, none ship)
1. **The pullback trigger is too early and too tight.**
   - Most losses are stop-outs within 5 minutes on a 0.15 ATR stop at VWAP.
   - Waiting until 10:00 helped on every test except T2.
   - A trigger that waits for confirmation could avoid the instant stop-outs without widening the stop, which failed.
     One example: a close back above the pullback bar's high, with the stop under the pullback low.
2. **Trade with the tape.** Longs on SPY-up days (+0.13) and shorts on SPY-down days (~0) were the only positive
   pockets of the tweaked version. This is DESIGN.md session rule S7 ("trade with the tape"), so it should be tested
   as that rule, pre-registered on FIT. It is untested here.
3. **Costs eat ~0.09-0.10R a trade.** Any revival needs gross >= ~+0.10R. Today it is about 0.
4. Overlap: the theme matches MCF's existing VWAP setups. No overlap check was run, because nothing was admitted.
