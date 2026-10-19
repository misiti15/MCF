# Testing new setups faster without damaging the results

*Answers to the owner's questions of 2026-10-18. Educational only — not financial advice.*

## Short answers

| Question | Answer |
|---|---|
| What data do backtests use? | **Alpaca SIP 1-minute bars** (consolidated tape, the same feed live trading uses: `config/default.yaml` `data.feed: sip`). Universe `research/lab_symbols.txt` (1,226 symbols). Two caches: `data/cache_hist/1Min` = **2024-09-16 to 2026-10-16** (extended tonight), and `data/cache/1Min` = 2026-06-15 onward (refreshed weekly by `scripts/refresh_lab_data.py` in the discover workflow). The lab resamples 1-min to 5-min decision bars (`research/history2y/build_frames.py`). Costs always in (`mcf/research/gates.py`). |
| Which bar size? | All setups are researched and traded on **5-minute decision bars** built from 1-min data. Tonight's swarm also tested 1, 3, 10 and 15 min (640 configurations, 0 pass, see `TIMEFRAMES.md`). |
| Are live sessions recorded? | **Decisions yes, bars no.** The state branches (`mcf-data`, `mcf-data-testing`, `mcf-data-testing2`) keep `journal.db` (Testing 2: 5,077 signals, 2,281 orders), `setups/<date>.json` (the frozen setup list per day), `intraday/<date>.jsonl` (P/L by setup each minute, since 10-08), `reviews/`, `earnings/` and `status.json`. Raw bars are not saved. |
| Do we need to record bars? | **No, not for testing.** Because live uses SIP, the Alpaca SIP history downloaded after the close *is* the recording, for every symbol, not just 30. Tonight's 7-session extension of all 1,226 symbols took about 5 minutes. What history can't reproduce is what only live knows: fills, rejections, latency and the day's universe/scanner ranking. That is what `journal.db` and `setups/` already hold, with one gap (below). |
| Are we bound by market days? | Only for **forward** evidence. For history, we already hold about 500 sessions on 1,226 symbols. A new setup can be scored on all of it tonight. The only thing that needs new market days is the final check on sessions the setup has never seen, and nothing honest can speed that up. Running many setups in parallel in Testing (rule 20, no cap) means we wait once for all of them, not once each. |

## The plan

### 1. Nightly history extension (housekeeping, rule 15)
- Run `research/tf1019/data/extend_1min.py` (or `scripts/refresh_lab_data.py` pointed at `data/cache_hist`) every weekday at about 20:00 ET. It is read-only Alpaca SIP, takes about 5 minutes, and has a split/adjustment check on the overlap day (`extend_report.json`).
- Then rebuild only the new month partition of the lab frames, for 5-min and, when needed, `frames_tf`.
- Keep the three-symbol no-data list (WBD, QRVO, PSKY) and the gap check in the report. Tonight we found 2026-10-07 had been downloaded with gaps (SPY 357 of 390 bars), so after each extension re-fetch the last cached day as well.

### 2. Replay recent sessions through the live strategy code
- `mcf --config config/account_testing2.yaml backtest --start 2026-10-08 --end 2026-10-16` runs the **same `Strategy` classes the live runner uses** (`build_strategies(cfg)`, `mcf/backtest/engine.py`). It uses conservative fills: next-bar entries, stop-first inside a bar, gaps fill at the open. Point `data.cache_dir` at `data/cache_hist`.
- Add a nightly **parity report**: replay trades vs `journal.db` trades for the same day and setup. If they differ, the problem is a research/live mismatch (warm-up, universe, timing) and is fixed as housekeeping. That catches problems like LabStrategy's 5-min-only `prior5` warm-up before they reach a decision.
- Close the one recording gap: archive `universe.csv` and the priors' symbol list per date (`universe/<date>.csv`). Today the file is overwritten, so replay can't reproduce exactly which symbols were eligible that morning.

### 3. A fixed forward window, separate from training
- Each setup's **forward window = sessions after its freeze date** (the date its rules entered `research/backlog.jsonl`). Today's shared forward block is 2026-10-08 onward.
- Forward data is **monitoring only**. It is never used to choose a variant, a threshold, a timeframe or a symbol list. The backlog gate is already fixed in advance: at least 20 sessions and 60 trades, t >= 1.0 (`mcf/research/backlog.py` `GATE`).
- Train and valid stay as they are: train 2024-10 + 2025-03..2025-12, valid 2026-01..2026-10-07. The locked block 2024-11..2025-02 is scored once per version.

### 4. Re-testing the same recent data repeatedly without overfitting
- **Every look counts.** Scoring 10 variants on the same 7 recent sessions is 10 configurations, and the bar `max(1.5, sqrt(2 ln N))` rises with them. Record N in the lineage (`configs_tried`).
- **Frozen rules only on forward.** If a setup is changed after looking at forward sessions, the new version's forward window restarts the day after the change.
- **Report, don't select.** The weekly backlog run scores every entry on forward and lists them all, failures included. Nobody promotes "the best of this week".
- **Prefer more sessions to more looks.** 7 sessions (one week) cannot separate a 0.1R edge from noise: day-clustered t on ~7 independent days is meaningless. Treat the first weeks as a check that the setup works mechanically, not as evidence.

### 5. Sound ways to get more evidence per calendar day
1. **More symbols per setup (largest gain).** Score on all 1,226 lab symbols, not core 80 or 30. On core 80 the near-miss setups had about 10% of their full-universe trade count, and most regime failures were n < 30. The 30-ticker idea would cut evidence by about 40x. If the disk can't hold multi-timeframe frames for everyone, keep 5-min for all symbols and multi-timeframe for a subset.
2. **More history (second largest).** Alpaca SIP minute history goes back to 2016. Extending `cache_hist` backward (for example 2020-2024, outside the locked block) adds about 1,000 sessions across several regimes (2020 crash, 2022 bear) **at no market-day cost**. `data/cache_hist` is 4.3 GB for about 2.1 years, so each year is about 2 GB of 1-min parquet for the 1,226 symbols. This machine has 3.0 GB free, so it needs more disk, or a download in chunks with only the 5-min frames kept. This is the honest answer to "we are bound by waiting on market days".
3. **Cross-instrument checks.** The same rule on ETFs vs single stocks, by sector, and by liquidity tier. A real edge should keep its sign across most of them. Use it as a **robustness filter on a finished candidate**, not as a search over subsets.
4. **Multi-timeframe as a plateau check, not a search axis.** Tonight showed timeframe is not a source of edge (1-min clearly hurts; 10/15 min don't help on average). Use the 3/10-min neighbours of a 5-min finalist as rule-18 plateau evidence. Do not pick "the best timeframe per setup": that is 5 tries per setup and is counted.
5. **Parallel swarms on pre-declared plans.** Write `PLAN.md` before scoring, as tonight. One 1-min core run takes about 19 s; a full-universe 5-min lab run takes minutes. CPU is not the bottleneck.
6. **Paper-trade many candidates at once in Testing** (rule 20). Forward sessions accumulate for all of them in parallel.

### 6. Things that would damage results (do not do)
- Choosing a 30-ticker list, or any symbol subset, **by how a setup did on it**. That is in-sample selection, and survivorship is already a caveat.
- Tuning on the forward window, or "re-running until it passes".
- Opening the locked 2024-11..2025-02 block to get more data.
- Dropping costs, or using the lab's 1c cost instead of production R, to make 1-min setups look viable.
- Treating 1-min bars as "7 times more data". Trades on the same symbol-day are highly correlated, and the swarm showed 1-min trades are worse, not more informative. Statistics stay day-clustered.
- Synthetic or bootstrapped sessions presented as evidence. A block bootstrap is fine for confidence intervals, never as new sessions.
- Comparing research on 1/3-min bars with live code that warms up on 5-min `prior5`, until the `DayContext.prior1` work in `PROPOSED_CONFIG.md` exists.

## What it buys
Tonight a setup idea can be scored on about 500 sessions x 1,226 symbols, with costs, the regime gate, walk-forward and the try-count bar, in minutes. With the backward extension, that becomes about 1,500 sessions. The only remaining wait is the forward confirmation (20 sessions / 60 trades, about 4 weeks), shared by every setup in Testing at once.

*Educational only — not financial advice.*
