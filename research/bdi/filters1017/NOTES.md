# filters1017: the two swarm1013 execution filters, revisited for Primary (2026-10-17)

*Educational only — not financial advice. Backtests (open two-year history), paper fills (Primary, Testing 1,
Testing 2) are labelled separately. Nothing here is a live-money result. The rule-19 locked block
(2024-11-01..2025-02-28) was never loaded. No file under config/ or mcf/ was changed.*

Filters under review (from `research/bdi/swarm1013/backtest/NOTES.md`):
- **K25** — skip an entry when the fill is already >= 0.25 lab R toward target (P = side x (fill - ref) / R).
- **SIR 15m** — skip a short when its ref-anchored stop sits below the high of the last 15 minutes (3 five-minute bars
  ending at the signal bar).

## Failures first / verdict
- **K25: NO for Primary.** Backtest delta +0.0037R/trade, t 2.61 — below the try-count bar 3.49 (and below 2.73
  even for this study alone). Kept-minus-skipped t 1.37; versus a random skip of the same 2.5% share only
  +0.002R. Paper fills do not show the skipped trades are worse: Primary since 10-14 skipped -0.18R vs kept -0.30R;
  all accounts pooled skipped -0.16R vs kept -0.14R.
- **SIR 15m: NO for Primary.** Backtest delta +0.0044R/trade on current Primary shorts, t 1.67 (bar 3.49);
  kept-minus-skipped t 0.99; versus random +0.002R. On the three newest setups (RW3-FD, RW5-FD, MF3-FD) it almost
  never fires (0.07-0.21% of trades) and the deltas are about zero or negative. Paper: Primary since 10-14 has
  4 triggers, all GTLB on 10-14 (one name, one day); Testing 2 contradicts it (skipped -0.05R vs kept -0.23R).
- Both remain where swarm1013 routed them (Testing 1 / backlog). Neither is a cost-free improvement big enough
  to show up in a week of Primary fills.

## (a) Original numbers (swarm1013, N = 402, bar t >= 3.46)
| cell | delta (t) | kept-skip (t) | vs random skip | share skipped |
|---|---|---|---|---|
| E1 K25 ALL (11 setups incl. NS2/NS3) | +0.004 (2.16) | +0.088 (1.2) | +0.003 | 3% |
| E6 SIR 15m SHORTS | +0.009 (1.80) | – | – | 1-5% |
Neither cleared 3.46; swarm1013 itself routed both to Testing 1, not Primary.

## (b) Paper fills (journals on origin/mcf-data*, run_id = 1, as of 2026-10-16 close)
Method: trades joined to signals by broker order id; ref, stop, target from `signals`; fill = `trades.entry`;
lab R = |stop - ref| / stop-multiple of the setup's GEOM (DN = 1 assumed for setups without a lab module:
heat_fade, orb20, exhaustion, LIQ, CWT). SIR uses Alpaca SIP 1-minute bars (read-only fetch) for the 15 minutes
before the signal's 5-minute bar close. Outcome = journal `r_multiple` (per-trade R) and `pnl_adj` (fill-realism
adjusted $). SE is day-clustered; with 3-5 days these are anecdotes, not tests.

| account / window | filter | triggered | skipped: avg R, sum R, $adj | kept: avg R |
|---|---|---|---|---|
| Primary 10-14..10-16 (all 95 trades) | K25 | 9 (9.5%) | -0.18, -1.59R, -$87 | -0.30 |
| Primary 10-14..10-16, current setups only (51) | K25 | 6 (11.8%) | +0.03, +0.18R, -$37 | -0.07 |
| Primary 10-14..10-16 shorts (89) | SIR 15m | 4 (4.5%) | -0.36, -1.44R, -$17 | -0.29 |
| Primary 10-14..10-16 current-setup shorts (45) | SIR 15m | 4 (8.9%) | -0.36, -1.44R, -$17 | +0.01 |
| Primary all (10-06..10-16, 311) | K25 | 18 (5.8%) | -0.03, -0.61R, -$89 | -0.17 |
| Primary all shorts (247) | SIR 15m | 11 (4.5%) | -0.46, -5.05R, -$71 | -0.19 |
| Testing 1 (10-09..10-16, 1,495) | K25 | 81 (5.4%) | -0.39, -31.7R, -$430 | -0.11 |
| Testing 1 shorts (1,081) | SIR 15m | 23 (2.1%) | -0.41, -9.4R, -$90 | -0.07 |
| Testing 2 (10-12..10-16, 2,280) | K25 | 297 (13.0%) | -0.10, -30.7R, -$412 | -0.16 |
| Testing 2 shorts (532) | SIR 15m | 131 (24.6%) | -0.05, -6.4R, -$71 | -0.23 |
| all three pooled (4,086) | K25 | 396 (9.7%) | -0.16, -63.0R, -$931 | -0.14 |
| all three pooled shorts (1,860) | SIR 15m | 165 (8.9%) | -0.13, -20.9R, -$232 | -0.13 |

Read: Testing 1 favours both filters, Testing 2 contradicts both, Primary is too small and concentrated
(the 4 SIR triggers are one symbol on one day; the K25 triggers on current setups were slightly *better* than kept
trades). Pooled across ~4,100 paper trades there is no selectivity for either. Testing 2's CWT setups use other
geometries, so its R units are not the lab R; Testing 1 and Primary are the comparable accounts.

Primary K25/SIR triggers 10-14..10-16: GTLB MF3 (K25+SIR, stop -1.04R), GTLB MF2 (SIR, stop -1.20R),
GTLB MF4 (SIR, target +0.34R), SKYD MF4 (SIR, target +0.46R), CRWV/ETHA/ARM NS2 (K25: +0.27/-1.02/-1.01R),
TSLL NS5 (K25, -1.02R), QSR MF5/MF3/MF3-FD (K25, +0.55/+0.52/+0.52R), FTNT MF3-FD (K25, +0.65R).

## (c) Re-score on the open history for the CURRENT Primary list (backtest)
Setups (config/default.yaml enabled): MF1-5, NS1, NS4, NS5, RW6G1, RW3-FD, RW5-FD, MF3-FD. 426 open sessions
2024-10..2026-10-07, rule-19 block excluded. Same pipeline and live fill model as swarm1013 (B1: next 5-minute
bar open + half-spread, bracket at the signal close, stop-first, gaps fill at the open, production costs incl.
3x extended tier). Signal counts reproduce swarm1013 exactly for the 9 shared setups; 5-minute close parity 100%.
Trades on the same symbol-day by several setups (e.g. MF3 and MF3-FD) are counted per setup, as Primary trades them.

**Configurations tried here: 41** (13 B1 reference cells, K25 x 13 scopes, K50 x 1, SIR15 x 11, SIR30 x 1,
2 holdout-window-excluded diagnostics). Lineage count 402 + 41 = 443 -> bar t >= max(1.5, sqrt(2 ln 443)) = **3.49**.

| cell | n | skipped | base exp | delta train / valid / open (t) | kept-skip (t) | vs random | ex-best-day | WF share | up / down |
|---|---|---|---|---|---|---|---|---|---|
| K25 ALL | 43,079 | 2.5% | -0.070 | +0.005 / +0.002 / +0.0037 (2.61) | +0.082 (1.37) | +0.002 | +0.003 | 0.82 | +0.005 / +0.002 |
| K50 ALL (neighbour) | 43,079 | 0.3% | -0.070 | +0.001 / +0.001 / +0.0012 (2.48) | +0.37 (2.06) | +0.001 | +0.001 | 0.59 | +0.002 / +0.002 |
| SIR 15m SHORTS | 41,330 | 3.0% | -0.072 | +0.007 / +0.001 / +0.0044 (1.67) | +0.077 (0.99) | +0.002 | +0.002 | 0.65 | +0.010 / +0.002 |
| SIR 30m SHORTS (neighbour) | 41,330 | 6.6% | -0.072 | +0.011 / +0.004 / +0.0076 (2.05) | +0.046 (0.86) | +0.003 | +0.004 | 0.77 | +0.019 / +0.001 |
| K25 ALL ex rule-2 holdout windows | 35,288 | 2.6% | -0.077 | open +0.0041 (2.48) | +0.081 (1.24) | +0.002 | | 0.79 | |
| SIR 15m SHORTS ex holdout windows | 33,894 | 2.9% | -0.079 | open +0.0051 (1.63) | +0.101 (1.11) | +0.003 | | 0.64 | |

Per-setup (diagnostic, all below the bar unless noted): K25 on MF4 +0.010 (t 3.61, MF4 base -0.10R), MF3-FD
+0.006 (3.22), NS4 +0.007 (2.02), RW3-FD +0.002 (0.88), RW5-FD +0.001 (0.77), RW6G1 -0.024 (-1.80; it removes
RW6G1's *better* trades), NS1 -0.002 (-1.97). SIR15 on RW6G1 +0.040 (3.35, 18 trades skipped, WF 0.13), MF4 +0.035
(1.54), MF2 +0.044 (1.70, but skips 61% of MF2 because its 0.5R stop usually sits in the range), RW3-FD +0.000,
RW5-FD -0.000, MF3-FD -0.000 (fires on 0.07-0.21% of their trades).

Only the K25/MF4 and SIR/RW6G1 per-setup cells clear 3.49 (K25/MF3-FD reaches 3.22). They are per-setup cells
that swarm1013 already rejected (MF4 loses; RW6G1 has 18 skips and is concentrated), so they are not a case for
a book-wide filter. The two pooled filters the owner asked
about fail the bar, and the skip-vs-random check shows most of each delta is just "skipping some of a losing book".

## Limitations
- The "rule-2 holdout windows" (Apr-Jun 2026, Sep 16-Oct 5 2026) sit inside the open history used by swarm1013 and
  here; a diagnostic without them is shown. Nothing was tuned; both filters were fixed in advance.
- 5-minute bar resolution; first signal per symbol-day per setup (no re-entries, no slot cap).
- Paper-fill R uses the journal's r_multiple; P for non-lab setups assumes stop = 1 R.

## Files
- `results.csv` — every cell of (c). `score.py`, `signals.py` — patched copies of the swarm1013 pipeline
  (bars.py unchanged apart from ROOT; scratch paths point at the session scratchpad). `live_check.py`,
  `fetch_bars.py` — paper-fill check (b) and the read-only Alpaca bar fetch.
