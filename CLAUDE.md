# MCF — notes for Claude sessions

- **Read `MARCOFLOW_CONTEXT.md` first** — what the predecessor system (MarcoFlow) learned, what failed, data rules, and the owner's standing rules.
- Then `README.md` (architecture), `docs/RESEARCH.md` (setup evidence), `docs/ROADMAP.md` (phases).
- MarcoFlow history DB: `python scripts/import_marcoflow.py` rebuilds `data/marcoflow.sqlite` from `data/marcoflow_export/Folder2_Data.zip` (not in git — too large).
- MarcoFlow live data: only via `mcf/marcoflow.py` (read-only GET allow-list). Never call tick/heartbeat/secret endpoints.
- Tests: `pip install -e ".[dev,alpaca]" && pytest -q`.
- Every result screen/report carries "Educational only — not financial advice". Never write secrets to files or logs.
- **Research rules (owner): `docs/RESEARCH_RULES.md`** — costs always in, locked holdouts scored once, report every finalist and the number of configurations tried, no setup/exit changes during market hours, every approved change goes in `research/ledger.jsonl` and is re-checked with `python -m mcf.research.ledger check`.
- **Backlog:** setup/strategy ideas go to `research/backlog.jsonl` (gates in `mcf/research/backlog.py`); only housekeeping ships directly. See RESEARCH_RULES 15-17.
- Merging: Claude merges its own PRs once tests pass; PRs that touch setups/exits are merged only outside 09:30-16:00 ET (the `setup-freeze` check enforces it).
