# Decision queue for Monday 11-30 (stacked by expected impact)

Educational only — not financial advice. Written 2026-11-28 ~01:30 ET by the exploration session (decisions key). **Nothing here is applied.** Every "prepared work" item is a draft under `exploration/sandbox/decisions/<code>/`. A change happens only after the owner's reply, outside market hours, with tests, a ledger entry and (for setup moves) `docs/live/assignments.json` regenerated in the same commit.

**Where the numbers come from.** Live journals, 10-23..11-27 (25 sessions), run 1, R after LR8 costs. The bench is the 2-year minute engine with LIVE-L costs. The locked holdout (2024-11-01..2025-02-28) was never read. About **9,650 configurations** have been tried so far: about 9,363 before tonight, about 280 from tonight's tracks and reviewers, and 4 descriptive lineup cuts in this file.

**Rule changes inside the 10-23..11-27 window** (ledger; they affect every number below):
- 10-23: ST-A (no per-setup stop in the arena).
- 10-28: Primary size about $4k.
- 10-29: −2R latch on closed R.
- 10-30: L3 re-promoted to Primary.
- 11-11: TEAM-6.
- 11-12: LR8 costs, LR3, the 300R arena halt and the half-day flatten.
- 11-17: TSZ1 (half lots, 2x slots in testing) and giveback/SPY exits.
- 11-19: Epoch 1 and C3-EXIT100.
- 11-20: stop rounding, FOOTRACE-EXIT, and MF2/MF4 out of Primary.
- 11-21: cost-basis fix.
- 11-23: ST7 out, BRAKE-BURST, Remedy-Q.
- 11-27: GYH, ROT-B3, GEN seed.
- **Next:** 11-30 brings ETF-STOP50/AV50 for NM-ETF and the 11-27 Friday-review arena moves.

## How to answer (one line, copy and edit)

```
LATCH-OPEN monday | L3-OUT out monday | B8 shadow monday | TAGS2 go | ARENA-LATCH-F yes | FROZEN-BLOCKS yes | REPORTS go | HS-SCALE shock-only friday | T1X2 yes | PRIM-ADD3 no | ODB3 as recommended | CRYPTO park
```
Replace `monday` with `friday` to wait for the 12-04 epoch. Any item left out stays open.

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

---

## D1. LATCH-OPEN: make the −2R per-setup latch count open losses too
**You tapped:** `friday`. **Question now:** apply for **Monday 11-30** (override the Friday-epoch rule), or at the **12-04** Friday window?

**Recommendation: Monday 11-30.**
- Monday is already an epoch start. AV50 is "epoch 3", effective 11-30. So applying it now does not split an epoch. It only skips the "decided at the Friday close" step, and the reason that step was missed is that you wanted to ask questions first.
- Waiting a week has a cost. Before LATCH-OPEN, the bench had about 11 days a year at −20R or worse (33 in 2.9 years), roughly a 20% chance in any given week. With it, about 3 a year.

**Options and prepared work** (identical change, different date; `sandbox/decisions/LATCH-OPEN/`):

| Option | What is done | Files |
|---|---|---|
| **monday** | Sat/Sun: `risk.latch_counts_open: true` in config/default.yaml (Primary only). Run the Friday-switch tests, then full pytest, flipping the default-off test expectation for primary. Ledger effective 2026-11-30. Card answered. | `config.diff`, `ledger_monday_1130.jsonl`, `APPLY.md` |
| **friday** (12-04) | Same change after the 12-04 close, effective 12-07 | `config.diff`, `ledger_epoch_1204.jsonl` |
| **-3R** | Also `latch_open_r: 3`: about a third of the cost, but a weaker 11-25 cut (−37 → −23R on the partial-day base; never re-scored on the full day) | `config.diff` (variant lines) |
| no | Nothing | — |

**Questions you are likely to ask, answered in advance:**
1. *Would it have saved 11-25?* Mostly. On the full-day minute replay, −40.1R becomes −8.3R (the journal day was −42.3R). Tonight's loss anatomy shows why the current latch could not act: Primary's L3 had **30 lots open** before the first stop cluster (12:00-13:00), so closed R was still above −2R while open R was far below it.
2. *Does it sell anything?* No. It only blocks **new** entries for that setup for the rest of the day. Open lots keep their own stops and targets.
3. *What does it cost on good days?* About 20% fewer lots. It trims recovery days: 11-12 L3 goes from +31R to about +1R. On a book earning +0.10R per lot that would be about −87R a year. On today's book (−0.156R per lot) the lots it skips are losing lots on average.
4. *Is it an edge?* No, it is insurance. On CHECK it scores the same as a plain size cut (E = 1.00). Tonight's testing-account replay agrees: once a day has gone bad, cutting *any* lots that day does as well as the latch's choice (shorts_autopsy reviewer). What it buys is acting **during** the day, before the whole basket is on.
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
| **out monday** | Sat/Sun:<br>• config/default.yaml: L3 `enabled: false`, removed from Primary `setup_order`<br>• config/account_testing.yaml (On Deck): `enabled: true`, appended to `setup_order`<br>• `python -m mcf.report.assignments`, ledger `kind: move` naming your override of probation, `ledger check`, pytest<br>Merged outside 09:30-16:00 (setup-freeze) | `config.diff`, `ledger_out.jsonl` |
| **out friday** | Same after the 12-04 close, effective 12-07 | same |
| probation | No config change. Ledger note: re-decided at the 12-04 review or at a −10R Primary record | `ledger_probation.jsonl` |
| no | Nothing | — |

**Questions you are likely to ask:**
1. *Isn't L3 positive across accounts?* +0.086R per lot over 453 lots, but 10-20 is 81% of it (`1 day`). Without its best day it is +0.019. In Primary it is −0.209R per lot without its best day (best day 11-12, +31R on 52 lots). On the bench it loses on both splits (−0.100 / −0.126R per lot).
2. *Why L3 and not RW3 or RW5?*
   - Removing any one short helps about equally on the bench (rwout: no short is special).
   - L3 is singled out by its live record without its best day (−0.204 vs −0.037 / −0.057).
   - L3 is also the **basket generator**: 19 lots a day and 35 lots on 11-25, and lots per day is the one setup trait that predicts next week's worst day (metrics track, rho −0.36).
3. *What does Primary lose?* L3's windfall days: 11-12 (+31.0R), 11-16 (+16.4R), 11-20 (+6.0R), 11-10 (+5.8R). The table shows total R is about unchanged without it. What drops is the swing.
4. *Does L3 keep playing?* Yes. In On Deck it gets full reps under On Deck rules, and it can return under C3-BAR2 plus the PRIME-RULES entry tests.
   - **Risk to flag:** On Deck has no per-setup stop and only a 300R account backstop. On 11-25 On Deck lost −391R, and seven arena L3 copies lost −1,037R between them.
   - Moving L3 adds an eighth L3 copy to the arena. That is paper risk only, but it enlarges the arena tail on the next squeeze day. D5 (a latch in one testing account) and D6 are the cheap guards.
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
| **shadow monday** | `risk.netbeta_shadow.enabled: true` (Primary, On Deck, Testing A), `betas_path: null` (beta 1.0 for every symbol). Ledger, tests | `B8-SHADOW/config.diff` |
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
- **Expected effect:** 0 R now. Prior chance that any rule clears both its control and t 2: about 10-20% (tonight's reviewers rated all of them low).

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
  - Account: Testing F. Blocked signals are still recorded by the what-if run (run_id 2), so reps are not lost.
  - Baseline: the same account with latched lots added back from what-if, costed with LIVE-L.
  - Controls: (a) a same-account-day random cut of equal size; (b) a constant size cut on latch-fire days.
  - Duration: 11-30..12-11 if approved by Sunday, else 12-07..12-18.
  - Success: worst-5 days improve ≥ 40%; total R is no worse than the same-day random cut; per-setup better/worse counts reported (remedy rule).
- **Conflict to weigh:** your playing-time rule says no in-session throttling in Primary/Testing. This is a single-account, time-boxed test of exactly that trade-off.
- **Prepared work:** `sandbox/decisions/ARENA-LATCH-F/config.diff`: `account.max_setup_daily_loss_r: null → 2.0` in config/account_testingf.yaml, plus a ledger line and a scoring script to be written before the block starts.

## D6. FROZEN-BLOCKS (new, account structure / process)
**Recommendation: yes.**
- **The rule:** Testing A-F and On Deck run in 2-week blocks with no rule changes inside a block. Setup moves happen only at the Friday epoch. Each account carries at most one pre-registered question per block. Bug fixes are exempt.
- **Why:**
  - There were 23 distinct rule-change dates in 25 sessions, so no testing comparison is clean.
  - Live setup records are 3-12% signal (dev_tactics E2). Paired, frozen designs read a +0.05R/trade change about 3x faster.
- **Prepared work:** `sandbox/decisions/FROZEN-BLOCKS/RULE_DRAFT.md` (proposed RESEARCH_RULES text, ledger `kind: process`). No config change.
- **First block:** 11-30..12-11, with D5 as Testing F's question.

## D7. REPORTS (new): four research-only reports, one "go"
Each reads journals after the close. None touches the trading path. Recommendation: **go**.
1. **PAIRED-CARD** (`sandbox/decisions/PAIRED-CARD/PLAN.md`):
   - Paired day-clustered scores of the pending cards on all ~1,150 live trades a session: LATCH-OPEN (skipped lots, if it is live), RW 1.25x target, L3 first-lot-only, SPREADFLOOR.
   - Skip rules are compared same day, same side, on net R.
   - Reported once on 12-11.
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
- `sandbox/decisions/HS-SCALE/config.diff`: `shock_v.enabled: true`, floors 16R / 24R. The scaled halt stays off.
- With L3 out, N = 3. Keep 16R / 24R: fewer false fires; the lower floors are not scored.
- `build-flatten` stays a separate build.

## D9. GY-SHADOW + TWIN (new, account structure; earliest 12-04, effective 12-07)
**Recommendation: discuss.** Approve the direction now, build for 12-04.
- **(1) Graveyard to shadow-only.** Keep 1-2 leaders live as a cost sample. Correct the shadow's −0.047R per trade bias before any foot race.
- **(2) The freed paper account becomes TWIN:** an exact copy of Primary plus **one** candidate change per block, read against Primary as a real-fill paired test.
  - First candidate: whichever of LATCH-OPEN / L3-OUT you did *not* apply, or the RW 1.25x target.
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
  - It cut green weeks from 2/6 to 1/6 in the live table.
  - It was positive on flat-open days (+21.1R).
- **Recommendation:** decide at 12-04 with the first week of LATCH-OPEN / L3-OUT data.
- **Prepared work:** `sandbox/decisions/PRIM-EXPOSURE/config.diff` (outline mirroring L3-OUT).

## D11. GOAL-STAGES (new): what counts as progress while the edge is negative
**Recommendation: yes.**

**The evidence** ([metrics](findings/metrics.md) §4; the reviewer reproduced it exactly):
- At Primary's lot correlation (0.185) and 38 lots a day, being red on no more than 1 day in 20 needs **+0.67R per lot**.
- Even at correlation 0.03 and 100 lots a day it needs about +0.29R per lot. That is about 6x the best live edge (about +0.01 to +0.12R per lot without the best day).
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

Educational only — not financial advice.
