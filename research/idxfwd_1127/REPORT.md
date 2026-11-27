# IDXFWD-1127 — forward shadow for the two index open-dip leads (BUILT)

**Educational only — not financial advice.** Research only: a journal-only script, not runner code. No change to
config/, setups, exits, assignments.json, decisions.json or the ledger. Rules frozen and pre-registered in
`research/forward/idx_dip/RULE.md` (commit 5db16f3d6e, made before the backfill was scored).
**Configurations: 2** (frozen copies of study cells, no new search). Cumulative program N ~9,300 -> ~9,302.

## In plain words

- We now have a daily forward log for the two index leads from waves 3 and 4:
  **IDX6** (QQQ down 1.5% or more from the open by 09:55 -> buy TQQQ on a 20% bounce, 1R trail) and
  **IWM45** (IWM down 0.75% or more by 09:45 -> buy TNA on a 20% bounce, 1R trail).
- The script re-creates the study exactly. On the cached FIT and CHECK history it gives the same trades and the same R
  as research/idxdip_1127 (IDX6 FIT +4.293R and CHECK +0.015R, one trade each; IWM45 FIT 10 trades at +1.148R and
  CHECK 9 trades at +0.261R). So the forward numbers really are these two rules.
- **Backfill 2026-11-05..11-27 (16 sessions, 11-27 a half day): 5 trades on 3 days, +1.43R in total after LIVE-L.**
  IDX6 2 trades, +0.63R and +1.48R, avg +1.06R. IWM45 3 trades: -1.10R, -1.12R, +1.54R, avg -0.23R. Book avg +0.29R
  per trade, day t 0.37. One day (11-25) carries more than all of it (best-day share 211%; avg w/o best day -0.53R,
  corrected 11-27 from -0.40R: see Fixes).
  With +1 min entry and +2 bp a side: +0.18R avg.
- **That is 3 of the 15 signal days the pass bar needs.** Nothing can be concluded yet. IDX6 fired twice in three weeks,
  more than its ~1 a year since 2023, because November 2026 has been very volatile (QQQ -5% on 11-20, swings of 2-3%
  most days). Expect ~12 signal days a year in calmer markets, so the bar is about a year away.
- Pass bar (frozen): >= 15 signal days; book avg R > 0 after LIVE-L with day-clustered t >= 2.0; best-day share < 50%
  and avg R w/o best day > 0; S12 avg > 0. Harm stop from 8 signal days (cumulative <= -6R or avg <= -0.40R). Time cap
  2028-06-30, then INCONCLUSIVE.
- **Daily trigger: the forward-logs trigger needs one added line** (after 16:15 ET):
  `python research/forward/idx_dip/shadow.py --date $(TZ=America/New_York date +%F)` (and `--score` when reporting).

## Backfill trades (LIVE-L main, LR8 alongside, S12 stress)

| date | rule | index low by T | entry (ET) | entry | stop % | exit | kind | R gross | R LIVE-L | R LR8 | R S12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-05 | IWM45 | -0.81% | 09:54 | 58.52 | 1.16 | 10:05 | stop | -1.00 | -1.10 | -1.09 | -1.16 |
| 2026-11-23 | IDX6 | -2.14% | 09:50 | 48.29 | 2.63 | 10:54 | trail stop | +0.69 | +0.63 | +0.65 | +0.06 |
| 2026-11-23 | IWM45 | -1.09% | 09:40 | 47.60 | 0.88 | 09:44 | stop | -1.00 | -1.12 | -1.16 | -0.41 |
| 2026-11-25 | IDX6 | -1.52% | 09:50 | 40.15 | 1.90 | 10:08 | trail stop | +1.56 | +1.48 | +1.49 | +2.13 |
| 2026-11-25 | IWM45 | -0.84% | 09:47 | 45.86 | 0.81 | 10:01 | trail stop | +1.67 | +1.54 | +1.49 | +0.28 |

Other sessions: 26 rule-days with no dip deep enough by the check time, 1 with a dip but no bounce in the window
(no row is dropped). 11-26 (Thanksgiving) has no bars. 11-27 (13:00 close): no signal; the half-day exit is 12:55
(after the fix below; before it, the script would have held to 15:55).

| | trades | days | avg R LIVE-L | t (day) | best-day share | avg w/o best day | LR8 | S12 |
|---|---|---|---|---|---|---|---|---|
| Book | 5 | 3 | +0.29 | 0.37 | 211% | -0.53 | +0.28 | +0.18 |
| IDX6 | 2 | 2 | +1.06 | – | 70% | +0.63 | +1.07 | – |
| IWM45 | 3 | 3 | -0.23 | – | – | -1.11 | -0.25 | – |

History for comparison (idxdip_1127, 2016-2026, LIVE-L): IDX6 n 16, +1.15R; IWM45 n 144, +0.24R.

## Rule-change context

These are shadow trades of fixed rules; no live account trades them and no ledger change applies to them. The live IDX
setups (IDX1-IDX5) and the 11-17..11-25 live rule changes are separate (research/wave3_1127/SUMMARY.md).
BDI 11-27 context: today's longs-vs-shorts gap is unrelated; neither rule fired on 11-27.

## Fixes (2026-11-27, after a skeptic review; the frozen rule in RULE.md is unchanged)

Two implementation bugs, both fixed in `shadow.py`; RULE.md already says "half days: close - 5 min", so the rule did
not change and the freeze date stands. Configurations: still 2.

1. **Half-day exit.** On a 13:00 close, SIP prints after-hours trades until 16:00, and the script's fixed 09:30-15:59
   window kept them, so its "last bar close - 5 min" rule put the flat at 15:55 (after hours) instead of 12:55. On
   11-27 the fetched bars ran to 15:59 for all four symbols (QQQ 177 bars after 13:00). Fix: the exchange close comes
   from the market calendar (`mcf.data.bars.close_min` -> `market_calendar.close_minutes`: PAST_EARLY_CLOSES /
   Alpaca calendar / EARLY_CLOSES), bars at or after it are dropped (`cap_at_close`), and the exit is
   min(15:55, close - 5 min, last bar close - 5 min). "Session finished" is now close + 15 min, not a fixed 16:15.
   **Backfill effect: none.** No backfill trade was open at 12:55 on a half day (11-27 had no signal), so
   forward.csv is byte-identical after the re-run (re-run twice: same md5, idempotent). `--verify` still matches the
   study exactly (IDX6 FIT +4.293 / CHECK +0.015; IWM45 FIT n 10 +1.148 / CHECK n 9 +0.261).
2. **Avg R without the best day.** The best day's R was removed but only one trade left the count. Fix: all of that
   day's trades leave the count. Book: (1.43 - 3.03) / 3 = **-0.53R** (was -0.40R = / 4); S12 -0.50; IDX6 +0.63 and
   IWM45 -1.11 unchanged (one trade on their best day). The pass bar needs this > 0 either way, so no verdict changes
   (WAITING, 3 of 15 signal days).

**The study engine (research/idxdip_1127/idx_sim.py) had the same half-day bug**, and half days were study days: 19
sessions per index pair (2016-11-25 .. 2025-12-24; the 2024-11-29 and 2024-12-24 half days are in the locked block and
were never read), and the data carry after-hours bars on them (e.g. QQQ 2018-12-24: 134 bars after 13:00). Fixed the
same way (`cap_at_close` + close - 5 min; a local list of the 2016-2023 NYSE half days, since PAST_EARLY_CLOSES starts
in 2024). Re-ran only the affected sessions (all 40 configs, all 19 half days per pair): 36 trade rows before and
after (18 BASE + 18 S1, on 2018-12-24 and 2021-11-26 only), **every one identical** (max |gross diff| 6e-17, same
entries, same exit minutes). All of them stopped out by 11:15, before any 12:55 flat, and the change cannot touch a
regular day. Neither frozen rule (G1 QQQ 1.5% 09:55, G1 IWM 0.75% 09:45) traded on a half day. **Delta: 0 on every
study number; results.json, REPORT and the verdicts of idxdip_1127 stand.**

## Files

- `research/forward/idx_dip/RULE.md` — frozen rules, costs, pass bar, harm stop, time cap (the pre-registration).
- `research/forward/idx_dip/shadow.py` — `--date`, `--from/--to` (backfill), `--score`, `--verify`. GET-only market data
  (mcf.replay.store._fetch_bars); upserts by date (idempotent); locked block asserted never read.
- `research/forward/idx_dip/forward.csv` — the log (one row per session per rule, no-signal days included).
- `tests/test_idx_dip_shadow.py` — 4 synthetic-session tests (signal + trail + costs, no-signal / IWM window,
  half-day exit at close - 5 min, idempotent upsert + score + lock assert; since the 11-27 fixes also: half day with
  after-hours prints to 15:59 flat at 12:55 (2025-11-28, 2024-07-03) vs 15:55 on a regular day, close override +
  session cap, w/o-best-day count). `pytest -q tests/test_idx_dip_shadow.py`: 8 passed (the 4 new ones fail on the
  pre-fix script).
- `research/idxfwd_1127/PREREG.md` — pointer + config count.
