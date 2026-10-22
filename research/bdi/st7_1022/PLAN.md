# st7_1022 - PLAN (written 2026-10-22 08:10 ET, before anything was scored; not edited after scoring)

*Educational only - not financial advice. Research only: no config, setup or exit change (market hours today); any
proposal goes to the owner. Backtests on the open two-year lab frames (2024-10, 2025-03..2026-10-07). The locked block
2024-11-01..2025-02-28 is never read (history2y/lib refuses it; the 1-minute cache is read with a row filter that
drops it before any value is used; every loader asserts no locked date survives). No holdout is scored.*

Owner 2026-10-22: "Review ST7-rsi50dn-long-pm-t1s1-FD - labeled good for bull markets (dashboard 'Best conditions'
chip) but performed poorly yesterday. Why? ... Deep dive it and see if a variant can be created to make it more
profitable on up-market days." Don't trade away its down-day strength.

## Parent and reference rows
- **P0 = ST7-rsi50dn-long-pm-t1s1-FD as run in Testing 1**: mask `RSI(14) crosses below 50 (prev >= 50, now < 50) &
  RSI(14) <= 30 & fromOpen < -1.0 & buyPressure > 0`, bar close 09:50-15:00, adv20 >= 95M, long, t1s1 (R = 0.25 x daily
  ATR, flat by 15:55), refire off (first signal per symbol-day), lot cap 3 (never binds with one signal per
  symbol-day). Must reproduce regime1022 k26: 1,035 trades, +0.0236R (train -0.0616 / valid +0.0712).
- **P1 = the windowed parent ST7-rsi50dn-long-pm-t1s1** (13:35-15:00, disabled in config), reference row (not counted).
- Costs always in: production cost (1c + 1 bps per side, exit side free on a target limit, +2c on stop fills),
  time-of-day entry multiplier, x3 on the extended tier (|gap| >= 20% or price < $5) - gates1021 `prod_r_tier`.
- TRAIN = sessions to 2025-12-31; VALID = 2026-01-01..2026-10-07.
- Regime labels: regime1022 `scripts/regime.py` (SPY regular session, hindsight): Bull o2c >= +0.5%, Bear <= -0.5%,
  Choppy |o2c| < 0.5% with range >= 20-day median, Quiet otherwise. **Choppy-up** = Choppy with o2c > 0 (10-20, 10-21
  type). "Up days" = Bull + Choppy-up. Labels describe and judge; never an entry input.

## Exit simulator
5-minute path rebuilt from the 1-minute SIP cache (data/cache_hist/1Min, bar close tod = end of the 5-minute bucket,
through the 15:55 bar - the lab frames stop at 15:00). Entry at the signal bar close; stop first when stop and target
fall in the same bar; timed exit at the close of the last bar <= 15:55 (setup_lab `_outcomes_asym`). Parity test before
any variant is scored: the simulator's t1s1 / t05s1 / t1s05 must equal the frames' lab outcome on >= 99% of P0 signals
(lab cost 1c/side), then production costs as above.

## Part 0 - live 10-20 / 10-21 (descriptive)
Each live trade (journal origin/mcf-data-testing run 1): entry time, setup state at the signal bar (RSI, prev RSI,
fromOpen, buyPressure, gap, cohort), SPY / QQQ path (fromOpen and VWAP side at entry and over the hold; read-only SIP
bars), MFE / MAE, exit. Is -2.5R on a Choppy-up day normal: share of P0's traded days (2 years, and Choppy / Choppy-up
days) with a day total <= the 10-21 live day total; streaks.

## Part 1 - diagnosis of P0 (descriptive, not counted)
Splits (train / valid / 2 years; n, avg R, total R, day-clustered t): regime (4 labels + Choppy-up / Choppy-down);
time of day (09:50-10:40, 10:45 exactly, 10:50-11:55, 12:00-13:30, 13:35-15:00); RSI at entry and RSI drop in the
trigger bar; fromOpen; gap (down / flat / up); RS vs SPY (fromOpen - SPY fromOpen); SPY and QQQ above / below their
VWAP at entry; SPY fromOpen sign; breadth level and 2-bar change; buyPressure; volume ratio; daily ATR%; signals in the
same bar (1 / 2 / 3+); trade # of the day. Same-minute random longs as the baseline. Where the regime split comes from
(train vs valid).

## Part 2 - pre-declared variants (every row counted; one or two knobs each)
Entry filters (inside the mask, then first signal per symbol-day):
- A1 SPY above its VWAP at entry (1); A2 SPY fromOpen > 0 (1); A3 breadth rising (2-bar change > 0) (1);
  A4 QQQ above its VWAP (1)
- A5 RS vs SPY (fromOpen - SPY fromOpen) >= -2.0 / >= -3.0 (2)
- A6 drop the 10:45 bar / only the 10:45 bar (2)
- A7 gap > 0 / gap <= 0 (2)
Entry windows: B1 09:50-12:00, B2 12:00-15:00, B3 09:50-11:00 (3)
Thresholds (+-10% / +-20%): C1 RSI <= 27 / 33 / 24 / 36 (4); C2 fromOpen < -0.8 / -0.9 / -1.1 / -1.2 (4);
C3 trigger level 45 / 55 (2)
Exits on P0 signals: D1 target 1.5R (t1.5s1); D2 target 2R; D3 no target, stop 1R, hold to 15:55; D4 1R trailing stop
(from the best high), no target; D5 target 2R + stop to entry after +1R; D6 half at +1R, rest held to 15:55 with the stop
at entry; D7 t05s1; D8 t1s05 (8)
Crowding: E1 at most 1 / E2 at most 2 entries per 5-minute bar (first by symbol order is arbitrary -> keep the lowest
RSI) ; E3 at most 5 entries per day (earliest) (3). One lot per symbol / cooldown: not applicable (refire off: one
signal per symbol-day already) - reported, not counted.
Tape-conditional exits (up-day idea, entry rule unchanged): F1 SPY above VWAP at entry -> D3 (hold), else t1s1;
F2 SPY above VWAP at entry -> D2 (2R), else t1s1 (2)
Pairs (selected on TRAIN only, judged on VALID): G = the 3 best entry rows (A/B/C/E) by TRAIN avg R with TRAIN
n >= 100 x the 2 best exit rows (D/F) by TRAIN avg R (6).

Count: A 10 + B 3 + C 10 + D 8 + E 3 + F 2 + G 6 = **42 configurations**. Study bar max(1.5, sqrt(2 ln 42)) = 2.73.
ST lineage: swarm1017 rework-st ~227,400 + tf1019 t1-rw-st 95 + regime1022 ST7 gate rows 6 + 42 = ~227,543 ->
lineage bar sqrt(2 ln N) = **4.97**. Anything added later is counted and reported as added.

## Part 3 - how each row is judged (pre-declared)
Per row, train and valid: n, kept %, avg R, total R, day-clustered t, avg R by regime (Bull / Bear / Choppy / Quiet and
Choppy-up), worst day, mean of the worst 5% of days, largest single-day share of total R, excess vs same-minute random
longs (same exit rule, 3 random adv >= 95M symbols at the same bar), "vs random thinning" (total R - P0 total x kept
share).

**Merit as a NEW Testing setup (owner's rule):** Testing bar = avg R > 0 in train and valid, beats same-minute random in
both, day-clustered t (2 years) >= 4.97 (lineage) - or the near-miss rule: avg R > 0 after costs in BOTH train and
valid, beats random in both, >= 30 train / >= 20 valid trades, no single day > 25% of total R.
**Plus the owner's "don't over-correct" guard (both required for a proposal):** (i) up days (Bull + Choppy-up) avg R
above P0's in train AND valid; (ii) Bear-day avg R over 2 years >= P0's Bear-day avg R - 0.05 and Bear-day total R in
VALID (where P0 is positive on Bear days) >= 75% of P0's.
A variant meeting merit + guard gets a lab module in `modules/` (module-vs-scan parity checked) and a DECISION in
research/owner_inbox/2026-10-22.md (reply S1/S2); otherwise one FYI. Ideas go to `backlog_proposals.jsonl`.
