Educational only — not financial advice.

# BREADTHGATE-1127 pre-registration (written 2026-11-27 ~20:30 UTC, before any breadth value was joined to any lot R)

**Question.** Several strong live GEN setups carry a market-breadth gate (BRop = share of the universe above its day
open, BRvw = share above its session VWAP; e.g. `BRoplt0p35`, `BRvwgt0p7`). Is a side-aware breadth gate a *portable*
filter that improves OTHER setups (Primary's L3 / RW3 / RW5 / NM-ETF and arena setups that carry no breadth gate)?
Side-aware = shorts are kept only when breadth is weak, longs only when it is strong (or, in the veto form, shorts are
skipped only when breadth is very strong and longs only when it is very weak).

**Prior evidence (guardrail 26 flag).** RESEARCH_RULES 26 lists "gates on proven setups" and "day-type on/off switches"
as items to flag before work. Priors: research/breadth_1125 (breadth as an SPY close-gate: 0/12 useful out of sample;
gating NM-ETF raised its CHECK per-trade R but on fewer trades), research/regsteer_1126 (regime steering of Primary:
FAIL, "mostly turns off a losing list"), W4 (0/31 live per-setup condition filters). This study is the workflow's
assigned research step (no live change is possible from it); it answers the open question with a size-matched random
control so that "trading less of a losing list" cannot pass as selection.

Research only: no change to config/, setups, exits, docs/live/assignments.json, decisions.json, ledger or backlog.

## Data and engine (rule 31: no new simulator; lot-table arithmetic on bench10 lots)
- **Lots:** bench10 (research/ultimate_1119/top10/bench10.py) live-config signals, 1-minute exits (stop first,
  gap-through at the worse price, target only when traded through by $0.01, flat 15:55), entry at the decision-bar close.
  Primary 4 (L3-gap-slope-fromopen-FD, RW3-gapdn-rsi5pop-flowsell-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD,
  NM-ETF-late-dip-di-long): the bench10/squeeze_1125 lots rebuilt tonight (same lots as regsteer_1126 cand.parquet;
  parity checked on r). Arena / reference (bg_gen.py, bench10 unchanged except SETUPS): L3-gap-slope-lowdist-FD,
  L3-gap-slope-rsi5hi-FD, RW6-ns2-up3-short-FD, NM-RWN4-ns2-spyup05-notfri-short, CWT14-failbrk-orl-p10-long-WB5,
  CWT09-gapdn-vwaploss-g10-short, ST7-rsi50dn-long-pm-t1s1-FD; plus GEN-261020-09-…-QQQltm0p3-holdtr-long (arena GEN with
  a QQQ gate, no breadth gate; regsteer_1126 cand.parquet, LIVE-L = LR8 for longs). **Judged set = these 12 setups.**
  Information only (not judged; they already carry a breadth gate): GEN-261022-05 (BRoplt0p35 short), GEN-261023-07
  (BRvwgt0p7 long), GEN-261026-07 (BRvwlt0p3 short).
- **Filters (as regsteer_1126):** entry >= $5; shorts easy-to-borrow (>= 90% of the universe snapshots). No book caps
  (lot level). Every lot weighs 1R.
- **Costs:** LIVE-L (primshorts_1126 cells_live.json) on shorts, LR8 research on longs = the judged basis. LR8 on every lot =
  second basis (bench10 add_r).
- **Breadth at entry:** the lab context value at the lot's decision bar (date, tod = bar-end HHMM, as of that bar's close;
  the same point-in-time column a live `context:` setup reads). T1 (FIT/CHECK): research/history2y/data/context (lab
  universe). T2: computed by bg_t2ctx.py from data/cache_fresh/1Min (469 names; method checked against the lab table by
  arenastars_1127/t2ctx_check.py). The T2 universe is smaller (disclosed). A lot with missing breadth is kept (gate cannot
  fire; fail-open for a filter, counted).
- **Splits:** FIT 2024-10 + 2025-03..09 (reported only); CHECK 2025-10-01..2026-11-04; T2 2023-01-03..2024-09-13.
  The locked block 2024-11-01..2025-02-28 is never read (asserted on every load in every script).

## Configurations (N = 6). keep(lot) rule; a lot that fails is skipped.
| id | measure | shorts kept when | longs kept when | form |
|---|---|---|---|---|
| VW-M | BRvw | < 0.50 | > 0.50 | side-aware gate, mild |
| VW-S | BRvw | < 0.40 | > 0.60 | side-aware gate, strict |
| OP-M | BRop | < 0.50 | > 0.50 | side-aware gate, mild |
| OP-S | BRop | < 0.35 | > 0.65 | side-aware gate, strict (the GEN grid values) |
| VW-V | BRvw | <= 0.70 (skip if > 0.70) | >= 0.30 (skip if < 0.30) | veto (targeted) |
| OP-V | BRop | <= 0.65 (skip if > 0.65) | >= 0.35 (skip if < 0.35) | veto (targeted) |
Thresholds come from the generator grid (mcf/research/generator/spec.py), not from this data. Cumulative N ≈ 8,952 → **8,958**.

## Metrics
- **RAW gain** of a config on a setup × split = R of the gated lots − R of all lots = −(sum of skipped R).
- **Z gain (selection, the judged quantity)** = −sum over skipped lots of (r − mean r of that setup × split, all lots).
  This removes the "trading less of a losing list" effect: a random skip has expected Z gain 0.
- **Size-matched random-skip control:** 500 draws (seed 1127); in each setup × split, skip the same NUMBER of lots chosen
  uniformly at random. Report the gate's RAW gain vs the draws' mean / 95th percentile, per split, pooled over the judged set.
- Daily series: per session, pooled Z gain over the judged setups; day-clustered t = mean / (sd / sqrt(sessions)) over all
  sessions of the split (sessions with no lots count as 0).
- One-big-day: best-day share of the total Z gain, and avg daily Z gain without the best day.
- Per setup (remedy report): Z gain per lot of the setup's whole lot count, CHECK and T2; improve / worsen counts and sizes.

## Pass bars (all must hold for a config; judged on LIVE-L, pooled judged set)
1. Z gain > 0 on CHECK and on T2, each with day-clustered t >= 1.5, and the combined CHECK+T2 daily series t >= 2.64
   (Bonferroni for 6 configs, two-sided 5%). A lineage claim (a rule worth a live shadow tag) is reported against the
   cumulative bar t >= 4.3 as information.
2. RAW gain above the 95th percentile of the size-matched random-skip control on CHECK and on T2.
3. One-big-day: best-day share of the Z gain < 50% and avg daily Z gain without the best day > 0, on CHECK and on T2.
4. Remedy targeting: among judged setups with >= 30 skipped lots in the split, at least 2/3 improve (Z gain > 0) on CHECK
   and on T2; no setup worse than −0.02 R per lot (on its whole lot count) in BOTH CHECK and T2.
5. Not a blanket cut: the config skips <= 50% of judged lots pooled (CHECK and T2 each).
6. Second cost basis: Z gain > 0 on CHECK and T2 under LR8 as well.
Also reported (not bars): whether the gated sleeve itself is positive after costs per setup (RAW avg R of kept lots),
FIT numbers, the 3 information GENs, Primary-4 vs arena subtotals.

## Salvage (optimism; pre-stated so it is not a garden of forking paths)
If no config passes but one passes bars 1-3 on a subset defined only by side (all shorts / all longs) or by group
(Primary 4 / arena 8), it is reported as a lead (LEAD verdict) with the exact bars it misses; no new threshold is searched.
No live trades are used: live breadth is not recorded per trade for setups without `context:`; the bench replays today's
rules on every day, so no ledger rule-change date falls inside these figures.
