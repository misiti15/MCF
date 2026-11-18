Educational only — not financial advice

# U9 — Stop wasting short signals and rejects (pre-registration, 2026-11-18, market hours, research only)

Item 9 of the approved USAGE PLAN. Nothing in config/code/runtime is changed; the fix is a patch file only
(`fix.patch`), for an after-hours owner decision. Written before any what-if was scored. Descriptive counts
(reason tallies) were looked at before this plan; no R was computed before it.

## Data
- Live journals (`journal.db`, table `signals` / `trades`) of every `mcf-data*` state branch, run as journaled live
  (no replay). Sessions 2026-10-06..2026-11-18 for counts; what-ifs on 10-06..11-17 (11-18 is still in session).
- 1-minute SIP bars (Alpaca market data, GET only, keys from env, never printed) of the symbol-days involved.
- Borrow flags: `mcf-data-borrow` 09:08 ET snapshots (2026-11-04, 2026-11-05) and one read-only GET /v2/assets
  taken today at ~13:15 ET. Locked block 2024-11-01..2025-02-28 never read (no date before 2026-10-06 is touched).

## Questions (descriptive, no verdict)
- Q1 Count every avoidable skip/reject: `not shortable/ETB`, broker `take_profit.limit_price must be ...`
  (target already passed at the broker's price), `stop_loss.stop_price must be ...`, `price already through
  target/stop`, `insufficient buying power`; per account, per setup, unique (account, day, setup, symbol).
- Q2 Mechanism: does an ETB skip take a slot / the "next candidate" from a borrowable name? (Code path in
  `mcf/execution/runner.py` + count of ETB skips in setups that select by a universe rank cap.)
- Q3 Flag stability: do the 09:08 pre-open flags predict every live ETB skip (and never block a short that was
  traded)? If yes, a pre-open list is enough; if names flip intraday, a periodic refresh is needed.

## What-ifs (scored; each counts as one configuration)
Engine (same for all): entry at the journaled ref_price (signal bar close) with LR8 costs (entry 1 bp + $0.01;
stop exit + 1 bp + $0.01 + max($0.02, 4 bp); target exit at the limit; flat at 15:55 1 bp + $0.01 + max($0.01, 1 bp)),
the signal's own stop and target, walked on 1-minute bars from the minute after the signal; stop and target in one
bar = stop. Setup-specific trailing / time stops are NOT modelled (stated as a limit of the estimate).
- W1 "ETB as if borrowable": first ETB skip per (account, day, setup, symbol). Reported against (i) the same setups'
  submitted shorts (first per account/day/setup/symbol) through the SAME engine, (ii) 5 random entry minutes per
  skipped signal (same symbol-day, same side, same stop distance in % of price, same target multiple; minutes drawn
  inside 09:50..15:00), (iii) per setup, avg R w/o best day and best-day share. This is R that cannot be recovered
  on Alpaca (it does not short hard-to-borrow names); it measures the gap between research records (which include
  these names) and what live can trade.
- W2 "target already passed" (broker take_profit reject):
  - B1 clean skip: pre-check the quote, skip with a clear reason (R = 0, same as today's reject).
  - B2 re-anchor: enter at the broker's base_price (from the reject) + LR8 entry cost, stop and target shifted by
    (base_price - ref_price) so the R geometry is unchanged.
  Fit = sessions <= 2026-10-22, check = sessions >= 2026-10-23 (verdict on check only).
  B2 passes only if on check: mean R > 0, t >= bar, avg R w/o best day > 0, best-day share < 50%, n >= 20,
  and it beats random entries (5 random minutes per signal, same geometry) on the same signals.

Configurations scored: 3 (W1, B1, B2). Bar t >= max(1.5, sqrt(2 ln 3) = 1.48) = 1.50.
Report per setup: how many setups improve / get worse and by how much.

## Fixes (patch only, not committed to the code tree)
(a) ETB: one bulk GET /v2/assets at job start (+ refresh every `shorts.borrow_refresh_min`) fills the broker's
    shortable cache for every symbol; short-only setups skip non-ETB names before they draw a signal (one journal
    line per setup/symbol/day instead of one per bar); can_short falls back to the per-symbol GET as today.
(b) Target passed: after the live quote is read, skip a signal whose entry-side quote is already at/through the
    target (clean reason, no broker call). B2 re-anchor ships only if it passes the check above.

Decision codes: U9-ETB, U9-TGT (proposals; the owner decides after hours; promotion hold is unaffected).
