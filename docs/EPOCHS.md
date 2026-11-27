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
| 2 | 2026-11-23 | ST7-MOVE: ST7-rsi50dn-long-pm-t1s1-FD Primary -> On Deck, unchanged (2026-11-23-st7-move-qa-exit2; row added 2026-11-27) | owner 2026-11-21 |
| 3 | 2026-11-30 | ETF-STOP50 / AV50: NM-ETF-late-dip-di-long burst lots (4+ signals within 10 min by decision bar) get half the stop distance when SPY is below its session VWAP; shares and R on the original stop (2026-11-30-etf-stop50-av50). BASE1's NM-ETF stays unchanged, so the pair measures AV50; Primary's of_live shadow lots apply it | owner 2026-11-24 (ETF-STOP50 yes, AV50); skeptic cleared 2026-11-27; applied Fri 11-27 after the close |
