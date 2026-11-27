# PRIM-ADD2 re-evaluation after Friday 2026-11-27 (research only, no config change)

Educational only — not financial advice.

Card: docs/live/decisions.json PRIM-ADD2. Owner on 11-24: "re-evaluate after Friday's session; most great players in Primary but not premature decisions".
Options:
- one = add L3-gap-slope-lowdist-FD.
- yes = also add RW7-gapdn-bounce-early-short-FD with no −2R latch.
- four = move L3-gap-slope-rsi5hi-FD and RW6-ns2-up3-short-FD from Primary shadow (PSHADOW) to live.

## Bottom line
On data to 11-27, no candidate passes PRIME-RULES ENTRY or C3-BAR2, and no written exemption covers the gaps. Recommendation: PRIM-ADD2 no.

What changed since the card (data to 11-24): Wed 11-25 was a squeeze day for gap-down shorts.
- On Deck (no per-setup latch in testing accounts, PROT-21): L3-lowdist 198 trades −144.6R; L3-rsi5hi 311 trades −219.1R.
- Testing F: RW7 −52.4R.

Fri 11-27 (half day) was quiet: L3-lowdist 1 trade −1.07R, RW7 15 trades −3.18R, L3-rsi5hi 3 trades −0.32R, RW6 0 trades, PSHADOW 0 trades.

Reconciliation with the card: recomputed to 11-24, the figures match it exactly (L3-lowdist 113 trades +21.81R; RW7 982 trades +14.22R, +0.014R).

## Data and method
- Live journals (run 1) of all 10 accounts from origin/mcf-data*, EOD 11-27. Identical signals across accounts are counted once (as footrace.live_trades). Engine label: Live.
- Cost bases:
  - LR8 = cost_r_lr8 (rule 32; the verdict basis).
  - Booked = journal pnl_adj / risk.
  - LIVE-L (primshorts_1126 cells_live.json) is a cost model for simulated fills and was calibrated on these live trades. Live fills already carry the real spread and slippage, so LIVE-L is not charged again on live rows; the booked column stands in for it. On the bench, LIVE-L is about 0.035R per trade worse than LR8 for these short families.
- day t = day-clustered t (primbook ct). Shrunk = n/(n+150)·avg + 150/(n+150)·(−0.10).
- Non-overlap = symbol-days that no current Primary member (L3-fromopen, RW3-FD, RW5-FD, NM-ETF) traded. Exact symbol match only, with no twin/ETF mapping.
- Primary-book = primbook.py logic: ≤30 open lots per setup, ≤3 per symbol, −2R realised latch. Engine label E4. The random-entry null was not re-run because every candidate already fails part (1).
- Active days come from arena_reps.json (to 11-25) plus 11-27. On Deck has had 11 sessions (11-12..11-27).
- The locked block 2024-11-01..2025-02-28 was not read.

## Criteria (quoted)
PRIME-RULES ENTRY (CLAUDE.md, 2026-11-16): "≥ 20 traded sessions (firm) + ≥ 5 sessions in On Deck; trades flexible by activity (≥ 40 trades for low-frequency setups … judge by shrunk avg R / confidence); avg R w/o best day > 0; best day ≤ 40% of R; owner's yes."

C3-BAR2 (RESEARCH_RULES 23; PROT-14): "W1-BAR: >= 30 testing trades after costs, >= 8 traded sessions, avg R without the best day > 0, >= 50% green days; >= 15 active days; … scored on its non-overlap record; shrunk estimate … > 0; best-day share of total R < 50%." It adds FP-C: "(1) avg R without its best day under [Primary book] rules > 0, and (2) beats the random-entry null". The 11-17 promotion hold still applies on top. FP-B counts L3-lowdist and L3-rsi5hi as one slot.

PROT-21 (docs/PROTECTED.md): "Primary -2R latch (cost R) and -20R halt … Change guard: Judge on worst-day protection over >= 30 sessions. No halt tighter than 20R without saves on >= 2 separate days. No latch in Testing".

## Option "one": L3-lowdist (On Deck)
- Record (LR8 | booked): 312 trades / 23 sessions, −123.88R | −121.63R, avg −0.397R | −0.390R.
- One-big-day check: w/o best day −0.507R; best day 11-12 +18.21R; share n/a because total < 0 (83% on the card).
- t −8.79, day t −1.65, green 43%. Worst day 11-25 −144.62R. Shrunk −0.301.
- Non-overlap: 247 trades / 15 sessions, avg −0.510R, w/o best −0.602R, green 60%, shrunk −0.355.
- Primary-book: with latch +13.82R / 120 trades, w/o best −0.050R (best day 132% of total). Without latch −56.1R.
- Rule-change context: 11-12 On Deck build, split-tape gate off in On Deck, LR8, testing halt 300R; 11-17 TSZ1 half-size testing lots; 11-19 U9-TGT / U9-ETB; 11-23 BRAKE-BURST; CF 0.15R filter in testing since 10-30; no latch in testing since 10-23.

| Criterion | Number | Result |
|---|---|---|
| PRIME ≥20 traded sessions | 23 | PASS |
| PRIME ≥5 On Deck sessions | 11 | PASS |
| PRIME trades / shrunk | 312 trades, shrunk −0.301 | FAIL |
| PRIME w/o best day > 0 | −0.507R | FAIL |
| PRIME best day ≤40% | total < 0 | FAIL |
| C3 ≥30 testing trades | 312 | PASS |
| C3 ≥8 traded sessions | 23 | PASS |
| C3 w/o best day > 0 (non-overlap) | −0.602R | FAIL |
| C3 ≥50% green (non-overlap) | 60% (raw 43%) | PASS |
| C3 ≥15 active days | 34 | PASS |
| C3 shrunk > 0 | −0.355 | FAIL |
| C3 best-day share < 50% | total < 0 | FAIL |
| FP-C w/o best day under Primary rules | −0.050R | FAIL |
| Promotion hold (11-17) | in force | needs owner lift |

## Option "yes": RW7 with no latch (Testing F)
- Record: 1,049 trades / 32 sessions, −41.38R | −23.84R, avg −0.039R | −0.023R.
- One-big-day check: w/o best day −0.082R; best day 11-20 +40.23R; share n/a because total < 0 (84% on the card).
- t −1.52, day t −0.46, green 47%. Worst day 11-25 −52.42R. Shrunk −0.047. Since the card: −55.6R.
- Non-overlap: 945 trades, avg −0.038R, w/o best −0.081R, green 53%.
- Primary-book: with latch −44.41R (w/o best −0.122R, worst day −32.3R). With no latch, as asked: 897 trades −20.17R, w/o best −0.062R, worst day −37.96R.
- To 11-24 the no-latch book was +20.97R against −8.91R with the latch; that gap was the case for the exemption. It has reversed.
- Rule-change context: On Deck only 11-12/11-13, then owner demote to Testing F from 11-16; LR8 11-12; TSZ1 11-17; BRAKE-BURST 11-23.

| Criterion | Number | Result |
|---|---|---|
| PRIME ≥20 traded sessions | 32 | PASS |
| PRIME ≥5 On Deck sessions | 2 | FAIL |
| PRIME trades / shrunk | shrunk −0.047 | FAIL |
| PRIME w/o best day > 0 | −0.082R | FAIL |
| PRIME best day ≤40% | total < 0 | FAIL |
| C3 ≥30 trades | 1,049 | PASS |
| C3 ≥8 sessions | 32 | PASS |
| C3 w/o best day (non-overlap) | −0.081R | FAIL |
| C3 green (non-overlap) | 53% | PASS |
| C3 active days | 34 | PASS |
| C3 shrunk | −0.047 | FAIL |
| C3 best-day share | total < 0 | FAIL |
| FP-C | −0.122R (latch) / −0.062R (no latch) | FAIL |
| PROT-21 guard (worst-day protection ≥30 sessions) | latch cuts the worst day by 5.7R; neither version is positive w/o best day | NOT met |

## Option "four": L3-rsi5hi + RW6, PSHADOW to live

L3-rsi5hi (On Deck; in Primary 10-30..11-10, 22 trades −10.32R)
- Record: 527 trades / 28 sessions, −200.27R | −198.33R, avg −0.380R | −0.376R.
- One-big-day check: w/o best day −0.436R; best day 11-12 +13.18R.
- t −12.39, day t −1.83, green 54%. Worst day 11-25 −219.08R. Shrunk −0.318.
- Non-overlap: w/o best −0.503R, shrunk −0.367.
- Primary-book: +0.36R, w/o best −0.072R.
- PSHADOW: 4 sessions (2 traded), 30 trades −11.95R.

RW6 (Testing C, Graveyard origin)
- Record: 227 trades / 30 sessions, +7.03R | +9.33R, avg +0.031R | +0.041R.
- One-big-day check: w/o best day −0.206R; best day 11-12 +38.06R = 542% of total (1 day).
- t 0.57, day t 0.16. Shrunk −0.021.
- By account: Graveyard +37.0R (with latch), Testing C −3.98R, Testing 1 −26.0R.
- Primary-book: −13.51R, w/o best −0.149R.
- PSHADOW: 14 trades −6.61R.

Rule-change context: PSHADOW from 11-23 (dated exception to rule 34(a)); RW6 moved Graveyard → Testing C on 11-13; L3-rsi5hi moved Primary → On Deck on 11-11.

| Criterion | L3-rsi5hi | RW6 |
|---|---|---|
| PRIME ≥20 sessions | 28 PASS | 30 PASS |
| PRIME ≥5 On Deck | 11 PASS | 0 FAIL (PSHADOW sessions do not count, 34(a) / SRCV1) |
| PRIME shrunk | −0.318 FAIL | −0.021 FAIL |
| PRIME w/o best day | −0.436R FAIL | −0.206R FAIL |
| PRIME best day ≤40% | total < 0 FAIL | 542% FAIL |
| C3 ≥30 trades | 505 PASS | 227 PASS |
| C3 ≥8 sessions | 28 PASS | 30 PASS |
| C3 w/o best day (non-overlap) | −0.503R FAIL | −0.192R FAIL |
| C3 green (non-overlap) | 57% PASS | 55% PASS |
| C3 active days | 34 PASS | 34 PASS |
| C3 shrunk | −0.367 FAIL | −0.021 FAIL |
| C3 best-day share | total < 0 FAIL | 398% FAIL |
| FP-C | −0.072R FAIL | −0.149R FAIL |

FP-B: "four" and "one" compete for the same L3 slot.

## Exemptions
- PROT-21 is a change guard on the latch and halt, not an entry exemption. Only "yes" needs it, and its guard is not met.
- No written rule lets a setup skip failing PRIME-RULES / C3-BAR2 criteria. PROT-14 protects C3-BAR2 itself (changing it needs a back-test on the 12 promotions and 5 graduates).
- The only route is the owner's explicit override, as for ST7-MOVE (WW-ST7). Every option would need it for w/o best day, best-day share, shrunk and FP-C.

## Note: arena's strongest live records against the same rules
GEN-261022-05 short (Testing B)
- Record: 223 trades / 7 sessions, +99.31R, avg +0.445R, t 6.57, day t 1.16, shrunk +0.226.
- One-big-day check: w/o best −0.179R; best day 11-20 +121.12R = 122% of total.
- Primary-book: −0.42R.
- Fails: fewer than 20 sessions (and fewer than 8), 0 On Deck sessions, w/o best day, best-day share, FP-C.

GEN-261026-07 short (Testing A)
- Record: 238 trades / 8 sessions, +98.90R, avg +0.416R, t 6.60, day t 1.47, shrunk +0.216.
- One-big-day check: w/o best +0.029R (non-overlap +0.018R); best day 11-20 +94.36R = 95% of total.
- Primary-book: +31.1R, but w/o best −0.041R.
- Passes the C3 counts, w/o best day, green 50%, 23 active days and shrunk. Fails best-day share, FP-C, PRIME's 20 sessions and On Deck.

Both were carried by 11-20 (before BRAKE-BURST) and have made 0 trades since. Keep them in rotation for reps.

## Concentration
All four candidates and three of Primary's four members are gap-down / overbought short fades. On 11-25 the family lost together: L3-fromopen hit its cap, its latch and the −20R halt in Primary, while the same family lost −144.6R / −219.1R / −52.4R outside Primary.
===== end REPORT.md =====
