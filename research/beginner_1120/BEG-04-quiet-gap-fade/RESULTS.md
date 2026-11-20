Educational only — not financial advice

# BEG-04 Quiet gap fade toward the prior close (long and short): results

*Research only. No setup, exit, config, account or ledger change.*
- Configurations tried: **4**. That is the base plus 3 pre-registered one-part tweaks. The random controls fit nothing.
- The locked block 2024-11-01..2025-02-28 was never read. The bench10 `hist_bars` filter blocks it, and asserts check it.
- CHECK was scored once for the base and once for the FIT pick (`gap25`).
- R is after LR8 costs, plus 1.2 bp borrow on shorts.
- Booking follows the testing-arena rules:
  - cap 100;
  - at most 3 lots per symbol;
  - price at least $5;
  - shorts only when easy to borrow (E90);
  - the 0.15R stop-cost filter.
- Rule-change context: the backtest applies one fixed rule set to every session, so no live rule change from
  `research/ledger.jsonl` falls inside these figures. The benchmark medians are on the same basis.

**Verdict:**
- **Base: FAIL** against the top-10 standard. It is not REALLY BAD.
  - Five of the seven Tier A legs hold, including T1 combined avg R +0.003 and T1 check −0.040.
  - Two CHECK legs miss. Avg R without the best day is −0.085 against a threshold of −0.078. That miss is within 0.02R.
  - Total R per session is −0.654 against −0.522. That miss is 0.13R, so it is not NEAR. It comes from volume
    (16 trades a session) as much as from a weak edge.
- **Tweak `gap25`** (|gap| ≥ 2.5%, picked on FIT): **NEAR**.
  - Every leg holds except CHECK avg R without the best day: −0.096 against −0.078, short by 0.018R.
  - It is **not** an improvement out of sample. CHECK avg R went from −0.040 to −0.030, but the figure without the best
    day went from −0.085 to −0.096. On T2 the tweak is −0.062 against the base's −0.050.
  - The FIT gap pattern that chose it (2.5-6% gaps +0.249 vs 1.5-2.5% −0.073) reversed on CHECK. In the base's CHECK
    trades, 2.5-6% gaps scored −0.050 and 1.5-2.5% scored −0.030.
- **Both records are one-day or one-episode records.**
  - FIT is the April 2025 tariff crash. On the base, 2025-04-08 alone is 100% of FIT total R, and 04-07 and 04-30 add
    +267R more.
  - On T1 combined the base's best-day share is 11.7 and the tweak's is 1.01, so both carry the `1 day` tag.
- **The trigger adds no edge in this test.**
  - A random fade entry on every universe day (`univ`, no trigger and no 1.2R test) averages −0.040 on T1 combined
    and −0.049 on CHECK. The setup scores +0.003 and −0.040.
  - The `same`-days control does far better than the setup (+0.13 on every test). That control is biased: those days
    are chosen because price later broke R20 toward the fill, so a random bar placed before the trigger "knows" the
    fade is coming.
  - Read together, the controls point to the day selection (which days fade) as the source of whatever edge exists.
    The entry trigger is not adding it. The trigger looks late: it enters after much of the fade is done.

## Files
- `beg04.py`: the module.
  - It holds the live `Strategy` class `Beg04QuietGapFade`, which sends a market signal on the first trigger, with the
    structural stop, a prev_close target and exit_by 15:55.
  - It also holds the pure functions `universe_ok` / `decide` / `find_entry` / `walk`, which the backtest uses.
  - The plainest readings of the spec are marked [R] in its docstring.
- `smoke_test.py`: passes (`OK`). It covers the gap-up short and the gap-down long, the volume, ADV and rank filters,
  the 0.35 ATR cap, the 1.2R skip, target and stop exits, the 15:55 exit, and that the live class emits the same order
  on the trigger bar only.
- `run.py`: the engine. It reads 1-minute bars straight from the caches on every run, so no copy of the bars is
  stored. Costs, `book()`, `stats()`, `half()` and the SPY day types are imported unchanged from
  `research/ultimate_1119/top10/bench10.py`. Candidate days and RVOL20 / rank_rvol20 come from the BEG-02 day table
  (read only).
- `PLAN.md`: the pre-registration, covering the base, the controls and the tweaks. Each part was written before it was
  scored.
- `diag.py`: the FIT-only loser diagnosis.
- `variants.json`: the three tweaks.
- `summarize.py` writes `results.json`, which holds every figure below.
- Booked trade lists (~10 MB) are in the session scratchpad `beg04w/` and are not in the repo. To regenerate them, run
  `python run.py WORK score base all` and the matching commands for the tweak and controls.

## Implementation notes (plainest readings)
- **Universe.**
  - Prior close ≥ $15 and point-in-time ADV20 ≥ $50M.
  - 1.5% ≤ |gap| ≤ 6%, where gap = 09:30 open / prev_close − 1.
  - RVOL20 < 1.5 **and** rank_rvol20 > 100. RVOL20 is the 09:30-09:49 volume over the mean of the prior 14 sessions.
    The rank is taken within the day's U0 universe: about 1,170 names on T1 and about 430 on T2.
  - A day without RVOL20 is not traded. That covers the first ~5 sessions of 2024-10 and of 2025-03, because the
    rolling mean never spans the locked gap.
  - Inverse and volatility funds are never shorted.
- **Trigger.**
  - Decision bars run 09:50..11:59, with the fill at the next bar's open. That follows the DESIGN global convention, so
    fills land in 09:51..12:00.
  - After a gap up: short when the close is below the R20 low and below session VWAP. After a gap down: long when the
    close is above the R20 high and above VWAP.
  - Only the first trigger of a symbol-day counts. If it fails the 1.2R test, the day is skipped with no second look.
- **Stop.**
  - The other side of R20, ± $0.02.
  - Capped at 0.35 × daily ATR(14), measured from the decision-bar close.
  - Booked R uses the real fill against that fixed stop.
- **Exit.**
  - Target = prev_close. The day is skipped if the target is less than 1.2R from the decision close.
  - Stop first. The target fills only when traded through by $0.01. Otherwise flat at the 15:55 open.

## Step 2: base scores (testing-arena book)
| test | trades | /session | win | avg R | gross | avg R w/o best day | best day | best-day share | total R/session | worst day | t (day-clustered) | SPY up / flat / down |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 FIT (170) | 1,860 | 10.9 | 49.6% | +0.106 | +0.166 | **−0.0005** | 2025-04-08 | **1.00, 1 day** | +1.162 | −67.1 | +0.68 | +0.215 / −0.328 / +0.241 |
| T1 CHECK (276) | 4,465 | 16.2 | 42.5% | **−0.040** | +0.021 | −0.085 | 2026-04-02 | n/a (total<0) | −0.654 | −53.1 | −0.53 | +0.190 / −0.211 / −0.043 |
| T1 combined (446) | 6,325 | 14.2 | 44.6% | **+0.003** | +0.064 | −0.029 | 2025-04-08 | **11.7, 1 day** | +0.038 | −67.1 | +0.04 | +0.199 / −0.231 / +0.071 |
| T2 2023-24, reference (427) | 1,284 | 3.0 | 42.4% | −0.050 | +0.017 | −0.094 | 2024-08-07 | n/a (total<0) | −0.152 | −31.1 | −0.56 | −0.108 / −0.300 / +0.509 |

- Costs take ~0.06-0.07R a trade. The gross edge on CHECK is +0.021R, which costs remove.
- **By side.**
  - Longs after gap downs: FIT +0.174, CHECK +0.008, T2 −0.081.
  - Shorts after gap ups: FIT +0.020, CHECK −0.093, T2 −0.015.
  - Neither side is consistent.
- **By exit, the same on every test.**
  - Full stops: about −1.08R each, roughly 40% of trades.
  - Targets: +1.65..+1.77R.
  - 15:55 time exits: +0.25..+0.34R.
- **By regime.**
  - It does well in volatile, mean-reverting episodes: 2025-04 (tariff crash), 2025-11 (+0.27), 2026-03/04 (+0.11 /
    +0.43).
  - It bleeds in calm trending months: 2026-05..11 run −0.10..−0.41 every month.
  - It is worst on SPY-flat days on every test (−0.21..−0.33).

### Random controls (mean of 3 seeds, same book; fit nothing)
| control | T1 FIT | T1 CHECK | T1 combined | T2 |
|---|---|---|---|---|
| setup (base) | +0.106 | −0.040 | +0.003 | −0.050 |
| `univ`: every universe day, random bar 09:50-11:59, fade side, setup stop rule, no trigger or 1.2R test | −0.010 (n 6,975) | −0.049 (n 22,048) | −0.040 | −0.040 |
| `same`: setup's days, random bar, same $ stop (biased upward, see verdict) | +0.168 | +0.117 | +0.132 | +0.121 |

## Step 3: tweaks (diagnosis on FIT only, pre-registered in PLAN.md before scoring)
FIT diagnosis:
- **Exits.** The 709 full stops cost −768R (median hold 70 min; only 33 within 10 min). Targets made +713R and 15:55
  exits +253R.
- **Worst losers.** All 25 are full stops. 19 of them are shorts after gap ups, and many had a tight R20 stop
  (0.12-0.25 ATR).
- **By bucket, without the best day:**
  - R20 stop ≤ 0.25 ATR: −0.167;
  - decisions 11:15-11:59: −0.223;
  - |gap| 1.5-2.5%: −0.078.

| tweak (one part) | FIT trades | FIT avg R | FIT w/o best day | best-day share | FIT R/session | FIT t |
|---|---|---|---|---|---|---|
| base | 1,860 | +0.106 | −0.0005 | 1.00 | +1.162 | +0.68 |
| `stopatr`: stop = 0.35 ATR always (stop) | 1,677 | +0.140 | +0.027 | 0.82 | +1.376 | +0.89 |
| `win1114`: decision bars until 11:14 (window) | 1,632 | +0.151 | +0.033 | 0.80 | +1.449 | +0.89 |
| **`gap25`: abs(gap) ≥ 2.5% (filter), PICK** | 1,058 | **+0.256** | +0.074 | 0.74 | +1.591 | +1.18 |

### The pick on CHECK (once) and T2
| test | trades | /session | win | avg R | gross | avg R w/o best day | best-day share | total R/session | worst day | t | SPY up / flat / down |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 FIT | 1,058 | 6.2 | 55.0% | +0.256 | +0.307 | +0.074 | 0.74 (1 day) | +1.591 | −27.7 | +1.18 | +0.393 / −0.406 / +0.441 |
| T1 CHECK | 2,462 | 8.9 | 43.0% | **−0.030** | +0.023 | **−0.096** | n/a (total<0) | −0.263 | −34.2 | −0.32 | +0.243 / −0.230 / −0.052 |
| T1 combined | 3,520 | 7.9 | | **+0.056** | | −0.001 | **1.01, 1 day** | +0.444 | | +0.59 | |
| T2 (reference) | 455 | 1.1 | 44.0% | −0.062 | −0.005 | −0.119 | n/a (total<0) | −0.066 | −22.6 | −0.58 | −0.096 / −0.315 / +0.547 |

**Effect on each family (Remedies rule).** Avg R, base → tweak:

| side | FIT | CHECK | T2 |
|---|---|---|---|
| shorts | +0.020 → +0.300 | −0.093 → −0.081 | −0.015 → −0.026 |
| longs | +0.174 → +0.214 | +0.008 → +0.012 | −0.081 → −0.087 |

On CHECK both sides improve slightly. On T2 both get slightly worse. The large FIT gain did not carry over.

## Step 4: against the top-10 benchmark (testing-arena book; thresholds from top10/PLAN.md)
| leg | threshold | base | margin | `gap25` | margin |
|---|---|---|---|---|---|
| T1 combined avg R | ≥ −0.0383 | +0.0027 | +0.041 ✓ | +0.0562 | +0.095 ✓ |
| T1 check avg R | ≥ −0.0464 | −0.0404 | +0.006 ✓ | −0.0295 | +0.017 ✓ |
| T1 combined w/o best day | ≥ −0.0674 | −0.0292 | +0.038 ✓ | −0.0007 | +0.067 ✓ |
| T1 check w/o best day | ≥ −0.0781 | −0.0849 | **−0.007 ✗** | −0.0960 | **−0.018 ✗** |
| T1 combined R/session | ≥ −0.4862 | +0.038 | +0.524 ✓ | +0.444 | +0.930 ✓ |
| T1 check R/session | ≥ −0.5218 | −0.654 | **−0.133 ✗** | −0.263 | +0.259 ✓ |
| T2 avg R | ≥ −0.1048 | −0.0504 | +0.054 ✓ | −0.0623 | +0.043 ✓ |
| ≥ 20 trades check / T2 | | 4,465 / 1,284 ✓ | | 2,462 / 455 ✓ | |
| **tier** | | **FAIL** (R/session leg misses by 0.13) | | **NEAR** (one leg, −0.018R) | |
| REALLY BAD | | no | | no | |

Benchmark medians (home book): T1 combined −0.028, check −0.036, T2 −0.085. Against those, both versions backtest
roughly as well as the setups now winning live. That is **not** the same as profitable: CHECK is negative for both,
and T2 is negative for both.

## Reading it (optimistic, honest, costs in)
- **What works.**
  - Fading quiet, no-news gaps toward the prior close carries a small gross edge on every test (+0.02..+0.17R).
  - In volatile, mean-reverting tapes (2025-04, 2025-11, 2026-03/04) the edge is large and survives costs.
  - Longs after gap downs are the steadier side: FIT +0.17, CHECK +0.01.
- **What does not.**
  - Costs (~0.06R) eat the calm-market edge.
  - The R20-break trigger enters after much of the fade, and it does not beat random fade entries out of sample.
  - The gap-size filter chosen on FIT did not hold on CHECK.
- **Next step (backlog idea, not tested here).** The controls suggest the selection of days carries the edge and the
  trigger does not. A version worth testing would:
  - enter earlier on the same quiet-gap days, for example the first VWAP cross after 09:50 rather than an R20 break;
  - add a regime gate for volatile tapes, for example a VIX or SPY ATR percentile.

  Either change would need its own pre-registration and the locked holdout.
