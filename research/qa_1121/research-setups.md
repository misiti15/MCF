# QA: research-setups (week 2026-11-16..11-20)

Scratch: /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/research-setups (live.parquet = LR8 loader with SELECT *; lt.pkl = mcf.report.footrace.live_trades(); out/ = my re-run of remedyq live_tod.py). The inbox was not changed.

## Checks

| # | Check | Result | Evidence (mine vs claimed) |
|---|---|---|---|
| 1 | Remedy-Q live sweep reproduces | PASS (data was partial) | I re-ran `live_tod.py` on journals updated to the close. I get 838 trades vs 825 claimed. The 13 extra are 11-20 trades: the study was committed at 14:53 ET on 11-20 (4f05fcace), during the session. Pooled R kept by cut-off: 13:00 +161.3 (claimed 154.31), 12:30 +156.8 (150.88), 13:05 +156.7 (149.72), 13:15 +154.3 (147.31), no cut +136.3 (126.7). Conclusions do not change. |
| 2 | "13:00 beats 13:05 / 13:15 live" | PASS pooled, minor exception | True pooled and per setup across all accounts. Primary L3 is the exception: 13:15 +37.45 > 13:00 +37.04 (study file); on full data 41.27 vs 40.87. |
| 3 | Is ~13:00 really the cut-off? | Mixed (correctly labelled "not confirmed") | Live all accounts peaks at 13:00; live Primary-only pooled peaks at 12:30 (89.23 vs 79.88 at 13:00). On lab CHECK (Primary rules), cutting at 13:00 lowers avg R for all 3 setups (L3 −0.0004, RW3 −0.0029, RW5 −0.0085; excess vs random −28.01R). These match verdicts.json. |
| 4 | Cut-off chosen on FIT = 12:30 | PASS | Recomputed from lab_cutoff_sweep.csv: FIT pooled d_avg smoothed over 3 points peaks at 1230 (0.0094), next 1215 (0.0058). There is a second FIT bump at 13:30–13:45 (0.0076). |
| 5 | Copy window [950,1230] matches the code and the study unit | PASS | heat.py:74-75: tod = bar close. setups.py:521-522 (eligible: bucket close ≤ hi) and :578-579 (mask tod ≤ hi), so the last entry is on the bar closing at 12:30. live_tod.py floors the signal minute; live signals land 0–4 min after the bucket close (590/843 at minute%5 = 0), so flooring gives the bar close. Matches. |
| 6 | RQa copies = parents except the window | PASS | testingf.yaml:1106-1123, testing2.yaml:1681-1695 and explore1.yaml:1123-1137 vs default.yaml:112-121 / 336-349: same module, min_adv, refire/cooldown and prefilter; only window 1500→1230 changes. Placement (F / A / B) matches ledger line 244 and assignments.py naming. assignments.json carries the copies. |
| 7 | Setup-freeze (merge time) | PASS | RQa and BEG configs reached the default branch in PR #238 at 16:18 ET on 11-20, after the close. |
| 8 | Look-ahead / locked block in lab_tod.py | PASS with caveat | `B.no_locked` asserts on both the trades and the QQQ dates. The QQQ read filters out 2024-11-01..2025-02-28. Caveat: CHECK (2025-10-01..2026-11-04) contains the live sessions 10-12..11-04 that produced the hypothesis (~17 of ~275 sessions), so it is not a fully independent sample. |
| 9 | Config count and t bar | PASS | 12 cut-offs + 4 salvage rules × 2 cut-offs + b + c = 22 per setup, 66 in total; sqrt(2 ln 66) = 2.895 → 2.89. |
| 10 | verdicts.json lab metadata | FAIL (minor) | verdicts.json says signals 55030, fit 169, check 274. lab_meta.json says 55029, 170, 276. These are two different runs. |
| 11 | Ledger RQa stats vs CSVs | PASS | Ledger lab CHECK (Primary rules) figures L3 −0.0633→−0.0586, RW3 −0.0486→−0.0415, RW5 −0.0515→−0.0476 and Testing-rules figures L3 −0.0078 / RW3 +0.016 / RW5 +0.004 all match lab_cutoff_sweep.csv. Live kept % (84.4 / 72.5 / 64.3) matches. |
| 12 | Salvage cross-check on live | PASS | Live after 12:30 with cost ≤ 0.08: 88 trades, −0.056 on full data (claimed 85 trades, −0.068 on partial data). |
| 13 | Rule-change context with stats (Remedy-Q) | PASS with one error | Stated in the verdicts and ledger, but verdicts.json dates BRAKE-BURST to 11-20. The ledger has it effective 2026-11-23 (ledger line 241). |
| 14 | lateqshort REVIEW numbers | PASS | Per-day table for GEN-261029-06 (Gen 85 trades −11.53R, avg −0.136, w/o best day −0.187; Testing D 97 trades +18.18R, best-day share 9.30/18.18 = 51%; all 182 trades +0.037, w/o best day −0.02) matches live trades exactly. The Testing D block is identical to the Gen block (account_testingd.yaml:968-982 vs account_gen.yaml:5907-5921). Module last committed 10-28 (d3d52e996). Rule-change context is stated. Since the review: 11-20 Testing D was 40 trades +21.97R, and the best-day share is now 55% (11-20). The "regime" verdict was written before that day. |
| 15 | st7_review REVIEW numbers | PASS on the headline, minor window mix | Primary LR8: 42 trades −7.30R, −0.174, w/o best day −0.307 (mine −7.30 / −0.174). Shrunk estimate −0.116 checks out. The "+15R to return" equivalence is correct. The Section 4 table for L3 / RW3 / RW5 since admission matches (37.9 / 21.1 / 10.7). The "Since TEAM-6: L3 +34.5, RW3 −4.5, RW5 −6.4" line reproduces only if partial 11-20 trades (to 12:47 ET) are included; through 11-19 it is +32.9 / −6.3 / −7.1, while the section header says "through 11-19". |
| 16 | latepb REPORT | PASS on counts, minor on basis | The 84 signals and every block count (21 halted, 21 buying power, 20 spread, 2 cost, 1/1/1 other) match live_signals_replay.csv. sqrt(2 ln 54) = 2.82 checks out. But "live journal +0.208 / Live +0.21R over 17 trades" is the booked basis: on LR8 it is +0.179 (17 trades), against rule 32. |
| 17 | beginner_1120 | PASS | 69 configs stated. The deployed classes (beginner_setups.py:79-131, 134-205) match the tested rules (stopOR far side of OR15, 2R target, breakeven at +1R, entries 09:50-11:29; GNG time exit 12:00). The overlap test ran (deploy/overlap.json): 52% of BEG-ORB's days are orb20_a's. The reverse is 80% (85% for orb20_a-WB3); this is disclosed and the copies are kept out of those accounts. The admission path is the CLAUDE.md "meets top-10 standard"; REPORT and config both state it is not profitable (CHECK −0.026, t −1.89) and that BEG-GNG is a `1 day` record. |
| 18 | Targeted tests | PASS | `pytest tests/test_assignments.py test_new_accounts_1111.py test_protected.py test_beg1120_deploy.py test_testing2.py`: 44 passed. |
| 19 | outsider_1120 headline | FAIL | Claimed: 28,097 trades, −0.125R, −3,500R, 3 of 33 sessions green, Primary −87.5R. On the LR8 basis (rule 32): −0.151R, −4,241R, 2 of 33 green, Primary −133.4R. The outsider numbers reproduce exactly from `footrace.live_trades()`, which is not LR8 before 11-12 (finding 1). |

## Findings

1. **Critical: `mcf.report.footrace.live_trades()` does not apply LR8 to pre-11-12 rows, although its docstring says it does. Every consumer of it is too optimistic.**
   - **Cause:** footrace.py:358 selects only `strategy, symbol, date, entry_time, entry, stop, shares, pnl, pnl_adj, r_multiple`, with no `side` or `target` column. In costs.py:191 the call `row["side"]` raises KeyError, and costs.py:194 swallows it with `continue`. So every pre-11-12 row keeps its booked flat-cost R.
   - **Size of the gap:** Primary before 11-12 is −127.1R (footrace) vs −173.0R (LR8, SELECT * loader); all accounts to 11-19 are −3,500R vs −4,241R.
   - **Where it shows up:**
     - The FOOTRACE-EXIT and RETIRE-R3 lists, built by `build(live_trades(...))` at footrace.py:453 and applied at the 11-20 Friday review, used the optimistic basis. That makes them less strict than rule 32 ("underestimate potential") intends.
     - The owner inbox (research/owner_inbox/2026-11-20.md) gives ST7-MOVE as 43 trades −0.149 (line 218) and RW3-FD as +0.175R (line 145). On LR8 these are −0.165 and +0.151. The ST7 REVIEW (LR8) gives −0.174 for the same decision, so the owner is shown two different numbers.
     - The QA harness's own recommended loader has the same problem, so other areas' Primary figures may be booked-basis too.

2. **Major: Remedy-Q (a) is labelled "confirmed (weak)" and built, but the owner's condition was not met.**
   - The owner's approval (ledger line 244) was "Double check the no new trades after 1pm theory ... If all is true, remedy-q yes". The 13:00 theory was *not* confirmed (lab CHECK is worse at 13:00 for all 3 setups), and (b) and (c) failed.
   - 12:30 was substituted, and its lab CHECK paired t is 1.94, below the stated bar of 2.89 and below the BAR90 Testing bar of 0.9 × 2.89 = 2.60 (rule 22).
   - The lab expectancy of every copy is still negative (about −0.04 to −0.06R per trade).
   - In the Testing book, where the copies actually run, the pooled CHECK is worse: d_avg −0.0017, excess vs random −14.6R. The verdict only says "Testing book mixed (L3 −0.0078)".
   - The decision may be legitimate as a Workbench-style copy, but "confirmed" overstates it.

3. **Major (method): the paired day t used as significance in Remedy-Q is biased upward whenever the base book loses.**
   - `paired_day_t` (common.py:38-46) compares day *totals*. Removing any slice of a negative-expectancy book raises the totals.
   - Proof from the CSV: Primary FIT cut_1300 has d_avg −0.0035 (worse per trade) yet t_paired 2.79; cut_1330 has t 3.84.
   - The t of 1.94 at 12:30 therefore does not test timing skill. Only the `excess_vs_random` column does (+31.25R pooled Primary CHECK), and it has no t or p.

4. **Minor: Remedy-Q ran on partial 11-20 data but labels its window "2026-10-12..11-20".** The commit was at 14:53 ET with 825 of 838 trades in, and the session was not finished. No conclusion changes (table above).

5. **Minor: provenance mismatch in Remedy-Q.** verdicts.json (signals 55030, fit 169, check 274) disagrees with lab_meta.json (55029, 170, 276), so the CSVs and the verdict come from different lab runs.

6. **Minor: verdicts.json `rule_changes_in_live_window` lists "BRAKE-BURST 11-20".** The ledger has it effective 2026-11-23.

7. **Minor: the claim "13:15 worse than 13:00 live" is not true per setup for Primary L3** (+37.45 vs +37.04). It does hold pooled.

8. **Minor: ST7 REVIEW mixes windows.** The "since TEAM-6" comparison (L3 +34.5 / RW3 −4.5 / RW5 −6.4) includes 11-20 morning trades, while its table is "through 11-19" (+32.9 / −6.3 / −7.1). ST7's own −9.4 is unaffected.

9. **Minor: latepb REPORT quotes the live record on the booked basis** (+0.208 / +0.21R) instead of LR8 (+0.179). The conclusion is unchanged.

10. **Minor (disclosure): the Remedy-Q lab CHECK window overlaps the live sessions (10-12..11-04) that motivated the after-1pm hypothesis.** It is not stated as a contamination caveat.

No issues found with:
- the lateqshort luck-vs-rule-change verdict (the numbers reproduce, the module and config are unchanged, and the rule-change context is listed);
- the BEG deployment versus the tested rules;
- the RQa config versus the ledger;
- the setup-freeze timing.

Educational only — not financial advice.

## Verifier

```json
{
 "confirmed": [
  {
   "finding": "F1: mcf.report.footrace.live_trades() does not apply LR8 to rows before 11-12, although its docstring says it does. Every consumer gets the booked flat-cost R, which is too optimistic: the FOOTRACE exit/retire review and the owner-inbox Primary records.",
   "severity": "critical",
   "evidence": "Code: footrace.py:358-359 selects only `strategy, symbol, date, entry_time, entry, stop, shares, pnl, pnl_adj, r_multiple`. costs.py:191 reads `int(row[\"side\"])`, which raises KeyError, and costs.py:194 catches it with `except (TypeError, ValueError, KeyError): continue`, so each row keeps its booked R.\n\nMy recompute (scratch qa/research-setups-verify/fr.py), same function, narrow select vs SELECT *:\n- Primary before 11-12: -127.1R vs -173.0R (1,149 trades).\n- All accounts to 11-19: 28,097 trades, -3,500.3R vs -4,240.7R. This matches the reporter and outsider_1120.\n\nLive consequence:\n- I re-ran footrace.build() on full data as of 11-20 (prev=None).\n- Narrow basis: exit_review empty, the same as the published docs/live/footrace.json (asof 11-20, 0 exit candidates).\n- LR8 basis: 2 exit candidates, CWT05-flush-m05-v3-long and GEN-261027-06-ORBfailUp... (the second is Testing C's -111.2R setup).\n- As of 11-19 both bases flag GEN-261027-04, so the gap shows only on the 11-20 data.\n\nOwner inbox: research/owner_inbox/2026-11-20.md says 'R after costs' and gives:\n- ST7-FD 43 tr -0.149R. Mine: narrow -0.149, LR8 -0.165.\n- RW3-FD 176 tr +0.175R. Mine: narrow +0.175, LR8 +0.151.\n- RW5-FD +0.109R. Mine: LR8 +0.078.\n- L3 +0.200R. Mine: LR8 +0.191.\n\nThe ST7 REVIEW (research/st7_review_1120/REVIEW.md) gives -0.174 for 42 trades through 11-19. That is the LR8 figure and I reproduce it. So the owner sees two bases for the pending ST7-MOVE decision. The 11-20 week numbers (+4.11R, 11-20 +3.00R) are post-11-12 and are not affected.",
   "fix": "In live_trades, select `*`, or at least add side, target and meta to the SELECT. Add a test that cost_r_lr8 changes a pre-effective row. Make cost_r_lr8 raise, or at least count and warn, on missing columns instead of a silent `continue`. Then re-run footrace (Friday exit/retire review) and the owner-inbox Primary records on LR8, and redo the outsider_1120 headline."
  },
  {
   "finding": "F2: Remedy-Q (a) at 12:30 is labelled 'confirmed (weak)' and built under an owner approval that was conditional on the 1pm theory being true. The 13:00 theory failed on lab CHECK, 12:30 was put in its place, and the Testing-book pooled CHECK, where the copies actually run, is worse.",
   "severity": "major",
   "evidence": "Owner condition: ledger line 244, approved_by: \"Double check the no new trades after 1pm theory ... If all is true, remedy-q yes\".\n\nverdicts.json:\n- a_cut_1300 = 'not confirmed' (lab CHECK worse for all 3).\n- a_cut_1230 = 'confirmed (weak) ... paired t 1.94 < bar 2.89; Testing book mixed (L3 -0.0078)'.\n\nlab_cutoff_sweep.csv:\n- Rows 55, 68 and 81 (Primary book, CHECK, cut_1230): copy avg is still negative, -0.0586 / -0.0415 / -0.0476.\n- Row 198, pooled testing CHECK cut_1230: d_avg -0.0017, excess_vs_random -14.57, so worse than the parents. The verdict only mentions L3.\n\nMitigation: ledger metrics_at_approval.note does say 'NOT the multiple-testing bar ... These are live tests, not confirmations'. The fault is the verdict label and the claim that the owner's condition was met, not a hidden number.",
   "fix": "Relabel a_cut_1230 as 'not confirmed: live test copy (Workbench)'. State the pooled Testing-book CHECK result (d_avg -0.0017, excess -14.6R). Tell the owner that the 13:00 condition failed and that 12:30 is a substitute, so the owner can re-confirm."
  },
  {
   "finding": "F3: paired_day_t, the significance statistic quoted for Remedy-Q, compares day totals. In a losing book, removing trades lifts the totals, so the t rises even when per-trade quality falls.",
   "severity": "minor",
   "evidence": "research/remedyq_1120/common.py:38-46 takes (alt - base) of day R sums.\n\nlab_cutoff_sweep.csv:\n- Row 44, pooled Primary FIT cut_1300: d_avg -0.0035 (worse per trade) but t_paired 2.79.\n- Row 47, cut_1330: t_paired 3.84.\n- Row 198, Testing CHECK cut_1230: d_avg -0.0017 but t_paired +1.35.\n\nSo the 1.94 quoted in ledger metrics_at_approval does not test timing skill. I rate this minor rather than major because 1.94 was already below the 2.89 bar and the decision did not rest on it.",
   "fix": "Report excess_vs_random with a bootstrap or permutation p (random removal of the same count per day) as the significance test, or a per-trade day-clustered difference. Use those, not paired day totals, against the bar."
  },
  {
   "finding": "F4: the Remedy-Q live sweep was committed during the 11-20 session but labels its window '2026-10-12..2026-11-20'.",
   "severity": "minor",
   "evidence": "`git log -- research/remedyq_1120/verdicts.json` gives 4f05fcace at 2026-11-20 19:53 UTC (14:53 ET), before the close.\n\nverdicts.json live.window = '2026-10-12..2026-11-20', trades 825.\n\nPrimary trio trades on 11-20 kept closing after 19:53 UTC (journal rows 1412-1429, exits up to 20:55 UTC). The conclusions do not change.",
   "fix": "Label the window '..11-20 (partial, to 14:53 ET)' or re-run after the close."
  },
  {
   "finding": "F5: verdicts.json lab metadata disagrees with lab_meta.json, so the verdict and the CSVs come from different lab runs.",
   "severity": "minor",
   "evidence": "verdicts.json lab: signals 55030, fit_sessions 169, check_sessions 274.\n\nlab_meta.json: n_signals 55029, sessions fit 170 / check 276. lab_meta.json is written by lab_tod.py:157.\n\nThe ledger metrics_at_approval quotes 55030.",
   "fix": "Re-run lab_tod.py once and regenerate verdicts.json and the ledger metrics from that one run."
  },
  {
   "finding": "F6: verdicts.json and the ledger notes date BRAKE-BURST to 11-20 inside the live window, but the ledger has it effective 2026-11-23.",
   "severity": "minor",
   "evidence": "Ledger line 241, id 2026-11-23-brake-burst: date 2026-11-20, effective 2026-11-23.\n\nverdicts.json rule_changes_in_live_window and ledger line 244 notes: 'stop rounding and BRAKE-BURST 11-20'.",
   "fix": "Change the text to 'BRAKE-BURST approved 11-20, effective 11-23 (outside the window)'."
  },
  {
   "finding": "F7: '13:05 / 13:15 worse than 13:00 live' does not hold per setup for Primary L3.",
   "severity": "minor",
   "evidence": "live_cutoff_sweep.csv, primary L3: 1300 tot 37.04 (n 166) vs 1315 tot 37.45 (n 168). Pooled it does hold (154.31 vs 147.31).",
   "fix": "Qualify the claim as pooled / all accounts."
  },
  {
   "finding": "F8: the ST7 REVIEW 'Since TEAM-6' line includes partial 11-20 trades, while its section header says 'through 11-19'.",
   "severity": "minor",
   "evidence": "research/st7_review_1120/REVIEW.md:135 header 'through 11-19, LR8'. Line 144: 'L3 +34.5R, RW3 -4.5R, RW5 -6.4R, ST7 -9.4R'.\n\nMy Primary LR8 figures since 11-11:\n- Through 11-19: L3 +32.90, RW3 -6.28, RW5 -7.11, ST7 -9.45.\n- Adding 11-20 trades exited by about 17:47 UTC: L3 +34.54, RW3 -4.52, RW5 -6.43. These match the line.\n\nST7's own -9.45 is unaffected.",
   "fix": "Use the through-11-19 figures (+32.9 / -6.3 / -7.1)."
  },
  {
   "finding": "F9: the latepb REPORT quotes the live record on the booked basis instead of LR8 (rule 32).",
   "severity": "minor",
   "evidence": "research/workbench/latepb_1120/REPORT.md:41,45 ('live journal +0.208') and :132 ('Live is +0.21R over 17 trades').\n\nMy recompute for GEN-261027-01 (Gen + Testing E, through 11-19), 17 trades:\n- mean r_multiple: 0.208\n- pnl_adj / risk: 0.201\n- cost_r_lr8 with SELECT *: 0.179\n\nThe conclusion is unchanged.",
   "fix": "Quote +0.179 (LR8), and the replay comparison on the same basis."
  },
  {
   "finding": "F10: the Remedy-Q lab CHECK window (2025-10-01..2026-11-04) contains the live sessions from 10-12 to 11-04 that produced the after-1pm hypothesis. This is not disclosed as a contamination caveat.",
   "severity": "minor",
   "evidence": "research/remedyq_1120/lab_tod.py:2,5 set CHECK = 2025-10-01..2026-11-04. The locked block is correctly excluded: no_locked asserts at :34 and :50, and the QQQ filter is at :44.\n\nThe hypothesis came from live data from 10-12 on (verdicts prior_research: whatworks_1120 P5, crunch w7). The ledger notes mention only that 'the afternoon weakness is recent (Oct-Nov 2026)'.",
   "fix": "Add the caveat, or report CHECK with and without 2026-10-01..11-04."
  }
 ],
 "rejected": [
  "None of the 10 reported findings was refuted. All reproduce.",
  "F3 is kept but downgraded from major to minor. The bias is real (FIT cut_1300: d_avg -0.0035 but t_paired 2.79), but the quoted t of 1.94 was already below the 2.89 bar and was disclosed as failing it, so no decision rested on it.",
  "F2 is kept as major with a mitigation noted. Ledger metrics_at_approval.note does disclose 't 1.94 < 2.89 ... live tests, not confirmations'. What is wrong is the 'confirmed (weak)' label, the claim that the owner's '1pm theory true' condition was met, and leaving out the pooled Testing-book CHECK result (d_avg -0.0017, excess -14.57R)."
 ]
}
```
