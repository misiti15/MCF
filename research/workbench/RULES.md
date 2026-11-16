# Workbench rules (owner 2026-11-15)
Educational only — not financial advice.
1. A setup on the Workbench is observed only; the parent stays in its account and on the leaderboard, unchanged.
2. Any tweak (one part at a time) creates a copy with a new id `<parent>-WB<n>` and a distinct display name ("<parent name> — WB<n>: <what changed>"), with lineage in `research/workbench/<parent>/variants.jsonl`.
3. The variant is tested independently, with the parent re-scored on the identical tests: replay sessions + 2-year backtest, costs in, locked block 2024-11-01..2025-02-28 untouched, configs counted.
4. Pass = matches, comes close to, or beats the parent. Close (default, owner may tune): avg R after costs ≥ 90% of the parent's or within 0.02R per trade, AND avg R without best day no more than 0.02R below the parent's. Report both side by side, per test.
5. A pass goes to a testing account at once (no owner approval; ledger entry + assignments regenerated + tests; after hours only) and is placed FIRST in that account's priority order — ahead of newly rotated / spotlight setups — for immediate exposure. Twins rule: not in the same account as its parent.
6. On Deck / Primary promotion still needs the owner. Because parents are already vetted, passing variants are prime Primary candidates; flag them in reviews.

## Update 2026-11-16 (owner): improvements only
"Setups coming in are like crudely made cars that need optimization, enhancement and refinement. A setup's copy should not leave the workbench without tested and vetted improvements." Rule 4 tightened: a copy leaves ONLY if it beats the parent on avg R after costs in BOTH the live-session replay and the 2-year backtest (improvement vs parent, paired by day, clears the configs-counted bar max(1.5, sqrt(2 ln N))), and is not worse on avg R without best day or on worst day by more than 0.02R / 10%. "About equal" no longer leaves. The Mechanic reviews EVERY component (P1..Pn), not only the ones tied to the worst trades.

## Clarification 2026-11-16 (owner) — supersedes the "Update" above
"Any new setup that comes out of the workbench meets or exceeds the parent setup's backtesting ... I don't want to be too quick to kick out a newly formed setup if it's close to or barely exceeds the parent's numbers. The parent and the modified setup should be tested in the exact same way, without considering the live stats of the parent."
- Parent and copy are scored with the IDENTICAL backtest pipeline: the replay of the live sessions (same days, same engine, same costs) and the 2-year backtest. The parent's live journal record is NOT part of the pass decision (live trades are still used to diagnose components).
- PASS = the copy meets or exceeds the parent's avg R after costs in both tests. "Meets" includes close: within ~0.01R per trade or ≥ 95% of the parent's avg R. And not worse than the parent on avg R w/o best day / worst day by more than 0.02R / 10%.
- No significance hurdle on the difference for passing; configs counted and the paired difference are still reported.
