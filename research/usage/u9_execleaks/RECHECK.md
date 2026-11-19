Educational only — not financial advice.

# U9-TGT re-check on recorded quotes (pre-registered 2026-11-18, before the first session with the check on)

Owner (2026-11-18): U9-TGT "Yes if the data supports that we are better off to do this." The evidence at approval
(research/usage/u9_execleaks/RESULTS.md) was a journal what-if: target part 96 fills +8.47R (15 setups better +8.98R,
4 worse −0.50R; check t 2.32 vs bar 1.67), stop part 19 fills +56.9R (11 better / 0 worse; large in R only because the
fill-to-stop distance was tiny, small in $). Quotes were recorded only from 11-18, so the approval rests on inferred quotes.

## What is logged from 2026-11-19
- Every skip is journaled `skipped` with reason `target passed at quote (...)` / `stop passed at quote (...)`; its
  `info` JSON carries `u9_skip` (target / stop), `u9_fill_side` or `u9_exit_side` (the quote price that decided it),
  `u9_ref` (the signal reference), plus the usual bid / ask / spread / quote age.
- The quote log (`quote_log_dir`) carries the same decision with `"u9": "target"|"stop"` and the recorded bid / ask /
  sizes / quote timestamp.
- The skipped entries keep their what-if R (journal what-if rows, engine costs) as every other skip does.

## Re-check (once, after the close of 2026-12-03 = 10 recorded-quote sessions 11-19..12-03; 11-26 closed)
1. Count u9 skips per account / setup / part (target, stop) and per session.
2. For each skip: the trade it would have been, from the recorded quote (fill at the recorded ask / bid, the broker
   bracket from there, LR8 costs) — the same path as research/reps2 replay with real quotes.
3. **Keep** if the summed would-have-been R of the skips is <= 0 (skipping gained >= 0R) AND setups better >= setups
   worse; report $ next to R (stop-part R is inflated by tiny stop distances) and avg R w/o the best day.
4. Otherwise propose a revert (or the target part only) to the owner, after hours, with a ledger entry.
Configurations: 1 (no thresholds are tuned at the re-check). Ledger: 2026-11-19-u9-tgt-quote-check (recheck 2026-12-03).
