Educational only — not financial advice

# Round 6: market-state gates for the long mean-reversion books. 0 of 24 pass, nothing deployed (2026-11-19)

Plan: round6/PLAN.md (sha256 in PLAN.sha256), committed before any gate was scored. Code: round6/gates.py. Every
number: round6/gates.json. Trade rows with their features: round6/trades_features.csv.gz.

## In plain words
- Rounds 1-5 found that our best "buy the dip" setups make money in 2025-26 but lost money in 2023-24. The question
  this round: is there a market reading, known before we trade, that says "today dip-buying works" and "today it
  doesn't"? If so, trading only on the good days might have been profitable in all three periods.
- We tested 12 readings decided in advance: market calmness (20-day volatility), market trend (vs 20- and 50-day
  averages), yesterday's and last week's market move, a fear gauge (VXX vs its 10-day average), how far apart stocks
  moved yesterday (dispersion), how many stocks are above their 20-day average (breadth), the market's opening gap,
  the market's move since the open and over the last 30 minutes at the moment of entry, and the weekday.
- For each reading, the cut-off was picked on two periods and then tested on the third, in all three rotations, so
  every period was once the "unseen" test. 822 settings were tried in total.
- **No reading passed for either book.** Most filters chosen on two periods did not help, or hurt, on the third.
- **Closest miss: dispersion (trade only when stocks moved far apart yesterday) for BOOK-EM.** It was positive in all
  three test periods and its pooled score cleared the strict bar (t 4.37 vs 3.88). But in 2023-24 it kept only 13% of
  trades (36 trades on 15 days in 427 sessions), below the 40% floor, and 45% of that profit came from one day
  (2023-03-14, the bank-failure week). So it fails, and it would trade far too rarely in a calm market.
- Side finding: the benchmark ST7-FD is also negative in the fit period (-0.132R, 250 trades), so it is positive in only
  1 of the 3 periods. No gate fixed that.
- Nothing was deployed. No setup, exit, YAML, account, assignments or ledger entry was changed.

## Set-up (as pre-registered)
- Books: **BOOK-EM** (ULT-32 32e: leg E late ETF dip + leg M one-bar RSI collapse) and **ST7-FD** (benchmark).
- W1 = 2023-01-03..2024-09-13 (427 sessions; round-5 rows). W2 = fit = 2024-10 + 2025-03..09 (170 sessions; BOOK-EM
  re-generated with the frozen ULT-32 harness, reproducing fit_grid 32e exactly: 270 trades, +0.1879). W3 = check =
  2025-10-01..2026-11-04 (276 sessions). The locked block 2024-11-01..2025-02-28 was never read (date filters on every
  read). Costs are in (LR8; long only, so no borrow).
- ST7-FD W1: 4 entries after a 13:00 early close (a known harness flaw, +2.74R together) were removed as planned:
  477 trades, -0.022R (round 5 quoted -0.016R on 481).
- Gates: 11 numeric readings x {keep low, keep high} x keep fraction {40..90%} + weekday (drop one day) = 137 per book
  per rotation; 822 in all. **N_job = 1,866 (up to 1,882); t bar = 3.88.**
- Pick rule on the two training windows: maximise the worse of the two gated avg R; apply the frozen cut-off to the
  held-out window. Pass: held-out avg R > 0 and w/o best day > 0 in all three, keep >= 40% in each, pooled held-out
  day-clustered t >= 3.88.

## Ungated baseline (same rows)
| Book | W1 n / avg R / w/o best | W2 | W3 | Pooled (t) |
|---|---|---|---|---|
| BOOK-EM | 270 / -0.040 / -0.067 | 270 / +0.188 / +0.148 | 341 / +0.115 / +0.099 | 881 / +0.090 (3.02) |
| ST7-FD | 477 / -0.022 / -0.046 | 250 / -0.132 / -0.180 | 864 / +0.084 / +0.073 | 1,591 / +0.018 (0.49) |

## Every gate, held-out results (avg R, kept share; "d" = gated minus ungated on the same rows)
### BOOK-EM
| Gate | W1 held out | W2 held out | W3 held out | Pooled n / avg R / t | Fails |
|---|---|---|---|---|---|
| rv20 | -0.040, 100% | +0.228, 84% | -0.158, 11% | 511 / +0.058 / 1.25 | pos, w/o best, keep, t |
| tr20 | -0.063, 76% | +0.258, 65% | +0.077, 36% | 487 / +0.077 / 1.69 | pos, keep, t |
| tr50 | +0.042, 55% | no rows (W2 feature crosses the locked gap) | +0.110, 81% | 424 / +0.086 / 2.70 | keep (W2), t |
| ret1 | -0.054, 38% | +0.175, 55% | +0.090, 41% | 390 / +0.084 / 1.67 | pos, keep, t |
| ret5 | -0.032, 70% | +0.220, 62% | +0.072, 46% | 502 / +0.080 / 1.89 | pos, t |
| vxx10 | -0.094, 39% | +0.083, 25% | +0.047, 16% | 223 / -0.010 / -0.17 | pos, keep, t |
| **disp** | **+0.186, 13%** | **+0.238, 63%** | **+0.118, 72%** | **447 / +0.168 / 4.37** | **keep (W1 only)** |
| breadth20 | -0.060, 75% | +0.236, 68% | +0.027, 26% | 455 / +0.064 / 1.27 | pos, keep, t |
| gap | -0.094, 74% | -0.016, 22% | +0.139, 51% | 431 / +0.010 / 0.27 | pos, keep, t |
| spy_fo | -0.004, 28% | +0.207, 47% | +0.076, 50% | 374 / +0.104 / 2.82 | pos, keep, t |
| spy30 | -0.008, 69% | +0.108, 44% | +0.125, 46% | 461 / +0.067 / 2.18 | pos, t |
| dow | -0.067, 79% | +0.162, 85% | +0.112, 87% | 739 / +0.076 / 2.29 | pos, t |

### ST7-FD
| Gate | W1 held out | W2 held out | W3 held out | Pooled n / avg R / t | Fails |
|---|---|---|---|---|---|
| rv20 | -0.086, 51% | -0.394, 48% | +0.092, 83% | 1,059 / +0.005 / 0.10 | pos, t |
| tr20 | -0.047, 59% | -0.194, 58% | +0.085, 89% | 1,172 / +0.024 / 0.58 | pos, t |
| tr50 | -0.015, 70% | no rows | +0.093, 89% | 1,098 / +0.060 / 1.48 | pos, keep, t |
| ret1 | -0.014, 84% | -0.108, 64% | +0.162, 38% | 888 / +0.035 / 0.63 | pos, keep, t |
| ret5 | -0.055, 65% | -0.138, 34% | +0.079, 69% | 989 / +0.019 / 0.45 | pos, keep, t |
| vxx10 | -0.000, 89% | -0.195, 84% | +0.073, 88% | 1,371 / +0.014 / 0.36 | pos, t |
| disp | -0.065, 13% | -0.014, 60% | +0.100, 80% | 904 / +0.070 / 1.37 | pos, keep, t |
| breadth20 | -0.080, 43% | -0.279, 72% | +0.083, 81% | 1,054 / -0.000 / -0.01 | pos, t |
| gap | -0.007, 37% | +0.098, 51% | +0.062, 55% | 769 / +0.052 / 1.44 | pos, keep, t |
| spy_fo | +0.070, 41% | -0.202, 72% | +0.040, 52% | 825 / -0.006 / -0.11 | pos, t |
| spy30 | -0.025, 92% | -0.078, 75% | +0.089, 92% | 1,419 / +0.032 / 0.82 | pos, t |
| dow | -0.000, 87% | -0.055, 74% | +0.087, 82% | 1,312 / +0.040 / 1.07 | pos, t |

Feature gaps (counted in gates.json `nan_trades`): only W2 has unknown features, because a lookback that would cross the
locked gap is not bridged: tr50 327 of 520 W2 trades (all of W2 BOOK-EM held-out rows), rv20 / breadth20 66, tr20 64,
vxx10 49, ret5 26, ret1 / disp / gap 12, spy30 2.

## Best gate in detail: BOOK-EM + dispersion (keep high), FAILS the 40% floor
| Held-out window | Cut-off (chosen on the other two) | Trades (/session) | Kept | Avg R | Ungated avg R | W/o best day | Best-day share | t |
|---|---|---|---|---|---|---|---|---|
| W1 2023-01..2024-09 | disp >= 3.13% | 36 (0.08) | 13% | +0.186 | -0.040 | +0.122 | 45% (2023-03-14) | 1.93 |
| W2 fit | disp >= 2.58% | 166 (0.98) | 63% | +0.238 | +0.188 | +0.179 | 38% | 3.60 |
| W3 check | disp >= 2.64% | 245 (0.89) | 72% | +0.118 | +0.115 | +0.096 | 21% | 2.62 |
| Pooled held out | | 447 (0.51) | | +0.168 | +0.090 | +0.144 | 20% | 4.37 |

Effect per leg (CLAUDE.md remedy rule): leg E improves in all three windows (W1 -0.040 -> +0.222 on 34 of 249 trades;
W2 +0.213 -> +0.253; W3 +0.110 -> +0.122). Leg M gets worse in W1 (-0.043 -> -0.434, 2 trades) and W3 (+0.124 ->
+0.108), better in W2 (-0.051 -> -0.003). So 1 family improves everywhere, 1 is mixed.

Why it fails, beyond the floor: the cut-offs come from W2 + W3, where yesterday's cross-sectional dispersion runs higher
(median day 2.4% / 2.9%) than in W1 (2.0%). In W1 the gate only opens on rare stressed days (15 days, led by the
March-2023 bank crisis). The W1 universe also comes from a different daily file (today's symbol list, survivorship),
so part of the level shift may be data, not market. The W3 improvement is tiny (+0.003R).

Diagnostic only (post-hoc, not counted, not a gate: it uses each window's own distribution, which is look-ahead):
BOOK-EM by within-window dispersion tercile, low / mid / high: W1 -0.214 / 0.000 / +0.101; W2 +0.107 / +0.115 /
+0.333; W3 +0.121 / +0.086 / +0.137. The low-dispersion third is the worst or near-worst in every window. A
point-in-time *relative* reading (yesterday's dispersion vs its own trailing median) is the natural next gate, but it
needs a window none of this work has seen (the locked block or live forward data). Backlog idea, not a result.

## Honest read
- Pre-registered verdict: **0 of 24 gate x book combinations pass.** No regime gate makes either book positive in all
  three held-out windows with enough trades.
- Most gates pick opposite directions depending on which two windows train them (e.g. tr20 high on W2+W3, low on
  W1+W3); that is the signature of no stable regime effect at this sample size.
- ST7-FD is the harder case: it is negative in two of three windows ungated (W1 -0.022, W2 -0.132) and no gate turns
  W2 positive with >= 40% kept except the opening-gap gate (+0.098), which fails in W1.
- All three windows have now been seen in some form, so even the dispersion near miss would be "promising, needs the
  locked block or live forward confirmation", never proven. As it fails the floor, it is not even that.
- Biases (today's symbol list in W1; breadth and dispersion built from the same lists) favour the gates.

## Configurations counted
822 this round (137 per book per rotation x 2 books x 3 rotations). Cumulative **N_job = 1,866 (up to 1,882)**,
t bar 3.88. Diagnostics above are reported, not counted.

## Rule-change context
All figures are 1-minute backtests with one fixed rule set per book (LR8 costs, next-minute-open fills, frozen ULT-32
and benchmark harnesses). No live-account window is quoted, so no `research/ledger.jsonl` change is mixed in. For
reference: ST7-FD was promoted 2026-10-26, WB4 went live 2026-11-17, NM-ETF runs in Primary; all after every window
here. No ledger entry was added, because nothing was deployed.

## Deployment
None. No setup, exit, YAML, account, display name, assignments or ledger change.

Educational only — not financial advice.
