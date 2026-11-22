Educational only — not financial advice.

# BDI-MH4 (2026-11-22): 2-year screen, crypto complex follows bitcoin + peer-group laggards

Owner said yes to BDI-MH4 on 2026-11-22. This is research only: no setup, exit, config or account changed.
Pre-registration: `PLAN.md`, written before any row was scored. Scripts: `build.py` (one pass over the 1-minute
caches) and `screen.py`. Outputs: `out.txt`, `fit_all.csv` (all 32 configs on FIT), and `picks.csv` / `picks.json`
(the FIT picks, scored once on CHECK and T2).

**Configs tried: 32** (16 crypto + 16 peer). Crypto lineage N = 16, so the bar is 2.355 (BAR90 2.12). Peer lineage
N = 32 (16 here + 16 in parked mh-1102), so the bar is 2.633 (BAR90 2.37). The locked block 2024-11-01..2025-02-28
was never read: it is filtered out at load and asserted on every load. Sessions: FIT 159, CHECK 276 (2025-10-01..
2026-11-04), T2 427. Costs: LR8 basis plus borrow. Book: Testing-arena rules (price >= $5, ETB shorts, cost filter
0.15R, cap 100), with adv20 >= $20M.

**How to read the benchmark:** the top-10 standard is negative (median T1 combined -0.028R). So "meets the standard"
means "backtests no worse than the setups that are winning live". It does not mean "profitable in backtest".

**Rule changes:** these are backtests under one fixed rule set. The live rule changes in `research/ledger.jsonl` inside
the window (sizing, stops, filters, timing, moves) do not enter these numbers.

## Headline
| idea | result | admission |
|---|---|---|
| Crypto follows BTC | **No edge out of sample.** The long FIT pick was +0.148R on FIT and -0.157R on CHECK. The short pick was -0.086 / -0.014. | No |
| Peer-group laggards | **Real selection information, but it loses after costs.** The long pick beats random entry at the 100th percentile on CHECK (+0.06R over random). In absolute terms it is -0.037R on CHECK and -0.048R on T2, because it carries the day's market direction. | No (misses Tier A on one leg) |

Neither idea meets the Testing admission bar, so there is **no DECISION line**.

## Idea 1: crypto complex follows bitcoin (`mh-1121-crypto-complex-follow`)
**Data limits, stated before scoring:**
- The inverse crypto ETPs (MSTZ, BTCZ, SBIT, BITI) are not in the bar cache. So "long-only via inverse ETPs on down
  days" could not be tested, and down days were tested as shorts.
- MSTU, MSTX, CONL and ETHU are not easy to borrow (0% ETB), so they never trade short.
- `cache_fresh` has no BTC proxy, so **T2 is not scorable**. Tier A cannot be reached.

**Trigger days:**
- |IBIT move| >= 0.5 ATR at 09:50: 94 up and 84 down days out of 435.
- At >= 0.75 ATR: 57 up and 45 down.

**FIT, all 16 configs:**
- **Longs** were positive in 7 of 8 configs (-0.02 to +0.22R). Every one leaned on SPY-up days (+0.17 to +1.26R) and
  lost on SPY-down days (-0.21 to -1.07R).
- **Shorts** were negative in 8 of 8 configs (-0.09 to -0.53R).

| FIT pick (best FIT t per side) | test | trades | avg R | w/o best | w/o top-2 | best-day share | t (cl) | null pct | day-type control |
|---|---|---|---|---|---|---|---|---|---|
| CX-L-k75-lag-t1s1 | FIT | 114 (16 sessions) | +0.148 | +0.045 | -0.017 | 0.74 (**1 day**) | 0.76 | 99.2 | +0.015 |
| | CHECK | 269 | **-0.157** | -0.201 | -0.233 | n/a (total < 0) | -1.49 | **3.0** | -0.110 |
| | T1 comb | 383 | -0.066 | -0.104 | -0.134 | n/a | -0.69 | 45 | |
| CX-S-k50-lag-t1s1 | FIT | 102 | -0.086 | -0.141 | -0.203 | n/a | -0.71 | 40 | -0.132 |
| | CHECK | 472 | -0.014 | -0.046 | -0.074 | n/a | -0.15 | 84 | -0.019 |
| | T1 comb | 574 | -0.027 | -0.053 | -0.076 | n/a | -0.34 | 82 | |

**April 2025 check:**
- Long pick: April 2025 gave -7.7R. Excluding April, FIT was +0.23R, so April did not carry the result.
- Short pick: April 2025 gave -2.1R.

**Long pick (CX-L-k75-lag-t1s1):** the FIT result was one big day and a SPY-up tailwind. It reversed on CHECK, where
it ranked in the 3rd percentile of random entries and did worse than the same names on non-trigger days. It falls under
the backlog's own falsifier.

**Short pick (CX-S-k50-lag-t1s1):** it is the near-miss on paper. It clears **every T1 leg** of the top-10 standard:
- comb -0.027 vs -0.038
- check -0.014 vs -0.046
- w/o best day -0.053 / -0.046
- R / session -0.035 / -0.024

But T2 is unscorable, the day-clustered t is about 0, it does not beat random (84th percentile), and it is no better than
the same names on non-trigger days (-0.014 vs -0.019). So its signal adds nothing. It is "debatable" and has no
promising parent, so it is not admitted.

**Salvage view:** the crypto complex is mostly a high-beta basket. Whatever edge it has is the day's direction, not a
lag. If the inverse crypto ETPs are added to the bar cache, the untested "long via inverse ETPs on down days" leg could
get one screen. Shorts were the worst side here, though, so expectations are low.

## Idea 2: peer-group laggards (`mh-1121-peer-cluster-laggard`)
**Setup:**
- Groups are point in time: residual-return (ex-SPY beta) correlation peers from the trailing 120 sessions before each
  month, stocks only.
- Trigger: at least 3 peers have moved >= m ATR the same way at 09:50.
- Laggard: own move between -0.5 and +0.25 ATR in the group's direction.

**FIT, all 16 configs:**
- **Longs:** -0.068 to +0.069R (3 of 8 positive). All are positive on SPY-up days and negative on SPY-down days.
- **Shorts:** -0.17 to -0.21R in every config, and walk-forward positive months were 0-38%.

| FIT pick | test | trades (/session) | avg R | gross | w/o best | w/o top-2 | best-day share | t (cl) | null pct (random mean) | same names, unsignalled days |
|---|---|---|---|---|---|---|---|---|---|---|
| PG-L-c35-m50-hold | FIT | 2,831 (17.8) | +0.046 | +0.126 | +0.015 | -0.016 | 0.69 (**1 day**) | 0.55 | 99.4 (-0.029) | -0.008 |
| | CHECK | 7,698 (27.9) | **-0.037** | +0.032 | -0.052 | -0.063 | n/a | -0.84 | **100.0 (-0.101)** | -0.089 |
| | T1 comb | 10,529 (24.2) | -0.014 | +0.057 | -0.026 | -0.034 | n/a | -0.37 | 100.0 (-0.081) | |
| | T2 | 1,999 (4.7) | -0.048 | +0.036 | -0.058 | -0.068 | n/a | -0.91 | 96.8 (-0.111) | |
| PG-S-c50-m75-hold | FIT | 177 | -0.194 | -0.085 | -0.259 | -0.322 | n/a | -1.45 | 53.5 | -0.163 |
| | CHECK | 402 | -0.105 | -0.016 | -0.147 | -0.179 | n/a | -1.11 | 61.9 | -0.097 |
| | T2 | 86 | -0.111 | -0.002 | -0.256 | -0.343 | n/a | -0.46 | 75.7 | |

**April 2025:** the long pick lost -96.5R in April 2025, so April hurt it rather than carried it. Excluding April, FIT
was +0.085R.

**SPY split (CHECK), long pick:**
- up days: +0.246R (2,506 trades)
- flat days: -0.086R (2,985 trades)
- down days: -0.291R (2,207 trades)

T2 shows the same pattern: +0.574 on up days and -0.633 on down days.

**Overlap with parked mh-1102** (MH4-style lag signal recomputed at the 09:50 row; an approximation): 5.9% of the long
pick's symbol-days and 10.5% of the short pick's. So this is a mostly different signal set.

**Tier check, long pick PG-L-c35-m50-hold (Tier A legs):**
| leg | value | threshold | result |
|---|---|---|---|
| T1 comb avg R | -0.014 | >= -0.038 | pass |
| T1 check avg R | -0.037 | >= -0.046 | pass |
| w/o best day, comb | -0.026 | >= -0.067 | pass |
| w/o best day, check | -0.052 | >= -0.078 | pass |
| R / session, comb | -0.349 | >= -0.486 | pass |
| R / session, check | **-1.021** | >= -0.522 | **fail** (28 trades / session at a negative average) |
| T2 avg R | -0.048 | >= -0.105 | pass |
| trades >= 20 on check and T2 | yes | | pass |

- Day-clustered t is -0.84, far from the 2.63 bar.
- Not REALLY BAD (FIT is positive), so it is "debatable".
- It has no promising live parent, so it is **not admitted**.

**Short pick PG-S-c50-m75-hold:** **REALLY BAD** under the binding rule: FIT, CHECK and T2 (86 trades) are all below
-0.03.

**What can be salvaged (with optimism, numbers as measured):**
- The long laggard picks are consistently better than random names on the same day:
  - FIT +0.075R, CHECK +0.064R and T2 +0.063R over the day-matched random mean, at the 97th-100th percentile in all
    three periods.
  - On CHECK they also beat the same names on their unsignalled days (-0.037 vs -0.089).
- Gross R is positive everywhere (+0.03 to +0.13).
- What sinks it is the market leg (+0.25R on up days, -0.29R on down days) plus costs.
- This independently confirms MH4's day-matched excess (+0.05 to +0.17R) on a different trigger (count-based, from the
  prior close) with only 6-11% overlap.
- The natural next step is the already-filed rework **mh-1102-group-laggard-hedged** (a beta-sized SPY hedge, or long
  and short laggards netted). It now has two independent pieces of evidence. It needs a hedged-book execution feature,
  which is an owner call.
- No more configs were run here (usage cap).
- A lower-volume version (fewer trades / session) would also pass the R / session leg, but it would still be negative in
  absolute terms. Not recommended on its own.

## Files
- `PLAN.md`: the pre-registration
- `build.py`, `screen.py`: the scripts
- `out.txt`, `fit_all.csv`, `picks.csv`, `picks.json`: the results
- `inbox_lines.md`, `backlog_updates.jsonl`: inbox FYI lines and backlog notes
- The intermediates (`work/rows_*.parquet` and the daily tables, about 55 MB) were deleted after scoring. Rebuild them
  with `python build.py WORK t1|t2`, which needs `etb_rate.parquet` in WORK.
- Not applied: earnings blackout (bench10 does not apply one either) and the 70% duplicate rule (nothing was admitted).

Educational only — not financial advice.
