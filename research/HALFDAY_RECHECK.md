# Checklist #42 re-check: Scout's bar-based studies without early-close sessions (2026-11-15 05:30 ET)
Educational only — not financial advice. Skeptic skeptic-20261115-0950-1 found that the LEAD20 5-min cache includes extended-hours
prints; on half days the 'afternoon' bars are after-hours trades. Half days detected from the data with `research/halfday_clean.py`:
SPY 13:30-15:55 volume < 0.2 x its 09:30-12:55 volume (normal ~0.9, half days ~0.05). My first rule (a share of the median) missed
2025-11-28's busy after-hours. Found: 2025-07-03, 2025-11-28, 2025-12-24 (the 2024 ones sit in the locked block). Re-run with those dropped:
| study | headline before | without half days |
|---|---|---|
| LEAD20 | SPY broad-minus-other +6.1bps (t 0.37) | +6.2bps (t 0.37); 450 sessions |
| ETFTIER | SPXL tiered-plain -0.021R (t -0.67); TQQQ -0.015R | -0.021R (t -0.67); TQQQ -0.010R (t -0.26) |
| SHORTUP | excess +0.0067 ATR (t 0.30) | +0.0060 ATR (t 0.26) |
| SIZETREND | efficiency Q5-Q1 -0.0006 (t -0.20) | -0.0004 (t -0.14); range ratio 1.14 unchanged |
| IMOM / ANCHOR950 / COMPCAL950 | (Skeptic's reruns) | -0.65bps / +5.7bps / Brier 0.1298, no change |
No conclusion changes. Outputs: `*_rth_out.txt` beside each study. Future bar caches: run halfday_clean.py first (or require RTH volume).
