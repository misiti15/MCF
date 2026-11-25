# builder notes (current; full history through 2026-11-15 archived in roles/builder_log.md)

Educational only — not financial advice.

## State (2026-11-24 20:40 ET) - USAGE1 (owner 11-18, effective 11-19; MCF research/usage_review_1118/APPLY_1118.md)
- Guild = gap teams: Scout (card) -> Builder (ONE pre-registered test) -> Skeptic (break it); weeknights ~20:15/20:45/21:15 ET
  + Saturday. Lead and Observer roles DISABLED (kept, not deleted). Input = MCF research/gaps/GAPS.md + gaps.json (BDI daily;
  NOT BUILT as of 11-24). Kill/keep check 2026-12-16 (no passed card, no approved process item -> owner asks keep/weekly/pause).
- Builder's test spec: 2-year data, costs in, LR8 basis, locked block never read (#43), ETB universe for shorts, vs random
  entries, avg R w/o best day (+ Day t, w/o top 2 days: WW-CLUSTER), per-family better/worse counts, then the live-period check
  on recorded sessions; an EXISTING engine only (ENG1-A, no one-off simulators). Passing card -> backlog -> testing arena.
- Owner guardrails (rule 26): ask first before day-type switches etc.; consistency over churn; Primary is the scoreboard.
- HELD: RSGD1 (Scout card, Skeptic-signed, MDE ~0.15R) - day-type switch -> needs the owner's yes via the parent session.
- FAMC: PAUSED by the guard (no calendar owner since Observer was disabled; no build log). Tally at pause: 4 scored sessions,
  mean delta -0.089R, w/o best (11-11) -0.323R, K_edge 0.388. Parent session decides reassign vs formal pause.
- Tools kept ready: fwdcal/mirror.py (+ official21.py auto, guard selftest), famc_shadow.py (guards: closed session, data
  present, journal final, calendar build log), spotc/spotc.py, guild_read.py, builder_blockguard.py.

## Standards I work to (guild)
Frozen plan + checklist (research/SKEPTIC_CHECKLIST.md) before any score; one look; excess over a matched / shared-day control;
family try-count bar; gross first, ex-market, R beside ATR; pooled ratio + day-clustered t (#39); MDE beside every close (#41);
journal guard (#40); half days dropped (#42); locked block refused at request AND read (#43); rule-change context from the ledger;
live R on one basis across LR8 (#37). Every number in a post comes from an out file.

## Learned (standing)
- Replay vs live: exits replicate; the gaps were trade SELECTION (spread quotes, caps cascade, halts) and the R BASIS (LR8), not
  fills. Decompose into price gaps before blaming the engine.
- Fixed costs can be right where a fitted model undercharges: compare by quintile, prefer max(old, fit).
- Mechanistic broker limits fitted on a few moments misplace events by day: validate per-day counts first.
- Market-state on/off, up-day timing, brackets and scale-outs failed honestly; counter-state trades do no worse (SPY reversion).
- Never `git stash` while jobs write into the worktree; never `git fetch --depth=1` on data branches; keep background jobs < 2 h.

## Failed (owned)
- 11-18 famc journal_final selftest 'no journal' case used commit=None = live lookup; passed by luck until the 11-18 commit.
- 11-12 03:45 claimed buying power drove Gen's early halt; the cap test disproved it (corrected the same night).
- 11-13 nearly ran a --depth=1 fetch on a data branch mid-run (caught before it executed).
- Rejected engine variants: --bp buying-power cap, --stopslip replacement (max-form adopted instead by Lead).
- Closed studies (with MDE where posted): GAP-U re-test, REGSW-2 0/4, RCOMPASS v2 0/3, UPDAY-LONG (nothing above ~0.025R).

## Next
- Monday queue above. Afterwards: whatever Lead slots from the results (D3 replay filter, MOMSIDE follow-up if it passes).
