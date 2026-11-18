Educational only — not financial advice

# U6 — Mechanism setups for missed moves (USAGE PLAN item 6) — PRE-REGISTRATION

Written 2026-11-18 (market hours) BEFORE any outcome was scored. Research only: no config, code, runtime, merge or PR.
Locked block 2024-11-01..2025-02-28 is never read (fit sessions start 2025-06-02; every daily row <= 2025-02-28 is
dropped at read time and asserted absent). EARN-GO (earnings reaction day) is already approved/built: not duplicated —
every setup here is run with the live earnings blackout (+-4 trading days) in CHECK, so it never trades EARN-GO's names.

## Why (Move Hunt, P6, C3-MECH)

research/bdi/moves/moves.csv (12 sessions 10-29..11-17, 600 tradable non-blackout top moves): live caught 15.0%.
Of the tradable moves: 383 decide by 09:45 (opening drive; caught 11.2%), 105 are non-earnings gap-and-go (gap >= 2% in
the move's direction; 16.2%), 75 are inverse / leveraged / vol ETFs (8.0%, mostly 09:35 index-drive days 11-05, 11-09,
11-17), 22 decide 13:00 or later (13.6%). Sector-lag moves are not labelled in moves.csv (no sector field); the setup
below tests the mechanism directly. (These category counts were read from moves.csv to choose the categories, as the
item asks; they are capture counts, not setup outcomes.)

## Data (docs/GLOSSARY.md terms)

- FIT = 2-year backtest bars (releases bars2y-2025-06 .. bars2y-2026-01, partial point-in-time universe),
  168 sessions 2025-06-02..2026-01-30. No earnings dates exist for these packs: FIT trades include earnings days
  (labelled; a known contamination for M1/M2).
- CHECK = Session replay bars of the live sessions (bars-2026-10 / bars-2026-11, full live universe),
  31 sessions 2026-10-06..2026-11-17 (11-18 still open: left out). Earnings blackout = union of mcf-data
  earnings/<day>.json dates, +-4 trading days (as live).
- Both are non-live sources (weight 0 toward On Deck / Primary, SRCV1). PASS = Testing-copy proposal only; promotion
  hold is on.

## Common mechanics (fixed)

- 5-minute decision bars from 1-minute RTH bars (bar k = minutes 5k..5k+4 after 09:30, decided at its close).
- Fill = OPEN of the 1-minute bar after the decision bar (minute 5(k+1)); R = |fill - stop|; no trade if the fill is
  at/through the stop. Exits on 1-minute bars from the fill minute: stop first (gap through -> that minute's open),
  target only when traded through by >= $0.01, time exit at the open of the exit minute (never later than 15:55).
- Costs = the Workbench/LR8 research model (research/workbench/CWT09-gapdn-vwaploss-g10-short/code/wb.py):
  entry (1c + 1 bp) x tod_cost_mult (3.8 before 09:35 close incl., 2.1 to 09:50, 1.4 to 10:30, then 1.0) + 1 bp
  + SEC 20.60/M + TAF + CAT; exit target 0, stop (1c + 1 bp) + max(2c, 4 bp), time (1c + 1 bp) + max(1c, 1 bp); + CAT.
  Both sides charged the same way (SEC on every side — conservative).
- Point-in-time daily features from 1day rows strictly before the session: prior close pc, ATR14, ADV20 ($ and
  shares), 50-session daily returns (for M3 / M4 mapping).
- STOCK universe (M1, M2, M3, M5): pc >= $10, ADV20 >= $20M, 1% <= ATR14/pc <= 8%, name NOT matching the ETF regex
  of wb.py (data/universe.csv names; unnamed symbols count as stocks).
- LEV-ETF universe (M4): name matches (2X|3X|-1X|-2X|-3X|Ultra|Bull|Bear|Inverse|Short|VIX|Volatility|Leveraged|
  Daily), pc >= $5, ADV20 >= $20M, 1% <= ATR14/pc <= 20%.
- Per setup and side at most 10 entries per day (first by decision bar; within one bar by strength); one trade per
  symbol per day per setup. d = +1 long / -1 short.

## The five setups (one pre-registered config each; both sides scored as one setup unless noted)

| # | id | category | entry at bar-close k | stop | target / time exit |
|---|---|---|---|---|---|
| M1 | U6-OD-drive | opening drive | k in {0,1,2} (09:35/09:40/09:45); \|gap\| <= 3%; d(C-open)/ATR >= 0.40; long: (C-LOD)/(HOD-LOD) >= 0.80 (short <= 0.20); d(C-VWAP) > 0; cum. shares to k >= (0.05 + 0.025k) x ADV20 shares. Strength = d(C-open)/ATR | fill - d 0.40 ATR | 2R; flat 11:00 |
| M2 | U6-GAPGO-nonearn | gap-and-go (non-earnings) | d gap >= max(2%, 0.5 ATR/pc), \|gap\| <= 15%; 09:30-09:45 gap held (long: low15 >= pc + 0.5(open-pc), C(09:45) >= open; short mirror); first k in 3..12 (09:50-10:35) with d C > d OR15 extreme (long: C > OR15 high) and d(C-VWAP) > 0. Strength = d gap / (ATR/pc) | fill - d 0.50 ATR | 2.5R; flat 15:55 |
| M3 | U6-SECLAG | sector-move follower | stock mapped to the sector ETF (XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC SMH XBI KRE XOP ITB) with the highest 50-session daily-return correlation, corr >= 0.60; \|gap\| <= 3%; k in 5..47 (10:00-13:30): ETF move E = d(C-open)/ATR_etf >= 0.75; stock s = d(C-open)/ATR in [-0.25, 0.35 E]; d(C_k - C_k-1) > 0 and d(C-VWAP) > 0. Strength = E - s | fill - d 0.40 ATR | 2R; flat 15:55 |
| M4 | U6-LEVETF-drive (long only) | inverse / vol / leveraged ETF spike | LEV-ETF universe; k in {1,2,3} (09:40-09:50); SPY drive D = (C_spy-open_spy)/ATR_spy, \|D\| >= 0.25; ETF's 50-session daily corr with SPY \|rho\| >= 0.5 and sign(rho) = sign(D); ETF (C-open)/ATR >= 0.40, (C-LOD)/(HOD-LOD) >= 0.80, C > VWAP. Max 5 entries/day. Strength = own move | fill - 0.40 ATR | 2R; flat 12:00 |
| M5 | U6-PMTREND | afternoon trend continuation | \|gap\| <= 8%; k in 41..59 (13:00-14:30); d(C-open)/ATR >= 0.80; every 5-min close from bar 17 (11:00 close) to k has d(C-VWAP) > 0; d C_k > every earlier d C (new closing extreme of the day). Strength = d(C-open)/ATR | fill - d 0.40 ATR | none; flat 15:55 |

Mechanisms (falsifiable, C3-MECH tag):
- M1 — heavy-volume opening drives from a flat open are informed order flow that keeps going for the first hour
  (if false: drive names mean-revert by 11:00 as often as they extend, avg R <= random).
- M2 — a non-news-day-sized gap that holds its first 15 minutes and breaks its 15-minute range is a continuation day
  (if false: no edge over random same-minute entries).
- M3 — highly sector-correlated names lag a strong sector ETF move and catch up the same day (lead-lag diffusion)
  (if false: laggards stay laggards — they lag for an idiosyncratic reason).
- M4 — index opening drives continue into late morning and the leveraged/inverse/vol wrappers carry it at 2-3x beta;
  leveraged-ETF rebalancing flows add in the drive direction (if false: no edge vs random lev-ETF entries).
- M5 — a stock that trended all day and holds VWAP all midday makes a new extreme after 13:00 and runs into the close
  (late-day momentum / MOC imbalance) (if false: afternoon breakouts fade; avg R <= random).

## Controls and counted configs

- R1-R5: random entries — for each setup trade, 3 random names from the same universe pool that day (same filters,
  not the signal), same fill minute, side, stop in ATR units, target R-multiple and time exit, same costs.
- Configurations: 5 setups + 5 random controls (scored for verdicts) + 9 side splits (M1, M2, M3, M5 x long/short and
  M4) shown descriptively = **19 looks**. Bar: day-clustered t >= max(1.5, sqrt(2 ln 19)) = **2.43**.

## Pass rule (per setup, both sides pooled, fixed now)

1. FIT (2-year): >= 100 trades, avg R > 0 after costs, day-clustered t >= 2.43, avg R > 0 on SPY-up and SPY-down
   sessions separately (SPY open-to-close sign), and >= 60% of the 8 calendar months positive.
2. CHECK (live-session replay, unseen): >= 25 trades, avg R > 0, avg R w/o best day > 0, best-day share < 50%,
   avg R > its random control.
- PASS (both) -> Testing-copy proposal (decision code), never deployed here. One of the two only -> WATCH (no proposal).
- Reported for each: trades, win %, avg R, total R, avg R w/o best day + share, worst day, green days, day-clustered t,
  random control, per side, and Move Hunt capture.

## Capture-rate report (Move Hunt, fixed now)

On the 12 Move Hunt sessions (10-29..11-17, tradable set, 600 moves): a move counts as captured by a setup when the
setup has a trade on that symbol, same side, with fill minute between decision - 30 min and the extreme (moves.py
definition). Reported: moves captured, how many of them live did NOT catch (new captures), the capture rate
15.0% -> new rate, the R of those trades, and per category (opening drive / gap-go / lev-ETF / afternoon).

- No parameter is changed after scoring. A bug fix (not a result) is logged in NOTES.md with what changed.
