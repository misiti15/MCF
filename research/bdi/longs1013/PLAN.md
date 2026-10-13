# More long opportunities (BDI, owner request 2026-10-12): pre-declaration

*Educational only - not financial advice. Written 2026-10-13 before any configuration of this study was scored.
Results go in NOTES.md; this file may only gain dated amendments written before the affected configurations are
scored.*

Owner (2026-10-12): "It may be worth investing more energy into long setups... what can we do to give more long
setups more opportunities without a separate account and also not disrupting progress in other areas?" Today's five
worst primary trades were all MarcoFlow heat <= -30 flow-sell SHORTS that went up (ZBH MF3 10:51, HSBC MF4 09:55,
BBY MF5 11:00, SM MF2 10:41, DUK MF3 10:46). Owner reads: "maybe the metrics showed the opposite of what was
intended?", "price dropped a lot at open ... then shot up; as a long it would have been a massive gain".

Seen before writing this plan: published notes only (nightly1012, reddit1012liq, bdi1012, turns1009 T1/T2/stage C
S1-S5 = 0 pass, playingtime, cwt/test_b, trendguard), the frame schema, and the journal signal *status counts* per
account (no R, no setup outcome).

## 0. Data and conventions (all questions)
- Open two-year history only: lab frames `research/history2y/lib.load_month` (open months; 5-minute bars, bar-close
  tod 09:50..15:00, lab outcomes `r/win_{side}_{geom}` resolved to 15:55), the head/tail 5-minute rows of
  `research/bdi/cwt/test_b/data/headtail.parquet` (09:35..09:50 and 15:05..15:55 h/l/c/vwap, rebuilt from the
  1-minute cache with the locked block filtered at read), `lib.daily()` (prior-day high/low/close). The rule-19 locked
  block 2024-11-01..2025-02-28 is never loaded; `MCF_HIST_ALLOW_LOCKED` is never set.
- Population: point-in-time adv20 >= $95M, atr_d > 0 (the primary min_adv). R = 0.25 x atr_d.
- Entry at the signal bar's close (lab convention); one trade per symbol-day per configuration (first qualifying bar).
- Exits: lab geometries `t1s1`, `t05s1`, `t1s05` (target/stop in R, stop first, timed exit 15:55) and `HTC` = hold to
  the 15:55 bar close with no stop and no target.
- Costs: `gates.prod_r` (1c + 1 bps per side, exit side free on target fills, +2c on stop fills) with the
  `gates.tod_cost_mult` entry multiplier; HTC pays both sides (entry x tod multiplier); x3 on the whole cost for the
  extended tier (|gap| >= 20% or price < $5).
- Splits: train = open sessions <= 2025-12-31; valid = 2026-01-02..2026-10-07; open = both. Day-clustered t
  (`gates.summary`), regimes (`lib.regimes()`), walk-forward (`gates.walk_forward`, locked months excluded),
  ex-best-day, busiest-session share. Same-time control: trade R minus the mean R of every eligible symbol's same-side
  trade with the same exit at the same date and bar ("excess over the market at that minute").

## 1. Q1 - opposite side of the MarcoFlow flow-sell family (lineage `longs1013-mfopp`)
Signal sets (live masks and live windows, `research/primitives/marcoflow/*.py` via config/default.yaml):
MF1 (950-1030), MF2 (950-1100), MF3 (950-1100), MF4 (950-1100), MF5 (950-1500), and FAM = the union of the five.
- Short side at delay 0 with the 4 exits: the reference (what the live setups do), 6 x 4 = 24.
- Long side on the same signals: entry delay d in {0, 1, 3} bars (0 = the MF bar itself; 1 / 3 = enter long at the
  close of the 5-minute bar 5 / 15 minutes later, same symbol-day, if that bar exists and is <= 15:00) x 4 exits:
  6 x 3 x 4 = 72.
- **Q1 N = 96.** Lineage N = 96 + 9,132 (trendguard per MF setup) = 9,228 -> t bar sqrt(2 ln N) = 4.27.
- "Is the metric inverted?" is answered by: gross (before costs) long vs short expectancy on the symmetric t1s1 and HTC
  exits per MF setup, train / valid / open and up / flat / down sessions; a metric is called *inverted* only if the
  gross long side is positive with day-clustered t >= 2 on the open history AND in both train and valid.
- Descriptive (not counted): today's five trades in the journal (entry, exit, R) and the long what-if if bars are
  available.

## 2. Q2 - "open flush, then a hard swing up" long (lineage `longs1013-flush`)
Day constants: open O = close / (1 + fromOpen/100) (any frame row), prior close PC = O / (1 + gap/100). Flush low
FL_W = lowest low of the head bars 09:30-09:40 (W10: bars ending 09:35, 09:40) or 09:30-09:50 (W20: bars ending
09:35..09:50).
- Flush (12): reference ref in {O, PC} x depth x in {0.5, 0.75, 1.0} ATR x W in {10, 20}: (ref - FL_W) / atr_d >= x.
- Trigger (3), on the 5-minute bar closing at tod in [09:50, 10:30], first one per symbol-day:
  - `RB` close > the highest high of the bars ending 09:45 and 09:50 (the "09:45/09:50 bar high"; from the 09:55 bar).
  - `VR` VWAP reclaim: close > session VWAP and the prior bar's close <= its VWAP.
  - `HL` higher low: no new session low on this bar or the prior bar (LOD unchanged from two bars ago) and the close
    is above the prior bar's high.
- Filter (3): `none`; `pdcl` prior-day close location (close - low) / (high - low) >= 0.5 (prior open session within
  5 calendar days, else NaN -> excluded); `spy` SPY fromOpen > 0 at the same bar.
- Exit (4): t1s1, t05s1, t1s05, HTC.
- Grid 12 x 3 x 3 x 4 = 432. Controls (counted): flush-only, entry at the 09:50 bar close, filter none, 12 x 4 = 48;
  random long bar (one per eligible symbol-day, seed 1013) in 09:50-10:30, 4 exits = 4. **Q2 N = 484.**
- Lineage N = 484 + 30,970 (CWT05 flush, package B5) = 31,454 -> t bar 4.55. Study-only bar (information):
  sqrt(2 ln 580) = 3.57.
- Comparison (published or re-read, not new configurations): NS1, NS5, heat_fade_long (current window) from
  `research/bdi/timeofday/data/trades.parquet`, overall and restricted to entries 09:50-10:30; LIQ longs from
  `research/bdi/reddit1012liq/NOTES.md`.

**Total N this study = 96 + 484 = 580.**

## 3. Selection, gates, Testing 1
- Finalists: per question, the 5 configurations with the highest train day-clustered t among those with n_train >= 150
  and train exp > 0, plus the best Q2 configuration per trigger. All finalists are reported on valid and open,
  failures included, with plateau (worst one-step neighbour in x and in W for Q2; in d for Q1).
- Research gate (`gates.verdict`, lineage N above). Nothing is scored on the locked block; that is the lead's look.
- **Testing-1 bar (all must hold):** n_open >= 150; open exp > 0 after costs with t_open >= 1.5; train exp > 0 and
  valid exp > 0; ex-best-day > 0; busiest session <= 10% of trades; same-time-control excess > 0; exp > the random
  long bar of the same exit + 0.05R (Q2) or > the short reference of the same set and exit (Q1); plateau > 0;
  runnable on the live frame (frame columns + head bars; RB/flush need the 09:30-09:50 bars, which the live runner
  holds). At most 2 configurations, best open t first, at most one per question. If none passes, none is proposed.

## 4. Q3 - crowding (descriptive) and mechanisms (lineage `longs1013-crowd`)
**Live (descriptive, journals from origin/mcf-data, mcf-data-testing, mcf-data-testing2):** per account and day,
LONG signals and their status/reason; for "already in symbol" the holder (`info.held_by`, else the setup with an
open trade or the last submitted signal on that symbol) and the holder's side; slot / per-setup cap skips; the
runner's what-if R (run "whatif") of the blocked longs.

**Mechanisms (entry-count + lab R replays on the open history, `timeofday/data/trades.parquet`, the playingtime
replay rule: one position per symbol, earlier signal wins, same bar -> setup_order, a blocked setup does not retry,
hold 120 min, account slots and per-setup cap), books = primary (12 current setups) and Testing 1 (lab-available
setups, -FD = 'full', windowed = 'current'):**
- M0 baseline (live rule).
- Ma side-aware priority: on the same bar longs go first, setup_order within side.
- Mb reserved long slots: K in {10%, 25%} of slots reserved for longs (shorts may not fill them).
- Mc same-direction pyramid: a long may enter a symbol held only by long positions, cap 2 positions per symbol.
- Md shadow trades: blocked signals are simulated (the runner's what-if) and counted as statistical trades.
- Me long setups in a long-only book (upper bound of moving long setups to the account with the fewest long setups).
- Mf retry after release: a blocked setup may take its NEXT qualifying bar after the holder exits (needs all
  qualifying bars; computed for NS1/NS5 from the frames, primary book).
Reported per mechanism: extra long trades/day, their lab exp R, short trades displaced/day and their exp R, and the
implementation size. 2 books x 7 scenarios = 14 replays (entry counts and existing lab R; no new setup is scored).
