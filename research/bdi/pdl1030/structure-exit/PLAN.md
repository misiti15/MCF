# pdl1030 / structure-exit: pre-declaration (written before any configuration is scored)

*Educational only — not financial advice.*

Written 2026-10-30 ~05:15 UTC (before the 09:30 ET open). Research only: nothing in config/, mcf/, ledger or backlog
changes; nothing is committed.

## Base and harness
- Entry: unchanged CWT14 `S6.b3_any` (PD level, long, p=0.05; p10 only in row D1), adv20 >= 95M, 09:50-15:00, first signal
  per symbol-day, entry at the signal bar's close. Exposure is therefore 100% of the parent's (153 trades/session for
  p05, 85.7 for p10). No entry filter is added in this family.
- Exits: a generalised copy of the top5_1028 simulator (`sim2`, numba) run on cached 5-minute paths (entry bar ..
  15:55). Stop first, +2c on stop exits, market exits 1c + 1 bp, entry 1c + 1 bp x time-of-day multiplier, target limits
  free, x3 on the extended tier, flatten 15:55. Parity: sim2 with the parent settings must reproduce swarm15's parent
  rows (p05 TRAIN -0.0677 / VALID -0.0675; p10 -0.0880 TV) within 0.005R, else stop.
- Same $ risk: R unit per trade = entry - stop price (the structural distance); r = P/L per share / R unit, costs / R unit.
- Data: TRAIN = 2024-10, 2025-03..12. VALID = 2026-01..03, 2026-07..09-15. HOLD months are never loaded (2026-09 rows after
  09-15 dropped at load) and the locked block 2024-11..2025-02 is never loaded.

## Quantities (all known at the signal bar's close = entry time)
e = entry price (signal-bar close); A = daily ATR (atr_d, known pre-open); LOD = day low through the signal bar
(includes the break bar); PDL = prior-day low; depth = PDL - LOD (>= 0.05A by construction); VWAP = session VWAP at the
signal bar; OPEN = today's open; PC = prior close; R0 = 0.25A (parent risk).

## Configurations (18 incl. 2 parity rows; every one is counted)
Parity (counted): P05 = parent p05 (stop e-R0, target e+0.5R0, half off at e+0.25R0 then stop to e); P10 = parent p10
(no scale-out).

A. Structural stops (target and scale-out prices kept at the parent's $ levels: target e+0.125A, scale half at
e+0.0625A then stop to e):
- A1 stop = LOD - 0.02A
- A2 stop = LOD - 0.10A
- A3 stop = LOD - 0.25A
- A4 stop = min(LOD - 0.05A, e - 0.25A) (structural, never tighter than the parent)
- A5 = A3 hard stop plus a close-based structural exit: exit at the close of the first bar that closes below LOD
  (market exit cost)
-> STOP* = the A row with the best TRAIN avg R (selection on TRAIN only).

B. Structural targets, on STOP*, single target, no scale-out (if the structural level is not above e + 0.125A, the
target falls back to e + 0.125A, the parent's price):
- B1 target = VWAP
- B2 target = today's OPEN
- B3 target = PC (prior close)
- B4 target = PDL + 1 x depth (measured move)
- B5 target = PDL + 2 x depth
- B6 target = e + 1.0 x (e - stop) (1:1 in structural R)
-> TGT* = the B row (or "parent target/scale" = best A row itself) with the best TRAIN avg R.

C. Management on STOP* + TGT*:
- C1 break-even after +0.5R (structural R)
- C2 stop raised to PDL - 0.02A once MFE >= 0.25R ("level must hold" trail; only if that is above the current stop)
- C3 hard time stop 60 min (12 bars) unconditional, market exit
- C4 scale-out: half at the parent target price e+0.125A, stop to e, runner to TGT*

D. Exposure / lineage check:
- D1 the best TRAIN row of A-C applied to the p10 entry.

N for this agent = 18. Bar (rule 22, BAR90): N = 121459 + 3 x 18 = 121513; t >= 0.9 x sqrt(2 ln N) = 4.355.
Pass also needs: walk-forward >= 54% of TRAIN+VALID months positive (>= 10 of 17), avg R > 0 on TRAIN and VALID separately,
and beating the best parent (p05: TRAIN -0.0677, VALID -0.0675) on both; exposure >= 76.6/session or >= 25/session
(automatic here: entries unchanged). Reported for every row: TRAIN / VALID avg R, t, trades/session, up/down-day R,
avg R without the best day, and the best day's share.
