# Swarm 2026-10-10 - shared rules for every workstream (owner request 2026-10-09 evening)

*Educational only - not financial advice.*

- Read first: CLAUDE.md, docs/RESEARCH_RULES.md (rule 19), docs/BDI_CHARTER.md, research/history2y/RESCORE.md,
  mcf/research/gates.py, research/history2y/lib.py, research/bdi/timeofday/NOTES.md, research/bdi/regime1009/NOTES.md.
- Data: open two-year history via research/history2y/lib.py (426 sessions). NEVER load the locked block 2024-11..2025-02
  and never set MCF_HIST_ALLOW_LOCKED - the lead scores finalists on it once.
- Costs always in (gates.prod_r / production cost model). Pre-declare the grid in your NOTES.md BEFORE scoring;
  count every configuration; try-count bar t >= max(1.5, sqrt(2 ln N)) per lineage; report failures first.
- Live-probation bar (for Testing-account candidates): n >= 150, exp > 0 in BOTH up and down sessions, day-clustered
  t >= 2.0, walk-forward positive share >= 0.6, plateau of neighbours mean > 0, ex-best-day > 0, busiest session <= 10%
  of trades. Full-day (09:50-15:00) versions first (owner preference); time of day is reported, not assumed.
- SHARED MACHINE: 4 CPUs, 15 GB RAM, ~5 GB free disk shared by 5 workstreams. Use ONE process (no multiprocessing
  pools), keep RAM under ~2.5 GB (load month by month, only needed columns, float32), keep your git-ignored data/ under
  1 GB and delete intermediates when done. If disk drops below 1 GB free, stop writing and report.
- Live parity: any candidate must be a lab module (SIDE, GEOM, LAYERS, mask(df)) using only live-frame columns
  (incl. 'volume'; PRIOR5_BARS = 60 prior 5-min bars), verified to reproduce the scan; stage Testing YAML snippets in
  your folder (never edit config/*, mcf/execution, mcf/strategies). Do not commit/push - the lead does.
- Backlog: append entries with your workstream prefix (failures too); keep python -m pytest tests/test_backlog.py passing.
- Final report: config counts, results table (failures first), candidates with module paths, what the live system
  would need.
