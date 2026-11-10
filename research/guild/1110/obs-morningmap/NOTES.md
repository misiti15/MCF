Educational only — not financial advice.

# obs-morningmap — where could a MORNING on/off condition help? (Observer, 2026-11-10 ~04:00 ET)

Lead's request lead-20261110-0300-4. Descriptive map, **2 counted looks** per family-side, both on ex-market R:
L1 = aligned minus counter, L2 = aligned minus no-reading. Reading at entry = e_checkpoint, the latest 30-min checkpoint strictly before
entry (Builder's re-tag). ex-market = gross minus TRAIN-fitted beta x signed SPY move over the hold (as coilam.py).
Contrast is **between days** (a one-side family has one reading per day, so a same-day contrast is impossible; first version tried
that and found 0 testable; fixed). `morningmap.py <tagged file>`, which works on coil_tagged.csv.gz and trades_tagged.parquet.

## Coil (CWT12-L, 20,779 two-year trades): no consistent sign
- L1 aligned minus counter: TRAIN **-0.030** (t -0.47, 39 counter days) vs VALID **+0.051** (t 1.11, 65). Sign flips.
- L2 aligned minus no reading: TRAIN -0.041 (t -1.00) vs VALID +0.036 (t 1.27). Sign flips.
- Pooled ex-market: TRAIN aligned -0.052 / counter -0.038 / none +0.020; VALID aligned +0.018 / counter -0.040 / none -0.028.
**Disclosure:** for coil longs, 'counter' = a DOWN checkpoint before entry, which is the split Scout's frozen COILAM rule scores.
COILAM was frozen (09:15 ET post, PLAN_COIL.md) before this look, so the rule was not chosen from it. But I have now seen the coil
outcome by state before Builder's independent score. Count this as a look on the same data. It previews a TRAIN problem for COILAM.

## All families: needs trades_tagged.parquet (Builder's container, not committed); requested on the board.
