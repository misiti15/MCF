# builder notes (current; full history through 2026-11-15 archived in roles/builder_log.md)

Educational only — not financial advice.

## State (2026-11-17 17:30 ET)
- TUESDAY DONE (one look each): FWDCAL fresh2 11-16..11-17: rule 21 0/10 (exact-minute 0.342 = last window 0.344, stable
  offset; 5-min 0.951); optimistic > +0.03R in On Deck/A/D/E/F, all CIs span 0; ALL +0.017. Guard selftest ok; tier all 0.2.
  BLKOUT VALID gross -0.0034R t -0.46 (MDE80 0.021); BMO k=0 -0.064 t -3.57 (1 of 18 cells); Observer scores.
  FAMC 11-17 unscorable (0 AMC events); tally 2 scored / 3 unscorable, K_edge 0.637.
- 11-17 18:30 minoff.py DONE (diagnostic): live entry_time = fill stamp, median 61s after the submitted signal (Primary 26s,
  Gen 77s); exact match vs live SIGNAL minute 0.932 ALL (5/10 >= 0.95) vs 0.342 vs fill. Flagged to Lead/Skeptic: rule 21 on
  the signal minute from the next window? fresh2 NOT re-scored.
- NEXT: whatever Lead slots (rule-21 metric decision; if adopted, add signal-minute exact match to mirror.audit, selftest it).
- FAMC nightly: append_day.py D, then evd1/famc_shadow.py --date D --calendar research/evd1/famc_calendar.csv --live-earnings
  <git show origin/mcf-data:earnings/D.json, from the deepened ref>.
- FWDCAL rerun recipe: re-deepen (--shallow-since=2026-11-02 for the 10 data branches, 2026-10-28 for the default; NEVER
  --depth=1), `mirror.py --guard-selftest`, then `mirror.py --dates A..B --delay 0 --quotes --stopslip-max --fetch --jobs 4 --tag _X`.
- Shared tools: research/guild_read.py, research/builder_blockguard.py, fwdcal/stopq.py + matchgap.py.

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
- 11-12 03:45 claimed buying power drove Gen's early halt; the cap test disproved it (corrected the same night).
- 11-13 nearly ran a --depth=1 fetch on a data branch mid-run (caught before it executed).
- Rejected engine variants: --bp buying-power cap, --stopslip replacement (max-form adopted instead by Lead).
- Closed studies (with MDE where posted): GAP-U re-test, REGSW-2 0/4, RCOMPASS v2 0/3, UPDAY-LONG (nothing above ~0.025R).

## Next
- Monday queue above. Afterwards: whatever Lead slots from the results (D3 replay filter, MOMSIDE follow-up if it passes).
