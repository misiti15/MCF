Educational only — not financial advice

# BEG-08 Stretched-from-VWAP snap-back (long and short): results

*Research only. No setup, exit, config, account or ledger change.*
- **Configurations tried: 4.** That is the base plus 3 pre-registered one-part tweaks. The random controls fit nothing.
- The locked block 2024-11-01..2025-02-28 was never read. The bench10 `hist_bars` filter blocks it, and asserts check it.
  FIT-only runs never load CHECK days.
- CHECK was scored once for the base and once for the FIT pick (`stop125`). The other two tweaks were never scored on
  CHECK or T2.
- R is after LR8 costs, plus 1.2 bp borrow on shorts.
- Booking follows the testing-arena rules (bench10 TESTING_RULES):
  - cap 100;
  - at most 3 lots per symbol;
  - price at least $5;
  - shorts only when easy to borrow (E90);
  - the 0.15R stop-cost filter.
- Rule-change context: the backtest applies one fixed rule set to every session, so no live rule change from
  `research/ledger.jsonl` falls inside these figures. The top-10 benchmark medians are on the same basis.

## Verdict
- **Base: FAIL.** It is also **REALLY BAD** under the binding top10/PLAN.md rule: avg R is below −0.03 on all three of
  T1 fit (−0.076), T1 check (−0.059) and T2 (−0.094).
  - Five of the seven Tier A legs miss.
  - T1 combined avg R is −0.066 against a threshold of −0.038. That gap is 0.027R, so it is not NEAR.
  - Avg R without the best day is −0.104 against −0.067.
- **Tweak `stop125`** (stop distance ×1.25, the best of 3 on FIT): **FAIL**, but not REALLY BAD.
  - T1 combined clears its avg-R leg exactly: −0.0383 against −0.0383.
  - CHECK is −0.057 against −0.046 (gap 0.011). CHECK R per session is −0.542 against −0.522 (gap 0.0202).
  - T2 is −0.134 against −0.105. That gap is 0.029R, and T2 is worse than the base there (t −3.4).
  - The FIT gain was large: −0.076 became −0.009. Most of it did not carry over. CHECK went from −0.059 to −0.057, and
    T2 got worse, from −0.094 to −0.134.
- **No edge after costs in any window.** Gross avg R is about zero: +0.004 FIT, +0.020 CHECK and +0.002 T2 for the base.
  Costs on stops that average about 0.2 ATR take roughly 0.08R per trade.
- **The trigger does matter, but only as a timing device.**
  - Against random entries on the same symbol-days, with the same stop distance and the VWAP target, it is about
    +0.32R better. The `same` control averages −0.38 to −0.40.
  - That control is harsh, because a tight structural stop placed at a random time is mostly noise.
  - Against random fade-to-VWAP entries on every universe day (`univ`, median stop size), the setup is no better:
    −0.059 against −0.068 on CHECK, and −0.076 against −0.068 on FIT.
- **The FIT record is one day.** On 2025-04-09, the tariff-pause rally from about 13:18, the setup booked **368 shorts
  for −238.6R** at the 100-lot cap. Without the 5 worst FIT days the rest averages +0.167. This is the failure mode of a
  per-name reversal setup on market-wide trend days: hundreds of names stretch together and keep going.

## Per test (testing-arena book)
| variant | test | trades | /session | win | avg R | gross | avg R w/o best day | best-day share | R/session | worst day | day-t | SPY up / flat / down |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | T1 fit (170) | 1570 | 9.24 | 0.348 | −0.076 | +0.004 | −0.180 | n/a (total<0) | −0.697 | −238.6 | −0.44 | −0.386 / +0.071 / +0.165 |
| base | T1 check (276) | 2424 | 8.78 | 0.375 | −0.059 | +0.020 | −0.073 | n/a | −0.522 | −67.5 | −1.20 | −0.101 / +0.117 / −0.150 |
| base | T1 combined (446) | 3994 | 8.96 | 0.364 | −0.066 | +0.014 | −0.104 | n/a | −0.589 | −238.6 | −0.89 | −0.244 / +0.100 / −0.045 |
| base | T2 2023-24 (427, ref) | 683 | 1.60 | 0.394 | −0.094 | +0.002 | −0.103 | n/a | −0.150 | −26.7 | −1.66 | −0.122 / +0.043 / −0.171 |
| stop125 | T1 fit | 1664 | 9.79 | 0.403 | −0.009 | +0.063 | −0.097 | n/a | −0.085 | −153.9 | −0.07 | −0.227 / +0.037 / +0.168 |
| stop125 | T1 check | 2615 | 9.48 | 0.417 | −0.057 | +0.015 | −0.069 | n/a | −0.542 | −78.8 | −1.15 | −0.081 / +0.100 / −0.146 |
| stop125 | T1 combined | 4279 | 9.59 | 0.412 | −0.038 | +0.033 | −0.072 | n/a | −0.368 | −153.9 | −0.66 | −0.149 / +0.076 / −0.039 |
| stop125 | T2 (ref) | 822 | 1.93 | 0.409 | −0.134 | −0.046 | −0.140 | n/a | −0.258 | −17.5 | −3.38 | −0.159 / −0.067 / −0.160 |
| fresh3 | T1 fit | 806 | 4.74 | 0.344 | −0.090 | −0.013 | −0.257 | n/a | −0.425 | −215.1 | −0.31 | — |
| tgthalf | T1 fit | 1587 | 9.34 | 0.367 | −0.144 | −0.069 | −0.213 | n/a | −1.344 | −260.2 | −0.98 | — |

Every total is negative, so the best-day share is not defined. The `1 day` question is answered by the avg R without
the best day, which is worse than avg R everywhere. On FIT the opposite tail matters more: one day is −238.6R.

## Against the top-10 benchmark (medians; Tier A thresholds from top10/PLAN.md)
| leg | threshold | top-10 median | base | stop125 |
|---|---|---|---|---|
| T1 combined avg R | ≥ −0.0383 | −0.0283 | −0.0657 ✗ | −0.0383 ✓ |
| T1 check avg R | ≥ −0.0464 | −0.0364 | −0.0594 ✗ (0.013) | −0.0572 ✗ (0.011) |
| T1 combined avg R w/o best day | ≥ −0.0674 | −0.0474 | −0.1041 ✗ | −0.0718 ✗ (0.004) |
| T1 check avg R w/o best day | ≥ −0.0781 | −0.0581 | −0.0728 ✓ | −0.0690 ✓ |
| T1 combined R/session | ≥ −0.4862 | −0.4862 | −0.5886 ✗ | −0.3678 ✓ |
| T1 check R/session | ≥ −0.5218 | −0.5218 | −0.5219 ✗ (0.0001) | −0.5420 ✗ (0.020) |
| T2 avg R | ≥ −0.1048 | −0.0848 | −0.0940 ✓ | −0.1341 ✗ (0.029) |
| **tier** | | | **FAIL (REALLY BAD)** | **FAIL** |

The top-10 medians are themselves negative. "Meets" would only mean "backtests no worse than the setups winning live".
It would not mean profitable.

## FIT diagnosis and the tweaks (pre-registered in PLAN.md before any tweak was scored)
- **Exits.** 913 stops cost −1,010R and 124 VWAP targets made +346R; only 8% of trades reached VWAP. The 533 45-min time
  exits made +545R (+1.02 each). The snap-back does start, but rarely reaches VWAP within 45 min. Meanwhile the
  structural stop (about 0.2 ATR, at the extreme of a still-running move) is hit on 58% of trades.
- **The 30 worst losers** are all full stops (−1.2 to −2.6R with gap-through). Thirteen of them are 2025-04-09 shorts.
- **Rejected as tweaks:**
  - a SPY-tape filter, which points the wrong way: trades in the SPY-stretch direction scored −0.21 against +0.05;
  - a SPY RSI5 < 70 filter, which was worse than base;
  - a 13:00-14:30 window cut, because that bucket is the 04-09 day itself.
- **The three tweaks, one part each:**
  - `fresh3` (entry timing: the setup run must have started ≤ 3 bars before the trigger): FIT −0.090, w/o best day
    −0.257. It halved the trades and did not avoid 04-09.
  - `tgthalf` (target halfway to VWAP): FIT −0.144. Banking early cut the time-exit winners more than it saved.
  - `stop125` (stop ×1.25): FIT −0.009. **Picked.** It gave fewer stop-outs (win rate 40%) and a smaller 04-09 loss
    (−154R). It did not hold on CHECK or T2.

## Controls (fit nothing)
| control | T1 fit avg R (n) | T1 check avg R (n) |
|---|---|---|
| setup (base) | −0.076 (1570) | −0.059 (2424) |
| `same` seed 1 / 2: booked symbol-days and sides, random bar, same $ stop, VWAP target, 45-min stop | −0.385 / −0.378 | −0.379 / −0.404 |
| `univ` seed 1: every universe day, random bar, fade vs VWAP, median stop/ATR, VWAP target | −0.068 (77,482) | −0.068 (156,235) |

(The planned second `univ` seed was not run to save time and disk. With 77k-156k trades per run, one seed is already
tight.)

## Reading it (honest, costs in, looking for what can be salvaged)
- As written, the beginner rule is a cost-dominated near-zero-gross reversal. It also carries a structural tail risk:
  on market-wide trend days the 100-lot testing book fills with same-side fades.
- **What might be salvaged:** the 45-min time exit is where the money is (+1.0R per time exit), not the VWAP target. A
  wider stop helps on every T1 window. A version with a stop of about 0.35-0.5 ATR, the time exit as the main exit and a
  market-wide clustering guard might be worth a backlog idea.
  - The guard would need to be targeted at the failure mode: for example, skip when the stretch is market-wide (many
    names stretched the same way at once). Such a guard was not tested here because it is not one part of the written
    spec.
  - Per RESEARCH_RULES it would go to `research/backlog.jsonl`, not ship. T2's −0.13 on `stop125` is a warning that
    the wider stop alone does not fix it.
- It overlaps in theme with MCF's existing `vwap_reversion`. It was written independently and was not compared to it.

## Files
- `beg08.py`: the module.
  - It holds the live `Strategy` class `Beg08VwapStretchSnapback`. RSI5 is seeded from `ctx.prior5`. The class sends a
    market signal with the structural stop, a VWAP target and exit_by at fill + 45 min.
  - It also holds the pure functions `rsi5_on_1min`, `active`, `decide`, `walk` and `day_trades`, which the backtest
    uses.
  - The plainest readings of the spec are marked [R] in its docstring.
- `smoke_test.py`: passes (`OK`).
  - It covers both sides, the RSI agreement between the live and backtest forms, the stop, the target, the 1R skip, the
    window, ETB, the rank filter, the 45-min time stop and gap-through stops.
- `PLAN.md`: the pre-registration, including the tweaks.
- `run.py`: the engine, using bench10 costs, book and stats.
- `diag.py`: the FIT-only diagnosis.
- `summarize.py`: the verdict.
- `variants.json`: the three tweaks.
- `results.json`: all figures.
- Booked trade lists are in the session scratchpad `beg08w/` (32 MB) and can be regenerated with
  `python run.py WORK score <variant> fit|check|t2`.

### Plainest readings (noted)
- **RSI5:** Wilder RSI(14) on 5-minute RTH closes, continuous from the prior session. The value at a 1-minute bar is the
  last completed 5-minute bar.
- **Setup and stop:** the setup must be active on the bar before the trigger. "Since the setup" means from the start
  of the current contiguous setup run.
- **Window and target:** decision bars 10:00-14:29, filled at the next open. The target is VWAP at the decision bar.
  The 1R test uses the decision close.
- **Skips and re-entry:** a skipped trigger does not end the day. Re-entry is allowed after an exit, with one open
  position per symbol.
- **Universe filters:** price and ADV are measured at the prior close. rank_rvol20 comes from the BEG-02 day table.
