# Decision queue for Monday 11-30 (stacked by expected impact)

Educational only — not financial advice. Written 2026-11-28 ~01:30 ET by the exploration session (decisions key). **Nothing here is applied.** Every "prepared work" item is a draft under `exploration/sandbox/decisions/<code>/`. A change happens only after the owner's reply, outside market hours, with tests, a ledger entry and (for setup moves) `docs/live/assignments.json` regenerated in the same commit.

**Where the numbers come from.** Live journals, 10-23..11-27 (25 sessions), run 1, R after LR8 costs. The bench is the 2-year minute engine with LIVE-L costs. The locked holdout (2024-11-01..2025-02-28) was never read. About **9,656 configurations** have been tried so far: about 9,363 before tonight, about 280 from tonight's tracks and reviewers, 4 descriptive lineup cuts in this file, and 6 from cycle 2 (GAPSWITCH 5, RW-TGT125 1).

**Rule changes inside the 10-23..11-27 window** (ledger; they affect every number below; this is a selection: the ledger has 23 distinct effective dates in the window):
- 10-23: ST-A (no per-setup stop in the arena).
- 10-28: Primary size about $4k.
- 10-29: −2R latch on closed R.
- 10-30: L3 re-promoted to Primary.
- 11-11: TEAM-6.
- 11-12: LR8 costs, LR3, the 300R arena halt and the half-day flatten.
- 11-17: TSZ1 (half lots, 2x slots in testing) and giveback/SPY exits (on the WB4 workbench copies in testing only; the Primary parents kept t1s1 exits, per rw_target).
- 11-19: Epoch 1 and C3-EXIT100.
- 11-20: stop rounding, FOOTRACE-EXIT, and MF2/MF4 out of Primary.
- 11-21: cost-basis fix.
- 11-23: ST7 out, BRAKE-BURST, Remedy-Q.
- 11-27: GYH, ROT-B3, GEN seed.
- **Next:** 11-30 brings ETF-STOP50/AV50 for NM-ETF and the 11-27 Friday-review arena moves.

## How to answer (one line, copy and edit)

```
LATCH-OPEN monday | L3-OUT out monday | B8 shadow monday | TAGS2 go | ARENA-LATCH-F yes | FROZEN-BLOCKS yes | REPORTS go | HS-SCALE shock-only friday | GOAL-STAGES yes | T1X2 yes | PRIM-ADD3 no | ODP2/ODB3 as recommended | CRYPTO park
```
Replace `monday` with `friday` to wait for the 12-04 epoch; for the softer latch write `LATCH-OPEN -3R monday` (or `friday`). Any item left out stays open. `ODP2/ODB3 as recommended` means the 5 yes / 3 wait split in D12. `ARENA-LATCH-F yes` also grants the time-boxed playing-time exception described in D5.

## Dry-run status (cycle 2, 02:00 ET): every draft applies and passes the tests

- Each draft below was applied to a throwaway copy of `claude/intraday-trading-system-witis4` at f5a2626587 and the full `pytest -q` was run. Nothing was committed there. Details: [DRYRUN.md](sandbox/decisions/DRYRUN.md).
- **As first written, none applied:** the `config.diff` files were not real patches, and each draft broke 1-12 tests. Both are fixed. **Apply with `sandbox/decisions/apply_draft.py`, not with `git apply`.** The script stops if any edit does not match exactly once, fills in the ledger line, and makes the matching test edits.
- **Result after the fixes:** each of LATCH-OPEN, L3-OUT, B8-SHADOW, ARENA-LATCH-F and HS-SCALE, the Monday combo (LATCH-OPEN + L3-OUT + B8) and an all-five stack pass (baseline 1,076 passed, 1 skipped). One timing test, `test_poll_log`, failed twice under machine load and passed when re-run alone.
- **Not checked:** `python -m mcf.research.ledger check` (needs the bar cache) and live behaviour.
- **Exact steps** (on a branch cut from witis4, outside 09:30-16:00 ET):
  ```
  python exploration/sandbox/decisions/apply_draft.py --repo <checkout> --code COMBO --when monday --date <reply date> --where <chat|inbox>
  python -m mcf.report.assignments      # same commit as the L3 move
  python -m mcf.research.ledger check && pytest -q
  ```
  For a single item use `--code LATCH-OPEN [--variant 3R] | L3-OUT | B8-SHADOW | ARENA-LATCH-F | HS-SCALE`. `--when friday` makes it effective 12-07.

## Summary table

| # | Code | Question | Recommendation | Weekly-R effect on Primary (honest) | Needs |
|---|---|---|---|---|---|
| D1 | **LATCH-OPEN** (tapped *friday*) | Latch counts open R too | **Yes, apply for Monday 11-30** (override) | +1 to +5 R/wk on today's losing book, all from trading less. Main value: an 11-25-type day goes from −40R to about −8R | Owner override of the Friday rule |
| D2 | **L3-OUT** (tapped *out*) | Move L3 to On Deck | **Yes, out, for Monday 11-30** (override) | Live total about unchanged (+0.6 R/wk). Day swings −42%, worst-5 −108 → −69R. Bench +1.8 to +3.9 R/wk, size effect | Override of PRIME-RULES probation and the Friday rule |
| D3 | **B8-SHADOW** (tapped *shadow*) | Log the net-beta cap | **Yes, from Monday** (log only) | 0 (log) | Your yes; arguably not a rule change |
| D4 | TAGS2 (new) | Freeze 7 would-skip rules from tonight and score once at 20 sessions | **Go** | 0 now; it can only produce candidates | One word |
| D5 | ARENA-LATCH-F (new) | Closed −2R latch in Testing F for one 2-week block | **Yes** | 0 on Primary. Testing F: tail cut, R effect about 0 outside squeeze days | Testing config change, by Sunday |
| D6 | FROZEN-BLOCKS (new, structure) | No rule changes inside 2-week blocks in testing accounts | **Yes** | 0 direct; faster, cleaner verdicts | Process rule |
| D7 | REPORTS (new) | PAIRED-CARD, LONG-SURVIVORS, weekly Stage-1 scorecard, review rules | **Go** | 0 direct | One word |
| D8 | HS-SCALE (open) | SHOCK-V failsafe only | **shock-only, at 12-04** | 0 (glitch failsafe) | Your yes |
| D9 | GY-SHADOW + TWIN (new, structure) | Graveyard to shadow-only; freed account becomes a Primary twin | **Discuss; earliest 12-04** | 0 direct; maybe 0 to +3 R/wk after 4-6 weeks | Exception to "promotion = move" |
| D10 | PRIM-EXPOSURE (heads-up for 12-04) | Also move RW5 out? | **Decide 12-04 on one more week of data** | +1 to +4 R/wk, size effect | Nothing now |
| D11 | GOAL-STAGES (new) | Measure Stage-1 loss bars now, green weeks and days once the edge is positive | **Yes** | 0 (it changes what "progress" means) | Your yes |
| D12 | Routine cards | T1X2, PRIM-ADD3, ODP2/ODB3 x7, CRYPTO, COMPASS-HALF | See D12 | 0 | One line each |
| D13 | RW-TGT125 | 1.25x target for RW3/RW5 | **None: dropped** (failed its LIVE-L re-check) | about 0 | Nothing |

---

## D1. LATCH-OPEN: make the −2R per-setup latch count open losses too
**You tapped:** `friday`. **Question now:** apply for **Monday 11-30** (override the Friday-epoch rule), or at the **12-04** Friday window?

**Recommendation: Monday 11-30.**
- Monday is already an epoch start. AV50 is "epoch 3", effective 11-30. So applying it now does not split an epoch. It only skips the "decided at the Friday close" step, and the reason that step was missed is that you wanted to ask questions first.
- Waiting a week has a cost. Before LATCH-OPEN, the bench had about 11 days a year at −20R or worse (33 in 2.9 years), roughly a 20% chance in any given week. With it, about 3 a year.

**Options and prepared work** (identical change, different date; `sandbox/decisions/LATCH-OPEN/`):

| Option | What is done | Files |
|---|---|---|
| **monday** | Sat/Sun: `risk.latch_counts_open: true` in config/default.yaml (Primary only). Run the Friday-switch tests, then full pytest, flipping the default-off test expectation for primary. Ledger effective 2026-11-30. Card answered. | `apply_draft.py --code LATCH-OPEN --when monday` (ledger `ledger_monday_1130.jsonl`; `config.diff` is the readable view) |
| **friday** (12-04) | Same change after the 12-04 close, effective 12-07 | `apply_draft.py --code LATCH-OPEN --when friday` |
| **-3R** | Also `latch_open_r: 3`: about a third of the cost, but a weaker 11-25 cut (−37 → −23R on the partial-day base; never re-scored on the full day) | add `--variant 3R` (3 more latch tests edited; passes) |
| no | Nothing | — |

**Questions you are likely to ask, answered in advance:**
1. *Would it have saved 11-25?* Mostly. On the full-day minute replay, −40.1R becomes −8.3R (the journal day was −42.3R). Tonight's loss anatomy shows why the current latch could not act: Primary's L3 had **30 lots open** before the first stop cluster (12:00-13:00), so closed R was still above −2R while open R was far below it.
2. *Does it sell anything?* No. It only blocks **new** entries for that setup for the rest of the day. Open lots keep their own stops and targets.
3. *What does it cost on good days?* About 20% fewer lots. It trims recovery days: 11-12 L3 goes from +31R to about +1R. On a book earning +0.10R per lot that would be about −87R a year. On today's book (−0.156R per lot) the lots it skips are losing lots on average.
4. *Is it an edge?* No, it is insurance. (Playing time: it extends the Primary latch you approved on 10-29 and blocks about 20% of Primary lots within the day. It is a loss guard, not a starvation fix, but see the reviewer notes at the end.) On CHECK it scores the same as a plain size cut (E = 1.00). Tonight's testing-account replay agrees: once a day has gone bad, cutting *any* lots that day does as well as the latch's choice (shorts_autopsy reviewer). What it buys is acting **during** the day, before the whole basket is on.
5. *If L3 goes out too, is it still worth it?* Yes, but it is worth less. RW3 and RW5 build the same baskets: 11-10 and 11-11 had 35-39 lots and about −24R each day. NM-ETF had 12 lots open at once on 11-20. Not re-replayed tonight on the 3-setup roster.
6. *What if marks fail?* That setup falls back to closed R for that check, and it is logged (`latch_open_fallbacks`). A restart re-derives the latch from marks.
7. *Is anything else changing Monday that would blur the read?* AV50 changes NM-ETF exits only. LATCH-OPEN blocks show their own skip reason (`setup daily loss limit (open)`), so the two can be told apart in the journal.
8. *Contrary evidence?* rules_1122 found that a closed latch for *every* setup was **−68R worse than a random trim** on live trades to 11-20. In the gap-down family it cost −104R before 11-25, because those setups often recover after a −2R start. LATCH-OPEN gives up the same recoveries. That is the price of the tail cut.

**Evidence:** [neveragain_1125](../research/neveragain_1125/REPORT.md), [loss_anatomy](findings/loss_anatomy.md) (§1, P3, and reviewer: "holds as a mechanism"), [regime_filters](findings/regime_filters.md) (F2a: on Primary the per-setup latch already does what a book budget would), [shorts_autopsy reviewer](findings/shorts_autopsy.md) (latch = day-level cut). Reviewer status: prior card reviewed by inspector_1127. Tonight's tracks support the mechanism and add no counter-evidence beyond Q8.

## D2. L3-OUT: move Gap-Down Recovery Fade (L3-gap-slope-fromopen-FD) from Primary to On Deck
**You tapped:** `out`. **Question now:** apply for **Monday 11-30** (override), or at **12-04**?

**Recommendation: out, Monday 11-30.**
- The PRIME-RULES probation clock has nearly run out: about 20 Primary sessions by 11-30 (the card counted 18 to 11-25).
- So "probation" would bring the same decision at 12-04 anyway, with one more week of the largest basket generator in Primary.

**What Primary looks like with each lineup** (live Primary lots, 10-23..11-27, LR8; [roster_options_out.txt](sandbox/decisions/roster_options_out.txt); a removal on live lots is a pure exposure cut):

| Lineup | Lots | Total R | Day sd | Red days | Worst day | Worst-5 | Total w/o best day | Green weeks |
|---|---|---|---|---|---|---|---|---|
| As is (L3, RW3, RW5, NM-ETF) | 576 | −30.1 | 15.8 | 14/25 | −42.3 | −108.1 | −70.8 | 2/6 |
| **L3 out** | 361 | −27.0 | **9.1** | 14/25 | **−25.7** | **−68.7** | −45.9 | 2/6 |
| L3 + RW5 out (see D10) | 201 | −15.7 | 5.5 | 14/25 | −10.2 | −39.5 | −31.7 | 1/6 |

**Options and prepared work** (`sandbox/decisions/L3-OUT/`):

| Option | What is done | Files |
|---|---|---|
| **out monday** | Sat/Sun:<br>• config/default.yaml: L3 `enabled: false`, removed from Primary `setup_order`<br>• config/account_testing.yaml (On Deck): `enabled: true`, appended to `setup_order`<br>• `python -m mcf.report.assignments`, ledger `kind: move` naming your override of probation, `ledger check`, pytest<br>Merged outside 09:30-16:00 (setup-freeze) | `apply_draft.py --code L3-OUT` (ledger `ledger_out.jsonl` now has the protected-list fields; 2 test edits for the 4 → 3 Primary count and Remedy-Q) |
| **out friday** | Same after the 12-04 close, effective 12-07 | same |
| probation | No config change. Ledger note: re-decided at the 12-04 review or at a −10R Primary record | `ledger_probation.jsonl` |
| no | Nothing | — |

**Questions you are likely to ask:**
1. *Isn't L3 positive across accounts?* +0.086R per lot over 453 lots, but 10-20 is 81% of it (`1 day`). Without its best day it is +0.019. In Primary it is −0.209R per lot without its best day (best day 11-12, +31R on 52 lots). On the bench it loses on both splits (−0.100 / −0.126R per lot).
2. *Why L3 and not RW3 or RW5?*
   - Removing any one short helps about equally on the bench (rwout: no short is special).
   - L3 is singled out by its live record without its best day (−0.204 vs −0.037 / −0.057).
   - Window note: −0.204 / −0.037 / −0.057 are the Primary records since each setup's first Primary session (231 / 199 / 202 lots; RW3/RW5 include their 10-22 best day). On the 10-23..11-27 window used elsewhere in this file they are −0.209 / −0.155 / −0.144 (PRIOR_RESEARCH): L3 is still the worst, but by less.
   - L3 is also the **basket generator**: about 13 lots a session in Primary (215 lots in 17 sessions) and 35 lots on 11-25. Lots per day is the one setup trait that predicts next week's worst day (metrics track, rho −0.36, though the reviewer found this is largely mechanical: more lots, bigger swings).
3. *What does Primary lose?* L3's windfall days: 11-12 (+31.0R), 11-16 (+16.4R), 11-20 (+6.0R), 11-10 (+5.8R). The table shows total R is about unchanged without it. What drops is the swing.
4. *Does L3 keep playing?* Yes. In On Deck it gets full reps under On Deck rules, and it can return under C3-BAR2 plus the PRIME-RULES entry tests.
   - **Risk to flag:** On Deck has no per-setup stop and only a 300R account backstop. On 11-25 On Deck lost −391R, and seven arena L3 copies lost −1,037R between them.
   - Moving L3 adds an eighth L3 copy to the arena. That is paper risk only, but it enlarges the arena tail on the next squeeze day. D5 (a latch in Testing F only, not On Deck where L3 would land) and D6 (a freeze, not a loss guard) do not cover this; see [critic](findings/critic.md).
5. *Side effects on running tests?*
   - The L3 leash shadow (K11/K12, Primary basis, currently hurting: dK11 −15.5R, dK12 −28.0R) loses its Primary basis.
   - GAP-U and the regime-switch shadows should be reported on the new roster from 11-30.
   - HS-SCALE's N becomes 3. Keep the 16R / 24R floors: they are more conservative than the unscored 12R / 18R that N = 3 would give.

**Evidence:** [primshorts_1126](../research/primshorts_1126/REPORT.md), rwout_1127, [shorts_autopsy](findings/shorts_autopsy.md) §4 (verdict "restrict"), [metrics](findings/metrics.md) (lots per day persists), [loss_anatomy](findings/loss_anatomy.md) §1. Reviewer status: the shorts reviewer calls "L3 restrict" reasonable. Both the live (+0.063) and Primary (−0.9 R/wk) records carry the `1 day` tag, so the bench should drive the decision, which it does.

## D3. B8-SHADOW: log the net-beta cap (journal tag only)
**You tapped:** `shadow`. **Recommendation:** start **Monday 11-30**.
- It changes no trade, slot, latch or halt, so it is a log, not a Primary trading rule.
- If you consider any Primary config edit to be a rule change, choose `friday`.

| Option | What is done | Files |
|---|---|---|
| **shadow monday** | `risk.netbeta_shadow.enabled: true` (Primary, On Deck, Testing A), `betas_path: null` (beta 1.0 for every symbol). Ledger, tests | `apply_draft.py --code B8-SHADOW` (ledger line now drafted) |
| shadow friday | Same at 12-04, effective 12-07 | same |
| no | Nothing | — |

**Likely questions:**
- *Why log it?* The midday-flip day (11-10, 11-25) is Primary's worst failure type. On top of LATCH-OPEN, the bench shows worst-5 +47% on CHECK and +22% on T2.
- *Why not enforce it?* It would fire on about 185 of 252 days, which makes it a large size cut. Live, for today's trio, it reads negative (−26.6R). Tonight's metrics track (P3) adds a standing rule: a "red days" lever is adopted only if it beats an exposure-matched size cut. Enforcement comes back only if B8 beats that cut and a size-matched random block on CHECK and T2, plus 20 sessions of tags.
- *What is the risk?* A new code path in the live runner, already covered by tests. Beta 1.0 is crude; a shrunk-beta JSON can follow.

## D4. TAGS2 (new): freeze tonight's surviving shadow ideas now, score once after 20 sessions
**Recommendation: go.** It is the cheapest way to turn tonight's in-sample hints into an honest forward test. Freezing the rules **before** 11-30 data exists is what makes them a forward test.

- **What:** seven would-skip rules computed from the journals after each close, using the TAGS1 pattern (approved 11-18). No order, slot, latch or halt change.
- **Rules:**
  - BASKET5X: lots 6 and later per setup-day.
  - GAPU_GD25 / GAPU_GD50: gap-down shorts on SPY gap-up days.
  - PLOCK25: the profit lock.
  - SIDE20 and BS30: book budgets on top of a latch.
  - LONGF1: long-strength tag, tested against wide-stop-only lots.
- **Each rule carries its reviewer-corrected control:** a day-block random cut for BASKET5X; a same-day random switch for GAPU; the first-N path control for PLOCK25; same-day neutral for SIDE20/BS30 (no TT); F5 for LONGF1.
- **Window:** 11-30..12-29 (20 sessions). 12-24 is a half day and is reported separately. Bar: day-clustered t ≥ 2. A pass is a candidate for a pre-registered bench test, never an adoption.
- **Prepared work:** `sandbox/decisions/TAGS2/rules_draft.json`. On "go", copy it to `research/tags2/rules.json` with `frozen` set, plus a scorer modelled on `research/tags1/score.py`. Research-only commit, outside the trading path.
- **Expected effect:** 0 R now. Prior chance that any rule clears both its control and t 2: about 10-20% (tonight's reviewers rated all of them low). Cycle-2 update: GAPSWITCH found the SPY gap-up short switch no better than random day-skips on the bench (0/5 configs, p 0.42-0.999; [gapswitch](findings/gapswitch.md)), so the prior for GAPU_GD25 / GAPU_GD50 is lower still.

## D5. ARENA-LATCH-F (new): closed −2R per-setup latch in Testing F for one frozen 2-week block
**Recommendation: yes**, as a tail test in the arena. Primary is untouched.

- **Why:**
  - On 11-25 the arena lost −1,160R, and the accounts had no per-setup stop.
  - Live replay (in-sample): Testing F's worst day goes from −261R to −63R.
  - You approved a "latch for every setup" study on 11-22. This runs it forward in one account.
- **Honest R:**
  - The live replay is +36 R/wk for Testing F, nearly all from 11-25.
  - rules_1122 found the latch was a size trim (−68R vs random) to 11-20.
  - So expect **about 0 R outside squeeze days**, plus a real tail cut.
- **Experiment:**
  - Account: Testing F. Blocked signals are still recorded by the what-if run (run_id 2), but only as bar-simulated rows without live fills, so live reps on latch days are lost.
  - Baseline: the same account with latched lots added back from what-if, costed with LIVE-L.
  - Controls: (a) a same-account-day random cut of equal size; (b) a constant size cut on latch-fire days.
  - Duration: 11-30..12-11 if approved by Sunday, else 12-07..12-18.
  - Success: worst-5 days improve ≥ 40%; total R is no worse than the same-day random cut; per-setup better/worse counts reported (remedy rule).
- **Conflict to weigh (explicit):** your playing-time rule (11-03) says starvation is fixed by session rotation, "never by in-session throttling in Primary/Testing". A per-setup latch that stops a setup's entries for the rest of the day **is** in-session throttling in a testing account. It is a loss guard, not a starvation fix, but it still takes reps from setups that start the day badly. So `yes` here means a **time-boxed exception** to that rule for Testing F only, 11-30..12-11; under the 11-19 conflict-check rule this needs your explicit yes.
- **Prepared work:** `apply_draft.py --code ARENA-LATCH-F` sets `account.max_setup_daily_loss_r: null → 2.0` in config/account_testingf.yaml. It reaches all 22 Testing F setups and works on raw R. The ledger line is drafted and names PROT-21 ("No latch in Testing"), so your yes must be explicit. One test edit is included, and the dry run passed. The scoring script still has to be written before the block starts.

## D6. FROZEN-BLOCKS (new, account structure / process)
**Recommendation: yes.**
- **The rule:** Testing A-F and On Deck run in 2-week blocks with no rule changes inside a block. Setup moves happen only at the Friday epoch. Each account carries at most one pre-registered question per block. Bug fixes are exempt.
- **Why:**
  - There were 23 distinct rule-change dates in 25 sessions, so no testing comparison is clean.
  - Live setup records are 3-12% signal (dev_tactics E2). Paired, frozen designs read a +0.05R/trade change about 3x faster.
- **Conflicts to weigh:** (a) your 11-20 rule "No freeze, but weigh every change heavily" (OUT-EPOCH). This is a freeze inside testing blocks, so it needs your explicit yes as an amendment. (b) The playing-time session rotation (ROT blocks in Testing A-F, about every 4 sessions) must stay exempt, or low-activity setups would be starved for two weeks. The draft should say so before it is applied.
- **Prepared work:** `sandbox/decisions/FROZEN-BLOCKS/RULE_DRAFT.md` (proposed RESEARCH_RULES text, ledger `kind: process`). No config change.
- **First block:** 11-30..12-11, with D5 as Testing F's question.

## D7. REPORTS (new): four research-only reports, one "go"
Each reads journals after the close. None touches the trading path. Recommendation: **go**.
1. **PAIRED-CARD** (`sandbox/decisions/PAIRED-CARD/PLAN.md`):
   - Paired day-clustered scores of the pending cards on all ~1,150 live trades a session: LATCH-OPEN (skipped lots, if it is live), RW 1.25x target, L3 first-lot-only, SPREADFLOOR.
   - Skip rules are compared same day, same side, on net R.
   - Reported once on 12-11.
   - Cycle-2 update: the RW 1.25x target failed its re-check under LIVE-L costs on the bench (CHECK +0.007, T2 +0.003 R/lot, both below the bar; the live gain is in-sample only: +0.001 R/trade on the 97 trades after the study window; [rw_target](findings/rw_target.md)). Keep it on the scoreboard as a descriptive read only; it is not a card.
2. **LONG-SURVIVORS** ([long_edge](findings/long_edge.md) P1):
   - GEN-261020-09 and CWT14-orl-p10-long-WB5 scored forward 11-30..12-28.
   - Pass needs: avg R without best day > +0.05, best-day share < 35%, day t ≥ 2, above the random p95.
   - The scoreboard follows the setup if ODB3-G102009 moves it.
3. **Weekly Stage-1 scorecard** ([metrics](findings/metrics.md) P1): worst day, 20-session floor, median day, R per lot with day t, lots per day and in-day correlation. Red days and green weeks are shown but not judged while R per lot ≤ 0.
4. **Review rules** (metrics P3, outside P2/P3):
   - (a) Any red-day lever is shown next to an exposure-matched size cut.
   - (b) A setup's own last 5-10 sessions are never a gate by themselves; the reason is "no better than random", not "worse than random".
   - (c) Size stays at the minimum until a setup has day t ≥ 2 net of costs over 20 sessions.

## D8. HS-SCALE (open card): SHOCK-V failsafe only
**Recommendation: `shock-only` at the 12-04 epoch.** It is a glitch failsafe, not an R lever, so there is no reason to override the Friday rule for it.
- `apply_draft.py --code HS-SCALE --when friday`: `shock_v.enabled: true`, floors 16R / 24R. The scaled halt stays off. The ledger line is drafted and the dry run passed.
- With L3 out, N = 3. Keep 16R / 24R: fewer false fires; the lower floors are not scored.
- `build-flatten` stays a separate build.

## D9. GY-SHADOW + TWIN (new, account structure; earliest 12-04, effective 12-07)
**Recommendation: discuss.** Approve the direction now, build for 12-04.
- **(1) Graveyard to shadow-only.** Keep 1-2 leaders live as a cost sample. Correct the shadow's −0.047R per trade bias before any foot race.
- **(2) The freed paper account becomes TWIN:** an exact copy of Primary plus **one** candidate change per block, read against Primary as a real-fill paired test.
  - First candidate: whichever of LATCH-OPEN / L3-OUT you did *not* apply. (The RW 1.25x target is no longer a candidate: it failed the cycle-2 re-check.)
- **Needs** your explicit exception to "promotion = move" (TWIN is a copy) and new GY-LIFE / GY-FOOTRACE wording.
- **Speed:** reviewer-corrected, about 4-8 sessions to read +0.10R per trade.
- **Prepared work:** `sandbox/decisions/GY-SHADOW-TWIN/OUTLINE.md`, which lists the files, the order and the controls. The full build is its own PR outside market hours.

## D10. PRIM-EXPOSURE (heads-up for 12-04, not for Monday)
**Question for 12-04:** move RW5 out of Primary too?
- **For:**
  - It is the worst live Primary short (−2.3 R/wk) and the worst on T2 (−0.182R per lot).
  - It loses on SPY gap-up days: −21.4R.
  - Removing it cuts day sd from 9.1 to 5.5 on top of L3-out.
- **Against:**
  - It is a size cut; no short is special (rwout).
  - It cut green weeks from 2/6 to 1/6 in the live table (one week's difference in 6, so this is noise either way).
  - It was positive on flat-open days (+21.1R).
- **Recommendation:** decide at 12-04 with the first week of LATCH-OPEN / L3-OUT data.
- **Prepared work:** `sandbox/decisions/PRIM-EXPOSURE/config.diff` (outline mirroring L3-OUT).

## D11. GOAL-STAGES (new): what counts as progress while the edge is negative
**Recommendation: yes.**

**The evidence** ([metrics](findings/metrics.md) §4; the reviewer reproduced it exactly):
- At Primary's lot correlation (0.185) and 38 lots a day, being red on no more than 1 day in 20 needs **+0.67R per lot**.
- Even at correlation 0.03 and 100 lots a day it needs about +0.29R per lot (recomputed: 1.645 x 0.89 x sqrt(3.97/100) = 0.29). That is about 2.5x the best live edge (about +0.01 to +0.12R per lot without the best day); the +0.67 at Primary's numbers is about 6x.
- Today: −0.156R per lot, 68% red days, 1 green week in 6.

| Edge per lot | Red days | Red weeks |
|---|---|---|
| 0 | 50% | 50% |
| +0.10 | 40% | 29% |
| +0.15 | 35% | 20% |

**Proposed stages:**
- **Stage 1 (now):** no day worse than −20R; 20-session floor ≥ −40R; median day > −2R; R per lot trending up.
- **Stage 2 (once R per lot > +0.05 with day t > 2 over 20 sessions):** green weeks ≥ 3 of 5, then red days ≤ 2.5 a week.

**Why this order:** "Every day a winning day in some way" (charter) can be literally true at Stage 1, as a day with no −20R loss and at least one measured verdict. "Green every day" in R is not reachable at any edge this system has shown. Green **weeks** need a positive per-lot edge, and none of tonight's 7 tracks found one after costs.

**Prepared work:** none to apply. If yes, the weekly review uses the D7.3 scorecard.

## D12. Routine open cards (one line each; `sandbox/decisions/ROUTINE/REPLIES.md`)

| Card | Recommendation | Why (tonight's lens) |
|---|---|---|
| T1X2 | **yes** | Phantom 12 SOXX in On Deck since 11-25 blocks On Deck's SOXX entries and skews its dollars. Housekeeping only. |
| PRIM-ADD3 | **no** | All 4 candidates are negative without their best day. Tonight: promotions averaged +0.190 before and −0.197 in Primary (dev_tactics). |
| ODP2-G261027-01, ODB3-G102306, -G102607, -G102009, -G102906 | **yes** (On Deck is for reps) | Positive without best day, but all `1 day`. Records are 3-12% signal, so this is reps, not proof. |
| ODB3-G102205, -G102104, -RWR4 | **wait** | Negative without their best day. |
| CRYPTO-SCOPE | **park** | Outside the intraday charter. 15-47 trades, t ≤ 2.22 vs a 3.82 bar. |
| COMPASS-HALF | **no action from this session** | Named as new in the 11-27 brief but not in docs/live/decisions.json on the default branch. Its card text was not visible here. |

## D13. RW-TGT125 (RW3/RW5 1.25x target): no decision, dropped
- **Verdict:** the cycle-2 re-check failed under LIVE-L costs, so there is no 12-04 decision, config draft or ledger line, as its pre-registration said.
- **Bench:** CHECK +0.007 R/lot (day t 1.47); T2 +0.003 (t 0.42); FIT −0.008.
- **Live:** the +0.04 gain came from the original study window. On the 97 trades from 11-18..11-27 it was +0.001 R/trade.
- **What is left:** a descriptive line on the PAIRED-CARD scoreboard, plus a possible backlog idea (extend the target only on SPY-down days) that must be pre-registered first. Details in [rw_target](findings/rw_target.md).

**Also failed in cycle 2, so not proposed:** the SPY gap-up short-switch day rule (GAPSWITCH). Same-count random day-skips did as well (0 of 5 configs passed; best p 0.42; worst-5 days unchanged). It adds no TAGS2 rule and no new shadow. The existing TAGS2 GAPU_GD25 / GAPU_GD50 tags stay in the frozen set with a lower prior (D4). Details in [gapswitch](findings/gapswitch.md).

## Reviewer notes (cycle 2)

Educational only — not financial advice. Adversarial review of MONDAY_PLAN.md, DECISIONS.md and PROPOSALS.md, 2026-11-28 ~02:00 ET. Read-only on everything outside exploration/; no new configurations scored (count unchanged by this review).

**1. Numbers traced (40 spot-checks; all found or recomputed unless listed under corrections).**
- Primary −147.0R, weekly sum −3.3/−10.1/−33.9/−44.7/+4.1/−59.2 = −147.1, 1 green week of 6, 17/25 red (68%), −0.156R per lot (−147/943): PRIOR_RESEARCH, metrics.
- The roster table (576 lots, −30.1R, sd 15.8, worst −42.3, worst-5 −108.1, w/o best −70.8; L3 out 361 / −27.0 / 9.1 / −25.7 / −68.7 / −45.9; L3+RW5 out 201 / −15.7 / 5.5 / −10.2 / −39.5; green weeks 2/6, 2/6, 1/6; red 14/25) matches `sandbox/decisions/roster_options_out.txt` line for line. Derived: +0.6 R/wk = 3.1R / 5 weeks; sd −42% = 9.1/15.8.
- L3 windfalls 11-12 +31.0, 11-16 +16.4, 11-20 +6.0, 11-10 +5.8; 11-25 35 lots −35.0R (roster_options_out). L3 Primary w/o best day −0.209 = (−3.07 − 31.0)/163 (recomputed).
- L3 all accounts +0.086 / 453 lots / +0.019 w/o best / 81% on 10-20; Primary 231 lots −0.204; RW3 −0.037, RW5 −0.057 (Primary): research/primshorts_1126/rescore.json. Bench L3 CHECK/T2 −0.100 / −0.126 and +0.77 / +0.36 R/session (t 3.4 / 3.7): primshorts REPORT; ×5 = +1.8..+3.9 R/wk.
- 11-25 full day −40.1 → −8.3R: research/squeeze_1125/REPORT.md (neveragain's −37.4 is the partial day); bench ≤ −20R days 33 → 8 in 2.9 years; recovery day 11-12 +31 → +1R; −87R/yr on a +0.10 book (/52 = −1.7 R/wk): neveragain_1125.
- CHECK −3.03 → −2.05 R/day (×5 = +4.9 R/wk): PRIOR_RESEARCH.
- rules_1122: −68.3R vs random trim; gap-down family −103.7R. squeeze_1125: B8 fires 185/252, worst-5 +47% / +22%, live trio −26.6R (RW5 −16.2, L3 −10.3, RW3 −0.1).
- rwout_1127 RW5-out +0.91 / +0.80 R/day. Testing F −261 → −63R, +36 R/wk; On Deck −391 → −49R: shorts_autopsy. Arena 11-25 −1,160R, seven L3 copies −1,037R, worst-5 = 64% of losing-day R, friction about 0.13R per lot: loss_anatomy.
- Green-day maths: +0.67 (N 38, rho 0.185) and +0.29 (N 100, rho 0.03) recomputed from sd_day = s·sqrt(N(1+(N−1)rho)); week-level "30-40% green" recomputed as P(N(−5.4, 20.3) > 0) = 39%.
- 23 distinct ledger effective dates 10-23..11-27 (recounted from research/ledger.jsonl); AV50 is ledger epoch 3, effective 11-30; promotions +0.190 → −0.197; reliability 3-12%; Graveyard shadow bias −0.047 (overall −0.037); dK11 −15.5 / dK12 −28.0; lots/day → worst day rho −0.36.

**2. Corrected in this pass (small edits).**
- D11: "+0.29 is about 6x the best live edge" → about 2.5x (the 6x belongs to +0.67).
- D2 Q2: "19 lots a day" for L3 had no source (19.4 is L3-rsi5hi across accounts) → about 13 a session in Primary (215 / 17). Added the window note: the −0.204 / −0.037 / −0.057 comparison uses each setup's whole Primary record; on 10-23..11-27 it is −0.209 / −0.155 / −0.144, so L3 is worst by less. Added the reviewer caveat that lots/day → worst day is largely mechanical.
- D5 / PROPOSALS #4: "reps are not lost" overstated → what-if rows are bar-simulated, live reps on latch days are lost.
- MONDAY_PLAN: FROZEN-BLOCKS scope said "Testing A-E, Explore 1, Live Lab, Gen"; D6 says Testing A-F + On Deck. Fixed to match D6; Explore 1 / Live Lab / Gen are outside the blocks.
- MONDAY_PLAN step 2: assignments.json must be committed in the same commit as the L3 move (owner 10-20).
- One-line reply: `ODB3 as recommended` did not clearly cover ODP2-G261027-01 → `ODP2/ODB3 as recommended`; D11 (recommended yes) was missing → added `GOAL-STAGES yes`.
- Cycle-2 results folded in: the RW 1.25x target failed its LIVE-L re-check (rw_target), so it is a descriptive read only in PAIRED-CARD and no longer a TWIN candidate; GAPSWITCH failed its random control (0/5), lowering the TAGS2 GAPU prior.
- Config count 9,650 → about 9,656 (cycle 2 added 6). The rule-change list is now labelled as a selection of the 23 dates.

**3. Under-a-minute check.** Each D1-D12 item has one recommendation and one token in the reply line; `monday` / `friday` is the only switch. Remaining ambiguity: `LATCH-OPEN -3R` has no date token in the example (write `LATCH-OPEN -3R monday` or `... friday`).

**4. Owner rules.**
- Promotion = move: L3-OUT and the RW5 outline disable in Primary and enable in On Deck with `mcf.report.assignments` in the same commit. OK. TWIN (D9) is a copy and is correctly flagged as needing an exception.
- Trimmed setups go to testing: L3 and RW5 go to On Deck, never switched off. OK. GY-SHADOW stops Graveyard paper orders; already flagged as needing new GY-LIFE / GY-FOOTRACE wording.
- Testing 1 = Testing 2: B8-SHADOW covers On Deck and Testing A equally; nothing ranks one testing account below another. OK.
- Setup-freeze and the Friday epoch rule (RESEARCH_RULES 25): LATCH-OPEN and L3-OUT on `monday` are correctly marked as owner overrides; all merges are planned for the weekend. OK.
- Rule-change context: present in all three files and the Monday brief line. OK.

**5. Open conflicts the owner must resolve.**
- **ARENA-LATCH-F vs playing time: conflicts.** A per-setup daily latch in Testing F is in-session throttling in a testing account, which the 11-03 rule forbids as a way to fix starvation and which costs reps. It is now worded as a time-boxed exception that needs your explicit yes.
- **LATCH-OPEN vs playing time: a softer conflict.** Primary already has an owner-approved closed latch (ST-P 10-29), so this extends an existing loss guard rather than adding a starvation fix. It still blocks about 20% of Primary lots within the day. Please confirm that loss latches sit outside the playing-time rule.
- **FROZEN-BLOCKS vs "No freeze" (OUT-EPOCH, owner 11-20):** an amendment that needs your yes. It must also exempt the ROT session rotation, or it would starve low-activity setups.
- **PRIM-EXPOSURE at 12-04:** it would move RW5 into On Deck inside the first frozen block. D6 allows moves at the Friday epoch, so this is consistent only if FROZEN-BLOCKS keeps that wording.

**6. Lookahead, overfitting and small samples.**
- The 11-25 figures (LATCH-OPEN −40 → −8, Testing F −261 → −63, arena +1,221R) are scored on the day that prompted the rules. The bench (33 → 8) is the fair evidence, and it says insurance (E = 1.00), not edge. The files say so.
- The live roster table is 25 sessions and 6 weeks: a green-week count moving by 1 is noise.
- All live records cited for decisions carry the `1 day` tag. The decisions lean on the bench as they should.
- No holdout reads were found. Costs are LR8 (live) or LIVE-L (bench) throughout.
- The shorts_autopsy table header says "all accounts, deduped", but its RW3 / RW5 lot counts (166 / 160) equal the Primary-only roster. That label may be wrong. Not edited here: it does not change any decision. *Critic check:* the label is consistent. The exact names RW3-...-FD and RW5-...-FD are enabled only in Primary (config/account_testing.yaml: "promotion = move; runs in Primary only from 2026-10-21"); their testing copies carry -WB4 / -RQa-1230 suffixes and count as different setups.

**7. Do-no-harm (git).**
- `git diff --stat be8e648c04 origin/explore/2026-11-27 -- . ':!exploration'` is empty: nothing outside exploration/ changed.
- Since 23:30 ET, origin/claude/intraday-trading-system-witis4 has one new commit: f5a2626587 by mcf-bot at 00:00 ET ("tags1: nightly would-skip tags"). That is the scheduled job, not this session.
- Every commit carrying this session's trailer since 23:00 ET is an ancestor of origin/explore/2026-11-27, so none landed on another branch.

Educational only — not financial advice.
