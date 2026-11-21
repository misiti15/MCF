# QA: merged changes, PRs #236-#239

Scope: I read the code and config changes from #236 to #239 at HEAD a1266f32d. The code and config there are the same as the default branch `claude/intraday-trading-system-witis4`; #240 after it only adds research files, a post and decisions.json.

- #236 and #237 change research files and the owner inbox only. No runtime change.
- #238 carries the runtime changes: runner burst brake, watchdog.yml, PROTECTED.md, robust.py, footrace.py, beginner_setups.py, the BEG and Remedy-Q account configs, and assignments.json.
- #239 carries the Friday review: 12 FOOTRACE-EXIT moves and 12 RETIRE-R3 retirements.

**Result:** the code and config match their ledger entries, and no setup is enabled in two accounts. Two problems stand out:
- **Watchdog (major):** GitHub has hardly run it during market hours since 11-05, so turning on "act" mode protects almost nothing.
- **Ledger check (major):** `python -m mcf.research.ledger check` could not be run here and has been open since 11-12.

There is also one small runner gap (BEG-GNG loses its 12:00 exit after a restart). The 2 test failures happen only because today is a Saturday.

## Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Full test suite | PASS (2 failures depend on the date) | Run in a scratch copy: `pytest -q` gives 913 passed, 2 failed, 1 skipped. Both failures are in `tests/test_hk_flat_1113.py` (`test_successor_needed_when_the_job_stops_before_1550`, `test_late_start_window_is_flatten_only`). They call `at("15:27")` with no date, which resolves to today, 2026-11-21, a Saturday. `handover.decide_trade` then returns "none" because of its `weekday()>=5` check. Neither file was changed in #236-#239. |
| 2 | `python -m mcf.research.ledger check` | FAIL (could not run) | It crashes at `mcf/research/ledger.py:75` with `IndexError` because `data/cache/1Min` is empty, so there are no bars. No `research/ledger_check.json` exists. `OPEN_ITEMS.md:210` (LEDGER-CHK-1111, open since 11-12) says ledger checks have been timing out since 11-12. None of the 11-23 entries has been re-checked as RESEARCH_RULES rule 12 requires. |
| 3 | Ledger entries are well-formed | PASS | All lines parse. These 11-23 entries have id, effective, patch, approved_by and owner_approval: beg1120, ww-protect, ww-cluster, brake-burst, brake-watchdog, remedyq, friday-review. brake-burst also carries `protected_ids` [PROT-23] and guard_evidence. |
| 4 | BRAKE-BURST config: 30 entries / 10 min in every account | PASS | Loaded every account config for 11-23. All 10 resolve to `burst_max_entries 30, burst_window_min 10` (`config/default.yaml:619-625`). No account file overrides it. |
| 5 | Brake logic | PASS | `runner.py` `_enter`: the check comes after the 09:50 gate and the mismatch check, and before the short/ETB and risk checks. It skips once the count reaches 30 within the 10-minute window, per setup, and logs "burst brake" with the count. Skipped signals do not count toward the window (`_burst_note` is only called from `_entered`). The window is rebuilt from today's journaled submitted/dry_run rows using the journal's `ts` column, which holds isoformat timestamps with the time zone. |
| 6 | Brake does not block exits | PASS | `_enter` is only called from `_step` (`runner.py` 1307, 1331, 1334). `manage`, `scale_outs` and flatten never go through it. |
| 7 | Remedy-Q copies: [950,1230] window wired | PASS | Built the strategies for 11-23: the L3 copy is a LabStrategy in testingf with window [950,1230] and refire True. The RW3 copy is in testing2 and the RW5 copy in explore1, both [950,1230] with refire False, which matches their parents. Live, `LabStrategy.eligible` (`setups.py` ~518) only evaluates 5-minute buckets that close by 12:30, and `generate` masks bars ending after 12:30 (`tod` is the bar end time, `heat.py:75`). Each copy block is identical to its parent in `default.yaml` except the window. Parents are unchanged and enabled only in Primary. Each copy is first in its account's setup_order. |
| 8 | BEG-ORB / BEG-GNG match ledger 2026-11-23-beg1120 | PASS | Config parameters match the ledger: BEG-ORB has rank 20, rvol 2, $10, $20M, ATR 0.5, 2R, order until 11:30, breakeven at 1R. BEG-GNG has 1R trail after +1R. Code: the BEG-ORB signal is at 09:49 with `entry_valid_bars=100`, which runs to 11:29; its stop is the far side of OR15. BEG-GNG arms each bar using bars before it only (`arm()` slices `[:k]`), so I found no look-ahead. Each is enabled in exactly one account: BEG-ORB in testingf, BEG-GNG in explore1. |
| 9 | Promotion = move: nothing enabled in two accounts | PASS | Union of enabled setups across the 10 accounts at asof 11-23 has 0 duplicates. The 12 setups moved to the Graveyard are disabled at their source accounts. |
| 10 | Friday review: moved blocks copied faithfully | PASS | Each Graveyard block equals its pre-review source block. The exception is the PDL-1a R2A legs, which drop `live_scale_out` and `scale_out_cap_exempt`, as the ledger rule says. `intraday_momentum`'s effective config is identical. |
| 11 | FOOTRACE-EXIT and RETIRE-R3 re-derived independently | PASS | Ran `footrace.build` on the pre-review configs (275219e23^) with 11-20 arena_reps and `live_trades()` (29,564 trades through 11-20). exit_review gives the same 12 setups as the ledger's `moves`. retire_review gives the same 12 as `retired`. Archive candidates are MF1, heat_fade_long and NS3, all of which are retired instead, so the "archive 0" decision is correct. 20 other setups meet the RETIRE-R3 thresholds, but each is either disabled in every config or one of the two Compass exemptions (CWT14-orl-p05-long, heat_fade_short-FD). |
| 12 | RETIRE-R3 numbers | PASS | Recomputed examples: MF2 has 26 days, 217 trades, w/o best day -0.358, last 10 sessions -78.4R. exhaustion_short has 26 days, 158 trades, -0.109, -1.17R. NS3 has last 10 sessions -0.01R, matching the ledger's "-0.008, by a hair". |
| 13 | assignments.json regenerated | PASS | `python -m mcf.report.assignments --asof 2026-11-23` in a scratch copy gives a file identical to the committed one (0 differences in accounts, setups and labels). It includes the 5 new setups, stamped 2026-11-20 16:05 ET, and the 24 Friday changes, stamped 16:55 ET. |
| 14 | Setup-freeze timing | PASS | #238 merged 2026-11-20 16:18 ET and #239 at 17:11 ET. #236 (19:01 ET 11-19) and #237 (09:11 ET 11-20) change research files only. |
| 15 | BRAKE-WATCHDOG mode actually "act" | PASS | `gh run view 44854206616`, the 11-21 02:08Z scheduled run, shows `MCF_WATCHDOG_MODE: act` in all 10 matrix accounts, so the repo variable does not override it. The 11-20 21:01Z run before the merge showed Primary act and the others dry. |
| 16 | BRAKE-WATCHDOG premise ("already runs every 10 min") | FAIL | `gh run list --workflow watchdog.yml -L 200`: watchdog runs inside 09:35-16:05 ET per weekday were 8-9 a day from 10-27 to 11-03, 4 on 11-04, at most 1 a day from 11-05, and **0 on 11-16, 11-17, 11-18 and 11-19**. On 11-20 the single run was at 16:01 ET. The cron line `5-55/10 13-21 * * 1-5` is not being honoured by GitHub. |
| 17 | PROTECTED.md / WW-CLUSTER | PASS | PROT-23 now lists the `live.burst_*` keys (`docs/PROTECTED.md:61`). `robust.wo_top_days` and footrace `wo2` agree, both giving None when there are 2 or fewer days. `day_t` gives the same result as before. |

## Findings

1. **Major: the watchdog barely runs during market hours, so the BRAKE-WATCHDOG approval rests on a false premise.**
   - Ledger `2026-11-23-brake-watchdog` and the owner's approval ("YES if low usage") say the watchdog "already runs every 10 min in all 10 accounts".
   - GitHub has fired it at most once per session since 11-05, and not at all on 11-16 to 11-19. The 11-20 run was at 16:01 ET.
   - Switching to "act" does not cause wrong behaviour. But Primary's LR7 protection and the new all-account protection are effectively missing for dead runs, stale data and failed flattens.
   - The brake REPORT itself (`research/whatworks_1120/brake/REPORT.md:131`) asked for the dry logs to be checked before the switch. I found no record that this was done.
   - The owner should be told before relying on it. One fix is to dispatch the watchdog from the trade job, as is already done for the hunch and trade jobs.

2. **Major (process): the ledger check required by CLAUDE.md and RESEARCH_RULES rule 12 has not been run for any 11-23 entry.**
   - The rule is that every approved change is re-checked with `python -m mcf.research.ledger check`.
   - It cannot run in this environment (no bar cache; `ledger.py:75` crashes with IndexError instead of a clear message). LEDGER-CHK-1111 has been open since 11-12.
   - Even if it ran, the tool could not test these entries:
     - `revert()` replays default.yaml, which is Primary only.
     - Patch keys like `"strategies.X (testingf)"` and `"live.setup_order (...)": ["...", ...]` cannot be reverted meaningfully.
     - The Backtester does not implement the burst brake, so BRAKE-BURST cannot be evaluated by it.

3. **Minor: BEG-GNG loses its 12:00 time exit after a runner restart.**
   - The 12:00 exit is carried only on the signal: `time_stop_min` is computed per signal in `beginner_setups.py` (`BegGapAndGo.generate`). The runner does not act on `exit_by`.
   - `_restore_management` and `_restore_lot_management` (`runner.py` ~480-525) re-arm from `st.params`, where BEG-GNG has no `time_stop_min`. After a crash or restart between entry (09:50-10:59) and 12:00, the position holds to 15:55 unless the trail, target or stop closes it first.
   - Normal handovers (~14:10 ET) come after 12:00, so the risk is small.

4. **Minor: two tests fail on weekends.**
   - The failing tests in `tests/test_hk_flat_1113.py` build times with `at("15:27")`, which takes today's date. They fail on any Saturday or Sunday, so a weekend CI or merge run would wrongly show red.
   - The fix is to pin a weekday date. This problem was there before #236-#239.

5. **Minor (disclosure, not an error): the L3 Remedy-Q copy runs under Testing account rules.** The ledger's own figure under those rules is -0.0078R per trade, worse than without the cut; the "agree in sign" case is under Primary rules. This is disclosed in `setups.stats`, but reviews of the copy should keep it in mind.

I found nothing wrong in the burst brake, the Remedy-Q window, the BEG signal logic, promotion = move, the assignments regeneration, or the FOOTRACE-EXIT and RETIRE-R3 selections.

Files are in `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/merged-changes/`:
- `pytest_full.log`
- `accts_1123.json` (enabled setups per account, 11-23)
- `live_trades.csv`
- `wd_runs.txt` (watchdog run times)
- `scripts/accts.py`

Educational only — not financial advice.

## Verifier

```json
{
 "confirmed": [
  {
   "finding": "Major: the BRAKE-WATCHDOG approval rests on a false premise. The ledger says the watchdog 'already runs every 10 min in all 10 accounts', but GitHub has barely run it during market hours since 11-05, so the new 'act' mode gives almost no protection against a dead run, stale data or a failed flatten.",
   "severity": "major",
   "evidence": "I re-ran `gh run list --workflow watchdog.yml -L 400`, which returns all 174 runs back to 10-16, so the run limit hides nothing. Every run is event=schedule. Runs inside 09:35-16:05 ET on weekdays: 11-12 per day from 10-19 to 10-23, 7-9 per day from 10-26 to 11-03, 4 on 11-04, at most 1 per day from 11-05, 0 on 11-09, and 0 on each of 11-16, 11-17, 11-18 and 11-19. On 11-20 the only in-window run was at 21:01Z (16:01 ET). The cron line is `5-55/10 13-21 * * 1-5` (.github/workflows/watchdog.yml:27). The ledger entry (research/ledger.jsonl:242, 2026-11-23-brake-watchdog) has approved_by containing 'the watchdog already runs every 10 min in all 10 accounts'. The brake report (research/whatworks_1120/brake/REPORT.md, Recommendation item 2) asked for 'a few days of watchdog.yml run logs' to be checked before the switch; I found no record that this was done. I also confirmed act mode is really live: `gh run view 44854206616 --log` shows 'MCF_WATCHDOG_MODE: act' 10 times. No trade or other workflow dispatches watchdog.yml; grep finds only comments that mention it.",
   "fix": "Tell the owner before relying on the watchdog. Give it a reliable trigger, for example dispatch watchdog.yml from the trade job or session-guard, as is already done for the hunch and trade jobs. Then correct the ledger note about how often it runs."
  },
  {
   "finding": "Major (process): RESEARCH_RULES rule 12 and CLAUDE.md require every approved change to be re-checked with `python -m mcf.research.ledger check`. This has not been done for any 11-23 entry, the tool crashes with an unclear error when there is no bar cache, and it could not test these entries in a meaningful way even if it ran.",
   "severity": "major",
   "evidence": "data/cache/1Min holds 0 files. At mcf/research/ledger.py:75, `probe = store.load(\"SPY\") if \"SPY\" in syms else store.load(syms[0])` raises IndexError when syms is empty. research/ledger_check.json does not exist. research/owner_inbox/OPEN_ITEMS.md:210 lists LEDGER-CHK-1111 as open since 2026-11-12 with 17 checks pending. (The original report gave the path as OPEN_ITEMS.md at the repo root; the real path is research/owner_inbox/OPEN_ITEMS.md.) On the limits of the tool: `revert()` (ledger.py:43-47) applies the patch to `load_config()` with no account argument, so it replays the Primary config only. Grep finds no 'burst' anywhere in mcf/backtest, so the backtester cannot evaluate BRAKE-BURST.",
   "fix": "Make the check fail with a clear message when there are no bars. Run it where there is a bar cache, for example as a GitHub Actions job. Extend revert() so it can replay per-account configs, or record in each ledger entry which checks cannot be run by this tool."
  },
  {
   "finding": "Minor: after a runner restart, BEG-GNG loses its 12:00 time exit. A restart between entry and 12:00 leaves the position held until 15:55 unless the trail, target or stop closes it first.",
   "severity": "minor",
   "evidence": "The 12:00 exit exists only on the signal. mcf/strategies/beginner_setups.py:198-203 computes time_stop_min per signal from exit_by=1200. The account config block (config/account_explore1.yaml:1105-1122) has trail_r and trail_after_r but no time_stop_min. `_restore_management` and `_restore_lot_management` (mcf/execution/runner.py:464-519) re-arm management from `st.params.get(k)` for k in keys including time_stop_min, so time_stop_min comes back as None. The time stop at runner.py:821 then never fires, and the runner does not act on exit_by.",
   "fix": "Store time_stop_min, or an absolute exit clock time, in the journal or lot state when the position is entered, and restore it from there. Alternatively, have the runner honour exit_by for BEG-GNG."
  },
  {
   "finding": "Minor: two tests in tests/test_hk_flat_1113.py depend on the date. They fail on weekends, so CI or merge checks run on a Saturday or Sunday show red for no real reason. This was already the case before #236-#239.",
   "severity": "minor",
   "evidence": "tests/test_live_ready_lr.py:28 defines `at(s)` as `pd.Timestamp(s, tz=NY)`, so a bare time like 'HH:MM' resolves to today's date. test_hk_flat_1113.py:30 and :122 call `ho.decide_trade(at(\"15:27\")...)` and `at(\"15:40\")`. mcf/execution/handover.py returns 'none' on weekdays >= 5 (lines 87, 107, 147). The log qa/merged-changes/pytest_full.log shows `assert 'none' == 'dispatch'` at lines 30 and 122, with 2 failed, 913 passed, 1 skipped. The last commits to the file are d0d73cb4c and 79d9c9647, both before #236.",
   "fix": "Use a fixed weekday date in these tests, for example at(\"2026-11-13 15:27\")."
  },
  {
   "finding": "Minor (disclosure): the L3 Remedy-Q copy in testingf runs under Testing account rules. The ledger's own figure under those rules is worse than having no cut; the improvement only holds under Primary rules.",
   "severity": "minor",
   "evidence": "The research/ledger.jsonl remedyq entry reads 'lab CHECK (Primary rules) avg -0.0633 -> -0.0586 (+0.005/trade) ... Testing rules -0.0078/trade (worse)'.",
   "fix": "Keep this in mind when the copy is reviewed. No code change is needed."
  }
 ],
 "rejected": []
}
```
