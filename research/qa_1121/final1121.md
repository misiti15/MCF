## QA area: final1121 (research/final1121/, 140 configs, nothing passed, FP-A..F)

Scratch: /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/final1121 (live.pkl, live_full.pkl, fullcost.py, fullb/, etf/)

### Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Scripts in research/final1121/scripts are the same as the scratch copies in fp/ | PASS | `diff -rq` shows only extra outputs in fp/ and no differing files |
| 2 | P1 (L3-gap-slope-lowdist-FD) live: 111 trades, +0.237, w/o best day +0.103, best-day share 69% | PASS as computed by the script (but see F1) | I re-ran promo-pipe/load_live.py and primbook.py: 111 / +26.3R / +0.237 / wo1 +0.103 / share 0.69, all trades in `testing`; best day 11-12 = +18.21R |
| 3 | P1 before 11-12 w/o best day -0.042; 6 trades / +1.5R after 11-12 excluding 11-12 | PASS | 73 trades, avg +0.091, wo1 -0.042; after 11-12: 38 trades (32 on 11-12), +1.49R without 11-12 |
| 4 | RW7 +60.1R to +18.1R under the Primary book (w/o best day -0.027) | PASS as computed (but see F1) | primbook.py: raw 872 / +60.1 / wo1 +0.024 / share 0.67; book 607 / +18.1 / wo1 -0.027 |
| 5 | Primary-book rules in primbook.py match config | PASS | config/default.yaml:11 max_positions_per_strategy 30, :17 max_setup_daily_loss_r 2.0 (cost-R for primary, :16), :667 max_lots_per_symbol 3 |
| 6 | FP-B: P1/P2 daily correlation 0.75 | PASS | 0.747 on the union of days, 0.756 on common days |
| 7 | P4 (CWT09-g10) best-day share 48% | PASS | 0.48 (0.49 under full LR8) |
| 8 | C1A1 FIT -12.8R; T2 -2.5R; net -8.2R | PASS | I rebuilt idx_feats/spy_daily from the 1-min caches (identical to fp/ files), then ran grid.py fit,t2: C1A1 FIT dR -12.818 (1 day better / 4 worse), T2 -2.525. -12.8 - 2.5 + 7.1 (CHECK, not re-scored) = -8.2 |
| 9 | ETF-burst base / V30A3 / V25A3 dev numbers | PASS | Base FIT +57.78R (226 lots, t 4.35, wo1 +0.200), T2 -9.17R; V30A3 FIT +3.58 / T2 +14.48; V25A3 +3.79 / +11.64 |
| 10 | Look-ahead in ETF-burst features | PASS | idx.py uses bars with hm < T only; spyd.py atr14p is `.shift()` (prior days only). The rolling window spans the locked gap, which is disclosed |
| 11 | No locked-block (2024-11-01..2025-02-28) reads | PASS | Every 1-min reader filters with pyarrow and asserts: od.py:82-97, score.py:120, cap-etp/build.py:30-38, idx.py, cov-long/eng.py:57/77/96/129, trio gd.py and gd_t2.py:25. The plain pd.read_parquet calls go to cache_fresh, whose files end 2024-09-13 (sampled 24 of 469: all end 2024-09-13). Neighbour CHECK reads (promo-pipe-rob) and the ETF-burst early CHECK print are disclosed and are not locked-block reads |
| 12 | Lab costs applied once (no double count) | PASS | bench10.add_r:371-383, cap-etp/engine.py:170-178 and open-drive/score.py:29-35 each charge tier*(entry+exit)+borrow once against r_gross. book() does not charge again |
| 13 | Config count 128 + 12 = 140 | PASS | 24+19+38+20+21 = 122, + 6 promo reviews = 128, + 12 neighbours = 140. Track files agree (19, 24, 21, 20) |
| 14 | WB2 bars | PASS | sqrt(2 ln 21) = 2.47; range 2.18-2.70 matches N = 11..38 |
| 15 | "All figures are R after costs (LR8)" for live records | FAIL | See F1 |
| 16 | mcf.report.footrace.live_trades gives LR8 basis (as its docstring says) | FAIL | See F2 |
| 17 | "Nothing passed" is not a bug artifact | PASS | No double costs, exits from the 1-min walk, and the book matches config. The only bug found (F1) inflates live records, so it makes "not promotable" stronger, not weaker |

### Findings

**F1 (critical: wrong numbers in the owner decision text, though no decision flips).** promo-pipe/load_live.py does not re-cost rows before 11-12 to LR8 correctly. Its SELECT (load_live.py, the `pd.read_sql` line) leaves out the `exit`, `exit_reason`, `meta` and `target` columns. As a result, `mcf.costs.parts_from_row` returns exit px 0 with an empty reason, and `lot_costs` drops every exit-side cost: the stop 4bp/2c minimum, the market-exit cost and the target price-improvement giveback. Only the entry cost and fees are charged.
- Single-row proof, a P1 target exit on 10-xx: full LR8 cost is $1.34, load_live-style cost is $0.11.
- On average, rows before 11-12 are overstated by +0.045R per trade. Rows on or after 11-12 match exactly.
- Corrected figures (my re-run with `SELECT *` and the same cost_r_lr8):

| Setup | Report figure | Corrected (full LR8) |
|---|---|---|
| P1 | +26.3R / +0.237 / wo1 +0.103 / share 69% | +23.1R / +0.208 / wo1 +0.061 / share 79% (w/o top-2 -0.062) |
| P2 | +16.0R / +0.096 / wo1 +0.022 / share 82% | +13.2R / +0.079 / wo1 -0.000 / share 100% |
| RW7 raw | +60.1R / wo1 +0.024 | +44.5R / wo1 +0.005 / share 90% |
| RW7 Primary book | +18.1R / wo1 -0.027 | +4.4R / wo1 -0.051 |
| P5 GEN | wo1 +0.040 | wo1 +0.026 (share 82%) |
| X1 RW1 (incl. WB3) | +2.3R | -0.9R |

- promo-pipe.md also says "costs average only 0.013R per trade". That figure is also understated.
- The FP-A, FP-C, Rank-1 and "gap to the bar" text all use the inflated numbers. For example, P1 is not "+10R from share < 50%"; it is further away. The direction (do not promote) is unchanged and stronger.

**F2 (major: shared infrastructure, affects other QA areas).** mcf/report/footrace.py:358 `live_trades()` selects no `side`, `exit`, `exit_reason`, `meta` or `target`. Inside `cost_r_lr8`, `row["side"]` raises KeyError, which is swallowed (costs.py:194), so every row before 11-12 silently keeps the booked flat-allowance pnl_adj. The docstring says "r (LR8 basis)", so this is not LR8.
- Proof: footrace gives P1 +25.31R and RW7 +62.02R. These equal the booked basis exactly; full LR8 gives 23.1 and 44.5.
- Any week or setup figure built on `live_trades()` that spans 11-12 mixes cost bases. Other research loaders that call cost_r_lr8 should be checked for the same column omission: research/beginner_1120/BEG-RULES/prep.py:53, giveback_1119/map/load_live.py:17, whatworks_1120/brake/load_trades.py:23, crunch/wave2/*.
- A unit test with a partial-column frame would catch this. Raising an error instead of swallowing the KeyError would be safer.

**F3 (minor, disclosed).** The report header says all figures are LR8. The live tables actually carry the F1 basis, which matches neither the booked basis nor true LR8.

**F4 (minor, disclosed; noting only).** ETF-burst A1 picks the "first lot per group" alphabetically, not in live signal order. The live replay does not add back latch-blocked lots. Neither changes the C1A1 FIT sign: the cut lots are April-2025 bursts.

**Wrongly killed?** None found.
- V30A3 is correctly held at shadow-at-most. Its dev numbers reproduce: 5/5 events improved, T2 +14.5. But its threshold was set with hindsight and its CHECK was contaminated, so FP-D "optional, lean No" is fair.
- Under correct costs, every live candidate (P1, P2, P3, P5, X1) gets weaker. P4 is barely changed (+0.218 / wo1 +0.141).
- The strongest live record in the dataset is L3-gap-slope-fromopen-FD: +75.1R full LR8, wo1 +0.122, share 42%. It is already in Primary, so it is not a candidate.

Educational only — not financial advice.

## Verifier

```json
{
 "confirmed": [
  {
   "finding": "F1: research/final1121/scripts/promo-pipe/load_live.py:13 selects only strategy, symbol, side, date, entry_time, exit_time, entry, stop, shares, pnl, pnl_adj and r_multiple. It leaves out exit, exit_reason, meta and target. So for rows before 11-12, mcf/costs.py parts_from_row (line 146) returns [(shares, 0.0, '')], and lot_costs (line 116) charges only the entry bp, TAF and CAT. It charges no stop cost (4bp or $0.02 minimum), no market-exit cost, no target giveback, and no SEC fee, because the sell price is read as 0. Every live figure in the final1121 decision text is therefore overstated. The direction does not change: nothing gets promoted either way.",
   "severity": "critical (wrong numbers in the owner decision text; no decision flips)",
   "evidence": "Script: /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/qa/final1121-verify/run.py. It loads every journal with SELECT * and runs cost_r_lr8 three ways: on the full frame, on the load_live column subset, and on the footrace column subset. Across all rows before 11-12, the load_live subset minus the full frame is +0.0450R per trade. Rows on or after 11-12 differ by at most 0.0. My numbers, load_live basis then full LR8 (report figure in brackets): P1 L3-gap-slope-lowdist-FD is 111 trades / +26.34R / +0.237 / wo1 +0.103 / share 0.69 [report: the same] vs +23.06 / +0.208 / wo1 +0.061 / share 0.79, wo2 -0.062. P2 L3-gap-slope-rsi5hi-FD is +16.01 / +0.096 / wo1 +0.022 / share 0.82 vs +13.17 / +0.079 / wo1 -0.000 / share 1.00. RW7-FD raw is +60.1 / wo1 +0.024 vs +44.5 / wo1 +0.005 / share 0.90. RW7 Primary book (primbook.py re-run on each basis) is +18.1 / wo1 -0.027 vs +4.4 / wo1 -0.051, with 602 lots kept instead of 607. P5 GEN-261029-06 has wo1 +0.040 / share 0.75 vs +0.026 / share 0.82. X1 RW1-FD+WB3 is +3.46-1.19 = +2.3R vs +0.31-1.19 = -0.9R. tracks/promo-pipe.md:178 says 'costs average only 0.013R per trade'. That is the load_live basis (P1 cost 0.0127R); under full LR8 it is 0.0422R. REPORT.md:3 says all figures are LR8, which is wrong for the live tables (this is F3).",
   "fix": "Change load_live.py to SELECT * (or add side, exit, exit_reason, meta and target), re-run live_stats.py and primbook.py, and restate the P1, P2, P3/RW7, P5 and X1 rows plus the FP-A, FP-C, Rank-1 and gap-to-bar text. For example, P1's best-day share is 79%, not 69%, so it is further from the share < 50% bar. Restate the 0.013R cost line as about 0.042R."
  },
  {
   "finding": "F2: mcf/report/footrace.py:358 live_trades() selects no side, exit, exit_reason, meta or target. Inside cost_r_lr8, row['side'] raises KeyError, and costs.py:194 catches it with `except (TypeError, ValueError, KeyError): continue`. So every row before 11-12 silently keeps its booked flat-allowance pnl_adj R, even though the docstring promises 'r (LR8 basis)'. This loader feeds the nightly footrace plan: footrace.py:453 calls build(live_trades(...)). Any figure from live_trades() that spans 11-12 is therefore on the booked basis, not LR8.",
   "severity": "major (shared infrastructure; mislabelled cost basis that feeds the footrace plan)",
   "evidence": "run.py: on the footrace column subset, cost_r_lr8 equals cost_r (the booked basis) on 100% of rows (`ft==book all rows: 1.0`). P1 comes out at +25.31R on the footrace basis vs +23.06R full LR8, and RW7 matches the booked basis in the same way. The pre-11-12 mean is -0.1324 on the footrace/booked basis vs -0.1701 full LR8. Partly refuted: the other loaders that F2 asks to be checked are fine. whatworks_1120/brake/load_trades.py:19 uses SELECT *. beginner_1120/BEG-RULES/prep.py:52 uses `select *`. giveback_1119/map/load_live.py selects side, target, exit, exit_reason and meta explicitly. I did not check crunch/wave2.",
   "fix": "Use SELECT * (or the five missing columns) in footrace.live_trades. Make cost_r_lr8 raise, or at least warn, when required columns are missing instead of swallowing the KeyError. Add a unit test that calls cost_r_lr8 with a partial-column frame."
  },
  {
   "finding": "F3: the REPORT.md header says 'All figures are R after costs (LR8)', but the live tables use the F1 partial-cost basis, which matches neither the booked basis nor true LR8.",
   "severity": "minor",
   "evidence": "REPORT.md:3, compared with the F1 numbers above. The load_live basis gives a pre-11-12 mean of -0.1251, the booked basis -0.1324, and full LR8 -0.1701.",
   "fix": "Fixed together with F1."
  }
 ],
 "rejected": [
  "QA side note under 'Wrongly killed?': 'L3-gap-slope-fromopen-FD: +75.1R full LR8, wo1 +0.122, share 42%' does NOT reproduce. On the same deduped journals with full LR8 I get 410 trades / +80.4R / wo1 +0.148 / share 0.39 raw, and 347 / +76.7R / wo1 +0.155 / share 0.40 under the Primary book (primbook.py on r_full). The conclusion (strong record, already in Primary, not a candidate) still holds, but the quoted figures are off.",
  "F2 sub-claim that research/beginner_1120/BEG-RULES/prep.py:53, giveback_1119/map/load_live.py:17 and whatworks_1120/brake/load_trades.py:23 may have the same column omission: refuted. All three select every needed column (SELECT * or an explicit list that includes side, exit, exit_reason, meta and target)."
 ]
}
```
