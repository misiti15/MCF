# MarcoFlow Context: load this before planning MCF work

*Sources:*
- the MarcoFlow knowledge pack (`data/marcoflow_export/Folder1_Knowledge.zip`, guides 00–07; 08–10 are code reference only)
- the data export (`Folder2_Data.zip`), snapshot taken 2026-10-02 ~15:50 ET
- queries against `data/marcoflow.sqlite` (rebuild it with `python scripts/import_marcoflow.py`)

*Educational only — not financial advice.*

**What MarcoFlow is:**
- It scans about 3,437 US stocks and ETFs every 5 minutes and scores each with a composite "Heat Score" (−100..+100).
- It records every signal with |heat| ≥ 30 (167,645 rows) and mines rule stacks ranked by Wilson lower bound (alerts at LB ≥ 60).
- It paper-trades the alerts on Alpaca paper: $80k fund, $640 per position, short-heavy, entries 10:00–11:59 ET in practice.
- **MCF uses different strategies. Use MarcoFlow to avoid repeating its mistakes, not as a template.**

## Results (clean window: paper entries on or after 2026-08-28)
- **Paper trading lost money in every clean era:** 2,123 trades, −$3,242, 31.8% win rate. Shorts: 1,956 trades, −$2,581. Longs: 167 trades, −$661.
- Overall since 8/20: 2,709 closed trades, −$3,320. Equity is $76,678 on the $80k fund.
- The win rate falls with each config era: 38.5% → 42.9% → 26.6% → 24.5% → 33.6% (v7.0, 9/29–10/2, too early to judge).

## What MarcoFlow learned
1. **A signal's win rate is not the trade's win rate.** The same traded signals score 44.1% / −0.03% at signal level but 32.3% / −0.28% after real fills. About 0.25% per trade is lost between signal and fill/exit.
2. **Latency kills the edge.**
   - Bars come from Yahoo, about 15 minutes delayed. Entries then land a median 6 minutes after the signal (90th percentile 17 minutes). Average entry slippage versus the signal price is −0.16%.
   - The persistence test priced 15 minutes of latency at about 14 win-rate points.
   - Entries more than 15 minutes late are clearly worse (−0.34% to −0.48% average).
3. **"Never-worked" trades are the loss.**
   - 840 trades never moved more than 0.15% in favour; they lost −$3,956, more than the whole book.
   - Winners give back about two-thirds of their peak: trades that reached ≥ 1% kept 0.59% on average, and 149 of 390 closed red.
4. **Only trailing-stop and take-profit exits make money** (+$396 and +$909). Stop-loss exits lost −$3,841; time exits lost −$710.
5. **Short the drop, don't fade the rip.** At signal level, live data since 8/28: follow-drop shorts 56.1% (n=8,857) vs fade-rip shorts 46.7% (n=1,309). Neither has a positive average return. The famous 75.7% was a small early sample.
6. **Wilson-LB alert gating helps selection** (45.4% alerted vs 34.2% not, at signal level) but did not make paper trading profitable.
7. **Real broker fills plus marketable-limit exits** fixed fake stop-outs. Exit prices before 8/28 are corrupted.

## What failed or was rejected
- **Persistence filter:** the wait consumed the edge.
- **Scanning faster than the 5-minute bar interval:** it reads half-formed bars and creates false setups.
- **Single-feature short vetoes** (buyPressure, rising RSI slope): they removed winners.
- **Blunt move-size gate.**
- **ADV gate on IEX volume:** IEX is about 2–3% of the tape, so the gate blocked 93% of flow.
- **Resting take-profit and give-back lock:** off since 9/28.
- **Duplicate-fill race:** 450 extra same-symbol entries, −$1,095.
- **Robinhood as a data feed:** rate-limited, invite-only.
- **Unofficial broker APIs:** account-suspension risk.

## Open problems
- **Scheduler reliability:**
  - The hourly task keeps orphaning; there were no trades on 9/23–24.
  - The external heartbeat cron has not fired since 9/29.
  - **As of 2026-10-05 12:10 ET, MarcoFlow has recorded no observations since 10/2 11:14 ET.** Health reports ticks, but data collection is stalled.
  - Lesson: check health by **data counts per ET day**, never by "the process is alive".
- No consolidated (SIP) volume or ADV data.
- Give-back on winners, and diagnosing why alerts never work. Update 7.0 is unvalidated.

## Data rules when using `data/marcoflow.sqlite`
- **Execution questions:** use `PaperTrade` with `entryTime >= '2026-08-28'` only.
- **Signal-level and paper-level results are always reported separately.**
  - `SignalObservation.status='WIN'` means the tracker's target was hit (default 4h / +2% / −1.5%). It does not mean dollars were made.
  - Link the two tables with `PaperTrade.observationId`.
  - A paper win is defined as `pnlDollars > 0`. That reproduces the pack's 36.6%; `returnPct > 0` gives 37.3%.
- **Backfill rows:** exclude `source='backfill'` from live claims, or label them.
- **Timestamps** are UTC text; ET = UTC−4 until 11/1.
- **Universe size changed:** about 64 → 2,100 → 3,437 symbols, so raw counts can't be compared across periods.
- **Missing days** mean the system was down, not that there were no setups.
- `rsi_runs` (1 optimizer row) was not in the CSV export.
- **Newer than 10/2:** use only `mcf/marcoflow.py`. It is allow-listed to the read-only GET endpoints in guide 07.
  - **Never call `/api/agent/tick`, `/api/paper/tick`, `/api/agent/heartbeat`, daily-brief or any secret-protected endpoint.** Those make MarcoFlow scan, trade or email.

## Owner's standing rules (carry over to MCF)
- **Approach:**
  - Quality over quantity.
  - Never inflate scores or lower thresholds to show more results.
  - Data accuracy and recording come first.
- **Honesty:**
  - Report failures first.
  - Label estimates.
  - Separate hindsight from tradeable findings.
  - Say "tested" or "live" only when actually observed.
- **Every result screen and email carries "Educational only — not financial advice."**
- **Changes:**
  - Every change is dated and visible (changelog), and reversible with one toggle.
  - Backtest on clean data before going live.
  - Make the smallest change that solves the problem.
- **Communication:**
  - Direct answers over long reports.
  - One concise daily brief after the close.
  - The owner is credit- and time-conscious.
- **Never expose secrets** in chat, files or logs.
- **Keep the system operational at every market open.**
- **MarcoFlow-specific rules — whether they apply to MCF needs confirming with the owner:**
  - never cap entries or filter bad alerts; diagnose them instead
  - skip entry hours 9 and 12 ET
  - no shorts at RSI ≤ 30
  - don't change the Heat Score
  - the optimizer stays paused

## What this means for MCF (design implications)
- **Real-time data and fast entries:**
  - Real-time SIP bars.
  - Act on the just-closed bar, with entries within seconds.
  - Stop entries resting at the broker.
- **Simulate execution, not signals:**
  - The backtester models next-bar fills and per-share slippage.
  - The journal keeps signal price vs fill price so the drag is measured.
- **Every setup has a defined invalidation and a measured exit.** Track MAE/MFE (already stored as `mae_r`/`mfe_r`) to diagnose give-back and never-worked trades.
- **Idempotent orders:** deterministic `client_order_id` per setup/symbol/day plus an in-process lock.
- **Liquidity:** use consolidated volume for relative volume and ADV, never IEX.
- **Tag every run and trade with its config version** so results are compared by era.
- **Data-count health checks** per ET day, with an external scheduler.

## Deep-dive findings (2026-10-05, `docs/MARCOFLOW_ANALYSIS.md`)
- **No target/stop pair on MarcoFlow's entries reaches ≥55% wins with positive expectancy**, for longs or shorts. Signal-level average return is about 0 in every hour, regime and price slice. The entries carry little directional edge, and exits can't fix that.
- The tracker's "4h" horizon is market hours. Median resolution is 19 clock hours, so signal-level stats are not intraday stats.
- Win rate by price band (59% under $5 vs 29% over $100) comes from fixed-% targets against different volatility, not from edge. **Use ATR/R-based stops and targets.**
- Holds of 5 minutes or less won 14.9% (470 trades). The fixed 1.25% stop and 0.3% trail (activated at +0.3%) were inside normal noise.
- `volumeRatio` is 0 in most rows, so the volume features were effectively missing.
- Owner decisions for MCF are in `docs/DECISIONS.md`, and the data/broker choice in `docs/DATA_AND_BROKER.md`.
