Educational only — not financial advice.

# GAPDEF-1124: family-wide gap-definition remedy for the gap-down short family — FAIL (configs 3)

Pre-registered by the consultant (owner inbox 2026-11-24, "One action"); merges backlog nightly-1124-gapdn-min-real-gap
and nightly-1124-thin-open-print-guard. Research only, after the close; no config or live change. Locked block
2024-11-01..2025-02-28 not read.

**Rule (pre-declared, 3 configs in total, same on live and lab).** gapV = 09:30 1-min bar VWAP (lab: typical price,
cache has no VWAP) vs the prior regular-session close. A: keep if gapV ≤ min(own threshold, −1.0%). B: keep if
gapV ≤ min(own threshold, −0.5 × daily ATR%). C (comparison arm): no entries before 12:00 ET.
**Pass bar (set before the results):** live ΔR > 0 without the best day and best-day share < 50%; most setups better and
the largest worsening ≤ 3R; lab removed trades worse than kept trades in both halves (fit and check).

**Family (rule has a "gapped down" layer, short):** RW1-gapdn-bounce-flowsell-short-FD, RW3-gapdn-rsi5pop-flowsell-short-FD,
RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, RW7-gapdn-bounce-early-short-FD, RW3S-gapdn-flowsell-short-FD (own rule gap < 0;
RW7-WB3 < −0.5), NM-MF3-qqqdn-gapdn-FD (≤ 0), L3-gap-slope-fromopen / lowdist / rsi5hi-FD (≤ −2.66; fromopen-WB4 ≤ −3.2),
with their WB / RQa copies. Not in scope: CWT09 (already ≤ −5 / −10%), RW6 (no gap layer), 1–3-trade NM setups.

## (i) Live: 10 journals, 10-23..11-24 (gapdef_live.py → live_out.txt, live_results.csv, live_gaps.csv.gz)
2,927 family trades (no identical cross-account duplicates found), R = pnl_adj / $ risk (live LR8 costs); 2,920 gaps
re-measured from Alpaca SIP. First print vs first-minute VWAP differ in sign on 64 trades (44 symbol-days; PTLO 11-24:
print −3.41%, VWAP −0.11%).

| Config | Removed | Removed avg R | ΔR | ΔR w/o best day | Best day | Day t | Sessions + | Setups better / worse | Largest worsening | Blocked also removed |
|---|---|---|---|---|---|---|---|---|---|---|
| A ≤ −1% | 1,225 | −0.034 | **+42.11** | **−20.17** | 11-24, 148% `1 day` | 0.45 | 12/23 | 12 (+65.19) / 8 (−23.09) | RW7 −8.39 | 1,768 / 8,493 |
| B ≤ −0.5 ATR | 2,215 | +0.001 | −2.21 | −128.83 | — | −0.01 | 10/23 | 10 (+106.13) / 10 (−108.34) | L3-fromopen −60.19 | 5,273 / 8,493 |
| C before-noon cutoff | 1,612 | −0.030 | +48.02 | −98.52 | 11-24, 305% `1 day` | 0.25 | 11/23 | 14 (+168.84) / 6 (−120.83) | — | 4,332 / 8,493 |

**Per setup, config A** (avg R w/o best day and best-day share are for the kept trades):

| Setup (accounts) | Trades | Removed | Removed avg R | ΔR | Avg R before → after | Kept avg R w/o best day | Kept best-day share (— = kept total ≤ 0) |
|---|---|---|---|---|---|---|---|
| RW3-gapdn…-FD (Primary) | 156 | 85 | −0.136 | **+11.54** (11-10 66%) | +0.018 → +0.202 | −0.038 | 116% `1 day` |
| RW1-gapdn…-FD (On Deck, A) | 231 | 126 | −0.043 | +5.39 (11-17 112%) | −0.010 → +0.029 | −0.037 | 214% `1 day` |
| RW1-…-FD-WB3 (D) | 67 | 38 | −0.196 | +7.43 | −0.110 → +0.002 | −0.138 | n/a (total ≈ 0) |
| RW3S-gapdn…-FD (A, E, GY) | 605 | 287 | −0.091 | +26.24 (11-24 91%) | −0.184 → −0.267 | −0.306 | — |
| RW7-…-FD-WB3 (E) | 151 | 64 | −0.077 | +4.93 (11-24 99%) | −0.090 → −0.099 | −0.233 | — |
| NM-MF3-qqqdn-gapdn-FD (A) | 63 | 26 | −0.124 | +3.23 | −0.083 → −0.054 | −0.156 | — |
| L3-fromopen-FD-WB4 (A) | 31 | 10 | −0.228 | +2.28 | −0.178 → −0.155 | −0.338 | — |
| RW5-…-FD-RQa-1230 (B) | 8 | 4 | −0.483 | +1.93 | −0.329 → −0.175 | — | — |
| L3-rsi5hi-FD (On Deck, P, A) | 180 | 12 | −0.120 | +1.43 | +0.106 → +0.122 | +0.058 | 63% `1 day` |
| RW3-…-FD-WB4 (C) | 37 | 18 | −0.023 | +0.42 | +0.013 → +0.047 | −0.077 | 230% `1 day` |
| RW3-…-FD-RQa-1230 (A) | 13 | 6 | −0.041 | +0.25 | −0.258 → −0.444 | −0.526 | — |
| RW5-heat30…-FD (Primary) | 156 | 91 | −0.001 | +0.12 | −0.046 → −0.109 | −0.170 | — |
| L3-rsi5hi-FD-WB5 (C) | 32 | 1 | +0.389 | −0.39 | +0.107 → +0.098 | −0.201 | 133% |
| L3-rsi5hi-FD-WB4 (B) | 29 | 1 | +0.662 | −0.66 | +0.233 → +0.218 | −0.153 | 108% |
| L3-fromopen-FD-RQa-1230 (F) | 10 | 1 | +0.785 | −0.79 | −0.875 → −1.059 | −1.025 | — |
| L3-lowdist-FD-WB4 (F) | 4 | 1 | +0.834 | −0.83 | −0.455 → −0.885 | −1.175 | — |
| L3-fromopen-FD (On Deck, P) | 267 | 42 | +0.073 | −3.08 | +0.234 → +0.264 | +0.181 | 46% |
| RW5-…-FD-WB4 (D) | 26 | 9 | +0.349 | −3.14 | +0.179 → +0.088 | −0.139 | 211% `1 day` |
| L3-lowdist-FD (On Deck) | 80 | 9 | +0.646 | −5.81 | +0.245 → +0.194 | −0.018 | 106% |
| RW7-gapdn…-FD (On Deck, F) | 781 | 394 | +0.021 | **−8.39** | +0.050 → +0.079 | +0.023 | 74% |

Primary under A: 216 trades removed, −11.61R (ΔR +11.61), of which 11-24 11 trades −8.07R. Removed R by date is
mixed: 11-10 −31.2, 11-11 −24.3, 11-24 −62.3 vs 11-12 +28.5, 11-19 +20.7, 11-20 +33.7 (removed trades that won).

## (ii) Lab: 2 years, bench10 conventions (gapdef_lab.py → lab_out.txt, lab_results.csv)
82,809 booked trades on 446 sessions (8 setups, home-account book; ETB filter off because bench10's etb_rate.parquet is
not in the repo). The whole family is negative in the lab (avg −0.046R), so ΔR totals are large for any filter that
removes trades (A +2,132R, B +2,525R, C +2,254R; 8 of 8 setups "better" in each) and say nothing by themselves.
The test is removed vs kept:

| Config | Fit half: removed / kept avg R | Check half: removed / kept avg R | Per-setup kept avg improves |
|---|---|---|---|
| A | −0.092 / −0.090 (t −0.17, no edge) | −0.034 / −0.016 (t −2.33, trade-level) | 6 of 8 (RW5 worse, L3-lowdist flat) |
| B | −0.085 / −0.107 (wrong sign) | −0.022 / −0.032 (wrong sign) | 2 of 8 |
| C | −0.097 / kept −0.042 overall | −0.027 | — |

The thin-print part alone: the 8,027 lab trades whose own rule fails on the VWAP gap average −0.070R vs −0.043R for
the rest. Live, the same re-measure cut L3 winners (ORCL / COIN / ALAB lots, L3-fromopen −3.08R, L3-lowdist −5.81R).

## Verdict: FAIL — no DECISION
- A's live gain is one session (11-24 = 148%; −20.17R without it; day t 0.45), 8 of 20 setups get worse (RW7 −8.39R,
  L3-lowdist −5.81R), and the lab shows no selection edge in the fit half. B fails both ways. C (cutoff) is `1 day`
  at 305% and is not supported, matching the consultant's read.
- **What can be salvaged (next step, not run tonight):** the thin-print guard alone (gap from the first-minute VWAP,
  own thresholds unchanged), 1 config, scored per setup — lab sign is right (−0.070 vs −0.043), but the L3 family must
  be checked first because its −2.66% threshold was fitted on the print gap.
- Backlog: nightly-1124-gapdn-min-real-gap parked (configs_tried 3), nightly-1124-thin-open-print-guard parked with the
  thin-print-alone test open.
