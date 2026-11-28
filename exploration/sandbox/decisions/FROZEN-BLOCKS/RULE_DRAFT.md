# FROZEN-BLOCKS process rule (DRAFT for the owner; would go to docs/RESEARCH_RULES.md only after a yes)
Educational only - not financial advice. Source: exploration/findings/dev_tactics.md Proposal 3(1) + reviewer notes.

Proposed text:
> Testing A-F and On Deck run in frozen 2-week blocks (first block 11-30..12-11 if approved by Sunday, else 12-07..12-18).
> Inside a block an account takes no rule change (risk, sizing, exits, filters). Setup moves (promotions / demotions /
> FOOTRACE / rotation) still happen, but only at the Friday epoch. Each account names at most ONE pre-registered question
> per block (e.g. Testing F: ARENA-LATCH-F). Emergency fixes (bugs, broker mismatches) are exempt and logged.

Why: 23 distinct rule-change dates in 25 sessions (ledger), so no testing-account comparison is clean; paired, frozen
designs need about 3x fewer sessions to read a +0.05R/trade change (dev_tactics E5).
Files that would change after a yes: docs/RESEARCH_RULES.md (new rule), research/ledger.jsonl (kind "process"),
docs/live/decisions.json (card answered). No config change.
