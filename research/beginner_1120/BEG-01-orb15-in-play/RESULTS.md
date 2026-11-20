Educational only — not financial advice

# BEG-01 ORB-15 on stocks in play: results (beginner experiment 2026-11-20)

This is research only. No setup, exit, config, account or ledger change was made.

- **Configurations tried:** 4 (the base plus 3 pre-registered one-part tweaks).
- **CHECK scoring:** CHECK was scored once for the base and once for the tweak picked on FIT.
- **Locked block:** 2024-11-01..2025-02-28 was never read.
- **Plan:** `PLAN.md` was written before any scoring. Addendum 1 (the tweaks) was written after the base FIT diagnosis and before any tweak was scored.
- **Code:** `BEG-01.py` is the module with the live `Strategy` interface (a stop-entry `Signal`). `beg01.py` is the backtest, `diag.py` the FIT diagnosis and `smoke_test.py` the smoke test, which passes.
- **Figures:** the numbers are in `out/`.

## Verdict
| | T1 fit avg R | T1 check avg R | T1 combined avg R | w/o best day (comb / check) | R/session (comb / check) | T2 avg R | tier |
|---|---|---|---|---|---|---|---|
| **base** (as written) | −0.384 | −0.252 | −0.291 | −0.296 / −0.259 | −1.220 / −1.199 | −0.204 | **FAIL** |
| **TW-b stopOR** (fit pick) | +0.020 | −0.026 | −0.009 | −0.011 / −0.029 | −0.103 / −0.293 | −0.029 | **MEETS** |
| top-10 median (standard) | −0.010 | −0.036 | −0.028 | −0.047 / −0.058 | −0.486 / −0.522 | −0.085 | |
| MEETS threshold | | ≥ −0.0464 | ≥ −0.0383 | ≥ −0.0674 / −0.0781 | ≥ −0.4862 / −0.5218 | ≥ −0.1048 | |

**Read with care.** The top-10 standard is negative: every median loses money after costs in this engine. "MEETS" means "backtests no worse than the setups that are winning live". It does not mean profitable.

The tweaked setup is still slightly negative after costs on CHECK (−0.026, day-clustered t −1.89) and on T2 (−0.029). It is barely better than random entries on the same symbol-days and sides: −0.032 on CHECK and −0.031 on T2. On FIT it is +0.020 against −0.032 for random entries. Most of what the tweak gains comes from holding an in-play stock with a wide stop. Little comes from the breakout trigger itself.

## Method (normal way)
- **Signals:** the module's own helpers, applied to per symbol-day statistics built from 1-minute bars.
  - T1 uses `data/cache_hist`, 1,226 symbols, with the lab frames' point-in-time `atr_d` / `adv20`.
  - T2 uses `data/cache_fresh`, 469 symbols, as reference only.
- **Entries and exits:** stop-entry semantics as in `mcf.backtest.engine`. A trigger that is already through fills at the bar open. The walk is on 1-minute bars:
  - stop first (on the entry bar too);
  - a target fills only when traded through by ≥ 1c;
  - breakeven from the next bar;
  - flat at 15:55.
- **Costs and book:** the bench10 `add_r` costs (LR8 + 1.2 bp borrow on shorts). The bench10 `book` under the testing-arena rules: cap 100, ≤ 3 lots per symbol, ETB shorts, stop-cost filter 0.15R.
- **Sessions:** FIT 170, CHECK 276, T2 427.
- **Random entries:** same symbol-day and side, a random fill minute in the order window at that bar's open, same $ risk and same exits, costs and book; 5 seeds.

## Base (the rule exactly as written)
| test | trades | /session | win | avg R (gross) | w/o best day | best-day share | R/session | worst day | day-t | random entries |
|---|---|---|---|---|---|---|---|---|---|---|
| FIT | 556 | 3.27 | 0.31 | −0.384 (−0.270) | −0.392 | n/a (total < 0) | −1.254 | −6.8 | −9.61 | −0.101 |
| CHECK | 1315 | 4.76 | 0.36 | −0.252 (−0.146) | −0.259 | n/a | −1.199 | −8.8 | −7.84 | −0.126 |
| combined | 1871 | 4.20 | 0.34 | −0.291 | −0.296 | n/a | −1.220 | −8.8 | −11.28 | |
| T2 | 1123 | 2.63 | 0.42 | −0.204 (−0.099) | −0.210 | n/a | −0.537 | −6.3 | −6.55 | −0.115 |

- **Every SPY day type loses.** FIT: up −0.38, flat −0.32, down −0.44.
- **Without the 0.15R stop-cost filter the base is worse:** FIT −0.548 on 1,701 trades. The filter removes most of the base's trades because its stops are only a few cents wide.
- **Median hold:** 2 minutes.

### Diagnosis of the worst losers (FIT only; `out/diag_fit_base.txt`)
- **The stop is the failing part.**
  - All 55 worst-decile trades are full stops.
  - 78% of all stops come within 5 minutes, and 36% on the entry bar itself.
  - 67% of stopped trades later reach the 2R target the same day.
  - The 0.10 × ATR stop (median 0.31% of price) sits inside the breakout bar's noise, and costs add about 0.14R to every stop.
- **Entry timing is secondary.** Fills after 10:15 average about −0.66R, against −0.34R for fills at 09:50-09:59.
- **Filters show no clear slope** across rank, RVOL or ATR.

## Tweaks (pre-registered, one part each, FIT only)
| tweak | part | FIT trades | FIT avg R | w/o best day | R/session | day-t | random |
|---|---|---|---|---|---|---|---|
| TW-a stop25: stop 0.25 × ATR (OR15 cap kept) | stop | 1407 | −0.053 | −0.064 | −0.436 | −1.51 | −0.083 |
| **TW-b stopOR: stop at the far side of OR15** | stop | 1759 | **+0.020** | **+0.016** (share 0.23) | +0.206 | 0.99 | −0.032 |
| TW-c until1015: order works 09:50-10:14 only | window | 460 | −0.350 | −0.360 | −0.946 | −7.97 | −0.095 |

The pick is **TW-b stopOR**. Only TW-b was scored on CHECK and T2, once.

### TW-b stopOR on every test
| test | trades | /session | win | avg R (gross) | w/o best day | best-day share | R/session | worst day | day-t | SPY up / flat / down | random |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FIT | 1759 | 10.35 | 0.47 | +0.020 (+0.049) | +0.016 | 0.23 (2025-04-08) | +0.206 | −8.0 | 0.99 | +0.069 / +0.001 / −0.017 | −0.032 |
| CHECK | 3101 | 11.24 | 0.46 | −0.026 (+0.000) | −0.029 | n/a | −0.293 | −8.5 | −1.89 | +0.019 / −0.052 / −0.039 | −0.032 |
| combined | 4860 | 10.90 | 0.46 | −0.009 (+0.018) | −0.011 | n/a | −0.103 | −8.5 | −0.82 | +0.038 / −0.035 / −0.030 | |
| T2 | 4151 | 9.72 | 0.46 | −0.029 (+0.007) | −0.032 | n/a | −0.277 | −9.5 | −1.90 | +0.017 / −0.072 / −0.030 | −0.031 |

- **Exits (combined):** 76% at 15:55, 19% stop, 5% target. The 2R target is far away with an OR-wide stop.
- **Median hold:** about 354 minutes.
- **Long vs short (combined):** long −0.012, short −0.006. On T2 the shorts are weaker: −0.052.
- **Book occupancy:** about 11 trades per session, inside the 100-lot cap.
- **Gross vs net:** the gross edge is about zero (CHECK +0.000), so costs make the net result negative.

## Caveats (stated, not fixed)
- **Universe size.** The backtest universe is about 1,226 names, against about 4,200 live. So "rank_rvol20 ≤ 20" ranks inside a smaller universe, and the selected names differ from what live would pick.
- **Entry-bar stops are pessimistic.** On the entry bar the stop is checked against the bar's low/high (the engine rule). That hurts the base's tight stop most.
- **Early March 2025 is missing.** The first ~5 sessions after the locked block have no RVOL (the lookback cannot cross the lock gap). They contribute no trades.
- **Not modelled:** no earnings blackout and no spread or quote skips. ETB uses today's flags. Account-wide slot and buying-power limits are not modelled.
- **Rule-change context:** none applies. Every test applies one fixed rule set to every session.
- **Plainest readings of the spec** are listed in PLAN.md:
  - RVOL over 14 sessions;
  - price taken at the 09:49 close;
  - stop and target are fixed prices set from the trigger;
  - a trigger already through at 09:50 fills at the open.

## Next step (optimistic, honest)
The setup is not ready for a testing account on evidence alone. The tweak meets the top-10 backtest standard, but it is no better than random in-play entries. The useful lesson is that the paper's tight stop does not survive a 1-minute walk with LR8 costs, while an OR-wide stop on stocks in play is roughly cost-neutral.

A next test worth trying is a trigger-specific improvement measured against the random-entry baseline, for example a later re-test entry or a gross-edge filter. It would be added as a backlog idea (`research/backlog.jsonl`), not as a change shipped directly.
