# builder notes (current; full history through 2026-11-15 archived in roles/builder_log.md)

Educational only — not financial advice.

## State (2026-11-16 22:35 ET)
- MONDAY SCORES DONE (one look each, all CLOSED, MDE stated): MOMSIDE C1 VALID t 0.96 (up-day cell, C3 ~0, FWD -723R t -3.06);
  SIZESTOP conditioning ~0 (C1 t 0.12 / C2 0.65; known widening red flag); DIPTURN C1 +0.009R t 0.92 / C2 -0.012R.
- NEXT: TUESDAY 11-17 >= 16:30 ET FWDCAL fresh 11-16..11-17 (guard selftest first; Skeptic signed off); audit now prints the
  effective_sessions.json tier per account (descriptive). Use GLOSSARY names (Session replay / 2-year backtest / Live). Then FAMC 11-17 (INFQ).
- Readiness: `python research/check_monday.py` (outcome-free) -> READY on 11-15 16:30 ET; rerun it first on Monday.
- ORDER (Lead 11-15 16:58): MONDAY 11-16 >= 16:30 ET: MOMSIDE -> SIZESTOP -> DIPTURN. TUESDAY 11-17 >= 16:30 ET: FWDCAL fresh
  11-16..11-17, only after `python research/fwdcal/mirror.py --guard-selftest` passes and Skeptic signs off. Steps:
  1. FWDCAL fresh 11-16..11-17: `cd research/fwdcal && python mirror.py --dates 2026-11-16..2026-11-17 --delay 0 --quotes
     --stopslip-max --fetch --jobs 4 --tag _fresh2` (re-deepen data branches first: `git fetch -q --shallow-since=2026-11-02
     origin <10 data branches>` + `--shallow-since=2026-10-28 origin claude/intraday-trading-system-witis4`; NEVER --depth=1).
     Journal guard + block guard built in; LR8-basis audit with exit_parts; split live-quote vs pool; Testing D/E/F included.
  2. MOMSIDE: `python research/momside/momside.py --score` (needs data/daily_closes.parquet + data/trades_full.parquet; rebuild
     with --fetch / build_full.py if the container is fresh). Plan + Amendments 1-4 (C4 6-1, full-day lists, top-5, half days).
  3. SIZESTOP: `python research/sizestop/sizestop.py <scratchpad/hold/bt> 4` (GEN hold lists: rebuild via bereplay/bt_hold.py if
     missing; dividends data/cash_div.parquet via fetch_div.py). Scout plan + A1 ex-div + A2 half days; Skeptic's 3 asks in.
  4. DIPTURN: `python research/dipturn/dipturn.py --score` (uses momside trades_full). Scout plan + A1 tod >= 955 + A2 half days.
  Each prints Skeptic's pre-registered audit items (roles/skeptic.md) and MDE / 'nothing above X; smaller unknown' on a close.
- Then: Observer runs MOMSIDE-LIVE after my lab post; Lead takes FWDCAL to the owner with the replay-records (D3) decision.
- Shared tools: research/guild_read.py (block-safe 1-min / daily reader; every new reader uses it), research/builder_blockguard.py
  (request-time guard in all my fetchers), fwdcal/stopq.py + matchgap.py (replay-vs-live diagnostics).
- FAMC nightly: append_day.py D, then evd1/famc_shadow.py --date D (needs Observer's pre-open calendar row; ~90% coverage).
  Tally: s1 11-11 raw +0.611 / gross +0.424; s2 11-12 raw +0.034 / gross -0.175; 11-13 and 11-16 unscorable (calendar timing).

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
