# PAIRS-1127 — stock vs sector-ETF intraday residual mean reversion

**Educational only — not financial advice.** Research only: nothing in config/, setups, exits, assignments.json,
decisions.json or the ledger changed.

## In plain words

We tested a market-neutral book: when a liquid stock runs away from its sector ETF (XLK, XLF, ... SMH, beta from the prior
60 sessions only) by more than 2.5 / 3 / 4 sigma intraday, trade it back against the ETF hedge. **It fails, and costs are
not the only reason: there is almost no reversion to capture.** Before costs the average trade makes between −2 and +2 bp
of the stock's notional (best cell +1.95 bp on T2; zero-latency fills only add about 0.5 bp). After costs on both legs it
loses 13–20 bp per trade under LIVE-L (about −0.13 to −0.19 R) and 4–10 bp even under the lenient LR8. **All 28 configs are
negative on FIT, CHECK and T2 under both cost models** (out-of-sample day t from −9 to −33). Larger deviations do not help:
k = 4 is no better than k = 2.5 before costs, and the 60-minute-window version at k = 4 is negative even gross.

The good news is the structure itself: the hedge works as designed. The daily P/L has almost no link to the index (corr with
SPY's open-to-close −0.07..+0.11 on CHECK/T2), so the "negative market intercept" problem is solved by the construction —
there is just no edge inside it at intraday horizons with a ~16 bp round trip. Verdict **FAIL**.

## Setup (PREREG.md, committed 3997378d26 before any score)

- SIP 1-min caches -> 5-min bars; 940 sessions (half days out); locked block 2024-11-01..2025-02-28 never read (row filter
  at read time + asserts in pr_build.py / pr_sim.py / pr_score.py). FIT 169 days, CHECK 274, T2 435. EARLY n/a (no
  single-stock minute bars before 2022-10).
- Universe: non-ETF names, prior close >= $5, top 500 (or 200) by prior-20-session dollar volume; T2 is limited to the
  469-name fresh cache (survivorship: today's lists applied to the past). 1,016 stocks considered, 333k eligible
  stock-days.
- Hedge ETF per stock-day = highest prior-60-session 5-min correlation (corr >= 0.30), beta clipped [0.2, 3]. Shares of
  trades by ETF: XLK 16%, XLI 14%, XLY 11%, SMH 11%, XLF 10%, XLV 9%, others below 8%.
- Entry at the next minute open after a 5-min close with |z| > k (10:00–15:00 decisions); exits at reversion / pair stop
  (k+2) / time / 15:55. Exit mix (all configs): reversion 47%, time 23%, stop 17%, 15:55 13%.
- Costs: LIVE-L stock leg (cells_live.json, a + b x W, W = pair-stop width, median 74–134 bp) averages 11–12 bp per round
  trip; ETF leg (one tick per side + 1 bp cushion, x beta) 4.7 bp; total 15–18 bp. LR8 total 6–7 bp (no spread term).

**Configs: 28** (all reported below). Cumulative N ≈ 9,176 + 28 = **9,204** (lineage bar t ≈ 4.28; family bar 2.61).

## Results — every config (bp of stock notional per trade)

| Cfg | Rule | n CHECK / T2 | gross bp FIT / CHECK / T2 | LIVE-L net bp FIT / CHECK / T2 | LR8 net bp CHECK / T2 | R/trade LIVE-L CHECK / T2 | OOS day t (LIVE-L) | ρ SPY CHECK / T2 |
|---|---|---|---|---|---|---|---|---|
| P01 | OPEN-k2.5-full-60-T500 | 42,081 / 40,091 | -0.3 / -0.1 / +0.6 | -15.8 / -16.7 / -15.0 | -6.9 / -6.4 | -0.155 / -0.187 | -29.7 | +0.02 / +0.03 |
| P02 | OPEN-k2.5-full-EOD-T500 | 42,081 / 40,091 | -1.1 / +0.3 / +1.1 | -16.5 / -16.2 / -14.5 | -6.5 / -5.9 | -0.152 / -0.179 | -19.3 | -0.02 / -0.00 |
| P03 | OPEN-k2.5-half-60-T500 | 42,081 / 40,091 | -0.5 / +0.4 / +0.8 | -16.0 / -16.2 / -14.8 | -6.4 / -6.2 | -0.151 / -0.185 | -30.2 | +0.03 / +0.04 |
| P04 | OPEN-k2.5-half-EOD-T500 | 42,081 / 40,091 | +0.2 / +1.0 / +1.0 | -15.2 / -15.6 / -14.7 | -5.9 / -6.1 | -0.147 / -0.180 | -24.0 | +0.01 / +0.02 |
| P05 | OPEN-k3.0-full-60-T500 | 29,351 / 27,030 | -0.5 / -0.6 / +0.7 | -15.9 / -17.1 / -14.8 | -7.3 / -6.4 | -0.156 / -0.186 | -23.7 | +0.04 / +0.02 |
| P06 | OPEN-k3.0-full-EOD-T500 | 29,351 / 27,030 | -0.8 / -0.7 / +0.8 | -16.2 / -17.2 / -14.8 | -7.5 / -6.3 | -0.158 / -0.181 | -16.5 | -0.01 / -0.00 |
| P07 | OPEN-k3.0-half-60-T500 | 29,351 / 27,030 | -0.7 / +0.0 / +0.8 | -16.1 / -16.5 / -14.7 | -6.7 / -6.3 | -0.152 / -0.184 | -24.0 | +0.05 / +0.04 |
| P08 | OPEN-k3.0-half-EOD-T500 | 29,351 / 27,030 | +0.4 / +0.4 / +1.1 | -15.0 / -16.1 / -14.5 | -6.3 / -6.0 | -0.152 / -0.178 | -19.3 | +0.02 / +0.03 |
| P09 | OPEN-k4.0-full-60-T500 | 14,060 / 12,560 | -2.1 / +0.2 / +1.1 | -17.4 / -16.3 / -14.4 | -6.6 / -6.2 | -0.156 / -0.177 | -13.2 | +0.05 / -0.05 |
| P10 | OPEN-k4.0-full-EOD-T500 | 14,060 / 12,560 | -2.2 / -0.2 / +1.1 | -17.5 / -16.7 / -14.5 | -7.0 / -6.3 | -0.160 / -0.176 | -9.5 | -0.00 / -0.03 |
| P11 | OPEN-k4.0-half-60-T500 | 14,060 / 12,560 | -1.1 / +0.6 / +1.0 | -16.4 / -15.9 / -14.5 | -6.2 / -6.3 | -0.154 / -0.176 | -13.4 | +0.05 / -0.03 |
| P12 | OPEN-k4.0-half-EOD-T500 | 14,060 / 12,560 | -0.1 / +0.1 / +0.1 | -15.5 / -16.4 / -15.4 | -6.8 / -7.2 | -0.160 / -0.182 | -12.1 | +0.01 / -0.02 |
| P13 | R60-k2.5-full-60-T500 | 24,564 / 23,782 | -1.8 / -0.4 / +1.7 | -18.3 / -18.1 / -14.9 | -6.5 / -4.8 | -0.132 / -0.146 | -26.8 | +0.03 / +0.03 |
| P14 | R60-k2.5-full-EOD-T500 | 24,564 / 23,782 | -1.9 / -0.8 / +1.6 | -18.4 / -18.4 / -15.0 | -6.8 / -4.9 | -0.135 / -0.146 | -25.1 | +0.01 / +0.04 |
| P15 | R60-k2.5-half-60-T500 | 24,564 / 23,782 | -1.7 / +0.4 / +1.4 | -18.2 / -17.3 / -15.1 | -5.7 / -5.0 | -0.128 / -0.148 | -33.0 | +0.04 / +0.06 |
| P16 | R60-k2.5-half-EOD-T500 | 24,564 / 23,782 | -2.0 / +0.3 / +1.4 | -18.4 / -17.4 / -15.2 | -5.7 / -5.1 | -0.128 / -0.148 | -32.9 | +0.03 / +0.06 |
| P17 | R60-k3.0-full-60-T500 | 13,467 / 13,065 | -2.9 / -0.7 / +1.7 | -19.4 / -18.4 / -14.9 | -6.8 / -5.0 | -0.135 / -0.144 | -18.5 | +0.06 / +0.05 |
| P18 | R60-k3.0-full-EOD-T500 | 13,467 / 13,065 | -2.8 / -1.0 / +1.6 | -19.2 / -18.6 / -15.0 | -7.1 / -5.1 | -0.136 / -0.146 | -17.5 | +0.02 / +0.06 |
| P19 | R60-k3.0-half-60-T500 | 13,467 / 13,065 | -2.6 / +0.6 / +1.5 | -19.1 / -17.1 / -15.1 | -5.5 / -5.2 | -0.128 / -0.147 | -23.5 | +0.09 / +0.09 |
| P20 | R60-k3.0-half-EOD-T500 | 13,467 / 13,065 | -2.7 / +0.4 / +1.5 | -19.2 / -17.3 / -15.1 | -5.7 / -5.2 | -0.128 / -0.148 | -23.2 | +0.07 / +0.08 |
| P21 | R60-k4.0-full-60-T500 | 4,496 / 4,534 | -2.2 / -1.6 / -1.0 | -18.6 / -19.1 / -17.7 | -7.8 / -8.0 | -0.139 / -0.163 | -10.5 | +0.11 / -0.04 |
| P22 | R60-k4.0-full-EOD-T500 | 4,496 / 4,534 | -2.4 / -2.1 / -1.6 | -18.9 / -19.7 / -18.2 | -8.4 / -8.6 | -0.140 / -0.169 | -9.3 | +0.09 / -0.05 |
| P23 | R60-k4.0-half-60-T500 | 4,496 / 4,534 | -3.7 / -0.3 / +0.0 | -20.1 / -17.8 / -16.6 | -6.5 / -7.0 | -0.136 / -0.151 | -10.4 | +0.11 / -0.02 |
| P24 | R60-k4.0-half-EOD-T500 | 4,496 / 4,534 | -3.8 / -0.3 / -0.1 | -20.3 / -17.8 / -16.8 | -6.5 / -7.1 | -0.136 / -0.153 | -10.4 | +0.11 / -0.03 |
| P25 | OPEN-k3.0-half-EOD-T200 | 13,307 / 17,512 | +0.3 / +0.4 / +1.4 | -14.8 / -16.3 / -13.3 | -6.2 / -5.0 | -0.143 / -0.185 | -16.3 | -0.07 / +0.06 |
| P26 | OPEN-k4.0-half-EOD-T200 | 6,428 / 8,244 | +0.1 / +1.0 / +0.7 | -14.9 / -15.7 / -13.9 | -5.6 / -5.9 | -0.149 / -0.185 | -9.5 | -0.05 / +0.01 |
| P27 | R60-k3.0-half-EOD-T200 | 5,910 / 8,216 | -2.5 / -0.9 / +2.0 | -18.7 / -19.1 / -13.8 | -6.9 / -4.0 | -0.132 / -0.150 | -18.3 | +0.03 / +0.08 |
| P28 | R60-k4.0-half-EOD-T200 | 1,981 / 2,811 | -1.2 / -0.2 / +0.9 | -17.3 / -18.2 / -14.8 | -6.3 / -5.3 | -0.130 / -0.156 | -9.5 | +0.08 / -0.00 |

FIT-selected primary finalist (highest FIT day t, as pre-registered): **P28 R60-k4.0-half-EOD-T200** — FIT −17.3,
CHECK −18.2 (n 1,981), T2 −14.8 (n 2,811) bp after LIVE-L; LR8 −6.3 / −5.3; R/trade −0.13 / −0.16; OOS day t −9.5 (bar
+2.61). Every pass bar fails except market neutrality:

| Bar | P28 result |
|---|---|
| LIVE-L > 0 on CHECK and T2 | −18.2 / −14.8 bp: fail |
| LR8 > 0 on both | −6.3 / −5.3 bp: fail |
| Pooled day t >= 2.61 | −9.5: fail |
| Best-day share < 50%, avg w/o best day > 0 | totals negative (share n/a); w/o best day −18.6 / −15.0: fail |
| Random size-matched control >= 95th pct | CHECK 33.5th pct (control −17.9), T2 95.0th (control −15.7): fail on CHECK |
| Stress (+1 min fills, +2 bp per leg per side) | −24.4 bp, t −13.7: fail |
| Market neutrality, abs(corr) with SPY < 0.30 | CHECK +0.08 / T2 −0.00: pass |

Best-day share and avg w/o best day do not rescue any config: no config has a positive total in any split.

## Do costs kill it? (CHECK+T2 pooled, all configs by baseline and k)

| Baseline, k | trades | gross | LIVE-L stock leg | ETF leg | LIVE-L total | net LIVE-L | LR8 total |
|---|---|---|---|---|---|---|---|
| OPEN 2.5 | 328,688 | +0.63 | 11.25 | 4.72 | 16.09 | −15.47 | 6.92 |
| OPEN 3.0 | 256,343 | +0.39 | 11.19 | 4.70 | 16.01 | −15.61 | 6.89 |
| OPEN 4.0 | 121,152 | +0.52 | 11.17 | 4.67 | 15.96 | −15.44 | 6.99 |
| R60 2.5 | 193,384 | +0.67 | 12.28 | 4.73 | 17.12 | −16.44 | 6.26 |
| R60 3.0 | 120,254 | +0.70 | 12.31 | 4.70 | 17.11 | −16.42 | 6.34 |
| R60 4.0 | 40,912 | −0.71 | 12.29 | 4.66 | 17.05 | −17.76 | 6.58 |

Yes, many times over: the gross edge (≤ 2 bp) is about one tenth of the LIVE-L round trip on both legs and under a third
of LR8. The hedge leg alone (≈ 4.7 bp) is larger than any gross edge. RESID-MAP's conclusion stands and is stronger here:
with a sector hedge and large deviations the reversal is smaller, not larger, at intraday horizons.

Diagnostic (information only, not a config; diag.json): the same rules with zero latency (fill at the decision bar's
close) raise gross by ~0.3–0.6 bp (e.g. P04 CHECK +0.95 -> +1.56, T2 +0.96 -> +1.50). So the first minute is not where
the edge goes; it is not there.

## Market beta of the result

Daily book P/L vs SPY open-to-close: corr −0.07..+0.11 on CHECK/T2 for all 28 configs; slope −17..+120 bp of book per 1%
SPY on books of ~60–150 trades a day (under 1 bp per trade per 1% SPY). Per-trade means on SPY-up vs SPY-down days are
both negative in every config (gap at most 9 bp, no consistent direction). One oddity: on FIT the R60 configs show corr −0.28..−0.41; FIT's 2025-03
betas are fitted on 2024 sessions across the locked gap (stale) and April 2025 had extreme index moves, so the hedge ratio
was off there. CHECK/T2 are neutral.

## Per-ETF effect (finalist P28, CHECK+T2, LIVE-L net bp)

SMH −10.3 (n 635, gross +6.1), XLE −6.2 (162, gross +10.1), XLV −7.2 (623, gross +6.2), XLI −12.2 (586), XLK −16.9 (874),
XLF −17.4 (517), XLRE −17.7 (28), XLP −19.1 (336), XLC −19.9 (241), XLB −21.9 (180), XLU −26.2 (69), XLY −31.9 (541).
No hedge group is positive after costs (12 of 12 negative).

## What can be salvaged (optimistic read, no claim)

- The neutral hedge works mechanically (corr with SPY ≈ 0): a future market-neutral book can reuse the
  prior-60-session best-correlated-ETF beta (pr_sim.py) as its hedge engine.
- The edge would need a horizon where costs amortise (multi-day residual reversion, one round trip per several days) or a
  zero-extra-cost use (residual z as a tiebreak inside trades already taken). Both are untested ideas, not backlog entries
  from this FAIL; each would need its own PREREG and N.
- Gross is mildly positive in energy / semis / health-care hedges (+6..+10 bp for the finalist), but on small n and chosen
  after the fact: noted only.

## Caveats and rule-change context

- Historical replay of one fixed rule set on every day; no live journal rows, so no ledger effective date (sizing, stops,
  LR8 11-12, moves) falls inside these figures. LIVE-L was calibrated on single-name live trades (10-14..11-25); its b x W
  term is applied here with W = the pair-stop width in residual space, a proxy. The ETF leg cost (one tick per side + 1 bp)
  is a judgement; setting it to zero still leaves every config at −8.5 bp or worse under LIVE-L (max −11.1 CHECK, −8.5 T2).
- SEC fee only (TAF/CAT omitted, < 0.1 bp). Pair stops are checked on 5-min closes. Stocks with "Trust" in the name were
  excluded with ETFs (drops some REITs).
- Files: PREREG.md, pr_build.py, pr_sim.py, pr_score.py, pr_diag.py, pr_diag_score.py, results.csv, results.json,
  diag.json. Bar arrays and trade files stayed in the scratch dir (not committed).
