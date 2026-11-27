# MEREBFWD-1127 — month-end rebalancing forward shadow (built)

*Educational only — not financial advice. Research only: no config, setup, exit, assignment, decision or ledger change.*

## Plain summary

- We now log, every month, whether big balanced funds should be buying stocks into the last session's close (stocks
  lagged bonds month-to-date) and what a fixed SPY long from 14:00 to 15:55 would have made after costs.
- The rule is the scout's best MEREB1 cell, frozen as found (research/forward/month_end/RULE.md). The script
  reproduces the scout exactly (2024-10..2026-11-04: n 7, +0.478R LIVE-L), so the port is faithful.
- One bug found and fixed in the frozen rule (not a re-tune): the scout "traded" the 2025-11-28 half day at 14:00 on
  after-hours prints (−1.18R). On a half day the rule now does not trade (flat time 12:55 is before the 14:00 entry).
- Dry seed 2026-10-30 (in-sample, not scored): S = −4.32% (SPY +0.88%, TLT +5.20% MTD) → signal; long 754.01 at 14:00,
  stop 752.23 (0.24%, 0.25 × ATR14 7.11) hit at 14:18: **−1.23R LIVE-L**, −1.11R LR8, −1.44R S12.
- First scored month-end: **Mon 2026-11-30** (not a half day; the 11-27 half day is not a month-end).
- Pass bar needs 12 signal trades (~3 years at ~35% of months): avg R > 0 after LIVE-L with t >= 2, best-trade
  share < 50%, avg w/o best > 0, S12 > 0. Harm stop from 6 trades (cum <= −4R or avg <= −0.40R). Time cap 2030-12-31.
- **Daily trigger: the forward-logs trigger needs one added line** (after 16:15 ET; it is a no-op on any other day):
  `python research/forward/month_end/shadow.py --date $(TZ=America/New_York date +%F)` (and `--score` when reporting).

## What was built

| file | what |
|---|---|
| research/forward/month_end/RULE.md | frozen rule, costs, history, pass bar, harm stop, time cap |
| research/forward/month_end/shadow.py | `--date` (acts only on a month's last session; GET-only bars; idempotent upsert) and `--score` |
| research/forward/month_end/forward.csv | log; seed row 2026-10-30 |
| tests/test_month_end_shadow.py | 5 offline tests: calendar (incl. 2025-11-28 half-day month-end, 2026-11-30, list-end refusal), long trade + 15:55 exit + costs, stop, S >= 0 control, half-day no-trade with after-hours prints, idempotent run, lock assert |

## Reproduction check (in-sample, cached SPY 1-min + Alpaca daily, locked block never read)

| month-end | S % | signal | R LIVE-L (rule or control) |
|---|---|---|---|
| 2024-10-31 | +6.69 | no | (−0.77 control) |
| 2025-04-30 | −0.35 | yes | +0.99 |
| 2025-09-30 | −0.71 | yes | +2.92 |
| 2025-11-28 (half day) | −1.10 | yes | no trade (scout: −1.18 on after-hours prints) |
| 2026-02-27 | −4.38 | yes | +0.53 |
| 2026-03-31 | −3.48 | yes | +1.20 |
| 2026-06-30 | −4.17 | yes | +0.12 |
| 2026-10-30 | −4.32 | yes | −1.23 |

With the half-day cap off the seven signal trades average +0.478R = the scout's RECENT split exactly. With the fix the
six average +0.75R — in-sample and post-hoc (the 2016-22 period was −0.415R on 28 trades), so it is not evidence; only
the forward log from 2026-11-30 counts. The other half-day month-ends in the scout window: 2019-11-29 (Nov 2019 SPY
outran TLT, so very likely S >= 0 and untouched) and 2024-11-29 (locked block, not read).

## Counts and context

- Configs: 1 forward test of a cell already counted in the scout's 8 (program cumulative N ~9,350 → ~9,351).
  Nothing was scored on new data tonight; the seed row is in-sample.
- Costs: LIVE-L (single-stock cells; conservative for SPY, ~0.23R on a 0.24% stop) is the pass currency; LR8
  (≈ 0.11R here) is closer to SPY's real spread and is reported alongside. S12 = +1 minute, +2 bp a side.
- Rule-change context: fixed shadow rule, no live setup involved; ledger changes inside the window do not apply.
