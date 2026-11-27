Educational only — not financial advice

# GENSIBS-1127: sibling family of the top live GEN setups — **FAIL** (0 of 56 configs positive on both CHECK and T2)

## Plain-language summary
- **Which setups.** I took the four best live Setup Generator setups by shrunk avg R:
  - P05 (PM weak-breadth short)
  - P07 (PM weak-breadth short)
  - P37 (lunch strong-breadth long)
  - P09 (midday QQQ-down long)
- **What they share.** All four use a day-type gate at an extreme: BRop < 0.35, BRvw < 0.3, BRvw > 0.7, or QQQ < −0.3%. All four trade midday or afternoon with a hold or trailing exit and no target.
- **What I tested.** I built 56 pre-registered siblings: gate thresholds moved, gate swapped, gate removed, one feature dropped, window widened, exit swapped, and the gate transplanted onto simple triggers.
- **Result.** None of the 56 is positive after LIVE-L costs on both CHECK and T2. All 5 FIT finalists come from the P37 family, and all are negative on CHECK and on T2. The verdict is **FAIL**, and there is no backlog proposal.
- **Why the live records look strong.** They are one-big-day records. The best day carries 95–142% of total live R, and the day-clustered live t is between 0.8 and 1.5.
  - On FIT, every gated sibling is again carried by one day: 2025-04-09 for the longs, and 2025-03-03 or 04-08 for the shorts.
- **What can be salvaged.** The P05 / P07 / P37 triggers have a small gross edge on CHECK: +0.09 to +0.12R per trade before costs. On CHECK they also beat a random entry on the same breadth gate (100th percentile).
  - At R = 0.25 × daily ATR, LIVE-L costs about 0.11R per trade, which removes that edge.
  - On T2 the gross edge is about zero, so this is not an edge yet. It is a pointer: a wider-R version could be worth a separate pre-registered test.

## Setup
- **Parents and selection rule.**
  - Rule: GEN setups, non-Graveyard, at least 50 live trades, trade-level t ≥ 2, top 4 by shrunk avg R.
  - Live data: footrace `live_trades()`, LR8 R, as of 11-27.
  - None of the four reaches t ≥ 2 on a day-clustered basis. This is disclosed in PREREG.

| Parent | Live n / traded days | Live avg R (LR8) | Live avg R (LIVE-L) | Trade t / day-clustered t | Best-day share | Avg w/o best day |
|---|---|---|---|---|---|---|
| P05 GEN-261022-05 | 223 / 7 | +0.445 | +0.488 | 6.57 / 1.16 | 122% (11-20) | −0.179 |
| P07 GEN-261026-07 | 238 / 8 | +0.416 | n/a | 6.60 / 1.47 | 95% | +0.029 |
| P37 GEN-261023-07 | 139 / 11 | +0.460 | n/a | 3.70 / 0.81 | 142% | −0.296 |
| P09 GEN-261020-09 | 259 / 12 | +0.293 | n/a | 4.86 / 1.29 | 96% | +0.018 |

The P05 LIVE-L figure comes from ARENASTARS-1127 live_audit.json. LIVE-L live figures for the other three are in that study.

- **Engine.** bench10 lots via `gs_gen.py`, which wraps the bench10 / ARENASTARS engine:
  - First qualifying 5-minute bar per symbol-day, entered at the decision-bar close.
  - Exits walked minute by minute, stop checked first.
  - hold / holdtr exits, Testing book (cap 100, ≤ 3 lots per symbol, cost filter 0.15), price ≥ $5, shorts ETB ≥ 90%.
  - Costs: LIVE-L (headline) and LR8.
- **Splits.** FIT 170 sessions, CHECK 276, T2 427. The locked block is never read.
  - The T2 breadth gates come from a 469-name universe (disclosed).
- **Parity check.** The P37 replica (S03) reproduces ARENASTARS exactly on FIT: 1,683 trades, +0.3468R.
- **Pre-registration and configs.** PREREG is commit 06193a6 and was written before any scoring. Configs: **56**. Cumulative N ≈ **9,023**.
  - The PREREG text says "~20:05 UTC". The commit time (~19:56 UTC) is the authoritative one.
- **FIT freeze.** The FIT finalists were frozen in `fit_pick.json` (commit a5a1cdb) before CHECK or T2 was scored.

## Finalists (all listed; LIVE-L; day-clustered t)

| Config | What changed | FIT avg / t (n) | CHECK avg / t (n) | CHECK w/o best day | T2 avg / t (n) | T2 w/o best day | LR8 CHECK / T2 | Same-gate random control (pct rank) CHECK / T2 | Bar |
|---|---|---|---|---|---|---|---|---|---|
| S22 | P37 gate → QQQ > +0.6% | +0.532 / 1.02 (1481) | −0.025 / −0.39 (3431) | −0.064 | −0.082 / −1.29 (1678) | −0.106 | +0.040 / −0.005 | 100 / 83 | FAIL |
| S21 | P37 gate → BRop > 0.65 | +0.413 / 0.97 (1776) | −0.014 / −0.15 (2443) | −0.076 | −0.171 / −2.87 (1930) | −0.202 | +0.051 / −0.094 | 100 / 21 | FAIL |
| S13 | P37 gate BRvw > 0.75 | +0.482 / 0.94 (1219) | −0.001 / 0.00 (1417) | −0.109 | −0.105 / −1.34 (1321) | −0.145 | +0.062 / −0.030 | 100 / 62 | FAIL |
| S03 | P37 replica | +0.347 / 0.86 (1683) | −0.110 / −1.07 (2384) | −0.177 | −0.152 / −2.39 (1996) | −0.180 | −0.047 / −0.078 | 100 / 58 | FAIL |
| S12 | P37 gate BRvw > 0.65 | +0.294 / 0.86 (2156) | −0.069 / −0.99 (3682) | −0.111 | −0.154 / −2.90 (2648) | −0.177 | −0.004 / −0.080 | 100 / 22 | FAIL |

- **FIT one-big-day check.** Every finalist is carried by 2025-04-09 (best-day share 103–119%), and avg R without that day is negative.
- **FIT screen strength.** The FIT screen itself was weak: no config reached FIT t ≥ 1.1.
- **Best-day share on CHECK and T2.** It is not defined, because the totals are negative.

## Per-family effect vs the parent replica (44 siblings in families B–G; LIVE-L avg R)
- **CHECK:** 12 better, 32 worse. Median −0.023R. Mean gain +0.044R where better, mean loss −0.063R where worse.
- **T2:** 23 better, 21 worse. Median +0.002R. Mean +0.030 where better, −0.039 where worse.
- **Gate removal (D).** Removing the gate makes CHECK worse for P05, P07 and P37:
  - P05: +0.013 → −0.159
  - P07: −0.025 → −0.089
  - P37: −0.110 → −0.134
  - It helps P09: −0.105 → −0.061.
  - So the gates do filter, but the gated parents are still at or below zero.
- **Transplants (H, 8 configs).** All 8 are negative on CHECK, between −0.08 and −0.16.
  - S52 (BRvw < 0.3 PM short on MACDh ≤ −0.079) is the only sibling positive on T2: +0.016, t 0.23. It is −0.158 on CHECK.
- **Day-type check on random pools (09:50–15:00 random bars, lunch window onwards).**
  - A breadth gate by itself does not improve random entries: random long-hold on BRvw > 0.7 days is −0.181R on CHECK, against −0.145 on all days.
  - So the live records did not come from the day-type alone.

## What can be salvaged (optimistic read, honestly scored)
- **Small gross trigger edge on CHECK.** Gross R per trade before costs is positive for the P05, P07 and P37-gate siblings: S01 +0.115, S13 +0.116, S21 +0.107, S22 +0.094, S45 +0.119.
  - This is also positive on LR8 (+0.04 to +0.065).
  - It beats the same-gate random pool on CHECK in all 5 finalists.
- **Costs remove it.** LIVE-L costs about 0.11–0.12R per trade at R = 0.25 × ATR on $95–150M ADV names.
- **T2 does not confirm it.** T2 gross is about 0 (−0.03 to +0.06).
- **Possible next step.** A cost-per-R remedy (a wider R, e.g. 0.5 × ATR with the same triggers) would halve the cost in R. That would be a new pre-registration and is not claimed here.
- **What this means for the live GEN winners.** Their live records should be read as one-day captures, for example the 11-20 afternoon selloff for P05. They are not evidence of a durable family. ARENASTARS reaches the same conclusion for the parents.

## Rule-change context (research/ledger.jsonl, inside the parents' live window 10-19..11-27)
- 10-23: per-setup daily loss stop switched off in Testing 1/2 and the Setup Generator.
- 10-26: GX2 Setup Generator caps 80 → 200 slots, 16 → 48 per setup.
- 10-27: GX1 lab setups evaluated on the 5-minute clock.
- 10-30: Testing cost filter 0.15.
- 11-05: low-rep rotation through Explore 1 / Live Lab.
- 11-12: LR8 live cost model; Testing A full universe; generic cap 30; account halt −300.
- 11-16: ROT1 arena rotation (P05 into Explore 1).
- 11-17: TSZ1 testing sizing.
- 11-20: stop rounding / FOOTRACE-EXIT.
- 11-21: cost-basis fix.
- P05's best day (11-20) falls after the TSZ1 and ROT1 changes. Its 101 trades that day were in Explore 1.

## Backlog proposal
None. No sibling survives. If a follow-up is wanted, it would be: "GENSIBS-R: P05 / P37 trigger sets at R = 0.5 × ATR (hold), FIT screen, CHECK + T2 LIVE-L". That is research only, not a setup.

## Files
- `gs_grid.py`: the grid
- `gs_gen.py`: lots and random pools
- `gs_score.py`: FIT screen, CHECK / T2 scoring, controls, bars
- `fit_pick.json`, `results.json`, `results.csv`: outputs
- Lots (≈1.3M rows) were kept in the scratch work dir and deleted afterwards.
