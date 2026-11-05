# BURST1 — pre-registered plan (owner 2026-11-05, written before any remedy was scored)

*Educational only — not financial advice.* Research only: nothing in config/, mcf/ or the trading path changes.
Locked block 2024-11-01..2025-02-28 is never read (`lib.load_month` refuses it; MCF_HIST_ALLOW_LOCKED unset).

## Failure situation (from the step-0/1 diagnosis of 11-04 / 11-05, Primary)
One setup opens many same-side positions within minutes (MF4-FD: 14 shorts 11:00-11:10 on 11-05 at the QQQ low,
stopped together 11:10-11:18 in a +2% index bounce; MF2-FD: 7 shorts 12:05-12:10 on 11-05 and 6 at 12:15 on 11-04,
stopped within ~10 min). The realised-only -2R latch cannot act: every position is entered before the first exit.
Dollar risk per lot is not constant (sizing = min(0.25% equity, slot notional ~$3,980) -> $ risk = slot x stop%), so a
burst into high-ATR names carries several times the usual $ per R.

## Remedies (each acts only in the failure situation). 16 configurations in total.
All per-setup rules are evaluated per setup-day in entry order (ties: file order); a blocked signal is simply not
taken (no displacement, no re-entry later). Kept positions are the only ones that count toward any rule.
- **(a) pacing** N in {2, 3, 4}: a setup's new entry is blocked if >= N of its kept entries have entry time in the
  previous 15 minutes (t-15min, t]. (3 configs)
- **(b) open-loss latch** L in {-2, -3}: like the live latch, but the setup's daily R = realised R of kept trades
  exited at or before t + mark-to-market R (5-min bar close at t, stop units, gross) of its open kept trades; once
  <= L, no new entries for the rest of the day (latched). Scored against no latch AND against the live realised -2R
  latch. (2 configs)
- **(c) first-out-first** K in {2, 3, 4}, x = 0.5R: a new entry is blocked while the setup has >= K open kept
  positions that have not yet exited and whose MFE-to-date (5-min high/low since entry) is < 0.5R. (3 configs)
- **(d) cross-setup same-side cluster cap** M in {4, 6, 8}: per account (setups.csv composition) and side, a new entry
  is blocked if >= M kept same-side entries (any setup of the account) entered in the previous 15 minutes. (3)
- **(e) burst needs compass** B in {2, 3}: an entry that would be the setup's (B+1)-th kept entry within 15 min is
  blocked if the GATE1 state at the last 30-min checkpoint before it is against the side (UP for shorts, DOWN for
  longs; research/bdi/gate1/state.py). Non-burst entries are never touched. (2)
- **(f) $ risk cap per lot** C in {$50, $75, $100}: shares = min(current shares, C / stop distance); R per trade is
  unchanged, so it is scored in dollars (trade $ = R x risk$; risk$ = min($250, $3,980 x stop%) as Primary's sizing).
  2-year stop% = geometry stop x 0.25 x daily ATR / entry. (3)

## Data and windows
- 2-year: `research/history2y/data/bt_lab1104` trade lists (95 setups, uncapped, production costs), enriched with
  5-min mark-to-market / MFE paths from the frames (same walk as bt_all.py). TRAIN = open dates <= 2026-02-28;
  VALID = 2026-03-01..2026-10-05. Live = all 7 accounts' journals 2026-10-06..2026-11-05 (run_id 1 trades; latch-
  blocked what-ifs from run_id 2 added back for the latch comparison), MTM from Alpaca 5-min bars (GET only).
- Backtest books are negative on average, so any block "helps". Every remedy is therefore also scored by the
  **excess delta**: blocked trades valued against their setup's own TRAIN average R (delta_excess = -sum(r_blocked -
  mean_r_setup)). This isolates timing/selection from "trading less of a losing book".

## Metrics per config and window
Total R, avg R per kept trade, avg R w/o best day (and best day share), green-day rate in R (account-days), max
drawdown of the daily R curve, delta vs baseline with day-clustered t (raw and excess), and the **per-setup and
per-family effect table**: # setups improved / worse, worst harm (R and setup), same per family (family = name prefix
before the first '-': MF, RW, L3, CWT.., GEN, ...). Replays of 11-04 and 11-05 (Primary, live).

## Decision rule (fixed now)
Bar = max(1.5, sqrt(2 ln 16)) = 2.35. A remedy passes only if (1) VALID raw delta day-t >= 2.35 AND VALID excess
delta day-t >= 1.0, (2) TRAIN raw and excess deltas > 0, (3) live delta (all accounts) > 0, (4) no family is
materially harmed: no family with VALID delta < 0 at day-t <= -1.0, and in no family do more setups get worse than
improve by more than 2:1 with a family loss > 5% of that family's |R|. For (f) the same tests apply in dollars.
Pass -> DECISION card in research/owner_inbox/2026-11-05.md. Else the best near-miss (highest VALID excess t with
TRAIN > 0) becomes a journal-only forward shadow in research/bdi/swings/hypotheses.jsonl + FYI.
