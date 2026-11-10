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

## Run 3 — 2026-11-09 10:41 ET (GATE2 amendment check + SC2 pre-score audit)
**Did:** verified GATE2 Amendment 1 in code (A2 compares conf bar end to the lab entry minute; lab tod = entry bar close,
research/bdi/1104/DATA.md). Audited SC2 (research/skeptic-20261109/sc2_audit.md).
**Learned**
- Lead adopted "excess t over a matched control" as the guild standard (lead-20261109-0900-1). My job now: check the
  control actually isolates the claimed mechanism, not just "some control exists".
- Lead-lag/laggard ideas: random-name and event-free controls don't separate "lag catch-up" from "driver momentum".
  Ask for driver-hedged R and a non-laggard same-event control.
- Lineage creep the other way: a new driver/universe can reset N to a small number while the underlying bet (laggard
  catch-up) has many parked attempts. Ask for the family count.
- Observer's data map: journals live at the root of mcf-data* branches (git fetch --depth=1; git show FETCH_HEAD:journal.db).
**Next**
- After 16:00 tonight's scores: re-run GATE2 / SC2 if the cache appears in this container; else spot-check outputs.
- Pre-audit C3FR (research/c3fr/) and Scout's SC1 script when posted; Observer's CWT14 skip-filter plan.
- Use the journals to recompute the fb1 / latch3 forward tallies myself (they are the two weak leads Lead kept).

## Run 4 — 2026-11-09 12:40 ET (CWT14SKIP + SC1 pre-score audits)
**Did:** research/skeptic-20261109/cwt14skip_sc1_audit.md. Lead adopted family try-counts (laggard family N 76, Scout);
SC2 Amendment 1 and GATE2 Amendment 2 (strict <) are in before scoring.
**Learned**
- Lab frame facts (mcf/research/heat.py:73-77): fromOpen in %, tod = bar END, atr_d = prior-day ATR. Reuse for any audit.
- Random-block controls should be stratified by sub-variant when the pool mixes setups with different mean R.
- Gap/event setups need market-structure realism the cost model doesn't have: Reg SHO 201 uptick rule after -10%,
  LULD halts hiding 1-min gap-throughs inside 5-min bars, borrow. Ask for these on any big-gap short or event trade.
- A "failed-hold" control is a fade signal, not a neutral baseline — controls built from the opposite condition inflate excess.
**Next**
- Tonight's scores (GATE2, SC2, CWT14SKIP, 09:50 measurement): check outputs against the audits; re-run if cache appears.
- Observer's near-HOD continuation long: when planned, insist on family N (GEN NewHOD, orb20) and the same-fromOpen-bucket control.
- Recompute fb1 / latch3 forward tallies from the journals (mcf-data* branches) after the close.

## Run 5 — 2026-11-09 14:40 ET (re-ran Observer's GEN giveback study from the journals)
**Did:** fetched all 7 journals (git fetch --depth=1 origin mcf-data*; journal.db at root), re-ran obs-genlate/genlate.py:
IDENTICAL on 10-06..11-06. Added gb_check.py: giveback by family, longs and shorts, day concentration.
**Learned**
- First independent re-run in the guild: Observer's numbers hold. Journal-only studies are cheap to re-run — do it.
- Scripts without a date cap drift as journals grow; ask every study to fix its window.
- Giveback (mfe >= 0.5R then <= 0) is book-wide: longs -620R (GEN 27%), shorts -713R (GEN 19%; MF1 57% of reached).
  A GEN-only exit remedy would break the Remedies rule; asked Builder to replay on all families.
- Exit-tag comparisons across setups (hold vs holdtr) are confounded by setup; only a replay of the same entries settles it.
**Next**
- Tonight's scores: GATE2, 09:50 measurement, SC2, CWT14SKIP (check amendments applied, controls behave).
- NH1 plan (N 1,671, bar 3.47): priors are negative (HOD-break long -0.099R); pre-audit its script when posted.
- fb1 / latch3 forward tallies need bars (dist to LOD, MTM): ask Builder for a cached 5-min file for live dates.

## Run 6 — 2026-11-09 16:41 ET (lab-vs-live cost check; OD0950 review)
**Did:** costgap.py on the 7 journals (trades joined to signals by broker_order_id; 16,615 paper trades 10-06..11-06).
**Learned**
- Lab costs are ~3x heavier than paper fills (0.218R vs ~0.015-0.06R/trade), same sign all 24 days and accounts.
  The 0.16R screen-to-live gap is not cost -> winner's curse / exits / delay. Never loosen costs from paper data.
- Journal facts: signals.ref_price is a stale price (~bar close; sd 20bp vs the quote mid); info JSON has bid/ask at submit;
  paper fills sit ~4.6bp from mid (at the touch); signal->fill ~1.5 s; bar_age ~1.2 min at signal.
- Cost per R is driven by stop width: tight quartile (44bp) 0.42R/trade lab cost. A min stop width in bps is a lever.
- OD0950: flat -0.10R across deciles = the cost charge; gross ~0. Ask for gross R whenever net R is flat across buckets.
**Next**
- GATE2 / SC2 / CWT14SKIP results tonight: check against the audits.
- Suggest to Scout/Builder a "min stop width" remedy test (per family, retention, excess) — Lead to slot.
- Real-money vs paper fill gap is unknown; flag if any real account data ever exists.

## Run 7 — 2026-11-09 18:43 ET (attacked GATE2 C1 and CWT14SKIP X1.5, the night's two "positives")
**Results of the night:** 0 of ~52 configs pass except CWT14SKIP X1.5 (own bar). Closed: 09:50 continuation, laggard family
(0/92), NH1 (market direction), SC1 (0/12), BE exits (hurt 27/27; giveback upper bound overstated ~10x, as I warned).
**Learned**
- A random-bar control can contain an anti-signal (random bars after a move include extended entries that revert);
  derive the control's own avg R (avg - excess) and ask whether it is plausible. Match controls on distance-to-stop
  and time, and report excess in ATR units, or R-normalisation (smaller R near the stop) inflates the excess.
- "N of N variants better" is not N confirmations when variants fire on the same symbol-days; count distinct events.
- Lab trade lists don't apply the earnings blackout; any filter whose skips cluster on event days may vanish live.
- pip/pyarrow unavailable here (PyPI install hangs): parquet-based checks must go to Builder with a script.
**Next**
- Builder's answers: GATE2 C1m / ATR-unit excess; cwt14_earn.py result.
- STOPW (my lever) scores next: check family-level better/worse and that same-$-risk sizing is applied honestly.

## Run 8 — 2026-11-09 20:40 ET (HODSEP attack; answered Observer; accepted GATE2 C1m)
**Found:** HODSEP look-ahead — `c[b] / c[b-6]` with b = 4/5 wraps to the same day's last bars (numpy negative index).
"Too strong to be true" (28/28 days, t 16.8, wrong sign) was the tell; Scout flagged it, I located it in the code.
**Night's closures confirmed:** CWT14SKIP closed (51.5% of skips in earnings blackout; blackout-free t 1.05, my call).
GATE2 timing survives C1m in ATR units (+0.02-0.03 ATR, below a round trip). STOPW = 85% size cut; stop effect fails down days.
**Learned**
- Grep every script for `x[b - k]` with small b: numpy wraps silently; slices go empty (a NaN symptom nearby = check).
- Results that are "too consistent" (all days same sign) on descriptive scans → look for look-ahead first.
- Paper's favourable fills on tight-stop reversion entries are bar-close-to-order drift, not fill flattery; the lab is
  harsh specifically there.
- Lab trade lists ignore the earnings blackout: always check event-day share of any filter's skips.
**Next**
- HODSEP re-run (b >= 6, next-bar-open fwd, tod strata) — re-check when posted.
- Observer's combined GATE2 rework plan: pre-audit (it must add gross; costs ~10-15bp vs +6-9bp timing).

## Run 9 — 2026-11-09 22:41 ET (Observer's extension split; rolling-compass pre-attack)
**State:** HODSEP closed after my fix (66% of v1 candidates were leaked bars). GATE2 closed (rework gross negative).
Owner focus 2026-11-10: rolling compass / condition-based setup on-off (Scout starting).
**Did:** challenged "longs at a fresh high are the only positive cell": EXT longs +0.058R gross but -0.003 ATR move.
**Learned**
- Always put R next to the price move in ATR: when R-mean is positive and the ATR move is ~0, R-normalisation (tight-stop
  winners) is carrying it. Ask for median R too.
- Compass / on-off studies: the classic trap is defining "held/flipped" by the close. Insist on point-in-time flip
  definitions and a random-standby control.
**Next**
- Observer's ATR / day-type answer; Scout's rolling compass descriptive split (pre-audit before any plan).
- Observer's flow-sell "short the drop, not the fresh low" idea: MF2 EXT n 29 — tiny; insist on 2y with per-variant retention.

## Run 10 — 2026-11-10 00:41 ET (compass backfill audit; market-state try-count ledger)
**Did:** audited research/compassbf (PASS on construction; tie fix: mark tag must be strictly before the entry minute);
wrote the market-state ledger (broad N 2,605 -> BAR90 3.57; narrow 291 -> 3.03). Observer withdrew the fresh-high long
thesis after my R-vs-ATR challenge (82% from 11-06, ex-SPY t 0.03).
**Learned**
- Ties at bar/mark boundaries recur (GATE2 A2, now the compass tags): live publishes a mark after it closes plus latency;
  any tag "at or before" an entry at the same minute is look-ahead. Always strict < or a latency offset.
- Split adjustment doesn't matter for within-day ratio features; it does for cross-day levels (prior close, gaps).
- With N in the thousands, the honest path for owner-directed gates is a single pre-registered rule + forward shadow.
**Next**
- Confirm Builder re-tagged with strict <; then pre-audit RCOMPASS's first descriptive output (up-vs-down-afternoon share,
  random standby control, same-signal comparison).
- MF fresh-low skip (Observer backlog entry): ~53 live trades, worst day 72% — 2y lab must carry it.
