# BDI direction1020: can the first 30 / 45 / 60 minutes tell us the day's direction, and does tilting the book help?

*Educational only — not financial advice. Backtest on the open two-year history only; nothing here is a live result.*

Written 2026-10-20, before any feature, target or policy was computed or scored. Nothing below changes after results are
seen; any later change is marked "ADDENDUM (post-result)".

Owner question (2026-10-20): "How can we recognise the direction of the market on a given day? Can much be said by the
first 30 / 45 / 60 minutes? ... Maybe Primary always starts neutral and shifts as the day goes on."

Prior work this builds on (not repeated): bdi1016 (day-class gate at 10:00/10:30 that blocks the against-trend side,
84 configs, 0 Primary pass: "the classifier works, the setups do not care enough"), bdi1019 (per-entry index-chase veto,
0/23), giveback1019 (book loses after the peak on the wrong side of the index). What is new here: (A) a direct
measurement of how much rest-of-day / afternoon index direction is predictable from early features, and (B) *size tilts*
(scale up the with-trend side, scale down / skip the against-trend side) instead of pure blocks, with a dynamic
"start neutral, update at each checkpoint" variant and an analytic random-tilt control.

## Data and splits
- SPY, QQQ, IWM, VXX 1-min SIP bars, `data/cache_hist/1Min` (2024-09-16..2026-10-16). Breadth: the lab context table
  (`research/history2y/lib.load_context`: `breadth` = share of the lab universe above its session VWAP at that 5-min bar
  close, `breadth_open` = share above its own open). Previous-day / 5-day trend from the index's own daily closes.
- **Locked block 2024-11-01..2025-02-28 is never read**: rows are dropped on load, scripts assert none survive, the
  context loader refuses those months and `MCF_HIST_ALLOW_LOCKED` must be unset (asserted).
- Train: open sessions <= 2025-12-31. Valid: 2026-01-01..2026-10-16 (Part A) / ..2026-10-07 (Part B, entries end there).
- Session regimes (up / flat / down): `lib.regimes()` (universe median open-to-close terciles). Splitting by regime is
  hindsight (the regime uses the full day) and is reported only descriptively.

## Part A — predictability (descriptive, no tuning)
Checkpoints C: 10:00, 10:15, 10:30, 11:00 (30 / 45 / 60 / 90 min). Price at C = close of the 1-min bar ending at C.
Targets per index: ROD = close(15:59 bar) / P(C) - 1 (rest of day); AFT = close / P(12:00) - 1 (afternoon).
Features at C (all point-in-time, signed so that + = "up" expectation if continuation):
1. `fo` from-open return (09:30 open -> C). 2. `gap` open / previous close - 1. 3. `gapstate`: +sign(gap) if |gap| >= 0.10%
and the gap is not filled by C, -sign(gap) if filled (price traded through previous close), 0 if |gap| < 0.10%.
4. `rpos` range position (P - LOD) / (HOD - LOD) - 0.5 over 09:30..C. 5. `vwap` P / session VWAP - 1.
6. `breadth` - 0.5 at C. 7. `breadth_open` - 0.5 at C. 8. `drive` first-15-min return (09:30->09:45).
9. `drive_cont`: sign(drive) if the move since 09:45 has the same sign as drive (continuation), -sign(drive) if opposite
(reversal) — i.e. the sign of the current from-09:45 leg, labelled by whether it continues or reverses the drive.
10. `prev1` previous session close-to-close. 11. `prev5` 5-session close-to-close to the previous close.
12. `vxx_fo` minus VXX from-open at C (sign flipped: VXX up = risk-off). 13. `comp` composite: mean of sign(fo),
sign(vwap), sign(breadth-0.5), sign(rpos) (no weights fitted).
Grid: 3 indices x 4 checkpoints x 13 features x 2 targets = **312 measurements** (features 2, 10, 11 do not depend on C
but are listed per checkpoint for the table; the count is kept at 312 to be conservative). Bar for a single correlation
t: max(1.5, sqrt(2 ln 312)) = 3.39.
Per cell, train and valid separately: n days, Pearson r (t = r sqrt(n-2)/sqrt(1-r^2), one observation per day so this is
day-clustered), Spearman r, hit rate sign(feature) == sign(target) on days with feature != 0, with a binomial SE, and
the naive baseline "always long" (share of days with target > 0) and "always the majority side of train".
Conditional means: target mean (bp) by train-cut terciles of the feature, with 95% CI (day-level SE).
Asymmetry: continuation rate P(sign ROD == sign fo) for fo > 0 vs fo < 0, and by |fo| bucket (<0.25, 0.25-0.5, 0.5-1,
>1 %); hindsight split by regime.

## Part B — book tilt simulation (pre-declared policies)
Entries: `entries.py` (copied unchanged from bdi1019: every setup that traded live in Primary or Testing 1 in the last
10 sessions, in its current config form, on the history2y 5-min lab frames; R = frame outcome with production costs and
time-of-day entry costs; first bar per symbol-day; orb20_a from the production backtester).
**Decision book = the current Primary setups** (enabled in `config/default.yaml`) that have history entries.
Secondary book = all Primary + Testing 1 entries pooled (same rules, counted as separate configurations).

Each policy produces, per entry, a weight w (1 = unchanged). The book "starts neutral": every entry whose decision bar
(frame tod = 5-min bar close) is before the policy's checkpoint keeps w = 1. For entries at tod >= C the day direction d
in {+1, -1, 0} decided at C sets w: with-trend side (side sign == d) and against-trend side. d = 0 leaves w = 1.

Signals (computed at C from bars closed by C):
- `Q25`: d = sign(QQQ fo) if |QQQ fo| >= 0.25 %, else 0. `Q50`: same with 0.50 %.
- `BR`: d = +1 if breadth >= 0.60, -1 if <= 0.40, else 0.
- `K3`: d = sign if SPY fo, QQQ fo and (breadth - 0.5) all share a sign and |SPY fo| >= 0.20 %, else 0.
Sizing: `M1` with x1.5 / against x0.5; `M2` with x1 / against x0 (skip).
Static grid: 4 signals x 4 checkpoints (10:00, 10:15, 10:30, 11:00) x 2 sizings = 32.
Dynamic ("start neutral, shift during the day"): d re-evaluated at 10:00, 10:30, 11:00, 12:00, 13:00; each entry uses
the latest d at or before its tod: {Q25, BR} x {M1, M2} = 4.
Fade (contrarian check, the reversal hypothesis): Q50 at 10:00 and 10:30 with M1 applied to -d = 2.
**Total N = 38 per book; 76 with both books.** Bar = max(1.5, sqrt(2 ln 76)) = **2.94**. Lineage (market-context gates:
2,450 through bdi1016 + 23 bdi1019 + 76) N = 2,549 -> 3.96, reported; a pass between 2.94 and 3.96 is labelled weak.

Metrics per policy, book, split: parent n, days, parent exp R; delta = mean over parent trades of (w r - r) (total R
change per parent trade); tilted exp = sum(w r) / sum(w); day-clustered t of daily delta sums; delta without the best
day; delta in up / flat / down sessions; share of days with d != 0 and share of entries re-weighted.
Random tilt with the same switching frequency: on each day where the policy is active, d is replaced by a fair coin.
Its expected daily delta is 0.5 (delta(+d) + delta(-d)) (analytic; exact mean of the coin draws), so
excess_day = delta_day(d) - E[random] = 0.5 (delta(d) - delta(-d)); excess t is day-clustered. Naive baselines: no tilt
(delta 0) and random tilt.

**Pass (Decision book) only if ALL:** delta > 0 on train and valid; valid day-t >= 2.94; excess > 0 on train and valid
with valid excess t >= 1.65; valid delta > 0 in up AND down sessions; valid delta without best day > 0; plateau: the
same signal/sizing at the neighbouring checkpoint(s) has valid delta > 0. If one passes, a proposal (exact rule, expected
effect, runner sketch, accounts) goes to `backlog_proposals.jsonl` (the backlog itself is not edited). Otherwise the best
near-miss is listed. No locked-block or holdout scoring tonight (a finalist would go to the lead for that).

Educational only — not financial advice.
