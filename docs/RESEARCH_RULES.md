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
18. **Failed is not final. Every failed or failing idea is reworked before it is dropped.**
    - **What a rework tries:**
      - the neighbourhood of each parameter, e.g. RSI 14 → 7/10/21
      - swapped indicator lengths, applied across all setups at once as well as one setup at a time
      - each condition removed in turn
      - one condition added from the feature library
      - tweaks in pairs
    - **Guard rails, because every tweak is another chance of a lucky fit:**
      - Search on train and choose on valid.
      - Count the configurations tried across the idea's whole lineage, and report the count.
      - The winner must sit on a plateau: neighbouring settings must also be positive.
      - A reworked version may go through the two locked holdouts again (owner, 2026-10-06). Each exact version is still scored only once.
      - Every extra look by the same lineage raises the bar, because each look leaks a little of the holdout into our choices. The day-clustered t must reach 1.0 on look 1, 1.5 on look 2, 2.0 on look 3 and 2.5 on look 4.
      - After 4 looks, the lineage is judged only on forward sessions.
      - A version that passes on look 2 or later goes to paper as **probation**, labelled as a holdout re-look. It is confirmed or retired automatically once it has at least 20 forward sessions and 60 trades.
    - An idea is dropped only after its rework rounds fail. The backlog keeps the full record.

## Multi-year history (owner, 2026-10-08)
19. **Setups are judged on about two years of history, with a third locked block and regime-aware gates.**
    - **Why:** three BDI rounds on 2026-10-08 (~790k configurations) produced finalists that passed train (06-30..08-25) and valid (08-26..09-15) and then failed the locked holdouts. The samples were tiny (40 / 14 / 14 sessions), and valid and test were down-drift windows (median stock open-to-close −0.16% / −0.22%) while Apr–Jun was flat, so short setups looked good because of the regime.
    - **History:** SIP 1-minute bars from 2024-09-16 to 2026-10-07 for the lab universe (`research/lab_symbols.txt`), in `data/cache_hist/1Min` (`research/history2y/download.py`), turned into lab frames by the same pipeline as `research/setups2` (`research/history2y/build_frames.py`). **Survivorship caveat:** the universe is today's list applied to the past, so names that were delisted or fell out of liquidity are missing and today's winners are over-represented.
    - **New locked block: 2024-11-01 to 2025-02-28** (4 months). It was drawn at random on 2026-10-08, before any setup was scored on the new history: seed `20261008`, a contiguous 4–6 month block inside 2024-10..2026-02 (`research/history2y/draw_locked.py`). Loaders refuse it unless `MCF_HIST_ALLOW_LOCKED=1`, which only the lead sets.
    - It is scored **once per version**, with the same rising bar per lineage as rule 18 (day-clustered t ≥ 1.0 / 1.5 / 2.0 / 2.5 on looks 1–4). It is never used to tune.
    - **The older holdouts keep their status but are no longer clean.** Sep 16 – Oct 5 2026 and Apr–Jun 2026 have each been looked at by many lineages (the 2026-10-08 rounds alone scored 28 finalists on them: 10 owner-directed, 8 rework, 10 video). They still count under rule 2, but a pass there is weak evidence; the 2024-11..2025-02 block is now the clean holdout.
    - **Gates on the history** (`mcf/research/gates.py`, fixed in advance, production cost haircut as in `research/owner1008/scan_fast.py`):
      - *Regime split:* every session is classed up / flat / down by the universe's median open-to-close return (terciles over the history). Expectancy after costs must be positive in up sessions and in down sessions separately.
      - *Walk-forward:* rolling folds (3 months of train, the next month as test, step 1 month). The share of test months with positive expectancy is reported and must be at least 60%.
      - *Try-count-scaled t:* the day-clustered t must reach `max(1.5, sqrt(2·ln N))`, where N is the number of configurations tried in the lineage (the expected maximum of N null t-statistics).
