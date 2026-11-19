Educational only — not financial advice

# ULT-15 CONFLUENCE — 2+ round-1 triggers on a base that must be >= 0 by itself, LONG + SHORT (round 2)

**Tier: FAIL (by the pre-registered base gate). Not BEATS, not TIER A, not TIER B.** The gate scores the bases before
any trigger is scored: one random base bar per symbol-session. All 4 bases (long / short x L1 / L2) lost money in
**both** fit sub-halves, with both exits: -0.009 to -0.039R per trade (R = 2u = 0.5 daily ATR). PLAN sec. 3 says "if
both fail, the config scores nothing", so **no configuration may trade, there is no fit pick, and nothing was scored on
CHECK as the candidate.** The frozen module has `SIDES_ON = ()` and never fires.

As a counted diagnostic, I froze the same selection rule with the gate ignored, before any check data was built. That
diagnostic pick (15c) is **-0.015R on fit and +0.001R on check** (t 0.09). It cannot change the tier, and it shows nothing
worth salvaging as a book.

## In plain words
- The round-1 lesson was that a good trigger on a losing base only shrinks the loss. So this candidate first asks one
  question: does the base make money with random entries? Only if it does do we stack triggers on it.
- **None of the four bases makes money with random entries, and the problem is not only costs.** Long names with daily
  ATR >= 3%, bought after 10:30 while SPY is up and rising, lose **before costs** too: -0.015R gross on fit, -0.035R gross
  on check. Gap-down names shorted after 11:00 while SPY is down and falling are about flat before costs on fit
  (+0.003 / -0.004) and lose -0.018 gross on check. Costs then add another 0.012-0.023R per trade.
- **The triggers do add value once again.** On the ungated diagnostic, signal minus random was +0.056R on fit and +0.053R
  on check (long +0.027 / +0.024, short +0.113 / +0.132). Three rounds of evidence now agree on this. But +0.05 on top of
  a -0.05 base comes out at zero.
- Confluence did not help. 2-of-3 gave the volume (4-17/session ungated) at about zero R. 3-of-3 almost never fires
  (0.2-0.6/session), because the three long triggers measure the same "oversold" event.

## Build (faithful to round2/PLAN.md sec. 3 "ULT-15"; no amendment to the rules)
- Module `research/ultimate_1119/modules/ULT-15.py` (live LabStrategy interface, two sides in one file as ULT-05/14: a
  setup name ending "-S"/"-short" is the short side; GEOM "S" = 2u catastrophic stop, YAML time_stop_min 30/45). bt.py
  imports the module's own `features()` / `base()`, so backtest and live use the same code.
- Intake U2: price >= $10, |gap| < 20%, atr_d > 0, cost_r cap; ADV20 point-in-time. L1 = ADV >= $200M long / $100M
  short with cost_r <= 0.05; L2 = ADV >= $50M with cost_r <= 0.08.
- Base BL: atr_d% >= 3.0, 10:30-15:00, spy_fo >= 0 and spy_r30 >= 0 (the universal long filter is kept but cannot bind).
  Base BS: ETB (universe.csv flag, today's), gap <= -1.0%, 11:00-15:00, spy_fo <= 0 and spy_r30 <= 0, RSI5 >= 25
  (universal). spy_r30 = SPY change over exactly 6 five-minute bars; unknown -> no signal.
- Triggers as specified: TL1 RSI14 cross below 50 within 3 bars and RSI14 <= 30; TL2 RSI5 up-cross 30 (this or previous
  bar) with buyPressure > 0; TL3 from_open_atr <= -1 or dist_hod_atr >= 1.5; TS1 RSI5 in [60, 90), dist_lod_atr >= 0.5,
  |sma20_dist| >= 1.5%; TS2 RSI5[prev] >= 80, RSI5 falling (the RSI5 slope, as ULT-08 read "rsiSlope < 0"), and
  upper_wick > 0; TS3 from_open_atr >= +1. Each trigger counts if it is true on the decision bar or one of the 2 bars
  before it, at exact 5-min spacing in the same session.
- Chassis (round 2): entry at the next 1-minute bar's OPEN; LR8 costs; **1.2 bp borrow fee on every short**; TX-n with a
  2u catastrophic stop, R per 2u (`avg_r_u025` = x2); one lot per symbol across both sides; refire >= 30 min after the
  exit; max 2 per symbol-session; day cap 30; flat 15:50. Forbidden columns (win_*, r_*, *heat*) are dropped and
  asserted absent. The locked block is excluded by pyarrow filters plus no_locked() asserts; MCF_HIST_ALLOW_LOCKED is
  refused.
- Base random bars: numpy default_rng seeded from (1119, month, side, liquidity). One bar per base-eligible
  symbol-session, drawn from that session's base-eligible bars and walked through the same chassis exit.

## 1. Base gate (FIT only, frozen 2026-11-19T07:04:44Z before any trigger was scored) — base_gate.json

| Base | random bars | TX30 A / B (all) | TX45 A / B (all) | ex 04-03..04-09 (TX45) | gross before costs (TX45) | Gate |
|---|---|---|---|---|---|---|
| Long L1 (ADV $200M, cost_r <= 0.05) | 11,472 | -0.020 / -0.029 (-0.023) | -0.023 / -0.039 (-0.028) | -0.033 | -0.016 | **fail** |
| Long L2 (ADV $50M, cost_r <= 0.08) | 31,951 | -0.027 / -0.026 (-0.027) | -0.034 / -0.028 (-0.032) | -0.032 | -0.015 | **fail** |
| Short L1 (ADV $100M, cost_r <= 0.05) | 3,023 | -0.030 / -0.010 (-0.025) | -0.016 / -0.009 (-0.015) | -0.016 | +0.003 | **fail** |
| Short L2 (ADV $50M, cost_r <= 0.08) | 6,685 | -0.032 / -0.022 (-0.029) | -0.025 / -0.030 (-0.027) | -0.032 | -0.004 | **fail** |

R per 2u. Sub-half A = 2024-10 + 2025-03..05, B = 2025-06..09. All 16 sub-half cells are below 0, so the gate result
does not hinge on a borderline cell. The bases are no better on CHECK (reported after the fact, not used): long -0.040
(TX30) / -0.050 (TX45), short -0.033 to -0.039; gross before costs, long -0.034..-0.039 and short -0.018.

## 2. FIT grid (8 configs) — fit_grid.json
**Gated (the pre-registered result): every config has 0 sides open and 0 trades. No pick.**

Ungated diagnostic (the same configs with the base gate ignored; the counted diagnostic only, never a candidate):

| Config | /session | avg R | avg R w/o best day | total R | total R w/o best day | A / B | ex 04-03..04-09 | long n, avg R | short n, avg R |
|---|---|---|---|---|---|---|---|---|---|
| 15a C2-TX30-L1 | 4.00 | -0.034 | -0.041 | -23.3 | -27.5 | -0.081 / +0.026 | -0.015 | 451, -0.026 | 229, -0.051 |
| 15b C2-TX30-L2 | 9.52 | -0.022 | -0.028 | -35.8 | -44.9 | -0.040 / -0.001 | -0.004 | 1217, -0.030 | 402, +0.002 |
| **15c C2-TX45-L1** (diag pick) | 3.96 | -0.015 | -0.030 | -10.3 | -20.1 | -0.068 / +0.053 | +0.002 | 448, -0.017 | 225, -0.011 |
| 15d C2-TX45-L2 | 9.45 | -0.017 | -0.024 | -28.0 | -37.9 | -0.036 / +0.005 | -0.003 | 1210, -0.032 | 397, +0.026 |
| 15e C3-TX30-L1 | 0.20 | -0.112 | -0.151 | -3.8 | -4.8 | -0.155 / +0.030 | -0.051 | 2 | 32, -0.122 |
| 15f C3-TX30-L2 | 0.41 | +0.029 | +0.002 | +2.0 | +0.2 | +0.025 / +0.040 | +0.087 | 11 | 59, +0.039 |
| 15g C3-TX45-L1 | 0.20 | -0.076 | -0.110 | -2.6 | -3.6 | -0.092 / -0.026 | +0.001 | 2 | 32, -0.085 |
| 15h C3-TX45-L2 | 0.41 | +0.071 | +0.041 | +5.0 | +2.8 | +0.063 / +0.092 | +0.144 | 11, +0.125 | 59, +0.061 |

Every config with >= 2 trades/session is negative on fit. The only fit-positive configs (15f, 15h: 3-of-3, L2) trade
0.4/session (70 trades in 170 sessions), far below the 2.0 floor, and their check plateau is +0.010 / -0.034 (below).

## 3. CHECK
- **The candidate: not scored.** There is no fit pick (check_once.json records "not scored", tier FAIL).
- **Diagnostic only, scored once (check_diag_ungated.json): 15c, gate ignored.**

| | FIT (170 sessions) | CHECK (276 sessions) |
|---|---|---|
| trades (/session) | 673 (3.96) | 2,396 (8.68) |
| avg R per 2u (per 0.25 dATR) | -0.015 (-0.030) | +0.001 (+0.002) |
| avg R w/o best day; best-day share | -0.030; n/a (total < 0) | -0.001; 234% **1 day** (2026-08-03, +4.7R) |
| total R; R/session | -10.3; -0.060 | +2.0; +0.007 |
| worst day; worst day / trade-session | — | -6.7R (2025-11-07); -0.72 |
| day-clustered t | — | 0.09 (BEATS bar 3.65) |
| SPY up / flat / down avg R | — | +0.003 / -0.024 / +0.057 |
| first / second half | A -0.068 / B +0.053 | -0.019 / +0.015 |
| long: n, avg R | 448, -0.017 | 1,757, -0.013 (t -1.33) |
| short: n, avg R | 225, -0.011 | 639, +0.040 (w/o best day +0.034, t 1.64) |
| without 2025-04-03..04-09 | +0.002 | n/a (no such dates in check) |
| same-name random control | -0.071 (signal - random +0.056; L +0.027, S +0.113) | -0.052 (+0.053; L +0.024, S +0.132) |
| bias diagnostic: signal-close fill, no borrow | -0.015 | +0.002 |
| median hold; exits | 45 min | 45 min; 2,349 time / 47 stop |

The **short side on check** (+0.040, t 1.64, 2.3/session) is the one bright cell. But it was -0.011 on fit, its base
failed the gate, and it is a post-hoc slice of a diagnostic. It is **not** evidence for promotion. At most it is a
backlog note: "gap-down pop/roll-over shorts in liquid ETB names on a falling tape beat random by +0.11..0.13R in both
halves". The base under it still loses.

### Check plateau (all 8, ungated, after the single diagnostic score; never used to select) — check_plateau.json
15a +0.002 (8.7/s), 15b -0.004 (16.8/s), 15c +0.001 (8.7/s), 15d -0.007 (16.7/s), 15e -0.008 (0.3/s), 15f -0.034
(0.6/s), 15g +0.071 (0.3/s, 78 trades), 15h +0.010 (0.6/s). Every config is within about +-0.01 of zero at volume. 15g
is fit -0.076 (a sign flip on 78 trades). The gated plateau is empty everywhere.

## 4. Tier by the bars (PLAN sec. 6)
- TIER A needs check avg R > 0 etc. on the fit pick. **There is no fit pick** (the base gate closed both sides at both
  liquidity levels). -> **FAIL.** Even read on the ungated diagnostic, it would fail TIER A (fit avg R -0.015 <= 0;
  check avg R w/o best day -0.001 <= 0) and BEATS (+0.001 vs +0.0836; t 0.09 vs 3.65).
- No look-ahead: features are built from the decision bar and earlier bars of the same session (test_features_point_in_time);
  forbidden columns are dropped and asserted absent; selection was frozen (fitsel.json 2026-11-19T07:05:07Z) before
  any check frame was built (sig check asserts that fitsel.json exists).

## 5. Configurations counted
8 grid + 4 base-gate evaluations (side x liquidity; each read at both exits on the same random bars, as the per-config
gate needs) + 1 bias diagnostic + **1 added ungated diagnostic check score** = **14** for ULT-15 (PLAN budgeted 13).
That makes cumulative N 775 if the extra diagnostic is counted against the round-2 total of 774. The t bar is 3.651 at
775 vs 3.650 at 774, so nothing changes. If the base gate is counted as 8 exit-specific evaluations, N = 779 and the bar
is 3.652. Random controls are reported, not counted.

## 6. Biases (all favour the candidate; none could rescue it)
Today's symbol list (survivorship; flatters the long base, so the true long base is worse). The ETB flag is today's,
not point-in-time. The borrow fee is in (1.2 bp per short). The entry fix is in (next-minute open; the bias diagnostic
moves avg R by only +0.000..+0.002). TX exits pay the full exit cost.

## 7. What it teaches (for the next round; backlog ideas, untested)
- Simple point-in-time base filters (volatility + tape direction + time window, or gap direction + tape) do **not**
  produce a non-negative random-entry base intraday at a 30-45 min horizon. They are negative even before costs (long
  with an up-tape -0.015 gross fit, -0.035 check). A future D3 attempt needs a base defined by something other than
  tape and volatility. The next targeted test is probably cost geometry (D4) or a base found by a model.
- The triggers' relative edge is robust: +0.05R vs random on both halves, and +0.11..0.13R on the short side. The open
  problem is a base that does not lose that edge back.

## 8. Rule-change context (owner 2026-11-02)
Both 2-year halves are scored with one fixed rule set (today's). No live rule change falls inside them. ledger.jsonl
changes in the live window 2026-10-06..11-18 (LR8 cost model 11-12, Primary sizing 10-28, Testing cost filter 10-30,
TSZ1/SPYEXIT 11-17, moves) do not touch these figures.

## Files
`research/ultimate_1119/modules/ULT-15.py` (frozen: SIDES_ON = (), never fires);
`research/ultimate_1119/round2/ULT-15/`: bt.py, test_module.py (4 pass under the live LabStrategy), base_gate.json,
fit_grid.json (gated + ungated diagnostic), fitsel.json, fit_random_diag.json, check_once.json (not scored),
check_diag_ungated.json, check_base_random.json, check_plateau.json. Trade lists were in the scratchpad and are deleted.

Educational only — not financial advice.
