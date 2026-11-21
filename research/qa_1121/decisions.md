# QA area: decisions (docs/live/decisions.json + research/owner_inbox/2026-11-20.md)

Repo checked at HEAD a1266f32d. Live data comes from origin/mcf-data* journals (last fetched 11-20 21:00 UTC). I produced two re-derivations:
- `live_trades()` as shipped: `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/decisions/live.csv`
- a true LR8 version that also selects `side` and `target`: `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/decisions/live_lr8.csv`, built by `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/decisions/lr8.py`

Status counts: 50 open (44 at the 19:18 brief, plus FP-A..F overnight) and 152 answered.

## Checks

| # | Check | Result | Evidence (mine vs claimed) |
|---|---|---|---|
| 1 | Week Primary R and 11-20 Primary R | PASS | 11-16..20 = +25.31, −2.46, −5.52, −16.21, +3.00; total +4.11R (claimed +4.1 / +4.11). 11-20 = +3.00R |
| 2 | Brief count "5 items + 37 more open" | PASS | decisions.json at ec82e29e4 has 44 open. The 5 brief items hold 7 codes; 7 + 37 = 44 |
| 3 | Consultant: "10 open > 3 nights, 44 open, 34 raised 11-18..20" | PASS | INACT added 11-16 19:21 (654a42745). W2-MTM / W3-GB5S added 11-18 10:15 (255c20390). 44 − 10 = 34 |
| 4 | G261019-04-GY numbers | PASS | 230 tr / 13 sess, −99.82R, avg −0.434, w/o best −0.524, w/o top-2 −0.626, day t −1.08, last-4 −107.59. Split: before 11-20 130 tr −0.76R; 11-20 100 tr −99.06R. All match the card |
| 5 | G261019-04-GY recommendation | PASS (note) | Keeping it in Gen goes against the owner's own 11-18 condition (keep only while total R is positive; it is now −99.8R). The card discloses this. FOOTRACE-EXIT does not apply (13 < 15 active days) |
| 6 | ST7-MOVE card vs source REVIEW.md | PASS | REVIEW: 42 tr, −7.30R, −0.174 avg, LR8 basis. My true LR8 to 11-19 = −7.31R; with 11-20 it is 43 tr, −7.08R, −0.165 |
| 7 | ST7 figures in nightly / brief / consultant (43 tr, −0.149, w/o best −0.281, day t −1.16) vs the card (−0.174, −0.31) | FAIL | The brief/nightly figures match `live_trades()` exactly (−6.41R), but that is the booked basis, not LR8 (see finding 1). The owner sees two different figures for the same decision |
| 8 | Nightly Primary records (RW3 +0.175, RW5 +0.109, L3 +0.200, NM-ETF −0.424; day t 0.61 / 0.87 / −0.15 / −0.34) | PASS on the shipped tool; FAIL on the stated LR8 basis | True LR8: RW3 +0.151 (26.6R), RW5 +0.078 (14.5R), L3 +0.191 (35.99R). NM-ETF is unchanged (all rows after 11-12). The day-t values reproduce with mcf/analytics/robust.day_t (per-day means), so L3's −0.15 alongside a +0.20 avg is correct |
| 9 | NMETF-SIZE card numbers | FAIL (stale) | Card: "Primary slice 15 tr +0.075R" and "whole record 33 tr +0.21R t 3.5". Those are Primary through 11-19 (15 tr, +1.11R) and all accounts before 11-19 (34 tr, +0.246). Current Primary is 27 tr, −11.45R (−0.424). All accounts now 79 tr, −23.7R (Testing E −18.3R) |
| 10 | ETF-BURST numbers | PASS | Primary 12 lots −12.57R. Testing E WB4 is 22 tr −17.88R for the whole day (the card's 15 burst-bar lots at −15.8R fits inside that). ULT-22 18 tr −12.24R for the day (11 burst lots at −10.1R) |
| 11 | FP-A..F numbers vs research/final1121 | PASS | C1A1 net −12.8 − 2.5 + 7.1 = −8.2R. Live replay 5.18 + 10.50 + 5.87 = +21.6R. P1 111 tr +0.237 / +0.103 (69%). RW7 +60.1 → +18.1R |
| 12 | LPB-* numbers | PASS (minor) | Blocks 21 + 21 + 20 + 2 + 3 = 67 of 84. P(3 empty) = 0.63³ = 0.25. The inbox text says both 42 and 43 Gen capacity rejects; the card says 53 variants, the inbox 54 configs |
| 13 | Answered RETIRE-R3: code matches owner condition | PASS | footrace.py:71 sets `RETIRE_MIN_SESSIONS, RETIRE_MIN_TRADES, RETIRE_MAX_WO, RETIRE_MAX_LAST10 = 20, 150, -0.10, 0.0`; ledger 2026-11-20-retire-r3 |
| 14 | RETIRE-R3 applied list on the stated LR8 basis | FAIL | NS3-failed-vwap-reclaim-short-FD last-10-session R: booked −0.008 (as in the ledger), true LR8 **+0.26** → fails `last10 <= 0`. exhaustion_short w/o best: −0.109 booked, −0.101 LR8 (passes by 0.001). The other 10 pass either way |
| 15 | BRAKE-BURST implemented | PASS | config/default.yaml:624-625 sets burst_max_entries 30, burst_window_min 10; ledger 2026-11-23-brake-burst |
| 16 | BRAKE-WATCHDOG implemented | PASS | .github/workflows/watchdog.yml:55 defaults to `'act'` |
| 17 | WW-PROTECT / WW-CLUSTER implemented | PASS | docs/PROTECTED.md has PROT-29; footrace metrics carry wo2_avg_r and t_day; ledger entries present |
| 18 | BEG-ORB / BEG-GNG implemented and timing | PASS | assignments: BEG-ORB in testingf (Testing F), BEG-GNG in explore1 (Testing B); ledger 2026-11-23-beg1120-testing-admissions. PR #238 merged 11-20 16:18 ET (after the close). The intraday "Merge … into HEAD" commits are local branch syncs, not main |
| 19 | C3-NS5 / PKT-FX / INV / ST7-A / G261019-04 answers implemented | PASS | NS5 in On Deck (assignments); 12 FOOTRACE moves in ledger 2026-11-23-friday-review-1120; inverse shadow ran day 1 (forward logs); ST7-FD still in Primary; G261019-04 still in gen |
| 20 | WW-REMEDY-Q implemented as approved | FAIL (scope) | See finding 3 |
| 21 | EARN-CLOSE answer reflected in reports | FAIL | See finding 5 |
| 22 | Open decisions still valid (not stale) | FAIL | M2, SIP-DEF, MF4-OK, LATCH-CLOSE, W3-GB5S, CONS-PMX, EXIT-MF5 (partly), ETF-BURST, FP-A (findings 6-8) |
| 23 | Ledger entries for answered OUT-* items | FAIL (minor) | `grep -c` in research/ledger.jsonl: OUT-NMETF 0, OUT-NULL 0, OUT-RETIRE 0, WW-ST7 0 |
| 24 | decisions / assignments schema tests | PASS | `pytest tests/test_decisions_json.py tests/test_assignments.py` → 10 passed |
| 25 | `python -m mcf.research.ledger check` | Not verifiable here | It crashes with IndexError at mcf/research/ledger.py:75 (`syms[0]` on an empty list) because the container has no bar data. That is an environment limit, but the tool should not crash |

## Findings

1. **Critical. `footrace.live_trades()` silently skips the LR8 re-cost (DQ-P3 broken), and the owner's decision numbers inherit it.**
   - mcf/report/footrace.py:358 does not SELECT `side` or `target`.
   - mcf/costs.py:191 reads `row["side"]`, the KeyError is caught at :194, and every row before 11-12 keeps the old flat cost basis.
   - The function and the ledger both say "LR8".
   - Effects:
     - Nightly / brief Primary records are overstated: RW3 +0.175 vs +0.151 true; RW5 +0.109 vs +0.078; ST7 −0.149 vs −0.165.
     - The ST7-MOVE card (−7.3R LR8, from REVIEW.md) and the brief (−6.41R) disagree, so the distance to the −10R line reads as 2.7R or 3.6R depending on where the owner looks. True: 2.9R.
     - FOOTRACE-EXIT and RETIRE-R3 ran on the wrong basis (finding 2).
   - Reproduce: compare `cost_r_lr8` on a full `SELECT *` of mcf-data trades with live.csv. ST7: −7.08 vs −6.41.

2. **Major. NS3-failed-vwap-reclaim-short-FD was retired terminally but fails RETIRE-R3 on the mandated LR8 basis.**
   - Last-10-session R is +0.26R under LR8; −0.008R on the booked basis the review used.
   - The ledger (2026-11-23-friday-review-1120) already marks it "borderline … <= 0 by a hair" and claims "LR8 R after costs".
   - Terminal retirement of a setup that fails the owner's condition should be reverted or re-asked before 11-23.
   - exhaustion_short (Testing F) passes by only 0.001 on LR8 (−0.101 vs the −0.10 bar).

3. **Major. Remedy-Q copies were deployed beyond the owner's conditional approval.**
   - Owner: "If all is true, remedy-q yes absolutely and quickly."
   - The re-check (research/remedyq_1120/verdicts.json) found:
     - (a) at 13:00: not confirmed.
     - (b) and (c): not confirmed.
     - A 12:30 cut, chosen after seeing the live sweep and a 66-config lab sweep: "confirmed (weak)", paired t 1.94 vs bar 2.89.
   - Copies with a 12:30 window were still added to Testing F, A and B from 11-23 (ledger 2026-11-23-remedyq-testing-copies; commit 4f05fcace, 14:53 ET).
   - The ledger discloses all of this honestly, but "all true" was not met and the cut-off differs from the approved 13:00. This should have been re-asked.
   - The inbox's "Owner answers" section still says "confusing … re-asked" with no record of the later conditional yes.

4. **Major. The NMETF-SIZE card is stale and paints NM-ETF positive.**
   - It shows only the through-11-19 Primary slice (+0.075R) and the pre-11-19 all-account record (+0.21R, t 3.5).
   - Current Primary is 27 tr, −0.424R after 11-20's −12.57R. The brief item has the current figure; the card the owner answers from does not.
   - OUT-NMETF (answered) carries the same pre-11-19 figures.

5. **Minor. The consultant mis-states EARN-GO's decision status.**
   - The C3 status table says EARN-GO is "Stalled … not on the decisions card. It needs a 'close C3-EARN' line from you".
   - EARN-CLOSE was answered yes on 11-19 ("EARN-GO closed"): decisions.json EARN-CLOSE and ledger 2026-11-19-owner-answers-evening.
   - The owner is being asked again for an answer he already gave.

6. **Major. Open decisions that are already implemented or overtaken (stale, cluttering the 44/50-item card).**
   - **M2**: GEN-261026-03 was already moved Gen → Testing D on 11-11/12 (assignments `first_session 2026-11-12`).
   - **SIP-DEF**: Testing D/E/F have traded since 11-12 (601 / 377 / 719 trades), yet the card still says "30 setups wait on it".
   - **MF4-OK**: MF4-FD left On Deck through C3-EXIT100 and was RETIRED on 11-20 (assignments `accounts: []`).
   - **EXIT-MF5**: asks to bring back setups it names, but CWT13-vwapstretch-z05-long and MF5-…-FD were RETIRED on 11-20. The card was not updated, and the retirement went ahead while this decision was still open.
   - **M1 / INACT / W2-ODOUT / HN3**: numbers are stale.
     - M1: 12 tr −0.397 then; nightly now 34 tr −0.287.
     - INACT: CWT13-z075-long has had zero trades since moving to Testing B on 11-05, about 12 sessions, not 2.
     - W2-ODOUT: RW1-FD made +9.6R on 11-20.
     - HN3: 51.9% vs 49.8% now.

7. **Major. Open decisions that conflict with answers already given.**
   - **LATCH-CLOSE** (close lots when the latch fires) conflicts with GB-NOEXIT, answered yes on 11-19: "No exit rule or day level lock"; "−2R latch untouched".
   - **W3-GB5S** (+5R peak giveback lock) conflicts with GB-NOLOCK, answered yes.
   - **CONS-PMX** (15:00 / 15:30 clock exits) is covered by GB-NOEXIT (O4 clock exits −481R) and GB-BLPARK.
   - These should be closed or re-framed, not left open next to the answers.

8. **Minor. Duplicates and overlaps.**
   - **ETF-BURST** asks for a study that final1121 has now run (etf-burst track, 15+ configs, FP-D / FP-F). It is superseded, yet it is still listed as a separate open "study" item.
   - **FP-A** (Primary shadow for P1 after On Deck) repeats W3-PSHADOW, answered "yes after On Deck" on 11-18 (rule 34).
   - **FP-B** (L3-lowdist + L3-rsi5hi as one slot) overlaps CORR1, which is still open and pairs L3-fromopen with L3-rsi5hi. The two groupings are inconsistent.
   - **GB-BRAKE** overlaps OUT-BRAKE (answered yes, study).

9. **Minor. Wording errors.**
   - Consultant: NM-ETF "green on 5 of 7 days (+2.01R) before 11-19". There are only 5 sessions before 11-19 and all 5 were green (12 tr, +2.01R).
   - Brief item 2 sets "record before 11-19 was 33 tr, +0.21R" (all accounts) next to the Primary figures without labelling it as all accounts.
   - ST7-MOVE's card does not cite ST7-A (answered the day before: "ST7-FD kept … as long as its not restricting"). It does acknowledge consistency over churn.

10. **Minor. Missing ledger lines.** OUT-NMETF, OUT-NULL, OUT-RETIRE and WW-ST7 were answered yes on 11-20 and have no ledger line. OUT-NMETF freezes NM-ETF and commits a size rule, so it arguably needs one under RESEARCH_RULES. `python -m mcf.research.ledger check` crashes on an empty symbol list (mcf/research/ledger.py:75) instead of failing cleanly.

Educational only — not financial advice.

## Verifier

```json
{
 "confirmed": [
  {
   "finding": "F1: footrace.live_trades() skips the LR8 re-cost for every row before 11-12, so every since-start record built on it is on the old flat-cost basis while the code and ledger call it LR8. The week's Primary R is not affected.",
   "severity": "critical",
   "evidence": "mcf/report/footrace.py:358-359 selects strategy, symbol, date, entry_time, entry, stop, shares, pnl, pnl_adj, r_multiple. It does not select side, target, exit, exit_reason or meta. mcf/costs.py:191 reads int(row['side']) and the KeyError is caught at :194 ('continue'), so the row keeps cost_r. My re-run with SELECT * (scratchpad/qa/decisions_verify/v.py): all 1149 Primary rows before 11-12 differ. Primary records, shipped vs true LR8: ST7 43 tr -6.41R / -0.149 vs -7.08R / -0.165; RW3 176 tr +0.175 vs +0.151 (26.6R); RW5 186 tr +0.109 vs +0.078 (14.5R); L3-fromopen 188 tr +0.200 vs +0.191. NM-ETF is unchanged (-11.45R, all its rows are after 11-12). Week Primary is unchanged and matches the claim: 25.31, -2.46, -5.52, -16.21, +3.00 = +4.11R. The ST7 distance to the -10R line is 2.92R true, against the 3.6R implied by the brief.",
   "fix": "Select side, target, exit, exit_reason and meta in live_trades (or SELECT *), add a test that cost_r_lr8 changes rows before 11-12, then regenerate the nightly, brief and footrace figures and the ST7-MOVE card on one basis."
  },
  {
   "finding": "F3: the Remedy-Q Testing copies were deployed although the owner's condition ('if all is true') was not met. Only (a) was confirmed, and only weakly, at a 12:30 cut-off picked after the sweep instead of the 13:00 that was approved. The owner inbox still shows the item as re-asked.",
   "severity": "major",
   "evidence": "research/remedyq_1120/verdicts.json: a_cut_1300 'not confirmed'; a_cut_1230 'confirmed (weak) ... paired t 1.94 < bar 2.89'; b_l3_gap_atr 'not confirmed'; c_rw_gap_le_1 'not confirmed'. docs/live/decisions.json:2698 quotes the owner, \"if all is true, remedy-q yes absolutely and quickly\", then records 3 Testing copies from 11-23. Ledger line 244 (2026-11-23-remedyq-testing-copies) sets windows [950,1500] -> [950,1230] in testingf, testing2 and explore1. research/owner_inbox/2026-11-20.md:115 still says 'confusing ... re-asked'. Mitigation: the copies are Testing-only, the parents are unchanged and the ledger discloses all of this.",
   "fix": "Re-ask the owner before 11-23 with the actual result ((a) weak at 12:30; (b) and (c) failed), or hold the copies. Update inbox line 115."
  },
  {
   "finding": "F4: the NMETF-SIZE card (open) and OUT-NMETF (answered) show stale, positive NM-ETF figures. Primary is now 27 trades and -11.45R after 11-20's -12.57R.",
   "severity": "major",
   "evidence": "decisions.json NMETF-SIZE numbers: 'Primary slice: 15 trades +0.075R t 1.18' and 'whole record 33 trades +0.21R t 3.5'. My Primary figure through 11-19 is 15 tr +1.12R (+0.075), which matches that stale slice. Primary through 11-20 is 27 tr -11.45R (-0.424); 11-20 alone is 12 tr -12.57R. Deduplicated all-account record: 45 tr -5.58R.",
   "fix": "Refresh the card with the current Primary record and label which figures are all-account."
  },
  {
   "finding": "F6 (partly confirmed): several open decisions are already implemented or overtaken.",
   "severity": "major",
   "evidence": "M2: assignments.json shows GEN-261026-03-...-holdtr-short in testingd from gen, first_session 2026-11-12, but the card still says 'condition not met yet'. SIP-DEF: the card says 'D/E/F have no data yet / 30 setups wait', yet testingd, testinge and testingf have traded since 11-12 (601 / 377 / 719 deduplicated trades). MF4-OK: MF4-h40-open-flowsell-FD is RETIRED (accounts [], first_session 11-23). EXIT-MF5: it asks to revisit CWT13-vwapstretch-z05-long, which was RETIRED on 11-20 (accounts []) while this decision was still open. MF5-flowsell-vwapup-rsi5hi itself (non-FD) is still in the Graveyard, so that part of the original claim is overstated.",
   "fix": "Close M2, SIP-DEF and MF4-OK as done or overtaken. Re-frame EXIT-MF5 now that CWT13-z05-long is retired."
  },
  {
   "finding": "F7 (downgraded): open decisions that overlap answers already given. LATCH-CLOSE is an exit rule after the owner answered 'No exit rule or day level lock' (GB-NOEXIT, -2R latch untouched). CONS-PMX's clock exits are covered by GB-NOEXIT. W3-GB5S is only a shadow flag, so it does not strictly conflict with GB-NOLOCK.",
   "severity": "minor",
   "evidence": "decisions.json: GB-NOEXIT answered 11-19 ('no time cut ... clock ... exit'; '-2R latch untouched'); LATCH-CLOSE open ('also close that setup's open lots'); CONS-PMX open; W3-GB5S open ('shadow flag ... no live effect').",
   "fix": "Close LATCH-CLOSE and CONS-PMX, or re-ask them with explicit reference to GB-NOEXIT."
  },
  {
   "finding": "F5: the consultant asks the owner to close C3-EARN / EARN-GO, which he already did on 11-19.",
   "severity": "minor",
   "evidence": "research/owner_inbox/2026-11-20.md:217 says 'It needs a \"close C3-EARN\" line from you'. Line 23 of the same file says 'EARN-CLOSE yes'. decisions.json EARN-CLOSE: answered, 'owner 2026-11-19: \"Earnings yes\" -> EARN-GO closed'.",
   "fix": "Mark EARN-GO as closed in the consultant's C3 table."
  },
  {
   "finding": "F8: ETF-BURST is still listed as an open study, but final1121 has already run that study.",
   "severity": "minor",
   "evidence": "research/final1121/tracks/etf-burst.md and scripts/etf-burst/{grid,check,replay}.py exist; ETF-BURST is still open in decisions.json.",
   "fix": "Close ETF-BURST or point it to FP-D/FP-F."
  },
  {
   "finding": "F9: wording error. NM-ETF is described as 'green on 5 of 7 days before 11-19', but Primary had only 5 sessions before 11-19 and all 5 were green.",
   "severity": "minor",
   "evidence": "Primary NM-ETF by date: 11-12 +0.21, 11-13 +0.44, 11-16 +0.54, 11-17 +0.74, 11-18 +0.08, i.e. 12 tr +2.01R; 11-19 -0.90; 11-20 -12.57.",
   "fix": "Reword to '5 of 5'."
  },
  {
   "finding": "F10: answered items have no ledger line, and the ledger check crashes when there is no bar data.",
   "severity": "minor",
   "evidence": "grep -c in research/ledger.jsonl: OUT-NMETF 0, OUT-NULL 0, OUT-RETIRE 0, WW-ST7 0. No ledger entry dated 11-19 or later records the NM-ETF freeze or its size rule. mcf/research/ledger.py:73 calls store.load(syms[0]) with no guard for an empty symbol list.",
   "fix": "Add a ledger line for the OUT-NMETF freeze and size rule. Make ledger check fail with a clear error when there is no bar data."
  }
 ],
 "rejected": [
  "F2 (NS3-failed-vwap-reclaim-short-FD fails RETIRE-R3 on LR8, last-10 +0.26R): REFUTED. The QA agent's lr8.py selects side and target but not exit or exit_reason, so costs.parts_from_row prices the exit at 0 and its 'LR8' row R is wrong (it comes out more favourable than the booked basis, which cannot happen when costs are added). With SELECT * and the shipped setup_stats, whole deduplicated record: NS3 290 tr / 26 sessions, w/o-best -0.165, last10 -0.995 -> retire_flag True. exhaustion_short 158 tr, w/o-best -0.126, last10 -1.755 -> True (not a 0.001 margin). Both retirements hold on the true LR8 basis.",
  "F2/F8 secondary claims that rely on live_lr8.csv for whole-record (non-Primary) figures, e.g. exhaustion_short -0.101: rejected for the same reason. The Primary-only LR8 figures happen to match mine and are kept under F1.",
  "F6 INACT sub-claim (CWT13-z075-long has zero trades since moving to Testing B on 11-05): REFUTED. The deduplicated live trades show CWT13-vwapstretch-z075-long with 60 trades in explore1, the last on 2026-11-20.",
  "F6 EXIT-MF5 sub-claim that 'MF5-...-FD' retiring makes the card stale: overstated. The card names MF5-flowsell-vwapup-rsi5hi (non-FD), which is still in the Graveyard. Only the CWT13-z05-long retirement is confirmed.",
  "F7 W3-GB5S conflict with GB-NOLOCK: not a strict conflict. W3-GB5S is a shadow log with no live effect, and GB-NOLOCK forbids a live lock rule.",
  "F6 M1 / W2-ODOUT / HN3 staleness: not independently re-checked; treated as unverified, not as errors."
 ]
}
```
