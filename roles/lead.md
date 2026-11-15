# lead notes

(Current state first; full run history in roles/lead_log.md.)

## State (2026-11-15, Sunday)
- **Owner priorities, in force:** (1) LIVE REPS faster (11-11, "until further notice"); (2) up-day / leveraged-ETF thread (restart 11-13) — CLOSED by guild 11-14 on net results, with MDE: index ~5-10bps unknown, long selection nothing above ~0.025R; (3) direction research anchored on the 09:50 state / 09:30-09:50 range (owner rule 11-14).
- **Monday 11-16 after 16:30 ET (in order):** FWDCAL fresh rule-21 audit 11-16..11-17 (frozen engine: quotes + max-form stops + LR8 basis w/ exit_parts; journal-timing guard) -> MOMSIDE (12-1 / 6-1 momentum side filter, full-day lists, strict holdout window, family 187, BAR90 2.91; live companion gated) -> SIZESTOP (size-conditioned stop width, size-cut + random-day controls) -> DIPTURN (owner's dip-then-turn on long/short setup trades, family 2,611, MDE ~0.08R).
- **11-18:** REPS3 forecast scoring + ICCSET refresh on LR8 basis (Scout) -> owner note with reps tables.
- **FAMC:** forward shadow, 2 scorable sessions (+0.61R, +0.03R vs control), coverage ~90%; nightly calendar (Observer) + shadow (Builder).
- **Open owner items:** COMPCAL (open / 09:50 reference), PROMO2 (strict / soft), RULE21-DB, days 1-3 questions (hunt vs harvest; earnings exception; GEN slots + 20 vs 40-60 sessions), S6 long-hold frozen book. After the fresh FWDCAL audit: raise D3 (replay records for rule-21-passing accounts) as a DECISION.
- **Tally since 11-09:** ~77 ideas, 164 configs/looks, 0 passes, 1 forward shadow.

## Standards the guild adopted (keep enforcing)
- Excess over a matched control, not raw t (losing-book volume cut). Gross edge first. Kept avg R beside totals.
- Family try-count governs Testing moves (market-state family 2,605; laggard 92; near-HOD 1,671...).
- Size-cut control for any sizing/stop result. Shared-day permutation nulls for day-level rules.
- Every closure prints its MDE: "nothing above X; smaller unknown". State a null's power before calling it negative.
- Labels known at entry only (no whole-day labels). Pool binned marks with day-clustered SE (#39).
- Half days dropped (#42). Every fetch refuses the locked block at request time; every read goes through guild_read.py (#43).
- LR8 cost basis from 11-12: recompute per trade or split at 11-12; raw R is basis-stable.
- SKEPTIC_CHECKLIST.md before freezing any plan.

## Learned (lead)
- Verify mechanism claims before they reach the owner (I relayed 'broker routing', 'Gen 2x slower', 'recognisable, not predictable' too fast; all corrected).
- Never guess a PR number in a parallel call. Fetch the base right before a PR; owner-inbox conflicts happen (union-merge appends).
- Keep board posts <= 120 words before writing (assert).
- test_poll_log timing test is flaky under load; re-run alone, note in PR.

## Next run
- Monday after the close: read results as they land, failures first; owner PR with results + D3 decision.
