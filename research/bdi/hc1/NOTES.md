# HC1 (Hunch → compass) + COMP15 (15-min rolling compass) — results 2026-11-05

*Educational only — not financial advice.* Research only; nothing in config/ or the trading path changed. Pre-registered
in `PLAN.md` (commit ba0ce7746, before any score). Locked block 2024-11-01..2025-02-28 never read. Periods = Hunch
replay's: TRAIN 2024-10..2026-02 (263 days with Hunch rows), VALID 2026-03-01..10-07 (153), FWD 10-08..11-04 (20),
LIVE 11-05 (1). **Configurations: 36 HC1 + 32 COMP15 = 68 → bar 2.90. 0 pass. No DECISION.**
Market-only study (SPY / Hunch bars, no setup R): no `research/ledger.jsonl` rule change bears on these numbers.

## Failures first
- **HC1: no.** Hunch breadth adds nothing to the GATE1 compass. 32 lift configs (8 Hunch blocks × 4 questions): best
  VALID accuracy lift **+0.77 pts** (next-60 min, pressure; log-loss t −0.08); staying with share_up **+0.36 pts**
  (t 0.29); rest-of-day "all" +0.60 pts but log-loss worse (t −0.55) and FWD −5.0 pts. Max VALID log-loss t 1.28
  (dshare6, 0 accuracy change). 16 / 32 configs > 0 on VALID = chance. None near +2 pts / t 2.90 (`hc1_lift.csv`).
- **Agreement split hurts or does nothing:** within directional readings, staying hit when Hunch's share_up side
  agrees vs disagrees: TRAIN 81.2 vs 82.3%, VALID 79.8 vs 83.3%, FWD 75.6 vs 83.5% (`hc1_split.csv`).
- **Why:** share_up has ~0 correlation with SPY's next-30-min move (TRAIN −0.04, VALID +0.01, `hc1_corr.csv`), and
  it is a one-factor swing: the pooled model leans on SPY/QQQ same-bar features, so all 200 calls flip together.
  Live 11-05 (SPY −4.2%): share_up went 0.41 → 0.00 → 0.56 → **1.00** → 0.00 → 0.05 → 0.91 at 10:00..13:30 while the
  compass sat DOWN-confirmed from 10:30 (`hc1_live_1105.csv`). Hunch live 11-05: pooled 53.2% vs base-rate 54.3%.
- **COMP15: no (pre-registered rule).** The 15-min windows confirm **30 min earlier** but the first confirmed reading
  is **8-13 pts less accurate** and flips rise **+0.3-0.4 a day** (day-paired t 5.8-6.6). VALID, 10:00-15:30:

| clock | confirmed staying hit (n, cover) | first conf. median / by 10:30 | first-conf. precision | side flips/day | conf. flips/day |
|---|---|---|---|---|---|
| 30-min GATE1 (held) | **89.4%** (1,690, 48%) | 11:00 / 37% | **79.9%** | **0.84** | 0.11 |
| W30 rolling | 86.6% (2,082, 59%) | 10:00 / 77% | 66.9% | 1.26 | 0.41 |
| W45 rolling | 87.7% (1,974, 56%) | 10:00 / 67% | 69.0% | 1.19 | 0.29 |
| W60 rolling | 88.4% (1,879, 53%) | 10:00 / 60% | 72.0% | 1.18 | 0.23 |
| whole day | 87.3% (943, 27%) | 10:00 / 60% | 68.7% | 1.02 | 0.00 |
  TRAIN same order (C30 first-conf. precision 77.8%, W60 78.2% — TRAIN alone would have passed W60; VALID did not).
- **Heading stays a coin flip on every clock:** rest-of-day 48-50%, next 30 min 50-51%, next 60 min 49-51% (VALID,
  confirmed and directional; `comp15_hits.csv`). No window improves it at the bar.

## What works / can be salvaged
- **Rolling 45/60-min windows read "staying" slightly better for all directional readings:** VALID 83.2 / 83.3% vs
  82.3% (+0.8 pts day-avg, t 2.95 / 2.80; TRAIN +0.45, t 1.7 / 1.4; FWD +2.1 / +1.9, t 2.2). W45 clears 2.90 on VALID
  only, not TRAIN → weak, but consistent sign in all three windows.
- **At the same half-hour checkpoints W60 matches the 30-min compass** (confirmed staying VALID 89.5 vs 89.9%, n 899 vs
  888; `comp15_halfhour.csv`): the loss is in the *extra* 10:00 / quarter-hour confirmations, not in W60 itself.
- **09:45 lean (low confidence, 09:30-09:45 only):** holds its side of the open 67 / 66% TRAIN, 63 / 61% VALID
  (lean up / down), i.e. a usable first hint 15 min before the 30-min compass has anything (`comp15_0945.csv`).
- **Live 11-05:** every 15-min window was DOWN-confirmed at 10:00, the 30-min compass at 10:30; SPY closed −4.2%
  (`comp15_live_1105.csv`) — one day, the kind of trend day where earlier confirmation pays.
- **Practical reading:** show the 15-min W60 reading as an early "lean / provisional confirm" (09:45 flagged low
  confidence), keep the 30-min reading as the "confirmed" call. Forward-logged as `comp15-w60-early`
  (hypotheses.jsonl), no trading change.

## Files
`hunch_probs.py` (replay re-walk of Hunch pooled logreg, per-bar P(up) aggregates), `state15.py` (15-min SPY state +
11-05 from Alpaca market-data GET; 11-05 breadth = 200 Hunch names), `comp15.py`, `hc1.py`. Tables: `comp15_hits.csv`,
`comp15_halfhour.csv`, `comp15_0945.csv`, `comp15_early_flips.csv`, `comp15_live_1105.csv`, `hc1_lift.csv`,
`hc1_split.csv`, `hc1_corr.csv`, `hc1_live_1105.csv`. Caveats: 11-05 live pressure uses same-day vol20 (approx.);
GATE1's own split differs (TRAIN < 2026-01) — the 30-min compass was recomputed on this split. Scratch panel deleted.
