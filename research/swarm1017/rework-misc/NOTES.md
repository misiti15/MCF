# swarm1017 / rework-misc — NOTES (2026-10-17)

*Educational only — not financial advice. Backtest results on the open 2-year history (rule 7: not paper, not live).
Research only — no config, ledger or backlog edits. The locked block 2024-11..2025-02 was never loaded.*

## Failures first
- **0 of 31,662 configurations pass.** No variant of heat_fade_short(-FD), heat_fade_long(-FD), orb20_a,
  intraday_momentum, LIQ-orl-sweep or LIQ-pdl-sweep reaches its lineage t bar. **No candidate is proposed.**
- Per family (configs / screened / all quality gates except the bar / pass the bar; bar = max(1.5, sqrt(2 ln N_lineage))):
  | family | configs | screen | quality | pass | bar | best quality t |
  |---|---|---|---|---|---|---|
  | HS heat short | 7,116 | 383 | 5 | 0 | 4.57 | 2.83 (fo<-1 & Monday) |
  | HL heat long | 7,740 | 340 | 59 | 0 | 4.57 | 3.85 (Tuesday, refire, 13:00-15:00) |
  | ORB (orb20 lab version) | 6,816 | 38 | 0 | 0 | 4.20 | none; best raw t 2.13 fails regime (up days only) |
  | IM intraday momentum | 1,098 | 12 | 0 | 0 | 3.75 | none; best raw t 1.30 |
  | LIQ sweeps | 8,892 | 97 | 0 | 0 | 4.41 | none; best raw t 2.31 fails regime (long beta) |
  Screen = n_train >= 150, n_valid >= 50, n >= 200, exp > 0 in train and valid (production costs, ToD entry costs).
- Parent cells re-scored on the lab geometries (all after costs, train / valid):
  heat_fade_short 09:50-10:30 t1s1 n 14,433: -0.005 / +0.022R, t 0.41; its -FD window (09:50-15:00) n 75,136: -0.043 / -0.024, t -2.31.
  heat_fade_long 11:05-13:30 t1s1 n 14,460: -0.066 / -0.028, t -1.16; -FD n 23,506: -0.046 / -0.022, t -1.30.
  orb20 lab version (agree + VWAP + rvol 1.5, 09:55-11:30) n 29,798: -0.053 / -0.075, t -3.9; the fade side is worse (-0.155 / -0.103).
  intraday_momentum ETFs at 10:30..15:00 entries: -0.06..+0.03R, no entry time positive in both halves at t > 0.6.
  LIQ ORL x0.15 open k15 with lab geometry n 13,754: -0.041 / -0.042 (t1s1); PDL x0.05 open k15 (without the VWAP-room filter) n 34,731: -0.100 / -0.107.
- Live week (paper, research/swarm1017/week, 10-06..10-16): heat_fade_short p/t1 82 tr -0.42R, -FD 240 tr -0.12R; heat_fade_long p/t1
  111 tr -0.27R, -FD 91 tr -0.52R; LIQ-orl 120 tr -0.04R; orb20_a 14 tr; intraday_momentum 5 tr; LIQ-pdl 1 tr. Consistent with history: these
  parents do not have positive expectancy after costs.

## What was learned
1. **heat_fade_short has relative skill but no absolute edge.** Its parent cell beats random shorts at the same minute by +0.095R
   (excess day-t 6.3) - but random shorts lose about -0.09R after costs, so the trade nets ~0. Every HS variant that is positive
   is short-beta (down sessions carry it; up sessions <= ~0). The only path left is an index-hedged (market-neutral) version,
   which needs pair-order code and cannot be scored with lab geometries. -> backlog hypothesis.
2. **heat_fade_long improves monotonically with a stricter threshold in the afternoon.** T >= 65-75, bar close 13:00-15:00,
   t05s1 is positive in train and valid for every gate (none / fo- / gap+) - a real plateau, but small: best t 1.93
   (T75, n 1,860, +0.045R). Far below 4.57.
3. Most "quality" near-misses are day-of-week cuts (Friday, Monday, Tuesday) picked from 37 filters x 666 pairs. With 31,662 tries,
   ~1,600 configurations clear p = 0.05 by luck; these splits are the most likely of all to be noise.
4. ORB and LIQ variants are long-beta: positive in up sessions, negative in down sessions; no decision-time gate (SPY from open,
   breadth) rescued the down-session side with enough trades.
5. intraday_momentum cannot be tested as live (15:30 entry, hold to close): frames stop at 15:00 and LabStrategy rejects
   bars after 15:00. Earlier entries do not work.

## Near-misses (fail the t bar; written as modules only for an optional Testing forward test)
Parity: `verify.py` runs each module's `mask(df)` on the raw open frames through `gates.lab_trades` -> verify.json (exact match with the scan).
| module | n (tr/va) | exp tr / va | t vs bar | up / down | WF | excess t |
|---|---|---|---|---|---|---|
| NM-HL-T75-pm-t05s1-long | 893 / 967 | +0.052 / +0.038 | 1.93 / 4.57 | +0.042 / +0.039 | 0.75 | 4.39 |
| NM-HL-atrhi-fri-midday-t05s1-long | 967 / 895 | +0.092 / +0.065 | 3.08 / 4.57 | +0.067 / +0.078 | 0.88 | 3.80 |
| NM-HS-fo1-mon-open-t05s1-short | 277 / 308 | +0.197 / +0.079 | 2.83 / 4.57 | +0.055 / +0.225 | 0.92 | 4.58 |
All are type lab (SIDE/GEOM/mask), min_adv 125M, live-frame features only (heat components, fromOpen, gap, atrPct, atr_d, tod, date/index day-of-week).
Full de-duplicated near-miss list: nearmiss.csv (21 rows; rows with spy/breadth filters need live code).

## Files
PLAN.md (pre-declared grid and gates; arithmetic of three stage counts corrected before scoring), build.py (per-month supersets),
common.py, scan.py (all configurations), gate.py (screen + regime / walk-forward / same-minute random / ex-best-day / bar),
dedupe.py, verify.py, modules/ (3 near-miss modules + liqx.py, the LIQ sweep port used by build.py),
scan_all.csv.gz (every configuration), results.csv (screened rows with all gates), nearmiss.csv, verify.json.
Split: train = 2024-10 + 2025-03..2025-12, valid = 2026-01-01..2026-10-07. Exits: lab geometries only (no scale-out / trail / time exits scored).
