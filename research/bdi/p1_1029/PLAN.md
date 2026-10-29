Educational only — not financial advice.

# p1_1029 pre-declaration (owner Prompt 1: asymmetric book & long side)

Written 2026-10-29 after the live audit (task 1, live paper only) and **before any history configuration below was
scored**. Not changed afterwards; results go in NOTES.md.

## Harness, data, costs, splits (all tasks)
- Entries: gates1021 live-shaped signal rows (live module mask, window, ADV, refire chain, production R with x3 on
  the extended tier, same-minute random control), rebuilt to scratch by `build_cache.py` for 28 covered setups.
  CWT14 failed-PDL-break longs: top5_1019/1027 kernel (`S6.b3_any`) + top5_1028 simulator.
- Exits for task 3: the top5_1028 simulator (stop first inside a bar; stop-distance rows at the same $ risk, target
  price unchanged; scale-out = half off at +x R, rest to breakeven). Parity gate: simulated parent = cache R
  (mean |d| < 0.002R) before any variant is read.
- Costs: 1c/share + 1 bp per side (time-of-day multiplier on entry), +2c on stop exits, target limits free, x3 on the
  extended tier (|gap| >= 20% or price < $5).
- TRAIN <= 2025-12-31; VALID 2026-01-01..2026-10-07 (all open 2026). Locked block 2024-11-01..2025-02-28 never
  loaded during the sweeps (lib asserts; MCF_HIST_ALLOW_LOCKED unset).
- Pre-open inputs only (G1 lesson): every regime value for session d uses daily bars through d-1 (closes, ranges);
  the SPY overnight gap uses d's 09:30 open vs d-1 close (known at the open, before any entry >= 09:50). The cached
  `spy_prev` column (gates1021 lookahead) is NOT used. Pre-market relative volume: the bar cache is RTH only
  (09:30-16:00), so it cannot be tested.
- Trailing percentiles: over the previous 250 open sessions (min 60); a session without enough history is ungated.

## Pass rules (fixed now)
- **Beats parent:** shrunk avg R (avg x n/(n+20)) above the parent's in TRAIN and in VALID, and the paired
  day-clustered t of the improvement (variant total R minus parent total R per parent trade, same days) >= the
  family bar max(1.5, sqrt(2 ln N_family)).
- **Finalist:** beats parent, variant avg R > 0 in TRAIN and VALID, avg R without best day > 0, and better than
  random removal of the same share of days (gates) / trades (task 3 n/a) at the 95th percentile of 1,000 draws.
- **Locked look:** a finalist only, once (look 1, t >= 1.0 and avg R > 0).
- Every row counts in N, including zero-trade rows.

## Task 2: pre-open long gate (keep the trade only if ...)
| id | gate |
|---|---|
| L1 | SPY prior close > its 20-day SMA |
| L2 | QQQ prior close > its 20-day SMA |
| L3 | both L1 and L2 |
| L4 | SPY overnight gap >= -0.25% |
| L5 | SPY overnight gap >= -0.50% |
| L6 | prior-day SPY return > 0 |
| L7 | prior-day QQQ return > 0 |
| L8 | prior-day SPY return > -0.5% |
Applied to every covered long setup (16 cached + 4 CWT14 pdl kernels = up to 20) and the pooled long book.

## Task 3: one-knob exits on MF2-FD, RW5-FD, RW3-FD (10 rows each incl. parent)
P parent; S1..S5 stop x1.5 / x2.0 / x2.5 / x3.0 / x3.5 of the live stop, same $ risk; O1..O4 scale half at
+0.25 / +0.40 / +0.60 / +0.80 R, rest to breakeven. Lineage N adds top5_1023 (RW5 18, RW3 17) and top5_1026 (MF2 17).

## Task 4: pre-open vol switch for FADE setups (skip the session's entries when the input is above its trailing pct)
- V1-V3: prior-day SPY ATR14 (% of close) above its trailing 70th / 80th / 90th percentile.
- V4-V6: prior-day SPY 20-day realized vol (stdev of close-to-close) above trailing 70 / 80 / 90.
- V7: prior-day VXX close 5-day % change above its trailing 80th percentile (VIX proxy; VIX itself not in the data).
- Fade = enters against the last move (shorts a bounce / pop / failed reclaim / exhaustion; buys a dip / flush /
  capitulation / failed breakdown). Momentum = enters with a confirmed turn or trend (breadth-up / index-turn
  confirmation longs, higher-low pm long). Per-setup list in NOTES.md. Applied per fade setup, to the pooled fade
  book, and to the pooled momentum book as a control (the switch should not help momentum if the story is right).
