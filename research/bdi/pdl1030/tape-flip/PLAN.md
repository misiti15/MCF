# pdl1030 / tape-flip: pre-declaration (written before any configuration is scored)

*Educational only — not financial advice.*

Written 2026-10-30. This is research only. Nothing in config/, mcf/, ledger or backlog changes, and nothing is committed.

## Base and harness
- Parent: CWT14-failbrk-pdl-p05-long (best parent, 153 trades/session). Kernel `S6.b3_any` (PD level, side +1, p=0.05), adv20 >= 95M,
  window 09:50-15:00, first signal per symbol-day. R = 0.25 x atr_d. Exit = top5_1028 `sim`: target 0.5R, stop 1R,
  scale-out at 0.25R (p05 config), flatten 15:55. Costs are in: 1c/share + 1 bp per side x the time-of-day multiplier,
  +2c on stop exits, x3 on the extended tier. This is the same harness as swarm15 and pdl1030/why.
- Data: TRAIN = 2024-10 and 2025-03..12. VALID = 2026-01..03 and 2026-07..09-15. HOLD months and the locked block are never loaded.
- Parity first: p05 (and p10) TRAIN/VALID must match the swarm15 parent rows within 0.005R.

## Tape definitions (all read at the signal bar's close, i.e. the entry moment; the same 5-minute bar as the entry)
- TA: SPY fromOpen at the signal bar. Up if > 0, down if < 0.
- TB: SPY vwapDistPct at the signal bar. Up if > 0, down if < 0.
- TC: breadth (lib context) at the signal bar. Up if > 0.5, down if < 0.5.
- If the tape value is missing or exactly at the boundary, take no trade.

## Short legs (taken only when the tape is down)
- Sx (immediate flip): short at the close of the same signal bar. The R, mirrored 0.5R target, 1R stop, 0.25R scale-out,
  costs and 15:55 flatten all match the long.
- Sb (re-break flip): after the signal bar, short at the close of the first bar (<= 15:00) that closes back below PDL,
  meaning the reclaim failed. The R is the same as the signal's R and the exits mirror the long.
  This is known at that bar's close.

## Configurations (16)
For each tape T in {TA, TB, TC}:
1. T-G: long when the tape is up, skip when it is down.
2. T-Sx: Sx short when the tape is down, nothing when it is up (the short leg on its own).
3. T-Sb: Sb short when the tape is down, nothing when it is up.
4. T-F: long when up plus Sx short when down (immediate tape flip).
5. T-B: long when up plus Sb short when down (re-break tape flip).
That gives 15 configurations. Config 16 (K): the T-F or T-B with the best TRAIN avg R among the 6 flips, with a cost floor added
(skip when the round-trip cost estimate is > 10% of R, the swarm15 K2 rule). It is chosen on TRAIN only.

N = 121459 + 3 x 16 = 121507. Bar t >= 0.9 x sqrt(2 ln N) = 4.355. Also required: walk-forward months positive >= 54%,
avg R > 0 on TRAIN and on VALID, beats p05 on both (-0.0677 / -0.0675), and exposure >= 25 trades/session (or >= 76.6).
Reported for each config: trades/session, up/down session R (lib.regimes), avg R without the best day, and the best day's share.
