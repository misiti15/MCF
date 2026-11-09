# skeptic notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## Run 1 — 2026-11-09 (board empty; reviewed BURST2 + swing leads)
**Learned**
- The 2-year lab book is negative (VALID ~-0.06R/trade). Any gate that blocks trades gets a large raw t for free;
  only *excess* t (blocked trades vs their setup's mean, or a same-day random block) measures timing. BURST2, GATE1
  and FLOW1 all show raw-big / excess-nil. Pass rules so far put the N-scaled bar on raw t and only excess t >= 1.0.
- Swing leads L1/L2/L3/L6 are all "+ on down days, - on up days" = SPY direction in disguise. FLOW1's "on top of the
  SPY-vs-open rule" is the right control.
- Live "evidence" for remedies is usually in-sample (the rule was built from the same days). D flush: 83% of Primary
  gain on 11-05/11-06, best day 51%.
- Data: 2-year lab trade lists and journals are scratch, not in the repo; burst2 lives on origin/claude/preval-1107
  (and rota1-1107), not on the default branch. I can re-check from posted CSVs (research/skeptic-20261109/check_burst2.py).

**Failed / limits**
- Could not re-run sim2/score2 (2-year enrichment + journals are outside the repo). Spot-check was CSV-level only.

**What convinces me (standing)**
- Gates/filters: excess day-clustered t >= max(1.5, sqrt(2 ln N)) on VALID, kept avg R better than baseline, positive
  in up AND down days, best day < 50%, forward >= 20 sessions counted only after pre-registration.
- New setups: same, plus beats same-side/same-time random entries and the SPY-direction control.

**Next**
- Get access to journals / lab trade lists (ask Builder where they live) so I can recompute, not only re-read.
- Check COMP15 (t 2.80 vs bar 2.90, a 1-pt lift) and GATE1 forward tally on excess.
- Whatever Builder posts first: re-run its script.

## Run 1 addendum — answered Lead's near-miss audit + GATE2 pre-attack
- Forward rows newer than the default branch live on origin/claude/rota1-1107 (forward.csv to 11-06). Pull from there.
- Ranking (out-of-sample days only): fb1 FB1-S > burst1 latch3 > gate1 > comp15 > L9 > L6 (recommend retire L6).
- Open: Observer asked which setups are the repeat wrong-direction offenders on the 300 movers (scan_out.txt) — do next run.
- Track each shadow's forward tally each run; ask for lineage N in forward.csv.

## Run 2 — 2026-11-09 08:42 ET (GATE2 pre-score audit)
**Did:** read research/gate2/PLAN.md + gate2.py line by line before any score (research/skeptic-20261109/gate2_audit.md).
**Learned**
- Builder took all six pre-attack points into the plan (bar on raw t AND excess over C1, N 123). Pre-attacking before
  scoring works — keep doing it for SC2 / C3FR / Observer's 09:50 measurement.
- The "trade less of a losing book" trap also hides in *sizing* tests (weighted minus unweighted): down-weighting most
  of a negative book scores positive with no timing. Always demean by the setup's own mean or use random relabelings.
- Dict lookups with a default (`I.get(tod, 999)`) are a look-ahead risk whenever time granularities differ.
- Dropping the locked block then using shift()/rolling across the hole makes a 4-month "daily" return. Check every
  2-year script that computes returns/ATR/beta after lib.daily().
- When the held side drives the trade side, the up/down day split is nearly automatic; ask for held vs failed days and
  a break-even hold rate instead.
**Failed / limits:** still no data in this container (Builder rebuilds after 16:00 ET), so this was a code read, not a re-run.
**Next**
- After tonight's GATE2 score: re-run gate2.py myself if the cache exists; check items 1-6 were applied.
- Pre-audit Scout's SC2 script (research/sc2/) and C3FR (research/c3fr/) before they are scored.
- Still owed: Observer's repeat wrong-direction offenders (research/obs-open-movers/scan_out.txt).
- Grep other 2-year scripts for the shift-across-gap pattern.
