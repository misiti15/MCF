Educational only — not financial advice

# ULT-35 EARN-FAIL — failed earnings gap, trade the reclaim against the gap (round 4) — **FAIL**

Research only: no setup, exit, config or account change. Nothing committed. **PARTLY CHECK-INFORMED** (PLAN sec. 0.6).
Any deployment would also **need an owner exception to the 4-day earnings blackout** (sec. 0.8). That question does not
come up: the candidate fails.

## Verdict
- **No grid config reaches 2.0 trades/session on FIT** (best 1.78/session, 35a). The volume plan (G3 ~1-3/session)
  was too optimistic: a gap that fully fails (back through VWAP and the open) inside 10:15-13:30 happens on only
  ~0.5 of the ~10 in-season intake reaction-day names per session.
- Per PLAN sec. 5 the best config by fit total R minus best day is carried anyway: **35f (G 6%, D 0, TX-45)**.
  It can never reach TIER A.
  - FIT: **+0.128R**, n 145, 0.85/session, w/o best day +0.085, best-day share 34%, t 1.59.
    Sub-halves A +0.043 / B +0.259.
- **CHECK, scored once:** **-0.034R**. 351 trades, 1.27/session, w/o best day -0.043, total -11.9R (-0.043R/session),
  day-clustered t -0.94 (the bar is 3.716).
- **Tier: FAIL.** TIER A misses on check avg R, w/o best day and volume. TIER B needs check > -0.02 and misses.
  **All 8 configs are negative on check** (-0.031 .. -0.149). The positive fit is not a plateau that holds.
- Signal minus random is **+0.129 on fit, -0.030 on check**. The fit edge (almost all on the long side, +0.265 vs
  random) does not reproduce: check long is -0.047 and -0.067 vs random.
- **News adds nothing on check.** The reaction-day rule (-0.034) is no better than its non-earnings twin (-0.028,
  2.5/session).

## Configurations tried
- This candidate: 8 grid + 1 bias diagnostic = **9**, as PLAN sec. 4.
- Cumulative N for the job stays **996** (round 4's 115 already includes these 9), so the t bar is 3.716.
- The random-entry control, the non-earnings twin and the side-only splits are reported but not counted.

## What was built
- **Module:** `research/ultimate_1119/modules/ULT-35.py`. It is live-ready, with the round 1-4 interface (LabStrategy
  `type: lab`, two entries in one file, "-S" = short, `context: [spy_fo]`, GEOM t1s1 or "S" + `stop_price` for TX-45).
  - Event source live: allow-list `SYMBOLS` (YAML `symbols: module`), today's reaction-day names from the calendar
    parquet (`MCF_EARN_CAL`). It uses the same `reaction_days()` / NYSE session calendar code as ULT-28. A missing
    calendar gives no trades (fail safe).
  - FAIL rule: core = s x vwapDistPct > 0 AND s x foa >= D, with foa = (close - open) / atr_d and
    open = close / (1 + fromOpen/100). Entry is on the first bar of the failure: core now, core false on the previous
    bar (exactly 5 min earlier, which must exist). Side s = -sign(gap).
  - The module still carries the default constants (G 3, D 0, EXIT T). It was not switched to the 35f pick, since
    the candidate fails.
- **Smoke test:** `round4/ULT-35/test_module.py`, 4 tests, all pass. It covers:
  - calendar: bmo / amc mapping, dmh excluded, fail-safe;
  - long and short under the live LabStrategy;
  - no signal on a holding gap, a small gap, a non-event name, or a gap-up for the long side;
  - point-in-time truncation on every feature and signal;
  - first-bar-only firing;
  - the foa formula;
  - e_rd gating;
  - **mutually exclusive with ULT-28's HOLD rule on every bar**.
- **Backtest:** `round4/ULT-35/bt.py`, adapted from round4/ULT-28/bt.py. The 1-minute walk, costs and stats are
  unchanged. Only the side rule, window, gap sign and report splits differ.
  - Costs: LR8, plus the reaction-day x1.5 entry cost (decision bar < 10:30, so the 10:15-10:25 bars) and x1.5 exit
    cost (exit < 10:30).
  - Short borrow: 5 bp of notional on reaction days (8 bp < $20); twin shorts pay 1.2 / 3 bp. Shorts are ETB only.
  - One lot per symbol, refire >= 30 min after the exit, max 2 per symbol-session, day cap 30, flat 15:50.
- **Rule conflict, stated:** the chassis' universal "no short if gap >= +0.5%" would remove every short of this
  design, since a gap-up failure is a gap-up by definition. The candidate's own short rule (ETB, RSI5 >= 25,
  earnings borrow) overrides it. The side split is reported, and the long-only and short-only checks are both
  negative anyway.
- **Locked block:** never read. Events with RD in the block are dropped. pyarrow filters and `no_locked` asserts run
  on every frame, event and 1-minute load. Forbidden columns (win_*, r_*, *heat*) are dropped and asserted absent.
- **Order:** fitsel.json was frozen at **2026-11-19T09:36:40Z** (sha256 of bt.py, the module and the earnings file)
  before any check frame, event row or trade was built. `bt.py sig check` asserts that it exists. Check was scored
  once at 09:37:41Z, and the plateau ran after it.

## FIT grid (170 sessions; selection = max fit total R minus best day among configs >= 2.0/session; none eligible)
| cfg | rule | /session | avg R | w/o best day | total R | t | A / B | long / short |
|---|---|---|---|---|---|---|---|---|
| 35a | G3 D0 t1s1 | 1.78 | -0.068 | -0.083 | -20.7 | -1.43 | -0.045 / -0.110 | +0.040 / -0.191 |
| 35b | G3 D0 TX-45 | 1.71 | +0.035 | +0.009 | +10.0 | 0.77 | +0.021 / +0.060 | +0.091 / -0.032 |
| 35c | G3 D0.5 t1s1 | 1.37 | -0.002 | -0.022 | -0.4 | -0.03 | +0.074 / -0.117 | +0.107 / -0.164 |
| 35d | G3 D0.5 TX-45 | 1.31 | +0.036 | +0.010 | +8.1 | 0.83 | +0.095 / -0.056 | +0.063 / -0.003 |
| 35e | G6 D0 t1s1 | 0.90 | +0.028 | +0.007 | +4.2 | 0.43 | -0.053 / +0.149 | +0.135 / -0.090 |
| **35f** | **G6 D0 TX-45** | 0.85 | **+0.128** | +0.085 | +18.5 | 1.59 | +0.043 / +0.259 | +0.199 / +0.046 |
| 35g | G6 D0.5 t1s1 | 0.71 | +0.004 | -0.020 | +0.4 | 0.05 | -0.083 / +0.109 | +0.069 / -0.098 |
| 35h | G6 D0.5 TX-45 | 0.67 | +0.129 | +0.075 | +14.7 | 1.43 | +0.141 / +0.114 | +0.131 / +0.127 |

- The plain fit-total-R pick (the task wording) is also 35f, so both rules agree.
- Fit leans long and on TX-45. Every t1s1 cell is ~0 or negative, so the 45-min hold carried the fit result.

## Fit pick 35f: FIT vs CHECK
| | FIT | CHECK (once) |
|---|---|---|
| trades (/session) | 145 (0.85) | 351 (1.27) |
| sessions traded | 63 of 170 | 109 of 276 |
| win | 0.503 | 0.499 |
| avg R (per 2u, TX-45) | **+0.1279** | **-0.0338** |
| avg R per 0.25-dATR unit | +0.256 | -0.068 |
| avg R w/o best day | +0.0853 | -0.0430 |
| best day (share of total R) | 2024-10-30 +6.3R (34%, no 1-day tag) | 2026-04-21 +3.0R (n/a, total < 0) |
| total R (R/session) | +18.5 (+0.109) | -11.9 (-0.043) |
| worst day (/ trade-session) | -2.57 (-1.12) | -4.91 (-1.52) |
| day-clustered t | 1.59 | -0.94 (bar 3.716) |
| w/o 2025-04-03..04-09 | +0.1279 (no trades in those dates) | n/a (no such dates) |
| sub-halves A / B | +0.043 / +0.259 | — |
| first / second half | +0.030 / +0.262 | -0.008 / -0.057 |
| long / short | +0.199 (n 78) / +0.046 (n 67) | -0.047 (n 209) / -0.015 (n 142) |
| SPY up / flat / down | +0.051 / +0.324 / +0.080 | +0.017 / -0.109 / +0.023 |
| entry 10:15-10:55 / 11:00-11:55 / 12:00-13:30 | +0.297 / +0.086 / -0.069 | -0.020 / -0.010 / -0.071 |
| gap 6-10 / 10+ % | +0.031 / +0.278 | -0.020 / -0.058 |
| surprise sign with the trade side / with the gap | +0.137 / +0.122 | -0.080 / +0.011 |
| season / off-season sessions (>= 5 RD names) | +0.132 (n 140) / +0.016 (n 5) | -0.038 (n 339) / +0.090 (n 12) |
| median hold; exit mix | 45 min; time 132 / stop 13 | 45 min; time 302 / stop 49 |
| bias diagnostic (signal-close fill, no borrow, no surcharge) | +0.146 | -0.027 |
| same-name random control (avg R; signal minus random) | -0.001; **+0.129** | -0.004; **-0.030** |
| signal minus random, long / short | +0.265 / -0.031 | -0.067 / +0.025 |
| non-earnings twin (same rule, no report in RD-5..RD+1) | +0.020 (2.07/session) | -0.028 (2.48/session) |
| long only / short only | +0.199 (0.46/s) / +0.046 (0.39/s, w/o best day -0.025) | -0.047 (0.76/s) / -0.015 (0.51/s) |

- **Bars:**
  - check avg R > 0: no.
  - w/o best day > 0: no.
  - fit avg R > 0: yes.
  - >= 2/session on check: no (1.27).
  - TIER B (fit > 0 and check > -0.02): no (-0.034).
  - BEATS: no on avg R, w/o best day, total R/session and t. Worst day / trade-session -1.52 would pass.
- **Bias fixes cost** ~+0.007R on check (bias diagnostic -0.027 vs -0.034). The fill, borrow and surcharge are not
  what sinks it.
- **Fit was thin and lopsided.** 145 trades in 63 sessions; A +0.043 vs B +0.259; long carried it. The early-entry
  bucket (10:15-10:55, +0.297 fit) is -0.020 on check.

## CHECK plateau (diagnostic after the single score; never used to re-select)
| cfg | /session | avg R | w/o best day | total R | t | long / short | 1st / 2nd half |
|---|---|---|---|---|---|---|---|
| 35a G3 D0 t1s1 | 2.43 | -0.078 | -0.087 | -52.2 | -2.03 | -0.025 / -0.146 | +0.013 / -0.150 |
| 35b G3 D0 TX-45 | 2.35 | -0.031 | -0.037 | -19.9 | -1.17 | -0.028 / -0.035 | +0.006 / -0.060 |
| 35c G3 D0.5 t1s1 | 1.76 | -0.149 | -0.161 | -72.7 | -3.45 | -0.121 / -0.187 | -0.108 / -0.182 |
| 35d G3 D0.5 TX-45 | 1.68 | -0.063 | -0.072 | -29.0 | -1.89 | -0.045 / -0.086 | -0.037 / -0.082 |
| 35e G6 D0 t1s1 | 1.31 | -0.062 | -0.076 | -22.3 | -1.22 | -0.019 / -0.123 | +0.019 / -0.134 |
| **35f G6 D0 TX-45** | 1.27 | -0.034 | -0.043 | -11.9 | -0.94 | -0.047 / -0.015 | -0.008 / -0.057 |
| 35g G6 D0.5 t1s1 | 0.97 | -0.095 | -0.113 | -25.4 | -1.61 | -0.100 / -0.087 | -0.076 / -0.113 |
| 35h G6 D0.5 TX-45 | 0.91 | -0.062 | -0.072 | -15.5 | -1.53 | -0.058 / -0.068 | -0.042 / -0.081 |

- 8 of 8 are negative. Waiting for a deeper reclaim (D 0.5) is worse in every pairing, and t1s1 is worse than TX-45 in
  every pairing. The "failed gap" entry is late: the snap-back is mostly done by the time price is back through VWAP
  and the open.

## Read and leads (optimistic, honest)
- Together with ULT-28 (the gap-holding mirror, -0.048 check) and ULT-30 (day-2, -0.034), this closes the
  "price-state trigger on reaction-day names" family on this chassis. Holding or failing, the 5-min price trigger does
  not beat random bars on the same names on check.
- The one consistent lead across rounds 4's earnings candidates stays the one ULT-28/ULT-30 found: **random with-gap
  bars on reaction-day names earn > 0 in both halves** (ULT-28 +0.091 / +0.044; ULT-30 +0.034 / +0.051). ULT-35's
  against-gap random control is ~0 in both halves (-0.001 / -0.004), which fits that lead: the gap direction carries
  the drift, and fading a failed gap does not. Any next earnings step should start from that unconditional with-gap
  base (a scheduled-time entry, not a price trigger), tested as a new pre-registered candidate.
- Caveats that favour this candidate and still did not save it: today's symbol list (survivorship flatters longs),
  today's ETB flag, report dates fetched after the fact.

## Rule-change context (owner 2026-11-02)
Both halves are scored with one fixed rule set (today's LR8 costs, the round-4 chassis). No live rule change applies
inside the windows. The candidate is research only and has no live record.

## Files
- `research/ultimate_1119/modules/ULT-35.py`: module.
- `research/ultimate_1119/round4/ULT-35/`: `bt.py`, `test_module.py`, `fit_grid.json`, `fitsel.json` (frozen),
  `fit_random.json` (random control, twin, side-only fit, bias diagnostic), `check_once.json`, `check_plateau.json`,
  `check_trades.csv.gz`.
- The intermediate signal / walk parquet (scratchpad work dir) was deleted after scoring (disk).

Educational only — not financial advice.
