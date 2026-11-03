# night1102 / simple - pre-declaration (written before any configuration was scored)

*Educational only — not financial advice.*

Question (owner 2026-11-02): are our setups too complex; do simpler forms work better, and with more trades?

1. **Census** (`live_census.py`): every enabled setup in the 5 account configs, its entry-condition count (module
   LAYERS / TRIGGER+FILTERS / CONDS, time windows and ADV floors counted separately; CWT loop kernels and classic
   strategies counted by hand from their code), its live paper record 10-06..11-02 (journals run_id 1, avg R =
   pnl_adj / $ risk), and the backtest expectation in docs/live/leaderboard.json where one exists. Correlate
   condition count with live avg R, trades/session and live - backtest gap (Spearman, per setup with >= 10 trades).
2. **Kernels** (busiest live setups whose conditions can be separated on the lab frames; the busiest overall,
   CWT14 failed-breakdown, included via loop parameters): CWT14-failbrk-pdl-p10-long, RW7-gapdn-bounce-early-short-FD,
   exhaustion_short-FD (with the RW2 ADV150 twin), CWT13-vwapstretch-z05-long, ST2-slope20up-long-am-t05s1-FD,
   RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (Primary) and RW3-gapdn-rsi5pop-flowsell-short-FD (Primary).
   Not decomposable here: heat_fade_short-FD (one composite heat threshold), CWT12-coil (loop), GEN-ORBfailUp (hold
   exit, no frame outcome).
3. **Forms scored per kernel:** every non-empty subset of its separable conditions (leave-one-out, pairs, singles =
   the 1-2 condition cores), same side, exit geometry, window, ADV floor and first-signal-per-symbol-day as live.
   CWT14: poke depth p in {0.10, 0}, reclaim limit {3 bars, none}, lowvol on, and the 1-condition "close crosses
   above the prior-day low". Identical masks are counted once.
4. **Data / splits:** history2y open frames; TRAIN = 2024-10, 2025-03..2025-12; VALID = 2026-01..03, 2026-07-01..
   09-15. Old holdouts (2026-04..06, 2026-09-16..10-05) not scored. **Locked block 2024-11-01..2025-02-28 never
   loaded** (lib.months() lists open months only; asserted). LIVE = 2026-10-06..11-02 lab frames rebuilt from
   1-minute SIP bars of the replay universe (1,226 names; `build_live_frames.py`), same pipeline; plus the parent's
   actual paper trades from the journals.
5. **Costs:** gates.lab_trades (production 1c + 1 bps per side, +2c on stops, time-of-day entry multiplier).
   **Random control:** day-matched — each trade minus the mean production R of every eligible bar (same side, geometry,
   window, ADV floor) on that date; excess and its day-clustered t reported.
6. **Pre-declared reading:** a simpler form *keeps* if its TRAIN+VALID avg R >= the parent's with >= the parent's
   trades; it is a *twin worth forward observation* if it also is > 0 in TRAIN and in VALID, beats the random control
   in TRAIN and VALID, and is >= the parent on the LIVE re-score. Ranking: LIVE re-score avg R (owner: live first),
   ties by TRAIN+VALID t. BAR90 (rule 22) status is reported for each; nothing is proposed for config here.
