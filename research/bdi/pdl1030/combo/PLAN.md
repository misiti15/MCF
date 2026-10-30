# pdl1030 / combo: pre-declaration (written 2026-10-30 ~05:30 UTC, before any configuration is scored)

*Educational only — not financial advice.*

Research only. No repo, config/, mcf/, ledger or backlog writes; nothing committed.
Lineage: Failed Prior-Day-Low Break Longs (CWT14-failbrk-pdl-p05 / p05-lowvol / p10 / p10-lowvol). N_prior 121566.

## Family: combine the best pieces from earlier rounds, no new knobs
Pieces (each already defined and scored in an earlier pdl1030 / swarm15 round):
- **S3** (swarm15 / symbol-quality): stop x3 (0.75 ATR) at the same $ risk; target 0.5R1 and 0.25R1 scale-out prices kept; r in 3R1 units.
- **cost5 / cost10**: skip when the round-trip cost estimate > 5% (symbol-quality Q08) / > 10% (swarm15 K2, tape-flip K) of R1 = 0.25 ATR.
  Known at entry (price, tier, time of day, ATR).
- **SPY above VWAP** (why, tape-flip TB): SPY vwapDistPct > 0 at the signal-bar close.
- **Breadth flip** (tape-flip TC-F): long if breadth > 0.5 at the signal-bar close, else Sx short at the same close (mirrored exits).
- **SPY-VWAP flip** (tape-flip TB-F): long if SPY vwapDistPct > 0, else Sx short.
- **Tape score sizing** (merge-size W3): w = 0.25 + 0.25[SPY above VWAP] + 0.25[breadth >= 0.5] + 0.25[SPY gap <= -0.5%].
- **SPY gap <= -0.5%** (why angle 3): SPY open gap, known at the open.
Missing tape / exactly at the boundary -> no trade (as tape-flip).

## Configurations (6 combos + 4 parity re-scores = 10 counted)
| id | rule |
|----|------|
| PAR-P05, PAR-P10, PAR-P05S3 | parity re-scores (swarm15 / symbol-quality values) |
| PAR-TCF | short-leg harness check: tape-flip TC-F re-score (-0.0392 / -0.0498) |
| K1 | p05 S3 + cost5 + long only when SPY above VWAP |
| K2 | p05 S3 + cost5 + breadth flip (long if breadth > 0.5, else S3 short) |
| K3 | p05 S3 + cost5 + SPY-VWAP flip (long if SPY above VWAP, else S3 short) |
| K4 | p05 S3 + cost5, weighted by tape score W3 (avg R = sum(w r)/sum(w)) |
| K5 | p05 S3 + cost10 + breadth flip (keeps the most exposure) |
| K6 | p05 S3 + cost5 + long only when SPY above VWAP OR SPY gap <= -0.5% |

Nothing is added after scoring; any addition would be disclosed and counted.

## Harness
Same as symbol-quality/build.py: CWT14 `S6.b3_any` (PD level, side +1, p=0.05, no vr cap), adv20 >= 95M, signal 09:50-15:00,
first signal per symbol-day, top5_1028 `sim` (costs 1c + 1 bp per side x time-of-day multiplier, +2c stop exits, x3 extended tier),
p05 exits (target 0.5R1, scale 0.25R1, flatten 15:55). Short leg = the same sim with side -1 at the same signal-bar close.
TRAIN <= 2025-12 (2024-10, 2025-03..12); VALID 2026-01..03 + 2026-07..09-15. HOLD months and the locked block never loaded.

## Bar (rule 22, BAR90)
N = 121566 + 3 x 10 = 121596 -> t_TV >= 0.9 x sqrt(2 ln N) = 4.355. Walk-forward >= 54% of months positive, avg R > 0 on TRAIN
and on VALID, beats p05 (-0.0677 / -0.0675) on both, exposure >= 76.6/sess or >= 25/sess (flip legs count).
Reported per row: train/valid avg R, day-clustered t, trades/session, wf%, up/down-day R, avg R w/o best day + best-day share.
