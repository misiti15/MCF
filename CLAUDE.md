# MCF — notes for Claude sessions

- **North star (owner 2026-10-29):** build a profitable, sustaining, autonomous intraday trading system. The moves are there in the 3,000+ names, long and short; the core job is finding the best ways to identify those moves beforehand, in high numbers, and turning that into setups. Everything else serves this. See docs/BDI_CHARTER.md (Move Hunt, capture rate, "every day is a winning day in some way").

- **Read `MARCOFLOW_CONTEXT.md` first** — what the predecessor system (MarcoFlow) learned, what failed, data rules, and the owner's standing rules.
- Then `README.md` (architecture), `docs/RESEARCH.md` (setup evidence), `docs/ROADMAP.md` (phases).
- MarcoFlow history DB: `python scripts/import_marcoflow.py` rebuilds `data/marcoflow.sqlite` from `data/marcoflow_export/Folder2_Data.zip` (not in git — too large).
- MarcoFlow live data: only via `mcf/marcoflow.py` (read-only GET allow-list). Never call tick/heartbeat/secret endpoints.
- Tests: `pip install -e ".[dev,alpaca]" && pytest -q`.
- Every result screen/report carries "Educational only — not financial advice". Never write secrets to files or logs.
- **Research rules (owner): `docs/RESEARCH_RULES.md`** — costs always in, locked holdouts scored once, report every finalist and the number of configurations tried, no setup/exit changes during market hours, every approved change goes in `research/ledger.jsonl` and is re-checked with `python -m mcf.research.ledger check`.
- **Backlog:** setup/strategy ideas go to `research/backlog.jsonl` (gates in `mcf/research/backlog.py`); only housekeeping ships directly. See RESEARCH_RULES 15-17.
- Merging: Claude merges its own PRs once tests pass; PRs that touch setups/exits are merged only outside 09:30-16:00 ET (the `setup-freeze` check enforces it).
- **Setup moves (owner 2026-10-20):** every promotion / demotion / move regenerates `docs/live/assignments.json` (`python -m mcf.report.assignments`) in the same commit, so the dashboard shows the new assignment and its timestamp at once (`tests/test_assignments.py` enforces it).
- **Promotion = move (owner 2026-10-20):** a promoted setup is switched off in the account it came from in the same change; it never runs as a copy in two accounts unless the owner asks.
- **Testing 1 = Testing 2 (owner 2026-10-23):** the two testing accounts carry equal weight for promotion; two accounts exist only to give more setups exposure. Never treat Testing 2 as a lower tier.
- **One-big-day check (owner 2026-10-25):** every promotion / demotion / review shows the setup's avg R *without its best session* and that session's share of total R (dashboard column "Avg R w/o best day", `1 day` tag at ≥ 50%). A record carried by 1-2 big days must be called out.
- **Rule-change context (owner 2026-11-02):** whenever stats or figures are given (chat, briefs, posts, reviews), note alongside them any rule / config change in effect before or after a date inside the window (from `research/ledger.jsonl` effective dates: sizing, stops, filters, timing fixes, moves), so setup results are never mixed up with rule changes.
- **Trimmed setups (owner 2026-11-03):** any setup trimmed for low activity moves to a testing account for more exposure; it is never just switched off. The 7 INACT2 setups (IDX1 trail, IDX1 hold, IDX2, IDX3, IDX5, LD4, LD5) move to Explore 1 when it opens.
- **Playing time (owner 2026-11-03):** low-activity setups must get a fair chance; a system that starves them fails at producing quality results. Fix starvation by session rotation (whole sessions off for top-trade setups, logged as benched, excluded from per-session stats), never by in-session throttling in Primary/Testing; no reports unless a decision is needed.
