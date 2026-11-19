Educational only — not financial advice

# "Ultimate setup" overnight job (2026-11-18/19): all rounds

The owner asked (2026-11-18) for the best intraday setups MCF can build from everything it has learned. That means
many trades per session across the universe, long and short, any market, and a high avg R per trade **after costs**.
Entries from 09:50, flat by 15:50, holds of about 5-45 min. The owner also said: "Do not stop until promising results
show that would be expected to beat our current best setups", and "I don't want to force weak setups."

**Result after 4 rounds and 35 candidates: none beats the benchmark and none is TIER A in a robust way. Nothing was
deployed.** No account, setup, exit, YAML or ledger entry was changed.

## In plain words (layman summary)
1. We built 35 candidate setups over four rounds: price patterns, learned rankers, ETF dips, mega-cap dips, sector
   lags, clock patterns, cheap-cost universes, and finally earnings/news setups.
2. Each one was tuned only on the older part of the history (the "fit" half). The chosen version was written down and
   frozen **before** the newer part (the "check" half, 276 sessions, 2025-10-01..2026-11-04) was opened. It was then
   scored there once. Costs were always in, and shorts paid a borrow fee.
3. 25 of 35 lost money on the check half. Most of the others were about zero.
4. Volume was never the problem: many candidates traded 5-28 times a session. The problem is that, after costs, the
   starting point (a random entry in the same names) loses about 0.02-0.05R per trade. A good trigger only shrinks that
   loss.
5. The only edges that held up again out of sample are the narrow ones we already know: the late-afternoon ETF dip
   (WB4 / NM-ETF style, about +0.10R) and one-bar RSI collapses in very liquid stocks (about +0.12-0.14R). Both trade
   less than 1 time a session.
6. The best near miss, ULT-32 (those two edges pooled plus a wider dip leg), made +0.062R per trade on check (both
   halves positive), but only 1.7 trades a session, t 1.98 against a 3.72 bar. It also used check-half knowledge in its
   design. It is TIER B: not deployable.
7. ULT-20 met TIER A by the letter (+0.0075R, t 0.55). The skeptic downgraded it to B: the edge is about zero, the
   newer check half is negative, and it does worse than random trigger bars.
8. A second reviewer (the skeptic) re-scored the saved trades where they existed and upheld every verdict in rounds
   2-3. The remaining biases (today's symbol list, fills, light borrow fee) all make results look **better**, so they
   cannot rescue a failure.
9. Per the owner's "no weak setups", nothing was put into any account.
10. Next step worth trying (backlog, not a setup): a book of independent small edges (WB4 late dip + liquid RSI collapse
    + others found the same way), each kept at its own narrow scope, rather than widening one edge into a losing one.

## The bars (pre-registered in PLAN.md and each round's PLAN.md)
- **TIER A:** check avg R > 0, check avg R w/o best day > 0, fit avg R > 0, >= 2 trades/session on check, no
  look-ahead.
- **TIER B:** fit avg R > 0 and check avg R > -0.02. Near miss, next round only, never deployed.
- **BEATS BENCHMARK:** TIER A and check avg R > +0.0836, w/o best day > +0.0734, check total R/session > 0, worst
  day/trade-session >= -2.152, day-clustered t >= max(1.5, sqrt(2 ln N)).
- **Deploy rule for this job:** BEATS (skeptic-upheld), or TIER A only if clearly positive and robust (both check
  halves > 0 and > 0 without 2025-04-03..04-09). **No candidate met either.**
- Benchmark (benchmark/BENCHMARK.md, same pipeline): only ST7-FD (+0.084R) and NM-ETF-late-dip (+0.052R) are positive
  on the check half among current setups.

## Configurations counted (cumulative N)
| Round | Candidates | Configs | Cumulative N | t bar sqrt(2 ln N) |
|---|---|---|---|---|
| 1 | ULT-01..10 | 94 grid + 574 evidence scans (+14 later adds) | 682 | 3.61 |
| 2 | ULT-11..19 | 97 (incl. ULT-15's extra diagnostic) | 779 | 3.65 |
| 3 | ULT-20..27 | 101 + 1 (ULT-24 diagnostic) | 881 | 3.68 |
| 4 | ULT-28..35 | 115 | 996 (up to 1,012 if ULT-29's extra diagnostics count) | 3.72 |

Random-entry controls and non-earnings twins are reported, not counted.

## Every candidate (fit-selected config, scored once on check; R per unit of risk, LR8 costs in)

Columns: fit = fit half (rounds 2-4 rankers use walk-forward out-of-fold fit). "w/o best" = avg R without the best
day. "Share" = best day's share of total R (n/a when total < 0). t = day-clustered t on check. "vs random" = check
avg R minus a random entry on the same names, sessions and side with the same exit. Check halves = first / second
half of check sessions. The 2025-04-03..04-09 week lies inside fit only; dropping it never changes a check figure.

### Round 1 (details: RESULTS.md)
| # | Candidate | Side | Fit /sess | Fit avg R | Fit w/o best | Fit share | Check /sess | Check avg R | Check w/o best | Check halves | vs random | Tier | Skeptic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Gap-down pop fade | S | 3.46 | -0.047 | -0.060 | n/a | 6.26 | -0.003 | -0.008 | -0.012 / +0.005 | +0.066 | FAIL | upheld |
| 02 | Tape-flush washout | L | 2.03 | +0.129 | -0.001 | 101% (1 day) | 1.83 | -0.091 | -0.185 | -0.185 / +0.090 | +0.116 | FAIL | upheld |
| 03 | RSI-collapse dip, broad | L | 9.52 | -0.019 | -0.028 | n/a | 15.26 | -0.006 | -0.008 | -0.008 / -0.005 | +0.060 | FAIL | upheld |
| 04 | Down-tape pop fade | S | 0.44 | +0.023 | -0.034 | 221% (1 day) | 0.41 | -0.078 | -0.129 | -0.098 / -0.003 | -0.112 | FAIL | upheld |
| 05 | With-gap continuation | L+S | 13.05 | -0.011 | -0.019 | n/a | 20.61 | -0.003 | -0.006 | -0.029 / +0.018 | +0.007 | FAIL | upheld |
| 06 | Late morning-turn | L | 11.15 | +0.032 | -0.009 | 127% (1 day) | 14.45 | -0.091 | -0.099 | -0.095 / -0.086 | -0.029 | FAIL | upheld |
| 07 | PM volatile dip | L | 2.54 | -0.042 | -0.058 | n/a | 5.45 | -0.030 | -0.037 | -0.018 / -0.040 | +0.020 | FAIL | upheld |
| 08 | PM overbought roll-over | S | 0.34 | +0.052 | +0.027 | 76% (1 day) | 0.45 | -0.053 | -0.062 | -0.091 / +0.013 | +0.030 | FAIL | upheld |
| 09 | Failed VWAP reclaim | S | 1.01 | +0.067 | +0.012 | 85% (1 day) | 1.17 | -0.157 | -0.185 | -0.171 / -0.123 | -0.087 | FAIL | upheld |
| 10 | Regime-switch book | L+S | 14.8 | +0.004 | -0.005 | 231% (1 day) | 20.8 | -0.039 | -0.042 | -0.065 / -0.010 | -0.045 | FAIL | upheld |

### Round 2 (details: round2/ULT-*/RESULTS.md)
| # | Candidate | Fit /sess | Fit avg R | Fit w/o best | Check /sess | Check avg R | Check w/o best | Share | t | Check halves | vs random | Tier | Skeptic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | Learned ranker, stocks (ridge, 45 min) | 6.72 | -0.041 | -0.050 | 11.04 | -0.028 | -0.031 | n/a | -2.30 | -0.027 / -0.028 | +0.000 | FAIL | upheld (re-scored) |
| 12 | WB4 ETF dip, widened to 205 ETFs | 3.44 | +0.107 | +0.087 | 4.20 | -0.005 | -0.014 | n/a | -0.21 | +0.035 / -0.038 | +0.013 | B | upheld; WB4-list anchor +0.110 at 0.82/sess is post-hoc |
| 13 | ST7 RSI collapse, ADV $50M | 3.36 | -0.022 | -0.041 | 6.46 | +0.019 | +0.014 | 29% | 1.58 | -0.004 / +0.035 | +0.077 | FAIL | upheld |
| 14 | Common-core dip/fade, two-sided | 2.70 | -0.038 | -0.074 | 2.94 | +0.004 | -0.013 | 433% (1 day) | 0.10 | -0.049 / +0.065 | +0.028 | FAIL | upheld |
| 15 | Gated confluence (base gate) | gate closed | — | — | 0 (diag 8.68) | diag +0.001 | diag -0.001 | 234% | 0.09 | — | +0.053 (diag) | FAIL | upheld |
| 16 | Wide bracket / limit entries | 4.48 | -0.036 | -0.041 | 8.75 | -0.001 | -0.002 | n/a | -0.10 | -0.003 / +0.002 | +0.024 | FAIL | upheld; LMT not live-expressible |
| 17 | Sector-lag catch-up | 12.5 | -0.017 | -0.022 | 18.29 | -0.010 | -0.013 | n/a | -1.02 | — | +0.012 | FAIL | upheld |
| 18 | Cross-sectional momentum/reversal book | 26.7 | -0.025 | -0.027 | 28.54 | -0.021 | -0.021 | n/a | -4.63 | -0.020 / -0.021 | -0.001 | FAIL | upheld |
| 19 | Signed ranker, stable factors | 2.10 | -0.020 | -0.039 | 7.55 | -0.026 | -0.028 | n/a | -2.52 | -0.022 / -0.030 | +0.011 | FAIL | upheld |

### Round 3 (details: round3/ULT-*/RESULTS.md)
| # | Candidate | Fit /sess | Fit avg R | Fit w/o best | Check /sess | Check avg R | Check w/o best | Share | t | Check halves | vs random | Tier | Skeptic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | Event-conditioned ranker | 3.77 | +0.043 | +0.032 | 6.13 | +0.008 | +0.005 | 32% | 0.55 | +0.021 / -0.004 | +0.028 (base) / -0.026 (trigger bars) | A by letter | **downgraded to B**: no edge, 99% long, 2nd half < 0. Do not deploy |
| 21 | ETF ranker (EQB) | 3.21 | -0.044 | -0.049 | 5.74 | -0.012 | -0.015 | n/a | -1.15 | -0.004 / -0.019 | -0.015 | FAIL | upheld (re-scored) |
| 22 | WB4 list, 12:30-15:00 | 2.44 | +0.104 | +0.088 | 2.27 | +0.004 | -0.003 | 177% (1 day) | 0.11 | -0.001 / +0.008 | +0.020 | B | upheld (re-scored); 14:00-15:00 part +0.096 |
| 23 | Mega-cap one-bar RSI collapse | 0.09 | +0.326 | +0.225 | 0.28 | +0.139 | +0.104 | 28% | 1.75 | +0.219 / +0.072 | +0.197 | B | upheld (re-scored); far below 2/sess |
| 24 | Basket/mega bases + triggers (gated) | gates closed | — | — | 0 (diag 20.2) | diag -0.023 | diag -0.026 | n/a | -2.67 | — | +0.019 (diag) | FAIL | upheld |
| 25 | Cheap-cost universe, two-sided | 6.63 | -0.002 | -0.009 | 14.52 | -0.007 | -0.008 | n/a | -1.49 | — | +0.008 | FAIL | upheld (re-scored) |
| 26 | Trend-tape with-gap VWAP pullback | 5.72 | +0.068 | +0.054 | 7.84 | -0.045 | -0.053 | n/a | -1.36 | -0.060 / -0.031 | -0.114 | FAIL | upheld (re-scored) |
| 27 | Periodicity (clock slots) | 14.24 | -0.018 | -0.020 | 16.80 | -0.017 | -0.018 | n/a | -4.01 | -0.016 / -0.018 | -0.011 | FAIL | (own verdict; skeptic text truncated in hand-off) |

### Round 4: earnings / news / flow (details: round4/ULT-*/RESULTS.md)
Skeptic verdicts for round 4 were not part of this hand-off; the tiers below are each candidate's own pre-registered
verdict. None claims A or BEATS, so no deploy decision depends on a skeptic upgrade.

| # | Candidate | Fit /sess | Fit avg R | Fit w/o best | Check /sess | Check avg R | Check w/o best | Share | t | Check halves | vs random | Tier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 28 | Earnings-day continuation with the gap | 2.11 | -0.022 | -0.034 | 2.52 | -0.048 | -0.064 | n/a | -1.24 | -0.088 / -0.012 | -0.092 | FAIL |
| 29 | Earnings-day gated confluence | gates closed | — | — | 0 (diag 2.96) | diag -0.024 | diag -0.029 | n/a | -1.06 | -0.050 / -0.005 | — | FAIL |
| 30 | Day-after-earnings continuation | 2.84 | -0.003 | -0.010 | 3.94 | -0.034 | -0.040 | n/a | -2.14 | -0.021 / -0.045 | -0.085 | FAIL |
| 31 | Earnings-aware learned ranker | 3.44 | +0.004 | -0.014 | 6.46 | -0.043 | -0.049 | n/a | -2.61 | -0.038 / -0.047 | -0.023 | FAIL |
| 32 | FLOW-DIP: WB4 ETF dip + liquid RSI collapse + stock dip leg | 2.17 | +0.114 | +0.080 | **1.71** | **+0.062** | **+0.050** | 21% | 1.98 | +0.074 / +0.049 | +0.103 | **B** (volume < 2; check-informed) |
| 33 | Earnings-move cost geometry (limit entries) | 3.12 | -0.029 | -0.043 | 3.81 | -0.028 | -0.033 | n/a | -1.97 | -0.023 / -0.033 | -0.160 | FAIL |
| 34 | No-news day-2 reversal | 2.91 | -0.027 | -0.054 | 2.98 | -0.061 | -0.066 | n/a | -3.61 | -0.047 / -0.076 | -0.058 | FAIL |
| 35 | Failed earnings gap reclaim | 0.85 | +0.128 | +0.085 | 1.27 | -0.034 | -0.043 | n/a | -0.94 | -0.008 / -0.057 | -0.030 | FAIL |

ULT-32 detail: leg E (WB4 exact ETF list) +0.110 and leg M (RSI collapse, ADV >= $500M) +0.124 hold up on check;
leg D (stock dip, the volume step) loses in both halves (-0.078 on check) and is why the pick misses. Worst day/trade-
session -1.98 (bar -2.152). Its check plateau shows the same edges at 1.0-1.4/session with t up to 3.77 (32a), but that
is a post-hoc read of the check half and cannot be used to pick.

## Tier tally
- BEATS: 0. Robust TIER A: 0. TIER A by the letter: 1 (ULT-20, skeptic-downgraded to B).
- TIER B (never deployed): 12, 20, 22, 23, 32.
- FAIL: the other 30.

## The honest read
- **Edge, not volume, is the bottleneck.** Every broad single-stock base loses 0.02-0.05R per trade with random entries,
  partly before costs. Triggers that beat random by +0.02..+0.10 only shrink the loss.
- **Widening a real edge destroys it.** WB4 at wider hours (22), wider ETF lists (12), lower ADV for ST7 (13) and a
  stock dip leg (32-D) all add losing trades.
- **Learned rankers over price features (11, 19, 20, 21, 31) learned nothing that survives costs.** Their directional
  factors flip sign between fit halves.
- **Earnings/news setups (round 4) fail too.** The triggers did worse than random bars on the same reaction-day names,
  and reaction-day costs are higher.
- **What holds out of sample:** the WB4 late-afternoon ETF dip (~+0.10..0.11R, ~0.8/session) and the one-bar RSI
  collapse in very liquid stocks (~+0.12..0.14R, 0.3-1.0/session). These match the two positive benchmark setups
  (NM-ETF-late-dip, ST7-FD). A pre-registered book of such narrow edges, on a fresh holdout, is the most promising
  next step. It needs a new window, because this check half has now informed these designs.
- **Biases left in** (today's symbol list, flat borrow fee, ETB flag as of today) all favour the candidates.

## Rule-change context
All figures above are backtests on 1-minute bar history, with one rule set (LR8 costs, next-minute-open fill, borrow
fee, U2 intake, universal SPY filters) applied to the whole window. No live-account window is quoted, so no live
rule change (research/ledger.jsonl) is mixed into these numbers. The ledger entries effective 2026-11-19
(2026-11-19-process-bundle, 2026-11-19-usage1-plan, 2026-11-18-tweaked-copies-new-setups) are process/policy only and
do not touch any figure here. The benchmark figures for ST7-FD and NM-ETF-late-dip are also replays on the same
pipeline, not live results.

## Files
- Plans: PLAN.md, round2/PLAN.md, round3/PLAN.md, round4/PLAN.md. Benchmark: benchmark/BENCHMARK.md.
- Per candidate: round<k>/ULT-<n>/ (RESULTS.md, bt.py, test_module.py, fitsel.json, check_once.json, ...).
- Modules kept for the record (not deployed): modules/ULT-*.py.

Educational only — not financial advice.
