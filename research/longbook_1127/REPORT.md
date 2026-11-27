Educational only — not financial advice

# LONGBOOK-1127: does adding ONE live long setup to Primary diversify its short book? **FAIL (0 of 8 configs)**

## In plain words
Primary loses mostly on up days. In the 2-year bench it makes −7.7R/day on CHECK up days and +1.0R/day on down days.
We tried adding each of four live long setups to Primary, one at a time, under Primary's live rules and with fair
(LIVE-L) costs. As hoped, each long moves against the short book: the correlation with the short book's daily R is
between −0.07 and −0.30. Each long also adds R on up days, by up to +1.4R/day.

**None of them pays for itself, though.** Before costs every long is about break-even on CHECK and T2. After LIVE-L
costs every one loses money, so adding any of them lowers Primary's R/day on both out-of-sample splits, in all 8
configs (−0.06 to −4.07R/day). It also adds red days. The up-day gain is far too small to offset Primary's up-day
losses, and it is given back on down and quiet days.

**There is nothing to promote and no backlog entry.** The live records look better (GEN-261023-07 +0.46R, GEN-261027-10
+0.15R per trade), but they come from 1–2 big days: 11-25 carries 142% and 224% of their totals.

Pre-registered in PREREG.md (sha256 in PREREG.sha256), committed in cb1474bfea before anything was scored. **Configs: 8.
Cumulative N ≈ 9,300 → ≈ 9,308.** The global bar is sqrt(2 ln N) ≈ 4.28; the study bar is paired t ≥ 2.5.

The engine is E4, the cfprimary_1127 numba book extended from 4 to 5 setup slots. Its parity with the 4-slot engine on
REF is exact (max day diff 0.000R). REF reproduces earlier studies: CHECK −3.04R/day (cfprimary −3.03) and T2 −1.76
(−1.75).

Costs: LIVE-L on the shorts and the candidate longs, LR8 alongside, and NM-ETF on LR8 as in every E4 study. The locked
block 2024-11-01..2025-02-28 was filtered at load and asserted absent in every script.

Sessions: CHECK 276 (98 up / 84 down / 94 quiet by SPY open→close ±0.25%), T2 425 (165 / 114 / 146), FIT 170
(descriptive). EARLY (pre-2023) is not available for these stock setups.

## Failures first: Primary book + one long (BASE rules, R/day vs REF; LIVE-L)
Bars: 1 dR > 0 · 2 t ≥ 2.5 · 3 above the random-add p95 · 4 worst-5 not > 5% worse · 5 red days not up · 6 best-day
share < 25% and dR w/o best day > 0 · 7 stress > 0 · 8 no P4 setup < −2R/month.

| Config | CHECK dR (t) | T2 dR (t) | LR8 dR CHECK / T2 | Stress CHECK / T2 | Corr w/ shorts CHECK / T2 | Worst-5 CHECK REF→cfg | Red/mo CHECK REF→cfg | dR up / down / quiet (CHECK) | Bars failed (CHECK; T2) |
|---|---|---|---|---|---|---|---|---|---|
| L1 CWT14-WB5 C30 | −4.07 (−10.2) | −1.41 (−8.3) | +0.33 / −0.16 | −4.76 / −1.72 | −0.30 / −0.12 | −35.2→−33.7 | 13.1→15.6 | −0.75 / −7.77 / −4.23 | 1,2,5,6,7; 1–7 |
| L1 CWT14-WB5 C10 | −2.04 (−11.0) | −1.21 (−9.3) | +0.78 / −0.10 | −2.42 / −1.46 | −0.23 / −0.14 | −35.2→−35.3 | 13.1→14.7 | −0.75 / −3.62 / −1.97 | 1,2,5,6,7; 1,2,5,6,7 |
| L2 ULT-05 C30 | −0.65 (−3.7) | −0.13 (−2.7) | +1.22 / +0.30 | −0.87 / −0.19 | +0.05 / −0.03 | −35.2→−35.4 | 13.1→13.7 | −0.13 / −0.85 / −1.03 | 1,2,3,5,6,7; 1,2,5,6,7 |
| L2 ULT-05 C10 | −0.51 (−4.0) | −0.13 (−2.7) | +1.26 / +0.30 | −0.70 / −0.19 | +0.03 / −0.03 | −35.2→−35.4 | 13.1→13.5 | −0.05 / −0.71 / −0.82 | 1,2,5,6,7; 1,2,3,5,6,7 |
| L3 GEN-261027-10 C30 | −0.31 (−1.0) | −0.18 (−1.3) | +1.12 / +0.17 | −0.50 / −0.24 | −0.15 / −0.08 | −35.2→−35.1 | 13.1→13.5 | **+1.40** / −0.78 / −1.66 | 1,2,3,5,6,7; 1–7 |
| L3 GEN-261027-10 C10 | **−0.06 (−0.4)** | −0.11 (−1.3) | +1.29 / +0.23 | −0.14 / −0.16 | −0.15 / −0.14 | −35.2→−35.1 | 13.1→13.2 | +0.62 / −0.35 / −0.51 | 1,2,3,5,6,7; 1,2,3,5,6,7 |
| L4 GEN-261023-07 C30 | −0.72 (−1.8) | −0.51 (−1.7) | +0.73 / +0.05 | −1.25 / −0.92 | −0.07 / −0.17 | −35.2→**−33.1** | 13.1→13.6 | +0.45 / −0.72 / −1.95 | 1,2,3,5,6,7; 1–7 |
| L4 GEN-261023-07 C10 | −0.25 (−1.3) | −0.33 (−1.9) | +1.11 / +0.13 | −0.49 / −0.60 | −0.09 / −0.19 | −35.2→**−33.3** | 13.1→13.4 | +0.55 / −0.47 / −0.88 | 1,2,3,5,6,7; 1,2,3,5,6,7 |

- **Verdict: FAIL for all 8.** No config meets bar 1 (dR > 0) on CHECK or on T2 under LIVE-L, so the LEAD rule is not
  met either. T2 worst-5 for every C30 config is equally bad or worse (−24.4 → −26.4 / −28.3 / −30.2 for L1 / L3 / L4).
  Bar 8 holds everywhere: the long does not crowd out the shorts. Each P4 setup's R changes by between −1.7 and
  +2.5R/month, and the largest move is L3-fromopen −1.7 in L1 C30, because the 77-slot cap binds.
- FIT (descriptive): GEN longs +0.18 / +0.34R/day (C30, best-day share 215–348%), CWT14 −2.8, ULT-05 −0.6.
- **Costs decide the sign.** Under LR8, 6 of 8 configs are positive on CHECK (+0.33 to +1.29R/day) and 5 of 8 on T2
  (+0.05 to +0.30). Under LIVE-L every config is negative, with day t from −0.4 to −11.0.
  - Live booked R for these setups matches LR8 to within 0.005R. That is expected: "booked" uses the same fill basis and
    does not settle which cost model is right.
  - LIVE-L was fitted on 32k live fills (fill vs the decision-bar close) and validated closer to live than LR8
    (primshorts_1126). It stays the main basis, as pre-registered.
  - **Main open risk:** the LIVE-L long side has not been checked separately. A spread-aware cost model for longs (the
    open STOPFLOOR / SPREADFLOOR item) could flip the LR8-positive GEN configs to marginal. It could not make any of them
    pass bars 2–3.

## Raw lots (unbooked, first-signal rows; R/lot after costs; day-clustered t)
| Setup | CHECK n · LIVE-L / LR8 / gross · t | T2 n · LIVE-L / LR8 / gross · t | Lots/session CHECK / T2 |
|---|---|---|---|
| L1 CWT14-failbrk-orl-p10-long-WB5 | 12,730 · −0.110 / −0.024 / −0.005 · −9.4 | 4,833 · −0.125 / −0.040 / −0.017 · −8.3 | 46 / 11 |
| L2 ULT-05-withgap-cont-long | 5,703 · −0.045 / +0.002 / +0.018 · −4.6 | 1,140 · −0.055 / −0.003 / +0.018 · −2.8 | 21 / 2.7 |
| L3 GEN-261027-10 (holdtr) | 2,871 · −0.069 / −0.032 / +0.038 · −0.8 | 1,125 · −0.157 / −0.131 / −0.038 · −2.2 | 10 / 2.6 |
| L4 GEN-261023-07 (hold) | 3,320 · −0.037 / +0.006 / +0.096 · −0.2 | 2,928 · −0.155 / −0.108 / +0.002 · −2.5 | 12 / 6.9 |

## Controls and robustness
- **Size-matched random add** (K = 20 per config): each long lot is replaced by the same symbol on the same day at a
  random minute inside the setup's window, with the same %-risk and exit rule, and booked under the same rules.
  - **CWT14-WB5 times its entries better than random:** 100th percentile on CHECK, 80th–100th on T2. Its losses come
    from costs, not timing.
  - **The GEN longs sit at the 0th percentile, and the random adds were positive** (CHECK +0.4 to +1.4R/day).
  - **Caveat:** this control is biased in favour of the random adds for setups gated on day-state. A shadow can enter
    before the real signal fired, so it knows the day's breadth stayed above 0.65 / 0.70 by then (look-ahead).
  - So the comparison does not show that random timing works. It only shows that the GEN triggers add nothing on top of
    "it is a strong-breadth day".
- **Stress** (+1 min entry, same levels, +2 bp per side): worse in every config (bar 7 fails everywhere).
- **Concentration:** CHECK best-day shares are 2–25% for L1 / L2 and 13–63% for L3 / L4. dR without the best day is
  negative in every config.

## Day types: what the longs actually do for Primary (CHECK, R/day)
| | REF (P4) | + L3 GEN-261027-10 C30 | + L4 GEN-261023-07 C30 | + L1 CWT14-WB5 C30 | + L2 ULT-05 C30 |
|---|---|---|---|---|---|
| up days (98) | −7.73 | +1.40 | +0.45 | −0.75 | −0.13 |
| down days (84) | +1.03 | −0.78 | −0.72 | −7.77 | −0.85 |
| quiet days (94) | −1.78 | −1.66 | −1.95 | −4.23 | −1.03 |

The up-day hole is about 5x larger than the best long's up-day contribution. T2 shows the same pattern but smaller:
REF −4.07 / +0.90 / −1.23 on up / down / quiet days, and L4 C30 +0.83 / −1.46 / −1.27.

## Live context (paper, all accounts, run 1, LR8, identical signals once; lb_live.py → live.json; window 10-06..11-27)
| Setup | Live n / days | avg R | w/o best day | Best day (share) | Corr with Primary live short R by day | On Primary's red days |
|---|---|---|---|---|---|---|
| L1 CWT14-WB5 (Testing D, from 11-17) | 148 / 7 | +0.076 | +0.035 | 11-18 (76%) | −0.27 (7 days) | +11.0R over 6 days |
| L2 ULT-05 (Testing E, from 11-20) | 467 / 5 | −0.025 | −0.056 | — (total < 0) | +0.07 (5) | −14.6R over 4 |
| L3 GEN-261027-10 (Gen → Testing D) | 176 / 6 | +0.146 | −0.409 | 11-25 (224%, `1 day`) | −0.85 (6) | +25.8R over 6 |
| L4 GEN-261023-07 (Gen → Testing 2) | 139 / 11 | +0.460 | −0.296 | 11-25 (142%, `1 day`) | −0.68 (11) | +63.1R over 10 |
| NM-ETF (already in Primary) | 53 / 18 | −0.050 | −0.120 | — | −0.10 (18) | +6.0R over 12 |

- Live correlations are strongly negative, but they rest on 5–11 days and on 11-25.
- The 2-year bench gives about −0.1 to −0.3, and it is the better guide.
- Replays and bench results never count as a live record (rule 21).

**Rule changes inside the live window (ledger):**
- **Setups:** 11-16 ROT1 arena block 1 (the GEN setups move to Testing A); 11-17 the CWT14-orl-p10 WB5 version starts
  (Testing D); 11-20 ULT-1119 testing admissions (ULT-05 starts) and ROT arena block 2 (GEN-261027-10 → Testing D).
- **Primary:** 11-23 BRAKE-BURST / PSHADOW in Primary; 11-27 GYH V1+V3, ROT-B3.
- **Next:** 11-30 ETF-STOP50 / AV50 on Primary's NM-ETF.
- Each long's live record above therefore covers only its current version. Primary's live short book changed on 11-23.

## What we learned / what is next (optimistic but honest)
- **The diversification mechanism is real but small.** Longs gated on strong breadth at midday (GEN-261027-10 /
  261023-07) are the only ones that pay on up days. Their edge sits in the day-state ("breadth stays above 0.65 at
  midday"), not in their triggers.
- **Salvage idea (post hoc, not tested, not logged, would need its own pre-registration):** an index-level expression
  of the same day-state, such as one SPY / QQQ long when breadth_open > 0.65 at 11:30. It would cost about 0.10R round
  trip instead of 10–12 stock lots each paying LIVE-L.
- Wave 4's DAYTYPE (breadth extremes as one SPY/QQQ position, 11:30 / 13:00 → 15:55) already failed after costs, with a
  +0.03R gross tilt, so expectations are low.
- **Primary's real lever on up days is still the short side** (exposure, squeeze exits, sizing). It is not a long add.
- **CWT14-WB5 has good timing but no gross edge.** It beats random entries, yet its gross R is about 0, its stops are
  tight and LIVE-L costs are 0.10R per lot. No new CWT14 variant is proposed (consultant guardrail).

## Files
- PREREG.md / .sha256
- lb_gen.py (lots: bench10 signals plus the time-stop / hold / holdtr / stress / shadow walk; T2 breadth proxy built from
  469 names, median 456 per bar)
- lb_book.py (E4 5-slot book, controls, bars)
- lb_live.py + live.json (live context)
- results.csv, summary.json, daily.csv (book R/day by config with date / split / day type), run_out.txt
- Scratch: about 450MB under the scratchpad, deleted after the run.
- Smoke runs before scoring: one month's signal counts, and a 120-symbol, 2025-10 walk and book test to debug the
  scripts. They are not counted as configs, and no setting was changed after them.
