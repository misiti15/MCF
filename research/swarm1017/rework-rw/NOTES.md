# swarm1017 / rework-rw — results (2026-10-17)

*Educational only — not financial advice. Backtest on the open 2-year history at production cost (prod_r with
time-of-day entry costs). Live numbers are paper (rule 7). The locked block 2024-11..2025-02 was not loaded.*

## Failures first
- **No variant of RW1-RW7 (-FD) or exhaustion_short (-FD) clears the try-count bar, and nothing is ready for live funds.**
  - Configurations scored: **132,892**. That is the declared 132,884 plus 8 first-signal parent diagnostics, which are
    counted.
  - By lineage: MF 69,848, exhaustion 32,620, NS 30,424.
  - Bars, as day-clustered t >= sqrt(2 ln N_lineage): **MF 4.95** (N ~203,800), **NS 4.83** (~114,400),
    **exhaustion 5.25** (~967,100).
  - **Gates plus bar: 0.** One config reaches its bar on t (RW6 short, brd>.65 & slope<0, t05s1, 09:50-11:00,
    t 5.25). It fails the regime gate: only 8 trades fall in down sessions, below the n >= 30 the gate needs.
- The family is negative, not just flat:
  - 90,856 configurations have n >= 200. Only 9.8% of them have exp > 0. 45,250 have t <= -2.
  - Only **330 reach t >= 2. A zero-mean null would give about 2,089.** So the search mostly finds losers.
  - The median exp is negative for every parent and side: -0.020 to -0.111R.
- **Screen:** 2,176 configs pass it (exp > 0 on train and valid, n_tr >= 150, n_va >= 50, n >= 200). On each gate
  alone: regime 632, walk-forward 700, beats same-minute random 1,299. All gates: **88**, and 31 after de-duplication.
  The best gate-passer has t 3.83 against a bar of 5.25.
- **Thresholds (Stage A).** Tighter or looser thresholds, and dropping each condition in turn, rescue nothing. One
  Stage A config passes the gates (G-EXH, RSI5 > 90, sma20 > 2, adv >= 300M, short t05s1, 13:00-15:00). It has
  t 1.90 and train t 0.71.
- **Opposite side (long).** It is worse than short for every parent at the median. The exception is the G-RW6 grid
  (-0.037R long vs -0.081R short), and that is still negative.
- **Refire vs first-signal:** no difference (median -0.069R both).
- **Geometry:** t05s1 is the least bad at -0.060R, then t1s1 at -0.066R and t1s05 at -0.073R. t05s05 was not tested:
  the frames have no outcome columns for it and LabStrategy does not support it.
- **Time windows:** every window is negative. 09:50-10:30 is the worst (-0.080R). 11:10-15:00 (the exhaustion
  prefilter's live cut-off) is the least bad (-0.054R).

## The live week's "SPY down at entry" read does not survive the history
- Live paper, this family, 2026-10-06..16, from week/rework_trades.csv: 517 trades.
  - With SPY below its open at entry: n 338, +0.113R. With SPY above its open: n 179, -0.334R.
  - Daily P/L tracked the tape: +30R on 10-14 and +23R on 10-16 (SPY down), -30R on 10-13 and -47R on 10-15 (SPY up).
- Over two years the same signal-time gate does not help. These are the parents short, t1s1, full day:

| parent | spy<0 | spy<-0.5 | spy>0 | spy>0.5 | brd<.35 | brd>.65 |
|---|---|---|---|---|---|---|
| RW1 | -0.029 | -0.071 | -0.069 | -0.090 | -0.061 | -0.046 |
| RW2 | -0.042 | -0.091 | -0.064 | -0.011 | -0.096 | -0.045 |
| RW3 | -0.060 | -0.101 | -0.080 | -0.039 | -0.103 | -0.016 |
| RW4 | -0.036 | -0.076 | -0.007 | -0.024 | +0.036 | -0.039 |
| RW5 | -0.017 | -0.110 | -0.089 | -0.092 | -0.053 | -0.054 |
| RW6 | -0.057 | -0.162 | +0.002 | +0.045 | -0.138 | +0.082 |
| RW7 | -0.040 | -0.082 | -0.082 | -0.107 | -0.087 | -0.046 |
| EXH | -0.052 | -0.090 | -0.066 | -0.008 | -0.096 | -0.046 |

  - "Short only when SPY is red" stays negative for every parent. "SPY < -0.5%" is worse.
  - The week's result came from which days the market fell, decided by end-of-day direction. It was not a rule that
    was knowable at the signal.

## Week-over-week (live paper, this family; a diagnosis, not evidence)
| window | trades | avg R (actual) | sum R |
|---|---|---|---|
| 10-06..10-09 | 38 | -0.110 | -4.2 |
| 10-12..10-16 | 479 | -0.036 | -17.3 |
| 10-12..10-13 | 181 | -0.133 | -24.1 |
| last 3 days, 10-14..10-16 | 298 | +0.023 | +6.7 |

- Per trade, this week is less bad than last week. Last week had only 38 trades, because Testing 1 started on 10-09.
- The last 3 days are positive (+0.023R), but two of those three sessions were SPY-down. The history says that is
  regime, not edge.
- Per setup this week: RW3-FD n 34, +0.37R; RW5-FD n 31, +0.42R; RW7-FD n 156, +0.04R; RW1-FD n 32, -0.09R;
  RW4-FD n 25, -0.08R; RW2-FD n 119, -0.15R; exhaustion_short n 38, -0.08R; exhaustion_short-FD n 20, -0.29R;
  RW6-FD n 35, -0.56R.
- Exit replays for the whole family:

| exit | avg R |
|---|---|
| actual | -0.042 |
| replayed base | +0.001 |
| trail 1R | -0.003 |
| hold, no target | -0.004 |
| stop 0.5R | -0.019 |
| BE at 0.5R | -0.011 |
| scale-out at 0.5R + BE | -0.025 |

  No live-supported exit change turns the family positive.

## Near-miss candidates (pass every quality gate, FAIL the try-count bar; not for live funds)
Ranked by min(train t, valid t), with trades overlapping less than 60%. Each was re-scored from its module on the raw
frames (verify.py / verify.json, an exact match):

| module | parent | side / geom / window | n tr / va | exp tr / va | t all | bar | up / down exp | WF | live |
|---|---|---|---|---|---|---|---|---|---|
| RWR1-exh150-gapdn-spyup-pm-short-t05s1 | RW2 | short t05s1 13:00-15:00 | 326 / 328 | +0.122 / +0.182 | 3.83 | 5.25 | +0.149 / +0.197 (n down 64) | 0.80 | spy_fo code needed |
| RWR2-exh-monday-slopedn-long-t1s1 | EXH | long t1s1 09:50-15:00 | 267 / 134 | +0.171 / +0.231 | 3.63 | 5.25 | +0.261 / +0.039 (n down 40) | 0.67 | lab-ready |
| RWR3-ns3-adv150-qqqup-early-short-refire | RW4 | short t1s1 09:50-10:30, refire cd1 | 157 / 198 | +0.251 / +0.171 | 2.97 | 4.83 | +0.091 / +0.290 (n 117/113) | 0.77 | qqq_fo code needed |
| RWR4-ns2-up3-qqqup-slopedn-am-short-t05s1 | RW6 | short t05s1 09:50-11:00 | 383 / 262 | +0.125 / +0.108 | 3.15 | 4.83 | +0.116 / +0.246 (n down 58) | 0.78 | qqq_fo code needed |

- The other 27 de-duplicated gate-passers are in finalists.csv. All have t <= 2.2, and none is written as a module.
- Concentration:
  - RWR1's 654 trades fall on 78 sessions, about 8 per session, mostly up-tape afternoons.
  - RWR2 is a day-of-week by filter pair, and most of its result comes from up sessions.
  - RWR3 has the widest spread (127 sessions, both regimes) and the cleanest same-minute excess (+0.27R, t 4.2).
    It is still far below its bar.
- Expected false positives: at 132,892 tries, several configs reaching t ≈ 3-4 is what noise produces. These are
  **backlog records**, not edges.

## Live-runner notes
- `spy_fo` / `qqq_fo` / breadth are not in the LabStrategy frame. Using them needs code (read ctx.peers['SPY'/'QQQ'];
  breadth needs the whole poll universe). The modules fail safe: without the column they produce no trades.
- Day-of-week needs the frame's DatetimeIndex or a `date` column.
- Hold-to-close and time exits are not supported live. Scale-out (live_scale_out + scale_out_r) and trailing are
  supported, but they cannot be scored on the frames, which carry no 1-minute paths.
- exhaustion_short-FD's live prefilter new_high_100m blocks entries before 11:10. In history, 11:10-15:00 is still
  negative (Stage A medians).

## Files
- PLAN.md (pre-declared), build.py (superset, kept in scratch and deleted), common.py, scan.py → scan_all.csv.gz
  (every configuration), gate.py → results.csv (2,176 screen passers with all gates), finalists.csv (31),
  gate_summary.json, verify.py → verify.json, modules/RWR1-4.
