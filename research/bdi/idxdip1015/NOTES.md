# Index open-dip bounce — results (2026-10-15)

*Educational only — not financial advice.* Backtest on history (SIP 1-minute bars), costs in. Not paper, not live.
Plan: `PLAN.md` (written before the grid ran). Scripts: `scripts/` (`dipstats.py`, `grid.py`, `conflicts.py`,
`make_config.py`, `render_yaml.py`, `fetch_spuu.py`). Locked block 2024-11-01..2025-02-28 excluded everywhere.
Samples: DEV 359 sessions; older holdouts (Apr–Jun 2026, Sep 16–Oct 7 2026) 78 sessions, scored once for the finalists.

## Owner change (2026-10-15): 3x only, one instrument per variant — results
Owner: each variant trades ONLY the highest-leveraged ETF with the most volume that day. S&P (V2/V3/V5, signal SPY):
SPXL or UPRO; V1 (signal QQQ): TQQQ (only 3x long QQQ tracker), trail and hold. 5 setups (`PROPOSED_CONFIG.md`).
Script `scripts/pick3x.py` -> `pick3x_trades.csv`, `pick3x_results.csv`, `pick3x_picks.csv`, `pick3x_counts.json`.
* **Pick rule (production):** the candidate with the larger dollar volume (sum close x volume) from 09:30 through the
  trigger bar — today's tape, known at decision time, causal in the backtest (later bars ignored). Ties -> first listed.
  Why today's rather than the prior session's: it reflects the day's actual liquidity on a stress day, needs no extra
  priors, and is computed from the same bars live and in the backtest. Robustness: the prior-session rule and a
  hindsight full-day rule give the same trades on all but 1-2 days and mean R within 0.007R in every rec20 row
  (today vs full-day pick agree on 26/31 trigger days, prior vs full-day 30/31). SPXL is picked on 85% of DEV trades
  (22 of 26), UPRO on 4.
* **Configs:** 252 new (3 S&P variants x 6 triggers x 7 exits x 2 pick rules: today, prior); V1 TQQQ 42 rows re-run,
  identical to `grid.py` (not new). Lineage 882 + 252 = **1,134; bar t >= 3.75. Not met.** Best t among new rows with
  n >= 5: 1.12; n >= 8: 1.00. 45% of rows have a positive mean R. Costs in; locked block never loaded.
* **Chosen rows (rec20, DEV) vs the prior per-instrument results:**

| variant / exit | 3x pick: n / mean R / t | prior: index ETF | prior: SPXL | prior: UPRO | prior: 2x (SSO / QLD) | ex-best-day (3x) | holdout once (3x) |
|---|---|---|---|---|---|---|---|
| V1 TRAIL (TQQQ) | 8 / +0.00 / 0.01 | QQQ +0.04 | — | — | QLD +0.07 | -0.60 | 1: +0.06 |
| V1 HOLD (TQQQ) | 8 / +0.15 / 0.23 | QQQ +0.17 | — | — | QLD +0.13 | -0.34 | 1: +0.76 |
| V2 TRAIL | 5 / +0.78 / 0.78 | SPY +0.76 | +0.78 | +0.98 | SSO +0.61 | -0.10 | no trade |
| V3 TRAIL | 7 / +0.47 / 0.64 | SPY +0.44 | +0.47 | +0.61 | SSO +0.34 | -0.17 | 2: +0.20 |
| V5 TRAIL | 14 / +0.51 / 1.00 | SPY +0.48 | +0.54 | +0.58 | SSO +0.24 | +0.16 | 3: +0.18 |

  The pick is mostly SPXL, so the 3x rows track the SPXL rows; UPRO alone was slightly higher, but choosing UPRO by
  its backtest R would be selection on 5-14 trades.
* **Leverage, R and dollars (honest reading).** Sizing is min(risk-based, slot notional). A bigger % dip on a 3x ETF
  does **not** mean a bigger R: the stop sits under the ETF's own morning low, so the stop distance is ~3x wider in %
  and risk-based sizing would buy ~1/3 of the shares-value for the same dollar risk — R is unchanged (the table: 3x
  R ≈ index-ETF R, within noise). In Testing 1 the slot cap binds instead (equity $100k x 3.8 / 400 = **$950** per
  slot; risk-based would be $250 / stop distance, i.e. tens of thousands of dollars), so every instrument gets ~$870-940
  of notional. With equal notional, dollar risk and dollar P/L scale with leverage: 3x DEV mean $ risk per trade
  $12-17 and mean P/L +$13 (V5) / +$24 (V3) / +$34 (V2) / +$20 (V1 trail), vs ~1/3 of that on SPY/QQQ (SPY TRAIL
  ≈ +$4-11 per trade at $950). Losers scale the same way. So the 3x choice raises $ per trade (still far below the $250
  risk budget), not edge per unit of risk; read the scorecard in R.

## Per-instrument grid (superseded choice; evidence kept)

## Failures first
* **Nothing meets the research bar.** N = 756 configurations in this grid (lineage 882 incl. the 126-config scan);
  bar t >= 3.64 (3.68 lineage). Best t among rows with n >= 8: 1.72; with n >= 5: 2.16. The 18 rows with t >= 3.64 have
  n = 2–3. 43% of index-ETF rows have a positive mean R (48% of all rows).
* **Samples are tiny.** Dip days in DEV: V1 9, V2 5, V3 7, V5 14 (holdout 1 / 0 / 2 / 3). V2 and V3 have no DEV dip
  day after 2025-09-01, so the H2 half is empty for them. The pre-declared choice rule (n >= 8) can only rank V1 and V5;
  V2/V3 follow the cross-variant choice.
* **Concentrated.** Without the best day, the chosen rows' mean R is -0.60..+0.37 (index ETF: V1 -0.56, V2 -0.10,
  V3 -0.18, V5 +0.13).
* **SPUU is thin**: downloaded (19,956 bars over 2 years, ~21 bars/day, ADV ~$2.8M). Its rows have fewer trades and
  larger R because its sparse bars make its "morning low" coarse — do not read SPUU numbers as evidence. Live, the
  participation cap (10% of the last 5 bars' volume) will often size SPUU to 0 shares ("size < 1 share after liquidity cap").

## Dip-day statistics (index bars, DEV + holdout)
| variant | days | drop to morning low (mean / median) | morning low time (median) | low before 09:50 / 09:50-10:05 / 10:05-11:00 | new low after 10:05 | recovered by 10:30 / 12:00 / close (median, x drop) | closes above open |
|---|---|---|---|---|---|---|---|
| V1 QQQ >=1% by 09:55 | 10 | -1.52% / -1.37% | 10:16 | 20 / 30 / 50% | 60% | 0.27 / 0.38 / 0.50 | 20% |
| V2 SPY >=0.75% by 09:45 | 5 | -1.38% / -1.11% | 09:47 | 60 / 20 / 20% | 60% | 0.79 / 0.36 / -0.05 | 40% |
| V3 SPY >=0.75% by 09:55 | 9 | -1.24% / -1.11% | 09:59 | 44 / 33 / 22% | 56% | 0.63 / 0.49 / 0.31 | 33% |
| V5 SPY >=0.5% by 09:45 | 17 | -1.01% / -0.85% | 09:59 | 41 / 24 / 35% | 59% | 0.57 / 0.49 / 0.39 | 35% |
Morning low = lowest low 09:30-11:00. The bounce is real by 10:30 on the S&P variants (57-79% of the drop back, median)
but fades into the afternoon and most dip days still close below the open — which is why trailing out beats holding.
A 10%/20% recovery trigger fires on 100% / 90-100% of dip days inside 09:50-10:05 (usually on the first eligible bar).

## Grid — index ETF rows (DEV), trigger = 20% recovery
mean R per trade (n), costs in; T1030 = the fixed 10:30 exit baseline.
| variant | T1030 | R50 | R75 | R100 | VWAP | TRAIL | HOLD | ctrl: same days, random time (TRAIL) | ctrl: all days, random time (TRAIL) |
|---|---|---|---|---|---|---|---|---|---|
| V1 QQQ | -0.16 (8) | -0.39 | -0.23 | -0.36 | -0.02 | +0.04 (8), t 0.06 | **+0.17** (8), t 0.26 | +0.01 | -0.17 |
| V2 SPY | +0.30 (5) | -0.18 | +0.16 | +0.03 | +0.40 | **+0.76** (5), t 0.78 | -0.38 | +0.26 | -0.23 |
| V3 SPY | +0.21 (7) | -0.15 | +0.21 | -0.07 | +0.44 | **+0.44** (7), t 0.61 | -0.36 | +0.04 | -0.23 |
| V5 SPY | +0.02 (14) | +0.04 | +0.05 | -0.25 | +0.18 | **+0.48** (14), t 0.94 | -0.27 | -0.05 | -0.23 |
* Trigger sensitivity (TRAIL, index rows): rec05 / rec10 / rec15 / rec20 — V1 +0.16/+0.02/+0.02/+0.04; V2 +0.76 all;
  V3 +0.38/+0.24/+0.24/+0.44; V5 +0.38/+0.31/+0.26/+0.48. 20% >= 10% in every variant; 5-20% is a positive plateau for
  V2/V3/V5. hi3 and VWAP-reclaim triggers: fewer trades (VWAP 2-9) and no consistent sign — not chosen.
* Exits: TRAIL beats the fixed 10:30 exit in all four variants (+0.04 vs -0.16, +0.76 vs +0.30, +0.44 vs +0.21,
  +0.48 vs +0.02). Retrace targets (50/75/100%) are mostly negative: the target caps the winners while the stop takes
  full losers. HOLD is negative on S&P (afternoon fade) but best on V1 QQQ.
* Controls: dip conditioning beats random 09:50-10:05 longs on all days (-0.23R, -1.2 bps). The trigger beats a random
  entry time on the same dip days by +0.03 (V1) to +0.53R (V5) — small n.
* Leveraged trackers (same signal, own levels): TRAIL rec20 DEV mean R — V2 SPY/SSO/SPXL/UPRO +0.76/+0.61/+0.78/+0.98;
  V3 +0.44/+0.34/+0.47/+0.61; V5 +0.48/+0.24/+0.54/+0.58; V1 QQQ/QLD/TQQQ +0.04/+0.07/0.00 (HOLD +0.17/+0.13/+0.15).
  R is consistent across leverage (stop distance scales ~2x/3x with the tracker), SSO lowest (1c/share costs on a ~$72
  price). Bps scale with leverage (V5 TRAIL: SPY 43, SSO 75, SPXL 144, UPRO 152 bps).
* Holdout, scored once (finalists, index ETF; n is too small to mean much): V1 QQQ TRAIL +0.05R / HOLD +0.76R (1 trade);
  V2 no trade; V3 SPY TRAIL +0.14R (2); V5 SPY TRAIL +0.11R (3). Leveraged rows similar (+0.08..+0.27R).

## Choice for Testing 1 — first version, superseded by the 3x-only change above (5 setups)
* Trigger: 20% recovery of the open-to-low drop off the running low, bar closing 09:50-10:05 (owner's 10% is inside
  the plateau and slightly weaker).
* Exit: stop at the traded symbol's running low - 10% of its drop; **trail 1R behind the best once +1R; no target;
  15:55 flatten** (V2, V3, V5). V1 (QQQ) gets two exit variants because the data prefer HOLD there: TRAIL and HOLD.
* Instruments: one setup per instrument (per-instrument rows on the scorecard): V1 QQQ/QLD/TQQQ x 2 exits;
  V2/V3/V5 SPY/SSO/SPUU/SPXL/UPRO. 21 setups. Parity: `scripts/make_config.py` rebuilds every proposed setup through
  `build_strategies` and reproduces the grid's trades exactly (21/21).

## Sizing and the other setups
* Sizing is min(risk-based on the traded symbol's own stop, slot notional). In Testing 1 the slot cap
  (equity x 3.8 / 400 ≈ 0.95% of equity) binds for every instrument (risk-based would be 25-80% of equity), so every
  instrument gets about the same dollars; **$ risk and $ P/L scale with leverage, R does not** — read the scorecard in R.
* Nested variants: every V2 day is also a V3 and V5 day with the same trigger, so the same trade is taken by up to
  3 setups x 5 instruments (+ V1) on one signal. max_lots_per_symbol 3 allows exactly the three S&P lots per symbol.
* Conflicts (`conflicts.csv`): on the dip days, other Testing-1 setups never held a position in these ETFs strictly before
  our entry. heat_fade_short / heat_fade_short-FD short them **in the same poll** on 24 of 171 rec20-TRAIL variant-instrument trade-days.
  With `longs_first_on_ties: true` (already on in Testing 1) and the IDX setups first in `setup_order`, the long takes the
  tie and heat_fade_short gets "opposite side held" on those symbols; that is a cost to heat_fade_short's Testing count
  and should be reported with it (rule 20). A long by another setup can take one of the 3 lots (seen twice, TQQQ).
* Code changes for this: `DayContext.peers` (every symbol's bars, set by the backtester and the live runner),
  `pinned_symbols` includes a setup's `signal_symbol`, and pinned symbols are exempt from the extended-tier in-play filter
  (so SPUU is not dropped). These only matter for symbols a config names.

## Finding outside this study (housekeeping)
The live runner never acts on `Signal.exit_by` (only the backtester does): setups that rely on it (index_gap_fill 12:00,
orb20 A 15:50, gap_continuation 15:55, gap_and_go/gap_fade `exit_by`) are flattened at the session flatten live, not at
their exit time. The proposed IDX setups do not use `exit_by` (the 10:30 rule was only a backtest baseline).
