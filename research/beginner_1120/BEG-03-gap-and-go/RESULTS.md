Educational only — not financial advice

# BEG-03 Gap-and-go continuation (long only): results

*Research only. No setup, exit, config, account or ledger change.*
- Configurations tried: **4** (the base plus 3 pre-registered one-part tweaks). The random controls fit nothing.
- The locked block 2024-11-01..2025-02-28 was never read (bench10 `hist_bars` filter plus asserts).
- CHECK was scored once for the base and once for the FIT pick.
- R is after LR8 costs. The setup is long only, so no borrow applies.
- Trades are booked under the testing-arena rules: cap 100, <= 3 lots per symbol, price >= $5, the 0.15R stop-cost
  filter.
- Rule-change context: the backtest applies one fixed rule set to every session, so no live rule change
  (research/ledger.jsonl) falls inside these figures. The benchmark medians compared against here are on the same
  basis.

**Verdict:**
- **Base: MEETS** the top-10 standard. Every Tier A leg holds. It is not REALLY BAD.
  - This means "backtests no worse than the setups now winning live". It does **not** mean profitable: T1 combined
    is −0.017R a trade, T2 is −0.084R.
  - The T1 CHECK record is a one-day record (`1 day` tag): best day +5.8R against a total of +3.3R (share 1.77).
- **Tweak `win1015`** (orders only until 10:14, picked on FIT): **FAIL**.
  - It improved FIT (−0.058 → −0.008) but fell apart on CHECK (−0.062) and T2 (−0.137).
  - The FIT timing pattern it relied on reversed out of sample.

## Files
- `beg03.py`: the module.
  - It has the live `Strategy` class `Beg03GapAndGo`, which arms a one-bar buy-stop for the next bar and is re-armed
    bar by bar.
  - It also has the pure functions `arm` / `find_entry` / `walk`, which the backtest uses.
  - The [R] notes in its docstring mark the plainest readings of the spec.
- `smoke_test.py`: passes.
  - It checks that the live class arms the same order as `find_entry`.
  - It checks that `walk` matches `mcf.backtest.engine.simulate`: same fill, same exit price and reason.
  - It also covers the filters, the stop band and the trail with a gap-through.
- `run.py`: the engine.
  - It reads the candidate symbol-days from the BEG-02 day table (the same RVOL20 definition, read only) and loads
    their 09:30-12:59 bars.
  - Costs, the book and `stats()` are imported unchanged from `research/ultimate_1119/top10/bench10.py`.
- `PLAN.md`: the pre-registration, covering the base, the control note and the tweaks. Each part was written before
  it was scored.
- `diag.py`: the FIT-only loser diagnosis.
- `variants.json`: the three tweaks.
- `summarize.py` writes `results.json`, which holds every figure below.
- Trade lists (~21 MB) are in the session scratchpad `beg03w/` and are not in the repo. They can be regenerated with
  `run.py build t1|t2` and `run.py score`.

## Implementation notes (plainest readings)
- **Universe.**
  - U0 = prior close >= $5 and ADV20 >= $20M. "Price $5-$200" is checked on the prior close.
  - Gap = 09:30 open / prior close − 1 >= 3%.
  - RVOL20 = the 09:30-09:49 volume / the mean of the prior 14 sessions (min 5) >= 3.0.
  - T1 has no RVOL for the first ~5 sessions of 2024-10 and of 2025-03, because the rolling mean never spans the
    locked gap. T2 uses the 469 cache_fresh names.
- **Trigger.**
  - A buy-stop at the R20 (09:30-09:49) high + $0.01 that can fill on the bars 09:50..10:59.
  - The order is armed for bar k only if the close of bar k−1 is above session VWAP. An unarmed bar cannot fill, and
    the order keeps working until 11:00.
  - A bar that opens above the trigger fills at its open.
- **Stop.**
  - max(R20 low, VWAP at the close of bar k−1) − $0.02.
  - A bar is not armed unless the stop distance is 0.4%-3% of the trigger price.
  - A stop touch on the entry bar fills at the stop (conservative, as `engine.simulate`).
- **Exits.**
  - Target = trigger + 2R.
  - Once the best price reaches +1R, measured from the real fill, the stop trails 1R behind the best price. It is
    updated for the next bar.
  - Time exit at the 12:00 open. One trade per symbol-day.
  - Stop first; a gap-through fills at the open. The target fills only when traded through by $0.01.

## Step 2: base scores (testing-arena book)
| test | trades | /session | win | avg R | gross | avg R w/o best day | best day (R) | best-day share | total R/session | worst day | t (day-clustered) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 FIT (170) | 321 | 1.89 | 45.8% | −0.058 | −0.005 | −0.074 | 2025-09-18 (+4.5) | n/a (total<0) | −0.110 | −5.8 | −1.01 |
| T1 CHECK (276) | 595 | 2.16 | 51.6% | **+0.006** | +0.058 | −0.004 | 2026-04-23 (+5.8) | **1.77, 1 day** | +0.012 | −7.8 | +0.12 |
| T1 combined (446) | 916 | 2.05 | 49.6% | **−0.017** | +0.036 | −0.024 | 2026-04-23 (+5.8) | n/a (total<0) | −0.035 | −7.8 | −0.46 |
| T2 2023-24, reference (427) | 296 | 0.69 | 45.3% | −0.084 | −0.027 | −0.098 | 2024-02-12 (+4.0) | n/a (total<0) | −0.059 | −4.3 | −1.44 |

- Costs take ~0.053R a trade (0.057 on T2). The gross edge is +0.036R on T1 combined, which is too small to survive
  costs.
- **The tape decides it.** On T1 combined: SPY-up days +0.042, flat +0.043, **SPY-down days −0.193**. CHECK shows the
  same split: up +0.095, down −0.183.
- Exit mix (T1 combined): 494 stop/trail exits, 303 12:00 time exits, 119 targets.
- The 0.15R stop-cost filter removes ~10% of raw trades (FIT 355 raw → 321 booked).

**Vs random entries.**

| control | T1 FIT | T1 CHECK | T1 combined | T2 |
|---|---|---|---|---|
| setup | −0.058 | +0.006 | −0.017 | −0.084 |
| `pre` (PLAN, 5 seeds): random bar 09:50-10:59, same days | +0.033..+0.059 | +0.117..+0.186 | +0.097..+0.137 | +0.122..+0.172 |
| `after` (3 seeds): random bar at/after the setup's fill | −0.107..−0.164 | +0.017..+0.055 | −0.030..−0.006 | +0.006..+0.031 |
| `univ` (3 seeds): every universe day, random bar, setup's stop rule | −0.054..+0.016 | −0.057..+0.041 | −0.047..+0.032 | −0.139..−0.031 |

- **The pre-registered control is biased upward.** It is drawn only on days where the buy-stop later fills, so a random
  bar before the fill "knows" a breakout is coming. Those draws average +0.63R. This was found after the base was
  scored and written into PLAN.md before any tweak.
- On the two fairer controls, added unfitted, the setup is about level with random entries on T1 (inside the
  `after` / `univ` ranges on combined). It is worse than random on T2 (−0.084 vs `after` +0.006..+0.031).
- **The R20 breakout trigger does not show a timing edge.** What it shows is that gap/RVOL days are roughly flat
  after costs, and positive on SPY-up days.

## Step 3: tweaks (FIT diagnosis → 3 pre-registered one-part tweaks → pick on FIT → scored once)
**Diagnosis (FIT only, `diag.py`).**
- Full initial-stop losers: 114 trades, −122R. They were mostly held 15-60 minutes; only 5 were stopped within
  5 minutes.
- Targets: 43 trades, +67R. Time exits: 105, +19R. Trail stops: 59, +0.29 each.
- **Entry timing was the clearest FIT split:** fills 09:50-10:14 −0.01 (238 trades) vs 10:15-10:59 −0.20 (83 trades,
  −16.9R).
- Gaps of 3-5%: −0.124. Wide stops of 1.8-3%: −0.148.
- The worst losers were wide-stop, high-gap names (APLD, SOUN, ECHO, OSCR) and late fills.

| tweak (part) | FIT booked (raw) | FIT avg R | gross | w/o best day | total R/session | t |
|---|---|---|---|---|---|---|
| base | 321 (355) | −0.058 | −0.005 | −0.074 | −0.110 | −1.01 |
| **`win1015`: order valid until 10:14 (window)** | 238 (257) | **−0.008** | +0.045 | −0.025 | −0.011 | −0.11 |
| `gap5`: gap >= 5% (filter) | 213 (229) | −0.025 | +0.024 | −0.045 | −0.032 | −0.34 |
| `stopmax2`: stop band max 2% (stop) | 284 (317) | −0.062 | −0.010 | −0.079 | −0.103 | −0.99 |

**Pick on FIT: `win1015`. Scored once:**

| test | trades | avg R | gross | w/o best day | best day (R) | total R/session | worst day | t |
|---|---|---|---|---|---|---|---|---|
| T1 FIT | 238 | −0.008 | +0.045 | −0.025 | +4.0 | −0.011 | −4.9 | −0.11 |
| T1 CHECK | 441 | **−0.062** | −0.007 | −0.074 | 2026-04-15 (+5.2) | −0.098 | −7.6 | −1.13 |
| T1 combined | 679 | **−0.043** | +0.012 | −0.051 | +5.2 | −0.065 | −7.6 | −0.99 |
| T2 (reference) | 226 | **−0.137** | −0.078 | −0.151 | +2.8 | −0.072 | −3.3 | −2.05 |

- **The FIT timing split reversed out of sample.** In the base, late fills (10:15-10:59) were −0.203 on FIT but
  **+0.198 on CHECK** (154 trades) and +0.084 on T2 (70 trades). Early fills were −0.008 / −0.062 / −0.136.
  - Cutting the late window therefore removed the best part of the setup out of sample.
  - This is a textbook FIT artefact, reported as found.
- Against the `after` random control, the tweak sits at about the control level: T1 combined −0.043 vs −0.081..−0.050.

## Step 4: vs the top-10 benchmark (research/ultimate_1119/top10/PLAN.md; standard = home-account medians)
| leg | threshold | median | base | tweak `win1015` |
|---|---|---|---|---|
| T1 combined avg R | >= −0.0383 | −0.0283 | **−0.0169 ✓** | −0.0428 ✗ (−0.0045) |
| T1 check avg R | >= −0.0464 | −0.0364 | **+0.0055 ✓** | −0.0616 ✗ (−0.0152) |
| T1 combined w/o best day | >= −0.0674 | −0.0474 | −0.0235 ✓ | −0.0508 ✓ |
| T1 check w/o best day | >= −0.0781 | −0.0581 | −0.0043 ✓ | −0.0743 ✓ |
| T1 combined R/session | >= −0.4862 | −0.4862 | −0.035 ✓ | −0.065 ✓ |
| T1 check R/session | >= −0.5218 | −0.5218 | +0.012 ✓ | −0.098 ✓ |
| T2 avg R | >= −0.1048 | −0.0848 | −0.0843 ✓ | −0.1365 ✗ (−0.0317) |
| >= 20 trades check / T2 | | | 595 / 296 ✓ | 441 / 226 ✓ |
| **Tier** | | | **MEETS** | **FAIL** (T2 leg misses by > 0.02R) |
| REALLY BAD | | | no | no |

- The base beats the benchmark median avg R on T1 combined (+0.011R), T1 check (+0.042R) and avg R w/o best day.
  It is level on T2 (−0.084 vs −0.085).
- Its R/session is far less negative than the median, but only because it trades ~2 a session against the median's ~9.
- Overlap: the name overlaps the existing MCF gap_and_go setup. Its rules were written independently. The 70%
  duplicate test against live setups was not run here; that belongs to the Report stage.

## Reading it (honest, costs in, looking for what works)
- A plain beginner gap-and-go is **about break-even before costs and slightly negative after costs** over two years.
  It is about as good as the setups now winning live, in the same engine.
- **The one-day caveat matters:** the positive CHECK figure is carried by 2026-04-23.
- **What can be salvaged:**
  - The SPY-down-day leg is the failure in every test: −0.19 on T1 combined, −0.18 on CHECK.
  - A tape gate (no new longs when SPY is down from its open at the trigger) is the natural next one-part test.
  - This was observed, **not tested**. It would be a new configuration (N 4 → 5) and belongs in `research/backlog.jsonl`.
- The pre-registered random control is unusable for stop-entry setups. Future stop-entry studies should pre-register
  the `after` / `univ` style controls.
