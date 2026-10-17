# swarm1017 / rework-cwt14 — NOTES (2026-10-17)

*Educational only — not financial advice. Backtest = lab results on the open two-year history (costs in, R = 0.25 x
daily ATR); live = Testing 2 paper (rule 7). Nothing was scored on the locked block 2024-11-01..2025-02-28.*

## Failures first
- **0 research-grade variants.** Lineage N = 121,309 prior + 252,846 study + 5,780 neighbour checks = **379,935**, so the bar
  is t >= **5.07**. The best day-clustered t of any configuration that passes the regime gate is 3.07, and that one fails
  the busiest-session check.
- **The parents carry no information.** At the same minute, on the same side and with the same exit, every parent is
  slightly WORSE than random entries: excess -0.008..-0.017R, excess t -1.4..-3.3 (t05s1).
  - The loss (about -0.09R) is the cost of the 0.5R-target geometry that every entry pays. The failed-break trigger adds
    nothing to it.
  - The best exit (scale-out at +0.25R) brings the parents to -0.058..-0.074R, and the opposite side to -0.039..-0.051R.
    Both are still negative.
- **3 variants (4 configurations) pass every pre-declared gate, but they are weak.** These are screen, regime, WF >= 0.6,
  beating same-minute random, ex-best-day > 0, busiest session <= 10% and plateau >= 2/3.
  - Their t is 1.05-1.30. For comparison, about 250k configurations with no edge would produce several of these by luck.
  - **With their 5 best P/L days removed, all of them go to about 0** (-0.016 / -0.003 / +0.001R).
  - They are reported as Testing-grade near-misses. **None is ready for live funds.**
- The strongest raw signals depend on a few market-wide days, so they are not edges:
  - ORH poke-and-reclaim then LONG, 11:30-15:00, depth >= 0.3 ATR: t 3.07, +0.168R, n 595. Busiest session 19%:
    2026-03-31 alone has 115 trades. Without its 5 best days it falls to +0.040R, t 1.04.
  - PDH p0.30 LONG: +0.44R. 2025-04-09 holds 154 of 403 trades. Without its 5 best days it falls to -0.078R.

## Live this week (paper, Testing 2, research/swarm1017/week/rework_trades.csv)
- 11 setups, 1,894 trades, -0.133R per trade. Only pdl-p10-lowvol-long was positive (+0.043R, n 77).
- By day:

  | day | R per trade | trades |
  |---|---|---|
  | 10-12 | -0.188 | 293 |
  | 10-13 | +0.052 | 540 |
  | 10-14 | -0.318 | 347 |
  | 10-15 | -0.093 | 357 |
  | 10-16 | -0.226 | 357 |

- **The last 3 days (-0.211R, n 1,061) were worse than the first 2 (-0.032R, n 833).** There is no earlier week to
  compare with, because Testing 2 started 10-12.
- The live replay is consistent with the history: the week's parents were about 0.04R worse than history (-0.09R).
- Hold-to-close (+0.036R) and trail 1R (+0.049R) looked better live this week. That is one week, which is a diagnosis,
  not evidence. On the history the no-target exits (hold / holdtr) were scored for every core and none passed.

## What was run (PLAN.md, pre-declared; N exactly as declared)
- `build.py` builds the event set:
  - the generalised b3 kernel (`sim.py b3k`): 4 levels x 6 p, reclaim up to 5 bars, with poke volume, depth and ordinal;
  - 2 sides x 11 exits, at production cost, for every 95M-universe frame row. These give the same-minute random
    baselines, plus SPY fromOpen and breadth.
- Parity checks:
  - the 5-min simulator matches the frame geometries on 99.998% of rows (2025-06);
  - the kernel reproduces all 11 parents' trade counts exactly: 37,499 / 66,875 / 20,080 / 44,026 / 30,261 / 19,479 /
    43,876 / 39,989 / 105,023 / 31,676 / 74,014.
  - Expectancy runs about +0.0015R above package B's scored figure (a small cost-convention difference, in the
    optimistic direction).
- `scan.py` scores Stage A 126,720 + B 82,368 + C 43,758 = **252,846** configurations, written to `scan_all.csv.gz`.
- `gate.py`: of these, 2,434 pass the screen and 1,282 beat random. Then:

  | check | configurations that fail |
  |---|---|
  | regime | 1,057 |
  | WF | 916 |
  | busiest | 1,017 |
  | plateau | 921 |

  - 225 configurations pass the regime gate, which is 0.09% of 252,846.
  - Output: `gate_all.csv`, `results.csv` (regime passers and candidates) and `gate_summary.json`.
- `robust.py` checks the result without the top-5 P/L days, without the 5 busiest days, without 2025-04, and per
  quarter (`robust.json`).
- `verify.py` checks the modules trade for trade on the live-like frame: 788/788, 438/438 and 622/622 trades match exactly
  (`verify.json`).

## Candidates (modules/, Testing-grade only, all below the 5.07 bar)
| module | rule | exit (live) | n tr / va | exp tr / va | t all | up / down | WF | ex-top-5 days |
|---|---|---|---|---|---|---|---|---|
| CWT14x-orl-p20-lowvol-gap2-long | ORL poke >= 0.20 ATR, v0 < 1, reclaim <= 3 bars, abs(gap) >= 2%, 09:50-11:30 | t1s1 + scale_out_r 0.5, live_scale_out | 385 / 403 | +0.059 / +0.062 | 1.30 | +0.142 / +0.076 | 0.625 | -0.016 |
| CWT14x-pdl-p05-lowvol-brdlo-fo1-long | PDL poke >= 0.05, v0 < 1, breadth < 0.4, fromOpen > +1% | t05s1 + scale_out_r 0.25, live_scale_out | 199 / 239 | +0.022 / +0.055 | 1.24 | +0.161 / +0.028 | 0.70 | -0.003 |
| CWT14x-orl-p10-gapup-heatlo-long | ORL poke >= 0.10, gap > 0, heat <= -30 | t05s1 + scale_out_r 0.25, live_scale_out | 254 / 368 | +0.039 / +0.028 | 1.05 | +0.036 / +0.032 | 0.75 | +0.001 |

- **Live code needed:**
  - **breadth** (the share of the 95M universe above its open, per bar) is not in the LabStrategy frame. The pdl-brdlo
    module returns all False without it.
  - **t05s05** is not in LabStrategy.GEOMS.
  - The **no-target exits** (hold, holdtr) need a no-target GEOM.
- Scale-out, breakeven, trail and the time stop are live-supported keys. They are simulated here on 5-min bars, while
  live manages them on 1-min bars.
- The sim marks the t1s1tr variant of the orl-p20 candidate as weaker (t 0.97).
