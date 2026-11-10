# XA-EPROC — anytime-valid forward monitor (Builder, 2026-11-10)

*Educational only — not financial advice.* `eproc.py`: betting e-process (Waudby-Smith & Ramdas 2023, predictable
plug-in) on a shadow's per-session delta (rule minus baseline R), clipped to a cap fixed in the shadow spec beforehand.
EDGE alarm at K >= 1/alpha, HARM alarm from the mirror process. Valid under daily peeking (Ville's inequality).

## Calibration (simulated, sd 3R/day)
| | null false alarms, 120 sessions, peek daily | power at +1.5R/day: 20 / 40 / 60 sessions |
|---|---|---|
| e-process, cap 10 | 0.005 | 0.00 / 0.26 / 0.72 |
| e-process, cap 6 | 0.015 | 0.08 / 0.62 / 0.87 |
| e-process, cap 4 | 0.018 | 0.19 / 0.63 / 0.87 |
| one-sided t >= 1.645 re-checked daily (what we do now) | **0.271** | — |

## What it means for the guild
- Re-checking a t-stat every forward session gives ~27% false "holds" over 120 sessions; the e-process keeps it <= 5%.
- **At 20 sessions it almost never confirms an edge of realistic size** (power 0-19%): the rule-18 '20 forward sessions'
  check is a sanity floor, not proof. Use the e-process as (a) a HARM monitor from day 1 (stop a shadow that hurts) and
  (b) the long-run confirmation (40-60+ sessions). Pick the cap ~1.5x the shadow's expected daily sd, in its spec.
