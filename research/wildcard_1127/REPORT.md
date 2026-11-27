Educational only — not financial advice

# WILDCARD-1127: "Market intraday momentum" (first half hour predicts last half hour) on index and sector ETFs

**Verdict: FAIL — 0 of 24 configs pass; the signal is not there even before costs.** Research only; nothing in config/,
setups, exits, assignments, decisions.json or the ledger changed.

## Plain-language summary
The 2018 Gao-Han-Li-Zhou paper found that the S&P 500's move from yesterday's close to 10:00 predicts its move over the
last half hour of the day. We tested the plain rule (trade 15:25 -> 15:55 in the direction of the early move) on SPY, QQQ,
IWM, DIA and 12 sector ETFs over 2016-2026 (40,400 ETF-days, 16 ETFs, 1-minute SIP bars). Before any costs the rule
earns about **0 bp per trade** (IDX4: T2 +0.6 bp, CHECK −0.2 bp, EARLY 2016-22 +0.06 bp). A live-style
round trip costs ~8-9 bp (LIVE-L, ≈ 0.16R on a 53 bp stop) and even a penny-spread model costs ~2 bp. So every config
loses on every split after costs. The published effect looks like it has faded since the paper's sample (1993-2013); it
shows up only in 2020 (+3 bp, t ≈ 1) and weakly on very large early moves (|R1| ≥ 2σ: +1 to +3 bp, t < 1.3).

## Pre-registration and count
PREREG.md (commit 9bebe1c15b) + Addendum A (NYSE half-day list, commit 6bc0f326ac; the registered volume detector found
1 of 22 half days), both before any config was scored. **Configs: 24** (group IDX4/SEC12 x predictor P1/P2 x threshold
k 0/0.5/1.0 σ x stop 1/2 x A20). Cumulative N ≈ 8,952 + 24 = **≈ 8,976**. Engine label: **E4 WILD-sim** (one-off;
Backtester fill semantics: market at bar open, stop-first, gap fills at the open). Locked block 2024-11-01..2025-02-28
never read (dropped at load, asserted in wc_sim and wc_score; 2025-03-03 skipped because its prior close is locked).
New data: 14 ETFs' 2016-01..2022-09 1-min SIP bars fetched GET-only (scratch, not in git).

## Results (LIVE-L primary; mean R per trade, day-clustered t)
| Config | EARLY | T2 | FIT | CHECK | OOS t | gross OOS R (t) | ETF-TIGHT OOS |
|---|---|---|---|---|---|---|---|
| **H1 IDX4 P1 k0 s2 (paper form)** | −0.166 | −0.145 | −0.132 | −0.183 | −14.9 | +0.003 (0.30) | −0.036 |
| **H2 finalist IDX4 P2 k1 s2** (best DEV t) | −0.126 | −0.147 | −0.093 | −0.154 | −6.0 | +0.013 (0.54) | −0.026 |
| Best gross OOS: IDX4 P2 k1 s1 | −0.225 | −0.209 | −0.151 | −0.269 | −5.3 | +0.037 (0.82) | −0.043 |
| SEC12 P1 k0 s1 (best SEC12 gross) | −0.238 | −0.215 | −0.216 | −0.236 | −18.4 | +0.016 (1.35) | −0.056 |
All 24 rows: grid.csv (every config negative on every split under LIVE-L and LR8; gross OOS t ranges −0.57..+1.35).

**H1 bars (all fail):** LIVE-L T2 −0.145 / CHECK −0.183 (LR8 −0.048 / −0.070); OOS t −14.9 (bar ≥ 2.0); one-big-day
n/a as totals are negative (T2 −251R, CHECK −200R; avg w/o best day −0.148 / −0.188); random-direction control: actual
−0.160 vs control mean −0.162, p95 −0.151 → 64th percentile (bar 95th); always-long −0.174, always-short −0.150 (same
cost, so direction adds nothing); per-ETF 0/4 positive (SPY −0.161, QQQ −0.161, IWM −0.134, DIA −0.184); SPY-up −0.174 /
SPY-down −0.143 days. Stop hit 2.4% of trades, LIVE-L cost 0.163R per trade (median stop 53.5 bp).
**H2 bars (all fail except "beats its k0 twin"):** T2 −0.147 / CHECK −0.154, OOS t −6.0 (bar 2.87), control 80th pct,
per-ETF 0/4, up −0.172 / down −0.121.
Highest random-direction-control percentiles across the grid were SEC12 P1 k0.5 s1 (96.6%) and SEC12 P1 k0 s1 (96.2%) —
both at −0.24R LIVE-L per trade; with 24 configs ~1 such hit is expected by chance.

## Per-family effect (remedy-style report, gross bp per trade, signed by the rule; gross_bps.txt)
IDX4: EARLY +0.06 · T2 +0.62 · FIT +0.08 · CHECK −0.20. SEC12: EARLY −0.03 · T2 +0.62 · FIT +0.07 · CHECK −0.11.
By year (IDX4): 2016 −0.95, 2017 −0.07, 2018 0.00, 2019 −0.10, **2020 +3.16 (t 1.06)**, 2021 −1.78, 2022 +0.09, 2023 +0.54,
2024 +0.95, 2025 −0.66, 2026 +0.14. 0/16 ETFs positive after LIVE-L on OOS under H1/H2-type configs.

## What can be salvaged (optimistic read, no claim)
* The only pockets with a gross sign are crisis-volatility days (2020) and huge early moves (|R1| ≥ 2σ20: IDX4 T2 +3.1 bp
  t 1.29, CHECK +1.1 bp t 0.26, EARLY +1.2 bp; SEC12 CHECK +1.7 bp). Even there gross ≈ 1-3 bp is below a penny-spread
  round trip, so no standalone trade exists. A possible use is as a free tiebreak only: on |R1| ≥ 2σ days, do not fight
  the early index direction with late-day (15:25+) entries that are already being taken. That would need its own
  PREREG on existing live late entries (no extra round trip) — noted, not proposed (no evidence above t 1.3).
* Instrument angle not tested here: a 3x ETF (TQQQ/SPXL) triples the move per bp of spread, but the gross is ≈ 0, so
  leverage cannot help.

## Caveats and rule-change context
* Historical bars only (E4 one-off simulator); no live journal rows, so the live ledger changes (e.g. LR8 2026-11-12,
  Epoch 1 2026-11-19, rules effective 2026-11-27) do not enter these figures.
* Raw prices: dividend ex-dates lower the gap part of R1 a few days a year per ETF (accepted in PREREG).
* Exit is 15:55 (live flatten), not the 16:00 close the paper uses; the final 5 minutes (closing-auction pressure) are
  not captured. That is a real difference from the paper and a candidate for its own test only if MOC orders were ever
  allowed (they are not in the current engine).
* LIVE-L's fixed b term was fit on stocks; ETF-TIGHT is shown so the result does not hinge on it — it fails there too.

## Backlog proposal
None (FAIL). Suggested backlog note for `intraday-momentum-paper`: status → tested/failed (WILDCARD-1127: 24 configs,
2016-2026, gross ≈ 0 bp, LIVE-L −0.15 to −0.30R per trade on every split).

Files: PREREG.md, wc_sim.py (rows), wc_score.py (grid, bars, controls), grid.csv, results.json, gross_bps.txt.
