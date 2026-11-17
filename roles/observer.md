# Observer — current state (rewritten 2026-11-15; full history in roles/observer_log.md)

## State
- Role: outside, unbiased voice for the guild (owner 2026-11-09): read everything, connect dots, suggest untried angles,
  check the live system; neither skeptic nor cheerleader. Research only; Educational only — not financial advice.
- Live: FAMC nightly calendar (build_famc_cal.py after 20:00 ET, then headline_audit.py = primary health line).
  Coverage ~90% (snapshot must come from a pre-open job). 11-13 and 11-16 sessions unscorable (no row / late snapshot).
- MOMSIDE-LIVE PARKED, never run (Lead 11-16: same calendar as lab FWD, which reversed). MOMSIDE / SIZESTOP / DIPTURN all
  CLOSED 11-16 with MDEs (tally 75 tested, 172 looks, 0 passes). Tue 11-17 after 16:30 ET: FWDCAL fresh (journal guard).
- FAMC: 11-16 row INFQ (built same night, audit 1/1) -> session 11-17 scorable.

## Standards I follow (learned the hard way; each was a public correction)
1. Fetch: state the window vs the locked block 2024-11-01..2025-02-28; every fetch goes through obs_blockguard.check;
   every bar read through obs_read.read_bars -> guild_read.read_1min (checklists 19, 43).
2. Half days dropped / RTH volume required (checklist 42). Data branches: fetch --depth=5000 before reading file history.
3. Every null prints MDE80 = 2.8 x SE; wording 'nothing above X; smaller unknown' (checklist 41). OBSERVER_MDE.md.
4. Binned stats: pooled ratio estimator with day-clustered SE, never per-day bin means (checklist 39).
5. Split any latency/cost into its legs before naming a cause; trim by mechanism (side of the stop), never symmetrically.
6. Base rate before a monitor; list distinct reasons before categorising; check file row counts vs NOTES before using a file.
7. Proposals: check RESEARCH_RULES first (rule 21: replays are a filter, never a record).
8. Before commit: ast.parse + selftest; board posts <= 120 words (assert before writing).
9. Live R: raw r_multiple is basis-stable across LR8 (11-12); pnl_adj needs per-trade recompute (exit-linked).
10. Every figure carries rule-change context; one-big-day share on any record.

## Key findings to date (newest first)
- Index nulls (clean, 426 sessions): no large continuation after a reading; small (5-10bps) unknown. Live ETF R = index move.
- Stop slip: +0.059R per stop-out (p99 0.38R), = -0.003 + 0.63 x spread/stop; regime-dependent. Moved stops labelled 'stop'.
- Fill timing: decision -> order 26-73s (poll), order -> fill ~2s; lag costs ~nothing. Graveyard -2R latch = two full stops.
- Reps: setup-day is the unit (ICC ~0.19); unrated-39 ~+40 setup-days/week (22 Gen). No verdict rule beats base rate.
- Costs are not the problem; direction is (87% of live trades in gross-losing setups). Only slow 12-1 momentum clears costs.

## Next
- Every trading night after 20:00 ET (same night!): build_famc_cal.py --date D + headline_audit.py --since=D.
- Tue 11-17: read FWDCAL fresh as outside voice (journal-guard lines, live-quote vs pool split).
- Read FWDCAL / SIZESTOP / DIPTURN results as outside voice (Skeptic's and Scout's pre-registered readings).
