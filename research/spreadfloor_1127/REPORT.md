Educational only — not financial advice

# SPREADFLOOR-1127: log-only spread-floor shadow logger (BUILT; housekeeping, no trading change)

## Plain summary
- **Built a recorder only.** At each real entry the runner now writes the decision-time quoted spread, the stop
  distance in spreads / bp / cents, and whether a 6- or 8-spread floor WOULD have skipped the trade. It goes into the
  journal (signal info and order meta, key `spreadfloor_shadow`).
- **It changes nothing in trading.** Orders, sizes, entries, exits and skip decisions are the same. The fields are
  written after sizing and nothing reads them. Any error is caught and printed.
- **Why:** stopfloor_1127 found a live lead. Trades with a stop under 6–8 spreads lose more (−0.31 vs −0.18 R) and
  the skip beat random skips live. There is no spread history to backtest that, so evidence has to build up from now on.
- **Tests: 8 new, all pass. Full suite after merging the branch head (incl. AV50): 1062 passed, 1 skipped** (11 min 16 s).
- **Configs scored: 0.** Cumulative N stays ≈ 9,176. PREREG.md fixes the later test now: 2 configs (F6, F8), run at ≥ 20
  and again at 40 logged sessions.
- This is not a setup or exit change. It touches execution code by one guarded call.

## What changed
| File | Change |
|---|---|
| `mcf/execution/spreadfloor.py` | new, pure `fields(bid, ask, ref, stop)` → {quote, spread_c, spread_bps, stop_c, stop_bps, stop_spreads, would_skip_6, would_skip_8} |
| `mcf/execution/runner.py` | +1 call in `_enter` (after sizing, next to the B8 netbeta tag) + `_spreadfloor_tag` (try/except, kill switch `live.spreadfloor_log`, default on) |
| `mcf/report/spreadfloor.py` | new read-only report: per setup n, days, median stop in spreads / bp / cents, would-skip counts and shares at 6 / 8, avg R of would-skip vs kept lots (after costs when the trade row has pnl_adj, else r_multiple) |
| `tests/test_spreadfloor_log.py` | 8 tests (below) |

- Quote source: the quote `_realism` already fetched for that entry. No extra API call.
- Stop used: the journal stop (the R basis, the same as the stopfloor study). When AV50 (effective 2026-11-30) gives a
  burst lot a tighter bracket stop, the tag adds `bracket` with the same fields on the broker stop.
- Entries only: skipped signals, the shadow book and what-if runs are not tagged.
- No quote (bid/ask missing or crossed) → `{"quote": false}`, with no floor verdict.
- Locked quote (spread 0) → stop_spreads null, would_skip false.
- The existing live filter already skips stops under 4 spreads (`max_spread_risk_frac` 0.25). So the logged
  would-skips fall in the 4–6 and 4–8 spread bands.

## No-op proof (reuses the Friday-switches golden, tests/data/friday_switches_noop_golden.json)
The golden scenario runs 12 full `runner.step` polls: 4 symbols, 3 setups, and 12 orders until the −20R halt. It must
produce the same decisions, orders and risk state in each of these cases:
1. Logger on with the golden's empty-info realism. The tag runs at all 12 entries.
2. Logger on with real two-sided quotes (4 / 6.67 / 10 spreads, plus a locked quote). Fields are written on all 12
   journaled entries and the 12 live orders' meta. Skips and shadow-book orders carry no tag.
3. Logger crashing (`fields` raises). The exception is swallowed and printed.
4. Kill switch off. Nothing is written.

Two more tests check the field math and floors (long, short, missing, crossed and locked quotes), the AV50 `bracket` sub-record, and that the tag
touches no other info key (e.g. `cap_qty`). Two report tests check the per-setup summary, would-skip counts and R join,
and the empty-journal case.

## Usage
`python -m mcf.report.spreadfloor data/journal.db [other account journals] --json out.json`

Before reading the numbers, list the rule changes inside the window from research/ledger.jsonl. For example, the
Testing CF (since 10-30) already removes the tightest stops in Testing 1/2, Explore 1 and Live Lab, so those accounts'
tight bins are thinner.

## Finalists / verdict
None scored. Verdict: BUILT. The F6 / F8 evaluation is pre-registered in PREREG.md. It runs once ≥ 20 sessions carry the
tag (first possible session 2026-11-30, after merge outside market hours).
