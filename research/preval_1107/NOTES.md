Educational only — not financial advice.

# PREVAL 1107 — full Primary reevaluation for the book starting Monday 2026-11-09 (owner 2026-11-06)

Research only: **no config, setup, assignments or ledger change**. Everything below is a proposal for the owner. Paper
trading results (Alpaca paper) and simulated replays are labelled as such. ROTA1 (rolling rule) is a separate study and is
not repeated here.

**Configurations tried:** 5 Primary books replayed (as is, Option 1 literal, Option 1b, Option 2 first draft, Option 2b) x 11
sessions; about 290 account-setup records screened for candidates (all with >= 10 live trades). Every finalist is reported,
including the two drafts that were revised (opt1 literal, opt2 first draft).

## Data and method
- Live journals of all 7 accounts (data branches mcf-data, -testing, -testing2, -graveyard, -gen, -explore1, -livelab),
  `journal.db` run_id=1, closed trades, 10-06..11-06. **R after costs = pnl_adj / (|entry - stop| x shares).** A setup's
  record is pooled across its homes; for a setup with a non-Graveyard home the Graveyard and Gen segments are left out (as
  the Team / nightly do), and the **P only** row shows the Primary segment.
- w/o best day = avg R without the best session (by summed R); share = that session's share of total R (`1 day` at >= 50%).
- Green days = share of sessions with summed R > 0; worst day = lowest session sum (R).
- last-10 = avg R of the setup's last 10 trades. since 10-29 = avg R from the Primary -2R latch date (n = trades).
- Ex-market avg R and beta = BETA1 sums from the 7 account scorecards merged (`mcf.analytics.market_beta`).
- 2y R = 2-year lab trade lists `bt_lab1104` (2024-10-01..2026-10-05, the locked block 2024-11-01..2025-02-28 left out;
  production costs; a second opinion only: the 10-29 replay / backtest audit was 75.9% trade match, +0.032R optimistic);
  "screen" = scorecard expectation; NM-ETF late dip = swarm1017 train +0.250R / **valid +0.029R**.
- REGX = `research/bdi/regx/table.csv`: the dashboard (hindsight) rating verdict, then the 6 point-in-time schemes as
  trustworthy / weak / false. REGX found the point-in-time ratings no better than a coin flip, so it is context, not a filter.
- Replay outputs (simulated trades per book and session): `replays/<book>_<date>.json`.
- Scripts: `stats.py` (table -> `all_setups.csv`), `table.py`, `replay.py`, `replay_summary.py`, `jrecomp.py`.

## B) Reevaluation — current Primary setups

| Setup | now | segment | trades / sessions | avg R | w/o best day (share) | green days / worst day | last-10 | ex-market (beta) | 2y R | REGX | since 10-29 (n) | call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` | P | P+T1 | 121 / 19 | +0.404 | +0.256 (50%) | 58% / -3.3 (10-30) | +1.021 | +0.189 (β -1.14) | -0.071 (n 5,953) | dash trustworthy (Bear>Bull); PIT 0T/1W/5F | +0.311 (37) | **KEEP** |
| Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` **P only** | P | P | 83 / 15 | +0.469 | +0.252 (62% `1 day`) | 53% / -3.3 (10-30) | +1.021 | +0.208 (β -1.16) | -0.071 (n 5,953) | dash trustworthy (Bear>Bull); PIT 0T/1W/5F | +0.311 (37) |  |
| Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` | P | P+T1 | 129 / 19 | +0.361 | +0.270 (42%) | 63% / -3.4 (10-29) | +0.368 | +0.204 (β -1.01) | -0.060 (n 5,554) | dash trustworthy (Bear>Bull); PIT 0T/4W/2F | +0.287 (30) | **KEEP** |
| Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` **P only** | P | P | 96 / 16 | +0.371 | +0.238 (55% `1 day`) | 62% / -3.4 (10-29) | +0.368 | +0.226 (β -0.83) | -0.060 (n 5,554) | dash trustworthy (Bear>Bull); PIT 0T/4W/2F | +0.287 (30) |  |
| RSI Collapse Dip Buy (all day) `ST7-rsi50dn-long-pm-t1s1-FD` | P | P+T1 | 37 / 12 | +0.161 | +0.058 (68% `1 day`) | 67% / -2.7 (10-21) | +0.422 | +0.225 (β 0.25) | +0.023 (n 1,029) | dash false (Choppy>Bear); PIT 0T/4W/2F | +0.161 (19) | **KEEP** |
| RSI Collapse Dip Buy (all day) `ST7-rsi50dn-long-pm-t1s1-FD` **P only** | P | P | 21 / 6 | +0.133 | -0.029 (112% `1 day`) | 50% / -1.2 (10-29) | +0.422 | +0.187 (β 0.09) | +0.023 (n 1,029) | dash false (Choppy>Bear); PIT 0T/4W/2F | +0.161 (19) |  |
| Big Loser Flush Buy `NS5-sma50-flush-oversold-long` | P | P+T1 | 31 / 12 | +0.064 | -0.004 (107% `1 day`) | 50% / -2.4 (10-20) | -0.203 | +0.199 (β 0.81) | -0.044 (n 1,303) | dash trustworthy (Bull>Bear); PIT 1T/1W/4F | -0.091 (11) | KEEP (borderline; long balance) |
| Big Loser Flush Buy `NS5-sma50-flush-oversold-long` **P only** | P | P | 27 / 12 | +0.047 | -0.032 (167% `1 day`) | 50% / -2.4 (10-20) | -0.203 | +0.221 (β 0.83) | -0.044 (n 1,303) | dash trustworthy (Bull>Bear); PIT 1T/1W/4F | -0.091 (11) |  |
| Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` | P | P+T1 | 257 / 17 | +0.169 | +0.056 (77% `1 day`) | 59% / -13.5 (10-15) | +0.286 | -0.033 (β -2.23) | -0.017 (n 40,679) | dash false (Bear>Choppy); PIT 0T/4W/2F | +0.312 (50) | KEEP (borderline; burst-day setup) |
| Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` **P only** | P | P | 35 / 6 | -0.178 | -0.298 (-) | 50% / -5.7 (10-21) | +0.286 | -0.197 (β -1.25) | -0.017 (n 40,679) | dash false (Bear>Choppy); PIT 0T/4W/2F | +0.069 (12) |  |
| Gap-Down Rebound Overbought Short (all day) `L3-gap-slope-rsi5hi-FD` | P | P+T1+T2 | 90 / 16 | +0.063 | -0.033 (142% `1 day`) | 56% / -3.6 (10-27) | -0.479 | -0.063 (β -2.30) | -0.040 (n 9,970) | dash false (Bear>Choppy); PIT 0T/3W/3F | -0.061 (29) | Opt 2: DEMOTE -> Testing 2 |
| Gap-Down Rebound Overbought Short (all day) `L3-gap-slope-rsi5hi-FD` **P only** | P | P | 14 / 5 | -0.536 | -0.603 (-) | 20% / -2.9 (11-04) | -0.479 | -0.508 (β -0.86) | -0.040 (n 9,970) | dash false (Bear>Choppy); PIT 0T/3W/3F | -0.536 (14) |  |
| Big Gainer Dip-and-Pop `NS1-rsidip-rsi5pop-long` | P | P+T1 | 21 / 9 | +0.050 | -0.131 (289% `1 day`) | 44% / -1.1 (10-16) | -0.073 | +0.057 (β 0.15) | +0.028 (n 441) | not rated | -0.129 (9) | Opt 2: DEMOTE -> Testing 2 |
| Big Gainer Dip-and-Pop `NS1-rsidip-rsi5pop-long` **P only** | P | P | 18 / 9 | -0.030 | -0.131 (-) | 44% / -1.1 (10-16) | -0.073 | -0.022 (β 0.33) | +0.028 (n 441) | not rated | -0.129 (9) |  |
| Early Sellers, Strong Heat `MF4-h40-open-flowsell` | P | P+T1 | 22 / 7 | +0.052 | -0.029 (148% `1 day`) | 57% / -1.4 (10-08) | +0.306 | +0.061 (β 0.02) | -0.099 (n 3,302) | not rated | - (0) | **DEMOTE -> Testing 2** (Opt 1+2; twin of MF4-FD) |
| Early Sellers, Strong Heat `MF4-h40-open-flowsell` **P only** | P | P | 21 / 7 | +0.062 | -0.021 (129% `1 day`) | 57% / -1.4 (10-08) | +0.306 | +0.083 (β 0.16) | -0.099 (n 3,302) | not rated | - (0) |  |
| Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD` | P | P+T1 | 124 / 18 | +0.121 | -0.141 (196% `1 day`) | 44% / -21.6 (11-06) | -1.136 | -0.106 (β -2.87) | -0.088 (n 5,195) | dash trustworthy (Bear>Bull); PIT 0T/2W/4F | -0.474 (65) | **DEMOTE -> Testing 1** (Opt 1+2) |
| Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD` **P only** | P | P | 101 / 13 | +0.065 | -0.290 (443% `1 day`) | 46% / -21.6 (11-06) | -1.136 | -0.175 (β -2.85) | -0.088 (n 5,195) | dash trustworthy (Bear>Bull); PIT 0T/2W/4F | -0.474 (65) |  |
| Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD` | P | P+T1 | 121 / 20 | -0.118 | -0.171 (-) | 55% / -10.7 (11-05) | -0.755 | -0.148 (β -1.49) | -0.085 (n 7,232) | dash trustworthy (Bear>Bull); PIT 0T/3W/3F | -0.404 (56) | **DEMOTE -> Testing 1** (Opt 1+2) |
| Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD` **P only** | P | P | 89 / 14 | -0.258 | -0.317 (-) | 50% / -10.7 (11-05) | -0.755 | -0.237 (β -1.43) | -0.085 (n 7,232) | dash trustworthy (Bear>Bull); PIT 0T/3W/3F | -0.404 (56) |  |

## B) Reevaluation — on-deck candidates (Testing 1 / Testing 2 / Explore 1 / Live Lab / Graveyard; Gen only if outstanding)

| Setup | now | segment | trades / sessions | avg R | w/o best day (share) | green days / worst day | last-10 | ex-market (beta) | 2y R | REGX | since 10-29 (n) | call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gap-Down VWAP Loss Short (10% gap) `CWT09-gapdn-vwaploss-g10-short` | LL | LL+T2 | 15 / 8 | +0.327 | +0.227 (54% `1 day`) | 75% / -1.4 (10-13) | +0.391 | +0.272 (β -0.17) | +0.041 (screen) | not rated | +0.390 (11) | on deck: stay Live Lab (replay -3.26R / 26 tr in Primary universe) |
| Late-Day ETF Dip Buy (near-miss) `NM-ETF-late-dip-di-long` | LL | LL+T2 | 15 / 7 | +0.296 | +0.248 (33%) | 86% / -0.6 (11-04) | +0.241 | +0.317 (β 0.47) | +0.250 (swarm) | not rated | +0.217 (8) | Opt 2: **PROMOTE** (move from Live Lab; low-rep) |
| Gap-Down Bounce Short, Heavy Selling (all day) `RW1-gapdn-bounce-flowsell-short-FD` | T2 | T1+T2 | 108 / 20 | +0.088 | +0.045 (56% `1 day`) | 60% / -5.8 (10-13) | -0.001 | -0.107 (β -1.48) | -0.047 (n 7,419) | dash trustworthy (Bear>Bull); PIT 0T/4W/2F | +0.127 (34) | stay (Testing 2) |
| Gap-Down Early Bounce Short (all day) `RW7-gapdn-bounce-early-short-FD` | T1 | T1 | 436 / 19 | +0.061 | +0.032 (53% `1 day`) | 53% / -9.9 (10-19) | +0.364 | -0.132 (β -1.34) | -0.060 (n 25,968) | dash trustworthy (Bear>Bull); PIT 0T/5W/1F | +0.253 (151) | stay (Testing 1) |
| L3-gap-slope-lowdist-FD `L3-gap-slope-lowdist-FD` | T1 | T1 | 72 / 14 | +0.067 | -0.074 (194% `1 day`) | 36% / -2.1 (10-21) | +0.266 | -0.108 (β -1.73) | -0.127 (n 4,139) | dash trustworthy (Bear>Bull); PIT 0T/2W/4F | +0.077 (23) | stay (Testing 1) |
| NS4-pm-vwap-reclaim-oversold-short-FD `NS4-pm-vwap-reclaim-oversold-short-FD` | T1 | T1 | 29 / 12 | +0.141 | -0.023 (113% `1 day`) | 42% / -1.2 (10-27) | -0.247 | -0.183 (β -5.41) | -0.119 (n 1,686) | not rated | -0.247 (10) | stay (Testing 1; mark M1) |
| Early Sellers into a Pop (index down, no gap up) (near-miss) `NM-MF3-qqqdn-gapdn-FD` | T2 | T2 | 26 / 5 | +0.308 | -0.464 (146% `1 day`) | 40% / -2.8 (10-29) | -0.569 | -0.410 (β -3.86) | -0.010 (n 2,097) | not rated | -0.370 (7) | stay (Testing 2) |
| Early NS3 Short While SPY Up (near-miss) `NM-RWN3-ns3-spyup-early-short` | EX1 | EX1+T2 | 12 / 5 | +0.279 | -0.450 (181% `1 day`) | 40% / -2.1 (11-04) | +0.368 | -0.206 (β -3.88) | - | not rated | +0.368 (10) | stay (Explore 1, low-rep) |
| Gap-Down Bounce Rejection Short (10% gap) `CWT09-gapdn-bounce-g10-lowerhalf-short` | EX1 | EX1+T2 | 19 / 7 | +0.087 | -0.158 (243% `1 day`) | 57% / -2.4 (10-26) | +0.511 | -0.106 (β -0.74) | +0.141 (screen) | not rated | +0.745 (8) | stay (Explore 1, low-rep) |
| Gap-Down Bounce Rejection Short (5% gap) `CWT09-gapdn-bounce-g5-lowerhalf-short` **GY only** | GY | GY | 99 / 11 | +0.220 | +0.101 (54% `1 day`) | 45% / -4.7 (10-29) | +0.566 | -0.123 (β -1.03) | +0.047 (screen) | dash weak (Bear>Quiet); PIT 0T/6W/0F | +0.364 (76) | stay (Graveyard) |
| MF5-flowsell-vwapup-rsi5hi-FD `MF5-flowsell-vwapup-rsi5hi-FD` **GY only** | GY | GY | 20 / 4 | +0.419 | +0.352 (62% `1 day`) | 100% / +0.6 (11-04) | +0.373 | +0.233 (β -1.40) | -0.059 (n 6,787) | dash trustworthy (Bear>Bull); PIT 0T/3W/3F | +0.419 (20) | stay (Graveyard) |
| Generated: NewLOD, Flow3lem0p37 LUNCH short (BRopgt0p5, holdtr) `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short` | GEN | GEN | 21 / 5 | +0.379 | +0.129 (77% `1 day`) | 80% / -1.1 (10-29) | +0.074 | +0.417 (β 0.19) | - | not rated | +0.074 (10) | stay (Gen; not outstanding) |

### Reading the numbers
- **Primary-grade by evidence (3):** Gap-Down Pop Fade, Heavy Selling (all day) `RW3-FD` and Gap-Down Pop Fade (all day)
  `RW5-FD` — the only setups positive on every cut (avg, w/o best day +0.26 / +0.27, ex-market +0.19 / +0.20, since 10-29
  +0.31 / +0.29); the 2-year lists are slightly negative (-0.07 / -0.06), so the live edge is not confirmed on history.
  RSI Collapse Dip Buy (all day) `ST7-FD`: +0.161R, ex-market +0.225R, 2y +0.023R, but `1 day` (68%; w/o +0.058R).
- **Clear demotions:** Early Sellers, Mid-High RSI (all day) `MF2-FD` (whole record = 10-22, 196% of R; w/o best day
  -0.142R, ex-market -0.106R, last-10 -1.14R, since 10-29 -0.474R; 11-06 -21.6R) and Early Sellers, Strong Heat (all day)
  `MF4-FD` (-0.118R, -0.171R w/o best day, ex-market -0.148R, P only -0.258R; 11-05 -10.7R, 11-06 -5.5R).
- **Early Sellers, Strong Heat `MF4-h40-open-flowsell` must go with MF4-FD.** It has had no trade since 10-19 because its
  all-day twin held every signal ("twin held"); with MF4-FD gone it takes the same morning signals. Replay: **-14.46R in
  41 trades** (11-06 -8.66R) in the literal Option 1. Its own record: 22 trades +0.052R, w/o best day -0.029R (148%, `1 day`),
  2y -0.099R.
- **Borderline (evidence weak either way):** Big Gainer Dip-and-Pop `NS1` (P only -0.030R, w/o best day -0.131R, 289%
  `1 day`); Gap-Down Rebound Overbought Short (all day) `L3-rsi5hi-FD` (P only -0.536R in 14, w/o best day -0.033R,
  dashboard rating false, 2y -0.040R; but the replay credits it +6.3R, all on 11-05 where live Primary was halted);
  Big Loser Flush Buy `NS5` (w/o best day -0.004R, but ex-market +0.199R and a long); Gap-Down Recovery Fade (all day)
  `L3-fromopen-FD` (pooled +0.169R but `1 day` 77%, ex-market -0.033R, P only -0.178R in 35; in the replay it carries
  +31.2R, of which 10-29 = 57% and 10-26 another 38% — **a burst-day setup**, flat otherwise).
- **Candidates:** Late-Day ETF Dip Buy `NM-ETF-late-dip-di-long` is the one candidate positive on every cut (15 trades,
  +0.296R, w/o best day +0.248R, 86% green, ex-market +0.317R, worst day -0.6R; replay in Primary +3.13R / 12) — but
  **low-rep (15 live trades)** and only +0.029R on its 2-year validation block. Gap-Down VWAP Loss Short (10% gap)
  `CWT09-g10` looked as good live (+0.327R, 15 trades) but **lost -3.26R in 26 trades** when replayed on Primary's wider
  universe (10-26: 13 trades -6.33R) -> stays on deck. Gap-Down Bounce Short, Heavy Selling (all day) `RW1-FD` and Gap-Down
  Early Bounce Short (all day) `RW7-FD`: ex-market negative (-0.107R / -0.132R), w/o best day +0.045R / +0.032R, 2y
  negative -> not ready. Graveyard: no setup is ready (the positive Graveyard segments — CWT09 bounce g5 +0.220R, MF5-FD,
  MF3-FD — have negative pre-Graveyard records and/or negative ex-market). Gen: nothing outstanding (best GEN-261026-03:
  21 trades, `1 day` 77%).

## Proposals (for the owner; nothing is changed by this note)

Destinations: a demotion is a move (switched off in Primary in the same change); trimmed setups go to a testing account,
never off; Testing 1 = Testing 2. MF2-FD / MF4-FD go to Testing 1 as asked in DM-MF2 / DM-MF4; the others to Testing 2 to
balance exposure. Note: Testing 2 trades a top-500 pool since 11-04 (UNI1). MF4 base (1 Testing trade) and NS1 (3 Testing
trades) are under 20 trades from Testing 1/2, so under the low-rep rule they could instead rotate through Explore 1 / Live
Lab — owner's call. A promotion moves the setup out of Live Lab in the same change.

### Option 1 — minimal (3 demotions: the 2 clear ones + the MF4 twin)
| Setup | Action |
|---|---|
| Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD` | DEMOTE -> Testing 1 |
| Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD` | DEMOTE -> Testing 1 |
| Early Sellers, Strong Heat `MF4-h40-open-flowsell` | DEMOTE -> Testing 2 (else it reactivates on MF4-FD's signals: replay -14.46R) |
| RW3-FD, RW5-FD, ST7-FD, NS5, L3-fromopen-FD, L3-rsi5hi-FD, NS1 | KEEP (7 setups: 4 shorts / 3 longs) |

Literal "2 demotions only" (`opt1`) is reported in the replay for completeness; it is not recommended.

### Option 2 — full recommended book (6 setups: 3 shorts / 3 longs)
| Setup | Side | Action |
|---|---|---|
| Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` | short | KEEP |
| Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` | short | KEEP |
| Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` | short | KEEP (borderline; burst-day setup, watch) |
| RSI Collapse Dip Buy (all day) `ST7-rsi50dn-long-pm-t1s1-FD` | long | KEEP |
| Big Loser Flush Buy `NS5-sma50-flush-oversold-long` | long | KEEP (borderline; long balance) |
| Late-Day ETF Dip Buy `NM-ETF-late-dip-di-long` | long | **PROMOTE** from Live Lab (move; low-rep, 15 trades) |
| `MF2-open-rsimidhi-flowsell-FD`, `MF4-h40-open-flowsell-FD` | short | DEMOTE -> Testing 1 |
| `MF4-h40-open-flowsell`, `NS1-rsidip-rsi5pop-long`, `L3-gap-slope-rsi5hi-FD` | | DEMOTE -> Testing 2 |

Book shape: gap-down short core (RW3 / RW5 / L3-fromopen, morning to midday) + three longs in different windows (ST7 all
day, NS5 flush, NM-ETF 14:00-15:00 on index ETFs).

## C) Replay — Primary as is vs Option 1 vs Option 2 (11 sessions, 10-23..11-06)

**Method (primary): the as-live replay engine** exactly as `mcf/report/team.py` runs the Team (`mcf.replay.harness.
run_session`, real PaperRunner loop, fills=costs, limit_fill=through, quote model from journaled spreads) under Primary's
rules (`config/default.yaml`: 0.25% risk, 77 slots, buying power x3.2, -2R per-setup latch, -20R account halt) on Primary's
universe of each session (universe.csv minus PTP denylist and earnings blackout), each setup with its own `strategies:` block
(frozen snapshot of its home account that day, else the config file). Simulated fills, not broker fills; equity $100k.
Each book is run over all 11 sessions with **today's** setup list and rules (so "as is" before 10-30 includes setups that
were not yet in Primary, and the latch is applied before 10-29).
**Fidelity check:** where the book equals live Primary, the replay matches live closely (11-06 -24.43R vs actual -24.18R;
11-05 +5.13 vs +4.54; 11-04 -9.71 vs -10.75; 11-03 +12.17 vs +11.33; 11-02 -5.90 vs -6.18).
**Method 2 (cross-check): journal recomputation** (`jrecomp.py`): Primary's live trades + its journaled what-ifs for signals
blocked by the halt / latch / twin (R = r_multiple minus modelled costs), home-account trades for setups not in Primary that
day, then Primary's halt / latch / one-position-per-symbol re-applied in time order.

| Book (replay, R after costs) | total R | avg R/day | green days | worst day | w/o best day | 11-05 | 11-06 |
|---|---|---|---|---|---|---|---|
| actual Primary (live, mixed rules) | -32.53 | -2.96 | 4/11 | -24.18 (11-06) | -43.86 | +4.54 | -24.18 |
| **Primary as is** | +0.99 | +0.09 | 6/11 | -24.43 (11-06) | -11.18 | +5.13 | -24.43 |
| opt1 literal (MF2-FD + MF4-FD out; MF4 base reactivates) | +47.64 | +4.33 | 7/11 | -8.41 (11-02) | +26.12 | +21.52 | +4.30 |
| **Option 1** (opt1b: + MF4 base out) | **+61.47** | +5.59 | 6/11 | -6.51 (11-02) | +40.44 | +21.03 | +12.33 |
| opt2 first draft (with CWT09-g10, without L3-fromopen) | +29.78 | +2.71 | 7/11 | -9.68 (10-26) | +12.73 | +17.05 | +7.76 |
| **Option 2** (opt2b, recommended book) | **+64.21** | +5.84 | **9/11** | **-4.27 (11-02)** | +47.35 | +16.86 | +10.11 |

Journal recomputation, same 11 sessions: as is -20.43R (5/11 green, worst -24.42), opt1 +23.14, **Option 1 +38.34R** (8/11,
worst -6.00), opt2 +44.52, **Option 2 +46.73R** (7/11, worst -3.43); 11-05 / 11-06: Option 1 +16.89 / +11.22, Option 2
+20.78 / +11.60. Over 16 sessions (10-16..11-06): as is +73.3, Option 1 +91.8, Option 2 +99.7 (the 10-22 +73R day
dominates). Both methods rank Option 1 and Option 2 well above "as is"; they disagree on the size of the gap between
Option 1 and Option 2 (replay +2.7R, journal +8.4R) — **treat Option 1 and Option 2 as roughly equal on R; Option 2 has
fewer setups, more green days and a smaller worst day in the replay.**

Daily R (replay; `j_` = journal recomputation):

```
book         asis   opt1  opt1b   opt2  opt2b  actual  j_asis  j_opt1  j_opt1b  j_opt2  j_opt2b
date                                                                                           
2026-10-23  -2.44  -1.85  -0.66   1.24   2.71   -2.05   -5.96   -3.01    -1.68   -0.20    -0.45
2026-10-26   9.93   9.12   9.04  -9.68   8.36   -3.37    7.23    4.40     4.40    0.23     1.31
2026-10-27  -3.10  -3.22  -0.76   3.28   0.25    6.36    5.17   -1.65     1.50    4.70     3.15
2026-10-28   6.89   6.03   6.03   8.16   7.69    5.58    4.99    4.07     4.07    5.33     4.74
2026-10-29  11.73  13.47  14.53  -4.08  13.18  -11.30   -3.86    0.17     1.30   -5.31    -0.66
2026-10-30   0.71   0.00  -0.61  -1.32  -0.84   -2.52   -2.52   -1.87    -1.87    0.42    -2.21
2026-11-02  -5.90  -8.41  -6.51   0.58  -4.27   -6.18   -6.18   -8.54    -6.00    0.66    -3.43
2026-11-03  12.17  10.71   9.60   8.18   9.54   11.33   11.33    9.17     8.44    7.93     8.95
2026-11-04  -9.71  -4.03  -2.54  -1.39   0.61  -10.75  -10.75   -2.78     0.07    1.18     2.96
2026-11-05   5.13  21.52  21.03  17.05  16.86    4.54    4.54   18.04    16.89   21.98    20.78
2026-11-06 -24.43   4.30  12.33   7.76  10.11  -24.18  -24.42    5.14    11.22    7.60    11.60
```

### Per-setup effect (replay, 11 sessions; sum R, trades)
| Setup | as is | Option 1 | Option 2 |
|---|---|---|---|
| RW3-FD | +12.33 (66) | +16.49 (73) | +16.49 (73) |
| RW5-FD | +10.70 (50) | +12.78 (56) | +12.78 (56) |
| L3-fromopen-FD | +23.66 (105) | +26.00 (125) | +31.15 (127) |
| L3-rsi5hi-FD | +6.25 (81) | +6.48 (85) | out |
| ST7-FD | +1.74 (22) | +1.58 (24) | +1.58 (24) |
| NS5 | -2.12 (11) | -0.94 (20) | -0.94 (20) |
| NS1 | -0.91 (8) | -0.91 (8) | out |
| NM-ETF late dip | — | — | +3.14 (12) |
| MF2-FD | -23.42 (79) | out | out |
| MF4-FD | -27.23 (75) | out | out |
| MF4 base | (twin-held) | out (literal opt1: -14.46 / 41) | out |

Kept setups vs as is: Option 1 — 5 better, 1 unchanged (NS1), 1 slightly worse (ST7 -0.16R); Option 2 — 4 better, 1 slightly worse (ST7 -0.16R) — removing MF2 / MF4 frees halt room
and symbols (the -20R halt fired on 11-05 and 11-06 in as is). The gain is concentrated in **2 sessions** (11-05, 11-06:
as is -19.3R vs Option 1 +33.4R / Option 2 +27.0R). Without those two days: as is +20.3R, Option 1 +28.1R, Option 2 +37.2R.

**In-sample warning:** the replay window overlaps the data used to choose the books (the demotions were proposed after
11-05 / 11-06, and NM-ETF / L3-fromopen were kept or added after seeing the first replay round). These are not
out-of-sample results; a forward check is needed — e.g. keep the Team (shadow) or a shadow of the non-chosen option running
from 11-09 and judge on >= 10 sessions, R first, with the one-big-day check.

## Rule-change context (research/ledger.jsonl effective dates inside the window)
- ST7-FD promoted to Primary 10-26; CWT13-z05 in Primary 10-26 only (demoted 10-27); MF1 demoted 10-26.
- **Primary lot ~$4k (slots 77) from 10-28**; **-2R per-setup latch in Primary from 10-29**; **CF** (Testing 1/2 cost filter)
  from 10-30; L3-rsi5hi-FD promoted and L3-fromopen-FD re-promoted to Primary 10-30; **UNI1** (Testing 2 top-500 pool)
  from 11-04; **ROLL1** (Explore 1 / Live Lab low-rep homes) from 11-05. MF2-FD / MF4-FD in Primary since 10-20.
- Live per-setup records span these changes (lot size does not change R; the latch and CF can). The replay runs one rule set
  (today's Primary rules) throughout; actual Primary did not.

## Limits
- Simulated fills (1-minute bars, stop first inside a bar); synthetic quotes; shortability = the session's universe flags;
  no borrow fees; replay uses equity $100k (real Primary ~$83k after the MTUM booking; R unaffected).
- Live samples are small (11-19 sessions); 2-year lists disagree with live for RW3 / RW5 (slightly negative on history).
- NM-ETF has 15 live trades; L3-fromopen-FD's replay R is 95% two burst days; NS5 is near zero without its best day.
- Journal method: what-if outcomes have no fills (modelled costs); home-account trades carry their home account's universe /
  filters (CF in Testing, UNI1 in Testing 2).

Educational only — not financial advice.
