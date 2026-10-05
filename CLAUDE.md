# MCF — notes for Claude sessions

- **Read `MARCOFLOW_CONTEXT.md` first** — what the predecessor system (MarcoFlow) learned, what failed, data rules, and the owner's standing rules.
- Then `README.md` (architecture), `docs/RESEARCH.md` (setup evidence), `docs/ROADMAP.md` (phases).
- MarcoFlow history DB: `python scripts/import_marcoflow.py` rebuilds `data/marcoflow.sqlite` from `data/marcoflow_export/Folder2_Data.zip` (not in git — too large).
- MarcoFlow live data: only via `mcf/marcoflow.py` (read-only GET allow-list). Never call tick/heartbeat/secret endpoints.
- Tests: `pip install -e ".[dev,alpaca]" && pytest -q`.
- Every result screen/report carries "Educational only — not financial advice". Never write secrets to files or logs.
