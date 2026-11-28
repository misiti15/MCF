# EDGEHUNT: pre-registration (written 2026-11-28 ~02:15 ET, before any cell below was scored)

Educational only — not financial advice.

**Question.** Is there any setup x side cell on the bench where the gross edge is big enough to clear costs? Costs are about 0.13R per lot and have swamped every gross edge so far. Two levers can change the cost share without changing the signal:
1. **Wide stops only.** LIVE-L cost is roughly a/stop_bp + b, so a wider planned stop (as a % of price) makes the cost per R smaller.
2. **Wider target.** Hold to the stop or the 15:55 flatten, with no target. This lets winners run, so the gross per lot can grow while the cost per lot stays about the same.

**Already seen before writing this.**
- long_edge.md: gross R is flat across stop widths in history, and wide stops lift net R only by the cost effect. History longs at stop ≥ 200 bp were still −0.105 on CHECK.
- rw_target.md: the RW 1.25x target failed under LIVE-L.
- PRIOR_RESEARCH: "holding beats cutting".
- The per-setup *base* means of rsw/cand.parquet by split (the setup x period table only, printed while choosing the universe). No filtered or variant cell has been looked at.

## Data (read-only caches, nothing re-generated)
- **Lots:** `scratchpad/rsw/cand.parquet` (REGSTEER-1126 bench candidates: bench10 signals plus the bench10 1-minute walk, entry ≥ $5, shorts only if ETB rate ≥ 0.9). Columns used: setup, symbol, date, per, tod, side, entry, risk, r.
- **Base net R** is `r` as stored. It uses LIVE-L (primshorts_1126 cells_live.json) for shorts and LR8 research for longs, which is the primshorts / regsteer convention.
- **Splits:**
  - CHECK = 2025-10-01..2026-11-04;
  - T2 = 2023-01-03..2024-09-13 (independent);
  - FIT is descriptive only.
  - The locked block 2024-11-01..2025-02-28 is never read. The code asserts this on lots and bars.
- **Setups scored:** the 5 with lots on both CHECK and T2:
  - L3-gap-slope-fromopen-FD (short);
  - RW3-gapdn-rsi5pop-flowsell-short-FD (short);
  - RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (short);
  - NM-ETF-late-dip-di-long (long);
  - GEN-261020-09-…-MID-QQQltm0p3-holdtr-long (long).
  - The three GEN setups with no T2 lots cannot meet the bar and are not scored.

## Variant walk (H arms)
- `exploration/sandbox/edgehunt/walk_hold.py` walks each lot again on the same 1-minute bars, using bench10.walk_trades unchanged. Stop = entry − side·risk, **no target**, exit at the stop or the 15:55 flatten.
- **Net R of the H arms:**
  - gross = side·(exit − entry)/risk;
  - shorts minus LIVE-L `predict_R(cells, entry, risk, kind)` (kind = stop or market; borrow is inside the fit);
  - longs minus the bench10 LR8 research cost (tier 1, tod multiplier, no borrow).
  - Sensitivity, descriptive only: longs at LIVE-L.

## Cells: 20 configurations (5 setups x 4 arms)
| Arm | Lots | Exit |
|---|---|---|
| W1 | planned stop (risk / entry) ≥ 1.0% of price | current exit (as stored) |
| W2 | planned stop ≥ 2.0% of price | current exit |
| H0 | all lots | hold: stop or 15:55, no target |
| H1 | planned stop ≥ 1.0% of price | hold: stop or 15:55, no target |

Configs counted: **20** (cumulative about 9,656 → about 9,676).

## PASS (a cell must meet all of these)
1. At least 100 lots on CHECK and at least 100 on T2.
2. CHECK: mean net R per lot > 0 and day-clustered t ≥ 2.0 (bench10.clustered_t).
3. T2: same sign (> 0) and day-clustered t ≥ 2.0.
4. Holm over the 20 cells at α = 0.05. The cell's p is the larger of its one-sided normal p on CHECK and on T2.
5. One-big-day check, on both CHECK and T2: avg R without the best day > 0, and the best day's share of total R < 50%.

## Reported for every cell, pass or fail
- n, mean, t and total R per split;
- Δ per lot against the setup's own base (all lots, current exit);
- Δ in R per day, since the W arms trade fewer lots;
- FIT;
- by year;
- per-setup better / worse count for each arm (the remedy rule).

**Outcome rules.**
- **Anything that passes** becomes a TAGS-style forward *shadow* spec: tag only, no order or live change.
- **If nothing passes,** edgehunt.md says what this rules out and names the most promising next step.
- **Rule-change context.** The bench applies today's rules to the whole window. Live rule changes (ledger) do not apply to bench rows. AV50 for NM-ETF takes effect 11-30, after the window.
