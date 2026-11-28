# GY-SHADOW + TWIN lane (account structure; DRAFT outline; earliest start = 12-04 Friday epoch, effective 12-07)
Educational only - not financial advice. Source: exploration/findings/dev_tactics.md Proposal 3(2-3) + reviewer notes.

1. Graveyard -> shadow-only: Graveyard setups keep full reps through the shadow run (run kind "shadow", 95% match to live,
   bias -0.047R/trade, pessimistic). Keep 1-2 Graveyard leaders live as a cost sample. The -0.047 bias must be corrected
   before any foot-race comparison with live-traded setups. Needs owner changes to GY-LIFE / GY-FOOTRACE wording.
2. The freed paper account becomes TWIN: an exact copy of Primary's book (same setups, same risk rules) plus exactly ONE
   candidate change per 2-week block (first candidate: whichever of LATCH-OPEN / L3-OUT the owner did NOT apply to Primary,
   or RW 1.25x target). Real-fill paired read vs Primary on identical signals.
   This is a copy, so it needs the owner's explicit exception to "promotion = move" (CLAUDE.md, owner 2026-10-20).
Files that would change: config/account_graveyard.yaml (paper orders off / shadow on), a renamed account overlay for TWIN
(copy of Primary's strategies block), workflows that list the account, docs/live/assignments.json, ledger (kind "move" +
"process"), decisions.json. A full build + tests is a separate PR outside market hours; not drafted line by line tonight.
Expected speed (reviewer-corrected): +0.10R/trade on ~30 lots/session reads at t 2 in roughly 4-8 sessions (MAE-rule
estimate 2-4 is optimistic: fills and latch paths diverge between two real accounts).
