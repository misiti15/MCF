# LATCH-CLOSE: close a setup's open lots when its −2R latch fires (pre-registered 2026-11-11, before any two-year read)

*Educational only — not financial advice.* Lead id `swing1111-L13` (research/bdi/swings/hypotheses.jsonl). Backlog
`nightly-1110-latch-closes-open-lots`. ONE configuration.

**Why.** The per-setup −2R latch stops new entries but leaves the open book on the same bet. Primary 11-10: 43 open lots
at the latches went on to −22.46R vs −9.34R at the latch; 11-11: 30 lots −20.86R vs −9.84R (−11.02R after the latch,
41 % of the day). Other accounts: 19/26 (11-10) and 24/27 (11-11) setup-days better if closed; the worse ones are
dip-buy longs. These two days are in-sample for the idea.

**Rule (exact).** Per (setup, session), entries in order under live caps (3 lots / symbol, 30 open / setup):
1. The latch (unchanged): a trade is not taken once the setup's realised R from trades exited at or before its entry bar is
   ≤ −2.0R. Latch bar = the 5-min exit bar at which the setup's cumulative realised R first reaches ≤ −2.0R.
2. LATCH-CLOSE: every lot of the setup still open after the bar following the latch bar is closed at that next bar's close
   (mark-to-market in stop units) minus the exit-side cost 1c + 1 bp (entry cost as already booked in r). Lots that
   exit on their own in the latch bar or the next bar keep their result. Both sides, every setup, no filters.

**Data.** bt_lab1104 2-year lab lists (all lab setups) + burst1/enrich.py 5-min marks; latch trigger on lab r (production
costs; live uses gross r_multiple — the lab's gross is not stored). Locked block 2024-11-01..2025-02-28 excluded (asserted).
TRAIN 2024-10 + 2025-03..2025-12, VALID 2026-01-01..2026-10-05, LATE 2026-10-06 on.

**Pass bar (fixed now).** Lineage N = stoplab grid-A latch study (64) + this = 65 → day-clustered t ≥ 2.89 (BAR90 2.60).
Day-t = mean / s.e. of the daily delta (rule − actual, R, costs in) over days the rule acts. PASS = VALID t ≥ 2.89 AND
TRAIN delta > 0 AND VALID delta without its best day > 0 AND ≥ 60 % of families (≥ 30 affected VALID trades) better.
Reported (owner remedies rule): every family and every setup (≥ 20 affected VALID trades) better / worse and by how much;
by side; LATE.

**Forward shadow (from 11-12, all accounts).** ≥ 15 latch sessions: pooled delta > 0 and > 0 on ≥ 60 % of them; Primary
reported alone. **If the backtest passes**: DECISION with reply codes "LATCH-CLOSE testing" (On Deck + Testing A/B/C
first) and "LATCH-CLOSE all" (incl. Primary; mid-TEAM-6 trial, owner only).
