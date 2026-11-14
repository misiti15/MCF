# COMPCAL950 — the M1 calibrated close-side line referenced to the 09:50 level (FROZEN 2026-11-14 15:20 ET, before scoring; display only)
Educational only — not financial advice. Lead lead-20261114-1500-2; owner anchor rule 2026-11-14; COMPCAL (research/compcal) M1.
## Line (no fitting; every probability uses only the 60 prior sessions, so it is out of sample by construction)
Anchor A = open of SPY's 09:50 bar. At mark T (every 10 min, 10:00..15:50): f = SPY % above A, using the close of the 5-min bar
that ends at T. y = 1 if SPY's close (close of the 15:55 bar) is on the same side of A as at T (marks with f == 0 dropped).
**M1-950:** P = share of the prior 60 sessions whose SPY move from T to the close, m (% of A), satisfies sign(f) x (f + m) > 0.
Display: 'SPY is X% above its 09:50 level at T; on N of the last 60 days the move from T to the close was smaller, so it
finishes above 09:50 ~P%'.
**Comparator M1-open (COMPCAL's M1)** on the same bars and days: reference = the 09:30 open, target = close side of the open.
The two predict different events, so Brier is compared per model against its OWN target (sharpness and calibration of each
line), and the calibration tables are printed side by side.
## Data and periods
LEAD20 cache: SPY 5-min SIP bars 2024-10-01..2026-11-13, locked block absent. Prior-60 windows never span the locked-block
gap (a day needs 60 prior sessions after the gap), so scoring starts ~2025-05-28. VALID 2025-10-01..2026-10-07 and FWD
2026-10-08..2026-11-13 as in COMPCAL; the earlier days are reported as 'pre'.
## Scores
Brier and log loss per period for each line; day-clustered t of the per-day Brier difference (M1-950 vs M1-open, descriptive,
targets differ); calibration table (10 bins) for each; Brier by time of day (10:00-11:50 / 12:00-13:50 / 14:00-15:50).
One look. Display research only; the card choice stays the owner's (COMPCAL DECISION).

## RESULT (one look, 2026-11-14 15:40 ET) — the 09:50 line is calibrated and usable; slightly less sharp before noon
`compcal950.py` -> `compcal950_out.txt`. 370 scored days (2025-05-28..2026-11-13), 36 marks per day.
| period | M1-950 Brier / hit | M1-open Brier / hit | per-day diff (t) |
|---|---|---|---|
| pre (87 days) | 0.152 / 77.4% | 0.141 / 78.4% | +0.011 (0.90) |
| VALID (256) | 0.129 / 81.7% | 0.124 / 82.7% | +0.005 (0.54) |
| FWD (27) | 0.137 / 80.4% | 0.112 / 82.6% | +0.025 (0.70) |
By time of day (VALID + FWD): 10:00-11:50 0.197 vs 0.176; 12:00-13:50 0.122 vs 0.117; **14:00-15:50 0.070 vs 0.076 (09:50 better)**.
Calibration (VALID + FWD), mean P -> hit: M1-950 0.47->0.51, 0.56->0.60, 0.66->0.69, 0.76->0.78, 0.86->0.86, 0.97->0.96 (slightly
under-confident by ~0.03 in the middle bins, i.e. honest or conservative); M1-open 0.47->0.53, 0.56->0.57, 0.66->0.68, 0.76->0.76.
Reading for the owner (display only; COMPCAL decision is his): a 09:50-referenced line ('SPY is X% above its 09:50 level at T; on
N of the last 60 days the rest of the day moved less, so it finishes above 09:50 ~P%') is as well calibrated as the open-referenced
one. It is a little less sharp before noon, because SPY sits closer to its 09:50 level than to its open early on. It is slightly
better after 14:00. None of the differences are significant (|t| <= 0.9). Both lines read 'staying', not 'heading': they say how
likely the current side is to hold, not where the market goes next (ANCHOR950: the move after 09:50 is ~0).
