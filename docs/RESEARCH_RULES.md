# Research and reporting rules (owner, 2026-10-06)

*Educational only — not financial advice.*

Goals must be backed by true data. No test, result or report may give a false impression, and no
variable may be left out to make a number look better. Every study, swarm, backtest and report
follows these rules.

## Testing
1. **Costs are always in.** Slippage per share, slippage in bps, extra stop slippage, and 3× slippage on extended-tier names. Fills are conservative: next-bar entries, stop-first inside a bar, gaps through stops fill at the open.
2. **Data is split by date, and holdouts are scored once.**
   - Fit on train and pick finalists on valid.
   - Every finalist is scored once on each locked holdout: Sep 16 – Oct 5 2026, and Apr–Jun 2026, which is untouched as of 2026-10-06.
   - A candidate passes only if it holds on both holdouts.
   - Holdouts are never used to tune.
3. **Report every finalist, including failures.** Never present only the winners. Each study states how many configurations were tried in total.
4. **Count the multiple testing.** With N configurations tried, expect roughly N × 5% false positives at p = 0.05. Report day-clustered statistics, because trades on the same day are correlated.
5. **Check for concentration.** Report results without the best day. If a few days carry the result, say so.
6. **Beat the baseline.** Every edge is compared with the same side and time window traded at random, and with same-time controls.
7. **Paper results, backtests and live results are always labelled separately.** Paper fills are optimistic, and the fill-realism checks and adjusted P/L stay on.
8. **"Tested" and "live" are used only for what was actually observed.**

## Changes
9. **No setup or exit changes during market hours.** Setups and exits are frozen per session (state/setups/<date>.json), and the `setup-freeze` PR check enforces this.
10. **Every proposed change is backtested by a swarm before it is proposed.** The evidence (files, configurations tried, holdout results) is linked in the PR.
11. **Every approved change is recorded in `research/ledger.jsonl`.** The entry holds the config before and after, the evidence, and the metrics at approval.
12. **Conflict check:** `python -m mcf.research.ledger check` re-runs the joint portfolio with each ledger change reverted, one at a time, on the latest data. If reverting a past change now improves the portfolio, that change is conflicting or has decayed, and it is flagged for review rather than stacked on.

## Reporting
13. **Failures come first, then results.** Numbers carry their sample size, window and standard error.
14. **No result is rounded, re-labelled or re-windowed to cross a goal line.** If a goal is not met, the report says so.

## Housekeeping vs. strategy (owner, 2026-10-06)
15. **Housekeeping fixes ship right away.** Bugs, reliability, reporting, dashboards, emails, docs and tooling that do not change which trades are taken or how they exit can go in any time, after tests pass.
16. **Setup and strategy ideas go into one backlog first:** `research/backlog.jsonl`, rendered as `research/BACKLOG.md`. This covers new setups, setup or exit changes, filters, sizing and risk rules. No idea goes straight into live trading, whatever its source (Reddit, papers, books, the EOD review, the owner, or Claude).
17. **The backlog is re-tested continuously on all collected data.**
    - `python -m mcf.research.backlog run` runs every week in the discover workflow, after the bar cache is refreshed. It scores train, valid, and forward. Forward means sessions after the rules were frozen.
    - The gates are fixed in advance in `mcf/research/backlog.py`. A finalist is scored once on the locked holdouts.
    - Only an idea that passes is proposed. It is merged after the close and recorded in the ledger.
    - Failed ideas stay listed, together with their numbers.
