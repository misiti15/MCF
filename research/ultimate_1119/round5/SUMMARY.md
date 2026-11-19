Educational only — not financial advice

# Round 5 summary: fresh 2023-24 test scored once, 0 of 8 rules beat, nothing deployed (2026-11-19)

## In plain words
- Rounds 1-4 tried 35 candidate setups. None beat our current best setup, ST7-FD (+0.084R per trade after costs on
  the check data, +0.073R without its best day).
- A few ideas looked good on the check data, but they had partly been shaped by that data. A fair test needs data no
  one has looked at, so we kept 2023-01-03..2024-09-13 (427 sessions) unseen and froze 8 rules before downloading it.
- All safety checks passed first: plan hash, both freeze manifests, the 2025-10 parity check, freeze files older than
  every fresh data file, the locked block untouched, enough disk. Then each rule was scored exactly once (11:12:10Z).
- **Result: none of the 8 rules beat.** Seven lose money or break even after costs. The only positive one (H-V2, an
  ETF snap-back buy) makes +0.042R per trade, half the bar, and 72% of its profit comes from one day.
- **Our own benchmark also failed on this window.** ST7-FD came in at −0.016R per trade (it was +0.084R on the check
  half). 2023-24 was a hard period for "buy the dip" setups, mainly on days the market fell.
- The entries themselves are not random: 6 of 8 rules beat a random entry time in the same stock and day. The edge is
  just too small to pay the costs in this period.
- A skeptic re-scored every rule from the saved trade rows, matched the numbers, and upheld the fail on every row.
- **Nothing was deployed.** No setup, account, display name, assignments file or ledger entry was changed.

## Every row (fresh window, costs in, one score each)
Pass bar (pre-registered, FRESH_PLAN sec. 5): avg R > +0.0836, avg R w/o best day > +0.0734, R/session > 0,
day-clustered t >= 2.039 (M = 8), and positive on the check half.

| Rule | What it is | Trades | /session | Avg R | W/o best day | R/session | t | 2023 / 2024 | Signal − random | Check avg R | Beats? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 BOOK-EM | leg E + leg M combined (ULT-32e) | 270 | 0.63 | −0.040 | −0.067 | −0.025 | −0.73 | −0.033 / −0.048 | +0.021 | +0.115 | no |
| R2 leg E | late-afternoon ETF dip, long | 249 | 0.58 | −0.040 | −0.069 | −0.023 | −0.69 | −0.024 / −0.057 | +0.027 | +0.110 | no |
| R3 leg M | one-bar RSI collapse, ADV >= $500M, long | 21 | 0.05 | −0.043 | −0.118 | −0.002 | −0.27 | −0.144 / +0.049 | −0.044 | +0.124 | no |
| R4 ST7-FD | benchmark, current best | 481 | 1.13 | −0.016 | −0.039 | −0.018 | −0.25 | +0.008 / −0.046 | +0.230 | +0.084 | no (bench) |
| R5 NM-ETF-late-dip | benchmark | 256 | 0.60 | −0.044 | −0.063 | −0.026 | −0.69 | −0.038 / −0.052 | +0.087 | +0.052 | no (bench) |
| R6 ST7-base | ST7 on the round-4 chassis | 256 | 0.60 | −0.001 | −0.015 | −0.000 | −0.01 | +0.004 / −0.006 | +0.164 | +0.094 | no |
| H-V1 leg X | late ETF rip, short (borrow fee in) | 88 | 0.21 | −0.141 | −0.193 | −0.029 | −1.38 | −0.194 / −0.107 | −0.108 | +0.105 | no |
| H-V2 leg K | one-bar shock snap in ETFs, long | 192 | 0.45 | +0.042 | +0.012 | +0.019 | +0.43 | +0.056 / +0.030 | +0.159 | +0.187 | no |

Notes on the rows:
- **H-V2, one big day:** 2024-08-23 carries 72% of its total R (`1 day` tag). That day was six index longs (MDY, QQQ,
  TQQQ, SPXL, UPRO, QQQM) all hitting target within 30 minutes: one market bet, not six wins. Counted as one exposure,
  its record is about flat. Its check record also leaned on one or two days (54% best-day share).
- **Best-day share** is "n/a" for the seven rules with a negative total.
- **R4 row count:** the trade file has 483 R4 rows. Two (CFG and FIS, 2024-07-03 at 13:35 and 13:45) have no R value
  because they were signalled after that day's 13:00 early close, so there were no bars to exit on; they are
  excluded, leaving 481. The deploy-stage review also found 4 more R4 entries after an early close (2023-11-24 x3,
  2024-07-03 x1) that did get an R, +2.7R together. Dropping them puts R4 at −0.022R over 477 trades. This is a small
  harness flaw that flatters only the benchmark and changes no verdict; any future harness should block entries after
  an early close.
- **Day cap** never bound, so R2 and R3 are exactly the two legs of R1 run alone.
- **Earnings blackout:** R1 without it had 280 trades at −0.032R, still a fail.
- **Volume** was far below the check half (R4 1.13 vs 3.13 trades per session; R6 0.60 vs 2.23), in line with fewer
  names clearing the ADV gates in 2023-24 (median 624 names a day at >= $95M, 121 at >= $500M).

## Biases (all favour the candidates, so true figures are likely at or below these)
- Today's symbol list: names delisted in 2023-24 (e.g. SIVB, FRC, SBNY) are missing; 54 later listings are empty and
  25 cover under half the sessions; renamed tickers lose early history.
- Today's easy-to-borrow flag and a flat borrow fee flatter H-V1 only (it fails anyway).
- yfinance earnings dates are thinner before 2024, so the blackout is weaker in 2023.
- Signal minus random is the read survivorship does not distort.

## Configurations counted
Cumulative N is **1,044 (up to 1,060)**: 996 (up to 1,012) before round 5, plus 40 in the round-5 volume hunt, plus
8 fresh scorings.

## Honest read
This was a clean, one-time test and every candidate failed it. The ideas that looked best on the check half (R1
BOOK-EM, R2 leg E, R3 leg M) lost money after costs on fresh data. The benchmark ST7-FD also lost slightly, so part of
this is a hostile period for long dip-buying setups (the damage sits on SPY-down days), not only weak candidates. But
"the benchmark failed too" does not make any candidate a winner: none came close to the bar, and the one positive rule
rests on one correlated day. The useful lesson for the next step is that entry timing keeps beating random entries
(6 of 8 rules); what is missing is an edge big enough to survive costs across market regimes, possibly via a
market-direction filter, which would need its own pre-registered test. Following "don't force weak setups", nothing
goes live. The fresh window is now used and cannot serve as a clean test again.

## Rule-change context
All figures are backtests on 1-minute bars with one fixed rule set (LR8 costs, next-minute-open fill, borrow fee for
shorts). No live-account window is quoted, so no `research/ledger.jsonl` rule change falls inside
2023-01-03..2024-09-13. For reference: WB4 went live 2026-11-17 (Testing E), ST7-FD was promoted 2026-10-26, NM-ETF
runs in Primary; all after every backtest window here. No ledger entry was added for round 5, because nothing was
deployed.

## Deployment
None. No rule beat on the fresh window, so no setup, YAML, account, display name, assignments file or ledger entry was
changed.

Files: FRESH_PLAN.md (binding plan), FRESH_RESULTS.md (full results), fresh_once.json (the single score),
fresh_trades.csv.gz (trade rows), FREEZE_HUNT.json / HUNT_FREEZE.md, PARITY_2025-10.json, coverage_fresh.*.

Educational only — not financial advice.
