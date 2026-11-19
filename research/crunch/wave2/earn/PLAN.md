Educational only — not financial advice.

# Wave 2 item 2 — RT-EARN: EARN-GO on 2-year earnings seasons (PRE-REGISTERED, written before any scoring)

Owner decisions this tests: C3-EARN (approved 11-18, EARN-GO in one Testing account at half size, blackout exception
for this setup only) and RT-EARN (approved 11-18 ~19:45 ET: hold EARN-GO's start until one pre-registered 2-year
earnings-season test). Research only: no setup, config, exit or account change. Configurations counted: **1**.

## What "EARN-GO" is here
The archive's EARN-GO (P3 P6: n 121, +0.346R, earlier half +0.045R) was never committed as a config
(docs/live/decisions.json: "pre-registered config not in the repo"). The only written description is
evidence_archive.md sec. 1e / item 4: **with the gap, entries >= 09:50, ATR-based stop, 60-75 min cap**, on earnings
reaction days. The one config below is the most literal reading of that text on the round-4 chassis
(research/ultimate_1119/round4/PLAN.md sec. 2; event table = modules/ULT-28.py `reaction_days()`).

## The one config: EARN-GO-2Y
- Events: earnings_yf.parquet (sha256 b80cdc46…e0dc). RD = report date (bmo) or next session (amc); dmh/unknown out;
  repeats within 10 sessions keep the first. Events with RD in the locked block dropped.
- Universe: RD names, ADV20 >= $30M, price >= $10, cost_r <= 0.08, 3% <= |gap| < 20%. Side = sign(gap).
  Shorts only easy-to-borrow (today's flag); no leveraged/inverse ETFs (none are RD names).
- Entry: the FIRST 5-min decision bar in 09:50-12:30 where the round-4 HOLD trigger holds (close on the gap side of
  VWAP; side x fromOpen >= 0; RSI5 <= 85 long / >= 25 short); surprise ignored. Fill = open of the next 1-minute bar.
  **One entry per symbol-session** (gap-and-go is a one-shot). Day cap 30 (first by time, ADV20 desc).
- Exit: catastrophic stop 2u = 0.5 x daily ATR from the decision close (stop first; gap-through at the worse of open
  and stop; +2c); no target; **time exit at 60 minutes** (low end of the archive's 60-75 cap); flat 15:50.
  R per 2u (0.5 dATR).
- Costs (LR8 + round-4 bias fixes): LR8 entry/exit cost with the time-of-day multiplier; x1.5 entry and exit cost
  before 10:30 on reaction days; short borrow 5 bp of notional (8 bp under $20).

## Data and windows
- Lab frames /home/user/MCF/research/history2y/data/frames + context; 1-min /home/user/MCF/data/cache_hist/1Min.
- Earlier half E = 2024-10 + 2025-03-01..2025-09-30; later half L = 2025-10-01..2026-11-04 (cache end).
- Locked block 2024-11-01..2025-02-28 never read (pyarrow filters + no_locked asserts on frames, events, 1-min bars).
- cache_fresh (2023-24) is NOT used.

## Prior exposure (stated up front)
ULT-28 (round 4, 11-19) scored a near neighbour on both halves: 28i = G3 HOLD S-any TX-45, max 2 per name:
fit -0.030R, check -0.045R. This config differs in cap (60 vs 45 min) and lots (1 vs 2 per name); it is not
independent of that result. It is run because the owner asked for this exact test and the archive text says 60-75 min.

## Pass bar (RT-EARN "job's bar" = the split EARN-GO failed, plus the standing reporting rules)
PASS only if ALL of:
1. pooled avg R > 0 after costs;
2. avg R without its best day > 0 and best-day share of total R < 50%;
3. avg R > 0 in BOTH halves (E and L) — the split C3-EARN failed;
4. day-clustered t >= 2.0 (single pre-registered config; the round-4 job's cumulative-try bar 3.716 is shown as context).
Otherwise FAIL (PARTIAL only if 1-3 hold but 4 does not). C3-EARN planning number (+0.1R/trade) reported alongside.

## Reported (not counted)
Per earnings season (Oct-24, Apr-May-25, Jul-Aug-25, Oct-Nov-25, Jan-Feb-26, Apr-May-26, Jul-Aug-26, Oct-26), long/short,
gap bucket, entry time, exit mix, same-name random-bar control, non-earnings twin (same rule, no report in RD-5..RD+1).
Affected setups: none of the live setups change (EARN-GO is new; the blackout stays for every other setup).
