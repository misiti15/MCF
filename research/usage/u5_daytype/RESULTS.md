Educational only — not financial advice

# U5 — Day-type specialists (USAGE PLAN item 5): RESULTS

**Verdict: 0 of 4 pass. No Testing-copy proposal.** One lead (S3, quiet-day VWAP-stretch long) goes on a
pre-registered forward watch. Configurations tried: **20** (12 scored as registered + 8 descriptive slices); bar
t >= max(1.5, sqrt(2 ln 12)) = 2.23. Costs in (LR8 engine model). Locked block not read. Plan: PLAN.md (committed
before scoring). Sources: FIT = 2-year backtest bars, 168 sessions 2025-06-02..2026-01-30; CHECK = Session replay
bars of the 31 live sessions 2026-10-06..11-17. Both are non-live sources (weight 0 under SRCV1).

## The problem being attacked (confirmed again)

Primary journal, 31 live sessions, day type from SPY open -> close (+-0.25%): down days +79.8R (9), quiet days -56.4R
(12), up days -89.1R (10). Primary is short-heavy (1,075 of 1,316 trades short). Rule changes inside this window
are listed in NOTES.md (latch 10-29, sizing 10-28, LR8 11-12, TEAM-6 11-11 and others) — they affect Primary's
journal R, not the bar tests below.

## Results (cue = the setup as registered; after costs)

| Setup | Sample | Trades | Avg R | Total R | t (day) | Avg R w/o best day | Best-day share | Worst day | No-cue avg R | Random avg R | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 DT-QD-FBD-long (quiet-day failed breakdown) | fit | 563 | -0.253 | -142.2 | -4.62 | -0.274 | — | -23.9 | -0.193 | -0.148 | |
| | check | 79 | +0.049 | +3.9 | 0.23 | -0.176 | > 100% (best day 14.3R vs total 3.9R) | -7.7 | -0.114 | +0.127 | FAIL |
| S2 DT-QD-FBO-short (quiet-day failed breakout) | fit | 587 | -0.272 | -159.6 | -3.94 | -0.294 | — | -32.6 | -0.158 | -0.261 | |
| | check | 85 | -0.502 | -42.7 | -5.72 | -0.502 | — | -17.0 | -0.168 | -0.443 | FAIL |
| S3 DT-QD-VWAPSTRETCH-long (quiet-day stretch below VWAP) | fit | 388 | -0.215 | -83.6 | -1.36 | -0.314 | — | -30.3 | -0.257 | -0.260 | |
| | check | 37 | +0.732 | +27.1 | 3.42 | +0.453 | 77% (1 day) | -3.5 | -0.091 | +0.333 | FAIL (fit) |
| S4 DT-UP-VWAPPB-long (up-day leader VWAP pullback) | fit | 2,352 | -0.196 | -460.0 | -3.95 | -0.214 | — | -28.0 | -0.201 | -0.146 | |
| | check | 509 | -0.211 | -107.6 | -1.41 | -0.284 | — | -51.6 | -0.143 | -0.178 | FAIL |

Full table incl. no-cue and random rows: u5_results.csv; verdicts: u5_verdicts.csv; per-day: u5_check_days.csv.

## Per-setup effect on Primary's losing days (check sessions, cue version)

| Setup | Active days | Corr with Primary day R | Primary red days it traded | Green / red on them | Its R those days | Primary R those days |
|---|---|---|---|---|---|---|
| S1 | 4 | -0.82 | 3 | 2 / 1 | +7.6 | -43.0 |
| S2 | 4 | +0.73 | 3 | 0 / 3 | -38.7 | -43.0 |
| S3 | 4 | -0.13 | 3 | 3 / 0 | +30.6 | -43.0 |
| S4 | 18 | -0.25 | 15 | 5 / 10 | -44.2 | -186.9 |

Improve / worsen count on Primary's red days: 2 setups help (S1 small, S3), 2 make them worse (S2, S4). Overlap with
Primary's live symbol-days 0.6-2.7%; with L3-gap-slope-fromopen-FD 0% (the protected setup is untouched).

## Why they failed (honest read)

1. **No gross edge in the 2-year fit.** Gross avg R before costs: S1 -0.126, S2 -0.142, S3 -0.055, S4 -0.056
   (u5_cost_drag.csv). The day-type cue did not create an edge where the plain pattern had none: the no-cue versions
   are also negative in both samples (-0.09 to -0.26R).
2. **Cost drag from tight structural stops.** Median stop = 0.14 ATR, so costs = 0.10-0.18R per trade. Mean-reversion
   inside a quiet range has small targets and small stops, which is exactly where the fixed per-share costs bite.
3. **The point-in-time cues are only mildly informative.** QUIET cue days were realized quiet (09:50 -> close) 54% of
   the time vs a 45% base rate in fit (6 of 11 in check); UP cue days were up 48% vs 31% base (10 of 18 in check). A
   good share of cue days turn into the opposite day — the same instability P2 found for switches.
4. **S4 random entries are about as bad (-0.146 fit / -0.178 check)**: buying up-day leaders on a VWAP test is no
   better than buying random names at that minute.

## What can be salvaged (lead, not a pass)

- **S3 quiet-day VWAP-stretch long** is the only setup positive in check (+0.732R, 37 trades, 3 of 3 Primary red
  days green, t 3.42) and its cue beats its no-cue version in BOTH samples (fit -0.215 vs -0.257; check +0.732 vs
  -0.091). But fit is negative (-0.215, t -1.36), check is 4 sessions with a 77% best-day share, and the random
  control on the same days was also positive (+0.333) — the check days were simply good for longs. It fails the
  pre-registered rule.
- Descriptive slice (post-hoc, not a verdict): trades whose stop was >= 0.25 ATR were better for S3 (fit +0.115,
  43 trades; check +0.344, 5) and S2 (fit +0.156, 26). Small n, chosen after seeing data.

## Decision codes

| Code | Proposal | Needs |
|---|---|---|
| U5-NONE | No Testing copy from item 5 (0 of 4 pass). Nothing deployed; no config touched. | — (information) |
| U5-WATCH-S3 | Forward watch, pre-registered now, NO changes: score S3 exactly as registered on the next 20 unseen live sessions (Session replay of 11-19 onward). Pass = the PLAN.md check rule on those sessions. Also one separate pre-registered variant S3-R25 (single change: minimum stop 0.25 ATR instead of 0.08) scored on the same unseen sessions. Configs +2 -> 22. If either passes, it becomes a Testing-copy proposal then. | ROUTINE (research only) |
| U5-NEXT | For the next day-type round: build entries with wider stops (>= 0.25 ATR, cost drag <= 0.06R) and day-type cues measured at 10:30 rather than 10:00, and start from patterns with a positive gross no-cue edge in the 2-year fit — the day-type cue should sharpen an edge, not create one. | ROUTINE |

Every number above: per trade R = net P&L per share / |entry - stop|, after LR8 costs; bar tests, not live trades.
