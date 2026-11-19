Educational only — not financial advice

# ULT-19 LR-LITE — shrunk linear score on "persistent" factors, LONG + SHORT (round 2)

**Tier: FAIL.** Fit (walk-forward out-of-fold) avg R is negative for all 6 configurations. The fit pick 19b scored
**-0.026R/trade on check** (t = -2.52, 7.55 trades/session). All 6 configurations are negative on check (plateau
diagnostic). It does not beat the benchmark and is not TIER A or TIER B.

## In plain words
- The idea: one small linear score over 14 inputs (time of day, gap, distance from the open and from VWAP, daily ATR %,
  cost, SPY tape, RSI5/RSI14), fitted only on the fit half. Any input whose effect had a different sign in the two parts
  of the fit half was switched off, so the model would keep only stable effects.
- **The stability filter switched off almost every directional input.** Gap, distance from open, distance from VWAP,
  SPY from open, SPY 30-min change and RSI5 all changed sign between fit part A (2024-10 + 2025-03..05) and part B
  (2025-06..09). The SPY tape inputs flipped hardest (A: follow the tape, +0.033 / +0.025; B: fade it, -0.016 / -0.019).
  On this target (after-cost R of a 45-min hold), the "persistent factors" from WAVE1 did not persist.
- What was left: time-block intercepts (all negative, i.e. costs), "prefer volatile names" (ATR % +), "prefer cheap
  names" (cost_r -) and a weak RSI14 mean-reversion term (long when RSI14 < 50). That picks entries a little better than
  random on the same names (+0.01 to +0.05R), but every version still loses after costs.
- Volume was fine (2-11/session out-of-fold, 7.5-35/session on check). The edge was missing.

## Build (faithful to round2/PLAN.md sec. 3 "ULT-19" + ULT-11's target / rule / walk-forward)
- Features from the **live module itself** (`modules/ULT-19.py` raw/design/scale/score), bt.py imports it: 5 time-block
  dummies; s x gap; s x fromOpen/dATR; s x vwapDist/dATR; atr_d %; cost_r; s x spy_fo; s x spy_r30; s x (RSI5-50);
  s x (RSI14-50). Signed inputs scaled by training sd (natural zero kept); atr_d % and cost_r z-scored; clip +-5; NaN -> 0.
  spy_r30 = SPY change over 30 min from spy_fo, NaN before 10:20 (frames start 09:50; the module does the same live).
- Target (FIT only): after-cost R of a 45-min time exit (decision close -> 5-min close at tod+45, frames + headtail tail
  rows), LR8 both legs + 1.2 bp borrow on shorts, 0.25-dATR units, winsorised +-4. Ridge alpha 1e5, long + short rows
  stacked (each side only where its universal filters pass; shorts only ETB).
- Stability filter: final model A vs B as PLAN; walk-forward folds split their own training sessions chronologically in
  two (the early folds have no B data). This was fixed in code before any fit score was seen.
- Rule: per name the better-scoring side; enter if score > tau and the side passes its filters; <= 3 entries per 5-min
  bar (highest score first), session cap 2k, one lot per symbol, next entry >= 15 bars later (45-min hold + 30-min
  cooldown), max 2 per symbol-session. tau = constant giving k entries/session when this rule runs on the training
  period's in-sample scores (bisection). Realised OOF volume is below k because the fold models drift.
- Chassis: entry at the OPEN of the 1-min bar starting at the decision close; TX-45 with a catastrophic stop at the
  decision close -+ 2 x 0.25 dATR (as the live stop_price); R per unit of risk (2 x 0.25 dATR), LR8 + 2c on stops +
  1.2 bp borrow on shorts. U2 intake, universal filters, entries 09:50-15:00, flat by 15:45.
- Walk-forward folds 2025-05..09 (105 sessions pooled OOF) = the "fit" figures for selection and the TIER A fit test.
- Freeze: `fitsel.json` 2026-11-19T06:21:38Z (sha256 of bt.py, module, model json) **before** any check feature was
  built; check scored once at 06:23:22Z (`check_once.json`); plateau afterwards (`check_plateau.json`).
- No look-ahead: only the frame columns close/fromOpen/vwapDistPct/gap/atr_d/rsi/rsi5/adv20 + context spy_fo are read
  (asserted; no win_*/r_*/heat columns). Locked block never read (month list, pyarrow date filters, no_locked asserts).

## Fit grid (pooled walk-forward OOF, 2025-05..09, 105 sessions; in-sample all-FIT in brackets)
| Config | k | Universe | trades/sess | avg R | avg R w/o best day | total R | total R w/o best day | t (day-clustered) | long / short avg R (n) | vs random | in-sample avg R (170 sess) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 19a | 5 | UA $50M, cost_r<=0.10 | 2.03 | -0.033 | -0.049 | -6.9 | -9.9 | -1.12 | -0.037 (184) / -0.007 (29) | -0.010 | [-0.010, 5.0/sess] |
| **19b** | 5 | UB $200M, cost_r<=0.06 | 2.10 | -0.020 | -0.039 | -4.3 | **-8.2** | -0.55 | -0.021 (195) / -0.013 (25) | +0.050 | [-0.004] |
| 19c | 10 | UA | 4.51 | -0.024 | -0.034 | -11.5 | -15.8 | -1.17 | -0.030 / +0.022 | -0.005 | [-0.007] |
| 19d | 10 | UB | 4.55 | -0.020 | -0.034 | -9.3 | -15.8 | -0.73 | -0.023 / +0.001 | +0.012 | [-0.011] |
| 19e | 20 | UA | 9.16 | -0.002 | -0.013 | -2.2 | -11.8 | -0.12 | -0.008 / +0.050 | +0.004 | [-0.002] |
| 19f | 20 | UB | 10.86 | -0.007 | -0.021 | -7.7 | -22.5 | -0.33 | -0.011 / +0.014 | +0.048 | [+0.002; best-day share 199% 1 day 2025-03-11] |

Selection (PLAN sec. 5): highest OOF total R minus the best fit day among configs with >= 2.0 OOF trades/session (all
6 qualify) -> **19b**. (Ranking by plain total R would pick 19e; it is also negative on check, -0.016.) Fit best-day
share n/a (total < 0). The window 2025-04-03..04-09 is not in the OOF folds (fold months start 2025-05), so the OOF
figures "without 04-03..04-09" equal the figures above; in-sample 19b without it: +0.005.

Frozen final model (19b, UB): w = time blocks [-0.028, -0.030, -0.029, -0.020, -0.031], atr_d % +0.0076,
cost_r -0.0070, RSI14 -0.0043; zeroed by the stability filter: gap, fromOpen, vwapDist, spy_fo, spy_r30, RSI5.
tau = 0.0130 (0.25-dATR units of predicted R). UA's final model zeroes the same six.

## CHECK — fit pick 19b scored ONCE (2025-10-01..2026-11-04, 276 sessions)
| Metric | Value |
|---|---|
| trades / per session | 2,083 / **7.55** (268 sessions traded) |
| win rate | 46.6% |
| avg R (per risk unit) / in 0.25-dATR units | **-0.0259** / -0.0518 |
| avg R w/o best day (2026-07-17) | **-0.0283** (best-day share n/a, total < 0) |
| total R / per session | -53.9 / -0.195 |
| worst day / per trade-session | -6.57R / -0.846 |
| day-clustered t | **-2.52** |
| SPY up / flat / down (end-of-day label) | +0.011 (682) / -0.016 (825) / -0.084 (576) |
| long / short | -0.026 (1,819) / -0.025 (264) |
| first / second half | -0.022 / -0.030 |
| same-name random entry / signal minus random | -0.036 / **+0.011** |
| without 2025-04-03..04-09 | -0.0259 (window not in check) |
| median hold | 45 min |
| bias diagnostic (signal-close fill, no borrow) | -0.0247 (the two fixed biases cost ~0.001R/trade here) |

## Bars
- TIER A: check avg R > 0 **no** (-0.026); w/o best day > 0 **no**; fit (OOF) avg R > 0 **no** (-0.020); >= 2/session yes
  (7.55); no look-ahead yes. -> not TIER A. TIER B (fit > 0 and check > -0.02): no. -> **FAIL**.
- BEATS (needs t >= 3.65 at N = 774, avg R > +0.0836, w/o best day > +0.0734): no on every term except the worst-day
  ratio (-0.846 >= -2.152).

## Plateau diagnostic (every config's own all-FIT model on check, after the single score; never re-selects)
| Config | trades/sess | avg R | avg R w/o best day | total R | vs random | long / short |
|---|---|---|---|---|---|---|
| 19a | 7.49 | -0.023 | -0.025 | -47.2 | -0.001 | -0.024 / -0.016 |
| 19b | 7.55 | -0.026 | -0.028 | -53.9 | +0.011 | -0.026 / -0.025 |
| 19c | 15.88 | -0.022 | -0.023 | -95.2 | +0.009 | -0.023 / -0.015 |
| 19d | 16.32 | -0.013 | -0.015 | -59.6 | +0.020 | -0.014 / -0.011 |
| 19e | 33.53 | -0.016 | -0.017 | -146.5 | +0.016 | -0.018 / -0.007 |
| 19f | 34.91 | -0.014 | -0.016 | -137.1 | +0.024 | -0.016 / -0.009 |
6 of 6 negative; t from -1.5 to -2.5. No plateau to salvage.

## Configurations tried
6 grid (19a..19f, walk-forward folds are part of each config) + 1 bias diagnostic = **7**, as pre-registered in
round2/PLAN.md sec. 4 (already in the cumulative N = 774; t floor 3.65). Random-entry controls and the plateau are
reported, not counted.

## Known biases / caveats
- Today's symbol list (survivorship) flatters longs; the model is ~87% long, so the true figure is likely worse.
- ETB from today's universe.csv (not point-in-time). Borrow fee 1.2 bp per short is an estimate.
- Per-bar top-3 ranking and the 2k session cap are account-side; the live LabStrategy cannot rank across names, so a
  live copy would take entries first-come (documented in the module). The module's refire thinning counts every mask
  hit, while the backtest skips hits blocked by the per-bar cap: a small live/backtest gap, irrelevant for a FAIL.
- Rule-change context: the 2-year halves are scored with one fixed rule set (today's); no live rule change falls
  inside them.

## What we learn (for the next round, optimistic read)
- The directional factors that looked persistent in WAVE1 flip sign between spring 2025 and summer 2025 on a 45-min
  after-cost target, especially the SPY tape terms (follow in A, fade in B). A linear score with a sign filter cannot
  carry them; a regime-conditioned term (tape follow vs fade by a point-in-time regime state) is the targeted next idea.
- With the directional terms gone, "volatile, cheap names" alone beats same-name random entries by +0.01..+0.05R, but
  is still negative after costs: the base still loses. Consistent with round 1 (triggers beat random, bases lose).

## Files
- research/ultimate_1119/modules/ULT-19.py (live interface; record only, not deployed) +
  research/ultimate_1119/modules/ULT-19_model.json (frozen 19b coefficients, scaler, tau, universe).
- research/ultimate_1119/round2/ULT-19/bt.py, test_module.py (3 tests pass: long, short, live/backtest parity on real
  frames), fit_grid.json (incl. every fold model), fitsel.json, check_once.json (incl. daily R), check_plateau.json.
  test_module.py's parity test was corrected after the freeze (its own filter wrongly applied ETB to longs); bt.py,
  the module and the model json are unchanged since the freeze (sha256 in fitsel.json).

Educational only — not financial advice.
