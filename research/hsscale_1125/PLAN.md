Educational only — not financial advice.

# HARDSTOP-SCALE pre-registration (written 2026-11-25, before any configuration was scored)

Owner 2026-11-24: "HS wait for the scaling version ... I don't want to stop the account prematurely, but I want it to not
crash either due to a bug or glitch. I really want to lean into the setup caps too." Research only: no config, ledger,
setup or account change; nothing committed.

## Engine (bench) — hardstop_1123 engine generalised to N setups
- Lots: bench10 trade lists (LR8 research costs + 1.2 bp borrow, 1-minute exits, live module masks / windows / refire).
  4 Primary setups from scratchpad pyramid/L1 (kind_ == prim); GEN-261029-06 from pyramid/S/work; L3-lowdist, L3-rsi5hi,
  RW6-FD, RW7-FD generated tonight with bench10 unchanged (hsscale/gen_extra.py; only SETUPS replaced).
- Book (Primary rules, one minute-by-minute simulator): price >= $5, shorts ETB >= 0.9, per-setup open-lot cap 30,
  <= 3 lots per symbol per setup, account slot cap 77 open lots (live max_concurrent_positions; new vs hardstop_1123,
  binds only for the larger lineup), burst brake 30 / 10 min per setup, per-setup -2R latch on closed cost-R,
  -20R account halt (no new entries) on closed + open cost-R. Point in time as hardstop_1123 (entries see minute m-1).
- Reproduction: the 4-setup base without the slot cap must match hardstop_1123's base (-1,701R / 873 sessions) to
  within rounding of the lot source; stated.
- Periods FIT / T2 / CHECK as hardstop_1123; 2024-11-01..2025-02-28 never read (asserts).
- Each base run records, per day and minute, closed + open R of the account and of each setup (marks less the
  market-exit cost). A flatten stop at level X on day d = the first minute the account path <= -X; the day's R is the
  path value at that minute (all lots flattened at that minute's close, cost in) and per-setup R likewise. This is
  identical to re-simulating with the stop layered on (the stop changes nothing before it fires); checked against
  a direct re-simulation for A12 on the 4-setup lineup.

## Lineups
- P4: NM-ETF, RW5, RW3, L3-fromopen (current Primary).
- P9: P4 + L3-gap-slope-lowdist-FD, L3-gap-slope-rsi5hi-FD, RW7-gapdn-bounce-early-short-FD, RW6-ns2-up3-short-FD,
  GEN-261029-06 (hypothetical larger Primary; not a proposal to move them).
- Latch variants: LAT (all setups -2R latch, as live) and GDX (gap-down short family — L3-*, RW3, RW5, RW7 — exempt
  from the -2R latch; the backlog remedy). 4 base runs: P4-LAT, P4-GDX, P9-LAT, P9-GDX.

## Layer 2 rules (scaled disaster stop; flatten + no new entries for the rest of the day when the account's closed +
## open R <= -X_w; X_w recomputed weekly from the lineup's own trailing simulated sessions)
Calibration: before each ISO week w, the previous up to 250 bench sessions of the SAME lineup / latch variant (base
run, no stop), minimum 120 (earlier weeks = warm-up, not scored for any rule incl. A12 / none, so all rules share one
scored set). Trough_d = the day's minimum closed + open R path; Final_d = the day's closed R.
| id | X_w |
|---|---|
| A12 | 12 (fixed, hardstop_1123) |
| A3N | 3 x N setups (P4 12, P9 27) — the simple linear scale |
| Q1 / Q2.5 / Q5 | -(q-th percentile of Trough over the trailing window), q = 1 / 2.5 / 5 % |
| K3 / K4 | k x sigma(Final over the trailing window), k = 3 / 4 (portfolio sigma: correlation included) |
| Q2.5N | Q2.5 for the flatten, plus no new entries from 0.6 x X_w (two-stage) — needs a re-simulation |
Floor / ceiling for every scaled rule: X_w clipped to [2.5 x N, 8 x N] R (P4 [10, 32], P9 [22.5, 72]).
Configurations: 7 rule ids + 1 latch variant = 8 (x 2 lineups, reported separately). Bar for any claim that a rule
IMPROVES R: max(1.5, sqrt(2 ln 8)) = 2.04 per lineup; lineage with hardstop_1123 (17) + rules_1122 / etfstop_1123
loss rules: N ~ 67 -> 2.90. Tail insurance is not edge and is reported as such.

Metrics (per lineup x latch variant x rule, FIT / T2 / CHECK / all scored sessions): fires (days, per year), worst day,
days <= -6R, dR vs none, R saved on fired days that ended worse than the fire level vs R lost on fired days that
recovered (base final > -X), dR_neutral (dR + base avg R per lot x lots entered after the fire minute; hardstop_1123's
approximation) and dR_p10 (book at +0.10R per lot), per-setup dR (setups better / worse and by how much — Remedies
rule), day-clustered t, X_w path over time (min / median / max per lineup).

Decision rule (fixed now). A Layer-2 rule is RECOMMENDED if, on BOTH lineups and both latch variants:
(1) fires <= 12 days / yr pooled (A12 fires ~45 / yr on P4), (2) worst day better than none in each period where it
fires, (3) dR_neutral per yr >= -5R (it must not cost much when the book has no edge), (4) on P9 it fires
at most half as often as A12 (shows it does not stop the larger lineup prematurely). Among passing rules, prefer the
fewest R lost on recovered days, then the simplest. If none passes, report the best and say No.
Latch question (GDX vs LAT): reported descriptively per setup (the bar 2.04 / 2.90 applies to any "better" claim).

## Layer 1 (glitch / bug failsafe) — measured, not optimised
Inventory first (risk.py, runner.py, kill.py, watchdog.py, outage.py, reconcile.py, config). Candidates:
| id | rule |
|---|---|
| V1 | account closed + open R falls >= max(8, 0.5 x X_w) R within 2 minutes |
| V2 | account closed + open R falls >= max(12, 0.75 x X_w) R within 10 minutes |
| E1 | open lots > 1.5 x the lineup's trailing p99 of daily peak open lots (bench), or > 77 slots |
| E2 | one symbol carries > 6 open lots across setups (2 x the per-setup 3-lot cap) |
| B1 | one setup opens >= 10 lots within 5 minutes (burst; current brake = 30 / 10) |
| M1 | >= 25% of open lots unmarked (no bar / no stop) for >= 3 consecutive polls (blind book) |
Measured on: (a) live poll snapshots (polls/<date>/*.jsonl.gz mtm, every account, from the first day they exist; the
R-velocity uses rr + ur, ur without exit costs), (b) live trades (entry times, all accounts 10-06..11-24) for B1,
(c) the bench paths (P4, P9) for V1/V2/E1/E2/B1, (d) the named incidents: 11-05/06 MTUM phantom, 11-20 NM-ETF 12-lot
burst, 2026-07-29 14:00 bench shock, 11-10 breadth day. Aim: fires on the incidents, ~0 on ordinary bad days.
Layer-1 action: no new entries + alert on first fire; flatten only on V1 (a shock) or when combined with a Layer-2 hit.
