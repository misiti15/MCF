# WILDCARD-1127 — Market intraday momentum (first half hour -> last half hour) on index and sector ETFs — pre-registration

*Educational only — not financial advice.* Research only: no change to config/, setups, exits, assignments,
decisions.json or the ledger. Written and committed BEFORE any scoring (data fetch only so far).

## Why this is new
Backlog `intraday-momentum-paper` (Gao, Han, Li, Zhou 2018 JFE, "Market intraday momentum": the return from the prior
close to 10:00 predicts the 15:30-16:00 return) is still status `idea`. Only VARIANTS were scored before, all on short
DEV windows with few trades: pod1022 `pod-gao-newsday-first30-hold-long` (9/1 trades, macro-news days, 10:00 entry),
`pod-qr-gao-first-and-penult-volgate-close-long` (+ctrl-novol, ctrl-short; 15:00 entry, vol gate, VWAP rule; 25-100
trades), `pod-raschke-trend-day-last-hour-*` and `pod-oa-wide-first-hour-continuation-*` (single stocks). The plain
paper rule — all days, index ETFs, last 30 min — and its sector-ETF extension (Baltussen et al.; Gao et al. report the
effect in sector ETFs too) have never been tested on long history with costs. Mechanism tag (C3-MECH): late-day
rebalancing / gamma hedging and late-informed traders push the close in the direction of the day's early move;
falsifiable: sign(early return) x last-30-min return has positive mean, stronger on high-|early| days.

## Data (all 1-minute RTH bars, raw prices)
* 2016-01-04..2022-09-30: SIP 1-min bars fetched GET-only from Alpaca market data (SPY, QQQ reused from the
  qqqopen_1127 fetch; IWM DIA XLK XLF XLE XLV XLY XLP XLI XLU XLB XLRE XLC SMH fetched tonight; scratch only, not in git).
* 2022-10-03..2024-09-13 `data/cache_fresh/1Min`, 2024-09-16..2026-11-04 `data/cache_hist/1Min` (main clone).
* **Locked block 2024-11-01..2025-02-28 is never read**: rows are dropped at load and asserted absent in every script;
  a prior close that would fall inside the block (2025-03-03) is not used (day skipped).
* Half days are excluded (detected per day from SPY: volume printed 13:05-15:54 < 3% of the session's volume — robust
  to the caches' stray post-13:00 prints). A day is used only when the previous session in SPY's calendar is present
  for that ETF (prior close = that session's 15:59 bar close) and the 09:59, 14:59, 15:24, 15:25 and 15:55 bars exist.

## Splits
EARLY 2016-01..2022-12 · T2 2023-01..2024-09 · FIT 2024-10 + 2025-03..2025-09 · CHECK 2025-10-01..2026-11-04.
DEV = EARLY + FIT (selection only). OOS = T2 + CHECK.

## Rule (one-off simulator, engine label **E4 WILD-sim**; same fill semantics as the Backtester: market entry at a bar
open, stop-first inside a bar, gap through the stop fills at the bar open)
* R1 = close(09:59 bar) / prior session close − 1 (Gao's first half hour incl. the overnight gap).
* ROV = close(15:24 bar) / close(14:59 bar) − 1 (penultimate half hour, truncated so it is known at 15:25).
* sigma20 = std of R1 over that ETF's prior 20 used sessions; A20 = mean over the prior 20 used sessions of
  (max high − min low) of the 15:25-15:54 bars, in price. Both strictly ex-ante; first 20 sessions per ETF unused.
* Direction d = sign(R1). Entry: market at the 15:25 bar open. Stop: entry − d x s x A20. Exit: market at the 15:55
  bar open (the live 15:55 flatten) unless stopped first. R = d x (exit − entry) / (s x A20).

## Configurations (counted): 2 x 2 x 3 x 2 = **24**
* group: IDX4 (SPY QQQ IWM DIA) | SEC12 (XLK XLF XLE XLV XLY XLP XLI XLU XLB XLRE XLC SMH) — each a pooled book
* predictor: P1 = sign(R1) every eligible day | P2 = only when sign(ROV) = sign(R1)
* threshold: |R1| >= k x sigma20, k in {0, 0.5, 1.0}
* stop: s in {1.0, 2.0}
Cumulative program N ~8,952 + 24 = **~8,976** (lineage-claim bar t >= ~4.3; this study's own bars below).

## Costs (always in)
LIVE-L (primary; research/primshorts_1126/cells_live.json, cost_R = a / stop_width_bps + b per price bucket x exit
kind, exactly as qqqopen_1127/qo_score.costs) and LR8 (1c + 1 bp per side x time-of-day mult, +2c on stops, short
borrow 1.2 bp). ETF-TIGHT (1 bp per side + 1c on stops) and gross are reported for information only, never for a pass.

## Hypotheses and pass bars
**H1 (pre-specified, the paper's form, no selection): IDX4 | P1 | k=0 | s=2.0.** Passes only if ALL hold:
1. LIVE-L mean R > 0 on T2 and on CHECK separately; also > 0 on EARLY (FIT reported).
2. LR8 mean R > 0 on T2 and CHECK.
3. Day-clustered t (sum of R per day) on OOS (T2+CHECK pooled, LIVE-L) >= 2.0.
4. One-big-day: on T2 and CHECK, avg R without the best day > 0 and best-day share of total R < 50%.
5. Random-direction control: same trades (ETF, day, entry, stop, exit rule, costs) with direction drawn 50/50, 2,000
   draws; actual OOS LIVE-L mean >= 95th percentile of the control. Always-long drift baseline reported alongside.
6. Per-ETF effect report: >= 3 of 4 ETFs with OOS LIVE-L mean > 0 (how many better/worse and by how much listed).
7. Up/down sessions (SPY close-to-close sign): OOS LIVE-L mean > 0 in both.
**H2 (selection): the best of the other 23 configs by DEV (EARLY+FIT) LIVE-L day-clustered t** — finalist. Same bars
1-7 but bar 3 is t >= 2.87 (Bonferroni over 24, one-sided 0.2%), bar 6 is >= 60% of the group's ETFs positive, and
for k > 0 it must also beat the same config at k = 0 on OOS (the filter must add). Every config's split table is
reported (grid.csv), every finalist listed.
**Verdicts:** PASS = H1 or H2 passes all bars. LEAD = OOS positive on CHECK and T2 under LIVE-L with t >= 1.5 and
the control beaten, but another bar fails; or gross / ETF-TIGHT positive with OOS t >= 2 but LIVE-L kills it (a real
signal blocked by the cost model, stated as such). FAIL otherwise. A pass would become a backlog proposal in the
REPORT (no direct backlog / config edit).

## Notes fixed in advance
* No live trades are used, so no live-window ledger rule changes enter the figures.
* Dividend ex-dates lower the gap part of R1 on raw prices (~4 days a year per ETF); accepted, noted as a caveat.
* Results by year and the gross-vs-cost decomposition are reported for every finalist.

## Addendum A (2026-11-27, after a code dry run on IDX4 rows and before any config / split was scored)
The registered half-day detector (SPY volume 13:05-15:54 < 3% of the session) found only 1 half day: the bar data carry
heavy post-13:00 prints on half days (shares 2-20%), overlapping normal days. Half days now come from the fixed NYSE
early-close list: 2016-11-25; 2017-07-03, 11-24; 2018-07-03, 11-23, 12-24; 2019-07-03, 11-29, 12-24; 2020-11-27,
12-24; 2021-11-26; 2022-11-25; 2023-07-03, 11-24; 2024-07-03 (+ 2024-11-29 / 12-24 inside the locked block) and
mcf/execution/market_calendar.PAST_EARLY_CLOSES for 2025-2026. The dry run (code check) printed only unconditional
pooled row means (always-long / always-short gross on IDX4, all splits together); nothing else changes.
