# swarm1017/final: assembler notes

*Educational only — not financial advice.*

## Locked block
- **Survivors of adversarial verification: 0.** Step 1 (score each survivor once on 2024-11-01..2025-02-28) therefore
  had nothing to score.
- `research/history2y/data/locked` was **not loaded** and `MCF_HIST_ALLOW_LOCKED` was not set. No lineage spent a
  look, so every version stays at look 0. The bar for a first look stays day-t ≥ 1.0 (rule 18/19), on top of the
  history bars.
- I deliberately did not score near-misses there. They already fail their try-count bars on history, so a locked pass
  could not make them live-ready. A look would only use up the clean holdout (QUESTIONNAIRE Q9).

## Configurations scored by the assembler
- Locked-block scores: 0. Configurations: 0.

## Other checks
- The 5 forward-observation modules were copied to modules/ and pass an import check (SIDE, GEOM and mask present).
- Their mutual trade overlap was **not** computed. Check it before enabling them.
- BACKLOG_ENTRIES.jsonl holds 58 entries (27 idea, 26 failed, 5 rework). It uses the research/backlog.jsonl schema.
  No id clashes with the existing backlog.
- Status rework is used only for the 5 entries with a live-runnable `lab_module`. Entries without a module use idea or
  failed, so `backlog run` does not count them as unrunnable.

## Files
PROPOSED_CONFIG.md, READINESS.md, QUESTIONNAIRE.md, BACKLOG_ENTRIES.jsonl, modules/*.py, and ../SUMMARY.md.
