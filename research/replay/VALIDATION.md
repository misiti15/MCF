# Replay validation: recorded sessions through the live runner vs the live paper journals

*Educational only — not financial advice. Replays are replays, not live results (rules 7–8). "Live" below means the
paper journals of the data branches (trades / signals, run 1). Every number carries its sessions and counts.*

## Failures and limits first

- **Universe gap.** The replay universe is the lab universe (1,226 most liquid names with 2-year SIP history) ∩ the
  live universe.csv of that day. Live signals on other symbols cannot be replayed: primary 75 of 685, Testing 1 1,091 of
  5,671, Testing 2 420 of 5,966. All match rates below are on the shared universe.
- **Speed target met only for Primary.** Seconds per session per account, 4 sessions in parallel on a 4-core box that
  another agent's jobs shared: Primary 190–290 s (133 s alone), Testing 1 290–520 s, Testing 2 (as live, 30–47 setups)
  270–530 s, Testing 2 with *today's* config (47 setups, 15 with breadth context) ~1,070 s — too slow, so the broad
  set below has no Testing 2. The remaining cost is the runner's own per-poll work on ~1,200 symbols (contexts, feed
  slices) and the non-lab setups (orb20 runs every poll); the fast path removed the rest (see Speed).
- **Testing 2 diverges most:** live Testing 2 lost 2,291 replay signals it never evaluated. The live status log shows
  8–11-minute gaps between polls on 10-19, 10-20 and 10-21 mornings (and the SIP outage 10-15 12:57–14:10 ET): a poll
  that takes 10 minutes skips the 5-minute decision bars in between. The replay has no poll latency, so it trades 4,476
  vs 2,740 live (in universe). This is a live throughput problem, not a replay error; the poll log
  (`live.log_poll_inputs`, shipped here) will measure it per poll from the next session.
- **Code drift:** the replay runs today's code on the setups/limits as they were. Rules added since (the twin block of
  2026-10-19 evening defaults on) block signals the live runner of 10-12..10-19 took: 158 Testing 1 and 10 Primary
  matched signals were `submitted` live and `twin held` in the replay.
- **Quotes are modelled** (spread drawn from the live journals' spreads, in-sample for these sessions); spread skips
  agree only statistically (each direction ~50–120 per account). Shortability uses today's ETB flags.
- Sessions available: Primary 11 (10-07..10-21; 10-06 has no frozen setup snapshot), Testing 1 and 2: 8 (10-12..10-21).
  Testing 1 on 10-09 was not replayed (time). 10-19..21 bars came from a read-only Alpaca market-data fetch
  (data/cache_hist ends 10-16).

## Method

- `python -m mcf.replay run --account primary,testing,testing2 --dates 2026-10-12..2026-10-21 --as-live --universe live
  --fills paper --limit-fill touch` (and `--fills costs --limit-fill through`); `research/replay/validate.py` compares
  with the journals; `research/replay/gap.py` builds the waterfall; `research/replay/tables.py` renders these tables.
  Raw outputs: `research/replay/results/*.json`.
- `--as-live`: the setups frozen for each session on the account's data branch (`setups/<date>.json`: strategies,
  exits, shorts, live, universe) plus the account limits and costs from the config committed before that session's open.
- Signals are matched on (setup, symbol, decision bar ±1 minute) — the decision bar is `info.bar_time`, which the runner
  journals live; trades are joined to their entry signal by order id and matched the same way.
- What the harness simulates and how the fast path is verified: see "What was built" at the end.

## 1. Replay vs live (paper fills: half-spread market/stop fills, touch limits = what Alpaca paper does)

**Headline:** the replay reproduces **98.0% / 99.9% / 99.6%** of the live signals on the shared universe (Primary /
Testing 1 / Testing 2), and **85% / 82% / 91%** of the live trades. On the matched trades the per-trade R differs by
**−0.006 / −0.005 / +0.024 R on average (median −0.015 / −0.012 / +0.003)**, entry prices by a median **−0.2 / +0.2 /
+0.1 bps**, and the exit reason agrees on **99.1% / 97.1% / 93.6%**. System level, Primary replay −0.161 R/trade (414
trades, −66.6 R) vs live −0.162 R/trade (398 in-universe trades, −64.4 R); Testing 1 −0.094 vs −0.104; Testing 2
−0.091 vs −0.123 (replay takes 1,700 more trades, above). Per setup (65 setups with ≥ 10 trades on both sides) the
median |avg R gap| is 0.04 (Primary), 0.065 (Testing 1), 0.053 (Testing 2) R; three setups drift by > 0.25 R:
MF5-flowsell-vwapup-rsi5hi (−0.28, 18 vs 28 trades), exhaustion_short (−0.26, 18 vs 15),
RW2-exhaustion-noon-adv150-short-FD (+0.50, 15 vs 69 — Testing 2 polls).

### Replay (paper fills) vs live

| account | sessions | live signals (in universe) | replay signals | matched | match % of live in-universe | status agree | live trades (in universe) | replay trades | matched trades | entry diff bps (median) | R diff matched (mean / median) | same exit | live R (in universe) | replay R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| primary | 11 | 685 (610) | 645 | 598 | 98.0% | 0.848 | 422 (398) | 414 | 338 | -0.2 | -0.006 / -0.015 | 0.991 | -64.4 (-0.162/tr) | -66.6 (-0.161/tr) |
| testing | 8 | 5671 (4580) | 5067 | 4575 | 99.9% | 0.861 | 2371 (2256) | 2154 | 1851 | 0.2 | -0.005 / -0.012 | 0.971 | -235.6 (-0.104/tr) | -202.9 (-0.094/tr) |
| testing2 | 8 | 5966 (5546) | 7816 | 5525 | 99.6% | 0.849 | 2824 (2740) | 4476 | 2486 | 0.1 | 0.024 / 0.003 | 0.936 | -337.4 (-0.123/tr) | -405.9 (-0.091/tr) |

**primary** (matched signals with a different outcome; live -> replay):
- 17 x `submitted: ok  ->  skipped: spread #bps > max`
- 15 x `skipped: spread #bps > max  ->  submitted: ok`
- 12 x `submitted: ok  ->  skipped: spread is #% of stop distance`
- 11 x `skipped: spread is #% of stop distance  ->  submitted: ok`
- 10 x `submitted: ok  ->  skipped: twin held`
- 9 x `submitted: ok  ->  skipped: already in symbol`
- 7 x `skipped: lot cap  ->  submitted: ok`
- 4 x `submitted: ok  ->  skipped: not shortable/ETB`
- 3 x `skipped: not shortable/ETB  ->  submitted: ok`
- 3 x `skipped: already in symbol  ->  submitted: ok`

**testing** (matched signals with a different outcome; live -> replay):
- 158 x `submitted: ok  ->  skipped: twin held`
- 117 x `submitted: ok  ->  skipped: spread #bps > max`
- 80 x `skipped: spread #bps > max  ->  submitted: ok`
- 78 x `submitted: ok  ->  skipped: spread is #% of stop distance`
- 50 x `skipped: spread is #% of stop distance  ->  submitted: ok`
- 22 x `submitted: ok  ->  skipped: not shortable/ETB`
- 21 x `skipped: not shortable/ETB  ->  submitted: ok`
- 19 x `skipped: halted  ->  submitted: ok`
- 17 x `skipped: setup daily loss limit  ->  submitted: ok`
- 16 x `skipped: lot cap  ->  submitted: ok`

**testing2** (matched signals with a different outcome; live -> replay):
- 179 x `skipped: halted  ->  submitted: ok`
- 133 x `rejected: {"base_price":"#.#","code":#,"message":"  ->  submitted: ok`
- 94 x `submitted: ok  ->  skipped: spread is #% of stop distance`
- 92 x `skipped: spread is #% of stop distance  ->  submitted: ok`
- 87 x `skipped: spread #bps > max  ->  submitted: ok`
- 62 x `submitted: ok  ->  skipped: spread #bps > max`
- 48 x `submitted: ok  ->  skipped: max positions for this setup`
- 32 x `skipped: max positions for this setup  ->  submitted: ok`
- 31 x `skipped: already in symbol  ->  submitted: ok`
- 15 x `rejected: {"base_price":"#.#","code":#,"message":"  ->  skipped: lot cap`

| account | setup | live trades | live avg R | replay trades | replay avg R |
|---|---|---|---|---|---|
| primary | NS2-sma50break-overbought-short | 54 | -0.453 | 48 | -0.435 |
| primary | MF3-open-flowsell-rsi5hi-FD | 45 | -0.140 | 40 | -0.163 |
| primary | heat_fade_short | 35 | -0.401 | 34 | -0.392 |
| primary | MF5-flowsell-vwapup-rsi5hi | 31 | -0.071 | 36 | -0.320 |
| primary | NS3-failed-vwap-reclaim-short-FD | 32 | -0.361 | 31 | -0.379 |
| primary | MF3-open-flowsell-rsi5hi | 29 | -0.069 | 20 | 0.074 |
| primary | MF1-945-flowsell-vwapup | 24 | -0.039 | 23 | 0.221 |
| primary | exhaustion_short | 22 | -0.221 | 21 | -0.157 |
| primary | MF4-h40-open-flowsell | 21 | 0.070 | 18 | 0.105 |
| primary | heat_fade_long | 17 | -0.163 | 17 | -0.313 |
| primary | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 16 | 0.219 | 15 | 0.174 |
| primary | NS4-pm-vwap-reclaim-oversold-short | 16 | 0.265 | 13 | 0.397 |
| testing | heat_fade_short-FD | 352 | -0.062 | 261 | -0.064 |
| testing | RW7-gapdn-bounce-early-short-FD | 195 | 0.002 | 180 | 0.007 |
| testing | LIQ-orl-sweep-open15-s25-long | 144 | -0.093 | 145 | -0.159 |
| testing | RW2-exhaustion-noon-adv150-short-FD | 136 | -0.086 | 140 | -0.071 |
| testing | heat_fade_long-FD | 150 | -0.380 | 97 | -0.164 |
| testing | L3-gap-slope-fromopen-FD | 128 | 0.213 | 106 | 0.007 |
| testing | heat_fade_short | 91 | -0.185 | 102 | -0.088 |
| testing | heat_fade_long | 94 | -0.454 | 91 | -0.483 |
| testing | ST2-slope20up-long-am-t05s1-FD | 81 | -0.200 | 72 | -0.170 |
| testing | NS2-sma50break-overbought-short-FD | 69 | -0.443 | 65 | -0.452 |
| testing | RW4-ns3-adv150-short-FD | 57 | -0.057 | 63 | 0.050 |
| testing | NS3-failed-vwap-reclaim-short-FD | 52 | 0.143 | 50 | 0.119 |
| testing2 | CWT14-failbrk-orl-p05-long | 363 | -0.141 | 551 | -0.146 |
| testing2 | CWT14-failbrk-orl-p05-lowvol-long | 351 | -0.233 | 544 | -0.151 |
| testing2 | CWT14-failbrk-pdl-p05-long | 269 | -0.035 | 413 | -0.049 |
| testing2 | CWT14-failbrk-orl-p10-long | 193 | -0.155 | 351 | -0.106 |
| testing2 | CWT12-coil-k4-long | 190 | -0.042 | 346 | -0.038 |
| testing2 | CWT14-failbrk-pdl-p05-lowvol-long | 200 | -0.059 | 318 | -0.006 |
| testing2 | CWT14-failbrk-pdl-p10-long | 209 | -0.022 | 281 | 0.035 |
| testing2 | CWT14-failbrk-orl-p10-lowvol-long | 177 | -0.139 | 281 | -0.065 |
| testing2 | CWT14-failbrk-pdh-p05-lowvol-short | 188 | -0.088 | 263 | -0.067 |
| testing2 | CWT14-failbrk-pdh-p10-short | 168 | -0.052 | 251 | -0.018 |
| testing2 | CWT14-failbrk-pdh-p10-lowvol-short | 102 | -0.167 | 168 | -0.131 |
| testing2 | CWT14-failbrk-pdl-p10-lowvol-long | 94 | 0.077 | 125 | 0.072 |

Main causes of mismatch, in order of size: (1) live poll throughput (Testing 2: decision bars skipped by
8–11-minute polls; replay-only signals concentrate 10:00–11:59 on 10-14, 10-19, 10-20 and 12:00–14:59 on 10-15, the
SIP outage); (2) universe (live symbols outside the lab universe); (3) path-dependent risk state — once R differs, the
daily loss halt (`halted`, 179 Testing 2 / 19 Testing 1 signals) and per-setup caps fire at different times;
(4) Alpaca bracket base-price rejects (133 live Testing 2 rejects that the replay accepted: the replay's base price is
the bar open, live used the trade at submission ~33 s later); (5) spread skips (modelled quotes); (6) code drift (twin
block); (7) shortability flags.

### Same sessions with production costs and trade-through limits (research rule 1)

### Replay (production costs, trade-through) vs live

| account | sessions | live signals (in universe) | replay signals | matched | match % of live in-universe | status agree | live trades (in universe) | replay trades | matched trades | entry diff bps (median) | R diff matched (mean / median) | same exit | live R (in universe) | replay R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| primary | 11 | 685 (610) | 645 | 598 | 98.0% | 0.848 | 422 (398) | 414 | 338 | 0.3 | -0.040 / -0.039 | 0.988 | -64.4 (-0.162/tr) | -79.1 (-0.191/tr) |
| testing | 8 | 5671 (4580) | 5067 | 4575 | 99.9% | 0.863 | 2371 (2256) | 2137 | 1847 | -0.4 | -0.018 / -0.017 | 0.978 | -235.6 (-0.104/tr) | -227.8 (-0.107/tr) |
| testing2 | 8 | 5966 (5546) | 7816 | 5525 | 99.6% | 0.861 | 2824 (2740) | 4245 | 2477 | 1.0 | -0.017 / -0.025 | 0.934 | -337.4 (-0.123/tr) | -453.3 (-0.107/tr) |

Costs and trade-through cost Primary 0.03 R/trade (−0.191 vs −0.161 with paper fills), Testing 1 0.013, Testing 2 0.016.

## 2. Why live ≠ backtest: decomposition on the same sessions, symbols, priors and bars

The waterfall (`research/replay/gap.py`, results/gap.json). A = every signal the setups give on the full session
(research view: the mask over the whole day, `simulate` with production costs, no caps); A' = what the live 5-bar gate
lets through; B = what the replayed runner journaled; C = what it took, with broker fills; D = paper fills; E = live.

| step | primary n / total R / avg R | testing n / total R / avg R | testing2 n / total R / avg R |
|---|---|---|---|
| A backtest (all signals, full session, costs) | 978 / -88.0 / -0.090 | 6723 / -888.5 / -0.132 | 12857 / -1245.0 / -0.097 |
|   of which lab signals the 5-bar gate never shows live | 372 / -0.0 / -0.000 | 1814 / 24.5 / 0.014 | 5034 / -316.8 / -0.063 |
| A' after the 5-bar gate | 606 / -88.0 / -0.145 | 4909 / -913.1 / -0.186 | 7823 / -928.2 / -0.119 |
| B signals the replayed runner journaled | 640 / -97.2 / -0.152 | 5063 / -934.1 / -0.185 | 7805 / -895.7 / -0.115 |
|   of which blocked (caps, twin, spread, risk...) | 230 / -16.8 / -0.073 | 2928 / -731.1 / -0.250 | 3560 / -491.8 / -0.138 |
|   of which taken (simulated like A) | 410 / -80.5 / -0.196 | 2135 / -203.0 / -0.095 | 4245 / -403.9 / -0.095 |
| C taken, broker fills, costs, trade-through | 414 / -79.1 / -0.191 | 2137 / -227.8 / -0.107 | 4245 / -453.3 / -0.107 |
| C' same with touch fills on targets | 414 / -78.2 / -0.189 | 2137 / -204.5 / -0.096 | 4245 / -387.7 / -0.091 |
| D paper fills (half-spread, touch) | 414 / -66.6 / -0.161 | 2154 / -202.9 / -0.094 | 4476 / -405.9 / -0.091 |
| E live paper journal (all symbols) | 422 / -67.0 / -0.159 | 2371 / -237.2 / -0.100 | 2824 / -341.8 / -0.121 |

**primary** blocked signals by reason (n, what they would have made in R, avg):
- `not shortable/ETB`: 71, -12.9R (-0.181/signal)
- `spread #bps > max`: 50, -3.2R (-0.065/signal)
- `spread is #% of stop distance`: 41, -4.3R (-0.104/signal)
- `already in symbol`: 40, +10.4R (0.261/signal)
- `twin held`: 18, -8.2R (-0.453/signal)
- `lot cap`: 10, +0.1R (0.012/signal)
- `missed: triggered at #:#`: 1, +1.1R (1.153/signal)

**testing** blocked signals by reason (n, what they would have made in R, avg):
- `halted`: 983, -610.1R (-0.621/signal)
- `not shortable/ETB`: 516, -132.3R (-0.256/signal)
- `spread #bps > max`: 328, +19.1R (0.058/signal)
- `spread is #% of stop distance`: 226, -11.6R (-0.051/signal)
- `twin held`: 225, -33.9R (-0.150/signal)
- `lot cap`: 171, +17.5R (0.102/signal)
- `opposite side held`: 165, -20.3R (-0.123/signal)
- `already in symbol`: 135, +20.4R (0.151/signal)

**testing2** blocked signals by reason (n, what they would have made in R, avg):
- `halted`: 965, -341.3R (-0.354/signal)
- `spread is #% of stop distance`: 527, +2.7R (0.005/signal)
- `spread #bps > max`: 514, -17.8R (-0.035/signal)
- `max positions for this setup`: 494, -36.8R (-0.075/signal)
- `already in symbol`: 343, -76.5R (-0.223/signal)
- `lot cap`: 287, -1.0R (-0.003/signal)
- `not shortable/ETB`: 200, -17.0R (-0.085/signal)
- `setup daily loss limit`: 135, -7.2R (-0.053/signal)

**(b) The 5-bar gate is the largest single step from backtest to live signals.** Lab setups evaluate only when the
symbol's 1-minute bar count is a multiple of 5 at the poll after the decision bar; a symbol that missed any earlier
minute (no trade in that minute) is out of step and its signal is never seen. That drops **40.7% (Primary), 30.2%
(Testing 1), 39.2% (Testing 2) of all lab backtest signals**. The dropped signals were *not* worse: −0.000, +0.014,
−0.063 R/signal against −0.145, −0.186, −0.119 for the ones kept, so the gate moves the per-signal expectancy from
−0.090 → −0.145 (Primary), −0.132 → −0.186 (Testing 1), −0.097 → −0.119 (Testing 2). A' and B agree (606 vs 640,
4,909 vs 5,063, 7,823 vs 7,805 signals; the remainder is refire/re-entry bookkeeping), which also confirms the replay
runs the live gating. Related finding: the engine `Backtester` calls `eligible()` on full sessions, which for lab setups
also rejects every symbol-day with fewer than 390 bars (n % 5 or the window check on the 16:00 bar end) — it silently
skips the same thin symbol-days, while the research scans (frames) keep them. Fixing the gate (evaluate on the clock's
5-minute boundary instead of the bar count) is a strategy-execution change → backlog idea, not shipped here.

**(c) Crowding / caps / twin / risk blocks.** Blocked signals (B − taken) and what they would have made:
Primary 230 (−16.8 R, −0.073/signal), Testing 1 2,928 (−731 R, −0.250), Testing 2 3,560 (−492 R, −0.138). The blocks
*helped*: the largest is the account daily-loss halt (`halted`: Testing 1 983 signals −610 R, Testing 2 965 −341 R —
the stop fired on the worst days); `not shortable/ETB` removed losers too (−0.18 to −0.26/signal); `already in symbol`
and `lot cap` removed slightly positive signals on Primary/Testing 1 (+0.10 to +0.26/signal), negative on Testing 2.

**(a) Fill model.** On the same taken trades: production costs + trade-through (C) vs paper fills (D) is 12.5 R on
Primary (414 trades, 0.030 R/trade), 24.9 R on Testing 1 (0.012), 47.5 R on Testing 2 (0.016 incl. 231 more trades).
Of that, touch vs trade-through limit fills alone (C' − C) is +1.0 R (Primary), +23.3 R (Testing 1, 0.011 R/trade) and
+65.6 R (Testing 2, 0.015 R/trade): target-heavy setups (t05s1/t1s1, CWT) get most of their paper edge over the
research cost model from limit orders that only touched. Live paper entries fill a median 33 s into the minute and
0.037 R (3.3 bps) above the minute's open (5,229 live trades 10-12..10-21); the replay's half-spread paper model
reproduces that (matched-trade entry diff median ~0 bps).

**(d) Regime.** The validation sessions were wide-range days: median open-to-close of the lab universe −0.29%, +0.75%,
+0.22%, −0.13%, −0.10%, −0.32%, +1.28%, −1.02%, −0.51%, +1.06%, −0.13% (10-07..10-21; rule-19 cut points −0.23 / +0.21),
i.e. 4 up, 4 down, 3 flat, with four ±1% days. The
broad replay below compares the same setups across regimes and against the weeks before live trading began.

**Net:** backtest A → live E per signal/trade: Primary −0.090 → −0.159, Testing 1 −0.132 → −0.100, Testing 2
−0.097 → −0.121. For Primary, the gate accounts for −0.055 of the −0.069 R gap, blocks for −0.04 more on the taken set,
and paper fills give back +0.03; residual live vs paper-replay ≈ 0. For Testing 1 the blocks (halts) turn a −0.186
signal pool into −0.095 taken. These are 8–11 sessions — a mixed, volatile stretch — so the levels are noisy;
the decomposition (which step costs what) is the robust part.


## 3. Broad replay (today's setups, 2026-09-01..2026-10-21, costs in)

Primary and Testing 1 over 36 sessions: running at the time of writing; results are added below when complete.

## 4. Speed

Seconds per session per account (fast path on, 4 parallel workers on 4 cores shared with other jobs): Primary 190–290
(133 alone), Testing 1 290–520, Testing 2 270–530 (as live) / ~1,070 (today's 47 setups with 15 breadth-context ones).
Before the rvol / gate / heat optimisations one Primary session took 357 s, and the earlier research attempt (verify_live) > 30
minutes. What the fast path does (all verified each session, 0 differences in 1,000+ sampled frames/masks/rvols):
whole-session lab frames built once per symbol by the real `LabStrategy.generate` and shared across accounts,
whole-session masks per setup, heat scores per heat setup, the rvol series, memoised `heat_frame`, and a per-poll gate
that skips a symbol only when no setup can act on its latest bar (non-lab setups always run). Remaining cost: the
runner's per-poll context building on ~1,200 symbols (~35%), the feed slices (~15%), orb20 every poll, and context
setups. Next: cache DayContext objects across polls, and run setups with `context:` on a precomputed breadth table.

## 5. Pipeline and drift tracking (dashboard data)

`python -m mcf.replay export` writes `docs/live/replay.json` (per setup: trades, sessions, win rate, avg R,
day-clustered t, total R, last session; the research-rule run with the most sessions; `meta` names the run) and
`docs/live/pipeline.json` (per setup: stage backtest|replay|live, the {trades, win, be_win, avg_r, t} blocks for
backtest expectation / replay / live, the accounts, and `agreement` = replay vs live on the shared sessions, with
`drift: true` when |avg R gap| > 0.25 R with ≥ 10 trades on both sides; `system_agreement` per account). Design:
**backtest → replay (~50 recorded sessions through the live runner, costs in) → testing account → primary**; a new
setup gets its live-like evidence in hours (`run --setup NAME --module PATH [--alone]`), and every live setup keeps a
running replay-vs-live agreement so a divergence (data, execution, code) shows up per setup and system-wide.

## What was built (mcf/replay)

- **Harness** (`mcf/replay/harness.py`): runs one recorded session through the real `PaperRunner.run()` — restore,
  poll loop, contexts, every setup's `eligible()`/`signals()`, dedupe/re-entry/twin/caps/risk checks, quote cross-check
  and fill-realism, sizing, bracket submission through `AlpacaBroker`, trade management, `reconcile_day`, the 15:55
  flatten and the what-if pass. Priors are the live prep's own `build_priors` run against the replay store.
- **Simulated**: the clock (polls at hh:mm:03), the feed (a poll sees exactly the 1-minute bars that started before
  its minute), quotes (last close ± a spread drawn per symbol and minute from the 7,412 spreads the live runner
  journaled), the broker (`mcf/replay/broker.py`: a `TradingClient` stand-in — brackets/OTO/OCO/stops/market closes,
  netted positions, shares held by legs, Alpaca's bracket base-price rejects, fills from the recorded bars).
  Two fill models: `paper` (what Alpaca paper does: market/stop fills cross half the spread, limits fill on a touch)
  and `costs` (research rule 1: production costs from config, limits only when traded through by a cent; every touch
  that did not fill is recorded, so each trade also carries its touch-fill counterfactual `r_touch`).
- **Config as traded**: `--as-live` uses the setups frozen for that session on the account's data branch
  (`setups/<date>.json`) plus the account limits and costs committed before that session's open.
- **Universe**: the lab universe (research/lab_symbols.txt, 1,226 most liquid names; 2-year SIP history) ∩ the live
  universe.csv of that day, minus the recorded earnings blackout and the PTP denylist. Live symbols outside the lab
  universe cannot be replayed (counted below).
- **Data**: `data/replay/1Min/<date>.parquet` (one file per session) from data/cache_hist (ends 2026-10-16) plus a
  read-only Alpaca market-data fetch for 2026-10-19..21 (the only network use; no trading endpoint). The locked block
  2024-11-01..2025-02-28 is filtered out at read time and `check_dates` refuses sessions whose priors would touch it.
- **Speed** (`mcf/replay/fast.py`): every lab / heat feature is causal, so the whole-session frame, mask, heat score and
  rvol are built once per symbol (by the real code) and served as prefixes; a symbol is skipped in a poll only when no
  setup can act on its latest bar. Each session re-computes a sample of 24 (symbol, poll) frames, masks and rvols from
  the truncated bars with the real code: **0 differences in all samples of all runs** (`fast_check` in each stats.json);
  `--exact` turns the fast path off. Tests: synthetic session end-to-end (long + short + a heat setup), fast == exact,
  determinism, flatten reconcile, broker fill rules.
- **CLI**: `python -m mcf.replay prep|run|export` (see the module docstring); e.g.
  `python -m mcf.replay run --account testing2 --dates 2026-09-01..2026-10-07 --setup NAME --module PATH [--alone] --jobs 4`.
