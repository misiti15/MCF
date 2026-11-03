Educational only — not financial advice

# eu1103 / universe — pre-declared before the two-year and live-period-expansion results were read

Written 2026-11-03 ~09:45 ET, after live_buckets_out.txt / live_rules_out.txt (live) had been seen, before
analyze2y.py or the expand_live.py results were read.

Setups (8 busiest live by trades, 10-06..11-02, one per family where twins exist): CWT14-failbrk-orl-p05-long,
CWT14-failbrk-pdl-p05-long, CWT12-coil-k4-long, CWT14-failbrk-pdh-p10-short, heat_fade_short-FD,
RW7-gapdn-bounce-early-short-FD, RW2-exhaustion-noon-adv150-short-FD, L3-gap-slope-fromopen-FD.

Rules (smaller): S1 top-300 / 500 / 800 by dollar-ATR (ADV x ATR%, point-in-time); S2 move history >= 3% of prior 60
sessions as a top-50 mover; S3 ATR% >= 3; S4 drop idiosyncratic names (no sector SPDR residual corr >= 0.15) —
**S4 is live-derived** (seen in live_buckets before it was declared); S5 ADV >= $300M.
Rules (larger): L1 floor $50M on 2 years (names added between $50M and the setup floor; survivor-biased lab names);
L2 floor $20M on the live period (10-05 universe membership, not survivor-biased).

Pass bar for proposing a universe rule (all needed): pooled kept-minus-dropped per-session difference > 0 on TRAIN and
VALID and live with t >= 1.0 on each of the two-year splits; kept avg R not worse than base on >= 6 of 8 setups on VALID;
and for a larger universe: the added names' avg R >= the base avg R on 2y VALID AND on the live-period re-score.
Configurations: 9 rules x (8 setups + pooled) x 2-3 data sets, counted in NOTES.md.
