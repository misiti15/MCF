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

## Run 11 — 2026-11-10 02:41 ET (counter-to-morning row; RCOMPASS stage 1)
**State:** re-tag done (36% of mark tags changed with strict <). RCOMPASS stage 1: flips don't separate (coin-flip counts).
MFFRESHLOW closed (live pattern did not carry to 2y). Coil (CWT12) fires before noon -> flips can't touch it.
**Did:** killed the "counter to the morning reading" row from the committed family table: ex-market, aligned is no better
(F1 -0.069 vs -0.058). Also flagged held_day = "no flip all day" as future-conditioned.
**Learned**
- "Held / stayed" day labels defined over the whole session are look-ahead for intraday entries; the tradable baseline is
  "not yet flipped at entry". Watch every compass study for whole-day labels.
- Always ask for ex-market (beta x SPY over the hold) next to any aligned-vs-counter or with-vs-against split.
**Next**
- Coil morning on/off rule if Scout pre-registers one: audit TRAIN/VALID ex-market, up AND down, random block.

## Run 12 — 2026-11-10 04:44 ET (XA-PBO tool audit)
**State:** morning-condition route empty on 2y (COILAM fails: gross -0.029, TRAIN ~0; all-family map at chance).
Owner's coil on/off question: no rule from 2y data so far.
**Did:** audited research/xapbo/pbo.py (correct CSCV). Simulated: shared real edge across all configs -> PBO ~0.4,
same as noise (0.5, sd 0.25); p_oos_loss separates (0.02-0.07 vs 0.57).
**Learned**
- PBO measures whether choosing among configs is informative, not edge or overfitting per se; correlated/equal
  configs push it to 0.5 even with a real shared edge, and systematic artefacts (size cut) push it to 0.
  Always read it with p_oos_loss and the controls.
**Next**
- Whatever the guild picks next after the compass route closed; keep pre-auditing plans before scoring.
- Consider proposing (to Lead) a "what's left" review: list the selectors that beat controls but not costs
  (GATE2 timing 0.02-0.03 ATR, rvol15 +0.02 ATR, NH1 vs bucket) — combined/cheaper-execution angle, counted.

## Run 13 — 2026-11-10 06:41 ET (earnings calendar pre-audit for D1)
**State:** compass on/off route closed on 2y; SIZEBKT, FLOW1-2Y closed; XA-EPROC built (20 sessions = HARM floor, not proof).
Observer proposed D1 earnings-calendar direction, D2 premarket, D3 GEN re-screen.
**Did:** pyarrow installed this time (pip worked with a 90 s timeout). Audited earnings_yf.parquet internals.
**Learned**
- Event calendars: report date != reaction day (AMC -> next session), intraday (dmh) reports are look-ahead for morning
  rules, vendor fields need sign-only use. Always get an alignment table (gap on mapped day vs other day) before outcomes.
- The forward-shadow success criterion needs power: 20 sessions can only rule out harm.
**Next**
- Builder's alignment table; then audit whoever plans D1 (BMO/AMC split, family N incl. er-react / SC1 / gap-and-go).
- D3 GEN re-screen: check the Spearman test uses only pre-live data for the new screen.

## Run 14 — 2026-11-10 08:41 ET (D2PM pre-score audit; D3GEN / alignment notes)
**State:** earnings calendar aligned (AMC next session 5.7x normal gap; dmh behave like AMC, dropped). EVD1 (Scout, N 858)
running at Builder. D3GEN: worst-quarter screen ranks live GEN rho +0.24 (p 0.037, 10 looks) — hypothesis only.
**Did:** audited D2PM (clean timing); asked for premarket-liquidity terciles, day-type split, fixed-universe rerun; D2 family N 229.
**Learned**
- Premarket features: thin prints and odd lots make sign features noisy; ask for liquidity strata.
- Universes built from "names we traded" are selected by our own signals; prefer the fixed lab list.
- A single pre-declared primary at p 0.037 among 10 looks is a hypothesis to test on new data, not a change.
**Next**
- EVD1 outcomes (first look at the earnings direction thread) — check BMO/AMC split, gap baseline, ex-market, day types.
- D2PM results tonight.

## Run 15 — 2026-11-10 10:41 ET (EVD1 read)
**State:** EVD1 closed by Scout's pre-registered rule (TRAIN/VALID signs disagree). D3GEN ranks (CI > 0) but top third still loses.
**Did:** labelled the post-hoc cells (AMC-agree vs gapper 4/4 negative = expected ~1 in 8 by chance; held-at-09:50 =
gap-and-go; unknown-surprise >5% VALID-only). Flagged surprise availability: 'unknown' is all VALID (vendor fills late).
**Learned**
- Pre-registered reading rules (Scout's) make closures clean; my job then is to stop post-hoc cells becoming leads:
  count the cells shown and the chance of a consistent-sign one.
- Vendor fields that fill in later (eps_reported) are a live-availability trap even when history looks complete.
**Next**
- D2PM results tonight (premarket cuts). Forward-only pre-registration if anyone wants the AMC fade.

## Run 16 — 2026-11-10 12:45 ET (FAMC forward-shadow audit)
**State:** FAMC (AMC reaction-session fade, forward-only) frozen; blocked on a point-in-time AMC list (Nasdaq blocked by proxy;
live snapshot drops 'time'). Options: A store 'time' in live snapshot (housekeeping), D re-run the Nasdaq fetch action.
**Did:** audited famc_shadow.py + eproc.py: control can include same-day BMO reporters (exclusion uses AMC-only calendar);
ex-market uses full-window SPY for stopped legs; no snapshot_at < open assert; adv20 matching; clipped-mean caveat.
**Learned**
- "Non-event" controls need the FULL event calendar (all timings), not the subset the rule uses.
- Ex-market adjustments must use each leg's own holding window when stops can end trades early.
- e-processes with clipping test the clipped mean; report the raw mean beside K.
**Next**
- First FAMC nightly rows once a calendar source is decided; D2PM results tonight.

## Run 17 — 2026-11-10 14:41 ET (owner COMPASS task: attacked COMPCAL; read compass_5m)
**State:** owner priority = compass improvements. Main session's compass_5m: next 5-90 min direction 48-53% (142 tests);
5/10-min glue earlier but noisier. COMPCAL: M1 (prior-60-day remaining-move line) beats the cell table out of sample.
FAMC fixes all in; status UNBUILDABLE until owner picks a calendar source (A/D).
**Did:** audited compcal.py (no leak); proposed a vol-scaled M1 (one counted look); framing note: 'stays' != tradable (GATE2).
**Learned**
- Display tools can still mislead: always pair a "probability it stays" with "and trading it has not paid" when that's known.
- Calibration models that ignore today's volatility are likely overconfident on high-vol days — test by vol tercile.
**Next**
- Vol-scaled M1 result if Builder runs it; D2PM results tonight; FAMC row 1 when a source exists.

## Run 18 — 2026-11-10 16:40 ET (option C news classifier; vol-scaled M1; D2PM)
**State:** vol-scaled M1 lost on FWD -> card keeps M1 (my overconfidence call confirmed: +3.8 pt high-vol). SZBAND drifts
with vol. D2PM closed by its kill line. Option C (Alpaca news 16:00-19:59 -> AMC) 79% recall / 91% precision on Yahoo names.
**Did:** challenged option C's precision denominator (only Yahoo-calendar names), multi-symbol news tags, preview headlines,
limit=50 truncation; advised TRAIN-fitted partial vol exponent if tried.
**Learned**
- Classifier precision measured on a pre-filtered set (known events) overstates live precision; demand the full-universe
  denominator before a classifier feeds a shadow.
- News APIs tag several symbols per item.
**Next**
- Option C full-denominator check; FAMC row 1 once a source passes. Anything new Scout/Observer propose for day 3.

## Run 19 — 2026-11-10 18:41 ET (hybrid AMC classifier; PVSCALE; OPTFLOW)
**State:** my full-denominator ask cut option C precision 0.91 -> 0.58; Observer's HYBRID (news + live pre-open calendar)
0.887 / recall 0.76. PVSCALE: size band vol-scaled (alpha 0.8, VALID t -4.48); close-side stays M1. OPTFLOW closed.
**Learned**
- When the reference labels go stale (Yahoo 'dmh' placeholders), switch to a label-free consistency check (gap on the
  mapped day vs normal) for forward monitoring of a classifier.
**Next**
- FAMC first rows once the nightly builder exists; check the gap-consistency share nightly.

## Run 20 — 2026-11-10 20:41 ET (FAMC calendar check 1 amendment; day-2 tally)
**State:** FAMC calendar live (11-10: ALC, RGTI), first reaction session 11-11; Builder runs the shadow nightly.
NEWSDIR closed (headline direction already in the gap by 09:50).
**Did:** accepted Observer's amended pre-open check (blackout() is a write-once cache); added: assert source=='nasdaq' and
complete, else unbuildable (fallback has past dates only). Posted a day-2 tally for Lead.
**Learned**
- Read the producing code before judging a provenance check: write-once caches make "single commit" a valid proof.
- Fallback paths in live code can silently change a research input's coverage; assert the source field.
**Next**
- FAMC nightly lines (n events small late in the season); health line (gap > 2x share).
- If the owner shifts to execution/risk on gross-positive setups, pre-audit those plans (size-cut control is standard).

## Run 21 — 2026-11-10 22:45 ET (cost-killed survivors re-check; LIMEX / UNGAP)
**State:** day-3 focus shifted to execution/sizing on gross-positive setups. LIMEX (limit at signal close) fails: adverse
selection (missed trades +0.22R). Observer: 17 cost-killed setups, live costs ~1/3 lab, only RW7/RW1 survive w/o best day.
UNGAP closed (wrong sign).
**Did:** re-ran RW7/RW1 on fresh journals to 11-10: RW7 back to ~0 (11-10 -28.7R); RW1 +0.078 / w/o best +0.036, thin, post-10-30.
**Learned**
- "Survivors" on a short live window can vanish with one more session; re-check with the newest day before anyone acts.
- Limit entries on these setups select the losers; market-entry cost buys follow-through.
**Next**
- FAMC first rows (11-11). Per-setup review of setups positive before AND after costs live (one-big-day check) if Lead asks.

## Run 22 — 2026-11-11 00:41 ET (CONFIRM pre-score attack; WHATWORKS)
**State:** WHATWORKS: one live setup passes all checks (RW1 T2) and every live survivor is negative on 2y and a
down-day bet (Builder's lab join) - "what works" = shorts in a short-friendly window. Observer wrote the owner page DAY1-3.md.
**Did:** CONFIRM audit: delta over all signals includes -B on untriggered = volume-cut gain; asked for timing/skip split,
random same-share skip control, and C's own net > 0 in the pass. Timing clean.
**Learned**
- Any "enter only if X" rule scored as delta vs "always enter" on a losing book contains a skip gain; always split it.
**Next**
- CONFIRM results with the split; FAMC rows; review Observer's DAY1-3.md numbers against sources before the PR.

## Run 23 — 2026-11-11 02:41 ET (CONFIRM result; minute-10 exit pre-attack)
**State:** CONFIRM fails as entry (own net -0.019 ATR, 0/10 better). BOTHDAYS: no live setup earns on both day types
w/o best day; book = stack of beta bets (~±0.14R per 1% SPY).
**Did:** flagged the skip-part t 19 as mechanical (outcome window overlaps the selection window); pre-attacked the
minute-10 exit: measure post-10 continuation gross, random same-share exit control, family with sw-w4 + BEREPLAY.
**Learned**
- Selections defined on the trade's own early path are not foresight; only the continuation after the selection
  time is tradable. Check overlap between selection window and outcome window every time.
**Next**
- Exit plan if Builder writes it; FAMC first rows (11-11 session).

## Run 24 — 2026-11-11 04:41 ET (checklist)
**State:** minute-10 exit closed (martingale; 2y and live); DISP1 closed; CONFIRM closed.
**Did:** wrote research/SKEPTIC_CHECKLIST.md (30 checks, each tied to the study it came from); asked Lead to reference it in
PROTOCOL so plans run it before freezing.
**Next**
- Keep the checklist current; FAMC first nightly row (11-11 session); audit any new plan against the checklist.

## Run 25 — 2026-11-11 06:41 ET (NEWSMID pre-audit; horizon ladder)
**State:** checklist adopted in PROTOCOL. Observer's horizon ladder: only the slow end (S6 weekly momentum, thin) clears
costs; live S6 frozen by its -25% halt (owner question). Builder: frozen book ~7% ahead of rotating model (model marks blank).
**Did:** NEWSMID pre-audit: control 'no news that day' is a whole-day label -> use 'no news before entry'; drop pre-market
re-posts; top pre-move tercile; lexicon sanity table.
**Learned**
- Whole-day labels sneak into CONTROLS too, not only into event definitions. Add to checklist item 4.
**Next**
- NEWSMID result 11-12; FAMC first rows; update checklist item 4 wording.

## Run 26 — 2026-11-11 08:41 ET (owner task: break GAP-U / IDX3-P; REGSW-2 audit)
**Did:** read main-session regime_switch score.py/base.py. Random baseline permutes days per setup independently -> null
too narrow for a day-level rule hitting all shorts at once; asked for a shared-day permutation. Gap clean except
first-day-after-locked-block. ETB proxy back-applies recent snapshots. REGSW-2: live check in-sample by construction.
Checklist items 31-32 added.
**Next**
- GAP-U / IDX3-P re-run with the joint permutation (main session or Builder); REGSW-2 results.

## Run 27 — 2026-11-11 10:41 ET (owner top priority: faster reps — FWDREP / FASTDEC challenge)
**State:** owner priority shifted to live reps (unlock reps, calibrated forward replays, faster verdict stats). COILGAP closed.
GAP-U re-break staged for tonight (shared-day null, gap fix, ETB-off row).
**Did:** FWDREP calibration fails rule 21 (match 56% vs >=95%; replay optimistic +0.081R vs 0.03 limit); comb_* columns mix
replay into records. Suggested non-isolated calibration mode. FASTDEC: demote lift vs 69% base rate not shown; verdicts
should use day x side-demeaned R.
**Learned**
- Replay engines built for "isolation" can't be calibrated against live without a mirror mode; calibrate first, isolate after.
- Verdict precision must be read against the base rate of the target, not against 50%.
**Next**
- GAP-U re-break results tonight; REGSW-2; RCOMPASS v2; FWDREP mirror-mode calibration if built.

## Run 28 — 2026-11-11 12:44 ET (reps priority audits: FWDCAL, REPS1)
**State:** Lead made live reps P1; I audit all three items vs rule 21. Observer: no demote rule beats base rate; information
comes from sessions (ICC ~0.19, a session ~5 trades). Scout REPS1: Gen starved by account -R halt / buying power; low-rep by borrow.
**Did:** FWDCAL: pick delay on a separate window, per-day config snapshots, buying-power skips separate, gap by exit kind.
REPS1: exit-model bias by entry hour, halt-skip what-if concentration, HTB virtual reps unrepresentative.
**Learned**
- "Relative use" of a biased simulator is only safe if the bias is homogeneous across the compared groups — check it.
- Calibrations that pick a free parameter (delay) on the audit sample are tuned audits.
**Next**
- FWDCAL audit table tonight; GAP-U re-break; REGSW-2; RCOMPASS v2.

## Run 29 — 2026-11-11 14:41 ET (promotion multiplicity under 'more setups live')
**State:** all my FWDCAL/REPS1 points adopted. Lead: setup-day is the unit. REPS1b: more setups live is the only lever that
scales; halt what-if unproven (2 days), buying power +0.13R t 1.7.
**Did:** simulated promotion luck at live noise: 11% of zero-edge setups flagged after 20 sessions; +0.10R edges ~40%.
Proposed On Deck as a fresh-sample confirmation stage (or a K-scaled bar) and showing K in promotion suggestions.
**Learned**
- Scaling the number of candidates without scaling the bar raises false promotions linearly; two-stage confirmation is the
  cheap fix and fits the owner's tier structure.
**Next**
- FWDCAL audit tonight; GAP-U re-break; REGSW-2; RCOMPASS v2; owner memo check.

## Run 30 — 2026-11-11 16:41 ET (GAP-U settled; REGSW-2 counter-state observation; self-correction)
**State:** GAP-U fails the shared-day null (my run-26 call confirmed); REGSW-2 0/4, but 'against the market state' entries do
better on the winning short base (t -2.3..-3.4, not pre-registered). FAMC session 1: 2 events. Owner memo shipped.
**Did:** asked to label/stop the GAP-U shadow; REGSW-2 challenge (ex-market over each leg's hold; full-base contrast; TRAIN
in-sample); corrected my two-stage claim (real +0.10R edges pass both stages ~16%, ~40 sessions).
**Learned**
- Correct my own overstatements publicly and quickly; precision gains have a recall price — state both.
**Next**
- FWDCAL rule-21 table tonight; REGSW-2 ex-market follow-up; RCOMPASS v2 result.

## Run 31 — 2026-11-11 18:42 ET (PROMO2 middle option simulation; on/off thread closure)
**State:** PR #184 merged (memo, PROMO2 decision, GAP-U re-test). RCOMPASS v2 0/3. REGSW-2 counter-state = ~70% SPY
reverting to its open (book-wide), residual below bar.
**Did:** simulated stage-2 options: P>=0.80 -> zero-edge 2.4%, +0.10R 22%, precision 51% (vs strict 1.1% / 15% / 60%;
one stage 10.7% / 40% / 29%). Recommended closing the market-state on/off thread.
**Next**
- FWDCAL rule-21 result; FAMC nightly; any owner reply on PROMO2.

## Run 32 — 2026-11-11 20:41 ET (FWDCAL code check before its result)
**State:** on/off thread closed (Lead). PROMO2 middle option to owner. FAMC session 2 (CTVA, ENS, FNV); calendar health 2/2.
**Did:** read run_fwdcal.sh / mirror.py: protocol right; rule21 flag uses a 5-min match window, rule 21 demands the same
entry minute -> score on exact minute; add n and CI; label a 2-session pass as provisional.
**Learned**
- Re-read the rule's exact words against the implemented check; tolerances creep in ("within 5 min").
**Next**
- FWDCAL result; NEWSMID if Lead runs it; REPS3 on 11-18.

## Run 33 — 2026-11-11 22:43 ET (FWDCAL fails rule 21; decision-bar matching view)
**State:** FWDCAL fails on exact minute (ALL 0.386) and 5-min (0.694). Matched trades priced right (+0.006R); the gap is
WHICH trades (spread quotes 32%, caps cascade 34%, no-signal 35%). Observer: exact-minute ceiling set by broker latency.
UNRATED14 ~7 setup-days/week.
**Did:** supported decision-bar matching as rule 21's intent with guards (R gap carries latency; fresh sessions; owner DECISION).
Acknowledged the exit-model hypothesis (mine and Scout's) was wrong.
**Learned**
- A "match" metric can be capped by an unmodelled delay (broker latency); measure the ceiling before setting a 95% bar.
- My exit-model guess was wrong: decompose before guessing (Builder's per-cause table settled it).
**Next**
- NEWSMID result 11-12; FAMC session 2; FWDCAL fresh decision-bar audit 11-12..11-13 if adopted.

## Run 34 — 2026-11-12 00:41 ET (journal meta parse check)
**State:** RULE21-DB to owner; FWDCAL next: replay logged spread quotes. FILLCOST: latency costs ~nothing.
**Did:** verified Scout's meta suffix: naive parse fails 15-51% of trades, and the failures are winners (+0.5..+0.9R).
Scanned scripts (guild + main repo): all split on ';' first. Checklist item 33.
**Learned**
- Parse-error drops can be outcome-selected; always measure what the dropped rows look like.
**Next**
- NEWSMID result after 11-12 close; FAMC session 2; fresh decision-bar audit if the owner adopts RULE21-DB.

## Run 35 — 2026-11-12 02:42 ET (FWDCAL quote lever; latch knife edge; ICCSET)
**State:** FWDCAL with live-logged quotes: 5-min match 0.869 (diagnostic window); next lever the -R halt / latch timing.
Graveyard latch = two stop-outs on a knife edge. Gen halt rule 120R -> 300R from 11-12.
**Did:** challenged calibration leaking live inputs (logged quotes, latch minute): audit must split live-quote vs pool-priced
trades, rule 21 must hold on the pool subset for non-live setups.
**Learned**
- Calibrating a simulator with live inputs only proves fidelity where live inputs exist; audit the input-free subset.
**Next**
- Fresh FWDCAL audit 11-12..11-13 (split by quote source); NEWSMID tonight; FAMC session 2.

## Run 36 — 2026-11-12 04:41 ET (stop-slip model; sim buying power)
**State:** FWDCAL halts understood: sim broker never rejects (Gen 101 extra trades), Graveyard latch on knife edge; live
stops fill +0.045R worse (Observer fit slip = 0.012 + 0.34 spread/stop). ICCSET-2 shrunk table ready.
**Did:** challenged the symmetric |slip| trim (drops adverse gap-throughs); split by side of original stop; refit + tail;
sell-off-month caveat. Checklist 34. Endorsed buying-power cap with a reject-count check.
**Next**
- Fresh FWDCAL audit 11-12..11-13 (no live-minute feeds, live-quote vs pool split); NEWSMID; FAMC.

## Run 37 — 2026-11-12 06:41 ET (stop-slip plug-in check; ICCSET-3)
**State:** buying-power cap rejected by its own check; stop-slip refit with side split: mean +0.059R, p99 0.38, slope varies
by day (0.34-0.74). ICCSET-3 groups explain 40% of ICC variance.
**Did:** caught Builder's planned |slip| > 0.3 symmetric drop in the validation check (same tail problem); asked Scout
whether ICC groups were fixed before computing ICCs, plus CIs per group.
**Next**
- Fresh FWDCAL audit 11-12..11-13; NEWSMID result; FAMC.

## Run 38 — 2026-11-13 23:03 ET (board quiet since 11-12 07:50)
**State:** stop-slip replacement rejected by quintile check (sim already right at tight spreads); Builder proposes max-form.
Scout withdrew the ICC group prior after a time holdout (-2%). Fresh FWDCAL audit, NEWSMID look, FAMC 2-4 not posted.
**Did:** approved max-form as one look judged only on the unused 11-10..11-11 holdout (q4-q5 better, q1-q3 not worse);
reminded that the fresh 11-12..11-13 window must be scored once with an engine frozen before opening it.
**Next**
- Whatever posts next; keep auditing FWDCAL / NEWSMID / FAMC when results land.

## Run 39 — 2026-11-14 00:41 ET (catch-up after the quiet day)
**State:** NEWSMID closed (excess -0.024 ATR; headlines trail the move in 46%). FAMC: session 2 raw +0.034R; 11-13 and
11-16 unscorable by the frozen pre-open rule. Observer: up-day null (index sign-so-far, ~0 continuation).
**Did:** endorsed up-day scoring standard (+3x ETF in its own price and costs); FAMC unscorable-count beside K; health line
measures precision only, recall needs a periodic check. Checklist 35-36.
**Next**
- Fresh FWDCAL audit when run; FAMC nightly; any up-day rule plans (score vs sign-so-far).
