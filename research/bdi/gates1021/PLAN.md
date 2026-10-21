# gates1021 - PLAN (written 2026-10-21 ~14:45 ET, BEFORE any configuration was scored)

*Educational only - not financial advice. History backtests only (not paper, not live). Live-day numbers come from
the journals and are labelled as paper/live.*

Owner request 2026-10-21 (~14:35 ET): (A) dive into NS3-failed-vwap-reclaim-short-FD and L3-gap-slope-fromopen-FD
(Primary lost ~-$534 today with them, ~+$43 without), test very small one-layer tweaks; (B) direction layer: B1 short
list of live setups whose 2-year backtest has a real, stable split by the market state known at entry; B2 one small
check-gate per such setup, tested as a new setup, with a participation check.

Only `research/bdi/gates1021/` is written. config/, mcf/, docs/, research/ledger.jsonl, research/owner_inbox/ and
research/backlog.jsonl are not touched. Nothing is committed.

## Data, split, costs (fixed)
- Open two-year lab frames (`research/history2y/lib.load_month(..., context=True)`), months 2024-10 and
  2025-03..2026-10 (frames end 2026-10-07). The locked block 2024-11-01..2025-02-28 is never read (lib refuses it;
  `common.py` asserts `MCF_HIST_ALLOW_LOCKED` is unset and that no locked date appears in any trade table).
- TRAIN = sessions <= 2025-12-31; VALID = 2026-01-01 onward. No holdout is scored.
- Costs always in: lab outcome -> production R exactly as `gates.prod_r` (1c + 1 bps per side, exit side free on a
  target fill, +2c on stop fills, entry side x time-of-day multiplier), x3 on the extended tier (|gap| >= 20% or
  price < $5; config/default.yaml `extended_slippage_per_share` 0.03 = 3 x 0.01), as research/bdi/longs1020.
- R = 0.25 x daily ATR; entry at the decision-bar close; exits from the frames' per-bar lab outcome (t1s1 / t05s1 /
  t1s05, flat 15:55).

## Live-shaped trade generation (every setup)
- Mask on the frame (with the context columns), decision bars inside the setup's YAML window and 09:50-15:00,
  adv20 >= min_adv, ATR > 0. Signals: the first hit per symbol-day, or, when the setup's account config has
  `refire: true`, the LabStrategy refire chain (`mcf.strategies.setups.refire_select` on decision-bar numbers, the
  configured cooldown) - the same chain live uses.
- Exit time of each lot: the 5-minute path in the frame (stop checked first, then target, bar after entry onward;
  no exit by the 15:00 row = held to 15:55). Agreement with the frame outcome's win flag is reported.
- Part A "parent-live" also applies the lot cap of 3 lots of this setup per symbol (live `max_lots_per_symbol: 3`,
  `same_setup_reentry: true`). Other setups' lots, the portfolio caps, shortability/ETB and spread skips are NOT
  modelled (stated in NOTES).
- Same-minute random control: for every (date, tod) the mean production R of all frame rows with adv20 >= $95M for
  the same side and geometry (= a random same-minute entry). Excess = trade R - control R.

## Market state at entry (all known at the decision-bar close)
`spy_fo`, `qqq_fo` (% from the open), `breadth` (share of the universe above its VWAP), `d2` = breadth minus breadth
two decision bars earlier (defined from the 10:00 bar; NaN at 09:50/09:55, so a slope rule never blocks those bars -
offline and live then agree), prior-day SPY close-to-close return (NaN on the first session after a data gap).
Buckets: spy_fo / qqq_fo <= -0.5, -0.5..-0.15, -0.15..0.15, 0.15..0.5, >= 0.5; breadth < 0.35, 0.35-0.5, 0.5-0.65,
>= 0.65; d2 <= -0.05, middle, >= +0.05; prior day <= -0.5, middle, >= +0.5. Hindsight day types (reporting only):
regime up/flat/down (`lib.regimes`, universe median open-to-close terciles), SPY open-to-close, choppy =
|SPY o->c| < 0.3%.

## Candidate gates (fixed list, 14 per setup; a gate BLOCKS entry in its state)
Market-up states: U1 spy_fo >= +0.50; U2 spy_fo >= +0.25 and d2 > 0; U3 qqq_fo >= +0.50; U4 qqq_fo >= +0.25 and
d2 > 0; U5 breadth >= 0.65; U6 d2 >= +0.10; U7 prior-day SPY >= +0.5% and spy_fo >= +0.25.
Market-down mirrors: D1 spy_fo <= -0.50; D2 spy_fo <= -0.25 and d2 < 0; D3 qqq_fo <= -0.50; D4 qqq_fo <= -0.25 and
d2 < 0; D5 breadth <= 0.35; D6 d2 <= -0.10; D7 prior-day SPY <= -0.5% and spy_fo <= -0.25.
Both directions are tested for every setup (the unfavourable state is found from the data, not assumed by side).

## Part A - NS3-failed-vwap-reclaim-short-FD and L3-gap-slope-fromopen-FD (16 configurations each = 32)
Parent-live A0 = Primary config (NS3-FD: min_adv 95M, refire cd1; L3-FD: min_adv 0, refire cd1) + lot cap 3.
1. A0 parent-live (baseline).
2. A1 first signal per symbol-day only (refire off).
3. g1 no re-entry on a symbol after this setup was stopped there that day.
4. g2 one lot at a time per symbol (no new signal while an earlier lot of this setup is open there).
5-6. g3 skip when spy_fo >= x and d2 > 0, x in {0.25, 0.50} (owner's form).
7-8. g4 skip when qqq_fo >= x, x in {0.25, 0.50}.
9-10. g5 peer gate (research only, needs live code): skip when the median fromOpen of the stock's 5 most-correlated
   peers (TRAIN daily close-to-close returns, non-ETF lab symbols with >= 120 train days, >= 3 peers present at the
   bar) is >= y, y in {+1.0, +2.0}%.
11-13. g6 time of day: entries only at bar close <= 11:30; <= 13:00; >= 10:30.
14-15. g7 setup-level concurrency: skip when this setup already holds >= K open lots (any symbol), K in {5, 10}.
16. g8 per-setup daily loss stop: no new entries once this setup's realized R that day is <= -2R (Testing rule).
Descriptive (not configurations): A0 trades split by every state bucket and day type, train and valid, with the
same-minute random control in the same buckets; re-entry-after-stop, stacked-lot and cluster statistics.

## Part B1 - short list (descriptive)
Every live lab setup of Primary / Testing 1 / Testing 2 (docs/live/assignments.json, merged configs) whose outcome
the frames carry (geometry t1s1 / t05s1 / t1s05, no 09:35-09:45 opening-range logic, no 1-minute VWAP-band guard,
no ETF allow-list); the rest are listed as not covered. Setups with identical module / window / min_adv / refire are
scored once. For each setup and each of the 14 gate states: trades in the state (share), mean R in vs out, the gate
delta (= -sum R of blocked trades / parent trades; day-clustered t), on train and valid.
**Real, stable split** (pre-declared): a state with >= 3% of trades in each split, blocking it improves avg R in
both splits, gate delta t >= 2.0 on train and >= 1.0 on valid. Short list = setup -> unfavourable state(s)
(favourable = the rest).

## Part B2 - one check-gate per short-listed setup
- The gate = the short-listed state with the highest TRAIN delta t among those that block <= 20% of train trades.
  Exactly one gate per setup, named `<setup>-g1` (`-g2` if a setup needs a second, independent try: not planned).
- Acceptance (all required): (1) participation: keeps >= 80% of the parent's trades on train AND valid (reported:
  % of trades blocked, % of the parent's winners blocked); (2) gated avg R > parent avg R after costs on train AND
  valid; (3) pooled (train + valid) gate delta day-clustered t >= bar = max(1.5, sqrt(2 ln N)), N = every
  configuration of this study (Part A 32 + Part B 14 x covered setups; B1 and B2 share the same evaluations, the
  B2 choice is not an extra configuration). Reported, not gating: choppy-day (|SPY o->c| < 0.3%) blocked share and
  delta, regime split, delta on the same-minute random control (how much is plain market beta), without-best-day.
- Finalist = passes (1)-(3). Near-miss = passes (1)-(2) only. Every evaluated gate is in `results_B.csv`.
- Finalists and near-misses get a module in `modules/` (parent mask + one context clause, LabStrategy
  `context:` columns only, so no live code is needed), checked for parity against the scan.

## Live-day diagnosis (paper/live, not a test)
Primary journal (origin/mcf-data, run_id 1) for 2026-10-21; 1-minute SIP bars for 10-20/10-21 fetched read-only
(scripts/fetch_today.py; market-data GET only) to compute SPY/QQQ from open, breadth and peer moves at each entry.
Also: would the Testing per-setup -2R realized daily stop have helped today (replayed on the journal's own exit times).

## Lineage bars (reported)
NS3 lineage: research/swarm1017 rework-ns counted 165,764 configurations (bar 4.90); this study adds its own N.
