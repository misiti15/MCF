# Edge principles from 336 Chat with Traders episodes, and what they mean for MCF

*Educational only - not financial advice. Paraphrased synthesis of the `edge_principles` fields in
`research/bdi/cwt/extract/batch_0*_episodes.jsonl` (2,348 principles from 336 episode records). Guests' numbers are
their own claims, unverified. Nothing here changes a setup; anything that would change trades goes to the backlog
first (RESEARCH_RULES 16).*

## Method
- Each principle was matched to themes by keyword (one episode counts once per theme; one principle can match more
  than one theme). The counts are **approximate** and only rank the themes; read the examples, not the decimals.
- "MCF today" checks the repository: `config/default.yaml`, `docs/RESEARCH_RULES.md`, `research/backlog.jsonl`.
- **Type:** *guard* = a portfolio/ops guard or report that does not change which trades are taken in normal
  conditions (can ship as housekeeping, rule 15, if it never binds on the history - verify first); *setup change* =
  changes entries, exits, sizing or filters (backlog first, rule 16).

## The 14 most repeated principles

| # | principle (paraphrased) | episodes (approx.) | MCF today | how it could apply | type |
|---|---|---|---|---|---|
| 1 | **Costs and liquidity decide whether a small edge exists.** Measure real slippage per trade; trade only liquid names; commissions and spreads can eat a strategy (Radge: an illiquid strategy lost 11-15%/yr to slippage; Evans: 20 bps round trip kills scalps). | ~125 | Yes: costs always in (rule 1), production cost model, 3x on extended tier. Ideas open: ops-stop-slippage, sw-w5-fill-audit, sw-w5-cost-tod-multiplier. | Ship the daily fill audit (live fills vs SIP NBBO) and calibrate stop slippage and opening-spread multipliers from it. This is the cheapest real edge protection MCF has. | guard (reporting, cost model calibration) |
| 2 | **Know your numbers per setup; review in groups.** Track every setup in a spreadsheet; judge in blocks of ~20 trades (win %, win/loss size, streaks), not single trades (Beggs, Grittani, Walker: one subscriber found all profit came from 3 setups). | ~71 | Yes: EOD review, per-setup scorecards, Testing lifecycle (rule 20), plain-English names. | Add a rolling 20-trade block per setup (win %, avg R, max streak) to the EOD report next to the backtest expectation. | guard (report) |
| 3 | **Edges decay; keep a pipeline and monitor live vs backtest.** Expect an intraday edge to fade within months (Azbel: 3-6 months), keep replacements coming (Chan: a pool where some die and some are born), notice when the Russell-close or index-add trade gets crowded (Davis, Schwager/Balarie). | ~72 | Mostly: ledger conflict check (rule 12), weekly backlog re-run (rule 17), Testing account demotion (rule 20). | Add a decay alarm to the EOD report: flag a primary setup whose last 40 trades' expectancy is more than 2 standard errors below its backtest expectation. Report only; demotion stays the owner's call. Cutting size on decaying setups is a setup change. | guard (alarm) / setup change (sizing) |
| 4 | **Robustness before money.** Out-of-sample, Monte Carlo of trade order, fixed parameters across markets (Radge's GLD pattern that fails on stocks), pay to disprove ideas cheaply. | ~60 | Yes: rules 2-4, 18-19 (locked block, try-count t bar, regime and walk-forward gates). | Add a Monte Carlo drawdown line (reshuffled trade order, 95th percentile) to each finalist report so sizing sees the likely worst drawdown, not the historical one. | guard (reporting) |
| 5 | **Regime awareness / playbook switching.** Trade momentum setups in trending, high-range markets and mean reversion in balanced ones; know why a strategy makes money so a regime mismatch is not mistaken for a broken system. | ~77 | Tested and failed as real-time gates: bdi-rg-signals, bdi-rg-g1..g6, ix-gate (912 configs, 0 pass). Rule 19 already demands profit in up AND down sessions. | Keep the up/down gate. The guests' version (switch playbooks) needs a regime known at entry; regime1009 found none at 10:00/10:30. Use daily-level gates only for daily books (TESTPLAN C8). | setup change |
| 6 | **Reduce size after losses / trade smaller in drawdowns.** After a losing streak size down for weeks (Sanghvi, Sykes); equity-curve governor (Komar: cut exposure when the equity curve is below its average); never size up to win it back. | ~90 (keyword count inflated by "drawdown") | No sizing response. Tested: sw-w4-book-process (per-setup stop after 2/3 losses, book stops: 0 of 18 pass), sw-w4-book-volsize (failed). | Equity-curve governor on the daily books is in TESTPLAN C9. For intraday books the evidence so far says it does not help per unit of risk. | setup change |
| 7 | **Size up only on A+ setups; be selective.** Most of the year's profit comes from a few high-conviction trades; size the best setups bigger and skip the rest; overtrading kills (Bellafiore, Kruger, Sanghvi, Zhang: under a third of intraday breakouts work). | ~51 | Fixed 0.25% risk per trade for every setup. Tested: loop-1008-multisetup-consensus-t1 (agreement count as quality filter: failed). | MCF has no A+ label that has proved itself. A candidate "A+" flag must be pre-declared (for example a setup's top-quintile signal strength) and backtested as a size multiplier. | setup change |
| 8 | **Hard daily loss limit.** Platform-enforced max daily loss; continuing past it usually deepens the loss (Desai, Welsh); exceeding it means sitting out the next day (Morad). | ~37 | Yes: `max_daily_loss_r: 20` (primary), 60 (Testing): stop new entries after -20R. | Already in place as a catastrophe cap. A per-setup daily cap (bdi-reddit-setup-day-loss-stop) would be a guard only if it never binds in the two-year history; otherwise it is a setup change. | guard (exists) |
| 9 | **Small fixed risk per trade, sized to volatility.** Risk 0.25-2% per trade with total open risk capped (Burns: 1% per trade, ~3% open); size by daily range (Burns, Basso, Brandt). | ~30 | Yes: `risk_per_trade_pct: 0.25`, R = 0.25 x daily ATR, `max_position_notional_pct: 10`. | Consider a total-open-risk cap (sum of open stop risk), useful mainly when many setups fire in the same minute (window-open-cluster idea). | guard (if it never binds) |
| 10 | **Most of the day's edge is early; avoid the midday chop.** Fabrio: 70-80% of P&L in the first 30-60 minutes; Shapiro: 90% of day-trading cash flow before lunch; Dick: half the day's P&L in the first five minutes; Max avoids the noon lull. | ~40 | Full-day scoring is the owner's default (bdi-tod-policy-fullday-default); time of day is reported per setup. Early entries failed on opening costs (bdi-tod-open-0935-simple). | The guests' morning edge is from opening auctions and news flow, which MCF cannot price without quote-based opening costs. Package A tests the open with 2x costs; do not move windows on this principle alone. | setup change |
| 11 | **Cut losers fast; scratch what does not work at once; time stops.** Good trades work almost immediately (Fifield/Hurwitz: exit if not in profit within ~10 candles; Beggs: scratch and re-enter). | ~30 | Tested: t6-exit-overlay (breakeven/trail/time stop: failed), sw-w4-book-exits (failed). Idea open: loop-1009-hfs-small-mfe-scratch. | Only as a per-setup exit study with pre-declared scratch rules; the book-wide versions failed. | setup change |
| 12 | **Diversify across uncorrelated strategy types** (trend + mean reversion, long + short), rather than switching after a drawdown (Radge, Azbel). | ~41 | Both sides traded, but the 2-year rescore shows most live shorts win in down sessions and lose in up sessions: the book is one regime bet. | Favour long-side and momentum families in the next rounds (TESTPLAN A3, A8, A9, B5, B6, C1-C4) so the book is not only down-regime shorts. | setup change (portfolio composition) |
| 13 | **Specialise where competition is weak.** Master a few setups or a niche (Sykes: low-priced stocks funds ignore; Grittani: one or two setups; Walker: 2-3 markets). | ~34 | MCF runs many setups on 1,226 liquid names; the small-cap niche most guests exploit (sub-$10, low float, 20-100% gappers) is mostly outside the lab universe (426 gap >= 20% symbol-days in two years). | A small-cap sleeve would need float/dilution data and borrow realism first (TESTPLAN section 6). Research question, not a change. | research |
| 14 | **Decide in advance how to handle scheduled events and news** - flatten before the biggest ones, wait for the algorithmic reaction to finish (Azbel, Sanghvi, Kruger; Kyle Ng trades FOMC weeks only after the release). | ~13 (plus the news/catalyst theme) | Partly: `earnings_blackout_days: 4`. No FOMC/CPI handling. | An FOMC-day/CPI-morning entry pause is a guard only if the history shows it never removes profitable trades on balance; TESTPLAN C5 reports FOMC-week splits for every package A/B family first. | guard candidate / setup change |

Also frequent but not actionable for an automated system: psychology, sleep and health (~80 episodes), and "follow
the written plan, do not improvise mid-session" (~17), which MCF already enforces mechanically through the setup
freeze during market hours (rule 9).

## Guards that could ship as housekeeping (after checking they never bind on the history)
1. Daily fill-quality audit and stop-slippage calibration (principle 1).
2. Rolling 20-trade block stats per setup in the EOD report (principle 2).
3. Decay alarm: live expectancy vs backtest expectation per primary setup, report only (principle 3).
4. Monte Carlo drawdown line in finalist reports (principle 4).
5. Total-open-risk cap and per-setup daily loss cap as catastrophe limits (principles 8, 9) - only if a replay of
   the two-year history shows they never bind; if they bind, they are setup changes and go to the backlog.

## Setup changes these principles suggest (backlog first)
- Equity-curve governor and drawdown size-down on daily books (TESTPLAN C9).
- A pre-declared "A+" size multiplier (needs its own study).
- Per-setup scratch / time-stop exits (rework of t6-exit-overlay).
- FOMC/CPI entry pause, if the history supports it.
- Rebalancing the book toward long and momentum families (principle 12).

## How the guests say small edges are gained (one paragraph)
Almost no guest describes a fixed indicator rule as their edge. They describe (a) **where** the trade is - a stock in
play, a failed level, a stretched move into a known reference - (b) **who is trapped** - late breakout buyers, gap
shorts, dip buyers on bad news - and (c) **execution discipline** - small fixed risk, immediate scratches, sizing up
only when everything lines up, and a hard daily stop. The measurable parts of (a) and (b) are what `TESTPLAN.md`
codes; (c) is mostly already in MCF's risk config, and the remaining pieces are listed above.
