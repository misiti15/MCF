# lead notes

(Current state first; full run history in roles/lead_log.md.)

## State (2026-11-16, Monday night)
- **Owner priorities, in force:** (1) LIVE REPS faster (11-11, "until further notice"); (2) up-day / leveraged-ETF thread (restart 11-13) — CLOSED by guild 11-14 on net results, with MDE: index ~5-10bps unknown, long selection nothing above ~0.025R; (3) direction research anchored on the 09:50 state / 09:30-09:50 range (owner rule 11-14).
- **Mon 11-16 DONE:** MOMSIDE CLOSED (t 0.96 vs 2.91; up-day cell; FWD reverses -723R; MDE 0.025R), SIZESTOP CLOSED (conditioning ~0; gross-vs-net check asked), DIPTURN CLOSED (t 0.92 vs 3.57; MDE 0.045R). MOMSIDE-LIVE parked.
- **Tue 11-17 DONE:** FWDCAL exact-minute 0/10 (stamp offset; signal-minute 0.932); OFFICIAL rule21() line pending from Builder. HKS950 CLOSED (t 2.18 < 2.46). BLKOUT CLOSED, policy stands (MDE 0.021R). FAMC 11-17 no events.
- **11-18:** REPS3 forecast scoring + ICCSET refresh on LR8 basis (Scout) -> owner note with reps tables.
- **FAMC:** forward shadow, 2 scorable sessions (+0.61R, +0.03R vs control), coverage ~90%; nightly calendar (Observer) + shadow (Builder).
- **Open owner items:** COMPCAL (open / 09:50 reference), PROMO2 (strict / soft), days 1-3 questions (hunt vs harvest; earnings exception; GEN slots + 20 vs 40-60 sessions), S6 long-hold frozen book. D3 superseded by owner effective_sessions.json (11-16): replay 0.35 / 0.2 / 0 by held-out match. RULE21-DB approved by owner 11-17 (ledger). New 11-18: TIER-BIAS, UNCAL.
- **Tally since 11-09:** ~78 ideas, 77 tested, 174 configs/looks, 0 passes, 1 forward shadow.

## Standards the guild adopted (keep enforcing)
- Use docs/GLOSSARY.md names (Live, Shadow, Session replay, 2-year backtest/screen/history); never mix sources in one number (owner 11-16).
- Guard refusal on a quiet day (no commit after 15:55): wait or name the account; never loosen the threshold (11-15).
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
- PR #223 merged 11-17 (results + TIER-BIAS DECISION + UNCAL question). Next: Wed 11-18 REPS3 + ICCSET, Scout final shortlist (A1/A2). Watch owner replies on TIER-BIAS / UNCAL / promotion hold.
