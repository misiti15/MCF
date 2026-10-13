# More long opportunities (BDI, owner request 2026-10-12)

*Educational only - not financial advice. Q1/Q2 are backtests on the open two-year history (426 sessions,
2024-10..2026-10-07), with costs in. Q3 mixes live **paper** journals (descriptive, rule 7) with lab replays. The
rule-19 locked block (2024-11-01..2025-02-28) was never loaded, and no holdout was scored. The grid was pre-declared
in `PLAN.md` before anything was scored. One amendment (A1) was added before Mf was computed: Mf was dropped, with
the reason given there.*

**Configurations scored: 580** (Q1 96, Q2 484), which is exactly the declared N. Bars:
- Study-only: t >= 3.57.
- Q1 lineage (MF + trendguard 9,132): t >= 4.27.
- Q2 lineage (+ CWT05 flush 30,970): t >= 4.55.

Q3 adds 16 entry-count replays (lab R only; no new setup is scored).

## Failures first
- **0 of 580 configurations pass.**
  - Research gate (`gates.verdict` keep): 0.
  - Pre-declared Testing-1 bar: 0 of 11 finalists.
  - The best open-history t of any long configuration is **0.52** (Q1 MF4 long hold-to-close, n 3,235, +0.039R).
- **Q1: the MF metric is not inverted.**
  - On the symmetric 1R/1R exit, long and short gross expectancies are mirror images and close to zero: |gross| <= 0.065R, |t| <= 2.
  - After costs, both sides lose on every MF setup.
  - The sign of an MF trade is set by the **session regime**. The short side earns +0.03..+0.19R in down sessions and loses -0.23..-0.38R in up sessions, and the long side does the mirror.
  - So the owner's five losers are what the short side does on up-drift names. They are not evidence that the signal points the wrong way.
- **Q2: the owner's "open flush, then a hard swing up" long has no edge.**
  - 18 of 484 configurations have a positive open expectancy (n >= 150), and every one of them is a hold-to-close variant.
  - Those 18 are long beta: about +0.5..+1.1R in up sessions and -0.8..-1.2R in down sessions. Their excess over the same-minute long control is about 0 (best excess t 0.41).
  - Every finalist is positive on train and negative on valid.
  - The reversal triggers add nothing over the flush alone or a random long bar. Median open expectancy: RB -0.086, VR -0.088, HL -0.093, flush-only -0.093, random bar -0.100R.
- **Q3: primary does not lose long trades to crowding. It has almost no long setups.**
  - Live (Oct 6-12): 1 of 80 long signals was blocked "already in symbol".
  - Lab: 3.7% of primary long signals are lost.
  - Primary's only long setups, NS1 and NS5, produce about 4 signals a day in the lab and 1-2 a day live (1 on 10-12).
  - No crowding mechanism adds a meaningful number of primary long trades: every one adds 0 to 0.15 a day.
  - The mechanisms matter only in the Testing accounts.

## Q1. The opposite side of the MF flow-sell family (`results.csv`, rows `Q1-*`)
Setup:
- Signals: the live masks and windows (MF1 09:50-10:30, MF2/3/4 09:50-11:00, MF5 09:50-15:00), the first bar per symbol-day, adv20 >= $95M.
- FAM is the union of the five.
- R = 0.25 x daily ATR.
- "net" includes production costs: the tod entry multiplier, x3 on the extended tier, and the stop extra.

| set | n | /day | short t1s1 gross | long t1s1 gross (t) | short t1s1 net | long t1s1 net | short HTC net | long HTC net | long HTC gross train / valid | short t1s1 up / down sessions | best long config (exp, t) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MF1 | 2,389 | 6.2 | +0.065 | -0.065 (-1.72) | -0.056 | -0.195 | -0.225 | -0.020 | +0.200 / -0.021 | -0.33 / +0.19 | long d0 HTC (-0.020, -0.24) |
| MF2 | 610 | 2.5 | -0.023 | +0.020 (0.41) | -0.075 | -0.028 | -0.091 | -0.003 | +0.220 / -0.064 | -0.23 / +0.03 | long d0 HTC (-0.003, -0.03) |
| MF3 | 4,136 | 9.9 | +0.027 | -0.027 (-0.95) | -0.086 | -0.141 | -0.124 | -0.097 | +0.096 / -0.094 | -0.30 / +0.14 | long d3 HTC (-0.076, -1.54) |
| MF4 | 3,318 | 8.0 | -0.034 | +0.033 (0.92) | -0.131 | -0.060 | -0.221 | **+0.039** | +0.235 / +0.028 | -0.38 / +0.06 | long d0 HTC (+0.039, 0.52) |
| MF5 | 6,827 | 16.1 | +0.041 | -0.041 (-1.99) | -0.057 | -0.144 | -0.075 | -0.124 | +0.061 / -0.137 | -0.28 / +0.16 | long d3 t05s1 (-0.101, -7.0) |
| FAM | 10,124 | 23.8 | +0.022 | -0.022 (-1.07) | -0.071 | -0.117 | -0.115 | -0.068 | +0.106 / -0.065 | -0.30 / +0.13 | long d0 HTC (-0.068, -1.49) |

**Verdict per setup** (pre-declared test: "inverted" means a positive gross long with t >= 2 on the open history and positive gross in both train and valid):
- MF1, MF3 and MF5: **not inverted.** The short side is the slightly better gross side, and the long side is worse after costs.
- MF2 and MF4: **not inverted** by the test. The gross long t1s1 is +0.02/+0.03R with t 0.4/0.9.
  - MF4 long hold-to-close is the best long line in the study: +0.039R, t 0.52, train +0.137 / valid -0.056, up +0.70 / down -0.51.
  - Its same-time excess is +0.093R (t 2.07). That is the most interesting number in Q1, but it is far below the 4.27 bar, and valid is negative.
- Delayed long entries (5 or 15 minutes after the MF bar) change little: -0.01..+0.07R versus delay 0, and none turns positive with t > 0.4.

**What the owner saw on 10-12** (journal + `nightly1012/trades.csv`, paper):

| trade | entry | R | MFE / MAE (R) | 1R/1R opposite side |
|---|---|---|---|---|
| ZBH MF3 | 10:51 | -1.03 | 0.26 / 1.06 | target first |
| HSBC MF4 | 09:55 | -1.12 | 0.00 / 1.19 | target first |
| BBY MF5 | 11:00 | -0.46 | 0.36 / 0.51 | neither (flattened) |
| SM MF2 | 10:41 | -1.19 | 0.68 / 1.06 | target first |
| DUK MF3 | 10:46 | -1.04 | 0.09 / 1.03 | target first |

- The 20 primary MF trades that day averaged **+0.34R**, and the opposite 1R/1R would have won on only 4 of the 20.
- The five worst are the tail of a day the family won. In the two-year lab, MF longs win in up sessions and lose in down sessions, as above.
- Picking the side needs the day's direction. regime1009, indexlink (912 configurations) and bdi1012 (800) found no entry-time rule that supplies it.

## Q2. "Open flush, then a hard swing up" long (`results.csv`, rows `Q2-*`; `finalists.csv`)
The grid (PLAN section 2):
- Flush: 12 definitions. The reference is the open (O) or the prior close (PC); the depth is 0.5, 0.75 or 1.0 ATR; the window is the first 10 or 20 minutes.
- Trigger: RB (a close above the 09:45/09:50 bar high), VR (VWAP reclaim) or HL (higher low).
- Filter: none, prior-day close location >= 0.5, or SPY above its open.
- Exit: 4 exits.
- Entries: 09:50-10:30.
- Controls: flush-only (enter at 09:50) and a random long bar.

**Medians by grid dimension** (open-history expectancy, R):

| dimension | values |
|---|---|
| exit | t1s1 -0.089, t05s1 -0.090, t1s05 -0.092, HTC -0.094 |
| trigger | RB -0.086, VR -0.088, HL -0.093, flush-only -0.093, random -0.100 |
| filter | none -0.085, prior-day close location -0.104, SPY up -0.076 |
| reference | O -0.107, PC -0.073 |
| depth | 0.5 -0.087, 0.75 -0.092, 1.0 -0.097 (a deeper flush is worse, not better) |

**Finalists** (the top 5 by train t with n_train >= 150, plus the best per trigger; all fail):

| config | train n / exp / t | valid n / exp / t | open n / exp / t | up / down | WF | ex-best | busiest | same-time excess (t) | plateau | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| PC-x0.75-W10-RB-spy-HTC | 6,491 / +0.147 / 0.75 | 6,108 / -0.071 / -0.43 | 12,599 / +0.041 / 0.32 | +0.72 / -1.17 | 0.35 | -0.031 | 5.7% | -0.050 (-0.80) | +0.001 | fail |
| PC-x0.75-W20-RB-spy-HTC | 7,305 / +0.140 / 0.74 | 6,883 / -0.062 / -0.40 | 14,188 / +0.042 / 0.34 | +0.72 / -1.17 | 0.35 | -0.023 | 5.2% | -0.049 (-0.82) | -0.001 | fail |
| PC-x1.0-W10-RB-spy-HTC | 3,233 / +0.207 / 0.84 | 2,844 / -0.234 / -1.28 | 6,077 / +0.001 / 0.01 | +0.73 / -1.21 | 0.29 | -0.126 | 9.5% | -0.099 (-1.21) | +0.034 | fail |
| PC-x1.0-W20-RB-spy-HTC | 3,678 / +0.230 / 0.94 | 3,238 / -0.189 / -1.04 | 6,916 / +0.034 / 0.20 | +0.76 / -1.18 | 0.29 | -0.087 | 9.1% | -0.077 (-0.98) | +0.001 | fail |
| PC-x1.0-W20-VR-none-HTC | 5,478 / +0.201 / 0.72 | 5,549 / -0.143 / -0.88 | 11,027 / +0.028 / 0.17 | +1.06 / -0.88 | 0.41 | -0.089 | 5.4% | -0.011 (-0.17) | +0.015 | fail |
| PC-x1.0-W20-HL-spy-HTC | 4,823 / +0.138 / 0.70 | 4,948 / -0.187 / -1.16 | 9,771 / -0.027 / -0.20 | +0.72 / -1.09 | 0.24 | -0.109 | 6.4% | -0.079 (-1.19) | -0.041 | fail |

The Q1 finalists (MF1, MF2 d0/d1, MF4 d0/d1, all long HTC) are in `finalists.csv`. All fail:
- valid is negative for every one;
- WF is 0.29-0.56;
- ex-best-day is <= 0 except MF4 d1 (+0.005).

**Comparison with the existing longs** (lab, current windows, `tables/q2_compare_longs.csv`; LIQ from reddit1012liq):

| setup | n | /day | exp R | t | up / down |
|---|---|---|---|---|---|
| NS1 (09:50-11:30) | 444 | 1.0 | +0.034 | 0.87 | +0.10 / -0.01 |
| NS1, entries 09:50-10:30 only | 134 | 0.3 | -0.008 | -0.08 | +0.14 / -0.22 |
| NS5 (09:50-11:30) | 1,305 | 3.1 | -0.039 | -0.47 | +0.10 / -0.20 |
| NS5, entries 09:50-10:30 only | 171 | 0.4 | +0.026 | 0.21 | +0.68 / -0.16 |
| heat_fade_long (11:05-13:30) | 14,460 | 33.9 | -0.046 | -1.16 | +0.08 / -0.15 |
| heat_fade_long-FD, 09:50-10:30 | 7,394 | 17.4 | -0.051 | -1.78 | +0.16 / -0.16 |
| LIQ-orl-sweep-open15-s25-long | 13,335 | 31.3 | -0.001 | -0.01 | +0.59 / -0.49 |
| LIQ-pdl-sweep-open15-vwap-long | 160 | 0.4 | +0.088 | 0.58 | (train -0.22 / valid +0.55) |
| **best flush long (this study)** | 18,903 | 44.7 | +0.048 | 0.39 | +1.03 / -0.86 |
| random long bar 09:50-10:30, t1s1 / HTC | 386,045 | 906 | -0.105 / -0.094 | | +0.13 / -0.32 (t1s1) |

The owner's pattern sits in the same place as every long tested so far: near zero, with the session's direction deciding the sign. This is the same conclusion as turns T2 stage C (S2 "1-minute flush", S3 "flush into a level": 0 of 80) and CWT05 flush (B5).

## Q3. Crowding, live (paper journals; `crowd_live.py`, `tables/crowd_long_per_day.csv`)

| account | day | long signals | taken | already in symbol (held by short / long) | cap skips | spread skips | what-if R of blocked longs |
|---|---|---|---|---|---|---|---|
| primary | 10-06 | 44 | 27 | 1 (1 / 0) | 0 | 16 | +0.89 (n 1) |
| primary | 10-07 | 8 | 7 | 0 | 0 | 1 | |
| primary | 10-08 | 8 | 6 | 0 | 0 | 2 | |
| primary | 10-09 | 19 | 16 | 0 | 0 | 3 | |
| primary | 10-12 | **1** | 1 | 0 | 0 | 0 | |
| Testing 1 | 10-09 | 14 | 11 | 1 (0 / 1) | 0 | 2 | |
| Testing 1 | 10-12 | 82 | 49 | **25 (11 / 14)** | 0 | 7 | +0.093 (n 26, both days) |
| Testing 2 | 10-12 | 702 | 287 | **302 (2 / 300)** | 37 (CWT12-coil-k4 cap 25) | 71 | **-0.254** (n 302) |

- **Primary.**
  - Long volume fell from 27 a day (Oct 6, when heat_fade_long and orb20_a still ran there) to 1 on 10-12, after the 10-11 demotions.
  - What is left: NS1 (3 trades, +0.48R live) and NS5 (5 trades, +0.51R live).
  - Shorts blocked by shorts: 30. Longs blocked: 1.
- **Testing 1, 10-12.**
  - 11 longs were blocked by shorts: ST2-FD 9 (by RW7-FD, heat_fade_short-FD, RW5-FD, MF-FD), ST4-FD 2.
  - 14 longs were blocked by longs: heat_fade_long and heat_fade_long-FD blocking each other (12), plus ST7/ST4.
  - Shorts blocked: 143, of which 133 were held by shorts.
- **Testing 2.** The crowding is long-on-long: CWT14 variants block each other.
  - 300 of 302 blocks came from another CWT long.
  - The blocked signals' what-if is worse than the taken ones (-0.254R).
- **Slots never bound** in any account. Peaks: 34 of 160 primary, about 101 of 400 Testing 1, about 137 of 400 Testing 2.

## Q3. Mechanisms, quantified (lab replay, `crowd_lab.py`, `tables/crowd_lab_*.csv`)
How the replay works:
- 426 sessions, hold 120 minutes, and the live rule: one position per symbol, earlier signal wins, same bar goes to setup_order, no retry.
- Primary: the 11 current setups. Testing 1: 35 setups in the lab (LIQ and L3 x3 are missing).
- "Extra" means trades a day versus M0, with the lab R of those trades.

| mechanism | primary: extra longs/day (R) | primary: shorts displaced/day | Testing 1: extra longs/day (R) | Testing 1: shorts displaced/day (R) | Testing 1 net R/day | implementation |
|---|---|---|---|---|---|---|
| M0 baseline | 3.95 taken of 4.11 (lost 3.7%) | - | 77.5 taken of 138.5 (lost 44%: 26.6/day to shorts, 33.3 to longs) | - | - | - |
| Ma side-aware priority (longs first on the same bar) | 0.00 | 0.00 | +0.31 (-0.12) | 0.31 | -0.06 | ~10 lines (`setups.py` sort key) |
| Mb reserve 10% / 25% of slots for longs | 0.00 / 0.00 | 0.00 / 0.11 | +0.01 / +0.47 | 0.05 / 1.65 | +0.04 / -0.16 | ~20 lines (`risk.check`); **no effect while slots never bind** |
| Mc same-direction pyramid (a long may join a symbol held only by longs, max 2) | 0.00 | 0.00 | **+29.7 (-0.013)**, 1.0 lost | 2.7 (-0.053) | -0.17 | ~40 lines (`risk.check`, `open_symbols` becomes a count by side, flatten and reconcile per order id); doubles per-symbol exposure |
| Ma + Mc | 0.00 | 0.00 | +30.1 (-0.014) | 3.1 | -0.23 | as above |
| Md shadow trades (count the what-if of blocked longs) | +0.15 statistical (+0.138) | 0 | **+60.9 statistical (-0.034)** | 0 | 0 (no capital) | housekeeping: the what-if already runs (`runner.what_if`); add per-setup "shadow n / R" to the scorecard and playing-time report |
| Me long setups alone in a long-only book (upper bound for "move longs to the account with the fewest longs") | +0.13 | n/a | +19.7 (-0.047); still lose 31% to each other | n/a | | config only; but no account has spare long room (Testing 2 is long-saturated by CWT14, and primary takes only gate-passers) |
| Mf retry after release (amendment A1: not replayed) | ~0 (primary longs lose 2-4%) | - | not quantified | - | - | ~15 lines: today `runner.seen` marks a blocked (symbol, setup) as done for the day, so a long blocked at 10:00 by a short that exits at 10:40 never re-checks |

Per long setup (Testing 1, lab), the share of signals lost at M0 → Mc → Me (long-only book):

| setup | M0 | Mc | Me |
|---|---|---|---|
| ST8-FD | 67% | 31% | 51% |
| ST4-FD | 65% | 40% | 40% |
| NS5-FD | 42% | 33% | 24% |
| ST2-FD | 43% | 35% | 13% |
| heat_fade_long | 44% | 22% | 35% |
| heat_fade_long-FD | 47% | 17% | 42% |
| ST1-FD | 41% | 26% | 25% |
| ST7-FD | 27% | 23% | 7% |
| NS1-FD | 13% | 13% | 0% |

The blocked signals' lab expectancy is close to that of the taken ones (for example ST2-FD -0.002 vs -0.016, heat_fade_long-FD -0.032 vs -0.031). So more long playing time adds sample, not P/L.

### Ranked recommendation (Q3)
1. **Md shadow trades. Ship as housekeeping.**
   - It gives every long setup "playing time" statistically, with no capital and no change to which trades are taken: about +61 long samples a day in Testing 1 and about 340 in Testing 2 live.
   - Report the what-if per setup next to the real trades (taken n / R, shadow n / R, by blocker side), as RESEARCH_RULES rule 20 already asks for context on lost signals.
   - Label them as simulated (rule 7). The what-if fill is optimistic: no realism checks.
2. **Mf retry after release, plus Ma side-aware priority. Small, low-risk Testing-only changes** (backlog, merged after the close).
   - They recover blocked longs that a short or another long held earlier. Ma alone is worth only about 0.3 a day, because collisions are mostly not on the same bar.
3. **Mc same-direction pyramid. Testing 1 only, if the owner wants volume.**
   - It is the only lever that adds trades at scale: about +30 longs a day in Testing 1, and about 300 a day in Testing 2 (all CWT longs).
   - It doubles exposure on one name, the extra trades are not better (-0.013R lab; Testing 2 blocked what-if -0.254R), and it displaces about 3 shorts a day.
   - Do not use it in primary or Testing 2.
4. **Not recommended: Mb reserved long slots** (slots never bind, so the effect is 0) **and Me moving long setups** (primary has no long crowding; Testing 2 is long-saturated; Testing 1 longs lose a third even among themselves).
5. **The real constraint in primary is supply.**
   - Only NS1 and NS5 are long, about 1-2 signals a day live.
   - None of the 580 long-side configurations tested today, the MF opposite side or the flush long, clears even the Testing bar.
   - More long trades in primary need a long setup that passes the gates. That is a research question, not a crowding one.

## Files
- `PLAN.md`: the pre-declaration and amendment A1.
- Pipeline:
  - `prep.py` builds the compact frames, head/tail bars and prior-day close location into `data/`.
  - `score.py` scores all 580 configurations into `results.csv`.
  - `report.py` does the finalists, plateau and Testing bar, writing `finalists.csv` and `summary.json`. It is split out of score.py after a type bug in the plateau lookup; nothing was re-scored.
- `crowd_live.py` reads the live journals and writes `tables/crowd_signals.csv` and `tables/crowd_long_per_day.csv`.
- `crowd_lab.py` runs the mechanism replays and writes `tables/crowd_lab_mechanisms.csv` and `tables/crowd_lab_{primary,testing1}_longs.csv`.
- `data/` is git-ignored: the journals and the compact frames.
