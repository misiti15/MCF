# Ultimate-setup BENCHMARK (ultimate_1119)

*Educational only — not financial advice. Research only: no setup, exit, config or account change. Nothing committed.*

The bar new "ultimate setup" candidates (research/ultimate_1119/) must beat: MCF's current best setups scored on the
SAME 2-year pipeline and halves the candidates use. Setups (8): the 5 named (L3-fromopen/lowdist/rsi5hi-FD, RW3-FD,
RW5-FD) + the other Primary members (NM-ETF-late-dip-di-long, ST7-rsi50dn-long-pm-t1s1-FD; docs/live/assignments.json
2026-11-19) + the live top 5 by total R after costs (L3-fromopen 80.9, GEN-261020-09 59.8, RW3 27.7, L3-lowdist 25.2,
RW5 22.7 — so the only addition is GEN-261020-09-…-holdtr-long). Configurations tried: 1 (fixed live rules, no fitting).

## Method (bench.py, stats.py, live.py in this folder; trade list kept in the scratchpad, 4 MB, regenerable)
- **Signals:** lab frames (research/history2y/data/frames, 5-min decision bars 09:50-15:00 ET, 1,226 lab symbols —
  survivorship bias) with each setup's **live** module + config (window, min_adv on point-in-time ADV20, gap prefilter,
  refire chain via `mcf.strategies.setups.refire_select`). Signal counts reproduce research/history2y/data/bt_lab1104
  exactly for the 6 setups it covers (checked on 2024-10). Entry = decision-bar close, R = 0.25 × daily ATR.
- **Exits:** walked on **1-minute bars** (data/cache_hist/1Min) from the decision close: stop first, then target,
  stop gap-through at the worse of open/stop, holdtr = 1R trail once +1R, flat 15:55. 74,951 trades, 2 without a path.
  The house 5-minute walk (as bt_all.py) is kept as a cross-check column: within ±0.006R of the 1-minute figure everywhere.
- **Costs (LR8 research basis, mcf.research.gates):** entry 1c + 1 bp × time-of-day multiplier; exit 1c + 1 bp except
  target (limit) fills; +2c on stops; ×3 on the extended tier (|gap| ≥ 20% or price < $5).
- **Halves:** FIT = 2024-10-01..10-31 + 2025-03-01..09-30 (170 sessions); CHECK = 2025-10-01..2026-11-04 (276 sessions,
  the cache's last day). **Locked block 2024-11-01..2025-02-28 never read** (pyarrow filters exclude it; asserts on every
  frame, trade list and 1-minute load; MCF_HIST_ALLOW_LOCKED never set).
- **SPY day type:** SPY 09:30 open → 15:59 close, up ≥ +0.30%, down ≤ −0.30% (fit 61/60/49, check 86/116/74 up/flat/down).
- "/session" and "R/session" divide by ALL sessions in the half. "Worst day / trade-session" = worst day's R ÷ trades per
  traded session (worst day per typical day's trade count). Best-day share is n/a when total R ≤ 0.
- Setup rules only: account caps, slots, the Testing cost filter (max_stop_cost_r 0.15), -2R latches and the full live
  universe (~4,200 names) are NOT modelled — the same holds for the candidates.

### CHECK half (276 sessions)

| Setup | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | worst day / trade-session | SPY up / flat / down avg R | median hold (min) | 5-min-walk avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GEN-261020-09 (holdtr) | 2407 | 8.72 | 0.478 | -0.055 | -0.075 | n/a (total<0) | -131.7 | -0.477 | -80.9 | -3.830 | +0.717 / +0.226 / -0.222 | 152 | -0.052 |
| L3-fromopen | 27029 | 97.93 | 0.519 | -0.027 | -0.054 | n/a (total<0) | -724.5 | -2.625 | -600.3 | -5.708 | -0.147 / +0.108 / +0.074 | 86 | -0.025 |
| L3-lowdist | 2541 | 9.21 | 0.482 | -0.106 | -0.117 | n/a (total<0) | -270.1 | -0.979 | -72.8 | -6.960 | -0.228 / +0.049 / +0.013 | 76 | -0.104 |
| L3-rsi5hi | 6653 | 24.11 | 0.653 | -0.026 | -0.035 | n/a (total<0) | -171.7 | -0.622 | -119.8 | -4.754 | -0.114 / +0.044 / +0.061 | 38 | -0.027 |
| NM-ETF-late-dip | 262 | 0.95 | 0.630 | +0.052 | +0.039 | 0.277 | +13.6 | +0.049 | -5.0 | -2.130 | +0.100 / +0.144 / -0.047 | 48 | +0.053 |
| RW3-FD | 4115 | 14.91 | 0.503 | -0.037 | -0.045 | n/a (total<0) | -153.2 | -0.555 | -43.1 | -2.892 | -0.254 / -0.013 / +0.111 | 100 | -0.035 |
| RW5-FD | 3827 | 13.87 | 0.507 | -0.038 | -0.045 | n/a (total<0) | -144.8 | -0.524 | -30.3 | -2.162 | -0.239 / -0.004 / +0.115 | 103 | -0.036 |
| ST7-FD | 864 | 3.13 | 0.562 | +0.084 | +0.073 | 0.134 | +72.2 | +0.262 | -7.2 | -1.956 | +0.123 / +0.068 / +0.072 | 87 | +0.084 |

### FIT half (170 sessions)

| Setup | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | worst day / trade-session | SPY up / flat / down avg R | median hold (min) | 5-min-walk avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GEN-261020-09 (holdtr) | 1082 | 6.36 | 0.510 | +0.124 | -0.023 | 1.171 | +134.3 | +0.790 | -55.6 | -3.343 | +0.482 / -0.077 / +0.136 | 111 | +0.130 |
| L3-fromopen | 15814 | 93.02 | 0.555 | -0.032 | -0.161 | n/a (total<0) | -499.2 | -2.936 | -554.7 | -5.507 | -0.037 / +0.046 / -0.052 | 39 | -0.030 |
| L3-lowdist | 1820 | 10.71 | 0.472 | -0.169 | -0.235 | n/a (total<0) | -308.2 | -1.813 | -221.9 | -17.073 | -0.475 / +0.012 / +0.124 | 42 | -0.165 |
| L3-rsi5hi | 3809 | 22.41 | 0.682 | -0.067 | -0.138 | n/a (total<0) | -254.3 | -1.496 | -235.3 | -9.700 | -0.062 / -0.060 / -0.075 | 16 | -0.067 |
| NM-ETF-late-dip | 233 | 1.37 | 0.833 | +0.269 | +0.217 | 0.374 | +62.8 | +0.369 | -2.8 | -0.604 | +0.260 / +0.179 / +0.291 | 11 | +0.269 |
| RW3-FD | 2191 | 12.89 | 0.458 | -0.111 | -0.123 | n/a (total<0) | -244.0 | -1.435 | -34.5 | -2.628 | -0.273 / -0.051 / +0.005 | 96 | -0.108 |
| RW5-FD | 2052 | 12.07 | 0.476 | -0.078 | -0.088 | n/a (total<0) | -161.0 | -0.947 | -33.8 | -2.736 | -0.340 / +0.041 / +0.132 | 105 | -0.076 |
| ST7-FD | 250 | 1.47 | 0.468 | -0.132 | -0.180 | n/a (total<0) | -33.1 | -0.195 | -26.4 | -11.094 | +0.496 / -0.036 / -0.448 | 60 | -0.130 |

### LIVE record (journal.db, R after costs on the one LR8 basis, 2026-10-06..11-18, all accounts pooled)

| Setup | trades | traded sessions | accounts | win | avg R | avg R w/o best day | best-day share | total R | worst day |
|---|---|---|---|---|---|---|---|---|---|
| GEN-261020-09 (holdtr) | 189 | 7 | gen 189 | 0.683 | +0.316 | -0.113 | 1.214 **1 day** | +59.8 | -7.0 |
| L3-fromopen | 397 | 24 | primary 175, testing 222 | 0.652 | +0.204 | +0.156 | 0.39 | +80.9 | -13.7 |
| L3-lowdist | 109 | 19 | testing 109 | 0.642 | +0.231 | +0.091 | 0.723 **1 day** | +25.2 | -2.5 |
| L3-rsi5hi | 158 | 23 | primary 22, testing 91, testing2 45 | 0.728 | +0.089 | +0.007 | 0.937 **1 day** | +14.1 | -3.6 |
| NM-ETF-late-dip | 30 | 14 | livelab 8, primary 12, testing2 10 | 0.800 | +0.248 | +0.235 | 0.177 | +7.4 | -0.6 |
| RW3-FD | 199 | 27 | primary 161, testing 38 | 0.613 | +0.139 | +0.025 | 0.846 **1 day** | +27.8 | -10.2 |
| RW5-FD | 206 | 27 | primary 173, testing 33 | 0.583 | +0.110 | +0.022 | 0.825 **1 day** | +22.7 | -15.5 |
| ST7-FD | 50 | 18 | primary 34, testing 16 | 0.540 | +0.081 | +0.002 | 0.979 **1 day** | +4.0 | -2.8 |
## Reading it (honest, costs in)
- **On the 2-year pipeline only two setups are positive on the CHECK half: ST7-FD (+0.084R, w/o best day +0.073R,
  3.1/session, +0.26R/session) and NM-ETF-late-dip (+0.052R, 0.95/session).** The L3 family and RW3/RW5 are negative in
  both halves; RW3/RW5 are positive only on SPY-down days (+0.11R), the classic short-side regime dependence.
- **Live vs pipeline disagree sharply for the live winners.** L3-fromopen: live +0.204R (397 trades) vs pipeline −0.027R
  check / −0.23R in the 10-12..11-04 overlap (1,970 pipeline trades vs ~17/session live). The pipeline fires L3-fromopen
  ~98×/session (refire cooldown 1, no caps, refire even while a position is open; one-position-per-symbol variant still
  −0.066R check, −0.14R overlap). RW3/RW5 in the same overlap window match live's sign (+0.15/+0.19R). So this benchmark
  is a *pipeline* bar — candidates scored the same way face the same biases — not a verdict on the live record.
- Live records carrying the **1 day** tag (best-day share ≥ 50%): L3-lowdist, L3-rsi5hi, RW3, RW5, ST7, GEN-261020-09
  (GEN: >100% — all its live R is one day; w/o it −0.113R).

## Recorded-quote replay (research/reps2, --replay) — existing 2026-11-18 run reused
The nightly replay with recorded live quotes covers Primary / On Deck / Testing A, only 2026-11-18 so far (the first
session with recorded quotes; pooled match 100%, extra 1.1%, bias +0.018R). A fresh run was not needed (same day, ~1 h,
frozen params). Per setup, recorded-quote replay vs live (avg R, trades): L3-fromopen −0.155 vs −0.130 (19); RW3 −0.300 vs
−0.288 (14); RW5 −0.105 vs −0.039 (8); NM-ETF +0.006 vs +0.026 (3); ST7 −0.554 vs −0.562 (1); L3-lowdist +1.053 vs +0.951
(1); L3-rsi5hi +0.205 vs +0.199 (6). GEN-261020-09 (gen account) is not in that replay. One session is far too small to
rank anything; candidates can be put through the same replay (research/reps2/nightly.py --replay --day 2026-11-18) for a
like-for-like look, as a fidelity check only.

## Rule-change context (owner 2026-11-02) — live window 2026-10-06..11-18 (research/ledger.jsonl)
Primary position size ~$5k then ~$4k (10-28); Primary per-setup −2R daily latch (10-29), counted in cost R from 11-12
(LR3); per-setup daily loss stop latches (10-23); Testing 1/2 cost filter max_stop_cost_r 0.15 (10-30); LR8 live cost
model (11-12; every live figure here is on the one LR8 basis, DQ-P3); Testing A-F half-size lots (11-17, R comparable);
SPYEXIT engine + Workbench tweaked copies (-WB*) from 11-17 (separate setups, not pooled here); refire option B for
L3-fromopen (10-14). Moves inside the window: L3-fromopen promoted 10-20, demoted 10-22, re-promoted 10-30; ST7-FD
promoted 10-26; L3-rsi5hi promoted 10-30, back to Testing 11-11; live records pool every account a setup ran in. The
2-year pipeline uses one fixed (today's) rule set, so no rule change falls inside its halves.

## Pre-registered "beats our best" bar (fixed 2026-11-19, before any candidate is scored)
A candidate beats the benchmark only if, on the **CHECK half** (2025-10-01..2026-11-04), scored with this pipeline
(lab frames or 1-minute bars, 1-minute exit walk, LR8-basis costs as above, locked block never read):
1. **avg R after costs > +0.0836** (best benchmark: ST7-rsi50dn-long-pm-t1s1-FD), AND
2. **avg R w/o best day > +0.0734** (best benchmark: ST7-FD; highest of all 8), AND
3. **total R per session ≥ −0.540** (median of the 8 benchmark setups: mean of RW3 −0.555 and RW5 −0.524). Because that
   median is negative it does not by itself stop a rare-firing winner; the effective volume floor comes from
   requiring **total R per session > 0** as well — stated here as part of the bar, AND
4. **worst day / trade-session ≥ −2.152** (ST7-FD −1.956, no more than 10% worse).
Report every candidate tried and the number of configurations (RESEARCH_RULES); a pass is a screening result for the
backlog, not a promotion.
