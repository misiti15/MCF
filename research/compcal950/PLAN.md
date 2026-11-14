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
