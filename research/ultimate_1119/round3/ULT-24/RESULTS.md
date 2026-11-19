Educational only — not financial advice

# ULT-24 CONFL-2 — gated triggers on gated cheap bases (LONG + SHORT) — round 3 — **FAIL (no candidate: every base closed at the FIT gate)**

CHECK-INFORMED (TS-1 / TS-2 / TL-B; round3/PLAN.md sec. 0.5). Research only: no setup, exit, config or account change.
Nothing committed.

## Verdict in one paragraph
The pre-registered rule was "first prove the base". None of the three bases did: one random base-eligible bar per
symbol-session lost money in **both** FIT sub-halves, under **both** exits, for equity-basket ETFs (BQ-L), mega-cap longs
(BM-L) and mega-cap shorts (BM-S). The trigger gate was therefore skipped, no grid config could trade, and the frozen fit
pick is "none" → **FAIL**, nothing scored on CHECK (the pre-registered result "if the gates close everything (as ULT-15),
the result is no candidate"). A **diagnostic** (base gate ignored, trigger gate kept, frozen before any check data,
counted) confirms the read: the triggers still beat random on these bases (+0.019R check, +0.025R fit), but the bases
lose more than that, so the trades lose (check −0.023R, t −2.67, 20/session). Not deployable; no BEATS / TIER A / TIER B.

## Build
- Module: `research/ultimate_1119/modules/ULT-24.py` (+ `ULT-24_symbols.json`, a copy of the frozen ULT-23 universe file:
  EQB 167 ETFs, FUNDS 229, STOCKS 1,021). Three setups in one file, base from the setup name (`ULT-24` → BQ-L,
  `ULT-24-M` → BM-L, `ULT-24-S` → BM-S); runs under the live LabStrategy (context spy_fo); GEOM t05s1 or "S" (2u stop).
  As frozen it never fires (BASE_OPEN all False, SURVIVE empty). W / CONF / EXIT hold the diagnostic pick 24b for the record.
- Smoke test: `research/ultimate_1119/round3/ULT-24/test_module.py` — 4 passed (frozen never fires; an opened copy fires
  a short confluence under LabStrategy with the 2u stop; no SPY context / SPY up > 0.20% since 09:50 / cost_r > 0.05 →
  no signal; features, triggers, bases and mask point-in-time under truncation; fund never MEGA, stock never EQB; SPY
  60-min reference).
- Backtest: `research/ultimate_1119/round3/ULT-24/bt.py` (the round-2/3 chassis from ULT-15 / ULT-23: entry at the next
  1-min open, LR8 costs, +2c stops, borrow 1.2 bp on every short, ETB-only shorts, one lot per symbol across sides,
  refire >= 30 min after exit, max 2 per symbol-session, day cap 30, flat 15:50; 1-min walk, stop first, gap-through).
- Faithfulness notes (all point-in-time, none favour the candidate):
  - ret3 / ret12 / di_diff7 come from `mcf.research.arena.indicators.compute` (as WB4), whose panel starts at the 09:50
    bar, so ret12 (the BQ-L falling-hour guard and TL-A) is NaN before 10:50 → BQ-L effectively trades 10:50–15:00.
  - SPY 60-min change: reference = spy_fo exactly 60 min earlier; when that bar is not in the frame, the open
    (t−60 ≤ 09:30) or the 09:50 bar (10:35–10:45 then use a 45–55-min change). Live frames have the earlier bars.
  - RSI2 = Wilder RSI(2) (alpha 0.5) of the session's 5-min closes from the 09:50 bar (as ULT-20 L5/S4).
  - TL-D uses the frame's `lower_wick` share, `volumeRatio` (bar volume / 20-bar mean) and (close − low)/(high − low).
  - "within W bars" = the decision bar or one of the previous W bars (exact 5-min spacing, same session).
  - Trigger gate = trigger true on the bar, through the chassis chain (no day cap), TX-45, minus the same base's random
    avg R (TX-45), per sub-half.
- Forbidden columns (win_*, r_long*, r_short*, *heat*) dropped and asserted absent; no_locked() asserted on every frame,
  trade list and 1-min load; LOCKED block never read.

## Step 1 — base gate (FIT only, before any trigger was scored) — `base_gate.json`
One random base-eligible bar per base-eligible symbol-session (seed 1119 per month and base). Pass = random avg R >= 0 in
BOTH sub-halves A (2024-10 + 2025-03..05) and B (2025-06..09).

| Base | exit | n | FIT avg R | A | B | gross before costs | w/o 04-03..04-09 | pass |
|---|---|---|---|---|---|---|---|---|
| BQ-L (EQB long) | TX-45 | 3,324 | −0.0097 | −0.0116 | −0.0037 | +0.0079 | −0.0119 | no |
| BQ-L | t05s1 cap45 | 3,324 | −0.0301 | −0.0350 | −0.0148 | +0.0007 | −0.0271 | no |
| BM-L (mega long) | TX-45 | 3,990 | −0.0254 | −0.0229 | −0.0284 | −0.0125 | −0.0204 | no |
| BM-L | t05s1 cap45 | 3,990 | −0.0379 | −0.0298 | −0.0480 | −0.0154 | −0.0354 | no |
| BM-S (mega short) | TX-45 | 2,314 | −0.0372 | −0.0472 | −0.0249 | −0.0184 | −0.0365 | no |
| BM-S | t05s1 cap45 | 2,314 | −0.0694 | −0.0793 | −0.0571 | −0.0351 | −0.0722 | no |

The equity-basket ETF base is the only one positive **before** costs (+0.008R TX-45), i.e. costs (~0.018R per 2u) turn
it negative; the mega-cap bases lose before costs too (mega longs on today's survivor list still −0.013 gross). Same read
on CHECK (reporting only, `check_gates_diag.json`): BQ-L −0.028, BM-L −0.017, BM-S −0.039 (TX-45).

## Step 2 — trigger gate and FIT grid — `trigger_gate.json`, `fit_grid.json`, `fitsel.json`
All bases closed under both exits → trigger gate skipped for every base, survivors = none, all 8 configs 24a..24h
0 trades. Fit pick = **none** (frozen 2026-11-19T08:07Z, before any check data was built). Eligible (>= 2/session): none.

## Step 3 — CHECK (scored once) — `check_once.json`
Nothing to score: 0 trades, tier **FAIL**.

## Diagnostic (cannot set the tier; counted +1) — base gate ignored, trigger gate kept
Added after the base gate closed everything and BEFORE any check data was built (frozen in fitsel.json at
2026-11-19T08:09Z; bt.py got a numpy dtype fix between the main freeze and the diagnostic freeze — no gate number changed;
both hashes are in fitsel.json).

Trigger gate with every base forced open (FIT, `trigger_gate_diag_ungated.json`; signal − same-base random, TX-45):

| Base | trigger | n | A − rnd | B − rnd | survives | CHECK − rnd (reporting) |
|---|---|---|---|---|---|---|
| BQ-L | TL-A dip | 335 | +0.152 | −0.151 | no | −0.030 |
| BQ-L | TL-B collapse | 160 | −0.029 | +0.056 | no | +0.054 |
| BQ-L | TL-C RSI2 <= 5 | 3,482 | −0.027 | +0.004 | no | +0.021 |
| BQ-L | TL-D capitulation | 1,196 | +0.011 | −0.015 | no | −0.003 |
| BM-L | TL-A | 253 | +0.048 | +0.084 | yes | +0.026 |
| BM-L | TL-B | 274 | −0.009 | +0.054 | no | +0.015 |
| BM-L | TL-C | 4,014 | +0.020 | +0.013 | yes | +0.001 |
| BM-L | TL-D | 545 | +0.048 | +0.007 | yes | −0.004 |
| BM-S | TS-1 pop | 113 | +0.037 | +0.058 | yes | +0.031 |
| BM-S | TS-2 roll-over | 2,158 | +0.048 | +0.000 | yes | +0.023 |
| BM-S | TS-3 +1 dATR | 49 | −0.076 | +0.064 | no | +0.035 |
| BM-S | TS-4 RSI2 >= 95 | 1,238 | +0.056 | +0.029 | yes | +0.028 |

Ungated FIT grid (`fit_grid_diag_ungated.json`; BQ-L has no survivor pair, so only BM-L / BM-S trade):

| cfg | label | FIT /session | FIT avg R | w/o best day | A | B | CHECK /session | CHECK avg R | CHECK w/o best | CHECK t |
|---|---|---|---|---|---|---|---|---|---|---|
| 24a | W3-C2-t05s1 | 10.92 | −0.0219 | −0.0265 | −0.034 | −0.013 | 20.26 | −0.0386 | −0.0406 | −3.16 |
| **24b** | **W3-C2-TX45 (diag pick)** | 10.86 | −0.0066 | −0.0092 | −0.006 | −0.007 | 20.17 | **−0.0228** | −0.0255 | −2.67 |
| 24c | W3-C3-t05s1 | 0.49 | +0.0958 | +0.0814 | −0.012 | +0.150 | 1.76 | −0.0691 | −0.0738 | −2.03 |
| 24d | W3-C3-TX45 | 0.49 | +0.0412 | +0.0220 | −0.007 | +0.066 | 1.72 | −0.0082 | −0.0152 | −0.33 |
| 24e | W6-C2-t05s1 | 13.29 | −0.0300 | −0.0355 | −0.050 | −0.014 | 22.61 | −0.0392 | −0.0415 | −3.29 |
| 24f | W6-C2-TX45 | 13.12 | −0.0152 | −0.0178 | −0.019 | −0.013 | 22.49 | −0.0216 | −0.0235 | −2.54 |
| 24g | W6-C3-t05s1 | 0.87 | −0.0435 | −0.0547 | −0.240 | +0.128 | 2.94 | −0.0612 | −0.0654 | −2.07 |
| 24h | W6-C3-TX45 | 0.83 | −0.0047 | −0.0232 | −0.097 | +0.072 | 2.83 | −0.0142 | −0.0184 | −0.70 |

(CHECK columns of the grid are a plateau diagnostic computed after the diagnostic pick's single check score; never used to
select.) The only FIT-positive cells (24c/24d, C3, BM-S only, < 0.5/session) are both negative on CHECK.

Diagnostic pick 24b in full:
- FIT: 1,846 trades, 10.86/session, win 0.48, avg R −0.0066 (−0.013 per 0.25-dATR unit), w/o best day −0.0092,
  total −12.1R, worst day −9.05R (−0.80 per trade-session), t −0.62; w/o 2025-04-03..04-09 −0.0077; A −0.006 / B −0.007;
  long (BM-L) 1.47/session −0.0127, short (BM-S) 9.39/session −0.0056; SPY up −0.026 / flat −0.027 / down +0.024;
  median hold 45 min, exits 1,833 time / 13 stop. Same-name random −0.0314 → signal − random **+0.025** (long +0.050,
  short +0.021). Bias diagnostic (signal-close fill, no borrow): −0.002.
- CHECK (scored once): 5,568 trades, 20.17/session, win 0.481, avg R **−0.0228** (−0.0455 per unit), w/o best day
  −0.0255 (best day 2026-10-08 +14.6R; total negative, so no best-day share), total −126.8R (−0.46R/session), worst day
  −11.53R (−0.57 per trade-session), day-clustered **t −2.67** (bar 3.68); first/second half −0.041 / −0.009; long
  2.57/session −0.0317, short 17.6/session −0.0215; SPY up −0.094 / flat −0.014 / down +0.012; exits 5,488 time / 80
  stop. Same-name random −0.0423 → signal − random **+0.019** (long +0.049, short +0.015). Bias diagnostic −0.0185.
  CHECK has no 2025-04-03..04-09 dates (avg R w/o them = −0.0228).

## Bars
| bar | value | needed | met |
|---|---|---|---|
| fit pick exists / trades | none (all bases closed) | >= 2/session | no |
| check avg R | — (0 trades) | > 0 (A), > +0.0836 (BEATS) | no |
| check avg R w/o best day | — | > 0 / > +0.0734 | no |
| day-clustered t | — | >= max(1.5, sqrt(2 ln 881)) = 3.68 | no |
**Tier: FAIL.** (Diagnostic 24b would also be FAIL: fit −0.0066, check −0.0228.)

## Configurations counted
23 pre-registered for ULT-24 (8 grid + 3 base gates + 12 trigger gates — the 12 were run as the diagnostic trigger gate,
since the real one was skipped) + 1 diagnostic check score = **24**. Bias diagnostic: reported on the diagnostic pick
(the PLAN's 8 bias diagnostics are already counted at round level). **Cumulative N for the job: 880 + 1 = 881**
(t floor sqrt(2 ln 881) = 3.68, unchanged).

## What this teaches (for the next round)
1. **The base is the problem, not the triggers.** On mega caps and equity-basket ETFs, as on round 2's stock bases,
   triggers add +0.015..+0.05R over same-name random in both halves, but random entries on the base lose −0.01..−0.04R
   after costs, and the mega-cap bases lose before costs as well. Stacking triggers (C2/C3) does not add enough to cross
   zero; C3 cells are too thin (< 1/session on fit) and flip sign on check.
2. **Equity-basket ETFs are the only base that is gross-positive (+0.008R TX-45 fit)**; costs of ~0.018R per 2u make it
   negative. None of the four long triggers kept a positive edge over random in both halves on that base; the one
   out-of-sample basket edge (WB4 dip, fixed % thresholds, ATR >= 3.6%) did not show up in the ATR-scaled TL-A at ATR >= 2%
   (A +0.15 / B −0.15).
3. **Mega-cap shorts under a flat/down tape are the volume engine (9–18/session) but carry −0.02R after borrow**; the
   short triggers' relative edge (+0.02..+0.03) is real and stable across fit and check but smaller than the base's loss.
   A remedy would have to fix the base (where random mega shorts lose −0.018 gross), not add triggers.

Rule-change context (owner 2026-11-02): both halves scored with one fixed rule set (today's LR8 costs, round-3 chassis,
1.2 bp borrow); no live ledger change falls inside them. Known biases still favouring the candidate: today's symbol list
(survivorship; flatters longs), today's ETB flag, the borrow fee is a flat estimate.

Files (all under `research/ultimate_1119/round3/ULT-24/`): bt.py, test_module.py, base_gate.json, trigger_gate.json,
fit_grid.json, fitsel.json, check_once.json, trigger_gate_diag_ungated.json, fit_grid_diag_ungated.json,
fit_random_diag.json, check_diag_ungated.json, check_plateau.json, check_gates_diag.json. Module:
`research/ultimate_1119/modules/ULT-24.py` + `ULT-24_symbols.json`. Trade lists were kept in the scratchpad only and deleted.

Educational only — not financial advice.
