# REGX — do the setups' market-condition ratings hold? (owner 2026-11-05)

*Educational only — not financial advice.* Research only: no config, setup, exit or dashboard change. Pre-registered
in `PLAN.md` (commit aee193343, before any cell was scored; no amendments). Costs in everywhere (2-year = production R
from `bt_lab1104`, uncapped chains, stop first; live = journal `pnl_adj`). Locked block 2024-11-01..2025-02-28 never
read. 2-year backtest and live **paper** results are labelled separately. 2-year lists are a second opinion (replay /
backtest audit of 10-29 failed: 75.9% trade match, +0.032R optimistic).

**Configurations:** 84 setups × 8 schemes = 672 ratings; 415 rated on 2-year TRAIN and tested on VALID + live, 232 live-
only (in-sample, no 2-year list), 25 not ratable (< 2 eligible cells). Plus 2 post-hoc looks (trend-day addendum below).

## Failures first
- **The point-in-time condition ratings do not hold.** Over the 6 schemes known at entry (VWAP, compass, first-hour day
  type, volatility, breadth, sector leadership): 309 ratings → **7 trustworthy (2%), 144 weak, 158 false (51%)**. Their
  best-minus-worst spread keeps its sign on VALID in **158 of 308 (51%) — a coin flip**. 42 had TRAIN t ≥ 2; at the
  VALID t ≥ 1 bar ~7 would pass by chance, 7 did. **The 7 are indistinguishable from luck.**
- **The compass is worse than chance:** VALID sign kept in 16 of 49 (33%), median rank correlation −0.5 on VALID and
  live, 35 of 50 ratings false. What a setup did in compass-up vs compass-down on TRAIN tends to reverse on VALID (the
  same TRAIN→VALID flip GATE1 saw for "with the tape"). Volatility regime 43%, sector 51%, VWAP side 55%, day type 59%.
- **Live cannot confirm the dashboard labels yet.** The 23 live sessions (10-06..11-05) had 1 Bull, 5 Bear, 7 Choppy,
  10 Quiet days (dashboard scheme). Of 32 dashboard-rated setups with ≥ 30 live trades only **4** have ≥ 10 live trades
  in both their best and worst label; 2 of 4 hold. Live is too short to judge the Bull/Bear labels.
- **6 dashboard ratings are false** (TRAIN-refit best/worst flips on VALID): L3-gap-slope-fromopen-FD (Primary, Bear /
  Choppy; live best-label −0.07R n 18 vs worst +0.26R n 150), L3-gap-slope-rsi5hi-FD (Primary, Bear / Choppy), RW6-ns2-
  up3-short-FD, NS2-sma50break-overbought-short, NM-AR-AM-gapdown-capitulation-long, ST7-rsi50dn-long-pm-t1s1-FD
  (Primary; dashboard Bull best — TRAIN refit says Choppy, flips on VALID). 11 more are weak (e.g. RW4-FD, ST2-FD,
  NS5-FD, NS2-FD, ST1-FD: TRAIN t < 2 or VALID t < 1). The one in-scope dashboard rating with a Choppy best (NM-HL-T75-pm-long) is weak.
- **Ratings flip between schemes for 33 of 84 setups** (best cell points up in one directional scheme and down in
  another). 168 of 415 rated cells have a best cell where one session carries ≥ 50% of the R on VALID or live.

## What holds (the hindsight direction label)
| scheme | rated | trustworthy / weak / false | VALID spread > 0 | live spread > 0 | med. Spearman VALID |
|---|---|---|---|---|---|
| **OC25** SPY open-to-close ±0.25% (**hindsight**) | 53 | **27 / 22 / 4** | **49/53 (92%)** | 26/36 (72%) | 1.0 |
| DASH dashboard Bull/Bear/Choppy/Quiet (**hindsight**) | 53 | 32 / 13 / 8 | 45/53 (85%) | 2/5 (40%) | 0.8 |
| BRD top-500 breadth vs VWAP at entry | 50 | 1 / 29 / 20 | 34/50 (68%) | 18/41 (44%) | 0.5 |
| DAYT first-hour trend / reversal / range (from 10:30) | 53 | 2 / 29 / 22 | 31/53 (58%) | 3/6 | 0.4 |
| VWAP SPY above / below VWAP at entry | 49 | 0 / 26 / 23 | 27/49 (55%) | 24/44 (55%) | (2 cells) |
| SECT offense − defense sectors at entry | 53 | 3 / 23 / 27 | 27/53 (51%) | 21/37 (57%) | 0.5 |
| VOL SPY range so far vs 20-day median | 54 | 0 / 23 / 31 | 23/54 (43%) | 17/37 (46%) | −0.5 |
| COMP GATE1 compass at entry (≥ 10:00) | 50 | 1 / 14 / 35 | 16/49 (33%) | 12/30 (40%) | −0.5 |

- **Most stable scheme: OC25 (hindsight ±0.25%)**, then the dashboard scheme. Their trustworthy ratings are almost all
  "shorts best on down days / worst on up days" (34 of 59) and "longs best on up days / worst on down days" (23; the other 2 are longs best on quiet days): the label restates the setup's
  side — the live book is a market-direction bet (night1102: daily R vs SPY corr +0.42 longs, −0.16 shorts). That
  part of the dashboard is real on 2 years; but it is **known only at the close**, and no point-in-time stand-in
  carries it (best one, breadth, keeps sign 68% on VALID and 44% live).
- **Per family / side** (VALID sign kept, all 8 schemes): CWT longs 70%, RW shorts 67%, GEN shorts 70%, MF shorts 52%,
  NS shorts 46%, CWT shorts 45%. Hindsight schemes hold for both sides (longs 84–92%, shorts 86–93%). Point-in-time:
  longs do best on breadth (17/22, but live 9/17) and sector (16/25); shorts are ≤ 61% on every point-in-time scheme
  (COMP 9/27, SECT 11/28). Full grid: `summary_famside.csv`, `summary_side.csv`.
- Point-in-time trustworthy (7, treat as chance-level): CWT14-failbrk-pdl-p05(-lowvol)-long and CWT12-coil-k6-long
  (sector: defense-led worst), CWT14-failbrk-pdl-p10-lowvol-long (breadth strong best), CWT13-vwapstretch-z05-long and
  NS5-sma50-flush-oversold-long (day type: trend-up worst), NS2-sma50break-overbought-short (compass up best; live
  disagrees −0.44R n 51). Even the "best" cells average ≤ 0R for 5 of the 7.

## MF4-h40-open-flowsell-FD and MF2-open-rsimidhi-flowsell-FD (11-04 up/Choppy, 11-05 Bear −4.2%)
- 11-04: SPY +0.48% (dashboard Choppy, OC25 up, first hour trend-up). 11-05: SPY **−4.22%** (Bear, trend-down, compass
  DOWN-confirmed from 10:30, breadth weak, defense-led).
- **Their Bear/Bull rating is trustworthy on 2 years — but "best" means "loses least".** MF4: Bear +0.01 / +0.02R
  (TRAIN / VALID, n 882 / 815) vs Bull −0.36 / −0.23 (t 5.0 / 4.3). MF2: Bear +0.21 / +0.10 vs Bull −0.33 / −0.31
  (t 3.3 / 2.5). Every point-in-time rating of both is weak or false (MF2: 4 false; MF4: 3 false).
- **MF2 behaved as rated.** 11-04 −6.5R (8 trades, 10:20–12:20) on an up day = its worst cell; 11-05 −1.7R (21 trades)
  on a down day, small. Live by OC25: down +0.68R (58), up +0.37R (20), quiet −0.58R (18); Primary 73 trades +0.39R.
- **MF4 broke its rating on 11-05**, not 11-04. 11-04 −4.3R (12 trades) on an up day fits the rating. 11-05 −10.7R
  (15 trades) on its best (Bear) day: **12 Primary shorts entered 11:00–11:10 ET, all stopped 11:12–11:18** in the
  same market bounce (FSLR, INIO, MRVL targets the only winners). One correlated cluster, not a condition miss: every
  point-in-time scheme read "with the short" at entry (below VWAP, compass down, breadth weak). Without 11-05 its live
  Bear record is +2.7R over 16 trades (+0.17R). 2-year: MF4's down-day avg is ~0R, so a −4% day gives it no edge.
- Shared thread (post-hoc, 2 looks): both do worse on first-hour **trend** days than on range / reversal days in TRAIN,
  VALID and live (MF4 −0.03 / −0.15 / −0.23R; MF2 −0.08 / −0.16 / −0.29R). Across all 28 rated shorts it does not hold
  (trend days worse on VALID for 25, but better on TRAIN for 18 and live for 21), so it is not a family remedy and is
  not proposed. The 11-05 cluster loss (12 same-side entries in 10 min) is a burst/correlation failure mode — passed to
  BURST1's scope, not tested here.

## Rule changes inside the live window (from `research/ledger.jsonl`)
Live results above mix: 10-20/21 MF2-FD, MF4-FD, NS3-FD promoted T1 → Primary (move from 10-21; MF4 T1 32 trades
+0.27R vs Primary 75 trades −0.23R straddle this); 10-23 per-setup daily stop latch; 10-27 GX1 5-minute clock (all
lab setups); 10-28 MF2 base rotated out of Primary, Primary size ~$5k → ~$4k; 10-29 Primary −2R per-setup daily stop;
10-30 Testing cost filter + BAR90, L3-rsi5hi promoted, L3-fromopen re-promoted; 11-02 NS3-FD / RW4-FD → Graveyard,
PDL-1a R2A into T2; 11-03 MF3-FD / MF5-FD → Graveyard, RW3S into T2; 11-04 NS5-FD / ST4 / RW6G1 → Graveyard, T2
top-500 pool (UNI1); 11-05 Explore 1 / Live Lab start (42 low-rep setups move). R is per trade, so sizing does not
scale it, but the −2R stop, the moves and UNI1 change which trades exist.

## Recommendation
1. Keep the dashboard "Best conditions" column but tag it **hindsight (SPY at the close)** and add the REGX reliability
   tag per setup (15 trustworthy / 11 weak / 6 false of the 32 in scope; `table.csv`, scheme DASH). It must not be read
   as "switch the setup on when the market looks bearish": nothing known at entry reproduces it. → DECISION REGX.
2. Do not build per-setup condition switches on VWAP side, compass, day type, volatility, breadth or sector ratings —
   out of sample they are a coin flip (compass: reversed).
3. Salvage: the direction label is real, so the lever is **book balance**, not per-setup timing — long and short books
   that each carry their own side's bad-day loss (a sizing/mix study, for the backlog only after a swarm).

Files: `table.csv` (one row per setup × scheme, verdict + reason), `table_full.csv` (+ spreads, t, Spearman),
`cells.csv` (every cell × window: n, days, avg, avg w/o best day, best-day share), `summary_scheme.csv`,
`summary_side.csv`, `summary_famside.csv`, `dash_live.csv`, `special_mf.csv`. Scripts: `fetch1105.py` (11-05 bars to
scratch), `breadth.py`, `cells.py`, `score.py` (`python X.py <scratch>`).
