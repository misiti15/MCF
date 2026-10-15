# BDI 2026-10-15 pre-declaration (written before any history configuration below was scored)

*Educational only - not financial advice.*

## Part A: per-trade analysis of 2026-10-15 (descriptive, not gated)
`analyse_1015.py` = `bdi1014/analyse_1014.py` re-dated. It re-uses `research/bdi/nightly1015/trades.csv` (806 real
trades) and the nightly's SIP 1-minute bars. Same what-ifs (be05, tr05, t05, t1, eod, SAR, re-entry, opposite side with
the hindsight pointer) and the same loss-type classifier. Losers are merged into `research/bdi/patterns.csv`
(idempotent by date). One session: a diagnosis, not evidence (rule 7).

## Part B: index dip-bounce measured from the PRIOR CLOSE (owner chart read, 2026-10-15)
**Motivation (one session, not evidence).** SPY opened -0.44% below the 10-14 close, made its low at 09:57
(-0.24% from the open, -0.67% from the prior close) and closed +0.72% from the open. The live Testing 1 IDX setups
measure the drop from today's open (>= 0.5/0.75/1.0%), so they would not have fired. Question: does measuring the drop
from the prior close (gap included) work at least as well as the open-based version?

**Data.** SIP 1-minute bars, `data/cache_hist/1Min` (2024-09-16..2026-10-07), RTH. The rule-19 locked block
2024-11-01..2025-02-28 is excluded **at read time** (pyarrow filter on the timestamp, so no locked row is ever
materialised); a session whose prior session is locked (2025-03-03) or missing (2024-09-16) is skipped.
Samples exactly as `idxdip1015`: DEV = every open session except the older holdouts (Apr 1 - Jun 30 2026,
Sep 16 - Oct 7 2026); halves H1 < 2025-09-01 <= H2.
Prior close = the previous session's last RTH 1-minute close (the backtester's `prev_close` definition,
`daily_from_intraday`).

**Definitions (fixed).**
- PC (prior-close dip): the signal index's running low since 09:30 <= prior close x (1 - d/100) on a bar that has
  closed by `dip_by`. Trigger: the first index bar closing 09:50-10:05 after the dip with
  close >= running low + 0.20 x (prior close - running low).
- GL (gap-down + early low): signal open <= prior close x (1 - g/100), AND the signal's running low by `dip_by` is at
  least 0.10% below the open (the gap extended into an early low). Trigger as PC (20% of prior close - running low).
- Trade (both): market entry at the next bar's open of the traded symbol; stop = traded running low
  - 0.10 x (traded prior close - traded running low); exits TRAIL (no target; trail 1R behind the best once +1R) or
  HOLD (stop only); flatten 15:55. Production fill model and config costs (`mcf.backtest.engine.simulate`,
  `Costs.from_cfg`), the same as `idxdip1015`.
- Instruments: S&P signal (SPY) -> the day's SPXL/UPRO pick (larger dollar volume 09:30..trigger bar, the production
  `choose` rule); QQQ signal -> TQQQ. Index-ETF rows (SPY, QQQ traded) are scored as consistency rows and counted.

**Grid (every configuration counted).**
| family | dimensions | configs |
|---|---|---|
| PC | signal {SPY, QQQ} x d {0.5, 0.75, 1.0} x dip_by {09:45, 09:55} x exit {TRAIL, HOLD} x instrument {3x, index ETF} | 48 |
| GL | signal {SPY, QQQ} x g {0.3, 0.5} x dip_by {09:45, 09:55} x exit {TRAIL, HOLD} x instrument {3x, index ETF} | 32 |
**N = 80.** Lineage: idxdip 1,134 + 80 = **1,214**, bar t >= sqrt(2 ln 1214) = **3.77** (research bar).

**Comparisons (reported for every row; not configurations).**
- Open-based version, re-run in the same harness on the same sessions: IDX5 (SPY 0.5/09:45), IDX2 (0.75/09:45),
  IDX3 (0.75/09:55) TRAIL on the 3x pick; IDX1 (QQQ 1.0/09:55) TRAIL and HOLD on TQQQ. Parity check against
  `idxdip1015/pick3x_results.csv` (rec20, rule today).
- Mapped pairs: PC-SPY d/dip_by vs the open-based setup with the same d/dip_by (0.5/09:45 vs IDX5, 0.75/09:45 vs IDX2,
  0.75/09:55 vs IDX3); PC-QQQ 1.0/09:55 vs IDX1.
- Incremental days: PC trades on sessions where the mapped open-based setup did not trade.
- Rule-6 controls: (a) all DEV sessions, 3 seeded random entry bars closing 09:50-10:05, same prior-close stop
  geometry (only where prior close - running low >= 0.05% of the prior close and price > running low), same exit;
  (b) the same trigger sessions, 20 seeded random entry bars in the window.

**Choice rule (pre-declared).** A PC/GL row is "at least as good as the open-based version" only if, on DEV, 3x TRAIL
(or HOLD for QQQ): mean R >= the mapped open-based mean R, t >= the mapped open-based t, the incremental-day trades have
mean R > 0, the row beats control (a), and the neighbouring threshold (adjacent d, same dip_by) is also positive
(plateau). Only such rows are scored once on the older holdouts and only they get a proposed YAML. The research bar
(3.77) is reported; as with idxdip1015, Testing 1 is a forward paper test and does not require it, but whether it was met
is stated. For GL, "mapped" = the open-based setup with the same signal and dip_by (IDX5/IDX3 for SPY, IDX1 for QQQ).

**2026-10-15 (out of sample, descriptive only):** whether each chosen row fires today, on the nightly's bars.

## Part C: patterns -> rules, tested on the two-year open history (production + time-of-day costs)
Harness: `research/bdi/nightly1015/bt1015.py`'s cached first-signal hits (lab frames via `research/history2y`,
locked block refused by the loader, `MCF_HIST_ALLOW_LOCKED` never set), live semantics (first qualifying decision bar
per setup-symbol-day). A filter is applied before "first", so the first bar that passes it fires.

**C1 `bdi1014-rw2-extension-floor` (queued 10-14).** RW2-exhaustion-noon-adv150-short-FD: a decision bar qualifies
only when fromOpen >= F% or rsi5 >= R. Grid F {2.0, 2.5, 3.0} x R {85, 90, 95} = **9 configurations**.
(Frame columns fromOpen and rsi5 merged on symbol/date/tod; head/tail rows with no frame row are kept unfiltered.)

**C2 index-up short veto (today's hindsight pointer, made causal).** For the 5 lab short setups of bt1015 (NS2, NS2-FD,
RW6-FD, RW2-FD, CWT09-g5-lowerhalf): a decision bar does not qualify when SPY fromOpen >= k at that bar,
k {0.25%, 0.50%} = **10 configurations**.

**Bars (fixed now).** Per configuration: exp > 0 after costs; exp minus baseline > 0 in both halves (<= 2025-12,
2026-) and in up and down sessions (`lib.regimes`); day-clustered t (`gates.summary`) >= the study bar
max(1.5, sqrt(2 ln N)): C1 N = 9 -> 2.10, C2 N = 10 + the nightly's 10 short-veto configs = 20 -> 2.45; plateau
(neighbouring F/R or k positive). Research/Primary bar for C1 is the RW2 lineage (934,970 + 23 + 9 configs -> t >= 5.24).
A pass makes a finalist only; nothing is applied, no holdout is scored here.

**Total configurations tonight: 80 + 9 + 10 = 99.**
