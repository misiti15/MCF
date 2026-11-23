Educational only — not financial advice.

# hardstop_1123 pre-registration (written 2026-11-23, before any configuration was scored)

Owner 2026-11-23: "I want hard stops in place on truly detrimental days based on hard numbers of what is likely to
happen" (automatic, never a human call; CLAUDE.md "no human-in-the-loop on losing days") and, on today's session,
"6/7 trades +4.1R but the rest trending bad. Not good at all!". Research only; no config, ledger or setup change.

## Engine (bench)
- Signals: the bench10 trade lists already on disk (scratchpad `top10w/trades_t1.parquet`, `trades_t2.parquet`,
  research/ultimate_1119/top10/bench10.py: live module mask, window, refire chain, 1-minute exits, LR8 research costs,
  + 1.2 bp borrow on shorts) for the 4 current Primary setups: NM-ETF-late-dip-di-long,
  RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, RW3-gapdn-rsi5pop-flowsell-short-FD, L3-gap-slope-fromopen-FD.
- Book (one simulator, minute by minute, all 4 setups together): price >= $5, shorts ETB >= 0.9, per-setup open-lot
  cap 30, <= 3 lots per symbol per setup, per-setup -2R latch on closed cost-R, burst brake (<= 30 entries per setup in
  10 minutes), account -20R halt on closed + open cost-R marks (no new entries; as live since LR3 11-12). Account slot
  cap 77 and buying power are not modelled (stated).
- Open mark of a lot at the close of minute m = side x (close - entry) less the market-exit cost (1c + 1 bp, x3
  extended tier) and borrow, / risk. A rule flatten exits at that close at that cost (kind "market").
- Point in time: entry gates at minute m use the state at the close of minute m-1 (marks) and realized R up to m;
  rule checks run at the close of each minute; a lot's own stop/target exits (bench walk) come first.
- Base must reproduce bench10's booked per-setup totals (when the -20R halt does not bind) before any rule is scored.
- Periods: FIT 2024-10 + 2025-03..09; T2 2023-01..2024-09-13; CHECK 2025-10-01..2026-11-04 (latest bar on disk).
  2024-11-01..2025-02-28 is never read (filters + asserts).

## Configurations (17)
| id | rule |
|---|---|
| A6 / A8 / A10 / A12 | (a) account stop: closed + open R <= -X -> flatten every open lot, no new entries for the rest of the day |
| L2 / L3 | (b) per-setup latch on closed + open R of that setup <= -X -> that setup takes no new entries (open lots ride) |
| LF2 / LF3 | (b') as L2 / L3 and the setup's open lots are flattened |
| N4 / N6 / N8 | (c) account closed + open R <= -X -> no new entries for the rest of the day (no flatten) |
| S1_0 / S1_2 / S1_4 / S2_0 / S2_2 / S2_4 | Part 2: no new SHORT entry while SPY (last minute close vs prior close) > +X% AND the book's open R (marks of all open lots) < -Y; not latched (re-evaluated each minute) |

## Metrics (per config, FIT / T2 / CHECK and all)
fires (days, days/yr), total R and dR vs base, worst day before/after, days <= -6R (count, sum), R saved on days that
ended worse than the trigger level vs R lost on days that recovered (base day R > fire level), per-setup dR (and how
many setup-days better / worse, by how much), day-clustered t of per-day dR (all three periods pooled and per period),
bootstrap by day (10,000 draws) of the per-year dR and of the mean of the worst 5% days.

## Bars and decision rule (fixed now)
- N = 17 -> bar max(1.5, sqrt(2 ln 17)) = 2.38 on the pooled day-clustered t of per-day dR for any claim that a rule
  IMPROVES R. Lineage note: rules_1122 / etfstop_1123 tried other loss rules (account-wide N noted in REPORT).
- A rule is "Yes" only if: worst day better in FIT, T2 and CHECK; dR >= 0 in at least 2 of 3 periods and t >= 2.38
  pooled. "Optional" if worst day better in all 3 periods and dR >= -1R/yr per period (tail insurance at a stated
  price). Otherwise "No". At most one rule is recommended. Tail insurance is not edge, and the report says so.
- Part 2 grid is judged the same way; SPY > +1% / +2% days are few in the bench (sample stated).

## Live replay (Primary run 1, 2026-10-23..11-23, today included)
- Journal: `origin/mcf-data:journal.db`, LR8 cost-R (mcf.costs.cost_r_lr8). Marks on SIP 1-minute bars (Alpaca
  market-data GET via mcf.data.priors). Blocked entries are removed (R 0), flattened lots exit at the minute close less
  the market cost; freed slots are not refilled (stated). Every figure carries the rule-change context: 10-29 Primary
  -2R latch; 11-11 NM-ETF in; 11-12 LR8 / LR3 halt in cost-R with open marks; 11-19 NS5 out; 11-23 ST7 out, burst
  brake, PSHADOW.
- Part 2 descriptive of 11-23: win rate vs R conversion (target / stop distances), hold time of winners vs losers,
  MFE / MAE of the shorts, entries taken while the book's open R was already negative (point in time).
