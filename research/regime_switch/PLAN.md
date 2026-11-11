# REGSW — switching setups on/off by the market compass or other factors (pre-registration)

*Educational only — not financial advice.* Research only: no config, setup, exit, ledger or workflow change.

Owner 2026-11-10 ~21:40 ET: "hard and thorough research into switching setups on/off based on either the market
compass or other factors." This file is committed **before any switch is scored**. Everything below is fixed in advance;
anything added later is labelled as added and counted.

## What already exists (not redone)
compass_5m (compass = rest-of-day side, coin flip on 5-90 min), compass_learn, GATE1 (failed 2y; forward shadow),
l3leash / l3leash2 (26 compass/SPY leashes on L3-fromopen, 0 pass), top20/CONDITIONS (RW3-FD / L3-fromopen
opposite SPY-at-10:00 dependence), rq1_1103 REG1/REG2 (parked), night1102 QDAY, BRAKE-1 shadow, stoplab, latch1103,
swing1110. REGSW is the cross-setup generalisation: many setups, many signals, three matching rules, one pass bar.

## 1. Unit and mechanics
- Unit = setup × session. At each decision time **09:50, 10:00, 10:30, 11:00, 12:00, 13:00** the switch reads the
  signal state (point-in-time, data up to that minute only) and sets the setup's weight **1 (ON) / 0.5 (HALF) / 0 (OFF)**
  for every trade *entering* from that time until the next decision time ("re-evaluated" mode, the main mode). Trades
  entering before 09:50 are always ON. Sensitivity (finalists only): **sticky** mode (once switched, stays switched).
- The switch sits on top of the base: the base trades are simulated once (B0 below) and the switch scales their R.
  A switched-off trade frees no slot and does not re-simulate the latch (stated limitation, same for every config).

## 2. Data and splits
- **Lab:** `research/history2y/data/bt_lab1104/sig_*.parquet` (live-shaped signals, production costs in the `r`).
  B0 = per-setup −2R daily latch, ≤ 3 lots/symbol, ≤ 30 open per setup (as L3LEASH B0).
  **Shorts are ETB-restricted** with the L3LEASH-2 E90 proxy (symbol shortable+ETB on ≥ 90% of the committed
  universe.csv snapshots; unknown symbols dropped).
- **Locked block 2024-11-01..2025-02-28 is never read** (filtered at load, asserted).
- Splits as compass_5m / COMPASS-LEARN: **TRAIN** 2024-09/10 + 2025-03..2025-12, **VALID** 2026-01-01..10-05,
  **FWD** 2026-10-06..11-04 (lab ends 11-04).
- **Live check:** run-1 (real paper) trades of the target setups in every account journal (Primary, Testing 1,
  Testing 2, Graveyard, Live Lab, Explore 1, Setup Generator), 2026-10-06..11-10 (Primary 26 sessions).
  R = pnl_adj / (|entry − stop| × shares) (costs in). Live trades are not re-simulated; the switch scales their R.
  Live is labelled separately (rule 7); rule changes inside the window are listed from research/ledger.jsonl.

## 3. Targets (resolved by rule, no R looked at)
- **Core:** TEAM-6 (RW3-FD, RW5-FD, L3-gap-slope-fromopen-FD, ST7-FD, NS5-sma50-flush-oversold-long; NM-ETF has no lab
  list → live only) ∪ the 11-10 top-20 leaderboard (research/bdi/top20/CONDITIONS.md) ∩ lab.
- **All:** core ∪ every setup with ≥ 20 run-1 live trades in Primary / Testing 1 / Testing 2 that has a bt_lab1104 list.
- Family = side × leading letters of the code (RW3 → RW, CWT14 → CWT, L3 → L, MF4 → MF, NS3V1 → NS, ...).

## 4. Signals (pre-declared; state ∈ {+1, 0, −1} at the decision time)
| id | signal | +1 | −1 |
|---|---|---|---|
| CMP | W60 compass (state15 history, live = production compass record) at the last 15-min mark ≤ T | UP-confirmed | DOWN-confirmed |
| CMPL | W60 incl. leaning | leaning/confirmed up | leaning/confirmed down |
| SPYO | SPY % from open | > +0.10% | < −0.10% |
| IDX3 | SPY, QQQ, IWM all beyond ±0.10% the same way | all up | all down |
| GAP | SPY open vs prior close | > +0.25% | < −0.25% |
| BRDO | breadth: share of lab names above own open | > 0.60 | < 0.40 |
| BRDV | breadth: share of lab names above own VWAP | > 0.60 | < 0.40 |
| RVOL | SPY realised vol 09:30→T (Σ abs 1-min returns) / median of the same window over the prior 20 sessions | > 1.25 (high) | < 0.80 (low) |
| VXX | VXX % vs prior close (VIX-futures ETN; **the VIX index and its term structure are not in the data → skipped**) | < −2% (calm) | > +2% (fear) |
| PDT | prior-day SPY open-to-close | > +0.25% | < −0.25% (0 = quiet) |
| SECT | XLK % from open − mean(XLP, XLU) % from open (11-10 rotation) | > +0.30% risk-on | < −0.30% risk-off |
| DOW | weekday (5 states) | | |
| FOMC | FOMC statement day, from 13:00 (dates hand-entered from the Fed calendar; **no CPI calendar in the data → skipped**) | event | |
| SELF | the setup's own realised R today (closed base trades, exit ≤ T) ≤ −1R | | latched |
| FSTOP | ≥ 3 stopped trades (r ≤ −0.95, closed ≤ T) today in the setup's family (side × family) | | braked |
c30, gate1 and the checkpoint have no two-year history outside GATE1 (already failed its 2y test); they are not re-derived.

## 5. Matching rules
- **U (universal, fixed direction):** directional signals → shorts switched when state = +1, longs when state = −1
  ("don't fight the tape"; the owner's example "shorts off when compass UP-confirmed"). RVOL → all setups switched on
  low-vol (QDAY). SELF / FSTOP / FOMC → all setups switched when triggered. PDT, DOW: no universal rule.
- **F (family, fit on TRAIN):** per family and signal, the single worst state is switched if, in TRAIN, its avg R is
  < 0, ≥ 0.05R below the family's avg R, the difference has day-clustered t ≤ −1.0, and it has ≥ 30 days. At most one
  state per family per signal (so a losing family is not just switched off).
- **P (per-setup fingerprint, TRAIN only, shrinkage):** per setup and state, m = (n·mean + k·family-state mean)/(n + k),
  k = 100 trades. Switch the single worst state if m < 0 and m ≤ setup avg − 0.05R. The fingerprint label = that state.
- Actions: **OFF** and **HALF** for every signal × matching pair.
- **Configs:** 9 directional × 3 × 2 = 54; RVOL 3 × 2 = 6; PDT and DOW 2 × 2 each = 8; SELF, FSTOP, FOMC 1 × 2 each = 6 →
  **74 main configs**. Finalist sensitivities (thresholds ×0.8 / ×1.2, sticky mode, single 10:00 or 12:00 decision) are
  capped at **26 more → N = 100, bar t ≥ max(1.5, √(2 ln 100)) = 3.03**.

## 6. Metrics per config (VALID, FWD, live separately; TRAIN shown)
ΔR vs always-on (raw R and setup-weighted R: each setup's ΔR / its TRAIN base trades per day, so the 100-trade/day
CWT lists do not drown the rest); red-day losses cut % / green-day R given up % (setup-days by base sign); per-setup
better / worse counts and worst setup ΔR; family better / worse; worst day; ΔR without the best ΔR day; avg R of kept vs
switched trades; paired day-clustered t of setup-weighted daily ΔR; **random-switch baseline** (each setup's day
schedules permuted across its days within the split, 200 draws: same fraction, same timing).
**REGX stability:** for P (and per signal), each setup's best and worst state in TRAIN vs VALID (and live): share of
setups whose label is the same, vs the chance rate; rank correlation of state means across splits.

## 7. Pass bar (all required)
1. VALID ΔR > 0 and FWD ΔR > 0 (raw and setup-weighted).
2. VALID paired t ≥ 3.03.
3. VALID: ≥ 60% of affected setups improve; no setup worse by more than max(5R, 10% of |its base R|).
4. ΔR > 95th percentile of the random-switch baseline in VALID and FWD.
5. VALID ΔR without the best day > 0.
6. Threshold ×0.8 and ×1.2: VALID ΔR > 0 at both.
7. Live check ΔR ≥ 0 (all accounts pooled).
**Near-miss** = fails only 2 (t) or only 7. A pass or near-miss goes to a forward shadow (≥ 20 sessions) before any
DECISION; nothing is switched live from this study.
