# Time-in-trade exits per family — results

*Educational only — not financial advice.* 2026-11-20. Plan pre-registered in `PLAN.md` (written before scoring).
Nothing committed, no live setting touched. **Verdict: FAIL** — the time-in-trade class does not add R on the check half.

## What was tested
- WB2 paired scoring on the parent's own signals: the giveback map's 2-year lab paths (first signal per (setup, symbol,
  day), bt_lab1104 lists, BEREPLAY walk, bt_all costs **plus an extra 0.01/share on every early exit**). Locked block
  2024-11-01..2025-02-28 absent (re-asserted at read). Unit = stop distance.
- Fit = 170 sessions to 2025-09-30 (370,276 trades); check = 276 sessions 2025-10-01..2026-11-04 (736,115 trades), scored once.
- Two classes per family-side (36 family-sides), checkpoints T ∈ {15, 30, 45, 60, 90, 120} min:
  - **A "never worked"**: exit at T if MFE < m and mark < r (m ∈ {0.25, 0.5}, r ∈ {−0.25, 0, +0.25}).
  - **B "worked, then faded"**: exit at T if MFE ≥ m and mark ≤ r (m ∈ {0.5, 0.8, 1.0}, r ∈ {0, +0.25}).
- Per family-side, the best of 72 configs on fit was adopted only if fit avg Δ > 0, fit day-clustered t ≥ 2.0, fit Δ
  without best day > 0, and ≥ 100 fit firings. Plus one book-wide config per class chosen on fit (secondary).
- **Configs: 2,592 per-family + 72 book-wide = N 2,664** (lineage with the map's 916 descriptive cells: 3,580).
  Bar = max(1.5, sqrt(2 ln N)) = **4.05** (3.97 at N 2,664; 4.58 at 10x N for sibling classes).

## Fit half
- Only 36 of 2,592 fit cells reach t ≥ +2 (fewer than chance would give); 81 reach t ≤ −2. Class A cells sum to −70,637R,
  class B to −7,256R: cutting time-stalled trades mostly costs R, as the map's stalled-trade signature said.
- CWT14 long (the largest family, 187,594 fit trades) has no config with positive fit ΔR.
- Adopted: **2 of 36** family-sides — RW1 short (A T15 m0.5 r0, fit +80.8R, t 2.21) and RW3 short (A T15 m0.5 r−0.25,
  fit +41.2R, t 2.11). The adopted book improved fit by +121.9R (t 2.61).

## Check half (scored once)
| measure | before | after | change |
|---|---|---|---|
| total R | −53,193.2 | −53,310.6 | **−117.4R** |
| avg R / trade | −0.07226 | −0.07242 | −0.00016 (paired t **−1.58**, bar +4.05) |
| avg R w/o best day | −0.07360 | −0.07376 | worse |
| trades exited early | | 3,097 | |

- Per family (adopted): **1 better, 1 worse.** RW1 short −125.0R (−0.024R/trade, t −2.10, 2,348 fired); RW3 short +7.6R
  (+0.002R/trade, t 0.29, 749 fired). Per setup: same (one setup in each family): 1 better, 1 worse.
- Best-day share: not meaningful (the change is negative).
- Diagnostic (not part of the rule): each family's fit-best config applied to check regardless of gates: **9 families
  better (+137.9R), 26 worse (−1,527.4R), 1 unchanged; net −1,389.5R.** RW7's fit-best "below entry" cut (the map's
  candidate) loses −345.6R on check; exhaustion_short −199.8R.
- Book-wide secondaries: A (T120, MFE < 0.25, mark < −0.25) −126.4R on check (t −0.62); B (T120, MFE ≥ 0.5, mark ≤ 0)
  −399.8R (t −2.35).

## Live (run 1, 10-06..11-19, 33 sessions, 28,097 de-duplicated trades; descriptive only)
- Adopted rules fired on 196 trades: −28.6R (−0.001R/trade over the book, t −1.71). RW1 short −15.5R (152 fired),
  RW3 short −13.0R (44 fired).
- Book-wide secondaries: A +27.2R (1,761 fired, t 0.69); B −13.9R (745 fired, t −0.41). Neither is evidence.
- Rule changes inside the live window (from the map / `research/ledger.jsonl`): Testing2 scale-out to breakeven
  (10-16/17); per-setup latch (10-23); Primary sizing x2 (10-28); Primary −2R latch (10-29); Testing cost filter (10-30);
  LR1 flatten time, LR3/LR8 costs, Gen/Graveyard sizing (11-12); TSZ1 sizing, SPYEXIT copies (11-17); C3 Epoch 1 (11-19).

## Pass rule
| condition | result |
|---|---|
| total and avg R improve on check | no (−117.4R) |
| avg R w/o best day not worse | no |
| not carried by one day | n/a (negative) |
| more families / setups better than worse | no (1 vs 1) |
| paired t ≥ 4.05 | no (−1.58) |

**FAIL.** Nothing goes to the backlog from this class. It agrees with L16, the book-wide breakeven, W5 X1-X3, the Wave 2
trail and the map's stalled-trade signature: a trade's own clock and R path do not say when to leave. The giveback
pockets the map found (far targets, GEN hold setups without a target, one-sided book against SPY) look like problems of
target geometry and book exposure, not time in the trade.

## Caveats
- The lab has no GEN hold lists, ETB, stacking or latch, and it walks only the first signal per (setup, symbol, day).
- Exits are marked at the checkpoint bar's close; the extra 0.01/share is the execution allowance. Checkpoints are
  limited to the map's grid, so a rule at, say, minute 20 was not tested.
- Lab trades are weighted equally, so CWT14 long (≈ 51% of trades) dominates book totals. It got no rule.

## Full family table (fit-best rule; check ΔR shown for all, but only adopted rows count)
| family-side | fit-best rule | fit ΔR | fit t | adopted | check ΔR (fit-best rule) | check Δavg |
|---|---|---|---|---|---|---|
| CWT05 long | A T45 m0.5 r0 | 15.6 | 1.2 | no | -18.4 | -0.0077 |
| CWT09 short | B T45 m0.5 r0 | 20.2 | 2.21 | no | 0.6 | 0.0002 |
| CWT12 long | A T15 m0.25 r0 | 57.9 | 0.8 | no | 49.7 | 0.0035 |
| CWT13 long | A T15 m0.25 r0.25 | 8.9 | 0.11 | no | -63.8 | -0.0049 |
| CWT13 short | B T30 m0.5 r0.25 | 50.1 | 0.99 | no | -37.8 | -0.0027 |
| CWT14 long | B T15 m0.5 r0 | 0.0 | nan | no | 0.0 | 0.0 |
| CWT14 short | A T30 m0.25 r-0.25 | 62.3 | 0.58 | no | -53.5 | -0.0007 |
| GEN long | B T30 m1.0 r0.25 | 16.8 | 2.19 | no | -27.2 | -0.0008 |
| GEN short | B T120 m0.5 r0 | 10.1 | 0.46 | no | -30.6 | -0.0014 |
| L3 short | B T60 m0.5 r0 | 26.0 | 1.17 | no | 3.2 | 0.0003 |
| MF1 short | A T45 m0.5 r0 | 15.5 | 0.62 | no | -32.9 | -0.0047 |
| MF2 short | B T120 m0.8 r0 | 12.5 | 3.14 | no | 0.5 | 0.0001 |
| MF3 short | B T60 m0.5 r0.25 | 31.9 | 1.52 | no | -14.6 | -0.002 |
| MF4 short | A T90 m0.5 r0.25 | 42.4 | 1.64 | no | -31.8 | -0.0042 |
| MF5 short | A T90 m0.5 r0.25 | 35.1 | 1.22 | no | -92.2 | -0.0209 |
| NM long | A T30 m0.5 r-0.25 | 14.9 | 0.89 | no | -11.4 | -0.0044 |
| NM short | B T45 m0.5 r0.25 | 5.1 | 0.45 | no | -8.3 | -0.0053 |
| NS1 long | A T90 m0.25 r0.25 | 1.0 | 0.25 | no | 9.1 | 0.0039 |
| NS2 short | A T15 m0.5 r0.25 | 31.8 | 0.38 | no | 64.7 | 0.0079 |
| NS3 short | A T60 m0.25 r-0.25 | 2.4 | 0.16 | no | -15.3 | -0.002 |
| NS3V1 short | A T90 m0.5 r-0.25 | 10.0 | 2.49 | no | -7.2 | -0.0058 |
| NS4 short | A T15 m0.25 r0.25 | 14.2 | 1.25 | no | 0.3 | 0.0002 |
| NS5 long | B T60 m0.5 r0.25 | 62.1 | 1.32 | no | -20.2 | -0.0066 |
| RW1 short | A T15 m0.5 r0 | 80.8 | 2.21 | yes | -125.0 | -0.0237 |
| RW2 short | A T45 m0.25 r0.25 | 45.2 | 1.03 | no | -69.9 | -0.0042 |
| RW3 short | A T15 m0.5 r-0.25 | 41.2 | 2.11 | yes | 7.6 | 0.0018 |
| RW3S short | A T30 m0.5 r-0.25 | 86.9 | 1.64 | no | -94.9 | -0.0042 |
| RW4 short | A T60 m0.25 r-0.25 | 5.0 | 0.37 | no | -14.9 | -0.0024 |
| RW5 short | A T90 m0.5 r0.25 | 13.2 | 0.56 | no | -72.1 | -0.0188 |
| RW6 short | A T15 m0.5 r0.25 | 5.0 | 0.18 | no | -31.1 | -0.0118 |
| RW7 short | A T15 m0.5 r0 | 126.5 | 0.98 | no | -345.6 | -0.0191 |
| ST1 long | A T120 m0.5 r-0.25 | 0.9 | 0.31 | no | 2.1 | 0.0018 |
| ST2 long | A T30 m0.5 r-0.25 | 11.0 | 0.48 | no | -39.2 | -0.0045 |
| ST4 long | B T30 m1.0 r0.25 | 4.3 | 2.56 | no | -10.4 | -0.0102 |
| ST7 long | A T15 m0.25 r0 | 8.1 | 1.04 | no | -59.2 | -0.0685 |
| exhaustion_short short | A T90 m0.5 r0.25 | 61.3 | 1.28 | no | -199.8 | -0.0093 |
## Files
`PLAN.md`, `score.py`, `summary.json`, `family_check.csv`, `family_check_all_bestfit.csv`, `setup_check.csv`,
`live_family.csv`, `fit_grid.csv.gz` (all 2,592 fit cells).
