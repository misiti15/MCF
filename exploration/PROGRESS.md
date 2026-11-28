# Exploration session 2026-11-27 → 2026-11-28 05:30 ET

Branch: explore/2026-11-27, cut from claude/intraday-trading-system-witis4 at be8e648c04. All work goes in the /exploration/ folder.

Rules: this session is research and exploration only. Every existing branch, the config and all 10 paper accounts are read-only. Alpaca calls are GET only. Nothing here changes the running system.

## Cycle log
- Cycle 0, 23:35 ET: created the branch and folder; launched step 0 (inventory of prior research), tracks 1-7 and the reviewer.
- Cycle 1, 00:58 ET: step 0 + 7 tracks + 7 reviewers + decisions agent finished (16 agents, 0 errors). Outputs: PRIOR_RESEARCH.md, findings/*.md (each with "Reviewer notes"), PROPOSALS.md, DECISIONS.md, MONDAY_PLAN.md. Verdict: no positive per-lot edge after costs found on either side; losses are lumpy short "baskets"; levers that help cut exposure on bad days. Monday plan drafted (Primary unchanged unless the owner approves LATCH-OPEN / L3-OUT overrides).
- Cycle 2, 01:00 ET: launched (a) a dry-run of every prepared draft in a throwaway worktree (tests only, nothing pushed outside this branch), (b) a gap-direction day switch study for the post-11-30 roster (pre-registered, CHECK/T2), (c) re-check of the RW3/RW5 1.25x target under LIVE-L costs, (d) an adversarial review of MONDAY_PLAN + DECISIONS (accuracy, under-a-minute approvals, rule compliance, do-no-harm).
- Cycle 2 done, ~02:15 ET: 4 agents, 0 errors.
  - (a) **Dry run.** None of the drafts applied as written; all do now with `sandbox/decisions/apply_draft.py`. Every draft, the Monday combo and an all-five stack pass `pytest -q` (1,076; one load-only timing flake). `ledger check` was not run.
  - (b) **GAPSWITCH failed.** 0 of 5 configs beat same-count random day-skips (best p 0.42). No rule or shadow was added, and the TAGS2 GAPU prior is lower.
  - (c) **RW-TGT125 failed** under LIVE-L (CHECK +0.007, T2 +0.003 R/lot). It is dropped (D13) and stays a descriptive line only.
  - (d) **Plan review:** 40 numbers checked, 9 corrections, and playing-time / no-freeze conflicts flagged.
  - DECISIONS, PROPOSALS and MONDAY_PLAN now carry the exact apply steps. Configurations about 9,656 (cycle 2 +6).

Educational only — not financial advice.
