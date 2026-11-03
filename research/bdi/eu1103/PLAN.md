Educational only — not financial advice

# eu1103 synthesis — what our edge is, the right pool, 09:40, pre-open (owner 2026-11-03)

Research only. No `config/`, setup, exit, backlog, ledger or live-path change was made by any of the four workstreams.
Costs are in everywhere; the locked block 2024-11-01..2025-02-28 was never loaded (asserted in every loader). Live =
**paper** fills, run_id 1, all 5 accounts, 10-06..11-02 (20 sessions, ~12,256 trades). Two-year = backtest (TRAIN
2024-10 + 2025-03..12, VALID 2026). Detail and files: `edge/NOTES.md`, `universe/NOTES.md`, `open/NOTES.md`,
`preopen/NOTES.md` in this folder.

**Configurations counted: 1,002** (edge 25, universe 188, open 16 + 1 descriptive look, preopen 756 gates + 17
descriptive checks). At that count the try-count bar is day-clustered t >= sqrt(2 ln 1002) = 3.72. **No trading result
passes it, and no pre-declared candidate passes its own bar in a way that would make the book green.**

**Rule changes inside the live window (research/ledger.jsonl), mixed into every live figure below:** 10-20 scale-out fix
and per-setup -2R stop in Testing; 10-21 promotion = move, Graveyard opens; 10-23 per-setup stop off in T1/T2/Gen;
10-26 CWT13-z05-long and ST7-FD promoted, MF1 demoted; **10-27 GX1 5-minute clock** (new record version for every lab
setup; latency fell from 76 s to 60 s); **10-28 Primary size ~$5k then ~$4k**; **10-29 Primary -2R latched stop,
BAR90, Generator paused**; **10-30 Testing cost filter CF**, L3-rsi5hi-FD and L3-fromopen-FD to Primary; 11-02
NS3-FD/RW4-FD/MF3-FD/MF5-FD to the Graveyard, R2A legs into Testing 2. The two-year tests are rule-fixed backtests.

## Q1 — What is our edge, really?

**Plainly: today the measurable edge is real but smaller than what we pay to trade it.**

- **The live book, split into parts** (12,256 trades, -1,695R, -0.138R per trade, 2 green sessions of 20):
  market/beta -0.008R + the stock's own day drift against our side **-0.108R** + entry/exit timing **+0.046R** -
  friction **0.068R**. Timing is the only positive line in the book.
- **What the timing is:** short-term mean reversion. 69% of entries are fades; fades earn +0.086R of timing vs -0.010R
  for momentum entries. But the harder the move we fade, the more we lose to that name's drift over the day
  (strongest-fade quintile: timing +0.16R, R after beta -0.21R). Big single-name moves tend to keep going; the quick
  bounce we catch does not pay for it.
- **What our profitable records are:** the 26 profitable setup x account records (1,510 trades, +0.168R, t 2.6) are
  **88% SPY beta** — 24 of 26 are shorts, 79% of their R came on SPY down days. Beta removed: +0.020R per trade (t 0.5),
  +0.001R without 10-22. All 26 take >= 50% of their R from one session. Only one record shows beta-removed R with
  t >= 1.5 (Primary MF2-open-rsimidhi-flowsell-FD, 40 trades, +0.41R beta-removed, t 2.65) — about what ~240 looks give
  by chance.
- **Where the money goes:** we pay for liquidity on almost every trade. Entry fills average +4.4 bps (+0.044R) worse
  than the NBBO mid at the signal; 86% are at or through the far quote, 4% beat the mid; stops slip 0.035R; ~11% of paper
  target exits are "touch" fills that a real order might not get, so realistic friction is ~0.10R per trade. Our median
  stop is 92 bps, so every bp of cost is ~0.01R.
- **Two-year confirmation:** the two cleanest versions of "small scalping edge" both fail after costs. Fade
  normal-volume extremes (A): TRAIN -0.082R, VALID -0.076R, 12/12 configs negative. Ride heavy-volume extremes (B):
  TRAIN -0.065R, VALID -0.058R; picking the strongest movers beats a random in-play entry by +0.03..+0.07R, but the
  random in-play entry loses -0.05..-0.10R after costs. Across every universe bucket the setups beat a random entry on
  the same symbol-day by only ~+0.02..+0.05R.
- **Who is on the other side:** the market makers we cross on every trade (the one party certainly paid); on our
  winners, dip-buyers in gapped-down names on days the market kept falling; on our losers, informed/institutional flow
  that keeps a name trending all day.

**What it isn't:** it is not stock-picking skill we can show, not a universe effect, and not a time-of-day effect.
"Green after costs every day" is not reachable from the current book (2/20 green sessions). The only route the evidence
supports is **cheaper execution first** (passive entries, a larger R unit), then the reversal timing we already have
might clear costs. More filters will not do it.

## Q2 — Is our universe the right pool?

**Verdict: keep the current pool ($95M ADV floor). Do not expand it. Shrinking it helps a little, but only by lowering
cost per R, not by finding better tickers.**

- **Bigger is worse on every test.** Live (the 398 trades below $95M): -0.081R, too few to read. Live-date re-score with
  a $20M floor (2,419 names, not survivor-biased): added names -0.128R (t -7.7) vs base -0.093R, worse in 6/7 setups.
  Two years with a $50M floor: added names worse in 7/7 setups on both splits.
- **Inside today's pool, live R is flat** at -0.13..-0.15R across ADV, price, ATR%, stock vs ETF, ETB status and sector
  (every setup-mix-adjusted bucket within +/-0.04R). The pool does not decide live results; the setups do. Hard-to-borrow
  shorts skipped live (3,902 what-ifs) made -0.095R gross, the same as the shorts we took.
- **Smaller (top 500 by ADV x ATR%):** live paper +0.019R (t 0.42), busiest 8 setups +0.048R (t 1.07); live-date
  re-score +0.036R (t 1.99), green sessions 2/20 -> 5/20; two years +0.037 / +0.053R (t 6.2 / 7.1), green VALID
  sessions 20% -> 39%. About half the trades. **Every kept book is still negative.** It overlaps the Testing cost filter
  CF (in effect since 10-30), but still adds +0.015 / +0.033R on top of a CF-like filter on two years.
- Sector, move-history and "no idiosyncratic names" filters do not hold up across periods. A minimum $0.25/share risk
  looks strong in backtests (t 16.5) but does nothing live (+0.000R), because live friction is quoted spread in bps, not
  cents per share.

## Q2b — Start at 09:40? And the 09:50-09:55 dip/spike then opposite swing

**09:40 is feasible but makes things worse; keep 09:50.**

- **Can the runner react?** Yes. Signal arrives a median 72 s after the 5-minute bar closes (43 s at 09:50-09:59 after
  GX1, 10-27), fill 1.3 s after the signal. Spreads at 09:40/09:45 are ~1.55x midday (median 11 bps vs 9.3 bps at 09:50);
  the spread cap would skip ~2x as many signals. Indicators are warm (60 prior bars). A 09:40 start would need a
  live-path change (`live.no_entry_before` and the hard 09:50 floor in `LabStrategy`).
- **But early signals are worse.** Starting at 09:40/09:45, total R per session falls on TRAIN and VALID for 3 of the 4
  setups that can fire that early (CWT14-pdl, CWT14-pdh, L3-gap-slope-fromopen). Trades entered 09:40-09:49 average
  -0.10 to -0.38R, vs -0.06 to +0.06R for the same symbol-days at 09:50. Only 0.02-0.03R of the gap is extra cost. L3 is
  Primary's best live setup (+0.255R live, 10-20..11-03); an earlier start would hurt it. No live journal data exist
  before 09:50 (no live setup has an earlier window), so this is backtest-only.
- **The 09:50-09:55 reversal loses after costs in all 8 forms on both splits.** Dip in an up morning, go long: n 4,849,
  -0.088 / -0.041R. Spike in a down morning, go short: n 4,679, -0.217 / -0.153R. A SPY filter barely helps (best 0.000R
  VALID). After that bar the next move follows the day's direction; it is not a reversal of the bar. If the owner's read
  is right, it is narrower (at a prior-day level, or on in-play names from a pre-open scan) and needs its own small test.

## Q3 — Pre-open intelligence: decide which setups are on deck at 09:25-09:38?

**No pre-open switch works for the current setups; pre-open data is good at finding the day's movers.**

- **0 of 756 pre-declared gates pass** (pre-market volume, gap, range, prior-day close location, opening 5-minute bar,
  SPY/QQQ pre-market move, breadth, news). Picks made on TRAIN fail on VALID and live. Thresholds drift: a gate set to
  drop 10% on TRAIN dropped 26-33% on VALID and 21-43% live — a fixed pre-open threshold quietly becomes a strangling
  filter. TRAIN lift vs VALID/live lift: Spearman -0.06. Live: green sessions 2/20 -> 4/20 with the best pick, but avg R
  falls -0.134 -> -0.176R. There is no market-level "on deck / off" switch.
- **What works:** a 09:35 scan finds the movers. Ranking the ~900 liquid names, the top 150 by opening 5-minute
  $ volume / adv20 hold 38% / 33% of the day's 50 biggest movers (random 18% / 15%); pre-market range 36% / 33%. That
  fits Move Hunt (33-36 of the top 50 moves start 09:35-09:45). But our setups' avg R is flat across those features:
  big movers hit our targets and stops alike. The gap is a side-taking rule on movers, not a filter.
- **Data:** all of this uses data the runner already has from Alpaca (SIP pre-market bars, snapshots, daily bars, the
  Benzinga news API — HTTP 200 on our keys, ~20 requests per morning). **Needs a NEW source:** short interest (FINRA free
  but twice-monthly and 1-3 weeks stale; FINRA Reg SHO daily short-volume free and next-morning; paid daily estimates
  Fintel ~$15-50/mo, Ortex ~$50-130/mo, S3 institutional — prices from memory, to check); borrow-fee rates (Alpaca gives
  only shortable / ETB flags, current state, no history); ES/NQ futures and the VIX index (paid; SPY/QQQ pre-market and
  VIXY are free proxies); closing-auction imbalances (paid, e.g. Databento, ~$100s/mo). Nothing found argues for buying a
  feed first.

## Owner decisions (5)

Evidence live first. Scope Testing / research only; nothing here touches Primary.

**EXEC1 — Research passive entries: replay the 12,256 live signals with a limit at the NBBO mid, valid 60 s?**
Recommend: **yes** (research only, no live change). Live: entries fill +4.4 bps (+0.044R) worse than the mid, 86% at or
through the far quote; total friction 0.068R per trade = -832R over 10-06..11-02, about the same size as the book's whole
gross loss from the mid (-862R). The replay measures fill rate and the R of filled vs missed signals (adverse selection),
by setup and time of day, on Alpaca historical quotes/trades. Paired with the R-unit re-score (10 busiest setups on two
years at a 0.5-ATR stop held to 15:55, bps per trade and cost share). Any execution change that comes out of it goes to
the backlog and Testing first. Reply: "EXEC1 yes" / "EXEC1 no"

**BETA1 — Show beta-removed avg R beside avg R in reviews and on the dashboard?**
Recommend: **yes** (reporting only, no trading change). Live: 88% of the 26 profitable records' R is SPY beta; after beta
+0.020R per trade (t 0.5), +0.001R without 10-22; 1 of 26 has beta-removed t >= 1.5. Shown next to "Avg R w/o best day"
and the day-type split, so a short-beta record on falling days is not read as setup skill in promotions. Reply: "BETA1
yes" / "BETA1 no"

**UNI1 — Live check in Testing 1 and Testing 2 only: lab setups trade only the top 500 names by ADV x ATR%?**
Recommend: **optional** (it lowers cost per R; it adds no edge). Live paper: +0.019R all setups (t 0.42), +0.048R busiest
8 (t 1.07), every kept book still negative; live-date re-score +0.036R (t 1.99), green sessions 2/20 -> 5/20; two years
+0.037 / +0.053R (t 6.2 / 7.1), roughly half the trades. Overlaps CF (since 10-30). Would enter `research/backlog.jsonl`
and its gates first; not Primary. The rest stays as is: do not lower the $95M floor, do not add hard-to-borrow names,
no sector or move-history filters. Reply: "UNI1 yes" / "UNI1 no"

**OPEN1 — Keep the 09:50 start, close the general 09:50-09:55 reversal idea?**
Recommend: **yes** (no change). Two years: starting at 09:40/09:45 makes total R per session worse for 3 of 4 setups that
can fire early; the 09:40-09:49 trades are -0.10 to -0.38R vs -0.06 to +0.06R for the same symbol-days at 09:50; latency
and spread are not the blocker. The reversal loses in all 8 forms on TRAIN and VALID. No live data before 09:50 exist.
Reply: "OPEN1 yes" / "OPEN1 narrow" (also pre-declare one small, max-8-config test of the reversal only at prior-day
levels or on scan-flagged in-play names) / "OPEN1 no"

**PRE1 — No pre-open on/off switch; instead record borrow and short-volume data daily, and aim new-setup searches at the
09:35 mover scan?**
Recommend: **yes** (data recording and research direction only; no setup is gated). 0 of 756 gates pass; thresholds
drift so out of sample they cut 21-43% of trades; live green sessions 2/20 -> 4/20 but avg R -0.134 -> -0.176R. The
09:35 scan holds 2x random of the day's top-50 movers on TRAIN and VALID. Recording at ~09:25 the free Alpaca borrow flags
and the free FINRA Reg SHO daily short-volume ratio lets a borrow / short-pressure feature be back-tested in a few months
without buying a short-interest feed. Reply: "PRE1 yes" / "PRE1 no"

## What we are not proposing
A 09:40 lane for existing setups; a lower ADV floor; any pre-open gate; sector, move-history or idiosyncratic-name
filters; paid short-interest, futures or imbalance feeds now; any Primary change. Smaller leads stay in the notes only:
news-name slot priority (post hoc, +0.009..+0.027R, same sign in all three splits), trading the market view in SPY/QQQ,
hedged peer-laggard catch-up (the 1102 lead).

**Today's win (charter):** a measured map of where the book's R comes from (beta / drift / timing / friction), and the
universe, 09:40 and pre-open questions closed with their numbers — so the next work goes where the R actually leaks:
execution cost.
