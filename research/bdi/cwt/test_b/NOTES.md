# CWT package B - intraday VWAP, level, mean-reversion and breakout setups (worker CWT-B, 2026-10-12)

*Educational only - not financial advice. Backtest results on the open two-year history only; nothing here is a paper
or live result. Guest descriptions are paraphrased from `../CATALOG.md`; no transcript was opened.*

**Verdict: all 7 families FAILED. 368 of 368 pre-declared configurations scored, none clears the live-probation bar,
none reaches its family t bar, and none beats its lineage bar or the round bar (t >= 3.73). No lab module was written
because there is no candidate.** Nothing was scored on the locked block (2024-11-01..2025-02-28), and nothing needs to be.

## 0. What ran

- Plan: `../TESTPLAN.md` section 3, run as declared (B1 32, B2 64, B3 96, B4 32, B5 64, B6 32, B7 48 = 368), with the
  package B amendment of 2026-10-12, which was written into TESTPLAN.md before anything was scored.
- Data: lab frames from `research/history2y/lib.py` (21 open months, 426 sessions; the locked months are never loaded),
  point-in-time adv20 >= $95M (the Testing -FD floor). The 09:30-09:45 and 15:00-15:55 5-min bars are rebuilt from the
  1-minute cache (`prep.py`; the locked block is filtered out at read). Daily features: `ret5` and `beta60` from the
  10-year daily file, and `near252` / `ret20` for B7 (a). All locked rows are dropped before any rolling computation.
- Checks: the head/tail rows match the frames at the shared 09:50 / 10:00 / 12:00 / 15:00 bars (close, high and VWAP
  agree 100% within 0.1% in every month). The re-simulated lab geometries match the frames' `r_*` columns on 99.998%
  of sampled rows (worst month 99.985%).
- Costs: `gates.prod_r` rules (1c + 1 bps per side, the exit side free on target fills, +2c on stops). The entry side
  pays `gates.tod_cost_mult` (1.4x before 10:30), and slippage is x3 when |gap| >= 20% or price < $5. R = 0.25 x daily
  ATR. Each configuration takes one trade per symbol-day (the first qualifying bar in its window), enters at the
  signal bar's close, and exits by the 15:55 bar.
- Controls: a random same-side, same-window baseline (one random bar per symbol-day, same exit). For S exits the
  baseline holds to 15:55 with a 1R stop. Every trade is also re-scored SPY-hedged (beta60, SPY leg costs in).
  FOMC-week sessions are a reporting split only.
- Gates: `mcf/research/gates.py`, i.e. the regime split, walk-forward (3m/1m), the try-count t, the plateau (same
  family / side / exit / window, one grid level away), ex-best-day and the busiest-session share.
  Live-probation bar (swarm1010/RULES.md): n >= 150, exp > 0 up AND down, t >= 2.0, WF >= 0.6, plateau > 0,
  ex-best-day > 0, busiest session <= 10%.
- Machine: one process. The peak RSS was 2.73 GB on the largest month, slightly over the 2.5 GB target (noted
  honestly; no other worker was starved). Scoring took about 14 minutes. `data/` (git-ignored) holds 258 MB.

## 1. Implementation choices fixed before scoring (amendment, details)

- B1: breakdown = the first bar with run_hod >= a, drop_hod >= 0.4 and close < VWAP. A new session high resets it.
  T1 fires on a later bar whose high reaches VWAP - 0.05 ATR and closes below VWAP. T2 fires on a later bar when the
  bounce since the post-high low retraces 38-62% (measured through the prior bar) and the bar closes below the prior
  bar's low. Stop = the highest high since the breakdown.
- B2: the extreme bar closes within 0.05 ATR of the high of day (low of day), |close - VWAP| >= z ATR and
  rng_used >= 0.4. The signal is the next bar if it makes a lower high (higher low). Stop = the extreme +- 0.1 ATR.
  The S limit is the prior bar's VWAP.
- B3: an excursion starts on the first bar trading >= p ATR beyond the level after a close inside. The trigger is a
  close back inside within 3 bars of that start; an excursion that stays outside longer is an accepted break, and it
  is not traded. V = the volumeRatio of the excursion's first bar. Stop = the poke extreme. The S limit is the
  prior-day midpoint (PD) or the other OR side (OR). An S target on the wrong side of the entry is dropped (the trade
  holds to 15:55).
- B4 (a): touches = bars whose high is within 0.1 ATR of the current high of day (>= 3). The coil = the last n bars,
  each with a range < 0.5x the mean range of up to 20 earlier session bars (>= 6 needed), and closes within 0.25 ATR
  below the high of day. (b): the push from the open >= s ATR. The pullback depth since the high is 30-50% of the
  push, with every low since the high above VWAP. The buy is a close above that high, and the stop = the pullback low.
- B5: the flush, B6, B7 (a) and B7 (b) are as in the amendment. For B7 (b), RS = fromOpen - beta60 x SPY fromOpen,
  and its running max is taken over the bars to 10:15 (causal). The fall must come after the max bar. The trigger is
  the next bar with RS rising and a close above the prior high. Stop = the lowest low since the max.

## 2. Results (failures first; all 368 rows in `RESULTS.md` / `results.csv`)

| family | configs | exp > 0 | best by t (n >= 30) | t bar fam / lineage | why it fails |
|---|---|---|---|---|---|
| B3 CWT14 failed breakout / stop-run reversal | 96 | 0 | OR long S guest: n 39,989, -0.105R, t -4.25 | 3.02 / 4.84 | All 96 configurations are negative, with t from -4.3 to -11.8 on 17k-105k trades. Fading a poke through the prior-day or 30-min range does about as well as a random bar minus costs (mean -0.108R vs baseline -0.087R). The shorts lose about -0.21R in up sessions. |
| B7 CWT11 VWAP trend pullback (new variants) | 48 | 0 | (a) RSI < 25 S guest: n 10,397, -0.055R, t -1.73 | 2.78 / 3.38 | All negative. They beat the random baseline in every configuration (-0.072 vs -0.089), but never after costs. The (a) universe (a close near the 252-day high plus a 20-day return >= 15%) is large: 3-21k trades. |
| B1 CWT04 backside lower-high short | 32 | 8 | a2.5 T2 t1s1 guest: n 152, +0.186R, t 0.90 | 2.63 / 5.06 | Every positive configuration is one day: 2025-04-07 carries 406 of 1,251 trades (+278R) in a1.5-T2-t1s1. The busiest-session share is 0.32-0.45, ex-best-day is negative, the up/down sign is inverted, WF is <= 0.35 and the hedged t is -2.5 to -6.5. Flagged "borrow unverified" (runners). |
| B5 CWT05 panic flush V-reversal long | 64 | 11 | m0.75 v5 none t1s1 guest: n 142, -0.118R | 2.88 / 4.53 | The positive configurations all have n <= 8 (the ret5 <= -15% filter leaves almost nothing). With n >= 30, every configuration is negative. |
| B2 CWT13 stretched-from-VWAP fade | 64 | 11 | index long t1s1 guest: n 34, +0.142R, t 0.69 | 2.88 / 3.24 | The all-symbol versions are negative (t down to -6.8). The index-ETF versions have n 9-35 in two years. No configuration passes the regime gate. |
| B4 CWT12 flag / coil breakout | 32 | 2 | (b) s2 S full: n 79, +0.539R, t 1.45 | 2.63 / 3.19 | The two positive (b) s=2 configurations rest on 2025-04-09 (14 trades, +17R), and their hedged exp is +0.02. The coil (a) fires very often (13-62k trades) and loses (t down to -11.2). |
| B6 CWT46 afternoon breakout in a strong mover | 32 | 12 | u4 w0.5 none t1s05: n 348, +0.009R, t 0.22 | 2.63 / 2.63 | About flat. It is the only family well above its baseline (-0.024 vs -0.088), but up sessions are negative in most configurations and n is 10-348. One configuration passes the regime gate, at t 0.22. The setup defines its own 13:35-15:00 window, so it has no full-day version. |

- Probation bar: **0 / 368 pass**. Family t bar: 0 reached. Lineage t bar: 0 reached. Round bar 3.73 / package bar
  3.44: 0 reached. Expected false positives at p 0.05: about 18, and the positive tails seen (all <= t 1.57 with
  n >= 7) are consistent with noise.
- Market-neutral control: no configuration with n >= 30 has a hedged t >= 2. Where a short looks positive (B1), the
  hedged version is clearly negative, so the gain was market beta on one day.
- Time of day: the full-day and guest-window versions agree in sign in 160 of 164 pairs (the 4 flips are small-n
  B2/B5 cells). Positive configurations per window (full/guest): B1 4/4, B2 5/6, B3 0/0, B4 1/1, B5 8/3, B7 0/0.
  No window rescues a family.
- Survivorship: today's 1,226 names applied to 2024-25. This favours longs; it does not explain the failures.

## 3. Observations for the backlog (not tested here, not proposed)

- B3 "with the break" is the mirror of a failed fade. It is not implied to work: the fade sits only about 0.02R
  below random, so the mirror would be about random minus costs. ORB lineages already failed.
- B6 is the only family that beats its random baseline by a wide margin (+0.06R), at n <= 348. A larger universe
  (lower ADV tier, where Desai/Capablanca trade) could be tried as a new lineage step. That needs a rework round
  with its configurations counted.

## Files

- `prep.py` (head/tail rows, rvol12, daily features), `score.py` (grid, kernels, exits, costs, baselines), `report.py`
  (gates, plateau, `results.csv`, `RESULTS.md`).
- `data/` (git-ignored): `headtail.parquet`, `rvol12.parquet`, `daily_feat.parquet`, `trades.npz` (all trades per
  configuration), `baseline.json`, and the logs.
