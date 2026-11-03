Educational only — not financial advice

# eu1103 / preopen — what can we know by 09:25-09:38, and can it switch setups on or off? (owner Q3, 2026-11-03)

Research only. Nothing in `config/`, no setup, exit, ledger, backlog or live-path file was changed. Costs are in
everywhere: two-year = production 1c + 1 bps per side, +2c on stops, time-of-day entry multiplier (`gates.lab_trades`);
live = journal `pnl_adj` / $ risk. Live means **paper** fills (rule 7). The rule-19 locked block 2024-11-01..2025-02-28
was never loaded or requested: asserted in every fetcher and loader, the 1-minute cache is filtered at read time, and
the news window for 2025-03-03 is clamped to start 2025-03-01. Pre-declaration: `PLAN.md` (committed 79290830d before
any feature was joined to an outcome).

**Configurations: 756 pre-declared gates** (14 features x 6 cuts x 8 setups + the pooled book), **plus 17 descriptive
checks** (16 big-mover rankings, 1 news yes/no split, added afterwards and labelled post hoc). Tercile tables (126 cells)
are descriptive only. Try-count bar at N = 773: day-clustered t >= sqrt(2 ln 773) = 3.65.

Trades: the 8 busiest live setups (one per family) on the two-year open frames, built by eu1103/universe's `score2y.py`
(the live modules' own mask() / score(), first signal per symbol-day, live min_adv per setup). TRAIN 2024-10 +
2025-03..12 (234 sessions, 183,856 trades), VALID 2026-01..03 + 2026-07-01..09-15 (114 sessions, 112,595 trades).
Live: run_id 1, all 5 accounts, 2026-10-06..11-02 (20 sessions, 12,295 trades; 3,881 from the 8 setups, which
traded on 14-16 of those sessions). 11-03 was excluded (session still open).

## Failures first

1. **No pre-open gate passes. 0 of 9 picks** (one per setup plus the pooled book, each the best admissible TRAIN gate)
   lifts avg R on VALID and live while keeping >= 70% of trades and >= 90% of top-decile winners on both
   (`chosen.csv`). Per-setup TRAIN lifts were tiny to begin with (+0.003 to +0.031R on bases of -0.10 to -0.02R).
2. **The thresholds do not travel.** Gates set to drop 10% on TRAIN dropped 26-33% on VALID and 21-43% on live (all
   picks except L3, whose opening-bar cut dropped ~0% out of sample)
   (pre-market volume, gaps and the SPY / QQQ pre-market move shift between regimes), so 8 of the 9 picks break the
   70% / 90% retention rule out of sample. A fixed pre-open threshold silently becomes a 30-40% filter in a different
   market — the strangling the charter warns about.
3. **TRAIN ranking carries nothing.** Across all 756 gates, Spearman of TRAIN lift vs VALID lift = -0.06 (p 0.09) and
   vs live lift = -0.06 (p 0.12). Of 83 gates admissible and positive on TRAIN, 42 are positive on VALID and 33 on live
   — the coin-flip rate. 7 are positive on TRAIN, VALID and live with retention on all three; about that many are
   expected by chance (`carryover.csv`), and the largest of them is +0.03R.
4. **No gate makes days green.** Pooled-book VALID: 20% of sessions green in total R (and avg R) before, 29% after the
   pooled pick, with no lift in avg R (-0.0601R before vs -0.0595R after, 69% of trades kept). Live: 2 of 20 sessions
   green before, 4 of 20 after, but avg R fell from -0.134R to -0.176R. The owner's goal (green after costs every day
   in total R and avg R) is not reached by any pre-open switch tested; the book is negative before and after.
5. **The "on deck" market switch does not exist in this data.** Four of the nine picks were market-level (QQQ vs SPY
   pre-market x3, pre-market breadth x1): 0 pass. Pooled terciles of the SPY pre-market move in the trade direction
   change sign between splits (TRAIN best tercile = against the trade, VALID best = with it, live best = flat SPY).
6. **Pre-market volume / gap / range do not sort setup winners.** Pooled tercile spreads are <= 0.03R on TRAIN and
   VALID with no stable order (`results.json` -> terciles_pooled).

## What the data does say

- **Pre-open data finds the movers, not the winners.** Ranking ~840-990 liquid names (ADV >= $95M) each morning, the
  top 150 hold 2x the random share of the day's top-50 movers (rest-of-day range from 09:40 in ATR):
  opening-bar $ volume / adv20 38% TRAIN / 33% VALID (random 18% / 15%), pre-market range 36% / 33%, pre-market
  relative $ volume 34% / 31%, overnight news count 32% / 29%, pre-market gap 33% / 29% (`movers.csv`). So a
  09:35 scan can put the likely big movers on deck — but avg R of the 8 setups is flat across the same features: big
  movers hit targets and stops alike. This fits Move Hunt (33-36 of the 50 biggest moves start 09:35-09:45): the moves
  are visible early; our setups do not yet have a side-taking edge on them.
- **Overnight news is the steadiest small tilt (post hoc, 1 check).** Trades on names with >= 1 overnight Benzinga
  article: TRAIN -0.070R vs -0.082R without (t 2.20), VALID -0.053 vs -0.062 (t 1.35), live -0.115 vs -0.142 (t 1.19);
  21% / 21% / 29% of trades. Same sign in all three, but it cannot be a gate (keeping only news names keeps 21-29% of
  trades) and it is still negative. Possible use: slot priority when setups compete for a name (a sizing / priority
  idea, not a filter) — would need its own pre-declared test.
- **Leads, not proposals (chance level, < +0.03R):** RW7-gapdn-bounce-early-short-FD off when SPY's pre-market move is
  in its top 10% up (+0.003 TRAIN t 0.46, +0.021 VALID, +0.027R live, ~88-92% kept); pooled: skip the 10% of names with
  the quietest opening 5-minute bar (+0.002 / +0.000 / +0.001R).

## What we can know by 09:25-09:38 — data sources

| Feature | Source | Available to the live runner? | Cost |
|---|---|---|---|
| Pre-market volume, range, last price, gap (04:00-09:30) | Alpaca SIP bars (extended hours are in the SIP feed) | Yes — same plan; 30-min bars for 1,226 names x 1 day = 7 requests, ~4 s | none new |
| SPY / QQQ / sector SPDR pre-market move (futures proxy) | Alpaca SIP bars | Yes | none new |
| Opening bars 09:30-09:38 | Alpaca SIP bars / stream | Yes (already used) | none |
| Prior-day close location, ATR, ADV | Alpaca daily bars | Yes | none |
| Overnight news count / headlines | Alpaca news API `/v1beta1/news` (Benzinga) — checked read-only, HTTP 200 on our keys, history back to 2024 | Yes — ~13 requests per morning for 1,226 names | none new |
| Snapshots (latest quote / trade / minute bar / prev day) | Alpaca `/v2/stocks/snapshots` — HTTP 200 | Yes | none |
| Shortable / easy-to-borrow | Alpaca assets API — current state only, no history | Yes going forward; cannot be back-tested until we record it daily | none |
| **Short interest** (shares short, days to cover) | **NEW source.** FINRA equity short interest (free, twice monthly, published ~7-8 business days after settlement, so 1-3 weeks stale); FINRA Reg SHO daily short-sale volume files (free, daily, next-morning usable — short *volume*, not interest); commercial daily estimates: Ortex (retail ~$50-130/month), Fintel (~$15-50/month), S3 Partners / IHS Markit (institutional, five figures a year). Prices are approximate, from memory, to be checked before buying. | No | free (FINRA) to $$$ |
| Index futures (ES / NQ) overnight | NEW source (not on Alpaca stock data): e.g. Databento CME (usage-priced), Polygon/other futures feeds | No | paid |
| VIX | NEW source (Cboe index data); VIXY ETF pre-market on Alpaca is a free proxy | proxy only | free proxy / paid index |

Cheapest next step if wanted: start **recording** each morning's borrow flags and FINRA daily short-volume ratio
(both free) so a short-side borrow / short-pressure feature can be back-tested in a few months. Nothing here argues
for buying a paid feed first: the free pre-open features we could test did not separate winners.

## Rule-change context (owner rule 2026-11-02)

Two-year numbers are fixed-frame backtests: no ledger change applies inside them. The live window 10-06..11-02 contains
(research/ledger.jsonl, as summarised in research/bdi/night1102/PLAN.md): 10-20 scale-out fix / twin cap / Testing
per-setup -2R stop; 10-21 promotion = move, Graveyard opens; 10-22 Primary removals; 10-23 per-setup stop off in
T1 / T2 / Gen; 10-26 promotions and MF1 demotion; **10-27 GX1 5-minute clock (new record version for lab setups)**;
**10-28 Primary size ~$5k then ~$4k**; **10-29 Primary per-setup -2R latched stop, BAR90, Setup Generator paused**;
**10-30 Testing cost filter CF, two L3 setups promoted**; 11-02 R2A legs into Testing 2, NS3-FD / RW4-FD to the
Graveyard. The live gate results mix trades from before and after these changes; with 14-16 sessions per setup they
are a diagnosis, not evidence.

## Caveats

- Lab universe is today's list applied to the past (survivorship, rule 19). Live features use Alpaca raw daily bars
  (ATR = 14-day mean true range, adv20 = 20-day mean $ volume, both prior-only); the two-year features use the same
  formulas on raw Alpaca daily bars, so scale matches, but they are not the lab frame's own atr_d.
- Live `pm_rvol` uses pre-market bars from 2026-09-03..10-05 as its trailing 20-session median; those dates sit inside
  the old Sep 16 - Oct 5 holdout, used only as a trailing baseline, never scored.
- 30-minute pre-market bars: the last pre-market bar ends 09:30, so features are "known at 09:30", not 09:25. A 09:25
  version would use bars to 09:00 plus a snapshot; not tested.
- Live has 3,881 trades of the 8 setups on 14-16 sessions; one session can swing a setup's live lift.

## Day's win (charter)

A measured negative with a positive by-product: pre-open data from our existing Alpaca plan (pre-market bars + the
news API, both confirmed on our keys) ranks the day's big movers at 2x random by 09:35 — a free, simple "on deck
names" list for Move Hunt and for new setups to aim at — while 756 pre-declared pre-open switches show that the same
data does not tell our current setups when to stand down. The missing piece is side-taking edge on movers, not a
pre-open filter.

## Files

`PLAN.md` (pre-declaration), `fetch_pm.py` (pre-market bars), `fetch_news.py` (news counts), `fetch_daily_hist.py`,
`fetch_live.py`, `build_o5.py` (opening bar), `features.py`, `gates.py` -> `all_gates.csv` (all 756 configs on TRAIN),
`chosen.csv` (the 9 picks on TRAIN / VALID / live), `results.json`; `carryover.py` -> `carryover.csv` (every config on
VALID and live, diagnostic); `movers.py` -> `movers.csv`. Scratch data (pre-market bars, news, features, trades) was
deleted after the run; rerun the fetchers to rebuild (~40 min, read-only Alpaca GETs).

Educational only — not financial advice
