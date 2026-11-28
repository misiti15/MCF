# Month-end rebalancing rule (MEREB1) — FROZEN 2026-11-27 (forward shadow only)

*Educational only — not financial advice. Research only: no order, no config, no account runs this.*

Source: research/bdi/scout_1127 (MEREB1, scout FAIL 0 of 8, parked; NOTES.md asked for "a forward shadow from the
2026-11-30 month-end, <= 1 config"). The rule below is the scout's best long cell **L | th 0% | 14:00** of
`mereb_bt.py`, ported line for line into `shadow.py`. It is not re-tuned. Any change to anything below = a new rule
with a new freeze date and a fresh count (program config count +1 for this forward test).

Reproduction check (research/merebfwd_1127/REPORT.md): run on the cached 2024-10..2026-11-04 month-ends,
`shadow.evaluate` gives the scout's RECENT split exactly (n 7, +0.478R LIVE-L) when the half-day cap is switched off.

## Rule

1. **Event day** = the last trading session of a calendar month (next NYSE session is in a later month;
   offline list `mcf.execution.market_calendar.HOLIDAYS`, which must be extended past 2027 — the script refuses to run
   on a date beyond the list).
2. **Signal** S = SPY MTD − TLT MTD, each = close(prior session) / close(last session of the prior month) − 1, from
   daily SIP bars with `adjustment=all` (total return). Known before the open. **Long if S < 0** (equities lagged
   bonds month-to-date; balanced funds / pensions must buy equities into the close). No short side.
3. **Entry**: long SPY at the open of the 14:00 bar (market).
4. **Stop** = entry − 0.25 × ATR14, ATR14 = mean RTH true range of the 14 sessions before the event day (high/low/close
   from 1-minute RTH bars; prior close = the previous session's last RTH close). Stop-first each bar; fill at the stop,
   or at the bar open if a later bar opened through it. No target.
5. **Exit**: at the open of the first bar at/after 15:55. **Half day** (e.g. a Black-Friday month-end such as
   2025-11-28): flat at calendar close − 5 min (`mcf.data.bars.close_min`), which is before 14:00, so **no trade**;
   bars at/after the exchange close are dropped (`cap_at_close`). This is a correction, not a re-tune: the scout kept
   SIP after-hours prints on 2025-11-28 and "traded" 14:00-14:19 after the 13:00 close (−1.18R).
6. One trade per month-end. On S ≥ 0 month-ends the same trade is logged as a **control** (`ctrl_*` columns), never
   scored as the rule.

## Costs (always in)

**LIVE-L main** (research/primshorts_1126/cells_live.json, cost_R = a / stop_bps + b by price bucket × exit kind;
built from single-stock fills, so conservative for SPY whose spread is ~0.15 bp), **LR8 alongside** (1c + 1bp a side,
entry × time-of-day multiplier, +2c on a stop fill; closer to SPY's real cost). Stress **S12** = entry at the 14:01 bar
open with the stop level kept + 2 bp adverse a side on top of LIVE-L.

## History (scout, 2016-01..2026-11-04, locked block 2024-11-01..2025-02-28 excluded, 124 month-ends)

n 44, avg +0.051R LIVE-L (gross +0.280, LR8 +0.186), t 0.26, avg w/o best day −0.047; EARLY 2016-22 −0.415 (n 28,
t −2.59), T2 2022-10..2024-09 +1.167 (n 9), RECENT +0.478 (n 7). Beats random non-event days (98th pct; those lose
~0.26R to costs). The 2022+ sign flip is post-hoc; this is why the rule is forward-only.

## Pass bar for a promotion write-up (stated up front, scored once)

Unit = one signal month-end (one trade). Scored on rows dated **2026-11-30 onward** (earlier rows are in-sample seed
rows, never scored) once the log holds **>= 12 signal trades** (S < 0 in ~35% of months → about 3 years):

1. avg R after **LIVE-L > 0** with **t >= 2.0** (one pre-specified test; LR8 reported alongside);
2. best-trade share of total R **< 50%** and avg R **without the best month-end > 0**;
3. avg R under **S12 > 0**.

All three → write it up for the owner (a DECISION; nothing enabled automatically). Any one missing → close the
question (logged; no re-tune on the same forward data). The S ≥ 0 control is reported, not tested.

**Harm stop**: from 6 signal trades on, cumulative LIVE-L R <= −4R or avg <= −0.40R → close the question.
**Time cap**: if 12 signal trades are not reached by 2030-12-31, score what is there and report INCONCLUSIVE.

## Run

    python research/forward/month_end/shadow.py --date YYYY-MM-DD    # after 16:15 ET; any non-month-end date = no-op
    python research/forward/month_end/shadow.py --score

Market data only (GET /v2/stocks/bars: daily SPY/TLT adjustment=all, SPY 1-minute split-adjusted). Idempotent: a
re-run replaces that date's row; a run before the session ends writes a 'pending' row that a later run replaces.
Rule-change context: shadow trades of a fixed rule; no ledger change applies.
