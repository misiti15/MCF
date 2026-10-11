# Entry cutoff study: 15:00 vs 15:15 vs 15:30 (BDI "EC", 2026-10-11)

*Educational only - not financial advice. Lab results on history only; nothing here is a live or paper result.*

Owner question (2026-10-11): "Are both trading accounts meant to run only through 3pm? A 3:15 stop might still be worth
it." Today no lab/heat setup can enter after the 15:00 bar close (lab frames stop at 15:00; live code caps every window
at `min(1500, hi)` in mcf/strategies/setups.py), and every position is flattened at 15:55. Entries after 15:00 have never
been tested.

## 0. Pre-declaration (written 2026-10-11 BEFORE any trade after 15:00 was scored)

### 0.1 Data
- Open two-year history only (research/history2y, 2024-10-01..2026-10-07 minus the rule-19 locked block
  2024-11-01..2025-02-28). `MCF_HIST_ALLOW_LOCKED` is never set.
- **Late frames** (`build_late.py`): one pass over data/cache_hist/1Min, one process. Locked-block rows are dropped at
  load, before any computation (as research/bdi/timeofday/build_open.py). Per symbol: 5-minute resample, the SAME code
  path as mcf/research/setup_lab.build (heat_frame + extra_features + _outcomes_asym for t1s1/t05s1/t1s05, R = 0.25 x
  daily ATR, exits by the 15:55 bar close, 1c/side lab cost), point-in-time adv20 as build_frames.daily_table; the only
  change is the decision-bar filter: rows with bar close 15:05..15:30 are kept (written to data/late/), rows <= 15:00
  come from the existing frames unchanged. The RW6G1 VWAP +2 SD band guard is computed for 15:05..15:30 by the module's
  own vwap_band_block on full-day 5-minute bars (rows <= 15:00 use research/bdi/timeofday/data/block, as verify.py).
- **Warm-up exclusion:** because locked rows are dropped at load, the first sessions after the block see a prior day of
  2024-10-31 (gap, prior-day levels, 14-day ATR, adv20). The first 20 open sessions after the block (2025-03-03 ..
  2025-03-28) are excluded from EVERY bucket of this study (406 of 426 sessions remain), so all buckets compare on
  the same sessions.
- **Identity check (before scoring):** for >= 8 symbols, the late builder's own rows <= 15:00 (all 59 columns) must
  equal the stored history2y frames on months outside the warm-up (exact or float32-equal), and the <= 15:00 trades of
  a few setups (MF5, NS4, exhaustion_short, ST1-FD, RW6G1-FD) on the combined frame must equal the trades on the stored
  frames (verify.json / rescore n).

### 0.2 Setups (35)
- Primary, only setups whose window already ends at 15:00: exhaustion_short [1300,1500], MF5-flowsell-vwapup-rsi5hi
  [950,1500], NS4-pm-vwap-reclaim-oversold-short [1130,1500] (run as their -FD module & their own window: verify.json
  proves FD mask & source window == source mask). Heat setups and the other primary lab setups end before 15:00 and are
  not affected by a cutoff change.
- Testing: all 32 -FD setups of config/account_testing.yaml (30 lab + heat_fade_short-FD / heat_fade_long-FD), window
  [950,1500]. Heat FD scores carry their window inside regime_score(950, 1500); for the extension the copy is executed
  with 1530 in place of 1500 (in memory; modules not edited).
- Each keeps min_adv (point-in-time adv20), side, exit geometry and every non-time condition. prefilters are live
  speed-ups not applied by the lab (as verify.py / timeofday).

### 0.3 Trade sets (entry = bar close ET; one trade per symbol-day per setup = the first qualifying bar, as live)
- `current`: the setup's window [lo, 1500] (= rescore / verify.json numbers on the 406 sessions).
- `B14`: the `current` trades whose entry is 14:05-15:00 (tod 1405..1500) - the existing last hour of the book.
- `L1` (15:00-15:15): window [lo, 1515], trades with entry tod 1505..1515 - the INCREMENTAL trades (symbol-days that
  had no qualifying bar by 15:00). This is exactly what moving the cutoff to 15:15 adds.
- `L2` (15:15-15:30): window [lo, 1530], trades with entry tod 1520..1530 (incremental on [lo, 1515]).
- `ext1515` = current + L1, `ext1530` = current + L1 + L2 (the extended setups as a whole).

### 0.4 Metrics (per setup x set; production costs incl. time-of-day entry costs, gates.lab_trades/prod_r)
n, n/day, win rate, exp R, day-clustered t, ex-best-day exp, up / down session exp (n) (gates.regime_split),
walk-forward positive share (gates.walk_forward, 3-month train / 1-month test, folds with n >= 10), exit mix (share
of trades that hit target, stop, or the 15:55 time exit; derived from win and lab R as in prod_r). Differences
L1 - B14 and L1 - current with a session-clustered SE (trades of both sets, per-session sums, paired by session).

### 0.5 Pooled book view (the owner's question)
- `pool_FD`: all 32 Testing -FD setups' trades concatenated per set (current, B14, L1, L2), day-clustered by session.
- `pool_FD_dedup`: the same, keeping only late (L1/L2) trades on symbol-days where no FD setup had an entry earlier
  that day (a conservative proxy for one-position-per-symbol).
- `pool_primary`: the 3 primary setups.

### 0.6 Configurations counted
35 setups x 2 extensions (to 15:15, to 15:30) = 70 per-setup configurations, + 2 pooled-FD + 2 pooled-FD-dedup +
2 pooled-primary = **76 configurations**. Try-count bar for this study: t >= max(1.5, sqrt(2 ln 76)) = 2.94.
Nothing is fitted: 15:15 and 15:30 are the owner's candidates, the buckets are fixed here.

### 0.7 Decision rules (declared before scoring)
- **Primary** (gates required, rule 19): a primary setup's window may be extended only if `ext1515` (or `ext1530`)
  passes gates.verdict == keep with N = the lineage's tries (rescore TRIES) + 76, AND its L-bucket alone has exp > 0.
  A setup that already fails the gates on its current window cannot pass by adding 15 minutes; then the verdict is
  "no change" regardless of the late bucket.
- **Testing** (owner-directed, lower bar; the account is a forward test of the full-day versions):
  - Book level: extend every Testing -FD window to [950, 1515] if pool_FD L1 has exp > 0 with day-clustered t >= 2.0,
    exp > 0 in up AND down sessions, walk-forward share >= 0.6, AND pool_FD_dedup L1 exp > 0. Likewise 15:30 for L2
    (both L1 and L2 must pass to go to 15:30).
  - "Not worse" (information only, not a reason to extend): L1 exp >= the book's current exp and L1 - current
    difference t > -1. If the late bucket is not worse than what the book already trades, the owner may still choose
    to extend for data collection; this is reported but the study's verdict follows the rule above.
  - Per setup: extend one -FD setup's window to 15:15 only if its L1 has n >= 30, exp > 0, day-clustered t >= 2.94
    (try-count bar), exp > 0 in up and down sessions (n >= 10 each) and walk-forward share >= 0.6 (folds with n >= 10;
    if fewer than 3 such folds, not met).
- Any extension also needs a code change (the `min(1500, hi)` cap in LabStrategy/HeatStrategy and the heat FD
  formulas' 1500), so it is a setup change: backlog first (rule 16), merged after the close, ledger entry.
- Report the 15:55-flatten share of late trades (a 15:15 entry has at most 40 minutes to reach target/stop).

## Results
(filled in after scoring - see below)
