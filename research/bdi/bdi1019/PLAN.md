# BDI 2026-10-19: index-chase veto family (pre-declared before any history was scored)

*Educational only — not financial advice. Backtest on the open two-year history only; nothing here is a live result.*

Written 2026-10-19 after the close, before entries.py / veto.py were run. Nothing below is changed after results are seen;
any later addition is marked "ADDENDUM (post-result)".

## Inputs
- Ideas: `nightly-1019-index-chase-veto` (skip entries whose side agrees with QQQ's last-60-min move; variant B near the
  index extreme), `gb-1019-post-peak-index-guard` (after 10:30, skip entries against SPY/QQQ's session move).
  `gb-1019-cut-1100-fd`, `gb-1019-noise-floor-stop`, `gb-1019-wide-stop-t05` are NOT tested tonight (stay "idea").
- Setups: every setup that traded live in Primary or Testing 1 in the last 10 sessions (journals on origin/mcf-data and
  origin/mcf-data-testing, 2026-10-06..10-19) and that has a history harness, in its CURRENT config form
  (config/default.yaml enabled lab setups; config/account_testing.yaml enabled lab and heat setups; the demoted
  windowed NS2/NS3/heat_fade_*/exhaustion_short from their default.yaml spec). Windowed T1 variants that traded on a
  single day under the previous overlay and are now replaced by their -FD versions are covered by the -FD version.
  orb20_a: production backtester trades (history2y bt_trades.parquet, entries >= 09:50).
  Excluded: intraday_momentum and the IDX* index-dip setups (they trade the index ETFs themselves, so an index-direction
  veto is definitional for them).
- Harness: the rescore / giveback1019 hist_entries method — history2y 5-min lab frames via `lib.load_month` (open months
  only; the loader refuses 2024-11..2025-02 and scripts assert no date in 2024-11-01..2025-02-28), module mask + YAML
  window + point-in-time adv20 >= min_adv, first qualifying bar per symbol-day, R = 0.25 x daily ATR, production costs
  with time-of-day entry costs (`gates.lab_trades`). Exhaustion's prefilter and refire are not modelled (as rescore).
- Index context: SPY and QQQ 1-minute SIP bars (data/cache_hist/1Min), rows in the locked block dropped on load and
  asserted absent. Decision time = the entry bar's close (bar tod + 5 min); every value uses bars up to that minute only.
  ret_L = index close at decision / index close L minutes earlier - 1 (09:30 open if earlier). fo = close / 09:30 open - 1.
  HOD/LOD = max high / min low of 1-min bars 09:30..decision.
- Splits: train <= 2025-12-31 (2024-10, 2025-03..12), valid 2026-01-01..2026-10-07. No locked-block or holdout scoring tonight.
- Regimes: `lib.regimes()` (universe median open-to-close terciles).

## Configurations (N = 23, pooled across all setups = one book-wide rule each)
A. Chase veto: skip if sign(ret_L) == side and |ret_L| > thr. index {QQQ, SPY} x L {30, 60} x thr {0.0, 0.2, 0.4}% = 12
B. Post-10:30 against-session guard: bar tod >= 1030, skip if sign(fo) == -side and |fo| > thr. index {QQQ, SPY} x thr {0.0, 0.25, 0.5}% = 6
C. Near-extreme: longs with QQQ close within d of its HOD / shorts within d of its LOD. d {0.10, 0.15, 0.25}% = 3
D. Late chase: A with QQQ, L 60, only bars tod >= 1100. thr {0.2, 0.4}% = 2
Total 23. Bar = max(1.5, sqrt(2 ln 23)) = 2.50. (Conservative alternative including the 71 configs of the giveback1019
lineage the guard came from: N 94, bar 3.01 — reported.)

## Metrics
Skipped trades score 0 R. Per config, split, setup and pooled: parent n / win% / avg R; kept n / win% / avg R; share
skipped; delta = mean over parent trades of (veto R - parent R) = total R change per parent trade; day-clustered t of the
daily delta sums; up / flat / down session delta. Random-skip control: skip the same number of trades per setup and
split at random (500 draws); report its mean delta and the share of draws the rule beats. "Excess" = delta minus the
random expectation (vetoed trades' R measured against their setup's split mean), with its day-clustered t.

## Decision rule (pooled; per-setup rows are descriptive)
Testing candidate only if ALL hold: delta > 0 on train and on valid; valid day-t of delta >= 2.50; beats random skip
(excess > 0 on train and valid, valid excess day-t >= 1.65); valid delta > 0 in up AND down sessions.
Per-setup rows: if one were singled out the count becomes 23 x S setups; its bar is sqrt(2 ln(23 S)) and it is reported only.
Otherwise the tested ideas are marked failed in backlog_updates.jsonl with their numbers.

Educational only — not financial advice.

ADDENDUM (pre-result, 2026-10-19, before any veto was scored): mechanical correction of the decision time. The history2y
frame `tod` is the 5-minute bar's CLOSE time (index_ctx.py output matches `lib.load_context` qqq_fo / spy_fo to 1e-7 only
with this alignment), so the decision minute is the frame tod itself, not tod + 5 min. orb20_a (backtester stop entries)
uses the 5-min bar close at or before its fill minute. No configuration changed.
