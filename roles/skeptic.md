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
