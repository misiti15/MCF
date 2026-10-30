# rdt1030 DESIGN: the "15-min ORB + FVG" and "IRL -> ERL" Reddit post, as six testable stock families

*Educational only — not financial advice.* Design only: **nothing below has been scored.** The calibration numbers in
section 0.4 describe signal features (bar sizes, stop sizes, counts); no outcome column was read.

Source (owner 2026-10-30): an r/Daytrading-style post by a 6-year NQ/GC futures trader. Journal of 270 trades, 52% wins,
$798 avg win / $513 avg loss (1.56 ratio), PF 1.68. These are self-reported, futures-only numbers. They are a hypothesis,
not evidence (BDI charter, "suggestions, not rules").

Prior evidence the testers must keep in mind (read research/bdi/reddit/NOTES.md 1.3, 2.1, 2.4):
- **R14 ict-fvg** (5-min FVG retrace, full day) scored -0.045 to -0.086R. **R18 orb-fvg** (an OR30 break, then the
  R14 retrace) scored -0.053 to -0.089R. Every ORB variant so far has failed: t2-orb15, orb5, live-orb20_a
  (Apr-Jun -0.040R), and bdi-tg-orb20-a.
- The **regime split was the whole story**: ORB30 long was +0.128 on up sessions and -0.318 on down sessions. The
  ORB30 short was the mirror. Long ORB and FVG rules carry market beta, so up/down-day R and the "don't trade chop"
  gates (F2) are where any edge would have to show.
- pdl1030: a plain PDL sweep-reclaim long has **no gross edge**: +0.020R before costs, about 0.088R of costs. Its
  strongest entry-time gradient is cost per R. F4 must not become that trade again.

---

## 0. Shared harness (every family)

### 0.1 Data and splits
- **Frames:** 5-min lab frames from `research/history2y/lib.load_month`. The `tod` field is the bar **close** time, from 0950
  to 1500. Each family also loads the 09:35-09:45 head rows and the 15:05-15:55 tail rows, using
  `scan_1019.build_paths(month)`, which is the `refire1014/scan.head_rows(liq=True)` and `tail_rows` path that
  pdl1030/combo/build.py uses. The lab frames have **no bar open**. Where a body or "candle direction" is needed, the
  open is proxied by the prior 5-min close. For the first bar of the day it is `open_d = close / (1 + fromOpen/100)`.
  This is the proxy that `liq_live_lib.sweep` uses.
- **Context:** `lib.load_context(month)` gives `spy_fo`, `qqq_fo`, `breadth` and `breadth_open` per (date, tod). The
  SPY and QQQ per-bar `vwapDistPct` and `close` come from their own frame rows. SPY daily H/L/C come from `lib.daily()`,
  using only days before the session. **F6 1-min only:** `research/history2y/data/frames_tf/1min` covers the 80 core
  symbols, including QQQ/SPY/TQQQ/SQQQ, with real opens, `tod` 0950-1500.
- **Splits:** TRAIN is 2024-10 and 2025-03..2025-12. VALID is 2026-01..03 and 2026-07..2026-09-15. Copy the
  `_cut` monkeypatches and asserts from `research/bdi/pdl1030/combo/build.py` verbatim (CUT = 2026-09-15, assert no
  2024-11-01..2025-02-28 row, assert month not in 2026-04/05/06/10). `MCF_HIST_ALLOW_LOCKED` must be unset.
  **Never load** the locked block or the HOLD months.
- **Universe:** `adv20 >= 95e6` on the signal row and `atr_d > 0`. For OR-based families, all three head rows 0935, 0940
  and 0945 must be present, and the OR width must be >= 0.05 ATR_d. This drops zero-width or missing-print ORs (about
  0.1% of symbol-days). F6 trades only the named ETFs, with no adv filter.
- **ATR_d** is the frame's `atr_d`, the daily ATR(14) known before the open and constant within the day.

### 0.2 Simulator (copy, then patch; do not edit the originals)
Copy `sim` from `research/bdi/top5_1028/scan_1028.py`, which is stop-first inside a bar and uses 5-min bars to 15:55,
into each family's script. Apply four patches and state them in NOTES.md:
1. **Structural R:** each trade's `Rv` is its own price risk (entry minus stop for a long), with `dn = 1`. `up` becomes a
   **per-trade array** so that liquidity targets (F4) can be expressed. It is capped at 4R.
2. **Costs per side, all exits.** Entry costs `(0.01 + e*1e-4) * _mult(tod)`, where `_mult` is 1.4 before 10:30 and 1.0
   after. **Every exit costs `0.01 + x*1e-4`, target exits included.** The original charges target fills nothing. Stop
   and moved-stop exits add +0.02. All costs are multiplied by 3 on the extended tier (|gap| >= 20% or price < $5). R
   in the result is net of all costs, divided by `Rv`.
3. **Gap-through stops:** a bar that opens beyond the stop is not visible without opens. As a conservative proxy, a long
   stop fills at `min(stop, high[k])` and a short stop at `max(stop, low[k])`.
4. **Entry price array:** NaN means the signal bar's close (`em = 0`). A number means a limit fill at that price on a
   given row (F4 retrace). The fill bar is checked for the stop, never for the target, as in the original `lim` mode.

Break-even (`be`) and the 15:55 flatten are unchanged. **Parity check (F4-18):** the unpatched sim, run on CWT14 p05,
must reproduce the pdl1030 parent's -0.0677R within ±0.002. This proves the frames and splits match before anything
new is read.

### 0.3 Statistics, bar and reporting (rules 1-6, 13-14, 18, 21-22)
- **Every row is one config per side.** Long and short are counted separately.
- **N** = 2,000 + every config scored in this swarm. The pre-declared total below is 108, so N = 2,108 and
  **t_req = 0.9 × max(1.5, sqrt(2 ln N)) = 3.52**. Every added rework row raises N, and t_req is recomputed.
- **Pass (BAR90):** all of the following must hold:
  - day-clustered t >= t_req
  - walk-forward share of positive months >= 54%, using `gates.walk_forward` and the open months only
  - avg R > 0 on TRAIN **and** on VALID separately
  - >= 3 trades per session
  - avg R > 0 in SPY up sessions **and** SPY down sessions, using SPY EOD fromOpen as a descriptive split only
  - avg R above the random control
- **Reported for every row, failures first:**
  - n, trades/session, win rate, avg win and avg loss in R
  - avg R on TRAIN and VALID, and day t
  - WF share
  - up / flat / down-day R
  - avg R without the best day, and that day's share of total R (flag it at >= 50%)
  - busiest-session share
  - median cost/R
  - exit-code mix: target, stop, BE and 15:55
  - control avg R
  - For F2 and F5 also: opportunity retained, meaning trades kept and top-decile winners kept relative to the parent row
    (charter: >= 80% and >= 90% to be proposable as a filter).
- **Random control (rule 6):** for each trade, take K = 5 random universe symbols at the same signal bar, using seed
  20261030. Use the same side, the same risk in ATR units and the same target multiple, through the same sim and costs.
- **Process limits:** one core per process (`OMP/OPENBLAS/MKL/NUMBA_NUM_THREADS = 1`), RAM < 5 GB, months processed one
  at a time. Write per-month trade parquet only under
  `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/<label>/`, keep it under 120 MB,
  and delete it after the report.
- **Outputs:** notes and scripts go under `research/bdi/rdt1030/<label>/`: PLAN.md (written **before** any score),
  NOTES.md, results.csv and the scripts. Do not commit. Do not touch config/, mcf/ or the ledger.

### 0.4 Calibration (2025-06, TRAIN, liquid names, 09:50-11:00; signal features only, no outcomes)
- **OR15 width / ATR_d:** q10 0.23, q25 0.31, median 0.42, q75 0.56, q90 0.74.
- **OR5 width / ATR_d:** median 0.33.
- **5-min bar range / ATR_d:** median 0.12 from 09:50 to 10:30, 0.09 from 10:30 to 11:00 and 0.06 after 11:00.
- **F1-A-like long signals (FVG >= 0.05 ATR):** about 0.27 per liquid symbol-day, median time 10:10.
  - Stop distance per ATR_d: q10 0.17, q25 0.22, median 0.29, q75 0.39, q90 0.50.
  - **Median round-trip cost per R: 0.11R.**
- **What this means:** on NQ, a 30-point stop costs about 1-2% of R in fees and slippage. Here the same structure costs
  about 11% of R, so the gross edge must clear about 0.11R before anything is positive. With FVG >= 0.02 ATR the
  median cost/R is 0.13; with FVG >= 0.10 it is 0.08.
- **Indicator ranges (09:50-11:00):**
  - volumeRatio: median 0.52, q95 1.49
  - buyPressure: q25 -0.19, q75 +0.34
  - heat (skewed): q5 -29, q25 -14, median -7, q75 +1, q95 +23
  - RSI(14): q25 40, q75 67
  - sma50_dist_pct: q25 -0.46, q75 +0.74
- **SPY daily range / close:** q25 0.62%, median 0.87%, q75 1.28%.

### 0.5 Common definitions
- **OR15:** ORH and ORL are the max high and min low of the 0935, 0940 and 0945 rows (09:30-09:45). They are known at
  09:45. **OR5:** the 0935 row only.
- **Bullish 5-min FVG completed at row i:** rows i-2, i-1 and i are consecutive in the same symbol-day, and
  `low[i] - high[i-2] >= g × ATR_d` and >= $0.02. The gap is [high[i-2], low[i]]. A **bearish** FVG is the mirror:
  `low[i-2] - high[i] >= g × ATR_d`, with the gap [high[i], low[i-2]]. The FVG is known at the close of row i.
- **"Stop at the first candle of the FVG":** the extreme of candle i-2 on the far side of the trade. For a long that is
  **stop = low[i-2]**, the low of the candle whose high forms the gap bottom. For a short it is **stop = high[i-2]**. No
  buffer is added; stop exits pay +2c slippage. Candle i-2 may be an OR bar (0945).
- **Risk guard (all families):** skip the trade unless 0.03 ATR_d <= R <= 1.0 ATR_d. This is a sanity floor and cap.
  F1-G adds a stricter cost floor as its own row.
- **1R vs 2R switch:**
  - The post takes 2R when the stop is under 30 NQ points. The NQ daily ATR(14) in 2025 was about 300-450 points, so
    the **literal translation is R <= 0.085 ATR_d → 2R target, else 1R**.
  - With our stop distribution this gives 2R to fewer than 10% of trades.
  - A **rank-equivalent** switch, which gives 2R to the smaller-stop third of trades as 30 points plausibly did for NQ,
    is **R <= 0.20 ATR_d → 2R**. It is pre-declared as a variant.
- **Fresh break:** a close above ORH (or below ORL) at row tod >= 0950 counts when it is the first such close today on
  that side.
- **Efficiency ratio ER(x):** `|c[i-1] - open_d| / Σ|Δc|`, summed over the 5-min closes from the 0935 row through i-1.
  The first term is `|c[0935] - open_d|`, and at least 3 bars are required. It uses only bars that closed before the
  signal bar.

---

## F1 orb15-fvg-break: the post's model as written (5-min bars)

**Long rule, at row i:**
1. OR15 is defined (0.5).
2. A bullish FVG with g = 0.05 completes at row i.
3. The fresh break above ORH happened at row i-1 or at row i. That is, the break bar is the FVG's displacement candle
   or its third candle: "the move that closes outside the range forms the FVG".
4. `close[i] > ORH`.

**Entry:** at `close[i]`. **Stop:** `low[i-2]`. **Target:** 2R if R <= 0.085 ATR_d, else 1R. Flat at 15:55.

**Short:** the exact mirror below ORL, with stop `high[i-2]`.

**Window and frequency:** signal rows from 0955 to 1100. The earliest possible row is i = 0955, with i-1 = 0950 as the
first bar that can close outside the OR. Take the first signal per symbol-day per side. If the fresh break does not form
an FVG within that two-bar allowance, that side is finished for the day, as written.

**How it differs from earlier tests:**
- **R14/R18** waited for a later *retrace into* an FVG (R18 needed an OR30 break first). They stopped at a 0.25-ATR
  geometry or a close below the gap, with no OR15 and no 1R/2R switch.
- **F1** enters on the bar that *completes* the FVG at the break, uses OR15, puts the stop at candle i-2's extreme, and
  sets the target by stop size.
- **t2-orb15, orb5 and orb20_a** had no FVG requirement and used OR-fraction stops and targets.
- **CWT14 and bdi-reddit-orb-failed-break** fade a failed break, which is the opposite thesis.

| row | change from F1-A | sides |
|---|---|---|
| F1-A | as written (above) | L, S |
| F1-B | FVG g = 0.02 | L, S |
| F1-C | FVG g = 0.10 | L, S |
| F1-D | 2R switch at R <= 0.20 ATR_d (rank-equivalent) | L, S |
| F1-E | always 1R | L, S |
| F1-F | always 2R | L, S |
| F1-G | cost floor: round-trip cost <= 10% of R (cost-per-R gradient, pdl1030) | L, S |
| F1-H | late FVG: the FVG may complete up to 3 rows after the fresh break, if every close since the break stays beyond the OR level | L, S |
| F1-I | window extended to 1500 | L, S |

**18 configs.**

## F2 orb15-fvg + no-chop: F1-A plus one "when NOT to trade" gate per row

Every gate is known at the close of row i. Each gate is side-relative where marked.

| row | gate | sides |
|---|---|---|
| F2-G1 | OR15 width >= 0.30 ATR_d (an active open, not a dead one; about q25) | L, S |
| F2-G2 | OR15 width <= 0.55 ATR_d (range not already spent; about q75) | L, S |
| F2-G3 | stock ER (0.5) >= 0.40 (directional opening, not chop) | L, S |
| F2-G4 | index trend from open: `qqq_fo` >= +0.20% (L) / <= -0.20% (S) | L, S |
| F2-G5 | SPY ER (same definition, on SPY rows through i-1) >= 0.40 | L, S |
| F2-G6 | SPY prior-day range (H-L)/C >= its trailing 20-day median (known before the open) | L, S |
| F2-G7 | relative volume: `volumeRatio` >= 1.0 at row i (about the top 10-15% of early rows) | L, S |
| F2-G8 | no double break: no close beyond the opposite OR side earlier today | L, S |
| F2-G9 | G3 and G4 together (the one pre-declared pair) | L, S |

**18 configs.** Report opportunity retained relative to F1-A for every row.

## F3 orb5-be-2max: the "NQ - BE / context / 5min / 2 trades / 30 points 2R / more 1R" backtest

**Base rule (F3-A):**
- **Entry signal:** F1-A's FVG entry, but on **OR5** (the 0935 bar's high and low).
- **Target:** 2R if R <= 0.085 ATR_d, else 1R.
- **Break-even:** the stop moves to entry once MFE reaches +1R (`be = 1.0`). This matters only for 2R trades.
- **Context gate:** QQQ is on the trade side of its open (`qqq_fo > 0` for a long, `< 0` for a short).
- **Max 2 trades per symbol-day.** Trade 2 must have its signal row after trade 1's exit row (`xrow` from the sim). It
  needs a new break: at least one close back inside the OR after trade 1's break, then a new close beyond either OR side
  that completes an FVG under the same rules. Trade 2 may be on either side.
- **Window:** 0950-1100.

Sides are reported by the side of trade 1. Trade 2 is attributed to its own side.

| row | change from F3-A | sides |
|---|---|---|
| F3-A | as above | L, S |
| F3-B | no context gate | L, S |
| F3-C | BE at +0.5R (so it also acts on 1R trades) | L, S |
| F3-D | max 1 trade per symbol-day | L, S |
| F3-E | stop after a win: trade 2 only if trade 1 lost | L, S |
| F3-F | 2R switch at R <= 0.20 ATR_d | L, S |
| F3-G | always 2R with BE at +1R | L, S |
| F3-H | window extended to 1500 | L, S |
| F3-I | context = SPY on the trade side of its VWAP (SPY `vwapDistPct` sign) instead of QQQ from open | L, S |

**18 configs.**

**Before any module is proposed:** check that live LabStrategy supports a second entry per symbol-day. If it does not,
F3 needs a re-entry key, which would be a config change outside this study.

## F4 irl-erl: liquidity sweep, then displacement, then 15-min (HTF) FVG (+ mirror short)

**HTF bars:** 15-min bars aligned to 09:30, ending at 0945, 1000, 1015 and so on. Build them from the 5-min rows the way
`liq_live_lib.sweep(k=15)` does: H = max, L = min, C = the last 5-min close, O proxy = the prior 15-min close (`open_d`
for the first bar). An HTF bar is known at its last 5-min row.

**Long rule (F4-01):**
1. **Sweep.**
   - The PDL variant sweeps the prior-day low. Some 5-min row from 0935 onward has `low <= PDL - 0.05 ATR_d`, and the
     day opened above the PDL.
   - The ORL variant sweeps the **day's early low**, the OR15 low. Some row from 0950 onward has
     `low <= ORL - 0.05 ATR_d`.
   - The sweep low **SL** is the day's low at entry. If a new low prints after the FVG's first candle, the setup is void.
2. **Displacement.** The middle HTF candle (K-1) has body `C[K-1] - O[K-1] >= 0.20 ATR_d`.
3. **HTF FVG.** `L[K] - H[K-2] >= 0.05 ATR_d`. Candle K-2 is at or after the sweep's HTF bar, and the sweep bar may
   itself be K-2. `C[K] >` the swept level (back through it).
4. **First** HTF FVG after the sweep, completed within 8 HTF bars (2 hours) of it.

**Entry:** the close of HTF bar K (formation). Window 1015-1400.

**Stop:** SL - 0.02 ATR_d. Risk must satisfy 0.10 <= R <= 1.0 ATR_d.

**Target DOL** (draw on liquidity): the nearest of {PDH, the session HOD made before the sweep} that is >= 1.0R above
entry. If neither is, use 2R. The cap is 4R.

**Short mirror:** a sweep of PDH (or ORH), bearish displacement, a bearish HTF FVG, stop at SH + 0.02 ATR_d, and a DOL
of {PDL, the pre-sweep session LOD}.

**Retrace variant:** after formation, rest a limit at the FVG top `L[K]` (long). It fills on the first 5-min row within
the next 6 rows (30 min) whose `low <= L[K] - 0.01`. The fill bar is checked for the stop (patch 4). The order is
cancelled if price reaches the target before the fill. R is measured from the fill price.

**How it differs from earlier tests:**
- **CWT14 PDL and LIQ-pdl-sweep-open15** enter on a reclaim close within 3 bars, or a 15-min close above the sweep bar's
  open. They use a fixed 0.25-ATR stop and VWAP or t05s1 targets.
- **F4** requires a large-bodied 15-min displacement candle **and** a 15-min FVG, stops under the sweep low, and targets
  liquidity.
- **R15 sweep** used the LOD and a close back above it, with no FVG.
- **The pdl1030 failure is a known prior.** The parity row F4-18 re-runs it only as a harness check.

| row | level, side | entry | target | other |
|---|---|---|---|---|
| F4-01 | PDL, L | formation | DOL | |
| F4-02 | PDL, L | formation | 2R | |
| F4-03 | PDL, L | retrace | DOL | |
| F4-04 | PDL, L | retrace | 2R | |
| F4-05 | ORL, L | formation | DOL | |
| F4-06 | ORL, L | formation | 2R | |
| F4-07 | ORL, L | retrace | DOL | |
| F4-08 | ORL, L | retrace | 2R | |
| F4-09 | PDH, S | formation | DOL | |
| F4-10 | PDH, S | formation | 2R | |
| F4-11 | PDH, S | retrace | DOL | |
| F4-12 | ORH, S | formation | DOL | |
| F4-13 | ORH, S | formation | 2R | |
| F4-14 | PDL, L | formation | DOL | displacement >= 0.30 ATR_d |
| F4-15 | PDL, L | formation | DOL | HTF FVG >= 0.10 ATR_d |
| F4-16 | PDL, L | formation | DOL | sweep depth: any trade-through (low < PDL) |
| F4-17 | PDL, L | formation | DOL | BE at +1R |
| F4-18 | parity: CWT14 p05 with the unpatched sim (harness check, not a candidate) | | | |

**18 configs**, including parity.

## F5 fvg-context: one indicator per row on fixed base entries

The base entries are fixed **now**, not chosen after F1/F4 results, to avoid selection leakage: **F1-A** (both sides)
and **F4-01** (long). Each row adds one indicator, side-relative, known at the signal row.

| row | base | indicator (L / S) |
|---|---|---|
| F5-I1 | F1-A L, S | VWAP side: `vwapDistPct` > 0 / < 0 |
| F5-I2 | F1-A L, S | RSI(14) momentum: `rsi` >= 55 / <= 45 |
| F5-I3 | F1-A L, S | RSI(5) not exhausted: `rsi5` <= 90 / >= 10 |
| F5-I4 | F1-A L, S | order flow: `buyPressure` >= +0.20 / <= -0.20 |
| F5-I5 | F1-A L, S | move from open: (close - open_d) / ATR_d >= +0.30 / <= -0.30 |
| F5-I6 | F1-A L, S | SMA50 (5-min) side: `sma50_dist_pct` > 0 / < 0 |
| F5-I7 | F1-A L, S | MarcoFlow heat: `heat` >= +10 / <= -20 (asymmetric, matching the skew in 0.4) |
| F5-I8 | F1-A L, S | index context: `breadth` >= 0.60 / <= 0.40 |
| F5-J1 | F4-01 L | VWAP side: `vwapDistPct` > 0 |
| F5-J2 | F4-01 L | order flow: `buyPressure` >= +0.20 |

**18 configs.** Report opportunity retained relative to the base row.

## F6 index-native: F1/F3/F4 on QQQ/SPY, traded as 3x ETFs (as the IDX setups do)

**Signal and trade:** the signal is computed on QQQ (or SPY) bars and traded on TQQQ/SQQQ (or SPXL/SPXS) at the **same
row's close**.
- The QQQ stop and target are mapped by percentage: `level_ETF = e_ETF × (1 + 3 × (level_QQQ / e_QQQ - 1))`. A QQQ
  short is a **long** SQQQ with the mirrored percentage.
- The sim then runs on the ETF's own bars, with the ETF's prices and costs.
- The 1-min rows use `frames_tf/1min` for the FVG and the ETF path through 15:00, then the 5-min tail rows to 15:55.

**1-min OR handling:** the OR still comes from the 5-min head rows. 1-min data starts at 0950. A day is skipped for a side
if the 0950 5-min close is already beyond the OR on that side.

| row | rule, signal symbol → traded | side |
|---|---|---|
| F6-01 / 02 | F1-A QQQ → TQQQ / SQQQ | L / S |
| F6-03 / 04 | F1-A SPY → SPXL / SPXS | L / S |
| F6-05 / 06 | F1-A with **1-min** FVG on QQQ → TQQQ / SQQQ | L / S |
| F6-07 / 08 | F3-A QQQ → TQQQ / SQQQ | L / S |
| F6-09 / 10 | F4 PDL-long (F4-01) → TQQQ / PDH-short (F4-09) → SQQQ, on QQQ | L / S |
| F6-11 / 12 | F4 ORL-long (F4-05) / ORH-short (F4-12) on QQQ → TQQQ / SQQQ | L / S |
| F6-13 / 14 | F4-01 / F4-09 on SPY → SPXL / SPXS | L / S |
| F6-15 / 16 | F1-A on {QQQ, SPY, TQQQ, SQQQ}, each traded as itself (the requested index-only row) | L / S |
| F6-17 / 18 | F1-A on QQQ traded as QQQ (unlevered reference) | L / S |

**18 configs.**

**These rows cannot meet ">= 3 trades/session"**, because there are at most 1-4 symbols. They are reported in full and
judged on every other gate. A pass would need an owner exception on trade rate, as for the IDX family. Never relabel one
to cross the bar.

---

## Budget and order
- **Configs:** F1 18 + F2 18 + F3 18 + F4 18 + F5 18 + F6 18 = **108**. N = 2,108, t_req = 3.52.
- **Order:**
  1. Each tester copies its family's table into its PLAN.md unchanged. Any deviation is a dated amendment, and its rows
     are counted.
  2. Run the F4-18 parity check.
  3. Score TRAIN and VALID once.
  4. Report everything.
- **Rework (rule 18):** only after a row fails, and only as new counted rows: neighbours, one condition removed, one
  condition added.
- **Finalists:** a finalist gets a mask module under `research/bdi/rdt1030/<label>/` with the
  `research/bdi/cwt/live/*.py` interface: `SIDE`, `GEOM = "S"`, `LAYERS`, `mask(df)`, `stop_price(f, i)`,
  `target_price(f, i, stop)`. It must use the same 0935-0945 head rows as `cwt/live/verify.py`. Mask parity with the
  scan is checked on 300 symbol-days. The locked holdouts are scored once, by the lead.
