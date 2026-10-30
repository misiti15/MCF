# rdt1030 / F6 index-native: pre-declaration

*Educational only — not financial advice.*

Written 2026-10-30, **before any configuration is scored**. No outcome column has been read. Research only: no config/,
mcf/, ledger or backlog writes; nothing is committed.

Source: the owner's Reddit post of 2026-10-30 (NQ/GC futures trader). The post's ideas are index-futures native, so this
family runs them on the index ETFs themselves. Design: `../DESIGN.md` sections 0 and F6; the table below is copied from
it unchanged.

## Signal and trade mapping (DESIGN F6)
- The signal is computed on QQQ (or SPY) 5-min lab rows with exactly the F1-A / F3-A / F4 rules (the entry code is
  imported from `../F1/build.py`, `../F3/build.py` and `../F4/build.py`, not rewritten).
- It is traded on TQQQ / SQQQ (or SPXL / SPXS) at the **same row's close**. The QQQ stop and target are mapped by
  percentage: `level_ETF = e_ETF × (1 + 3 × (level_QQQ / e_QQQ - 1))`. A QQQ short is a **long** SQQQ with the mirrored
  percentage. So R_ETF = 3 × e_ETF × R_QQQ / e_QQQ and the target multiple (in R) is unchanged.
- The sim (F4's patched copy of the top5_1028 sim: per-trade R and target, 1c + 1 bp per side × ToD multiplier on entry,
  1c + 1 bp on every exit, +2c on stop exits, ×3 extended tier, gap-through stop fill) then runs on the ETF's own 5-min
  bars to 15:55, with the ETF's prices and costs.
- The 1R/2R switch, risk guard (0.03-1.0 ATR) and break-even use the **signal symbol's** ATR_d and R, as in F1/F3/F4.
- No adv filter on F6 trades (DESIGN 0.1). The OR-width floor (>= 0.05 ATR_d, all three head rows present) still applies.

## 1-min rows (F6-05 / 06)
- OR15 from the 5-min head rows (0935-0945). The 1-min frames (`frames_tf/1min`, real opens) start at the 0950 bar. A day
  is skipped for a side if the 0950 5-min close is already beyond the OR on that side.
- Fresh break = the first 1-min close beyond the OR level (from 0950). The FVG is the F1-A one on 1-min candles (i-2, i-1,
  i consecutive minutes; gap >= 0.05 ATR_d and >= $0.02); the break must be candle i-1 or i; `close[i]` beyond the level;
  signal rows to 1100. Entry at the 1-min close; stop at candle i-2's extreme.
- ETF path: 1-min TQQQ / SQQQ rows through 15:00, then the 5-min tail rows 15:05-15:55.
- The signal function is a copy of F1's `signals` with the bar step (5 → 1 min) and the earliest row (0955 → 0952) as
  parameters; with (5, 0955) it must reproduce F1's output exactly (checked in `build.py check`).

## Configurations (18 counted)
| row | rule, signal symbol → traded | side | plain-English name |
|---|---|---|---|
| F6-01 / 02 | F1-A QQQ → TQQQ / SQQQ | L / S | Nasdaq 15-min Opening Range Break with Gap, Long via TQQQ / Short via SQQQ |
| F6-03 / 04 | F1-A SPY → SPXL / SPXS | L / S | S&P 15-min Opening Range Break with Gap, Long via SPXL / Short via SPXS |
| F6-05 / 06 | F1-A with **1-min** FVG on QQQ → TQQQ / SQQQ | L / S | Nasdaq 15-min Opening Range Break with 1-min Gap, Long via TQQQ / Short via SQQQ |
| F6-07 / 08 | F3-A QQQ → TQQQ / SQQQ | L / S | Nasdaq 5-min Opening Range Break with Gap, break-even, 2 tries, Long via TQQQ / Short via SQQQ |
| F6-09 / 10 | F4 PDL-long (F4-01) → TQQQ / PDH-short (F4-09) → SQQQ, on QQQ | L / S | Nasdaq Prior-Day-Low Sweep then 15-min Gap, Long via TQQQ / Prior-Day-High Sweep, Short via SQQQ |
| F6-11 / 12 | F4 ORL-long (F4-05) / ORH-short (F4-12) on QQQ → TQQQ / SQQQ | L / S | Nasdaq Opening-Range-Low Sweep then 15-min Gap, Long via TQQQ / Opening-Range-High Sweep, Short via SQQQ |
| F6-13 / 14 | F4-01 / F4-09 on SPY → SPXL / SPXS | L / S | S&P Prior-Day-Low Sweep then 15-min Gap, Long via SPXL / Prior-Day-High Sweep, Short via SPXS |
| F6-15 / 16 | F1-A on {QQQ, SPY, TQQQ, SQQQ}, each traded as itself (the requested index-only row) | L / S | Index ETFs (QQQ/SPY/TQQQ/SQQQ) 15-min Opening Range Break with Gap, Long / Short |
| F6-17 / 18 | F1-A on QQQ traded as QQQ (unlevered reference) | L / S | Nasdaq 15-min Opening Range Break with Gap traded as QQQ, Long / Short |

- F6-07 / 08: F3-A runs once on QQQ (max 2 trades per day, QQQ-from-open context, BE at +1R). Trade 1's exit row (on the
  ETF) is mapped back to the QQQ row with the same time for the "trade 2 after trade 1's exit" rule. Every trade is
  attributed to its own side (L → TQQQ, S → SQQQ), as in F3.
- F6-15 / 16: shorts are real shorts of the symbol itself (a short of SQQQ is a short, not a TQQQ long).

## Bar (BAR90, rules 21-22)
- N = 2,000 + every config scored in this swarm (108 declared + every family's dated rework rows at score time; 24 as of
  this writing → N = 2,132), t_req = 0.9 × max(1.5, sqrt(2 ln N)) ≈ 3.52.
- Pass: day-clustered t >= t_req, WF >= 54% positive months, avg R > 0 on TRAIN and VALID separately, >= 3 trades per
  session, avg R > 0 on SPY up and down sessions, avg R above the random control.
- **These rows cannot meet >= 3 trades/session** (1-4 instruments). They are reported in full and judged on every other
  gate; a pass on every other gate would be flagged "needs owner trade-rate exception", never relabelled as a pass.
- Random control (rule 6): per trade, 5 random lab-universe symbols (adv20 >= $95M, OR defined) at the same signal row
  (seed 20261030), same side as the traded instrument, same R in ATR units of the traded instrument, same target
  multiple and BE, same sim and costs. For the 1-min rows the pool is the 1-min core symbols (adv20 >= $95M) at the same
  minute on the 1-min path.

## Sanity check before scoring
2025-06 (TRAIN), signal features only: trades per session per row, median R / ATR_d, median cost / R, median signal
time. If a row has fewer than ~10 trades over the 17 open months it is still scored and reported, with that caveat; no
threshold is changed after seeing the counts unless it is written here as a dated amendment and counted.

## Splits and harness
TRAIN = 2024-10, 2025-03..12; VALID = 2026-01..03, 2026-07..2026-09-15. The `_cut` monkeypatches and asserts are those
of F1/F3/F4 (pdl1030/combo). Locked block 2024-11..2025-02 and HOLD months 2026-04..06, 2026-09-16..10 are never loaded
(the 1-min loader reads only the open month folders and cuts at 2026-09-15). Outcome columns of the frames are never
loaded. Scratch: `/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F6/`, deleted after the report.
