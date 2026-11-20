Educational only — not financial advice

# BEG-10 Narrow-range day -> first-30-minute breakout (long and short): results

Research only. Nothing was changed in any setup, exit, config, account or ledger. **Configurations tried: 4** (the base
plus 3 pre-registered one-part tweaks). The random controls count as 0 fitted configurations. The locked block
2024-11-01..2025-02-28 was never read. PLAN.md was written before any scoring. Its "Tweaks" section was written
after the FIT-only diagnosis and before any tweak was scored.

**Verdict: base = FAIL and REALLY BAD. Tweak `win1015` (the fit pick) = FAIL and REALLY BAD.** Both miss every T1
Tier A leg. Both pass only the T2 leg. On T1, neither beats random entries placed on the same armed days.

## 1. What was tested
- **Spec** (DESIGN.md B10, as written):
  - universe: U0 + price >= $10 + ADV20 >= $30M;
  - setup: yesterday's range <= 0.6 x ATR; skip if the 09:30-09:59 range (OR30) is > 0.8 x ATR;
  - entry: OCO stop orders, a buy-stop at OR30 high + $0.01 and a sell-stop at OR30 low − $0.01 (easy to borrow
    only), working 10:00-12:30;
  - stop: the OR30 midpoint;
  - exit: 2R target, otherwise 15:55.
- **Plainest readings** are marked [R] in `beg10.py`:
  - price is checked on the prior close;
  - yesterday's range is the prior RTH session's high − low (1-minute bars). ATR is the daily ATR14 at the prior
    close;
  - the orders work on the 10:00..12:29 bars;
  - fill = max(open, trigger) (short: min). If one bar touches both triggers, the side nearer the open fills;
  - on a non-ETB name only the buy-stop is placed;
  - 2R is measured from the order price, and the booked R uses the real fill;
  - the stop is checked first, including on the fill bar.
- **Engine**: the bench10 "normal way". LR8 costs plus 1.2 bp borrow on shorts, and the testing-arena book (cap 100,
  <= 3 lots per symbol, ETB >= 90%, stop-cost filter 0.15R). The point-in-time day context (prev close, ATR, ADV20)
  is reused read-only from the BEG-02 day tables.
- **Windows**:
  - FIT: 2024-10 + 2025-03..09 (170 sessions);
  - CHECK: 2025-10-01..2026-11-04 (276 sessions), scored once for the base and once for the pick;
  - T2: 2023-01..2024-09 (427 sessions, 469-symbol cache, seen before; reference only).
- **How often it fires.** About 18-19% of eligible symbol-days are narrow-range days by this definition. That gives
  ~29k raw T1-fit trades. After the book (cap 100 binds often), 81-90 trades are booked per session on T1, and 30 per
  session on T2.
- **Files**:
  - `beg10.py`: the module, with the live `Strategy` interface. It emits two stop-order Signals at the 09:59 close,
    tagged `meta["oco"]`. **The live engine has no entry OCO today.** Deploying it would need that support, or one leg
    only;
  - `smoke_test.py`: passes. It checks the live class against the backtest helpers and `mcf.backtest.engine.simulate`;
  - `run.py`, `diag.py`, `variants.json`, `PLAN.md`, `results.json`;
  - booked trade lists are in the session scratchpad `beg10w/` (28 MB). The candidate bars (~470 MB) were deleted to
    save disk. `run.py WORK build t1|t2` regenerates them.

## 2. Base (as written)
| test | trades | /session | win | avg R | gross | avg R w/o best day | best-day share | R/session | worst day | day-t | SPY up / flat / down |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 fit | 13,733 | 80.8 | 0.409 | −0.053 | +0.027 | −0.064 | n/a (total < 0) | −4.28 | −146.8 | −1.65 | +0.074 / −0.184 / −0.049 |
| T1 check | 24,779 | 89.8 | 0.397 | **−0.076** | −0.006 | −0.081 | n/a | −6.81 | −127.3 | −3.78 | −0.033 / −0.171 / +0.034 |
| T1 combined | 38,512 | 86.4 | 0.401 | **−0.068** | +0.006 | −0.072 | n/a | −5.85 | −146.8 | −3.92 | +0.010 / −0.175 / +0.003 |
| T2 (ref) | 12,972 | 30.4 | 0.407 | −0.052 | +0.034 | −0.058 | n/a | −1.59 | −60.3 | −2.31 | +0.006 / −0.190 / +0.099 |

- **By side:**
  - longs: fit −0.028, check −0.098, T2 −0.039;
  - shorts: fit −0.084, check −0.052, T2 −0.067.
- **Costs:** 0.07-0.09R a trade. Gross R is about zero (−0.006 to +0.034), so the costs decide the sign.
- **By exit type (T1):**
  - stops: 49% of trades;
  - targets: 20%;
  - 15:55 time exits: 31%.
- **SPY flat days** (|SPY open-to-close| < 0.3%) are the worst in every test, at about −0.17 to −0.19R. A breakout
  needs a day that trends.

## 3. Tweaks (FIT only, pre-registered after diagnosing the worst FIT losers)
**Diagnosis (diag.py, FIT):**
- **Fast stop-outs carry the loss.** Stops total −7,527R; targets +5,450R; time exits +1,349R.
- The worst 10% of trades are all stop-outs. Their median hold is 35 minutes. Their risk is tighter than usual
  (0.17 vs 0.21 x ATR) and their cost is 0.16R.
- Trades stopped within 30 minutes average −0.55 to −0.73R. Trades held more than 2 hours average +0.23R.
- Narrow OR30s (< 0.3 x ATR) are worst.
- Fills after 10:15 are worse than fills at 10:00-10:15.

| tweak (one part) | FIT trades | FIT avg R | gross | w/o best day | R/session | day-t | long / short |
|---|---|---|---|---|---|---|---|
| base | 13,733 | −0.053 | +0.027 | −0.064 | −4.28 | −1.65 | −0.028 / −0.084 |
| T1 `stopx15`: stop distance x 1.5 (target scales) | 14,763 | −0.044 | +0.022 | −0.052 | −3.78 | −1.69 | −0.018 / −0.074 |
| **T2 `win1015`: orders valid 10:00-10:15 only** | 8,286 | **−0.034** | +0.049 | −0.049 | −1.65 | −0.79 | −0.011 / −0.065 |
| T3 `ormin03`: also skip if OR30 < 0.3 x ATR | 11,246 | −0.041 | +0.035 | −0.052 | −2.71 | −1.29 | −0.026 / −0.059 |

All three tweaks improved FIT, by 0.01-0.02R. The pick is `win1015`.

**The pick, scored once on CHECK and on T2:**
| test | trades | /session | win | avg R | gross | avg R w/o best day | best-day share | R/session | worst day | day-t | SPY up / flat / down |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 fit | 8,286 | 48.7 | 0.406 | −0.034 | +0.049 | −0.049 | n/a | −1.65 | −98.0 | −0.79 | +0.103 / −0.162 / −0.054 |
| T1 check | 14,588 | 52.9 | 0.385 | **−0.087** | −0.014 | −0.094 | n/a | −4.60 | −75.6 | −3.21 | −0.047 / −0.179 / +0.020 |
| T1 combined | 22,874 | 51.3 | 0.393 | **−0.068** | +0.009 | −0.074 | n/a | −3.47 | −98.0 | −2.91 | +0.015 / −0.174 / −0.008 |
| T2 (ref) | 7,454 | 17.5 | 0.399 | −0.056 | +0.034 | −0.065 | n/a | −0.97 | −42.0 | −1.81 | −0.027 / −0.187 / +0.117 |

**The FIT gain did not hold.** On CHECK the tweak is worse than the base (−0.087 vs −0.076). On T2 it is about the
same (−0.056 vs −0.052).

**Effect of the tweak by side** (the remedy-reporting rule; base → win1015):
| side | FIT | CHECK | T2 |
|---|---|---|---|
| longs | −0.028 → −0.011 (better) | −0.098 → −0.110 (worse) | −0.039 → −0.085 (worse) |
| shorts | −0.084 → −0.065 (better) | −0.052 → −0.061 (worse) | −0.067 → −0.022 (better) |

The tweak improves both sides on FIT only. Out of sample, 3 of the 4 side-test cells get worse.

## 4. Random-entry control (5 seeds each, booked the same way; mean avg R, with the range)
The control uses every armed symbol-day (OCO placed, filled or not), a random side (short only if ETB), entry at the
open of a random bar inside the order window, the same $ stop distance and the same 2R target.

| control | T1 fit | T1 check | T1 combined | T2 |
|---|---|---|---|---|
| base window (10:00-12:29) | −0.080 (−0.103..−0.064) | −0.063 (−0.081..−0.049) | −0.069 (−0.079..−0.060) | −0.083 (−0.097..−0.070) |
| win1015 window (10:00-10:14) | −0.093 (−0.109..−0.079) | −0.071 (−0.081..−0.061) | −0.079 (−0.087..−0.068) | −0.077 (−0.089..−0.056) |

- **Base vs control:**
  - T1 combined: −0.068 vs −0.069, a tie;
  - check: −0.076 vs −0.063, worse than random;
  - fit: +0.027 better than random;
  - T2: +0.031 better than random.
- **win1015 vs control:**
  - check: −0.087 vs −0.071, worse than random;
  - T2: −0.056 vs −0.077, better than random.
- The breakout trigger adds a small edge on FIT and T2. That edge is gone on the scored T1 check, where random
  entries did better.

## 5. Against the top-10 benchmark (research/ultimate_1119/top10/PLAN.md Tier A, testing-arena book)
| leg | threshold | base | win1015 |
|---|---|---|---|
| T1 combined avg R | >= −0.0383 | −0.0677 ✗ (−0.029) | −0.0677 ✗ (−0.029) |
| T1 check avg R | >= −0.0464 | −0.0759 ✗ (−0.030) | −0.0870 ✗ (−0.041) |
| w/o best day, combined / check | >= −0.0674 / −0.0781 | −0.0716 ✗ / −0.0808 ✗ | −0.0735 ✗ / −0.0941 ✗ |
| R/session, combined / check | >= −0.4862 / −0.5218 | −5.85 ✗ / −6.81 ✗ | −3.47 ✗ / −4.60 ✗ |
| T2 avg R | >= −0.1048 | −0.052 ✓ | −0.056 ✓ |
| >= 20 trades on check and T2 | | ✓ | ✓ |
| **tier** | | **FAIL** (both avg-R legs > 0.02R short of NEAR) | **FAIL** |
| REALLY BAD | combined <= −0.05 with t <= −2.0, or < −0.03 on all of fit, check and T2 | **yes** (−0.068, t −3.92; and all three < −0.03) | **yes** (−0.068, t −2.91; and all three < −0.03) |

- The benchmark medians are T1 combined −0.0283, T1 check −0.0364 and T2 −0.0848.
- Both versions beat the T2 median by about 0.03R. On T1 they are about 0.04-0.05R below the median.
- **The R/session leg fails by a factor of 7-13.** That comes from volume as well as quality. NR days are common, so
  the setup books 50-90 trades a session, and a small negative avg R becomes a large daily loss.
- All the medians are negative. "Meets" would only mean "backtests no worse than the setups winning live". It would
  not mean profitable.

## 6. Reading it (honest, costs in)
- **Too broad.** About 1 in 5 liquid names qualifies as "narrow range" every day. The 0.6 x ATR proxy is much looser
  than Crabel's NR7 (the narrowest of 7 days, ~14% by construction, and usually combined with an inside day). The
  trades are ordinary large-cap opening-range breaks with near-zero gross edge, and costs take 0.07-0.09R.
- **The midpoint stop is the main source of losses.** Half the trades are stopped out, mostly within 35 minutes. The
  costs, the +2c on stops and gap-throughs push the average loss to −1.1R. A wider stop helped FIT a little (−0.044)
  but not enough.
- **Day type matters more than the trigger.** Every version loses ~0.17-0.19R on SPY-flat days and is about flat or
  positive on trend days.
- **Promising next steps (backlog ideas, not scored here; each would need its own pre-registration):**
  - a true NR7 + inside-day definition, which is rarer and closer to the source;
  - a gate that skips the day when the market is quiet early (the SPY-flat losses);
  - a fill-quality gate, since entries that gapped through the trigger (slip > 0) averaged −0.10..−0.19R on FIT.
- **Rule-change context:**
  - Every backtest applies one fixed rule set (today's LR8 costs and testing-arena book) to every session, so no
    rule change falls inside the test windows.
  - The live benchmark figures come from 2026-10-06..11-18. That window spans the rule changes listed in
    research/ultimate_1119/top10/BENCHMARK.md §1: refire option B 10-14, cost filter 0.15R 10-30, LR8 cost model
    11-12, half-size Testing A-F lots 11-17, and others.
- **Known biases (inherited from bench10):**
  - the lab universe is ~1,200 names (survivorship);
  - T2 uses only 469 symbols;
  - there is no earnings blackout, and no spread or quote checks;
  - ETB uses today's flags;
  - 1-minute bars cannot order the two OCO legs inside one bar (handled by "nearer the open").
