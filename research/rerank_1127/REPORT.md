Educational only — not financial advice.

# Weekly top-20 re-rank by avg R w/o best day — 2026-11-27 (owner request 11-25)

- **What:** the non-Graveyard setups, ranked by **avg R per trade without their single best session** (min 20 trades),
  instead of the dashboard's shrunk score. One row per setup, every account's record merged exactly as the dashboard
  leaderboard does it (`docs/live/index.html`: scorecard sums merged, best day found on the merged per-session record).
- **Data:** `origin/mcf-data*/reports/scorecard.json` of all ten accounts, EOD reports generated 2026-11-27 12:58-12:59 ET
  (half day; LR1 flatten 12:55, so 11-27 is complete), and `docs/live/assignments.json` (last change 2026-11-25 17:49 ET,
  i.e. it already includes the ROT-B3 / GYH moves effective 11-27). Records run from each setup's first live trade
  (earliest 10-06) through 11-27. Read with `git show` only; no broker or MarcoFlow call was needed.
- **Costs in:** every R is the scorecard's R after costs on the single **LR8 cost basis** (LR8 live cost model from 11-12;
  DQ-P3 restates every record spanning 11-12 on that basis). Paper trades (rule 7): a ranking, not evidence of an edge.
- **Eligible:** assigned to a non-Graveyard account now (Primary, On Deck, Testing A-F), not `no_leaderboard`; GEN-* only
  when graduated to a testing area (non-graduated GEN-* in the Setup Generator account out); Graveyard-only setups out.
  137 eligible setups, **84 with >= 20 trades and two or more traded sessions** (a one-session record has no
  "w/o best day": NM-RWN5-ns3-mon-weakrs-short-WB3, 32 trades in one session, shrunk #4, cannot be ranked).
- **No previous re-rank of this kind exists** (searched research/, the owner inbox, OPEN_ITEMS and decisions.json).
  "Last week's list" is therefore the previous weekly top 20: `research/bdi/top20/CONDITIONS.md`, 2026-11-21 block =
  the plain shrunk-score leaderboard as of 11-20 (>= 20 trades, all GEN-* out, graduates included). Today's plain
  shrunk-score top 20 is shown as well, so the effect of the new sort key is visible on its own.
- **Configurations tried: 1** (one ranking rule, as requested; no thresholds varied). Descriptive only: no setup, exit,
  config or assignment was changed. The locked block (2024-11-01..2025-02-28) was not read (no history data used).

## Rule changes in the windows (research/ledger.jsonl effective dates)
- **Inside the record window (10-06..11-27):** 10-28 ~$4k sizing; 10-29 Primary -2R latch; **11-12 LR8 cost model**
  (+ GEN-GRAD, ODX-1, testing caps 10 -> 30, account halts 300R); 11-17 **TSZ1** testing half-size lots (R comparable,
  $ not); 11-19 C3 bundle (NS5 out of Primary, EXIT100, ROT2) and DQ-P3 one LR8 basis; 11-20 stop rounding,
  FOOTRACE-EXIT, ROT block 2, ult_1119 admissions; 11-22 owner yes to a rules study of a per-setup -2R latch for
  every setup (ledger `2026-11-22-owner-answers`; a study approval, Primary keeps its 10-29 latch); 11-23 BRAKE-BURST
  (30 entries / setup / 10 min, every account), watchdog act everywhere, ST7 Primary -> On Deck, Remedy-Q 12:30 copies.
- **Inside this week (11-23..11-27):** the 11-23 changes above; **11-25** was the squeeze day (SPY V-turn; gap-down short
  families stopped en masse; no ledger change that day). **11-27: ROT-B3** (arena block 3: 8 to the Graveyard, 3 On Deck
  OD-OUT exits, 7 rebalance moves, 25 rare-tagged) and **GYH V1+V3** (9 arena setups at the floor to the Graveyard,
  18 Graveyard setups archived), plus 10 new Setup Generator seeds (not eligible). Moves effective 11-27 that touch
  this list: GEN-261021-01 and GEN-261023-09 (Graveyard -> Testing E), GEN-261029-07 (Testing C -> Testing F),
  ST3-rsi5up (Testing C -> Testing B). Their records before 11-27 were made in the old account; only 11-27 is new.
- Accounts mix these: a setup's record before and after 11-17 / 11-23 is not the same rule set.

## 1. New top 20 (avg R w/o best day, >= 20 trades)
"t" = trade-level t of the merged record; "day t" = t of the per-session mean R (WW-CLUSTER). `1 day` = best session
>= 50% of total R; a share > 100% means the rest of the record is net negative; "–" = total R <= 0.

| # | setup | account now | trades | sess | avg R | avg R w/o best day | best day (share) | trades left w/o best day | t | day t | shrunk rank | record from |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | NM-RWN5-ns3-mon-weakrs-short | Testing D | 52 | 4 | +0.179 | **+0.530** | 11-23 (55%) `1 day` | 8 | +1.40 | +2.73 | 10 | Testing A 7 + Testing D 45 |
| 2 | GEN-261021-01 | Testing E | 27 | 7 | +0.318 | **+0.318** | 11-13 (52%) `1 day` | 13 | +2.12 | -0.05 | 5 | Gen 14 + Graveyard 10 + Testing E 3 |
| 3 | GEN-261026-03 | Testing D | 27 | 7 | +0.313 | **+0.127** | 10-27 (70%) `1 day` | 20 | +1.37 | -0.02 | 6 | Gen 21 + Testing D 6 |
| 4 | GEN-261027-01 | Testing E | 42 | 10 | +0.185 | **+0.105** | 11-23 (62%) `1 day` | 28 | +2.08 | +2.53 | 11 | Gen 14 + Testing E 28 |
| 5 | GEN-261023-09 | Testing E | 82 | 4 | +0.149 | **+0.069** | 11-24 (67%) `1 day` | 58 | +2.13 | +0.85 | 12 | Gen 10 + Graveyard 27 + Testing E 45 |
| 6 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB4 | Testing D | 26 | 5 | +0.179 | **+0.064** | 11-17 (70%) `1 day` | 22 | +1.48 | +0.99 | 14 | Testing D 26 |
| 7 | GEN-261029-06 | Testing D | 295 | 12 | +0.111 | **+0.042** | 11-20 (67%) `1 day` | 255 | +3.23 | +1.23 | 13 | Gen 85 + Testing D 210 |
| 8 | CWT14-failbrk-orl-p10-long-WB5 | Testing D | 148 | 7 | +0.076 | **+0.035** | 11-18 (76%) `1 day` | 77 | +2.19 | -0.63 | 19 | Testing D 148 |
| 9 | GEN-261026-07 | Testing A | 238 | 8 | +0.416 | **+0.029** | 11-20 (95%) `1 day` | 159 | +6.60 | +0.92 | 3 | Testing A 163 + Gen 75 |
| 10 | NM-RWN3-ns3-spyup-early-short | Testing B | 24 | 8 | +0.262 | **+0.026** | 11-06 (93%) `1 day` | 18 | +1.33 | +0.12 | 8 | Testing A 6 + Testing B 18 |
| 11 | GEN-261019-02 | Testing E | 26 | 9 | +0.081 | **+0.023** | 11-18 (75%) `1 day` | 23 | +0.67 | +0.02 | 22 | Gen 8 + Testing E 13 + Testing F 5 |
| 12 | GEN-261029-07 | Testing F | 70 | 7 | +0.070 | **+0.007** | 11-20 (92%) `1 day` | 57 | +1.29 | +0.08 | 21 | Gen 22 + Testing C 48 |
| 13 | L3-gap-slope-fromopen-FD | Primary | 460 | 30 | +0.073 | **+0.005** | 10-20 (94%) `1 day` | 380 | +1.73 | -1.09 | 18 | Primary 238 + On Deck 222 |
| 14 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | Primary | 238 | 33 | +0.083 | **+0.005** | 10-22 (95%) `1 day` | 209 | +1.57 | +0.25 | 17 | Primary 205 + On Deck 33 |
| 15 | RW3-gapdn-rsi5pop-flowsell-short-FD | Primary | 242 | 33 | +0.100 | **+0.004** | 10-22 (97%) `1 day` | 217 | +1.73 | +0.24 | 15 | Primary 204 + On Deck 38 |
| 16 | ST3-rsi5up-short-pm-t1s1-FD | Testing B | 36 | 12 | +0.063 | **-0.003** | 11-23 (103%) `1 day` | 26 | +0.66 | +0.49 | 23 | On Deck 2 + Testing C 29 + Testing B 5 |
| 17 | GEN-261019-10 | Testing F | 142 | 16 | +0.066 | **-0.008** | 11-05 (111%) `1 day` | 131 | +1.07 | -0.16 | 20 | Gen 86 + Testing F 56 |
| 18 | NM-RWR4-ns2-up3-qqqup-slopedn-short | Testing E | 37 | 7 | +0.134 | **-0.014** | 11-12 (104%) `1 day` | 13 | +1.56 | +0.97 | 16 | Testing A 5 + Testing B 27 + Testing E 5 |
| 19 | ULT-05-withgap-cont-long | Testing E | 467 | 5 | -0.025 | **-0.056** | 11-27 (–) | 348 | -2.45 | +0.88 | 30 | Testing E 467 |
| 20 | NM-RWN4-ns2-spyup05-notfri-short | Testing D | 40 | 2 | +0.223 | **-0.066** | 11-12 (106%) `1 day` | 8 | +3.16 | – | 7 | Testing A 8 + Testing F 32 |

**Read-outs**
- **Every one of the 20 is a `1 day` record** (the only exception, ULT-05-withgap-cont-long, has a negative total).
  Only **15** of the 84 have a positive avg R w/o best day; ranks 16-20 are already below zero, so the list is a
  top 15 plus five least-bad.
- **Thin samples at the top:** #1 NM-RWN5-ns3-mon-weakrs-short (4 sessions) keeps only **8 trades** once its best day
  (11-23, 44 trades +5.08R) is removed; #2 GEN-261021-01 keeps 13, #18 NM-RWR4 13, #20 NM-RWN4 8 (2 sessions; day t
  undefined). Their w/o-best-day averages are small-n and should not be read as the strongest records.
- **Most robust of the positives (n left >= 50 and avg w/o best > 0):** GEN-261029-06 (255 left, +0.042R, t 3.23 /
  day t 1.23), GEN-261023-09 (58 left, +0.069R), CWT14-orl-p10-WB5 (77 left, +0.035R), GEN-261026-07 (159 left,
  +0.029R; 95% of R on 11-20 and no trade this week), GEN-261029-07 (57 left, +0.007R).
- **Primary trio at 13-15**, all ~+0.005R w/o best day (L3-fromopen 10-20 = 94% of R; RW5-FD 10-22 = 95%; RW3-FD 10-22 =
  97%). Without one October session each, the three Primary records are flat after costs. The fourth Primary setup,
  NM-ETF-late-dip-di-long, ranks #27 (53 tr, -0.050R; w/o best day -0.120R).
- **Generator graduates take 9 of 20 places** (last week's list excluded every GEN-* by rule, so 9 of the 13 entries
  below are a definition change, not new performance).

## 2. Who rotated in / out vs last week's top 20 (CONDITIONS.md 11-21 = shrunk score to 11-20)
- **Stayed (7):** L3-gap-slope-fromopen-FD (2 -> 13), RW3-FD (4 -> 15), RW5-FD (8 -> 14), NM-RWN4 (5 -> 20),
  CWT14-orl-p10-WB5 (9 -> 8), NM-RWR4 (11 -> 18), ST3-rsi5up-short-pm (20 -> 16).
- **In (13):** NM-RWN5-ns3-mon-weakrs-short (#1), GEN-261021-01, GEN-261026-03, GEN-261027-01, GEN-261023-09,
  RW5-FD-WB4, GEN-261029-06, GEN-261026-07, NM-RWN3-ns3-spyup-early, GEN-261019-02, GEN-261029-07, GEN-261019-10,
  ULT-05-withgap-cont-long. (9 GEN graduates were outside last week's definition.)
- **Out (13):** ULT-05-withgap-cont-short (1 -> 54), L3-gap-slope-lowdist-FD (3 -> 71), CWT09-g10 (6 -> 21),
  RW3-FD-WB4 (7 -> 35), NM-MF3 (10 -> 34), L3-gap-slope-rsi5hi-FD (12 -> 68), RW7-FD-WB3 (13 -> 40), RW7-FD (14 -> 22),
  MF4-h40 (15 -> 32), NS1 (16 -> 47), RW1-FD (17 -> 29), CWT12-flag (19 -> 26), RW6G1-ns2-up3-vwap2sd (18; in the
  Graveyard now, not eligible).
- **Versus today's plain shrunk-score top 20** (section 4): 16 names are shared. The new key drops the three biggest
  `1 day` records of the shrunk board, GEN-261022-05 (shrunk #1, w/o best day -0.179R, 122%), GEN-261023-07 (#2,
  -0.296R, 142%) and GEN-261027-10 (#9, -0.409R, 224%), plus the one-session NM-RWN5-WB3 (#4); it brings in
  GEN-261019-02, GEN-261029-07, ST3-rsi5up and ULT-05-withgap-cont-long (the last two only because the pool is thin).

## 3. This week (11-23..11-27, 4 sessions) for last week's top 20
Cells = trades / R after costs (LR8). Rank now = this re-rank / today's shrunk rank.

| last wk # | setup | account now | 11-23 | 11-24 | 11-25 | 11-27 | week trades | week R | week avg R | record to 11-20 (n, avg R) | rank now (w/o best / shrunk) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ULT-05-withgap-cont-short | Testing E | – | 39 / -3.43 | 46 / -21.39 | – | 85 | -24.83 | -0.292 | 24, +0.456 | 54 / 62 |
| 2 | L3-gap-slope-fromopen-FD | Primary | 5 / -2.77 | 3 / -3.87 | 35 / -34.98 | 7 / -5.39 | 50 | -47.00 | -0.940 | 410, +0.196 | 13 / 18 |
| 3 | L3-gap-slope-lowdist-FD | On Deck | 2 / -1.25 | – | 198 / -144.62 | 1 / -1.07 | 201 | -146.94 | -0.731 | 111, +0.208 | 71 / 77 |
| 4 | RW3-gapdn-rsi5pop-flowsell-short-FD | Primary | 6 / +3.61 | 12 / -7.05 | 5 / -6.16 | 5 / -1.43 | 28 | -11.03 | -0.394 | 214, +0.165 | 15 / 15 |
| 5 | NM-RWN4-ns2-spyup05-notfri-short | Testing D | – | – | – | – | 0 | +0.00 | – | 40, +0.223 | 20 / 7 |
| 6 | CWT09-gapdn-vwaploss-g10-short | On Deck | 1 / -0.47 | 1 / -1.07 | 3 / -3.10 | – | 5 | -4.64 | -0.929 | 24, +0.218 | 21 / 26 |
| 7 | RW3-gapdn-rsi5pop-flowsell-short-FD-WB4 | Testing C | 2 / -0.38 | 13 / -3.95 | 5 / -2.99 | 2 / -0.90 | 22 | -8.22 | -0.374 | 22, +0.218 | 35 / 40 |
| 8 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | Primary | 7 / -3.35 | 8 / -1.19 | 1 / -1.17 | 3 / +1.17 | 19 | -4.54 | -0.239 | 219, +0.111 | 14 / 17 |
| 9 | CWT14-failbrk-orl-p10-long-WB5 | Testing D | 23 / -2.21 | 1 / -1.00 | 21 / +3.27 | 27 / +3.25 | 72 | +3.30 | +0.046 | 76, +0.104 | 8 / 19 |
| 10 | NM-MF3-qqqdn-gapdn-FD | Testing A | 2 / -1.03 | 11 / -0.03 | 3 / -3.32 | 2 / -1.28 | 18 | -5.66 | -0.314 | 68, +0.097 | 34 / 27 |
| 11 | NM-RWR4-ns2-up3-qqqup-slopedn-short | Testing E | – | 2 / +0.93 | 1 / +0.22 | – | 3 | +1.15 | +0.382 | 34, +0.113 | 18 / 16 |
| 12 | L3-gap-slope-rsi5hi-FD | On Deck | – | 46 / +5.97 | 311 / -219.08 | 3 / -0.33 | 360 | -213.44 | -0.593 | 167, +0.079 | 68 / 76 |
| 13 | RW7-gapdn-bounce-early-short-FD-WB3 | Testing E | – | 50 / -21.33 | – | 3 / +0.44 | 53 | -20.89 | -0.394 | 101, +0.077 | 40 / 50 |
| 14 | RW7-gapdn-bounce-early-short-FD | Testing F | 12 / +3.29 | 98 / -33.55 | 52 / -52.42 | 15 / -3.18 | 177 | -85.86 | -0.485 | 872, +0.051 | 22 / 35 |
| 15 | MF4-h40-open-flowsell | Testing A | 6 / +0.12 | 11 / -0.18 | 13 / -5.27 | 2 / -0.72 | 32 | -6.05 | -0.189 | 72, +0.019 | 32 / 34 |
| 16 | NS1-rsidip-rsi5pop-long | On Deck | 1 / +0.13 | 3 / -3.15 | – | – | 4 | -3.02 | -0.754 | 30, +0.007 | 47 / 39 |
| 17 | RW1-gapdn-bounce-flowsell-short-FD | On Deck | 7 / +1.43 | 39 / -7.53 | 21 / -21.63 | 8 / -3.29 | 75 | -31.02 | -0.414 | 243, +0.001 | 29 / 57 |
| 18 | RW6G1-ns2-up3-vwap2sd-short-FD | Graveyard | 2 / -0.32 | 2 / +0.69 | 9 / -8.05 | – | 13 | -7.69 | -0.591 | 67, +0.002 | out (GY) / – |
| 19 | CWT12-flag-s1-long | Testing C | 1 / -1.20 | – | 1 / +0.61 | – | 2 | -0.59 | -0.293 | 33, +0.002 | 26 / 29 |
| 20 | ST3-rsi5up-short-pm-t1s1-FD | Testing B | 10 / +2.34 | – | – | 5 / +0.06 | 15 | +2.40 | +0.160 | 21, -0.006 | 16 / 23 |

- **Last week's top 20: 1,234 trades, -614.55R this week (-0.498R per trade); 19 traded, 3 finished positive**
  (CWT14-orl-p10-WB5 +3.30R, ST3-rsi5up +2.40R, NM-RWR4 +1.15R). By day: 11-23 -2.06R, 11-24 -79.74R,
  **11-25 -520.08R (725 trades)**, 11-27 -12.67R. Two On Deck L3 shorts on 11-25 alone: L3-rsi5hi 311 trades
  -219.08R and L3-lowdist 198 trades -144.62R (the burst brake of 11-23 caps 30 entries per 10 min per setup, not per
  day). Without 11-25 the 20 still lost -94.47R on 509 trades (-0.186R per trade).
- The Primary trio together: 97 trades -62.58R (L3-fromopen -47.00R, 35 of its 50 trades on 11-25).
- Last week's #1 (ULT-05-withgap-cont-short) was a one-session record (24 tr, 11-20); this week 85 tr -24.83R.
- **For comparison only (in-sample, it shaped the new rank):** the new top 20 did 917 trades -41.40R this week
  (11-25 -43.71R; 11 of 17 that traded finished positive). This is not a forward test of the new list.

## 4. Today's plain shrunk-score top 20 (dashboard key, same eligibility, >= 20 trades)

| shrunk # | setup | account now | trades | avg R | avg R w/o best day | best-day share | w/o-best rank |
|---|---|---|---|---|---|---|---|
| 1 | GEN-261022-05 | Testing B | 223 | +0.445 | -0.179 | 122% `1 day` | 39 |
| 2 | GEN-261023-07 | Testing A | 139 | +0.459 | -0.296 | 142% `1 day` | 55 |
| 3 | GEN-261026-07 | Testing A | 238 | +0.416 | +0.029 | 95% `1 day` | 9 |
| 4 | NM-RWN5-ns3-mon-weakrs-short-WB3 | Testing E | 32 | +0.352 | – | – | – (1 session) |
| 5 | GEN-261021-01 | Testing E | 27 | +0.318 | +0.318 | 52% `1 day` | 2 |
| 6 | GEN-261026-03 | Testing D | 27 | +0.313 | +0.127 | 70% `1 day` | 3 |
| 7 | NM-RWN4-ns2-spyup05-notfri-short | Testing D | 40 | +0.223 | -0.066 | 106% `1 day` | 20 |
| 8 | NM-RWN3-ns3-spyup-early-short | Testing B | 24 | +0.262 | +0.026 | 93% `1 day` | 10 |
| 9 | GEN-261027-10 | Testing D | 176 | +0.146 | -0.409 | 224% `1 day` | 66 |
| 10 | NM-RWN5-ns3-mon-weakrs-short | Testing D | 52 | +0.179 | +0.530 | 55% `1 day` | 1 |
| 11 | GEN-261027-01 | Testing E | 42 | +0.185 | +0.105 | 62% `1 day` | 4 |
| 12 | GEN-261023-09 | Testing E | 82 | +0.149 | +0.069 | 67% `1 day` | 5 |
| 13 | GEN-261029-06 | Testing D | 295 | +0.111 | +0.042 | 67% `1 day` | 7 |
| 14 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB4 | Testing D | 26 | +0.179 | +0.064 | 70% `1 day` | 6 |
| 15 | RW3-gapdn-rsi5pop-flowsell-short-FD | Primary | 242 | +0.100 | +0.004 | 97% `1 day` | 15 |
| 16 | NM-RWR4-ns2-up3-qqqup-slopedn-short | Testing E | 37 | +0.134 | -0.014 | 104% `1 day` | 18 |
| 17 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | Primary | 238 | +0.083 | +0.005 | 95% `1 day` | 14 |
| 18 | L3-gap-slope-fromopen-FD | Primary | 460 | +0.073 | +0.005 | 94% `1 day` | 13 |
| 19 | CWT14-failbrk-orl-p10-long-WB5 | Testing D | 148 | +0.076 | +0.035 | 76% `1 day` | 8 |
| 20 | GEN-261019-10 | Testing F | 142 | +0.066 | -0.008 | 111% `1 day` | 17 |


## What this suggests (no decision asked)
- Ranked w/o the best day, the board has **8 positive records with >= 50 trades left** (5 testing setups plus the Primary trio at
  ~+0.005R) and none with a day t >= 2 among them (GEN-261029-06, day t 1.23, is the best). The weekly list is a watch list, not a promotion list; promotions keep
  going through C3-BAR2 (best-day share < 50%, which none of these 20 meets).
- The re-rank does what the owner asked: it pushes out records carried by one day (GEN-261022-05 / -23-07 / -27-10,
  ULT-05-short) and shows that the Primary trio's edge sits in two October sessions.
- Next week's re-rank (Fri 12-04) compares against section 1 of this report; the forward results of this list start 11-30.

## Files
- `research/rerank_1127/rerank.py` (merge + rank; `python research/rerank_1127/rerank.py <git dir with origin/mcf-data* fetched>`),
  `rerank.json` (all 84 ranked rows, shrunk top 20, last week's 20), `rerank_week.json` (per-day 11-23..11-27),
  `make_report.py` -> `tables.md` (the tables above).

Educational only — not financial advice.
