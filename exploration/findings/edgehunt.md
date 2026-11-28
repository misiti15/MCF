# EDGEHUNT: can a cost-share lever turn a bench cell positive? (result)

Educational only — not financial advice.

- **Pre-registration:** `findings/edgehunt_prereg.md`, commit 5fa15c1269, pushed before any cell was scored.
- **Scripts and outputs:** `exploration/sandbox/edgehunt/`:
  - `walk_hold.py`;
  - `score.py` → `score_out.txt` and `cells.csv`;
  - `describe.py` → `describe_out.txt`, which is descriptive and not counted.
- **Configs tried: 20** (5 setups x 4 arms). The cumulative count is about 9,676.
- The locked holdout 2024-11-01..2025-02-28 was never read. It is asserted absent on both lots and bars.

**Rule-change context.** This is a bench study. Today's rules (LIVE-L costs for shorts, LR8 research costs for longs, the 15:55 flatten) apply to the whole window, so live ledger changes do not apply to these rows. The next live change for one of these setups is AV50 / ETF-STOP50 for NM-ETF from 11-30, after the window.

## Answer in one line

**0 of 20 cells pass.** No cell reaches t 2 on CHECK; the best CHECK t is 0.97. The cost-share levers move net R in the right direction for most setups, by +0.01 to +0.04R per lot. But the gross edge underneath is only about 0 to +0.09R per lot, so nothing clears costs on both splits.

## What was tested
- **Universe:** 56,967 bench lots of the 5 setups that have lots on both CHECK and T2:
  - L3-fromopen, RW3 and RW5 (shorts);
  - NM-ETF-late-dip and GEN-261020-09 (longs).
  - Source: REGSTEER-1126 candidates, with bench10 signals and the 1-minute walk.
- **Arms:**
  - **W1** — planned stop ≥ 1% of price, current exit;
  - **W2** — stop ≥ 2%, current exit;
  - **H0** — hold: stop or 15:55, no target;
  - **H1** — hold, with stop ≥ 1%.
- **Bar:**
  - t ≥ 2 and a positive mean on CHECK, and the same on T2;
  - Holm over the 20 cells;
  - one-big-day check on both splits;
  - at least 100 lots per split.

## Results (net R per lot after costs; t is day-clustered)
| Setup | Base CHECK / T2 | Best arm, CHECK | Its T2 | Pass |
|---|---|---|---|---|
| L3 (short) | −0.063 / −0.053 | W2 −0.021 (t −0.35) | −0.027 (t −0.49) | no |
| RW3 (short) | −0.100 / −0.138 | W2 −0.020 (t −0.28), 274 lots | −0.086, 53 lots | no |
| RW5 (short) | −0.105 / −0.182 | H1 −0.049 (t −0.75) | −0.061 | no |
| NM-ETF (long) | +0.041 / −0.048 | H1 +0.077 (t 0.97; best day 43%) | **−0.102** (sign flips) | no |
| GEN-261020-09 (long) | −0.053 / −0.079 | W2 −0.041 | −0.092 | no |

**Per-setup better / worse against each setup's own base** (the remedy rule). Each cell gives the number of setups better / worse, then the mean change per lot.

| Arm | CHECK | T2 |
|---|---|---|
| W1 | 4 / 1, +0.015 | 4 / 1, +0.028 |
| W2 | 4 / 1, +0.037 | 3 / 2, +0.021 |
| H0 | 3 / 2, +0.008 | 4 / 1, +0.005 |
| H1 | 4 / 1, +0.015 | 4 / 1, +0.039 |

- The levers that drop lots (W1, W2, H1) also raise R per day. That is the known "trade less" effect: they shed losing lots. It is not a new edge.
- **One-big-day check:** every cell has a negative total on at least one split, so the check fails or does not apply. NM-ETF is the only cell that is positive on CHECK, and there its best day carries 43% of total R.

## The gross / cost picture (descriptive; shorts pooled, hold arm, by planned stop width)
| Stop % of price | CHECK gross / cost / net | T2 gross / cost / net |
|---|---|---|
| < 0.5% | +0.076 / 0.196 / −0.119 | −0.002 / 0.196 / −0.198 |
| 1-2% | about +0.01 / 0.09-0.10 / −0.08..−0.10 | about +0.09 / 0.11 / −0.02 |
| 2-3% | +0.068 / 0.078 / −0.009 | +0.117 / 0.097 / +0.020 |
| ≥ 3% | +0.070 / 0.062 / +0.008 | +0.137 / 0.070 / +0.068 |

- **Shorts with very wide stops held to the close come close to break-even** on CHECK and T2, mostly through L3.
- **FIT contradicts it.** Under the same rule FIT gives 2-3% −0.155 and ≥ 3% −0.270. L3 with a stop ≥ 2%, held, is −0.003 on CHECK, +0.047 on T2 and −0.182 on FIT.
- That is a sign flip across splits. It is post-hoc and not a candidate.

## What this rules out
1. **No cost-share fix on the current gross-down / long set.**
   - Making cost a small share of R lowers cost from about 0.13-0.20R to about 0.06-0.08R per lot. Gross stays at about 0 to +0.1R, and it is unstable across the three splits.
   - So for these setups, "trade only the cheap lots" and "let winners run" are not sources of edge.
   - This confirms long_edge.md (gross flat across widths) and rw_target.md (wider targets do not help) for the shorts and the GEN / NM longs as well.
2. **A wider target does not raise gross reliably.** Holding to the close changes net R per lot by about −0.05 to +0.04R against the current exit (H0 vs base). Costs are about the same in both arms. It is not a lever on its own.
3. **The arithmetic of the bar.** To survive costs at stops ≥ 2% of price, a cell needs a stable gross of at least about 0.10-0.15R per lot, about 2-3x what any of these 5 setups shows on any split.

## Most promising next step (for the backlog; no live change)
- **GROSS-FIRST discovery.** Search the 3,000+ names for signals with the stop fixed wide (≥ 2% of price or ≥ 12 spreads) and a hold-to-close exit, so cost is about 0.06R from the start.
- Rank candidates on **gross R ≥ 0.15 on FIT**. Only then apply costs and score CHECK once and T2 once, with Holm over the configs tried.
- This turns the search around. It looks for big moves where cost cannot matter, instead of trying to rescue existing signals whose gross is about 0.
- The SPREADFLOOR shadow (logging from 11-30) remains the live test of the cost-share effect itself.
- **Forward shadow spec:** none. Nothing passed, so no TAGS-style tag is proposed.

Educational only — not financial advice.
