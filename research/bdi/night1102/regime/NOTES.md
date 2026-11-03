Educational only — not financial advice

# night1102 / regime — which live setups hold up across market conditions, and is there a simple day switch?

Workstream "regime" for the owner's 2026-11-02 evening ask ("something has to be different"). Research only: no
config, setup or exit change; nothing merged. Costs in everywhere (live = journal `pnl_adj`; two-year = production R
with the x3 extended tier and time-of-day entry cost). Locked block 2024-11-01..2025-02-28 never loaded.
This run was restarted after the 20:00 ET container kill; the live map, pairs and live switch scan and the
pre-declaration (PLAN.md) were written before the restart and re-used; the two-year scan was resumed month by month.

## Data and definitions

- **Live**: paper trades run_id 1 of all five accounts (P 761, T1 3,402, T2 4,149, GY 2,942, GEN 1,002 = 12,256
  trades), 20 sessions 2026-10-06..11-02, R = pnl_adj / (|entry-stop| x shares).
- **Session tags** from SIP 1-minute SPY/QQQ/RSP: EOD type `up` (SPY open-to-close >= +0.25%), `down` (<= -0.25%),
  `quiet` (between). Live window: 5 up, 5 down, 10 quiet sessions. At-entry tags (last bar closed before entry):
  SPY vs session VWAP, SPY from open, with/against tape. Point-in-time day states at 09:50 / 10:00 / 10:30: SPY from
  open, SPY vs VWAP, breadth proxy (RSP - SPY from open), 09:30-09:50 range vs prior-20-day median range.
- **Two-year**: covered live lab setups (57 of the 113 assignment rows; scripted live setups, ETF/IDX setups and a
  few others are not covered) re-scanned on the open frames, TRAIN 2024-10 + 2025-03..2025-12, VALID
  2026-01-01..2026-10-05 (live window excluded). Simplification: refire chain as configured but no slot / per-symbol
  lot cap, so the two-year book is much larger than what an account would trade. Replays/backtests failed their
  audit on 10-29 (75.9% trade match, optimistic +0.032R), so two-year numbers here are a second opinion, not proof.

## Rule changes inside the window (owner rule 2026-11-02)

From `research/ledger.jsonl` effective dates, 10-06..11-02 — results below mix these periods:
10-21 promotions L3-gap-slope-fromopen-FD and CWT14-pdl-p10-lowvol T->Primary, MF3-FD demoted; 10-22 NS3-FD,
RW6G1 demoted, L3-fromopen demoted; 10-23 per-setup daily stop latch (all), off in Testing/GEN; 10-26 MF1 demoted,
CWT13-z05-long and ST7-FD promoted; 10-27 GX1 lab setups on the 5-minute clock (all accounts); 10-27 CWT13-z05-long
demoted; 10-28 CWT14-pdl-p10-lowvol, NS4-pm, MF2 base rotated out of Primary; **10-28 Primary position size ~$5k then
~$4k (slots 77, per-setup 30)**; **10-29 Primary per-setup daily stop -2R (latched)**; 10-29 Setup Generator paused
after the 10-28 run; 10-30 Testing cost filter CF and BAR90; 10-30 L3-gap-slope-rsi5hi-FD promoted, L3-fromopen-FD
re-promoted to Primary; 11-02 NS3-FD/RW4-FD to the Graveyard; plus many Graveyard moves of CWT longs. R is per-trade
so sizing changes do not scale R, but the -2R stop and the slot changes change which trades exist: Primary averaged
~42 trades/session before 10-29 and 12-16 after.

## 1. Regime map of the live book (`live_regime_map.csv`, 68 setups with 30+ live trades)

| book (live, all accounts) | up days | down days | quiet days |
|---|---|---|---|
| longs  (6,972 trades) | -0.01R x1,479 = -19R | **-0.34R x2,161 = -743R** | -0.08R x3,332 = -281R |
| shorts (5,284 trades) | **-0.28R x1,406 = -393R** | +0.05R x1,550 = +70R | -0.14R x2,328 = -330R |
| Primary longs (179) | -0.05R | -0.23R | +0.04R |
| Primary shorts (582) | -0.20R (-38.5R) | **+0.37R (+61.5R)** | -0.21R (-46.4R) |

- The live book is a market-direction bet: median correlation of a setup's daily R with SPY open-to-close is +0.42
  for longs and -0.16 for shorts. Longs lose most on down days, shorts on up days, and **both lose on quiet days**
  (10 of 20 sessions, -611R together) — the book has no edge on range days in either direction.
- At-entry tags separate little: SPY above vs below VWAP at entry -0.14 vs -0.16R (longs), -0.10 vs -0.15R (shorts);
  "with the tape" vs "against" -0.135 vs -0.163 (longs), -0.109 vs -0.138 (shorts). Trading with the tape at entry is
  not a fix.
- **(a) Robust setups: none.** 0 of 68 setups are positive in all three EOD types (13 positive in two, 30 in one, 25
  in none). Closest — the gap-down / flow-sell short family, positive on up AND down days, about flat on quiet:

| setup | n | avg R | w/o best day | best-day share | up | down | quiet |
|---|---|---|---|---|---|---|---|
| MF2-open-rsimidhi-flowsell-FD | 63 | +0.71 | +0.38 | 52% (1 day) | +1.16 (12) | +1.11 (37) | -0.76 (14) |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 91 | +0.37 | +0.14 | 58% (1 day) | +0.41 (11) | +0.59 (52) | -0.07 (28) |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 104 | +0.33 | +0.19 | 45% | -0.07 (17) | +0.59 (48) | +0.19 (39) |
| L3-gap-slope-fromopen-FD | 249 | +0.15 | +0.03 | 51% (1 day) | +0.20 (137) | -0.07 (36) | +0.17 (76) |
| L3-gap-slope-rsi5hi-FD | 79 | +0.15 | +0.06 | 38% | +0.20 (31) | -0.09 (9) | +0.16 (39) |

  Three of five are carried by one session (best-day share >= 50%, 10-22 for most). Two-year check: all five are
  negative or ~0 on two years and are direction bets there (e.g. RW3 TRAIN up -0.27 / down +0.03; VALID up -0.25 /
  down +0.10). Only 1 of 57 covered setups is positive in up/down/quiet in both TRAIN and VALID
  (NM-PM-gapdn-above-pdh-rvol-short, an observation setup selected on these frames, live n < 30). Two-year medians
  by side: shorts up -0.16 / down +0.08 / quiet -0.04 (TRAIN), -0.14 / +0.09 / +0.04 (VALID); longs +0.13 / -0.18 /
  +0.01 (TRAIN), +0.06 / -0.00 / +0.05 (VALID).

## 2. Complementary pairs (`pairs_live.csv`, `pairs_2y.csv`)

- 1,543 pairs of live setups scored on the sessions both were live. 22 have combined R > 0 in all three EOD types
  (>= 2 sessions each): 14 short+short, 7 long+short, 1 long+long. **None is a real long/short hedge**: every
  long+short pair rides one of the positive shorts (RW3 / RW5 / L3) with a long near 0R; the "hedge" is the short
  being positive, not the long covering the short's bad days. With 1,543 tries, 22 survivors is about what chance
  would give.
- Two-year re-check of the 22 (16 covered by the scan) and of the 7-short core book: **0 of 17 positive in all three
  EOD types in TRAIN or in VALID**; all lose on up days (-0.03..-0.29R) and win on down days. No small book in the
  live set is regime-neutral.

## 3. Point-in-time regime switch (`switch_live.csv`, `switch_2y.csv`, PLAN.md)

Rules read one state at T (09:50 / 10:00 / 10:30) and decide which side may open new trades for the rest of the
day; trades before T are untouched. "vs random" = kept R minus total R x kept share, day-clustered t.
Live scan: 57 rule x state combinations x 5 books = **285 configurations**. Three were pre-declared from live only
(PLAN.md) with a fixed two-year pass test (TRAIN and VALID: kept avg > parent avg, vs-random t >= 1.0, kept avg > 0
in 2 of 3 EOD types). Two-year scan: 45 x 5 = **225 configurations** (breadth states not available on two years).

| pre-declared switch | book | live kept / all R (vs-rnd t) | TRAIN kept vs parent avg (t) | VALID kept vs parent avg (t) | verdict |
|---|---|---|---|---|---|
| A fade@10:00 (after 10:00 shorts only if SPY >= open, longs only if SPY < open) | Primary | +43.3 / -32.1R, 53% kept (1.45) | -0.017 vs -0.055 (1.04) | -0.009 vs -0.020 (0.62) | **fail** (VALID t) |
| B calm-open short skip (09:30-09:50 range < 0.30 x 20-day median: no shorts after 09:50) | core7 | +179.0 / +168.6R, 81% kept (2.15) | -0.037 vs -0.051 (0.79) | -0.020 vs -0.022 (0.19) | **fail** |
| C fade@09:50 VWAP | all / shorts | -593 / -1,695R (0.90); shorts (1.17) | all 0.55, shorts 0.63 | all 0.19, shorts 0.01 | **fail** |

- A is the only switch whose sign agrees on live, TRAIN and VALID for Primary and core7, but it is weak (VALID t
  0.62), its kept trades still average below 0R on two years, and its live gain leans on one session (10-22: +70.6 of
  +43.3R kept; without 10-22 kept -27.3R vs all -97.8R, still better because it drops half the trades). The earlier
  day-class lineage (bdi1016-dayclass-direction-gate, market-context gates, 2,450 configurations, bar t 3.95) is far
  above anything here.
- The best two-year switch picked after the fact (fo@10:30 fade, Primary TRAIN t 1.19 / VALID t 1.10) is **-1.55 on
  live** (kept -91.2R vs -32.1R). Live and two-year disagree on most switches; none is proposable as a filter.
- Last three Primary sessions (10-29 quiet, 10-30 down, 11-02 down; 43 trades, -20.0R, mostly the same core shorts):
  A -4.5R, B -14.9R, C -4.5R. 11-02 was a "down" day on which SPY was +0.55% at 10:30 before falling — shorts entered
  into the morning rally and were stopped, so the loss was not a simple wrong-direction day.

## Proposals for the owner (at most 2; both research/monitoring only, no setup or exit change)

1. **Forward live test of switch A on Primary, scored from the journal, no trading change.** Each night tag every
   Primary trade entered at/after 10:00 as "kept" (short when SPY >= its 09:30 open at the 10:00 bar close, long when
   below) or "dropped", and keep the running kept-minus-random figure. Pre-declared decision after 20 more sessions
   (40 live sessions total): propose a Testing trial only if, on the new 20 sessions alone, dropped trades average
   below kept trades, vs-random t >= 1.0, and kept avg R > 0 without its best session. Evidence: live +43.3R kept vs
   -32.1R all (t 1.45, one-day share high), two-year TRAIN t 1.04, VALID t 0.62 (fails the pre-declared bar).
   Backlog: `regime1102-fade-1000-forward`.
2. **Show day type next to every result.** In reviews / briefs, give each setup's R split by SPY up / down / quiet
   day and by "SPY above/below its open at 10:00", as is now done for the one-big-day check. Evidence: live, 10 of 20
   sessions were quiet and both sides lost there (-611R); every family tested this week is a direction bet on two
   years; three of the five best live setups owe >= 50% of their R to one session. This is a report change only and
   makes "low success" stretches readable as regime vs setup failure.

What did NOT work, stated plainly: no live setup with 30+ trades is robust across day types; no pair or small book
is regime-neutral on two years; no simple 09:50/10:00/10:30 switch passed its pre-declared two-year test. The
honest reading is that the current book's edge (where it exists — the gap-down / flow-sell shorts) is a direction
exposure plus a few big sessions, and the "diverse conditions" goal needs new setups built for quiet/range days,
not a switch on top of the existing ones.

## Configurations counted

Live: 68 setup maps (11 tag cells each), 1,543 pairs, 285 switch configurations. Two-year: 57 setup maps,
225 switch configurations, 17 pair/book re-checks. Total scored configurations (pairs + switches + re-checks):
**2,070**, plus 125 descriptive setup maps. Three pre-declared finalists, all failed.

## Files

`scripts/` (fetch_idx, days, live, live_map, pairs, daybook, switch_rules, switch_live, predecl_days, days2y,
scan2y, eval2y, pairs2y), `live_regime_map.csv`, `pairs_live.csv`, `switch_live.csv`, `map_2y.csv`,
`switch_2y.csv`, `pairs_2y.csv`, `PLAN.md` (pre-declaration written before any two-year switch was scored).
Scratch (journals, bars, two-year signals) deleted after the run.
