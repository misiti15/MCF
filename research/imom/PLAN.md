# IMOM — published 'market intraday momentum' (Gao, Han, Li & Zhou, JFE 2018) on our SPY window (FROZEN 2026-11-15 03:30 ET, before scoring)
Educational only — not financial advice. Source (read-only): Gao, Han, Li, Zhou, 'Market intraday momentum', Journal of Financial
Economics 129(2), 394-414, 2018 (SPY 1993-2013): the first half-hour return, measured from the PREVIOUS day's close to 10:00,
predicts the last half-hour return; stronger after positive first half-hours. A named external rule = Lead's reopen criterion for
the direction thread. It respects the owner's anchor rule (no 09:30 entry; the decision is at 15:30, scored by the return after it).
Prior: published effects decay after publication (in-sample R^2 ~1.6%); our window is post-publication and short, so ~0 is likely.
## Data
LEAD20 cache: SPY (and SPXL) 5-min SIP bars 2024-10-01..2026-11-13, locked block absent. Prior close = the previous session's
close of the 15:55 bar; the first session after the locked-block gap has none and is dropped. TRAIN <= 2025-09-30 < VALID.
## Definitions (paper's, on 5-min bars)
r1 = SPY close of the 09:55 bar (= 10:00) / prior close - 1. r_last = close of the 15:55 bar / open of the 15:30 bar - 1 (15:30 -> 16:00).
- **C1 (sign):** position = sign(r1) in SPY from 15:30 to 16:00; value = sign(r1) x r_last.
- **C2 (long-only):** long SPY 15:30 -> 16:00 only when r1 > 0.
Costs per round trip: SPY 1c + 1bp x 1.0 + 1bp spread entry, 1c + 1bp exit (index ETF, late day). SPXL rows reported (own price), not gated.
## Score, bar, pass
Mean per trade in bps, gross and net; t over days (one trade per day, so day-clustering is automatic); TRAIN / VALID; w/o best day;
MDE80 = 2.8 x SE and MDE at the bar (guild standard); also the OLS slope of r_last on r1 (paper's form) with its t.
Family market-state 2,611 + 2 = 2,613 -> BAR90 3.57.
Pass (lead for an arena field test only): C1 or C2 net mean > 0 with t >= 3.57, > 0 in TRAIN and VALID, w/o best day > 0. Else closed
with 'nothing above MDE'. One look; no variation of times (10:00 / 15:30) or of the reference.

## RESULT (one look, 2026-11-15 03:40 ET) — FAIL, IMOM closed: the published effect is absent in our window
`imom.py` -> `imom_out.txt`. SPY 451 sessions (2024-10-02..2026-11-13; r1 > 0 on 250).
- Slope of the last half-hour on the first half-hour return: **-0.016 bps per bp (t -1.10)**; the paper found a positive slope.
- C1 (trade the sign): -0.71bps gross (t -0.71), -4.01 net; TRAIN -0.18 / VALID -1.02. C2 (long after a positive first
  half-hour): -0.87bps gross (t -0.75), -4.17 net; TRAIN +1.49 / VALID -2.15 (t -1.70). SPXL rows: the same signs (-2.2 / -2.6bps).
- Power: MDE80 2.8bps (C1) / 3.3bps (C2). The paper's long-only result, as replicated by secondary sources (~6.3% a year gross, about
  2.5bps a day), is about the size we could detect, and our estimate is about one SE below it, on the other side of zero. So:
  nothing above ~3bps in our window, and no sign of the published effect. That is consistent with post-publication decay. The
  2024-2026 sample is short (one SPY trade a day).
- Costs (~3.3bps round trip on SPY) exceed even the paper's in-sample effect, so it was never tradable at our cost level.
