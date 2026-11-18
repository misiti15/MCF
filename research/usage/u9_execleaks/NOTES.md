Educational only — not financial advice

# U9 notes (working log, 2026-11-18, market hours, research only)

- 18:11 UTC: fetched every `mcf-data*` branch; journals copied to scratch (10 accounts: Primary = `mcf-data`, On Deck =
  `testing`, Testing A = `testing2`, B = `explore1`, C = `livelab`, D/E/F = `testingd/e/f`, Gen, Graveyard).
  Descriptive reason tallies first (no R): `not shortable/ETB` is the largest single skip reason (9,237 rows).
- Code read (`mcf/execution/runner.py`): the ETB test runs inside `_enter`, after the setup has drawn and marked
  the signal and BEFORE `risk.check` (position / trade caps). A skipped short never increments trades_today, never
  opens a slot, never blocks another symbol. Every symbol is evaluated on its own each poll, so the "next candidate"
  is already taken. The only way a non-ETB name can take a place is a universe-rank cap (orb / orb20 /
  vwap_pullback top_n by rvol): 8 ETB skips in 32 sessions (orb20_a).
- `AlpacaBroker.can_short` caches the first answer per symbol for the whole job: one per-symbol GET inside the entry
  path the first time each name signals (20,474 account/day/symbol lookups in 32 sessions).
- 18:14: one read-only GET /v2/assets (paper endpoint, keys from env, never printed): 14,430 active, 5,238 ETB.
  `mcf-data-borrow` only holds 09:08 snapshots for 11-04 and 11-05.
- 18:15: PLAN.md committed and pushed (435a4161c) before any R was computed.
- First what-if pass used split-adjusted bars: two names (EFG, SOXX) had a split after the session and gave
  -174R / -80R. Re-fetched raw (unadjusted) bars and added a price-sanity guard (bar close within 3% of ref, else
  dropped; 12 of 5,829 ETB signals dropped, 0 of 223 target rejects). Only the raw-bar results are reported.
- Engine calibration: the same 10,784 submitted shorts through the simplified engine give -0.108R/trade vs -0.119R
  live (journal R). The engine is close to live, slightly kind (no trailing / time stops, no partial fills).
- B1 (pre-registered: "R = 0, same as today's reject") has a side effect I had not written into the plan: the same
  quote test also skips trades that DID fill with the fill-side quote already at/through the target (the
  take-profit then fills at once for <= 1 cent of upside) or the exit-side quote at/through the stop. Measured from
  the live journal (quote in `signals.info`, R from `trades`): 96 + 19 fills. Counted as a 4th configuration
  (stop part), bar t >= max(1.5, sqrt(2 ln 4)) = 1.67.
- The stop part's R is large per trade (-3.0R avg) because R is measured on the FILL-to-stop distance, which is tiny
  when the fill is already at the stop; the dollar loss is small. Reported in R as the rules ask, with this note.
- Tests: ran with `PYTHONPATH=<worktree>` instead of `pip install -e` so the shared container's installed `mcf`
  (other usage items run in parallel) is not re-pointed at this worktree. Same code, same pytest.
- Rule-change context inside the window (research/ledger.jsonl): LR8 live cost model from 2026-11-12 (journal R
  before that uses the flat $0.02 stop slippage; the what-if engine applies LR8 throughout); CWT14 family moved
  Testing 2 -> Graveyard 10-21..10-30 and got live scale-outs from 10-16 (most target rejects are CWT14, 10-13..10-20
  in Testing A, later in Graveyard); account renames + Testing D/E/F from 11-12; TSZ1 testing sizing from 11-17
  (R comparable). None of these changes the borrow test or the bracket validation.
- Full suite, first run: 769 passed, 2 failed (tests/test_quote_record.py). The new check fired before the
  existing spread-to-stop reason on a 1-cent-stop fixture (same skip, different reason). Moved the U9-TGT check after
  the spread / cost checks; the B1 numbers are unchanged (they come from trades that had already passed those checks).
- Full suite after the reorder (scratch worktree, PYTHONPATH): 771 passed, 1 skipped, 0 failed (5 min 35 s).
