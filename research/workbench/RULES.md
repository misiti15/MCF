# Workbench rules (owner 2026-11-15)
Educational only — not financial advice.
1. A setup on the Workbench is observed only; the parent stays in its account and on the leaderboard, unchanged.
2. Any tweak (one part at a time) creates a copy with a new id `<parent>-WB<n>` and a distinct display name ("<parent name> — WB<n>: <what changed>"), with lineage in `research/workbench/<parent>/variants.jsonl`.
3. The variant is tested independently, with the parent re-scored on the identical tests: replay sessions + 2-year backtest, costs in, locked block 2024-11-01..2025-02-28 untouched, configs counted.
4. Pass = matches, comes close to, or beats the parent. Close (default, owner may tune): avg R after costs ≥ 90% of the parent's or within 0.02R per trade, AND avg R without best day no more than 0.02R below the parent's. Report both side by side, per test.
5. A pass goes to a testing account at once (no owner approval; ledger entry + assignments regenerated + tests; after hours only) and is placed FIRST in that account's priority order — ahead of newly rotated / spotlight setups — for immediate exposure. Twins rule: not in the same account as its parent.
6. On Deck / Primary promotion still needs the owner. Because parents are already vetted, passing variants are prime Primary candidates; flag them in reviews.
