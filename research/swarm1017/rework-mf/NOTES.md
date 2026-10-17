# swarm1017 / rework-mf — results (2026-10-17)

*Educational only — not financial advice. Backtest on the open 2-year history at production cost. Live numbers below
are paper (rule 7). The locked block 2024-11..2025-02 was not loaded.*

## Failures first
- **No variant of MF1-MF5 (+FD) clears the try-count bar. Nothing is ready for live funds.**
  - Configurations scored: **47,820**, exactly as declared in PLAN.md (Stage A 6,240 / B 4,950 / C 31,680 / D 4,950).
  - Lineage N is about 133,904 (prior ~86,084 + 47,820), so the bar is day-clustered t >= **4.86**. The best t across
    all 32,442 configurations with n >= 200 is **2.42**. None reaches 3.
- The family is negative, not merely zero:
  - Of the 32,442 configurations with n >= 200, only 1,259 (3.9%) have exp > 0 on the whole open history.
  - 19,987 (62%) have t <= -2. Under a zero-mean null, about 2.3% (~740) would reach t >= 2 by luck. Only 16 do.
  - The median exp is -0.054 to -0.136R per parent and side. Refire is no better than first-signal (median -0.088 vs
    -0.085R). Every window and every geometry is negative at the median.
- **Opposite side (long the same signal):** this is worse for MF1, MF3 and MF5, and about as bad for MF2 and MF4.
  Fading the flow-sell is not the missing edge.
- **Screen:** 221 of 47,820 configurations passed (exp > 0 on train AND valid, n_tr >= 150, n_va >= 50, n >= 200).
  - 11 of those 221 pass the regime gate, 72 pass walk-forward >= 0.6, and 139 beat random at the same minute.
  - Only **2 pass every gate**. Both are MF4 long, t1s1, 09:50-11:00, Fridays only (with `slope<0` or `sma50<0`), and
    their trades overlap. After de-duplication 1 remains, MFR1 below, at t 2.16. Its t is far below the bar, and it is
    a day-of-week x filter pair picked out of 47k tries: **treat it as noise.**
- Most of the "best" cells are **MF1 short on Wednesdays only**, t1s1, 09:50-10:30. They are positive on train and
  valid, but they all **fail the regime gate**: up-session exp is about -0.10R, so they are a down-tape effect again.
- Plateau (Stage A, the threshold neighbourhood): no Stage A configuration even passed the screen. Tighter or looser
  heat, buyPressure, RSI5, RSI band or VWAP cuts do not rescue any parent.

## Filters that move the family toward 0 (Stage B medians, all still negative)
These are directional hints only, not edges:
- the high-ATR% tercile (-0.049R)
- fromOpen < -1% (-0.049R)
- off the high of day (dist_hod > 0.5 ATR, -0.063R)
- below VWAP (-0.065R) or below SMA50 (-0.065R)

The worst filters are low ATR, near the HOD, and above SMA50 or VWAP (about -0.11 to -0.12R). So the MF "flow-sell above
VWAP" premise (MF1, MF5) points the wrong way: shorting strength into VWAP-above loses the most.

## Parents reproduced (short, own geometry, open history, production cost)
| parent | window | n | exp R | day-t |
|---|---|---|---|---|
| MF1 | 950-1030 | 2,679 | -0.080 | -3.03 |
| MF1 | FD | 10,540 | -0.079 | -5.76 |
| MF2 | 950-1100 | 676 | -0.013 | -0.36 |
| MF2 | FD | 4,517 | -0.047 | -2.24 |
| MF3 | 950-1100 | 4,566 | -0.070 | -2.47 |
| MF3 | FD | 10,564 | -0.075 | -4.32 |
| MF4 | 950-1100 | 3,639 | -0.092 | -3.35 |
| MF4 | FD | 7,273 | -0.082 | -4.71 |
| MF5 | FD | 6,827 | -0.057 | -2.64 |

The FD trade counts match research/bdi/timeofday exactly. The MF1 window here includes the 10:30 bar, as the YAML
does.

## Live week (paper, research/swarm1017/week/setups_live.csv, 2026-10-06..16)
| setup | trades | adjusted avg R |
|---|---|---|
| MF2-FD | 19 | +0.43 |
| MF4-FD | 20 | +0.25 |
| MF3-FD | 43 | +0.08 |
| MF1 | 12 | +0.18 |
| MF4 | 19 | -0.01 |
| MF3 | 27 | -0.03 |
| MF5 | 33 | -0.12 |
| MF5-FD | 24 | -0.18 |
| MF1-FD | 26 | -0.30 |
| MF2 | 4 | -1.21 |

- 4-7 sessions is a diagnosis, not evidence. The 2-year history says every parent is negative after costs, and the
  positive live weeks of MF2-FD, MF4-FD and MF3-FD sit inside normal noise for 20-40 trades (SE about 0.2R).

## Candidate (fails the bar, reported for completeness)
- `modules/MFR1-h40-flowsell-fri-sma50dn-long.py` (long, t1s1, window [950, 1100]):
  - train n 151, +0.076R, t 0.86
  - valid n 171, +0.203R, t 2.11
  - all n 322, +0.144R, t 2.16
  - regime up / flat / down +0.215 / +0.094 / +0.076R
  - walk-forward 0.70, ex-best-day +0.102R, excess vs same-minute random +0.156R (t 2.59)
- Its train n is 151, so it barely passes the 150 screen. The day-of-week layer needs the frame's DatetimeIndex or a
  `date` column; the module handles both.
- **Recommendation: do not deploy.** At most it is a backlog note for forward tracking.

## Exits not tested
- t05s05 is not in the frames or in LabStrategy.GEOMS.
- Scale-out and trailing are supported live but need 1-minute paths, which were not scored here.
- Hold-to-close and time exits need live code.

## Files
- PLAN.md: the pre-declaration.
- build.py: the superset build (scratch).
- common.py, scan.py: the grid.
- gate.py: the gates.
- scan_all.csv.gz: all 47,820 configurations.
- results.csv: the 221 screen passers with every gate.
- finalists.csv, gate_summary.json.
- modules/.
