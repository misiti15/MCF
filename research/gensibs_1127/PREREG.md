# GENSIBS-1127 pre-registration (written 2026-11-27 ~20:05 UTC, before any sibling was scored)

Educational only — not financial advice. Research only: no config, setup, exit, assignments, decisions.json, ledger or
backlog change. No broker / MarcoFlow calls (journals via `git show`, bars from the local caches).

## Question
Can the best live Setup Generator (GEN) setups be turned into a family of siblings that holds on history?
Optimistic hypothesis: what the live winners share (a day-type gate at an extreme of breadth / index move, midday or
afternoon window, hold / trailing exit with no target) is a real edge, and a disciplined perturbation finds a version
that is positive on CHECK and on T2 after LIVE-L costs and beats a random entry on the same day-type.

## Parents (selection rule, from journals of all non-Graveyard accounts, LR8 R, mcf.report.footrace.live_trades())
Rule: GEN setups, >= 50 live trades, trade-level t >= 2, ranked by shrunk avg R = n/(n+150)·avg + 150/(n+150)·(−0.10);
the top 4 (shrunk > 0.10). **Disclosed: with a day-clustered t none of them reaches 2** (7-12 traded days each; the
best day carries 95-142% of total R for P05/P07/P37/P09). Parents:
| id | setup | n | avg R (LR8) | trade t | day-clust t | shrunk | best-day share |
|---|---|---|---|---|---|---|---|
| P05 | GEN-261022-05 MACDh/UpWick/ORHdist PM BRop<0.35 holdtr short | 223 | +0.445 | 6.57 | 1.16 | 0.226 | 122% |
| P07 | GEN-261026-07 Flow3/BBpct/ADX7 PM BRvw<0.3 holdtr short | 238 | +0.416 | 6.60 | 1.47 | 0.216 | 95% |
| P37 | GEN-261023-07 RSIslope/BarRng/VWAPcrosses LUNCH BRvw>0.7 hold long | 139 | +0.460 | 3.70 | 0.81 | 0.169 | 142% |
| P09 | GEN-261020-09 EMAdChg/Z12/VWAPcrosses MID QQQ<−0.3 holdtr long | 259 | +0.293 | 4.86 | 1.29 | 0.149 | 96% |
(6th by shrunk, GEN-261029-06 t1s1 LATE QQQ<−0.3 short, shrunk 0.040, not taken.)
**Prior disclosed:** the ARENASTARS-1127 study (same branch, tonight) already replayed P05/P07/P37 at their live config
on history; I read its hist_results.csv before writing this: all three fail (P05 CHECK +0.013 / T2 −0.072R; P07
−0.025 / −0.198; P37 −0.110 / −0.152, LIVE-L). The sibling grid below was fixed after seeing that (it is why gate
removal and transplant families are included), but no sibling has been scored.

## Shared traits -> grid (56 configs, fixed in gs_grid.py)
A parent replicas (4) · B gate threshold neighbours (12) · C gate swapped to another breadth / index gate (8) ·
D gate removed (4) · E one core feature dropped (12) · F window widened (4) · G geometry hold<->holdtr (4) ·
H breadth gate transplanted onto simple single-trigger bases: weak-breadth BRvw<0.3 PM holdtr short with RSI5>=80 /
Z12>=1.5 / VWAP-loss / MACDh<=−0.079; strong-breadth BRvw>0.7 lunch hold long with RSI5<=20 / Z12<=−1.5 /
VWAP-reclaim / MACDh>=0.079 (8). Full list: `python gs_grid.py`.

## Engine
bench10 pipeline (research/ultimate_1119/top10/bench10.py) as wrapped by research/arenastars_1127/as_gen.py: lab
frames (T1) / frames built from the T2 1-minute cache, first qualifying 5-min bar per symbol-day in the window,
min_adv on ADV20, entry = decision-bar close, 1-minute walk, stop first (gap-through at the open), R = 0.25 x daily
ATR, hold = stop 1R / no target / flat 15:55, holdtr = + stop trails 1R behind the best price once MFE >= 1R. Testing
book (cap 100 per setup, <= 3 lots per symbol, cost filter 0.15), price >= $5, shorts ETB >= 90%.
T2 context: breadth / breadth_open from the T2 1-minute cache (469 names; ARENASTARS t2ctx.py output) — a narrower
universe than live/T1 (disclosed). Costs: **LIVE-L** (primshorts_1126 cells_live.json, headline) and LR8 (bench10).
Splits: FIT 2024-10 + 2025-03..09; CHECK 2025-10-01..2026-11-04; T2 2023-01-03..2024-09-13. The locked block
2024-11-01..2025-02-28 is never read (bench10 guards + asserts in every script).

## Screen (FIT only) -> finalists
Rank all 56 on FIT LIVE-L day-clustered t among configs with >= 60 FIT trades and FIT avg R > 0; the top 5 are the
finalists (if fewer than 5 qualify, the remainder by FIT t regardless of sign, labelled). CHECK and T2 are scored only
for the reporting table of all 56 after the finalists are frozen in fit_pick.json (committed with the results).

## Control
Random pools: one random eligible 5-min bar (09:50-15:00) per sampled symbol-day (5%, seeded crc32), walked as
short/long x hold/holdtr, with the context columns at that bar. For each finalist: pool rows with the same side, geom,
window, min_adv and **the same context gate** (so it tests the triggers beyond the day-type), same filters; 500 draws
matched to the finalist's trade count per day. Bar: finalist avg R > control 95th percentile.

## Pass bars (each finalist, LIVE-L; LR8 must also be > 0)
- CHECK: avg R > 0, day-clustered t >= 2.0; T2: avg R > 0, day-clustered t >= 2.6 (5 finalists, Bonferroni one-sided
  ~0.005; T2 is the only history the GEN lineage never saw).
- Both: avg R without the best day > 0; best-day share < 25%; above the same-gate random control 95th pct.
- Reported, not a bar: FIT, per-family table vs parent (how many siblings beat their parent on CHECK/T2 and by how
  much), the parent live record, shrunk estimate.
**Verdict:** PASS if any finalist passes all bars; LEAD if one is positive on CHECK and T2 with t >= 1.5 on both and
beats the control but misses another bar; else FAIL. A PASS goes to the testing arena only (exploration, never
Primary; the GEN lineage bar t >= ~4.3 is not claimed).
Configs counted: **56**; cumulative N ≈ 8,952 (+15 ARENASTARS) → **≈ 9,023**.
