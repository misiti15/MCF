Educational only — not financial advice.

# COMPASS-5M — pre-registration (2026-11-10, written before any score)

Owner question (11-10 ~13:55 / ~14:00 ET): do rolling 5-min (and 10-min, "moveable glue") stats between the 15-min
marks give a more up-to-date direction? Which window can the plain-English line honestly name?

Data: the COMPASS-LEARN 5-min panel (research/compass_learn/panel.py; history cache + live days 11-05/06/09; locked
block 2024-11-01..2025-02-28 filtered inside the read). Periods as COMPASS-LEARN: TRAIN (2024-10 + 2025-03..12),
VALID (2026-01-01..10-05), FWD (10-06..11-04), LIVE (11-05..11-09, 3 days, shown only).

## Family (10 state definitions; cap declared 16)
A state is +1 / -1 / 0 at each 5-min mark, from bars closed by the mark, held until its next update.
| id | state |
|---|---|
| S1 W60 | today's compass, 15-min marks, confirmed side (baseline) |
| S2 GLUE5 | W60 votes recomputed every 5 min; persistence = the 15-min marks of the last 60 min + the current 5-min reading all on one side; confirmed rule unchanged |
| S3 GLUE10 | same, updated every 10 min |
| S4 CHK15 | SPY >= 0.20% from its open at the 15-min marks (COMPASS-LEARN best) |
| S5 MOM5 | sign of SPY's last-5-min return, when >= 0.05% |
| S6 MOM15 | sign of SPY's last-15-min return, when >= 0.10% |
| S7 MOM30 | sign of SPY's last-30-min return, when >= 0.15% |
| S8 TILT5 | "fresh tilt": SPY, QQQ, IWM last-5-min returns all one sign AND breadth (share of 200 names above open) moved >= 2 pts the same way in 5 min |
| S9 VWAP | SPY >= 0.10% from its session VWAP on that side (every 5 min) |
| S10 TILT10 | fresh tilt over 10 min (breadth >= 3 pts) |

## Targets
- Short horizons h = 5, 10, 15, 30, 45, 60, 90 min, at every 5-min mark 10:00..(15:55 − h) where the state fires:
  (a) direction: SPY's sign over the next h minutes equals the state (zero moves dropped);
  (b) size: SPY moves >= 0.10% in the called direction over the next h minutes.
  Hit rate, coverage (share of marks where the state fires), base rate (period share of moves in the called
  direction, for (b) share of >= 0.10% moves in that direction), excess = hit − base, t clustered by day.
- Rest of day (side): GLUE5 / GLUE10 vs W60 with COMPASS-LEARN's score S on the 15-min grid (paired t by day).
- Tests: 10 states x 7 horizons x 2 targets + 2 side tests = 142 -> bar t >= sqrt(2 ln 142) = 3.15.
- "Works" = VALID t >= 3.15, VALID hit >= 55% (direction) or excess >= +5 pts (size), TRAIN t >= 1.5 same sign,
  FWD same sign. Contrarian readings (hit well below base) are reported the same way (|t|).

## Conditional stats (descriptive, no test)
Table by time of day (10-min, 10:00..15:50) x SPY-from-open bucket (< −0.4, −0.4..−0.2, −0.2..0, 0..0.2, 0.2..0.4,
> 0.4 %) x SPY vs the previous close (above / below), and a second grouping with the gap (up >= +0.2%, down <=
−0.2%, flat). Outcomes: % closing on the same side of the open, % closing on the same side of the previous close,
median / quartiles of the move to the close, next 5/10/30/60-min direction hit (in the from-open direction), n.
Built on all periods except LIVE first, then appended nightly (mcf/report/compass_cond.py).

## Plain-English line
State table (W60 level x time block, plus "after a midday flip": SPY at 12:00 >= 0.20% from its open on one side,
then on the other side of the open at a later 15-min mark): % SPY closes on the stated side, TRAIN+VALID with FWD
shown. Window = the rest of today unless a short horizon passes the rule above.
