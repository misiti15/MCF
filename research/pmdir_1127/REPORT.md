# PMDIR-1127 — can SPY's afternoon direction be called at 12:00? — REPORT

**Educational only — not financial advice.** Research only; no change to config/, setups, exits, assignments, decisions
or the ledger. Pre-registered in `PREREG.md` (commit a48a3fa500, before any scoring). Locked block 2024-11-01..2025-02-28
dropped at load and asserted absent (pm_build.py, pm_score.py).

## Plain summary
**FAIL. At 12:00 we cannot tell which way SPY goes into the close, out of sample, beyond its long-run upward drift.**
- Six frozen models fit on FIT (logistic on 12 features, logistic on the morning return, depth-2 tree, stump, a W60-proxy
  compass rule, always-long), scored once on CHECK (2025-10..2026-11-04, 276 days), T2 (2023-01..2024-09, 437 days) and
  EARLY (2016-2022, 1,734 days).
- **Hit rates:** best trained model (tree / stump, both just "prior day up > 1% -> short, else long") 46.4% CHECK, 53.8% T2,
  53.6% EARLY; pooled 52.8%, z 2.77, but **every split is at or below the "always long" base rate** (50.4 / 55.2 / 54.1%).
  The full logistic was *worse than a coin* on CHECK (44.2%, AUC 0.416) and T2 (47.1%, AUC 0.457): what it learned on 149 FIT
  days reversed later. AUCs on CHECK were 0.41-0.49 for every trained model.
- **The SPY trade loses in every split after costs:** -0.12 to -0.31R per trade at LIVE-L (t -3.5 to -7.8), and still
  negative at LR8 (-0.02 to -0.20R) on CHECK and T2. Gross edge is 0 to +4 bp per trade; LIVE-L charges ~8 bp at a 50 bp stop.
- **The 53-55% LEAD bar was not met honestly:** the only pooled hit rates >= 53% (always-long 53.9%, morning-return logistic
  53.7%, which is also nearly always long) are the market's upward drift in 2016-2024, not a prediction; CHECK shows none
  (50.4% up afternoons) and the morning-return model's CHECK AUC is 0.485.
- **Secondary view (fit on 7 years of EARLY instead):** no better; the logistic hits 52.0% T2 / 48.9% CHECK, trees collapse
  to "always long".
- **What changed over time:** the morning's direction used to continue into the afternoon (2016-2022: big mornings
  |ret| > 0.5% followed through 57.9% of the time, n 470) but not since 2023 (T2 50.0%, n 94; CHECK 49.3%, n 71). That
  decay is consistent with COMPASS-5M ("heading is a coin flip") and the WILDCARD intraday-momentum failure.
- **One post-hoc crumb (not a pass, exploratory):** the QQQ-minus-IWM morning spread was the one feature with AUC > 0.5 in
  EARLY / T2 / CHECK (0.545 / 0.559 / 0.545), but it pointed the other way in FIT (0.408), so the FIT-fit models used the
  wrong sign. Traded as a plain sign rule it is +1 to +5 bp gross and -0.09 to -0.18R after LIVE-L in every split. Too small to
  matter for gating; it would need its own pre-registration and forward data.

**Bottom line for live setups:** an afternoon-SPY-direction gate built from noon information is not supported. Index-like
setups whose records ride the afternoon (G05/G07/G37, ARENASTARS-1127) are taking a near-coin-flip bet each day; treat their
big afternoon days as luck until a forward record says otherwise.

## Configurations
8 primary (M1-M6, M1c, M3c) + 4 secondary (EARLY-fit M1-M4) + 2 exploratory sign rules (qi, gap; post-hoc, not a pass
route) = **14**. Cumulative program N ~9,176 -> **~9,190**. Bars from PREREG: trade PASS needs positive LIVE-L R in CHECK, T2
and EARLY and pooled t >= 2.04; LEAD needs pooled hit >= 53% with z >= 2.04 and hit > 50% and AUC > 0.5 in every OOS split.

## Every finalist (fit FIT, frozen; LIVE-L R/trade with t; LR8 alongside; hit; AUC)

| Model | CHECK n / hit / AUC / LIVE-L (t) / LR8 | T2 n / hit / AUC / LIVE-L (t) / LR8 | EARLY n / hit / AUC / LIVE-L (t) / LR8 | Pooled OOS hit (z), LIVE-L t, rand pct |
|---|---|---|---|---|
| M1 logistic all | 276 / 44.2% / 0.416 / -0.312 (-7.8) / -0.201 | 437 / 47.1% / 0.457 / -0.234 (-6.1) / -0.128 | 1734 / 53.3% / 0.509 / -0.143 (-6.3) / -0.043 | 51.2% (1.19), -9.9, 21 |
| M2 logistic mret | 276 / 50.4% / 0.485 / -0.222 (-5.0) / -0.104 | 437 / 55.2% / 0.505 / -0.135 (-3.6) / -0.022 | 1734 / 53.9% / 0.535 / -0.158 (-7.4) / -0.051 | 53.7% (3.66), -9.3, 59 |
| M3 tree d2 | 276 / 46.4% / 0.410 / -0.264 (-6.0) / -0.152 | 437 / 53.8% / 0.510 / -0.150 (-3.9) / -0.044 | 1734 / 53.6% / 0.529 / -0.125 (-5.3) / -0.024 | 52.8% (2.77), -7.7, 90 |
| M4 stump | 276 / 46.4% / 0.462 / -0.264 (-6.0) / -0.152 | 437 / 53.8% / 0.516 / -0.150 (-3.9) / -0.044 | 1734 / 53.6% / 0.516 / -0.125 (-5.3) / -0.024 | 52.8% (2.77), -7.7, 90 |
| M5 W60-proxy | 140 / 47.1% / - / -0.247 (-3.9) / -0.140 | 242 / 50.0% / - / -0.182 (-3.5) / -0.080 | 994 / 53.9% / - / -0.132 (-4.5) / -0.035 | 52.5% (1.89), -6.4, 76 |
| M6 always long (control) | 276 / 50.4% / - / -0.222 (-5.0) / -0.104 | 437 / 55.2% / - / -0.135 (-3.6) / -0.022 | 1734 / 54.1% / - / -0.152 (-7.0) / -0.045 | 53.9% (3.82), -8.9, 67 |
| M1c (|p-.5| >= .05) | 206 / 43.7% / 0.416 / -0.314 (-6.6) / -0.202 | 344 / 48.0% / 0.457 / -0.205 (-4.6) / -0.098 | 1354 / 52.7% / 0.509 / -0.155 (-6.1) / -0.053 | 50.8% (0.73), -8.8, 21 |
| M3c (|p-.5| >= .05) | = M3 (all leaves confident) | = M3 | = M3 | 52.8% (2.77), -7.7, 91 |

FIT (in-sample) for reference: hits 57-66%, LIVE-L -0.03 to -0.14R. Secondary EARLY-fit view (T2 / CHECK hit, LIVE-L):
M1 52.0% / 48.9%, -0.183 / -0.244; M2 55.6% / 50.4%, -0.138 / -0.221; M3 and M4 = always long 55.2% / 50.4%, -0.135 / -0.222.

Stress (LIVE-L): +1 min entry moves R by -0.02..+0.02, +2 bp makes every cell 0.04R worse; nothing is positive under any cost model (or gross) on CHECK.
One trade per day, so day-clustered t = per-trade t; best-day share is undefined (every split's total is negative); avg R
w/o best day is -0.13 to -0.32 in every OOS cell (results.json). Random-direction control: no model reaches the 95th pct on
pooled OOS (best 90-91, the tree, whose "edge" is being long most days in up-drifting EARLY/T2).

Learned FIT models: logistic largest weights lmom -0.45, breadth +0.42, Thursday +0.45, Wednesday -0.34, mret -0.22, vwap
+0.22 (signs that mostly reverse out of sample); tree = prev-day return > ~1% -> down afternoon, else up.

## Per-feature AUC by split (diagnostic, pm_diag.py; 12 features x 4 splits looked at)
| feature | EARLY | T2 | FIT | CHECK |
|---|---|---|---|---|
| mret | 0.535 | 0.505 | 0.538 | 0.485 |
| breadth (sector) | 0.528 | 0.468 | 0.579 | 0.431 |
| vwap | 0.532 | 0.498 | 0.510 | 0.469 |
| qi (QQQ-IWM) | 0.545 | 0.559 | 0.408 | 0.545 |
| gap | 0.519 | 0.539 | 0.510 | 0.579 |
| rv20 | 0.499 | 0.527 | 0.514 | 0.540 |
| prev | 0.483 | 0.498 | 0.410 | 0.505 |
| others (mrange, rvm, lmom, w60, dow) | 0.49-0.53 | 0.49-0.50 | 0.50-0.55 | 0.46-0.50 |

Momentum-type features (mret, vwap, breadth, w60) were mildly predictive in 2016-2022 and FIT, then flat or reversed in T2
and CHECK. gap is > 0.5 everywhere, but as a sign rule its hit rate sits below the always-long base rate in 3 of 4 splits.

## Method notes and caveats
- Trade: SPY market entry at the 12:00 bar open, 0.50% stop (stop-first, gap fill at the open), exit at the 15:55 bar open
  (half days: last bar - 4 min). LIVE-L ($100+ bucket, a / 50 bp + b, ~0.166R) is far above SPY's real spread; LR8 is the
  kinder view and still negative on CHECK/T2. Even gross, no model exceeds +0.04R on CHECK (all negative) or ~+5 bp anywhere.
- Breadth is sector-ETF breadth (share of 11 SPDR sectors above their open), used on all splits because the stock-universe
  breadth has no EARLY history; W60 is a proxy built on it (not the live 200-name compass).
- Early March 2025 is excluded from FIT (prior-day / 20-day features would cross the locked gap); 42 days dropped in total
  for missing features. 149 FIT days is a small fit set; the secondary EARLY fit shows more data does not rescue it.
- Rule changes: market-only study (no setup R), so no research/ledger.jsonl effective date bears on these numbers.

## What next (optimism, honestly scoped)
- Nothing to gate or promote. The useful product is negative knowledge: afternoon direction is ~unpredictable at noon since
  2023, so setups should not be judged on afternoons that happened to trend.
- If anyone pursues it: a forward shadow of the QQQ-IWM spread sign (logged only, no trading), pre-registered as a new
  lineage with the post-hoc selection disclosed. Not added to the backlog from this FAIL study.

Files: `PREREG.md`, `pm_build.py` (features/sims; days table kept in scratch, not committed), `pm_score.py` -> `results.json`,
`pm_diag.py` + `pm_expl.py` -> `diag_out.txt`.
