# Primary epochs (C3-EPOCH, owner yes 2026-11-18)

Educational only — not financial advice.

Primary lineup / rule / sizing changes are made only in the Friday-after-close window (docs/RESEARCH_RULES.md rule 25).
Each change set opens a numbered epoch. Every epoch is judged by the same-day paired difference against **BASE1**: the
Primary book as it ran in session 2026-11-18 (Epoch 0), frozen in `baseline:` (config/default.yaml) and run journal-only
in Primary's shadow book as `BASE1:<setup>` (never an order). The pair compared each session is Primary's of_live shadow
R (the current book, resource-free) vs BASE1's shadow R (the frozen book, resource-free): same polls, same fill model.
`python -m mcf.report.c3score --journal <primary journal.db>` prints the paired mean, SD and SE (target paired SD < 8R).
Verdicts in weeks, not months; no direct R is claimed for any epoch until its paired difference clears ~2 SE.

| Epoch | From session | Change set (ledger ids) | Approved |
|---|---|---|---|
| 0 | 2026-11-11 | TEAM-6 lineup (L3-fromopen, NM-ETF, ST7, RW5, RW3, NS5) — the BASE1 book | owner Team yes 2026-11-10 |
| 1 | 2026-11-19 | C3-NS5: NS5-sma50-flush-oversold-long Primary -> On Deck (2026-11-19-c3-ns5); BASE1 twin on (2026-11-19-c3-epoch-base1) | owner 2026-11-18 (set up the Wednesday evening by owner instruction, outside the Friday window) |
