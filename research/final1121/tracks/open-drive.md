Educational only — not financial advice.

# Open-drive track: opening drive and failed opening push setups (overnight 2026-11-21)

**Bottom line:**
- None of the setups is profitable after costs.
- One setup meets the top-10 standard: **OD2-failpush-p0.6-orx-L**, a long on a failed down push. In plain terms it backtests no worse than the setups that are winning live. It is not an edge: CHECK avg R is −0.037 and day-t is about 0. It reached the finalists only through a rule change made after FIT (see §5).
- The BDI 11-20 pattern loses over 2 years at FIT. That pattern is a failed UP push followed by a short.
- Gap-down shorts look strong in FIT only because of the April 2025 crash days.

**Configurations:**
- 38 candidate configs (6 families plus 2 follow-up families, both sides) and 2 null configs that are not candidates.
- WB2 bar: max(1.5, sqrt(2 ln 38)) = 2.70. No finalist comes near it.
- CHECK was scored once, for 5 finalists.
- The locked block 2024-11-01..2025-02-28 was never read (pyarrow filter plus assert).
- No repo edits, no orders, no MarcoFlow calls.

## 1. Method (the normal way, matched to bench10.py)

**Data and universe**
- T1: 1-minute bars from data/cache_hist (1,226 symbols). ATR14, ADV20 and gap come from the lab frames' 09:50 row.
- T2: data/cache_fresh (469 symbols, 2023-01-03..2024-09-13), with daily features rebuilt the same way.
- Filters: ADV20 >= $10M, open >= $5. First hit per symbol-day.

**Signals and exits**
- The decision is taken at the 5-min bar close, 09:50..10:30 (9 bars). Entry is the close of the minute before the tod label.
- Exits are walked minute by minute:
  - stop first; a gap-through fills at the worse of open and stop;
  - the target fills only when traded through by $0.01;
  - flat at the 15:55 open.
- Geometry is t1s1 (stop 0.25 ATR, target 1R) for all configs. orx15 (stop 1c beyond the day extreme, target 1.5R, risk <= 1.5 ATR) is added for OD2 and OD6 only.
- The short side is the long rule run on the mirrored price series.

**Costs and book**
- Costs: LR8 (entry (1c + 1 bp) × time-of-day multiplier, which is 1.4 for 09:50-10:25), exit 1c + 1 bp except target fills, +2c on stops, ×3 extended tier, +1.2 bp borrow on shorts.
- Book: testing rules (cap 100, <= 3 lots per symbol, 0.15R cost filter, shorts only with ETB >= 0.9).

**Windows**
- FIT = 2024-10 plus 2025-03..09 (170 sessions).
- CHECK = 2025-10-01..2026-11-04 (276 sessions).
- T2 = 427 sessions.

**Nulls**
- Matched random null: the same symbol-day, side and risk, with 3 random 09:50-10:30 entries.
- Unconditioned null: the setup's 09:50-known filters, entered at 09:50.

**Pre-registration**
- The finalist rule was fixed in prereg.json before scoring: FIT n >= 30, avg R > 0, w/o best day >= −0.02, excess over the null > 0.
- If fewer than 2 configs pass, up to 2 "debatable" finalists may be added (best FIT avg R, avg R >= −0.0099).

## 2. Families (long form; the short side is the mirror)

| Family | Rule |
|---|---|
| OD1 orbdrive | Drive >= 0.3 ATR by 09:50, then the first close above the OR20 high (rvol >= 1 or >= 2) |
| OD2 failpush | Push >= p ATR in the first 20 minutes, then a reclaim of the open and VWAP with no new extreme (p 0.3 or 0.6; t1s1 or orx) |
| OD3 firstpb | Strong drive (>= d ATR, closing in the top quarter of the OR), then a >= 38.2% pullback that holds above VWAP, then a close above the prior bar's high |
| OD4 gapfail | Gap >= g% one way, then a close back through the open and VWAP |
| OD5 gapgo | Gap >= g%, holds beyond the open at 09:50, then breaks the OR20 extreme |
| OD6 failorb | A close through one OR20 extreme, then a close back past the OR midpoint |
| OD7 (round 2) | Gap >= g% with the 09:50 close beyond the open and VWAP; enter at 09:50 |
| OD8 (round 2) | 09:50 drive >= 0.5 ATR beyond VWAP; enter at 09:50 |

## 3. FIT results, all 38 configs (testing book; matched null shown)

| config | n | /ses | avg R | w/o best | w/o top-2 | day-t | matched null |
|---|---|---|---|---|---|---|---|
| OD5-gapgo-g4-S | 695 | 4.09 | +0.439 | +0.292 | +0.128 | 3.52 | +0.486 |
| OD5-gapgo-g2-S | 1638 | 9.64 | +0.163 | +0.088 | −0.018 | 1.27 | +0.264 |
| OD7-gapdrive950-g4-S | 715 | 4.21 | +0.125 | +0.028 | −0.084 | 0.78 | +0.143 |
| OD1-orbdrive-rv2-S | 1575 | 9.26 | +0.062 | +0.014 | −0.022 | 1.00 | +0.198 |
| OD2-failpush-p0.6-orx-L | 1800 | 10.59 | +0.051 | −0.009 | −0.032 | 0.75 | +0.107 |
| OD2-failpush-p0.6-L | 1637 | 9.63 | +0.042 | −0.073 | −0.083 | 0.42 | +0.127 |
| OD4-gapfail-g2-L | 4541 | 26.71 | +0.020 | −0.040 | −0.063 | 0.25 | +0.053 |
| OD4-gapfail-g4-L | 1442 | 8.48 | +0.017 | −0.117 | −0.142 | 0.12 | +0.040 |
| OD4-gapfail-g4-S | 1238 | 7.28 | +0.004 | −0.028 | −0.062 | 0.07 | +0.165 |
| OD2-failpush-p0.6-orx-S | 1290 | 7.59 | −0.004 | −0.028 | −0.047 | −0.11 | +0.099 |
| OD3-firstpb-d0.8-S | 199 | 1.17 | −0.005 | −0.036 | −0.068 | −0.05 | +0.268 |
| OD2-failpush-p0.3-orx-L | 12626 | 74.27 | −0.013 | −0.024 | −0.031 | −0.41 | +0.064 |
| OD3-firstpb-d0.8-L | 129 | 0.76 | −0.030 | −0.095 | −0.132 | −0.28 | +0.338 |
| OD1-orbdrive-rv1-S | 4509 | 26.52 | −0.036 | −0.066 | −0.089 | −0.74 | +0.131 |
| OD3-firstpb-d0.5-L | 786 | 4.62 | −0.041 | −0.073 | −0.099 | −0.68 | +0.195 |
| OD2-failpush-p0.6-S | 1062 | 6.25 | −0.054 | −0.086 | −0.107 | −1.11 | +0.107 |
| OD6-failorb-rv1-L | 1276 | 7.51 | −0.058 | −0.092 | −0.121 | −0.84 | +0.246 |
| OD5-gapgo-g2-L | 1476 | 8.68 | −0.065 | −0.089 | −0.111 | −0.84 | +0.148 |
| OD2-failpush-p0.3-orx-S | 10773 | 63.37 | −0.065 | −0.075 | −0.084 | −1.82 | +0.030 |
| OD6-failorb-rv1-S | 1246 | 7.33 | −0.067 | −0.130 | −0.155 | −0.84 | +0.253 |
| OD2-failpush-p0.3-L | 11499 | 67.64 | −0.068 | −0.096 | −0.104 | −1.78 | +0.082 |
| OD7-gapdrive950-g2-L | 2387 | 14.04 | −0.068 | −0.086 | −0.102 | −1.08 | −0.033 |
| OD7-gapdrive950-g2-S | 1988 | 11.69 | −0.069 | −0.119 | −0.172 | −0.57 | −0.046 |
| OD8-drive950-d0.5-L | 5160 | 30.35 | −0.072 | −0.083 | −0.091 | −1.86 | −0.089 |
| OD8-drive950-d0.5-S | 5314 | 31.26 | −0.082 | −0.096 | −0.110 | −1.73 | −0.087 |
| OD1-orbdrive-rv1-L | 4490 | 26.41 | −0.091 | −0.115 | −0.126 | −2.13 | +0.092 |
| OD6-failorb-rv2-L | 260 | 1.53 | −0.095 | −0.129 | −0.154 | −1.11 | +0.173 |
| OD6-failorb-rv1-orx-L | 1504 | 8.85 | −0.099 | −0.134 | −0.152 | −1.55 | +0.217 |
| OD1-orbdrive-rv2-L | 1331 | 7.83 | −0.100 | −0.138 | −0.149 | −1.98 | +0.108 |
| OD4-gapfail-g2-S | 3646 | 21.45 | −0.101 | −0.124 | −0.144 | −1.88 | +0.014 |
| OD5-gapgo-g4-L | 434 | 2.55 | −0.102 | −0.130 | −0.158 | −0.94 | +0.113 |
| OD2-failpush-p0.3-S | 9023 | 53.08 | −0.103 | −0.122 | −0.134 | −3.00 | +0.079 |
| OD6-failorb-rv2-orx-L | 320 | 1.88 | −0.120 | −0.146 | −0.168 | −1.58 | +0.213 |
| OD3-firstpb-d0.5-S | 879 | 5.17 | −0.126 | −0.162 | −0.193 | −1.66 | +0.153 |
| OD6-failorb-rv2-S | 257 | 1.51 | −0.133 | −0.215 | −0.251 | −1.19 | +0.243 |
| OD6-failorb-rv1-orx-S | 1482 | 8.72 | −0.139 | −0.206 | −0.216 | −1.70 | +0.171 |
| OD6-failorb-rv2-orx-S | 298 | 1.75 | −0.145 | −0.233 | −0.275 | −1.26 | +0.209 |
| OD7-gapdrive950-g4-L | 780 | 4.59 | −0.210 | −0.232 | −0.244 | −1.85 | −0.155 |

**What FIT shows:**
- **No trigger beats its matched null.** That null conditions on the trigger day happening (a look-ahead on the day), so it overstates what random entries can do. The fair comparison is the 09:50-known filter entered at 09:50 (OD7, OD8 and the NULL rows). Against that, the OR-low break in OD5-g4-S looks strong in FIT (+0.44 vs about +0.14). That edge does not hold in CHECK.
- **FIT is dominated by April 2025.** For OD5-g4-S, 484 of 695 trades fall in that month, and 2025-04-03 and 2025-04-04 alone make 264 of +305 R.

## 4. Finalists: CHECK and T2, each scored once

| finalist (how it got there) | FIT | CHECK avg / w/o best / w/o top-2 / t / R per ses | T1 comb (t) | T2 (t) | Tier A |
|---|---|---|---|---|---|
| OD5-gapgo-g4-S (debatable clause) | +0.439 | −0.023 / −0.071 / −0.112 / −0.22 / −0.08 | +0.169 (1.48), 1-day 0.57 | −0.161 (−2.39) | NEAR (T2 fails) |
| OD5-gapgo-g2-S (debatable clause) | +0.163 | −0.067 / −0.097 / −0.117 / −0.98 / −0.81 | +0.009 | −0.095 | FAIL |
| OD7-gapdrive950-g4-S (round 2, debatable) | +0.125 | −0.018 / −0.051 / −0.072 / −0.27 / −0.10 | +0.029 (0.39), 1-day 1.15 | −0.129 (−1.55) | NEAR (T2 fails) |
| OD1-orbdrive-rv2-S (round 3, amended null) | +0.062 | −0.059 / −0.065 / −0.072 / −1.90 / −0.52 | −0.011 | −0.111 (−2.68) | FAIL |
| **OD2-failpush-p0.6-orx-L** (round 3, amended null) | +0.051 | **−0.037 / −0.049 / −0.058 / −1.42 / −0.36** | −0.002 (−0.05) | **−0.051** (−1.92) | **MEETS** |

Unconditioned nulls in CHECK: OD1's is −0.060, so OD1's excess is zero. OD2's is −0.082, so OD2 is +0.045 above it.

**OD2-p0.6-orx-L in detail:**
- Gross is only +0.025R. 77% of exits are flat at 15:55, because the stop is wide (median 0.83 ATR) and the 1.5R target is rarely hit.
- It is positive in 11 of 22 months, and negative over 2026-06..09.
- By time of day it is flat overall, with the best bar at 09:55 (+0.125).

## 5. Rule changes inside this run

| Round | When written | What it did |
|---|---|---|
| 1 | Before any scoring | 32 configs |
| 2 | After round-1 FIT, before any CHECK | 6 configs that enter at 09:50, to separate the day-selection edge from the trigger |
| 3 | After FIT, before CHECK (amendment) | Excess measured against the unconditioned 09:50 null instead of the matched null, because the matched null is biased for trigger setups |

**Round 3 is post-hoc.** It is the only reason OD2-p0.6-orx-L and OD1-rv2-S became finalists. Treat OD2's MEETS with that in mind.

## 6. Duplication (symbol-days, T1 fit + check)

All overlaps are below 70%, so none of the finalists duplicates an existing setup.

| finalist | orb20_a | orb20_a-WB3 | BEG-ORB-stopOR | CWT09-g10 | RW3-FD | RW5-FD | highest other |
|---|---|---|---|---|---|---|---|
| OD2-p0.6-orx-L | 2.6% | 1.3% | 3.8% | <1% | <1% | <1% | gap_and_go (off) 2.5% |
| OD7-g4-S | 10.9% | 7.3% | 15.4% | 9.1% | <4% | <4% | L3-rsi5hi 31% |
| OD5-g4-S | 11.0% | 7.1% | 16.5% | 9.3% | <4% | 4.2% | L3-rsi5hi 28% |
| OD1-rv2-S | 13.3% | 6.2% | 22.5% | 2.6% | <3% | 2.4% | — |

**Gap-down trio:** OD7-g4-S takes 32% of CWT09's symbol-days, but CWT09 is only 9% of OD7's. RW3 and RW5 overlap under 5% with every finalist.

## 7. Fit with Primary (goal: positive daily R)

**Backtest proxy** (the current Primary lineup's home books from top10w, T1 combined):

| finalist | daily corr | avg R on proxy red days | avg R on proxy green days |
|---|---|---|---|
| OD2-p0.6-orx-L | −0.13 | +0.44 | −0.66 |
| OD7-g4-S | +0.03 | +0.42 | −0.26 |
| OD5-g4-S | +0.03 | +0.60 | +0.68 |

**Live window 2026-10-06..11-04** (22 sessions; backtest daily R vs live Primary daily R):

| finalist | corr | avg R on Primary red days |
|---|---|---|
| OD5-g4-S | +0.80 | −1.73 |
| OD5-g2-S | +0.80 | −3.76 |
| OD7-g4-S | +0.36 | +1.22 |
| OD2-p0.6-orx-L | +0.26 | −0.28 |

- The OD5 shorts stack on Primary's existing gap-down short bet and make its red days worse.
- No finalist turns more than 1-2 of the 16 live red days green.

**Rule changes inside that live window** (ledger): refire option B (10-14); L3-fromopen moved 10-20, 10-22 and 10-30; per-setup daily-stop latch (10-23); Primary sizing and cap 30 (10-28); −2R latch (10-29); Testing 0.15R cost filter (10-30). The backtests run one fixed rule set, so no rule change falls inside them.

## 8. Verdicts and next steps

| Setup | Verdict | Notes |
|---|---|---|
| **OD2-failpush-p0.6-orx-L** | Candidate under the testing-admission rule (meets the top-10 standard), low priority | Not profitable (CHECK −0.037, t ≈ 0). Its finalist path was post-hoc. If admitted, judge it as a brand-new setup and use its 2026-06..09 weakness as an early-exit flag. |
| OD7-g4-S and OD5-g4-S | Near-miss | Fail only the T2 leg. FIT is carried by April 2025. Earnings blackout not modelled. OD5 adds to Primary's red days. Do not force them. |
| BDI 11-20 failed-push short | Fails over 2 years | p0.3 −0.103 (t −3.0); orx p0.6 −0.004. The low capture on 11-20 does not come from a missing stock-level setup of this shape. Higher-level variants are banned (day-type switches) or already failed (OPX1). |
| OD3 first pullback | Fail | — |
| OD6 failed ORB | Fail | — |
| OD4 gap-fill | Fail | — |
| Opening-drive continuation (OD1 rv1, OD8) | Fail | — |

**Reusable lesson:** the matched random null overstates the null for any trigger that needs the move to continue first. Use the 09:50-known filter entered at 09:50 as the null for opening setups.

**Files** (scratch dir /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/open-drive, 77 MB):
- od.py (engine), score.py (costs, book, stats), overlap.py (duplication and Primary fit)
- prereg.json
- fit_table.csv, final_r12.json, final_r3.json, overlap_r12.json, overlap.json
- trade lists trades_T1*.parquet and trades_T2*.parquet; booked lists bk_*.parquet and bk2_*.parquet

Educational only — not financial advice.

## Robustness

null