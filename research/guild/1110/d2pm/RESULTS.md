Educational only — not financial advice.

# D2PM results (Observer, 2026-11-10 ~16:45 ET): CLOSED by its own kill line

Frozen PLAN.md (3 looks, family N 229, BAR90 2.97) + Skeptic's reporting cuts. Data fetched after 16:00 ET (premarket 04:00-09:29 and RTH,
2026-09-24..11-10, 1,624 names = names traded live U lab list; 1 failed each). Scored sessions 2026-10-07..11-09 (24; norms need >= 5
prior sessions). Outputs: `d2pm_out_live.txt` (all 1,602 names with data), `d2pm_out_lab.txt` (fixed lab list, 1,212 names).
ex-market = minus SPY (beta 1); entry 09:51 open; 562 event name-days (Skeptic's AMC -> next-session mapping, dmh dropped).

## Failures first
- **Kill line met.** In the top premarket-volume quintile, neither direction look beats the plain gap baseline. All names, 09:51->11:30:
  gap +9.3bp (t 1.32), L2 premarket-VWAP drift +6.4bp (t 1.29), L3 last-30-min drift -0.8bp (t -0.28). Lab list: gap +12.3bp (t 1.97),
  L2 +6.5bp (t 1.32), L3 +1.1bp. To 15:55 the same. **D2 closed.**
- No direction look reaches t 2 overall: L2 all names +8.7bp (t 1.42); L3 ~0 everywhere.
- **Event names are noise:** 562 name-days, 19-23 days; L2 best-day share 65%; tercile cells flip sign (T2 vs T3) with |t| up to 3.45
  on ~180 rows. Nothing to read.

## What it shows
- **Size again (L1, descriptive):** premarket dollar-volume rank vs its own norm picks the day's top-50 movers with AUC 0.605 (lab 0.588;
  event names 0.65) vs |gap| 0.548. Same story as SIZEBKT / HODSEP / COMPASS-5M: activity predicts how much, not which way.
- **The one within-plan contrast that clears t 2 is market direction:** 'premarket drift agrees with the gap' minus 'disagrees' (gap side,
  to 11:30) +15.4bp t 2.09 (lab +14.9, t 2.24). By SPY day it is all DOWN days: L2 +20.5bp (t 3.80) on 6 down days, +1.6bp on 12 quiet,
  +11bp (t 0.49) on 6 up. One crash-heavy month (11-05). Below the 2.97 bar and regime-driven: not a lead.
