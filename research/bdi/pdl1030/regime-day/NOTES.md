# pdl1030 / regime-day: results

*Educational only — not financial advice.*

Research only (no repo / config / ledger / backlog writes). TRAIN+VALID only (348 sessions); HOLD months and the locked
block were never loaded (asserted in build.py and score.py). 17 configurations scored, all pre-declared in PLAN.md, none added.
N = 121566 + 3 x 17 = 121617 -> BAR90 t >= 4.355.

**Parity:** exact. PAR-P05 -0.0677 / -0.0675, PAR-P05S3 -0.0210 / -0.0173, REF-K3 (combo) +0.0062 / -0.0003.

**Result: nothing passes.** Best t is 1.32 (C1). No module was written.

| id | rule | TRAIN | VALID | t_TV | wf% | /sess | up / down day R |
|----|------|------:|------:|----:|----:|-----:|----|
| C1 | R4A flip only when intraday SPY-VWAP side agrees | +0.0108 | +0.0009 | 1.32 | 52.9 | 27.7 | +0.018 / -0.007 |
| R2A | S3+cost5; SPY prior-day range/ATR > 0.80 long, else short | +0.0031 | +0.0071 | 1.14 | 76.5 | 54.3 | +0.008 / +0.002 |
| REF-K3 | intraday SPY-VWAP flip (combo) | +0.0062 | -0.0003 | 1.18 | 58.8 | 54.3 | 0.000 / +0.007 |
| R4A | SPY ATR% > 1.00 long, else short (TRAIN-best) | +0.0053 | -0.0017 | 0.52 | 52.9 | 54.3 | +0.018 / -0.013 |
| R1B | SPY gap < +0.08% long, else short | +0.0045 | -0.0008 | 0.52 | 47.1 | 54.3 | +0.012 / -0.008 |
(all rows in results.csv / score_out.txt)

What it shows:
1. Pre-open SPY regime does not predict the session's direction out of sample. The feature-to-SPY-session-return
   correlations change sign between TRAIN and VALID (gap -0.12 / -0.01, prior range +0.04 / +0.19, close location -0.12 / +0.13,
   ATR% +0.09 / -0.05, prior return -0.18 / 0.00). So the TRAIN-best orientation (R4A) fails on VALID.
2. Every A/B pair sums to about the S3+cost5 base (~-0.003): the flip only redistributes the ~0 gross edge.
3. R2A (long after a wide SPY prior-day range, short after a narrow one) is the only row positive on both splits with
   wf >= 54% and balanced up/down R, but its lift is ~+0.005R and t 1.14, far below 4.355. It was not the TRAIN-best row.
4. With parent exits and no cost floor (C3) the regime flip is -0.052 (153/sess): the S3 stop and cost floor carry all the lift.

Timing: GAP known at 09:30; PRNG, PCLV, ATRP, PRET are prior-day quantities (reconstructed exactly from the first 09:45-09:50
bar row: the close and fromOpen terms cancel). The SPY-VWAP side in C1 is read at the signal-bar close (the entry).
