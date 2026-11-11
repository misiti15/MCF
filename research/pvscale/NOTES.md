# PVSCALE — compass card SIZE line: implementation notes (Builder, 2026-11-10)

*Educational only — not financial advice. Display only — not a trading signal, not a direction call.*
Evidence: `pvscale_out.txt` (one counted look, plan `PLAN.md` frozen first; alpha fitted on TRAIN only, scored once on
VALID, FWD sanity only). Lead adopted it by its fixed rule (lead-20261110-1900-1). The close-side line stays COMPCAL M1.

## The rule (exact, point-in-time)
At a 15-minute mark T (09:45 .. 15:15; bars that START before T, i.e. closed by T), for SPY:
1. `rg_today` = (highest high - lowest low of today's 1-min RTH bars before T) / today's open x 100.
2. For each of the PRIOR 60 full sessions j (not today; skip a session with rg_j = 0; need >= 40):
   - `rg_j` = the same range at the same T on day j;
   - `mv_j(h)` = |SPY close at T+h / close at T - 1| x 100 on day j, for h = 30, 60, 90 min, and to the 15:55 close;
   - scaled move `s_j(h) = mv_j(h) x (rg_today / rg_j) ** 0.8`.
3. Band for horizon h: `median_h` = median of s_j(h), `p80_h` = 80th percentile of s_j(h).
- **alpha = 0.8** (fitted on TRAIN pinball loss; 0 = Scout's unscaled band). Do not refit it on recent data; re-check it
  only through a counted look.

## Card wording
> **Next hour: SPY usually moves about {median_60}% from here; on 4 of 5 days less than {p80_60}% (scaled to today's
> range so far). By the close: about {median_close}%, 4 of 5 days less than {p80_close}%. Size only — not a direction.**

## Calibration (why it can be shown)
| | in 80% band (target 0.80) | in median (target 0.50) | in80 by vol tercile low / mid / high |
|---|---|---|---|
| unscaled band (alpha 0), VALID | 0.791 | 0.505 | 0.90 / 0.81 / 0.64 |
| **scaled (alpha 0.8), VALID** | **0.794** | **0.503** | **0.77 / 0.80 / 0.81** |
| unscaled, FWD (24 sessions) | 0.677 | 0.423 | 0.87 / 0.62 / 0.56 |
| **scaled, FWD** | **0.780** | **0.485** | **0.78 / 0.71 / 0.88** |
Pinball loss VALID 0.1192 vs 0.1280 (day-clustered t -4.48); FWD 0.1082 vs 0.1277 (t -1.07).

## Example (computed for 2026-11-09, a wide-range day; prior 60 sessions)
| mark | range so far (prior-60 median) | next 60 min: unscaled med / p80 | **scaled med / p80** | to close, scaled med / p80 |
|---|---|---|---|---|
| 10:00 | 0.94% (0.27%) | 0.13% / 0.31% | **0.34% / 0.83%** | 0.71% / 1.22% |
| 11:30 | 1.45% (0.49%) | 0.12% / 0.19% | **0.26% / 0.45%** | 0.41% / 0.80% |
| 13:00 | 1.61% (0.58%) | 0.07% / 0.17% | **0.18% / 0.35%** | 0.25% / 0.50% |
| 14:00 | 1.67% (0.60%) | 0.09% / 0.17% | **0.20% / 0.35%** | 0.19% / 0.44% |
On a wide day the unscaled band says "small moves ahead" and would be wrong ~1 time in 3 on high-vol days; the scaled
band widens with the day.

## Limits
- SPY only; survivorship not relevant (index). 1-minute SIP bars; half days excluded.
- FWD is 24 sessions; the vol-tercile coverage there is noisy (mid 0.71).
- Recheck: every ~20 sessions, recompute in80 / in50 on the newest sessions; a drift beyond +-5 pt is a reason for a new
  counted look, not a silent retune.
