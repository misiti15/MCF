Educational only — not financial advice

# COMPASS-RD-1126 Part 2: which setups depend on market conditions (2026-11-26, research only, nothing changed)
**Data.** Live: run-1 closed trades, all 10 journals, LR8 R, identical signals once (`footrace.live_trades` rule + entry
time/side), 10-06..11-25 = 36 sessions, 152 setups with >= 30 trades. State at entry is point in time (1-min SPY/QQQ/IWM
bars closed before the entry minute; W60 compass mark T used from T+2 min; recorded `mcf-data-compass` rows, missing days
recomputed with `compass_live.compute`). "Aligned" = condition on the side of the trade's market exposure (inverse ETFs
flipped, `compass_gate` classes). Cell means shrunk toward the setup mean (k = 20). Bench: bench10 engine unchanged,
8 setups, home-account book, research LR8 costs; FIT 2024-10 + 2025-03..09, CHECK 2025-10..2026-11-04 (overlaps live
10-06..11-04), T2 2023-01..2024-09; locked block never read. Day type = hindsight close side (up/down >= 0.25%,
V = close one side after >= 0.5% the other): descriptive, not tradable.
**Configs counted: N = 4,762** (live 4,104 cells = 152 setups x 27; bench 600 cells; 40 OFF what-ifs; 18 pooled
time-bucket contrasts). At this N no single cell clears a family-wise bar (t ~ 4.3); everything below is a lead.
**Rule changes inside the live window (ledger):** 10-23 latch semantics / stop off in T1/T2/Gen, 10-28 Primary size,
10-29 Primary -2R latch, 10-30 T1/T2 cost filter, 11-12 LR3/LR8 cost basis + caps, 11-17 Workbench copies + testing
half-size lots, 11-19 Epoch 1 (NS5 out of Primary), 11-23 ST7 out of Primary, BRAKE-BURST, Remedy-Q 12:30 copies. R is
per trade, so the moves do not bias a cell, but the trade set differs before / after.

## 1. The one condition that always flips edges: the day's close side (hindsight)
Every bench setup flips sign by day type in every split (avg R, with-day / against-day, n):
| setup | FIT | CHECK | T2 | live (shrunk, t) |
|---|---|---|---|---|
| RW3-gapdn-rsi5pop-flowsell-short-FD | +0.03 / -0.35 (537/608) | +0.13 / -0.29 | +0.15 / -0.38 | +0.39 / -0.24, t 3.0 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | +0.11 / -0.40 | +0.11 / -0.30 | +0.11 / -0.39 | +0.32 / -0.31, t 4.0 |
| L3-gap-slope-fromopen-FD | +0.05 / -0.25 (481/634) | +0.03 / -0.17 | +0.07 / -0.23 | +0.19 / +0.02, t 0.7 |
| RW7-gapdn-bounce-early-short-FD | +0.10 / -0.36 | +0.16 / -0.22 | +0.16 / -0.38 | +0.16 / -0.35, t 3.2 |
| MF3-open-flowsell-rsi5hi-FD | +0.01 / -0.41 | +0.06 / -0.25 | +0.07 / -0.42 | +0.06 / -0.45, t 3.6 |
Contrast t 2.1-11.1 in 23 of 24 bench setup-splits (NM-ETF FIT the exception). Mechanism: all are directional bets with
market beta; the sign is set by where SPY goes *after* entry. Live: 54 of 55 setups (>= 15 days) are better on with-days.
**But the point-in-time state at entry captures little of it.** SPY-from-open aligned at entry, pooled 8 setups, with
minus against: FIT +0.12 (<11:00, t 2.4) / +0.06 / +0.02 (>=13:00); CHECK +0.01 / +0.02 / +0.04; T2 +0.04 / +0.04 /
+0.08 — a tenth to a fifth of the day-type gap, and it does not grow late in the day. This is COMPASS-LEARN's finding in R terms:
the compass reads where the day *stands* (side-of-close 12/14 forward), not where it goes after a new entry.

## 2. Most condition-dependent setups (point-in-time conditions; live vs bench)
| setup | condition | live with / against (n) | bench switched vs kept avg R, excess t (FIT / CHECK / T2) | read |
|---|---|---|---|---|
| MF3-open-flowsell-rsi5hi-FD | SPY gap vs the short (gap up >= 0.25% = against) | -0.01 (84) / -0.41 (114), t 2.1; off = +51.6R, best day 40% | -0.21 vs -0.15, 2.50 / -0.16 vs -0.05, 3.18 / -0.20 vs -0.18, 1.96 | **only rule consistent in all 4 windows**; open-window shorts fight a gap-up tape. Kept trades still < 0 on bench |
| RW3-gapdn-rsi5pop-flowsell-short-FD | SPY from open at entry | +0.26 (127) / -0.04 (69), t 1.4 | with-minus-against +0.01 / +0.13 (t 2.2) / +0.04; off-against excess -0.04 / 1.60 / 0.55 | with-tape short; real but small, CHECK-heavy |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | SPY from open at entry | +0.25 (106) / -0.05 (83), t 1.4 | +0.09 / +0.14 (t 2.0) / -0.03; excess 0.60 / 0.79 / -0.31 | same, weaker; T2 flips |
| L3-gap-slope-fromopen-FD | SPY from open (counter-tape) | SPY down -0.14 (144) / SPY up +0.22 (260), t -1.4; >+0.5%: +0.41 (134) | off-when-SPY-down excess -0.58 / 1.74 / 0.12; IDX3 CHECK t -2.31, FIT/T2 ~0 | counter-tape only in CHECK + live (same period); FIT/T2 do not show it - a regime, not a stable label |
| NM-ETF-late-dip-di-long | W60 compass against the long | +0.12 (18) / -0.27 (24), t 2.2 (9 / 7 days) | checkpoint-against switched +0.31 vs +0.20 (wrong way) / -0.08 vs +0.11 / 0.00 vs -0.05 | live only; bench does not confirm (n 226-262 / split) |
Also tested, not confirmed on bench: CWT09-gapdn-bounce-g5-lowerhalf-short (live SPYO t 2.0, sign flips CHECK vs FIT/T2),
RW7 (live SPYO t -0.3), CWT14-failbrk-pdh-p10-short (IDX3 excess negative in CHECK/T2). Live counts across 152 setups:
|t| >= 2 for compass-aligned 1 / 50 (chance), SPYO 7 / 61, IDX3 6 / 44, gap 12 / 56; the IDX3-aligned diff is positive in
32 of 44 setups (mean +0.16R) — tape alignment helps on average, but per-setup labels are noisy (REGX: 31% vs chance 32%).

## 3. Top candidates for "switch on/off by condition" (all leads; none passes; nothing to change live)
1. **Gap-against brake for the open-window momentum short family (MF1-MF5):** MF3 above; live gap t 2.44 MF1-945-FD and
   2.24 MF5-FD. Family-targeted (owner remedy rule 11-05), not GAP-U's all-shorts switch that hurt NM-AR / NS1 / RW1.
   Next: pre-register 1 config on bench (MF1/2/4/5 lists), report per-setup better/worse.
2. **Primary trio as a tape pair, not a switch:** RW3/RW5 earn on down tape, L3-fromopen (recently) on up tape. Their
   flips offset inside one book, so a switch on one leg mostly moves R between days. The lever is size balance
   (NETBETA-B8, squeeze_1125: passed the bar, Friday decision) rather than on/off.
3. **Day-type forecast is the missing piece.** Day type moves R 0.3-0.5R/trade in every setup; nothing at entry predicts
   it (heading = coin flip, 0 / 205 COMPASS-LEARN, 0 / 12 breadth). Work that forecasts *the close side from 10:30-11:00*
   (compass precision 76-86%) and acts only on entries *after* the reading — e.g. gate1's setup-state gate (15 / 20
   forward sessions, +127R, day t 2.44, excess t 0.89 vs 1.0) — is the piece closest to completing the puzzle.
Scripts: `scripts/` (scratch paths hard-coded; journals copied to scratch and deleted after reading); live cells `cond_live.csv`, bench OFF table `bench_off.csv`.
