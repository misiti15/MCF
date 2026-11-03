Educational only — not financial advice

# eu1103 / edge — Q1 "what is our edge?" (owner 2026-11-03)

Research only: no config/, setup, exit or live-path change; nothing proposed for live. Costs always in. The locked block
2024-11-01..2025-02-28 was never loaded (pyarrow read filter + assert). Live = paper trades run_id 1 in all five accounts;
two-year = backtest. They are labelled separately throughout (rule 7).

**Configurations counted: 24 two-year configs (pre-declared in PLAN.md, committed b5ee580c5 before scoring) + 1 live
decomposition (no tuning).** Files: `decompose.py`, `extra.py` (live), `xs2y.py` (two-year), `by_setup.csv`,
`profitable_alpha.csv`, `results.json`, `extra.json`, `results_2y.csv`.

## Rule changes inside the live window 10-06..11-02 (research/ledger.jsonl effective dates)
10-20 scale-out fix, twin cap, per-setup -2R stop in Testing; 10-21 promotion = move, Graveyard opens; 10-23 per-setup
stop off in T1/T2/Gen; 10-26 CWT13-z05-long, ST7-FD promoted, MF1 demoted; **10-27 GX1 5-minute clock (new record version
for every lab setup)**; 10-28 Primary size ~$5k then ~$4k, three Primary setups rotated out; **10-29 Primary per-setup -2R
latched stop**, BAR90, Setup Generator paused; **10-30 Testing cost filter CF**, L3-rsi5hi-FD and L3-fromopen-FD to Primary;
11-02 NS3-FD/RW4-FD and MF3-FD/MF5-FD to the Graveyard, R2A legs in Testing 2. R is per trade, so the size changes do not
scale R, but the stop, CF and slot changes change which trades exist. Every live figure below mixes these periods.

## Failures first

1. **Once market direction is taken out, the profitable live setups have no edge we can show.** The 26 setup x account
   records with 20+ live trades and avg R > 0 (1,510 trades, +252.9R, +0.168R per trade, day-clustered t 2.6) are worth
   **+0.020R per trade after their SPY-beta part is removed (t 0.5), and +0.001R without their best session (10-22,
   94% of that remainder)**. 88% of their R is SPY beta. 24 of the 26 are shorts; 79% of their R came on SPY down days
   (+200.9R of +252.9R). This is chosen after the fact (the 26 are the winners of ~240 records), so even the +0.168R is
   an upper bound.
2. **Only one record has beta-neutral alpha with t >= 1.5:** Primary MF2-open-rsimidhi-flowsell-FD, 40 trades, 9 sessions,
   +0.904R, of which +0.41R alpha (t 2.65), +0.36R alpha without its best day. 40 trades is a hint, not evidence; with
   ~240 records looked at, one t of 2.65 is about what chance gives.
3. **All 26 profitable records take >= 50% of their R from one session** (one-big-day check); 10 of 26 stay positive
   without that session, 5 of 26 stay positive on alpha without it.
4. **The book: 2 green sessions out of 20** (all accounts together, -1,695R on 12,256 trades, -0.138R per trade,
   avg R w/o best day -0.148R).

## Q1a. Where the live R comes from (12,256 trades, 20 sessions 10-06..11-02, `decompose.py`)

Per trade, with rps = |entry - stop|: R_net (journal, costs in) = **R from the signal-time NBBO mid** minus **entry
friction** (fill vs mid + the 2c stop haircut). R from the mid splits into **market** (beta x SPY return over the hold, beta
from 5-minute returns, shrunk to 1), **stock-day drift** (the stock's own open->15:55 move net of beta, pro-rated by
minutes held, signed by our side) and **timing** (the rest: what our entry/exit timing earned on the stock itself).

| R per trade (live) | n | R_net | from mid | market | stock drift | timing | friction |
|---|---|---|---|---|---|---|---|
| all accounts | 12,256 | -0.138 | -0.070 | -0.008 | **-0.108** | **+0.046** | **0.068** |
| Primary | 761 | -0.042 | +0.025 | +0.043 | -0.105 | +0.088 | 0.067 |
| Testing 1 | 3,402 | -0.118 | -0.055 | +0.007 | -0.138 | +0.076 | 0.063 |
| Testing 2 | 4,149 | -0.135 | -0.062 | -0.023 | -0.091 | +0.052 | 0.072 |
| Graveyard | 2,942 | -0.143 | -0.076 | +0.006 | -0.140 | +0.058 | 0.067 |
| Setup Generator | 1,002 | -0.282 | -0.211 | -0.078 | +0.014 | -0.147 | 0.071 |
| 26 profitable records | 1,510 | +0.168 | +0.224 | **+0.148** | -0.098 | +0.175 | 0.057 |
| ... on SPY down days | 546 | +0.368 | +0.422 | +0.260 | +0.059 | +0.103 | 0.054 |
| ... on SPY quiet days | 546 | -0.024 | +0.034 | +0.066 | -0.091 | +0.059 | 0.058 |
| ... on SPY up days | 418 | +0.156 | +0.215 | +0.109 | -0.314 | +0.419 | 0.059 (88% of it one day) |

Book totals: R_net -1,695R = market -103R + stock drift **-1,327R** + timing **+567R** - friction **-832R** (+ rounding).

- **Market direction (beta):** close to zero for the book, but it is almost all of what the winners have. Our winners are
  a short-beta position on falling mornings, not a stock-picking edge.
- **Timing / mean reversion: this is the one positive line (+0.046R per trade, +567R).** 7,572 of 11,001 classified
  entries (69%) are fades (against the stock's prior 30-minute move); fades earn +0.086R timing vs -0.010R for momentum
  entries. Among the profitable records fades make +0.220R vs momentum +0.080R. So we do capture short-term reversal.
- **But we fade names that keep going over the day (stock drift -0.108R, the largest loss line).** The harder the move we
  fade, the more timing we earn and the more drift we lose: by prior-30-minute move quintile, the strongest fades have
  timing +0.16R but alpha (R_net minus market) -0.21R; entries with the move (top quintile) have timing -0.02R and
  alpha -0.10R; the near-flat quintile is least bad (-0.08R). A big intraday move in a single
  name is, on average, information that persists into the close, and the quick bounce we catch does not pay for it.
- **Cost / fill quality: friction 0.068R per trade (832R in total) — about as large as the whole gross loss.** Even at the
  mid with zero friction the book would be -0.070R per trade, so friction is not the only problem, but it turns every
  "small edge" negative: our median stop is 92 bps, so 4.4 bps of entry cost is already 0.044R.
- **One big day:** 10-22 carried the profitable records (best-day share 0.34 for the group, 0.94 of its alpha).

## Q1b. Our fills vs the signal price and vs the bar (are we paid for liquidity or paying it?)

| measure (live, 12,253 fills with quotes) | value |
|---|---|
| entry fill vs NBBO mid at the signal | **+0.044R / +4.4 bps worse** (median +0.037R) |
| fills better than the mid | **4.1%** |
| fills at or through the far side (ask for buys, bid for sells) | **86.4%** |
| quoted half-spread at the signal | 0.044R (median full spread 7.1 bps) |
| entry fill vs the next 1-minute bar open | +0.020R worse (Primary +0.040R, Graveyard +0.046R) |
| stop exits vs the stop price | 0.035R worse (paper), plus the 2c journal haircut (0.024R on average) |
| target exits where the bar never traded 1c through the target (paper "touch" fills) | **10.7%** of 5,427 target exits; if they had not filled, about -0.029R per trade on the book |

**We pay for liquidity, every time.** Market entries cross the full spread (86% at or through the far quote), stops
slip further, and on paper about 1 target fill in 10 is a touch that a real resting order might not get. Realistic
all-in friction is about **0.07R in the journal and ~0.10R with the touch-fill optimism removed**.

## Q1c. Who is on the other side of our winning trades?

Plainly, from the numbers above (inference, not observed counterparties):
- **The market makers / wholesalers we cross** on every entry. They earn our ~4.4 bps entry spread plus the stop slippage
  on every trade, winner or loser. They are the one party that is certainly paid.
- **On the winners (gap-down / flow-sell shorts in the first hour of down days):** whoever is buying the morning dip in
  names that already gapped down — dip-buyers, retail "buy the gap-down" flow, and passive / index buying at the open —
  on days when the whole market keeps falling. We win because SPY fell (88% beta), not because we out-read them on the
  stock.
- **On the losers that dominate the book (fades of names that keep trending):** informed or institutional flow working
  a large order through the day (news, re-rating, sector rotation). Their persistent pressure is the -1,327R stock-drift
  line. In short: **we provide immediacy against trends but pay the spread to do it** — the worst of both roles.

**So what is our edge today?** Measured live: a small, real short-term reversal timing effect (+0.05R per trade before
costs, +0.09R on fades) — smaller than the ~0.07R we pay to take it and far smaller than the trend we stand in front of.
The rest of the record is SPY direction and a few big days. Our *structural* strengths (breadth, testing discipline,
speed of iteration, no emotions) have not yet been turned into a measured market edge; they are what we would use to find
one.

## Q1d. Where a retail system with our strengths can realistically have an intraday edge (ranked)

Ranked by (size of the live evidence for it) x (fit to our strengths) / (data cost). Each has one concrete test. Tests 1
and 2 were run on two years (below); the rest are not run.

| # | edge | why it fits us | one concrete test | data |
|---|---|---|---|---|
| 1 | **Ride heavy-volume idiosyncratic moves, beta-hedged** (stocks in play continue) | our largest live loss is fading names that keep trending (-1,327R); 3,000-name scan at 09:40-09:50 is our strength | **Test B, run**: RVOL >= 3, top-10 \|idio z\|, side with the move, SPY hedge, stop 0.5 ATR, hold to 15:55 | have (SIP bars) |
| 2 | **Fade normal-volume idiosyncratic opening extremes, beta-hedged** (liquidity shocks revert) | timing/fades is our only positive live line; hedging removes the beta that drives our records | **Test A, run**: RVOL < 1.5, top-10 \|idio z\|, fade, SPY hedge, exit 10:30 | have |
| 3 | **Stop paying the spread** (passive / mid-peg entries) | 86% of fills at or through the far quote; 0.044R per trade = ~540R on this window | replay the 12,256 live signals with a limit at the mid valid 60 s, on Alpaca historical quotes + trades: fill rate, and R of filled vs missed signals (adverse selection) | have (Alpaca historical quotes/trades) |
| 4 | **Bigger R unit, fewer trades** (costs are fixed in bps, so a 92-bps median stop makes 4.4 bps = 0.044R) | discipline: simple rule, fewer levers | re-score the 10 busiest live setups on 2 years with stop 0.5 ATR and hold to 15:55 vs their live geometry; report bps per trade and friction share | have |
| 5 | **Trade the market view explicitly in SPY/QQQ** instead of through 30 short-beta stock trades | 88% of the winners' R is beta; index spread ~0.3 bps vs 4.4 | 2-year SPY/QQQ: 09:30-09:50 index drive and breadth -> 09:51-15:55 continuation vs reversal, costs in, beside the existing intraday_momentum setup | have |
| 6 | **Peer/sector laggard catch-up, hedged** | breadth; 1102 found +0.075R over day-matched random (t 2.43) | the queued mh-1102-group-laggard-hedged with a sector-ETF leg | have (sector ETFs as bars) |
| 7 | **Overnight-news / earnings gap drift** (pre-market selects, 09:35-09:45 confirms) | Move Hunt: 33-36 of the top 50 moves start 09:35-09:45 | gap >= 3% with a news item 16:00-09:30 vs without; ride hedged to the close | Alpaca News API (Benzinga, included with Alpaca market data; check plan) or an earnings calendar |
| 8 | **Pre-market scan decides the day's pool** (Q3) | 09:25-09:38 scan of 3,000 names | rank by pre-market $ volume and gap; use top 50 as the only universe for #1/#2 | have (SIP pre-market bars) |
| 9 | Short-interest / borrow squeezes | — | high-SI names' gap-up continuation | **new data**: FINRA SI free but bi-monthly, ~2 weeks late; Fintel ~$15-40/mo, Ortex ~$50-150/mo retail, S3 institutional (thousands). Alpaca gives only shortable / easy-to-borrow flags |
| 10 | Closing-auction imbalance | — | MOC imbalance direction vs 15:50-16:00 move | **new data**: NYSE/Nasdaq imbalance feeds (not in Alpaca; e.g. Databento, usage-priced, roughly $100s/mo) |

Not on the list on purpose: plain ORB on stocks in play (live as orb20_a; 2-year +0.008R, research/bdi/regime1009) and
more single-name filters on fades (the night1102 work: 0 of 26 adjustments pass).



## Two-year tests (backtest; PLAN.md pre-declared, 24 configs; `xs2y.py`, `results_2y.csv`)

TRAIN 2024-09-30..10-31 + 2025-03..12 (231-235 sessions), VALID 2026-01-01..10-05 (189-190 sessions), lab universe
(1,226 names), ~8-10 trades per session per config, costs in, SPY hedge costs in, R = 0.5 x ATR14 (the stop).
Bar for a primary: TRAIN and VALID avg R > 0, VALID t >= 2.52 (sqrt(2 ln 24)), beats baseline in both, w/o best day > 0,
up and down regimes > 0.

### Failures first: both tests fail. 0 of 24 configurations are positive in both TRAIN and VALID.

| primary (pre-declared) | split | n | avg R | t | w/o best day | vs day-matched random (t) | up / flat / down R | WF months + |
|---|---|---|---|---|---|---|---|---|
| **A** quiet fade, 09:50, exit 10:30, hedged | TRAIN | 2,259 | **-0.082** | -4.78 | -0.085 | -0.007 (-0.42) | -0.10 / -0.11 / -0.04 | 8% |
| | VALID | 1,898 | **-0.076** | -3.90 | -0.080 | -0.020 (-1.09) | -0.06 / -0.10 / -0.07 | 20% |
| **B** in-play ride, 09:45, exit 15:55, hedged | TRAIN | 1,860 | **-0.065** | -1.72 | -0.076 | +0.010 (+0.30) | -0.05 / -0.13 / -0.01 | 33% |
| | VALID | 1,567 | **-0.058** | -1.23 | -0.074 | +0.032 (+0.78) | -0.16 / +0.11 / -0.14 | 30% |

- **Test A (fade normal-volume extremes) is dead on every neighbour:** all 12 configs negative in both splits (TRAIN -0.05
  to -0.14R, VALID -0.05 to -0.10R) and none beats the day-matched random entry in both splits. The live "timing from
  fades" (+0.05-0.09R before costs) does not survive as a market-neutral, costed, cross-sectional rule. 09:40 is the
  worst decision time (-0.10 to -0.14R): the earlier we fade, the more the open's move keeps going.
- **Test B (ride heavy-volume extremes) is the better half but still negative.** Every one of the 6 VALID configs beats
  its day-matched random in-play baseline (+0.03 to +0.07R; best t 1.83), and the 09:50 / 10:30 config does so in TRAIN
  too (+0.080R, t 2.64; raw avg R +0.026 TRAIN, -0.006 VALID). So *choosing the strongest idiosyncratic movers among
  in-play names, in their direction, carries some information* — about +0.05R over random — but the random in-play
  entry itself loses ~-0.05 to -0.10R after costs, and the net stays below zero. Best raw config: 09:50, exit 10:30,
  unhedged: TRAIN +0.026R (t 0.79, w/o best day +0.011, 57% of R one day), VALID -0.006R (t -0.19). Not a candidate.
- **Hedging with SPY made every config worse** (by 0.01-0.04R): the hedge costs ~0.02R and removes beta that, on these
  days, was slightly in our favour. Beta-neutral is not free at our R size.
- **Neither is positive on up AND down sessions.** B in VALID makes money only on flat sessions (+0.04 to +0.11R) —
  noted, not tuned (that would be a new lineage step).

### What the tests say about our edge
The two most natural "edges" for a fast, broad, disciplined scanner — fade the liquidity shock, ride the informed
move — are both under water after the production cost (1c + 1 bps per side, the early-session spread multiplier, the hedge
leg), even with a 0.5-ATR stop that keeps costs a small share of R. The information we can measure (Test B's +0.05R over random) is smaller than one
round-trip of costs. That is the honest size of our "extremely small, almost scalping edges": real, but below costs
unless execution costs fall (list item 3) or the R unit grows (item 4).

## Summary for the owner (Q1)

1. **What our edge is (measured):** a small short-term reversal timing effect (+0.05R per trade before costs live) and
   some selection information in in-play names (+0.05R over random on two years). Both are smaller than our costs.
2. **What our record is (measured):** the profitable live setups are a short-SPY bet on falling mornings (88% of their
   R is beta; +0.020R per trade left after beta, +0.001R without 10-22). One record (Primary MF2-open-rsimidhi-flowsell-FD)
   shows beta-neutral alpha (t 2.65 on 40 trades) — a hint, inside what ~240 looks would give by chance.
3. **Where the money goes:** friction 0.068R per trade (-832R; we cross the spread on 86% of fills, 4.4 bps per entry,
   ~0.10R all-in with paper touch-fill optimism removed) and standing in front of trending names (stock drift -1,327R).
4. **Who is on the other side:** the market makers we pay on every trade; dip-buyers in gap-down names on the days the
   market keeps falling (our winners); informed / institutional flow in names that trend all day (our losers).
5. **Next tests, best first:** #3 passive entries (largest, cheapest, uses the data we have), #4 bigger R unit, #5 trade
   the market view in SPY/QQQ, #6 hedged peer laggards. A "green every day" goal is not reachable from the current
   book: it had 2 green sessions of 20; any path there goes through lower costs first, not more filters.

**Today's win (charter):** a measured map of where the book's R comes from (beta / drift / timing / friction per account
and setup), and two pre-declared edge hypotheses closed with their numbers.

Nothing in this folder needs a new data source. Items 9-10 in the list do (short interest; auction imbalances), with
rough costs given there.
