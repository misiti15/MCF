Educational only — not financial advice

# STOPX-1127 pre-registration (written 2026-11-26 ~22:00 ET, before any score; sha256 in PREREG.sha256)

Source: research/inspector_1127/ideas.json rank 2 "STOPX" (judge 7.0), run as written; notes say where a detail had to be fixed.
Research only: no config, ledger, decisions.json or live change. Nothing here touches setup or exit code.

## Step 0: live stop-slippage audit (measurement, not a config)
- Data: the cleaned live trade set of primshorts_1126 (10 journals, run 1, 10-14..11-25, R3C cleaning: multi-part exits,
  |fill-ref| > 2 %, price < $5, bad exit bars and moved stops dropped; exit-minute SIP bars) = scratchpad ps_live copy. No new
  journal read for Step 0 (11-26 exits have no exit bars yet; noted).
- Stop exits only. Slippage per share = side x (engine stop fill - live fill), engine fill = stop, or the exit-minute open when
  that open is already through the stop (bench10 rule). Reported in bps of price and in R, mean / median / p90, by price
  bucket, by setup family (gap-down shorts vs rest), by side; against LR8's 4 bp the inspector quotes and against the LR8
  research stop-exit charge (1c + 1 bp + 2c stop add-on, in bps of price) and the LIVE-L stop cell.
- Also: share of live stop exits whose exit-minute 1-min close was back on the right side of the stop (a close-confirmed rule
  would not have exited on that bar) — information only.

## Step 1: 3 stop configs on the minute engine
- Lots: Primary's 4 setups (L3-gap-slope-fromopen-FD, RW3, RW5 shorts t1s1; NM-ETF-late-dip-di-long t05s1) bench10 candidate
  lots as built by regsteer_1126 rs_cand.py (price >= $5, ETB shorts; scratch copy rsw/cand.parquet, setup rows only).
  Stop = entry - side x risk; target = entry + side x (1.0 | 0.5) x risk (t1s1 | t05s1). Exits re-walked on 1-minute bars
  (data/cache_hist/1Min from 2024-09-16, data/cache_fresh/1Min before), from the entry minute (bench10 rule: bars with
  hhmm >= tod), flat at the 15:55 open.
- BASE = bench10 walk (stop on intrabar touch, gap-through fills at the worse of open/stop; target on a trade through by $0.01;
  stop checked first in a bar). Parity: BASE must reproduce the cand xm on >= 99 % of lots and avg R within 0.005R per split.
- C1 close-confirmed stop: the stop fires only when a 1-min bar CLOSES at or through the stop; fill = next 1-min bar open
  (order sent at the bar close). If that bar is the last before 15:55 the 15:55 open is the fill. Target unchanged (intrabar);
  in a bar where the close confirms the stop the stop wins (conservative).
- C2 = C1 + catastrophe stop at 2x the stop distance (entry - side x 2 x risk), intrabar, checked first; fill at the worse of
  open / catastrophe level.
- C3 = 5-min close trigger: the stop fires only when a clock-aligned 5-min bar (09:30 + 5k) closes at or through the stop;
  fill = next 1-min bar open. Keeps C2's 2x catastrophe stop (fixed here: a 5-min trigger without any intrabar protection is
  not a live candidate). Target unchanged.
- Costs: LIVE-L (primshorts_1126 cells_live.json) on the shorts, LR8 research on NM-ETF (primshorts convention). Confirmed /
  catastrophe exits are charged as kind "stop" (LIVE-L stop cell; LR8 +2c), conservative; kind "market" shown as sensitivity.
- Book: Primary rules (primshorts_1126 booksim.sim_day: <= 77 lots, 30 per setup, 3 per symbol, burst brake, -2R latch,
  -20R halt) with LATCH-OPEN on for every setup ("Primary rules + LO"); open marks = 1-min close path less the lot's full cost,
  per config (each config's own exit minutes and R). BASE book reported with LO off too.
- Splits: FIT 2024-10 + 2025-03..09 (information only; nothing is fitted), CHECK 2025-10-01..2026-11-04,
  T2 2023-01-03..2024-09-13. Locked block 2024-11-01..2025-02-28 never read: bar loads filter it out and assert, the lot table
  is asserted on load and before scoring.

## Pass bar (ideas.json), each config, on CHECK and on T2 separately
1. Paired dR/trade > 0 with day-clustered t >= 3.4: dR = config R - BASE R of the same lot, over the lots the BASE book
   (Primary rules + LO) takes.
2. >= 2/3 of setups improve (>= 3 of 4 on paired dR/trade) and none worse than -0.03R/trade.
3. Book worst-5 days (sum of the 5 worst session totals) no more than 5 % deeper than BASE.
4. Best-day share < 50 %: the best session's share of the config's total book dR vs BASE (must be > 0).
A config passes only if all 4 hold on both CHECK and T2. Reported for every config: per setup paired dR, book R/session, avg R
w/o best day + best-day share, red days / 21 sessions, worst-5, 20-session floor, lots/session, exit-kind mix.

## Multiplicity
Configs: 3 (Step 0 is measurement). Lineage: ~8,891 (regsteer_1126) + this week's later studies + 3; the ideas.json bar
t >= ~3.4 is used as written (t >= 4.26 at N ~ 8,900 shown alongside).
