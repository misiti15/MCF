# Research wave 5 — 2026-11-27 (evening, market closed) — synthesis

**Educational only — not financial advice.**

## In plain words

Four tasks ran tonight: three studies, each pre-registered before scoring with costs in (LIVE-L first, LR8 alongside)
and the locked block 2024-11-01..2025-02-28 never read, plus one build. **No study passed.** The build, the index
open-dip forward shadow (IDXFWD), is **not safe to rely on yet**: one skeptic upheld it, the other found two real defects.
It logs journal rows only (no orders), so nothing live is at risk, but it must be fixed before its first half-day trade
and before it is ever scored.

What we learned that is useful:
- **The 09:50 entry rule is not what costs us the big movers.** BDI today saw 48 of 50 big movers set up at 09:35-09:45.
  Entering then does get a better price (pooled CHECK +0.048 R/trade before costs vs +0.004 at 09:50), but wider early
  spreads and tighter stops eat all of it (-0.057 vs -0.059 after costs on CHECK; T2 worse, -0.113 vs -0.063). The
  earlier mover lists also catch fewer big movers the right way (CHECK 14.5% vs 17.5%).
- **Longs do not fix Primary's up-day losses at single-stock cost.** None of four live longs added to Primary helps
  (-0.06 to -4.07 R/day on CHECK and T2). They do move against the short book (corr -0.07 to -0.30) and the SQZ
  squeeze-reclaim long hedges Primary's worst 20% of days (+0.8 to +1.7 R/day), but with about zero edge before costs the
  hedge costs about 0.10 R per trade. Two studies point the same way: if a hedge is wanted, buy it in the index
  (about 1/5 of the cost), not in single stocks. That idea is untested and needs its own PREREG.
- **Costs are the wall again**, as in waves 3 and 4.

Verdict rule: a PASS/LEAD with 2 skeptic refutations becomes FAIL, 1 refutation becomes INCONCLUSIVE; for a BUILD, any
refutation means **not safe**. Only IDXFWD was given to skeptics (1 of 2 refuted it). The three FAILs had no pass to
overturn.

## Table

| Task | Verdict (after skeptics) | Configs | Key numbers (after LIVE-L costs unless stated) | What next |
|---|---|---|---|---|
| OPENDRIVE — enter K6 movers at 09:35/09:40/09:45 instead of 09:50 | **FAIL** (0/24) | 24 | Pooled CHECK gross +0.048 (09:35) vs +0.004 (09:50); net -0.057 vs -0.059; T2 net -0.113 vs -0.063. Right-way capture of big movers CHECK 14.5% vs 17.5%, T2 24.0% vs 30.4%. A 7.6 bp early surcharge was assumed (no live entry before 09:49 in 115,993 journal rows); without it 09:35 CHECK is -0.024, still negative. | Not added. Log-only quote snapshot idea (OD-EARLYQUOTE) noted below; useful only if a later early rule is positive before the surcharge. |
| LONGBOOK — one live long added to Primary as a diversifier | **FAIL** (0/8) | 8 | Primary R/day change on CHECK (cap 10): GEN-261027-10 -0.06, GEN-261023-07 -0.25, ULT-05 -0.51, CWT14-WB5 -2.04; range on CHECK+T2 -0.06..-4.07. Corr with shorts -0.07..-0.30; up-day help up to +1.4 R/day (about 1/5 of Primary's -7.7 R/day up-day loss), given back on down and quiet days. | Not added. Untested idea: index long on breadth_open > 0.65 at 11:30 (low hopes: wave-4 DAYTYPE failed). |
| UPDAY — long-only up-day setups (RSL, SQZ, third family) | **FAIL** (0/16) | 16 | All 16 negative on CHECK and T2. SQZ S2 -0.095 R/trade (CHECK+T2); +1.7 R/day on Primary's worst 20% days, -1.11 R/day on the rest; gross about 0. Best of 16 RSL R1 -0.004. | Not added. Untested idea: index-long hedge sleeve at the SQZ moment (overlaps HEDGE-B "one-shot hedge"). |
| IDXFWD — forward shadow for IDX6 (QQQ 1.5% by 09:55 -> TQQQ) and IWM45 (IWM 0.75% by 09:45 -> TNA) | **BUILT — NOT SAFE** (2 skeptics, 1 refutation) | 2 frozen | Reproduces the study exactly (IDX6 FIT +4.293 n1, CHECK +0.015 n1; IWM45 FIT +1.148 n10, CHECK +0.261 n9). Backfill 11-05..11-27: 5 trades, 3 days, +1.43R (avg +0.29; IDX6 +1.06 avg on 2, IWM45 -0.23 avg on 3); stress +0.18 avg; t 0.37; 3 of 15 signal days. Both skeptics re-ran the backfill byte-for-byte. | Fix the two defects below, then add the trigger line. Do not score before the fix. |

### Why IDXFWD is not safe (skeptic 2, confirmed against the code description)

1. **Half-day exit lands in after-hours.** `_session()` keeps bars to 15:59 and Alpaca SIP bars include after-hours
   prints, so on half days `exit_min = min(955, last+1-5)` gives 15:55, not the 12:55 RULE.md rule 6 promises. The study
   (`idx_sim.py`) has the same formula, so "reproduces the study" partly reproduces the bug; the cached history
   (2025-07-03, 2025-11-28, 2025-12-24) shows it. The unit test passes only because its synthetic bars stop at 13:00.
   No backfill trade is affected (11-27 had no signal), but a trade on 12-24 would be held into after-hours. Fix: take
   the close from the market calendar (or cut bars at the official close) in both shadow.py and idx_sim.py, and re-run
   `--verify` to see whether any historical half-day trade changes.
2. **"Avg R w/o best day" is wrong.** `_st` divides (total - best day total) by (n_trades - 1), removing a whole day but
   one trade. Book now: reported -0.40, correct -1.60/3 = -0.53. It is a frozen pass bar, so it must be fixed before any
   scoring (a code fix of the metric, not a rule change).
3. Minor (skeptic 1): risk <= 0 crashes instead of skipping like the study; an empty API fetch on a re-run overwrites
   done rows; a run before ~10:30 writes "skipped" (the after-16:15 run replaces it); the PREREG random-day control (500
   draws) is not coded yet and its sentence is cut off.

Until the fix lands, the parent should **not** add the shadow line to the daily forward-logs trigger.

**Configs tonight: 50** (24 + 8 + 16 + 2 frozen forward rules). **Cumulative N ≈ 9,300 → ≈ 9,350.** Lineage bar stays
about t ≥ 4.3; nothing tonight comes near it.

Every finalist is listed in each study's REPORT / results file under `research/<key>_1127/` (opendrive, longbook,
upday, idxfwd).

## Rule changes inside the windows used

OPENDRIVE, LONGBOOK and UPDAY replay the same rules on history (T2, FIT, CHECK to 2026-11-04; LONGBOOK uses live
rules and LIVE-L costs on the same history), so no ledger effective date falls inside their figures. The IDXFWD
backfill (2026-11-05..11-27) is shadow-only on index ETFs and uses no live setup, sizing or account rule, so none of the
117 ledger entries effective in that window (from `2026-11-04-lowrep-explore1-livelab`, eff. 11-05, through
`2026-11-27-gyh-v1-v3` and `2026-11-27-rot-b3`, eff. 11-27) changes its numbers. Any figures quoted from live accounts
for these windows must list those dates alongside.

## Backlog actions (this commit)

- No study survived, so no new backlog entry.
- `qqqopen-1127-idx6-qqq150-trail`: notes updated with the IDXFWD build, backfill, and the two defects that block scoring.
  Stays an idea / forward lead.
- Not added (from FAIL studies; each would need its own PREREG and N): OD-EARLYQUOTE (log-only 09:35-09:45 NBBO snapshot
  for K6 names; housekeeping-logging, worth doing only if an early rule is positive before costs), the breadth index long,
  and the SQZ-moment index hedge sleeve.

Educational only — not financial advice.
