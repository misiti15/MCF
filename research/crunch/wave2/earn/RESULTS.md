Educational only — not financial advice.

# Wave 2 item 2 — RT-EARN: EARN-GO on 2-year earnings seasons — **FAIL**

Research only: no setup, config, exit or account change. Nothing committed by this stage (the Skeptic stage commits).
PLAN.md was written at 21:53Z, before any signal was built (sha256 b9ce0c20…a8bc3). The one score ran at 22:06:58Z.
**Configurations counted: 1** (EARN-GO-2Y). Controls (same-name random bar, non-earnings twin, bias diagnostic) are
reported but not counted. Locked block 2024-11-01..2025-02-28 was never read. cache_fresh was not used.

## The config (PLAN.md)
The archive's EARN-GO (P3 P6: n 121, +0.346R, earlier half +0.045R) was never committed as a config. This run uses
the most literal reading of its only written spec (evidence_archive 1e: with the gap, entries >= 09:50, ATR stop,
60-75 min cap) on the round-4 chassis:
- earnings reaction days (yfinance calendar, bmo = report day, amc = next session);
- ADV20 >= $30M, price >= $10, 3% <= |gap| < 20%, side = gap side, shorts ETB only;
- first HOLD bar 09:50-12:30, one entry per name-day, day cap 30;
- 0.5 dATR stop, time exit at 60 min, R per 0.5 dATR;
- costs: LR8 plus x1.5 before 10:30 on reaction days, short borrow 5/8 bp.

## Result: 446 sessions (E = 2024-10 + 2025-03..09, 170; L = 2025-10-01..2026-11-04, 276)
| | trades (/session) | win | avg R | w/o best day | best day (share) | total R | day-clustered t |
|---|---|---|---|---|---|---|---|
| **Pooled** | 1,110 (2.49) | 0.441 | **-0.070** | **-0.079** | 10-28-2026 +8.6R (n/a, total < 0) | **-77.7** | -2.44 |
| Earlier half E | 343 (2.02) | 0.429 | -0.047 | -0.062 | 07-31-2025 +4.8R | -15.9 | -0.99 |
| Later half L | 767 (2.78) | 0.446 | -0.081 | -0.094 | 10-28-2026 +8.6R | -61.8 | -2.27 |
| Long | 541 | 0.442 | -0.043 | -0.059 | | -23.3 | -0.92 |
| Short | 569 | 0.439 | -0.096 | -0.108 | | -54.4 | -2.45 |

**Bars (all four needed): 1 avg R > 0 — no. 2 w/o best day > 0 and share < 50% — no. 3 both halves > 0 — no.
4 t >= 2.0 — no (t is -2.44, i.e. reliably negative).** The C3-EARN planning number (+0.1R/trade) is missed by 0.17R.

### By earnings season (avg R, n, total R)
| Oct-24 | Apr-May-25 | Jul-Aug-25 | Oct-Nov-25 | Jan-Feb-26 | Apr-May-26 | Jul-Aug-26 | Oct-26..11-04 | off-season |
|---|---|---|---|---|---|---|---|---|
| +0.062 (53) +3.3R | -0.077 (134) -10.3 | -0.021 (110) -2.3 | -0.208 (130) -27.0 | -0.125 (166) -20.7 | -0.085 (160) -13.5 | -0.066 (167) -11.1 | +0.036 (85) +3.1 | +0.008 (105) +0.8 |

- Only 2 of 8 seasons are positive, and both are one-day-carried. Oct-24 is 96% one day (w/o best day +0.003).
  Oct-26 is 278% one day (w/o best day -0.080).
- Oct-26 is the season that overlaps the archive's live EARN-GO window (10-06..11-17). It is the same shape as the
  archive record: a small positive driven by a few big days. That fits the red team's E10 read: +0.045 earlier half,
  carried by 11-05 / 11-09.

### Diagnostics (not counted)
- Long E +0.059 (w/o best day +0.032, share 47%) turns into long L -0.089, so the side sign flips between halves.
  That is the same instability ULT-28 showed. No sub-slice survives both halves.
- Surprise agrees -0.035 (606) / disagrees -0.141 (418) / missing +0.025 (86, one-day-carried). An "agree" filter
  makes it less bad but still negative. ULT-28 28a (agree, t1s1) had already scored -0.048 on check.
- Gap 3-5% -0.056 / 5-10% -0.066 / 10%+ -0.100. Entry 09:50-10:25 -0.075 / 10:30-11:25 -0.035 / 11:30-12:30 -0.150.
- Exits: 764 by time, 346 by stop. Median hold 60 min.
- Bias diagnostic (signal-close fill, no surcharge, no borrow): -0.058. Costs are not what sinks it.
- Same-name random bar: +0.055. **Signal minus random = -0.125.** The HOLD timing is worse than a random bar on the
  same reaction-day names. This repeats ULT-28 (-0.092 check).
- Non-earnings twin (same rule, no report in RD-5..RD+1): -0.011 (5,079 trades). News makes the rule worse, not better.

## Prior exposure and caveats
- ULT-28 (round 4, 11-19 morning) had already scored a near neighbour, 28i (TX-45, 2 entries/name): fit -0.030,
  check -0.045. This result is not independent of that one. It confirms it at the archive's 60-minute cap.
- Survivorship: the universe is today's 1,226 names, which flatters longs. The ETB flag is today's.
- The calendar was fetched after the fact; rare date revisions are not modelled.
- The 2-year cache ends 11-04, so 11-05..11-18 (the archive's best EARN-GO days) are not in it.
- The archive's +0.346R came from live/what-if data spanning these rule changes (ledger): 10-28 Primary sizing,
  10-29 -2R latch + BAR90, 11-05 ROLL1, 11-12 LR8 after-cost R. W1 found 62% of pre-11-12 trades carry zero cost,
  so part of that figure is on a no-cost basis. This replay uses one fixed chassis throughout, so no rule change
  falls inside its window.
- C3-EARN was approved 11-18 (effective 11-19). RT-EARN put its start on hold the same evening, so EARN-GO has never
  traded live.

## Setups affected
None. EARN-GO is not running. No live setup changes. The earnings blackout (config `earnings_blackout_days: 4`,
owner 10-07) stays as it is for every setup.

## Proposal (owner decision)
**EARN-CLOSE:** do not start EARN-GO in Testing. Withdraw C3-EARN's blackout exception and leave the blackout
unchanged. Log the idea as parked in the backlog: 1 config, FAIL, with links to ULT-28 and this file.
Reply **"EARN-CLOSE yes"**, or **"EARN-CLOSE no"** to keep C3-EARN's half-size Testing start (not recommended).
- **Conflict check (owner rule 11-19):** this reverses part of an owner approval, **C3-EARN (2026-11-18)**.
  It is therefore asked, not acted on. It agrees with the standing blackout rule (owner 2026-10-07) and with
  RT-EARN (11-18).
- Optimistic next step: the one lead left is the archive's daily-level finding, after-hours reaction continuation
  (+0.68% net, t 2.77, n 890). It is a close-to-close / overnight effect, not intraday from 09:50. Under GUARDRAILS
  it is flagged here as an idea only; no time will be spent on it without the owner's yes.

Files: PLAN.md, code/rt_earn.py (reuses round4/ULT-28/bt.py), scores.json, trades.csv.gz (1,110 trades).
