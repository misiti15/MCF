# Giveback map: where R is lost after a trade or a book has been up (giveback_1119/map)

*Educational only — not financial advice.* Live figures are **paper** results from 33 sessions. The 2-year lab is a
replay. This is a descriptive map. It tests no exit rule (**exit configs tried: 0**) and changes nothing live. The plan
was written before any scoring: [PLAN.md](PLAN.md). Cells scored in part (c): K = 916 (lab), bar T = 3.69.
**Locked block 2024-11-01..2025-02-28: filtered at read and asserted absent.** Costs are in throughout. Live R uses the
LR8 basis on every row (`mcf.costs.cost_r_lr8`, DQ-P3). Lab R uses bt_all costs. An early exit is charged the market-exit
cost plus $0.01 a share extra, and live early exits also pay half the spread.

## Bottom line (5 lines)
1. **No state in a trade's path says, on average, "get out now".** In the 2-year lab, 0 of 916 cells (family x side
   x state x minute 5-120) favour an early exit in both halves. In 31 cells, holding pays in both halves (t >= 3.69).
   Even `faded` trades favour holding: these reached +0.5R and are now at or below entry, yet the rest of the trade
   is worth +0.03 to +0.13R more than exiting. Live (33 sessions) agrees: no consistent negative cell, and holding
   short `working` trades pays (+0.09 to +0.16R from minute 15). This fits the earlier failures: L16 near-target
   breakeven, book-wide breakeven, W5 X1-X3 and Wave-2 trail.
2. **Most of the "hold pays" margin is the exit cost.** An early exit costs about 0.04-0.06 stop units, and the median
   cost gap is 0.068 including entry. Before that cost, paths are close to fair from every state. A per-trade exit
   rule cannot add R unless it finds a state with real negative drift, and none passed the bar.
3. **Trade-level giveback sits in two structural pockets, not in timing.** (i) **Far targets.** These are t1s05
   setups (2:1 target with a half-size stop), or live targets more than 1.2R from the fill. Of the trades that touch
   +0.8R, 21-40% end at a full stop. Elsewhere it is about 5%. These setups lose 41-48R per 100 trades after +0.8R
   (lab), and live they are 3,100 trades at -0.29R. (ii) **GEN `hold` setups with no target.** Of their trades that
   reach +0.8R, 25% end at a full stop (live, 3,406 trades, -0.23R). The lab cannot see this pocket because it has no
   hold lists.
4. **Book-level reversals are mostly a market move against a one-sided book, plus entries after the peak.** 83
   account-days peaked at +5R or more, and 48 of them (58%) closed red. On the 70 days that gave back at least 5R
   from a +5R peak, the 2,201R giveback splits into 1,268R from lots open at the peak and 933R from later entries.
   The later entries are only -52R worse than each account's normal rate. At the peak the open lots were 83% one
   direction (median). Majority-side lots carry 1,029R of the 1,268R. Lots where SPY then moved against them lost
   928R. One percent of SPY against a lot is worth about -0.8R per lot, and the intercept is -0.23R per lot even with
   SPY flat (regression from a peak picked in hindsight).
5. **So the remedy space is the book and the geometry, not trade timing.** Candidates for the remedy teams follow.
   None is tested here, and every one must go through WB2, the backlog and the setup freeze. (a) A book-level
   net-direction brake or hedge when the open book is at least 80% one side and up. (b) Re-anchor or shorten the far
   targets on t1s05-type setups only. Wave 2 parked target-from-fill book-wide, so this would be the targeted form.
   (c) A trail for GEN hold/holdtr setups (backlog `xa-1105-hwm-giveback-exit` fits this pocket). (d) Primary only:
   look at late entries on days that have already reversed. On Primary's 9 big-giveback days, late entries made
   -63R against -18R expected, but this number is circular, because late entries are part of the giveback.

## Data
- **Live:** run 1 of all 10 journals (`origin/mcf-data*`: Primary, Testing1, Testing2, LiveLab, Explore1, Graveyard,
  TestingD/E/F, Gen), 2026-10-06..11-19, 28,118 trades (28,097 after removing identical cross-account signals),
  avg R -0.151 (LR8 basis).
  - Minute paths come from Alpaca 1-minute SIP bars for all 13,426 (day, symbol) pairs plus SPY/QQQ. Bars start the
    minute after the entry minute.
  - Bar MFE vs journal `mfe_r`: corr 0.95.
  - Path unit = |entry - stop| of the fill.
- **Lab:** `research/history2y/data/bt_lab1104` lists for 95 setups (32 families), 2024-10..2026-11-04, minus the
  locked block. First signal per (setup, symbol, day): 1,106,391 trades, 446 sessions, avg -0.074 stop units.
  - Walked on `data/cache_hist/1Min` with the BEREPLAY conventions: entry at the signal-bar close, live geometry,
    stop checked first inside a minute.
  - Fit = sessions up to 2025-09-30, check = later sessions.
  - Geometry mix: t05s1 783k, t1s1 284k, t1s05 31k, t05s05 8k.
- Code in this folder: `load_live.py`, `fetch_bars.py`, `live_paths.py`, `lab_paths.py`, `analyze_live.py`,
  `analyze_lab.py`, `drivers.py`, `common.py`. Full tables: `live_tables.md`, `lab_tables.md`, `drivers.md`.
  Per-cell CSVs: `data/`.

## Strongest giveback pockets (where R is lost after being up)
"Lost after +0.8" = the sum of (MFE - final R) over trades that reached +0.8R and closed <= 0. "Stop | +0.8" = the
share of trades touching +0.8R that ended at a full stop.

| # | Pocket | Source | n | avg R | reach +0.8 | stop \| +0.8 | lost after +0.8 | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | Target > 1.2R from fill (MF1/MF2/CWT09/CWT12/LIQ/GEN t1s05, heat_fade, CWT14 drift) | live | 3,100 | -0.293 | 43% | **25%** | **993R** (409 trades) | 11-19 Primary type: targets 1.0-1.6R from the fill |
| 1b | t1s05 geometry | lab | 31,026 | -0.108 | 55% | **28%** | 43.6R / 100 trades | t1s1: 4.8%, 6.4R / 100; t05s1: about 0 |
| 1c | CWT09-gapdn-vwaploss-g5-short | lab / live | 4,990 / 182 | -0.133 / -0.383 | 55% / 43% | 32% / 40% | 47.6 / 100 ; 86R | w/o best day: lab -0.190, live -0.609 |
| 1d | MF1-945-flowsell-vwapup-FD | lab / live | 11,012 / 157 | -0.171 / -0.332 | 55% / 52% | 29% / 31% | 46.0 / 100 ; 76R | |
| 1e | MF2-open-rsimidhi-flowsell-FD | lab / live | 4,739 / 217 | -0.099 / -0.222 | 54% / 46% | 26% / 21% | 40.9 / 100 ; 65R | |
| 1f | CWT12-coil-k6-long | lab / live | 3,844 / 271 | -0.140 / -0.236 | 54% / 49% | 30% / 23% | 43.7 / 100 ; 97R | |
| 2 | GEN `hold` / `holdtr` (no target) | live | 3,406 | -0.231 | 36% | **25%** | **538R** (279) | Worst: GEN-261022-09 ...-hold-short, 220 trades, -0.87R, 60% stop \| +0.8. No lab coverage |
| 3 | SPY moved against the trade (> 0.2%) | live | 6,512 | -0.591 | 14% | **30%** | 693R | With the trade: 6.3%. Lab: 23% against vs 2.3% with |
| 4 | Entries 10:30-12:00 | live | 11,265 | -0.145 | 25% | 14% | **985R** (largest by time) | Lab: stop \| +0.8 is 8.8% here vs 3.3-5.9% at other times |
| 5 | Hold 2-4h / > 4h | lab | 130,739 / 48,057 | -0.154 / -0.188 | 22% / 20% | 11% / 7% | 7.1 / 8.9 per 100 | Stop \| 80% of target: 12.5% / 10% (1% for holds <= 15m) |
| 6 | Book: majority-side lots open at a +5R peak | live | 70 days, 3,082 lots | | | | **-1,029R** of -1,268R | 1% SPY against a lot = -0.8R |
| 7 | Book: entries after the peak on giveback days | live | 5,756 trades | -0.162 | | | -933R (expected -881R) | Primary: -63R vs -18R expected (circular) |

Trades that reached +0.8R and closed <= 0 (live, all accounts): 902 trades. Their final R was -822R, and they gave
up 1,907R from peak to exit. At +0.5R: 2,432 trades, -2,083R final, 4,124R from peak. These are upper bounds that
need an oracle. On 2 years, L16 shows that a rule which tries to collect them gives up as much on target trades that
dip back first.

## (a) Per trade
**Side (live):**
- Longs: MFE 0.48, MAE 0.62, median time to MFE 21 min. 16% reach +0.8, and 14.5% of those stop.
- Shorts: MFE 0.59, median time to MFE 29 min. 28% reach +0.8, and 11.6% of those stop.

**Lab:**
- Longs (mostly t05s1): 0.47 / 0.57 / 13 min.
- Shorts: 0.62 / 0.63 / 20 min.

**Geometry is the dominant cut.** Thresholds in R mean different things for a 0.5R and a 2R target.

| Geometry | n | reach +0.8 | stop \| +0.8 | stop \| 80% of target |
|---|---|---|---|---|
| t1s1 | 284k | 45% | 4.8% | 4.8% |
| t1s05 | 31k | 55% | 28.4% | 8.1% |
| t05s1 | 783k | 2.8% | 0.2% | 5.4% |

Live by target distance from the fill:

| Target from fill | n | avg R | stop \| +0.8 |
|---|---|---|---|
| < 0.6R | 11,335 | -0.128 | 0% |
| 0.6-0.9R | 5,890 | -0.118 | 1.5% |
| 0.9-1.2R | 4,366 | -0.091 | 6.1% |
| > 1.2R | 3,100 | -0.293 | 25% |
| No target | 3,406 | -0.231 | 25% |

**Up-then-stopped trades are slow reversals, not instant spikes.**
- Lab: MFE at a median of 22 minutes, then 48 more minutes to the stop (t1s1: 26 and 65). Target trades last a
  median of 39 minutes.
- Live: MFE at 30 minutes, then 37 minutes to the stop.

**Instrument type (live):**

| Type | stop \| +0.5 | stop \| +0.8 |
|---|---|---|
| Stock | 13% | 11.7% |
| ETF | 15% | 14.2% |
| Leveraged ETF | 19% | 17.4% |
| Inverse ETF | 21% | 19.8% |

The lab shows the same order but small differences (6.2-7.3%).

**Time of day:**
- Live, stop | +0.8 falls through the day: 14.6% / 14.2% / 8.9% / 8.2% across the four buckets.
- Lab: 5.9% / 8.8% / 5.5% / 3.3%.
- Avg R improves later in the day, both live (-0.208 to -0.068) and in the lab (-0.092 to -0.027).

**Day type:** SPY down days carry the most live giveback (982R of 1,902R lost after +0.8, stop | +0.8 15.6% vs about
10.5% on up and flat days). In the lab the effect is small and reversed (5.4% on down days, 7.8% on up days).

**Market during the trade is the strongest conditioner.**
- Live: SPY against the trade gives avg -0.59R and stop | +0.8 of 30%. SPY with the trade gives +0.31R and 6.3%.
- Lab: -0.67 vs +0.32, and 23% vs 2.3%.
- This is known only after the fact. rootcause_1119 found no entry-time state that predicts it.

**Accounts (live), stop | +0.8:**

| Account | stop \| +0.8 |
|---|---|
| Gen | 20% |
| LiveLab | 32% (n small) |
| Primary | 14% |
| Graveyard | 10% |
| Testing2 | 10% |
| Testing1 | 8% |

## (b) Per account-day (live, minute mark-to-market in R; realized after costs, open lots marked at the minute close)
| Peak | Account-days | Closed red | Closed below half the peak | Avg giveback |
|---|---|---|---|---|
| >= +3R | 105 | 66 (63%) | 82 | 25.7R |
| >= +5R | 83 | 48 (58%) | 63 | 26.9R |
| >= +8R | 53 | 24 (45%) | 37 | 26.9R |

**Primary:**
- Overall: 33 sessions, 15 with a peak of +5R or more, 7 of them closed red. Peak-to-close giveback summed to 422R
  against a closing total of -133R.
- Since the -2R latch (10-29): 16 sessions, 8 peaks of +5R or more, 4 closed red.

**What drove the reversals** (the 70 account-days with peak >= +5R and giveback >= 5R; `drivers.md`):
- **Lots open at the peak (-1,268R, 58%).**
  - Mark at the peak was +0.20R per lot, final -0.10R, a change of -0.30R per lot.
  - Exits: 29% stop, 23% target, 47% flatten.
  - Lot change vs SPY's move from the peak to the lot's exit, signed by side: slope +0.81R per 1%, R^2 0.10.
  - **Same-direction clustering:**
    - At the peak, median 83% of open lots were one side. On 37 of the 70 days it was 80% or more.
    - Majority-side lots carry -1,029R of the -1,268R.
    - SPY moved against the book's net side after the peak on 45 of 70 days.
  - By account: Primary slope +0.88R per 1% (R^2 0.15), Testing1 +1.01 (0.14), Testing2 +0.81 (0.03).
- **Entries after the peak (-933R, 42%).**
  - 5,756 trades at -0.162R, against -881R expected at each account's own rate on its other days.
  - Late entries are the account's normal negative expectancy, not a special failure. The exception is Primary:
    -63R against -18R expected, which is circular as noted above.
  - In high-count accounts (Graveyard, Testing2, Gen) late entries are most of the giveback. Graveyard: -1,213R late
    vs -426R from open-at-peak lots.
- **Peak timing:** median 11:52. 35 of 70 peaks came before 12:00.
- **Families with the largest open-at-peak giveback:**

  | Family | Lots | Peak mark | Final | Total change |
  |---|---|---|---|---|
  | GEN long | 762 | +0.40 | +0.10 | -230R |
  | CWT14 long | 781 | | | -150R |
  | CWT09 short | 99 | +0.59 | -0.55 | -112R |
  | MF2 short | 92 | +0.68 | -0.41 | -100R |
  | GEN short | | | | -78R |
  | heat_fade_short | | | | -78R |
  | RW7 | | | | -74R |
  | RW3S | | | | -62R |

  CWT09 and MF2 are again the far-target pocket.
- **11-19 Primary** (rootcause_1119, swings): peak +8.69R at 11:40, trough -19.6R at 13:39. 16 lots were open at
  the peak, 56% one side. The signed SPY move after the peak was -2.1% against the book. That is the tail of the
  slope above, not a different mechanism.

## (c) The stalled-trade signature: remaining value at minute t
Remaining value = final net R minus a market exit at the minute-t close (costs as above). A negative value means
exiting at t would have been better.

**Lab, all families, by side:**
- Every state at every t is >= 0 on average, except `below` at t >= 90 for longs (-0.001 to -0.008, t > -0.8).

  | State | Remaining value | Final R |
  |---|---|---|
  | `below` | +0.00 to +0.02 | about -0.76 |
  | `faded` | +0.03 to +0.22 | -0.10 to -0.30 |
  | `flat` | +0.01 to +0.05 | |
  | `other` | +0.03 to +0.05 | |
  | `working` | +0.05 to +0.16 | +0.63 to +0.77 |

- Below the bar, the share of family cells with a negative value is highest for `below` (6-12 of 18-25 cells at each
  t). It is lowest for `other` and `working` (0-4 of 18-36).
- Families closest to a "cut it" signal, all below the bar:
  - RW3 `below` at t 10-30: -0.04 to -0.09 (t -1.0 to -2.0).
  - RW7 `below` at t 15-60: -0.01 to -0.02.
  - L3 `faded` / `working` at t 45-60: -0.02 to -0.06, with halves that disagree.
  - MF2 `below` at t 30: -0.08 (t -1.7).
  - These are the cells a remedy team could pre-register. None is evidence on its own.
- **Live (descriptive):**
  - The only side-level cells with t <= -2: long `below` at t 5 (-0.09, t -2.2) and short `below` at t 60 (-0.07,
    t -2.5). Short `faded` at t 5 is -0.49 (n 60).
  - Short `working` from t 15 and short `other` from t 60 favour holding (+0.10 to +0.16, t up to 2.6).
  - The most negative family cells: GEN long `below` at t 5 (-0.19, t -2.7); heat_fade_long `flat` at t 30-45
    (-0.17); CWT12 long `below` at t 30-60 (-0.11 to -0.13); CWT13 short `other` at t 10-15 (-0.25).
  - Positive: L3 short `flat` at t 5-15, +0.30 to +0.33 (t 3.6-4.4). Holding a stalled L3 short is where its record
    comes from. RW7 short `other` / `working`: +0.12 to +0.21.
- **Reading:** in this record, "historically not going to work out" is not visible from the R path alone at any
  checkpoint from 5 to 120 minutes. The `faded` trades that the owner describes ("the entry looked good, it was up,
  now it isn't") are worth more held than cut, in the lab and in most live families. Earlier exits pay the exit cost
  and give up the trades that come back. Where giveback is large, it comes from target geometry (pocket 1), from
  having no target at all (pocket 2) and from book-wide market reversals (pockets 3 and 6). These are the places to
  aim.

## Caveats
- **The lab is not the live book.**
  - Entry is the signal-bar close, R = 0.25 x ATR(day) x dn, and the stop is checked first inside a minute.
  - Holds run to 15:54. No ETB, stacking, latch or slippage model.
  - GEN hold/holdtr lists are absent.
  - The first-signal-per-day filter drops refires.
- **The live record is short.** 33 sessions, so the live (c) cells are descriptive only.
- **Live account-day MTM is gross on open lots and net on realized lots.** Lots are summed in R, which assumes equal
  risk. Bars start the minute after entry.
- **The account-day "late entries" split is mechanical.** A late entry is any entry after the peak minute, and the
  peak is chosen with hindsight.
- **The early-exit cost assumption drives the sign of the small (c) margins.** With frictionless exits, most cells
  sit near 0 (within about ±0.03).

## Rule / config changes inside the live window (research/ledger.jsonl) — results above span them
- **10-16 / 10-17:** Testing2 CWT14 scale-out (bank half at +0.25R, rest to breakeven), then 4 more setups at +0.35R.
  This produces the 309 `scaled+*` exits, which are not counted as stops here.
- **10-23:** per-setup loss latch, and the Testing setup stop off.
- **10-26:** Gen caps raised (GX2).
- **10-28:** Primary sizing changed twice (to about $5k, then about $4k; slots 160 → 61 → 77).
- **10-29:** Primary -2R per-setup latch. This truncates late entries on bad days.
- **10-30:** Testing cost filter (CF).
- **11-12:**
  - LR1 flatten at 15:55.
  - LR3 latch and halt counted in R after costs.
  - LR8 cost model. Every row here is re-costed to LR8.
  - Gen and Graveyard sizing/caps (REPV).
- **11-17:**
  - TSZ1 testing sizing.
  - SPYEXIT engine and its WB4 copies (LiveLab RW3, TestingD RW5): 10 `spy_exit` exits.
- **11-19:** C3 Epoch 1 (EXIT100, ROT, WB5, U9-TGT, U9-ETB, TAGS1).
- **11-20 (after the window):** broker stop rounding fix.

Account-day and family figures spanning these dates mix rule regimes.

## Prior results respected (not repeated)
- **Book-wide exits that failed:**
  - L16 near-target breakeven: research/bdi/1119, -0.007R per trade, 1 of 35 families better.
  - Book-wide breakeven: kept off.
- **Earlier-exit classes:** W5 X1/X2/X3 hurt gap-down short fades (research/crunch/w5_workbench). The (c) map is the
  wider version of X3, and it agrees.
- **Wave 2:** trail after +1R and target-from-fill parked; 1.25x target on RW3/RW5 optional (research/crunch/WAVE2.md).
  Pocket 1 suggests the targeted, geometry-specific form of target-from-fill.
- **Open idea:** `xa-1105-hwm-giveback-exit` is still idea-only. Pocket 2 (GEN holds) is where it would have the
  most to work with.
- **Remedy test method:** WB2 (paired scoring on the parent's own signals, pooled by mechanism family, configs
  counted).
