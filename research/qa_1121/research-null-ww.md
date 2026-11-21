# QA report: research-null-ww (research/whatworks_1120/{null,retire,brake,nmetf} + docs/PROTECTED.md)

Everything ran read-only against the inbox checkout (`git fetch` only; `git status` is clean afterwards). Bars came from read-only Alpaca GETs. Scratch is /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/research-null-ww (87 MB).

**Bottom line:** the null study reproduces exactly, and RETIRE-R3 is implemented as the owner answered. The main error is a bug in `footrace.live_trades()`: for trades before 11-12 its R is on the old flat cost basis, not LR8 as its docstring says. Because of that, the retire and NM-ETF reports label some figures "LR8" that are not.

## Checks

| # | Check | Result | Evidence (mine vs claimed) |
|---|---|---|---|
| 1 | Trade base for the null study | PASS | I rebuilt the trades from the 10 `origin/mcf-data*` journals (run 1, same de-dup, `cost_r_lr8` with side/target/exit/meta columns). Up to 11-19: 28,097 rows and -4,240.7R. 165 setups have ≥10 trades, holding 27,875 trades. Report: 28,097 / -4,241 / 165 / 27,875. |
| 2 | Null re-run on a sample: 9 setups (the Primary 5, heat_fade_long, MF1-945, RW6-ns2, GEN-261027-08), 1,485 trades, fresh SIP bars, the report's own `null.py`/`fetch.py` | PASS | The day-clustered p-values match the CSV to 4 decimals for all 9 setups. These p-values are deterministic. Examples: L3 0.0021, RW3 0.0148, RW5 0.0014, NM-ETF 0.0000, ST7 0.1008, MF1 0.0157. Post-only p: NM-ETF 0.0198, L3 0.5977, RW3 0.9145. n, live_avg, sim_avg, best_share and w/o-best figures are identical. Null means and i.i.d. p differ only in the 3rd decimal (resampling noise). |
| 3 | "32 of 165 beat the ±30 null; only NM-ETF beats the post-only null" | PASS | From `null_results.csv`: `pc_live<0.05` = 32; `pc_post_live<0.05` = 1 (NM-ETF-late-dip-di-long, 0.0198). Other table cells also match: sim 70/81; i.i.d. 41/82 and 55/88; w/o best day 25/29; post sim 11/15; pre sim 99/103; BH q<0.10 18, 69, 34/82. |
| 4 | "13 of 32 live-positive; 21 of the 37 live-positive do not beat" | PARTIAL | 13 and 37 are correct. 37 − 13 = 24, not 21: 21 do not beat the null and 3 are untestable (fewer than 3 days, `pc_live` NaN). The report leaves out those 3. |
| 5 | Primary-5 table, null report | PASS | All cells match the CSV: n, live avg, edge, p clust, w/o-best, best-day share 42/20/83/94%, post p, Primary-only n/live/null/p. |
| 6 | Costs in the null study | PASS | `null.py` `r_after()` reproduces `mcf/costs.lot_costs` from `config/default.yaml` `live_model`: entry 1bp; stop max($0.02, 4bp); flat max($0.01, 1bp); target 0; SEC $20.60/M on sells; TAF 0.000195; CAT 2×0.00005. |
| 7 | Replay agreement | PASS (mostly) | `replay_agreement.json`: match 96.3%, corr 0.30 with outliers, mean gap 0.063 — matches the report. My sample: 97.9% / 0.98. The "median gap 0.002R" and "Pearson 0.957 after dropping outliers" are not in the JSON (its `mae` field is a median absolute gap of 0.017), so I could not verify them. |
| 8 | Locked block 2024-11-01..2025-02-28 never read | PASS | null and retire use only live trades from 10-06 to 11-19 and SIP bars for those dates. brake reads only the journals. No 2024/2025 dates anywhere in the code. |
| 9 | Configuration counts reported | PASS | null: 3 nulls × 2 tests × measures, about 10 p-values per setup, all in the CSV. retire: 25 × 2 = 50 (+1 post-hoc); `retire_eval.csv` has 50 rows. brake: 48 × 6 scopes = 288; `brake_eval.csv` is 288 × 28. |
| 10 | One-big-day check present | PASS | null: `best_share`, `*_wo` columns, "1 day" tags on RW3/RW5. retire: saved R without the largest setup. brake: net w/o best day plus share. NM-ETF: Primary 66% `1 day`. |
| 11 | Retire study tables vs CSV | PASS | All Friday rows match `retire_eval.csv` (e.g. R3 n150 wo-0.10: 28 / 6,138 / 746.2 / -0.122 vs -0.073 / 650.3 / strict 1). Compass-removed variant: 26 / 5,216 / -671.6 / 575.8. Daily rows match: 34 / 855.6; R6 132.0. |
| 12 | My re-run of the retire study (d15 config) | PASS | My copy of `retire_study.py` reproduces the study's d15 result exactly (28, 746.2, -0.122 vs -0.073). |
| 13 | RETIRE rule in code vs owner answer | PASS | `mcf/report/footrace.py:71`: `RETIRE_MIN_SESSIONS, RETIRE_MIN_TRADES, RETIRE_MAX_WO, RETIRE_MAX_LAST10 = 20, 150, -0.10, 0.0`. `retire_flag` (l.198) tests days ≥ 20 AND n ≥ 150 AND wo ≤ -0.10 AND last10 ≤ 0. `retire_review` (l.204) skips anything enabled in Primary and the Compass exemptions. Accounts are the arena plus Graveyard; On Deck is excluded, as rule 39 says. Matches the owner's 11-20 answer, CLAUDE.md:54, RESEARCH_RULES 39 and ledger `2026-11-20-retire-r3`. |
| 14 | The 12 retirements at the 11-20 Friday review | PASS | I ran `retire_review` on the live record to 11-20 with the account membership from commit `275219e23^`. It gives exactly the 12 retired: 11 Graveyard plus exhaustion_short in Testing F; NS3 is borderline at last-10 -0.008. The other 20 setups that meet the thresholds are already off in every account. |
| 15 | Adopted rule (≥20 sessions) tested | FAIL (disclosure) | The study's R3 used days ≥ 15. In R3's 28 Friday retirements, 22 had fewer than 20 days at retirement. My re-run with d_min=20, Friday cadence: 25 retired, 3,764 trades after, 428.1R saved (not 746), -0.114 vs -0.060 kept, **2** strict wrongful kills (not 1). The ledger's `metrics_at_approval` quotes only the d15 numbers. It labels them "(days >= 15)", but the adopted rule was never reported on its own. |
| 16 | `footrace.live_trades()` cost basis | FAIL | `mcf/report/footrace.py:358` does not SELECT `side`, `target`, `exit`, `exit_reason` or `meta`. `cost_r_lr8` (`mcf/costs.py:186-194`) then hits a KeyError on `row["side"]` and silently keeps the flat-basis R. Result to 11-20: `live_trades()` gives -3,703.3R vs -4,443.7R true LR8. Before 11-12 the mean is 0.0377R per trade too high; from 11-12 on the difference is 0. Primary week 11-16..20 is unaffected: +4.11R (11-20 +3.00), matching the claim. |
| 17 | Retire report says "R is after costs on the LR8 basis" | FAIL | The study reads `live_trades.pkl`, which is the flat basis before 11-12 (28,097 rows, -3,500R). The brake and null reports state this correctly. Retire candidates at 11-20 are the same on both bases (12 = 12). |
| 18 | NM-ETF numbers | PARTIAL | Primary slice matches: 15 trades / 6 days / +1.12 / +0.075 / t 1.18 / w/o best +0.034 / 11-17 at 66%. Whole record is on the flat basis but labelled LR8: claimed +7.00 / +0.212 / t 3.50 / best day 11-05 +1.46; true LR8 is +6.54 / +0.198 / t 3.41 / best day 10-22 +1.31 (20%). Pre-Primary: claimed +5.88 / 0.327; LR8 +5.42 / 0.301. Exits: claimed 5 targets / 10 flattens; the journal shows 4 targets / 11 flattens (0 stops is correct). The 25-session window list is correct. |
| 19 | Brake numbers | PASS / minor FAIL | The burst-30-in-10 rows match `brake_eval.csv`: Primary 0 blocked; all accounts 632 blocked / +198.6R / w/o best +85.6 / share 0.57 / 26 vs 10 setups; Gen +141.1, Graveyard +34.5, Testing +22.9. However, the summary says it "fired on 12 days across all accounts"; the CSV shows `days_triggered` = 17 (12 better, 5 worse). The config matches: `config/default.yaml:624-625` `burst_max_entries: 30`, `burst_window_min: 10`, no account overrides; runner.py:1644 enforces it. |
| 20 | PROTECTED.md vs REPORT.md section 2 | PASS | All 32 IDs are present. Text is the same apart from ≥/>= typography. PROT-23 was deliberately updated for BRAKE-BURST, with a note. |
| 21 | Protected config keys and values | PASS | All dotted keys exist with the stated values: spread_risk_frac 0.25, spread_bps 30, flatten 15:55 and lead 5, no_entry 09:50, blackout 4, min_price 5, latch 2.0, halt 20, cap 30, lots 3, burst 30/10. `live.block_twin_same_symbol` is not in default.yaml but defaults to True in risk.py:93 and is set in the account yamls. PROT-06 L3 thresholds match the module and prefilter. |
| 22 | Tests | PASS | `pytest tests/test_protected.py tests/test_ww1120.py`: 21 passed. Ledger entries from 11-21 on: none touch protected items without the required fields. The 11-23-effective entries are dated 11-20, so the gate does not apply to them. |

## Findings

1. **Major — `footrace.live_trades()` returns flat-basis R for pre-11-12 trades while documenting LR8** (`mcf/report/footrace.py:338-370`, `mcf/costs.py:186-194`).
   - The missing journal columns make `cost_r_lr8` fall back silently, so R is 0.038R per trade too high before 11-12. That is +740R across 29,564 trades.
   - Production uses this function for FOOTRACE-EXIT, RETIRE-R3 (`setup_stats` wo_avg_r and last10) and the GY plan, so these rules run on a mixed cost basis and are slightly lax. It changed no candidate on 11-20, but it could later.
   - The QA brief itself names this function as the live-trade source.
   - Fix: add `side, target, exit, exit_reason, meta` to the SELECT. Week and 11-20 Primary R are unaffected because all of it is after 11-12.
2. **Major (disclosure) — the RETIRE rule as adopted (≥20 sessions) was never walk-forward reported.**
   - The evidence and ledger metrics are for days ≥ 15; 22 of that config's 28 retirements happened before day 20.
   - My d20 re-run: 25 retired, 428.1R saved vs 746.2, after-avg -0.114 vs -0.060 kept (it still discriminates), and 2 strict wrongful kills vs 1.
   - The owner's figures (746R saved, 1 wrongful kill) describe a rule that was not adopted.
3. **Minor — "LR8 basis" is mislabelled in `retire/REPORT.md` Method and `nmetf/REPORT.md`.**
   - NM-ETF whole record is +0.212 / t 3.50 / best day 11-05 as reported, against +0.198 / t 3.41 / best day 10-22 on true LR8. The "+0.212 whole record" row of the power table inherits this.
   - Decisions are unaffected because the protocol scores Primary only, which is entirely after 11-12.
4. **Minor — null report "21 of the 37 live-positive setups do not beat".** It should read 24: 21 tested and not beating, plus 3 untestable with fewer than 3 days.
5. **Minor — brake summary "fired on 12 days".** It fired on 17; 12 were better and 5 worse, as the report's own table shows.
6. **Minor — NM-ETF Primary exits.** The report says 5 targets and 10 flattens; the journal shows 4 targets and 11 flattens.
7. **Note, not an error — replay-agreement figures.** "Median gap 0.002R" and "Pearson 0.957 after dropping 15 outliers" are not in `replay_agreement.json`, so I could not verify them. On my 9-setup sample, agreement is 97.9% with corr 0.98, which supports the verdict.

No problems found with:
- look-ahead or locked-block reads;
- costs in the null study;
- configuration counts;
- one-big-day checks;
- the RETIRE implementation thresholds and the Primary exemption;
- PROTECTED.md contents or its tests.

Key files are in /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/research-null-ww:
- `out/null_results.csv` — the sample re-run
- `retire20/retire_eval.csv` — the d15 vs d20 retire re-run
- `build.py` and `retire20/study20.py` — the scripts behind them

## Verifier

```json
{
 "confirmed": [
  {
   "finding": "footrace.live_trades() gives flat-cost-basis R for trades before 11-12, although its docstring says LR8. The cause is a silent KeyError fallback in cost_r_lr8.",
   "severity": "major",
   "evidence": "mcf/report/footrace.py:358-359. The SELECT reads only strategy, symbol, date, entry_time, entry, stop, shares, pnl, pnl_adj and r_multiple. It does not read side, target, exit, exit_reason or meta. At mcf/costs.py:186-194, int(row[\"side\"]) raises KeyError, which `except (TypeError, ValueError, KeyError): continue` catches, so the row keeps the flat cost_r. I re-ran it (scratchpad/qa/verify-null-ww/v.py). live_trades() gives 29,564 trades and -3,703.3R. The same trades read with SELECT * and costed through cost_r_lr8 give -4,443.7R. The whole gap is in trades before 11-12: -2,597.2 vs -3,337.6. The function feeds `footrace build` at footrace.py:453, which drives FOOTRACE-EXIT, RETIRE-R3 and the GY plan. This part of the finding is inference: the bug did not move any candidate on 11-20. The Primary week is unaffected, and I reproduced the claims: +4.11R for the week and +3.00R for 11-20.",
   "fix": "Add side, target, exit, exit_reason and meta to the SELECT in live_trades(), or use SELECT *. Narrow the except in cost_r_lr8 so a missing column raises an error or logs instead of silently keeping the flat R. Then regenerate footrace.json and re-check the retire and FOOTRACE candidates."
  },
  {
   "finding": "RETIRE-R3 as the owner adopted it (active days \u2265 20) was never walk-forward tested or reported. The evidence and the ledger metrics are for days \u2265 15.",
   "severity": "major",
   "evidence": "retire_study.py:48 sets rule_wo_last10 to d_min=15. The 50 configs contain no R3 with d20. R6 uses d20 but adds a t \u2264 -2.5 test. Ledger 2026-11-20-retire-r3 metrics_at_approval quotes the d15 study (28 retired, 1 strict wrongful kill). Its note admits days were raised from 15 to 20 but gives no numbers for that. I re-ran the study script on the same input with an added R3 n150 wo-0.10 d20 config, Friday cadence. d15 reproduces exactly: 28 retired / 746.2R saved / post -0.122 vs kept -0.073 / strict wrongful 1. d20 gives 25 retired / 428.1R saved / post -0.114 vs kept -0.060 / strict wrongful 2. In the d15 kill list, 22 of the 28 retirements had days_at < 20.",
   "fix": "Report the adopted d20 rule's walk-forward numbers in the retire REPORT and in a ledger note: 25 retired, 428R saved, 2 strict wrongful kills. Count it as one more configuration tried (post-hoc)."
  },
  {
   "finding": "The NM-ETF and retire reports label figures as LR8 when they are on the flat basis before 11-12. This follows from the live_trades bug.",
   "severity": "minor",
   "evidence": "nmetf/REPORT.md:29 gives the whole record as 33 trades / +7.00 / +0.212 / best day 11-05 +1.46 (21%). My live_trades() run reproduces that: 7.00 / 0.212 / 11-05 1.46. True LR8 is +6.54 / +0.198 / best day 10-22 +1.31 (20%). By account, Live Lab is 3.26 vs 2.94 and Testing 2 is 2.62 vs 2.48. Primary is identical at 15 trades / +1.12. The protocol scores Primary only, so the decision is unchanged.",
   "fix": "Re-cost the whole-record and pre-Primary rows, and the power-table row at +0.212, once live_trades is fixed."
  },
  {
   "finding": "The NM-ETF report states Primary exits as 5 targets / 10 flattens. The journal shows 4 targets / 11 flattens.",
   "severity": "minor",
   "evidence": "nmetf/REPORT.md:42. From origin/mcf-data journal.db, run 1, NM-ETF-late-dip-di-long up to 11-19: target 4 (11-13 \u00d71, 11-16 \u00d72, 11-17 \u00d71), flatten 11, stop 0.",
   "fix": "Correct it to 4 targets, 11 flattens."
  },
  {
   "finding": "The brake summary says burst-30-in-10 'fired on 12 days across all accounts'. It fired on 17.",
   "severity": "minor",
   "evidence": "brake/REPORT.md:6. brake_eval.csv row burst_30in10m_cool, scope all: days_triggered 17, days_better 12, days_worse 5. The report's own table at line 83 shows 12/5.",
   "fix": "Change it to 'fired on 17 days (12 better, 5 worse)'."
  },
  {
   "finding": "Null report: '21 of the 37 live-positive setups do not beat' leaves out 3 setups that could not be tested.",
   "severity": "minor",
   "evidence": "null/REPORT.md:44. From null_results.csv, 37 setups have live_avg > 0. Of those, 13 have pc_live < 0.05, 21 have pc_live \u2265 0.05, and 3 have pc_live NaN (too few days to test).",
   "fix": "Say that 21 do not beat the null and 3 were untestable."
  }
 ],
 "rejected": [
  "Finding 7 (median gap 0.002R and Pearson 0.957 not in replay_agreement.json) was labelled a note, not an error. It is unverifiable rather than wrong, so I did not keep it as a finding."
 ]
}
```
