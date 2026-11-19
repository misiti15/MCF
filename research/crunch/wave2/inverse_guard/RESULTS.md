Educational only — not financial advice

# INV — inverse guard (root-cause remedy R1): results

Pre-registered in PLAN.md (this folder) before scoring. Research only: no config, setup, exit or order changed; nothing
committed by this stage. **Configurations tried: 7** (G1, G2, G3, M1, G1+M1, G1-ETBp, G2-ETBp), all reported.
Costs in (live: LR8 basis via mcf.costs.with_cost_r, which lowers pre-11-12 rows by 0.064R on Primary; lab: production
costs). Locked block 2024-11-01..2025-02-28 never read (lab file asserted to have 0 rows there). cache_fresh not used.

## Rule changes inside the windows (research/ledger.jsonl)
Live window 2026-10-06..11-19 (run 1, 10 accounts, 28,118 closed trades): stacking/refire rules 10-13/10-14; Primary
sizing 10-28 (twice); Primary -2R latch 10-29; ROLL1 low-rep homes 11-05; LR8 live costs 11-12 (all rows re-costed on
LR8 here); GY-BENCH 11-18; C3-EXIT100, C3-ROT/ROT2, U9-TGT and **U9-ETB (bulk borrow list) effective 11-19**. Rules
already effective 11-20 (not in any window here): 9 new testing setups (ultimate_1119), FOOTRACE-EXIT, GY-FOOTRACE,
stop-rounding fix. Lab window 2024-10-01..2026-11-04 (118 enabled lab setups, first fire per symbol-day, no caps, no
ETB); halves split at 2025-11-01.

## Classes (frozen, research/forward/compass_gate/shadow.py at b38a16981)
G1 = INVERSE ∪ LONG_VOL (107 names). G2 = index/sector/country row of INVERSE ∪ LONG_VOL (drops single-stock and crypto
inverse). G3 = broad-market inverse (18) ∪ LONG_VOL. M1 = the mirror (longs on G1). ETBp = lab shorts on symbols that
were ETB-skipped in >= 50% of their live short signal pairs are dropped from both arms (397 symbols; of the G1 names in
the lab only SQQQ, SOXS and PSQ survive it, so G1-ETBp = G2-ETBp exactly).

## 1. Headline (better / worse = setup x account live, setup in lab; delta = guarded minus base total R)
| config / source | affected (trades) | better | worse | net | largest worsening |
|---|---|---|---|---|---|
| **G1 live, all** | 75 (224) | **50 (+99.3R)** | 24 (-20.6R) | **+78.8R** | -2.65R |
| G1 live, ex 11-19 | 69 (188) | 45 (+76.9R) | 23 (-21.0R) | +55.9R | -2.65R |
| G1 live, by family | 23 | 19 (+81.8R) | 4 (-3.1R) | +78.8R | -1.0R |
| G2 live, all | 75 (204) | 50 (+94.1R) | 24 (-20.6R) | +73.6R | -2.65R |
| G2 live, ex 11-19 | 67 (168) | 44 (+71.0R) | 22 (-20.3R) | +50.7R | -2.65R |
| G3 live, all | 54 (127) | 34 (+64.5R) | 20 (-15.9R) | +48.7R | **-3.12R** (fails bar) |
| G3 live, ex 11-19 | 44 (91) | 25 (+43.3R) | 19 (-17.4R) | +25.8R | -3.12R |
| G1 lab, raw | 60 (8,981) | 32 (+753.5R) | 28 (-207.8R) | +545.7R | -21.0R |
| G1 lab raw, early / late | 58 / 58 | 29 / 32 | 29 / 26 | +58.9R / +486.8R | |
| **G1 lab, ETB proxy** | 56 (2,004) | **36 (+139.2R)** | 20 (-59.6R) | **+79.6R** | -16.3R (2-yr, uncapped) |
| G1 lab ETBp, early / late | 54 / 52 | 34 / 26 | 20 / 26 | **+13.3R / +66.3R** | |
| G2 lab, raw (early / late) | 58 | 31 | 27 | +387.9R (+28.3 / +359.6) | -22.0R |
| G3 lab, raw (early / late) | 57 | 30 | 27 | +366.2R (+40.4 / +325.8) | -21.6R |
| M1 live (mirror) | 97 (587) | 41 (+92.3R) | 56 (-112.8R) | **-20.5R** | -18.9R |
| M1 lab | 53 (13,554) | 38 (+2,610.6R) | 15 (-81.0R) | +2,529.6R | -17.3R |
| G1+M1 live / lab | 172 / 113 | 91 / 70 | 80 / 43 | +58.3R / +3,075.3R | -18.9R / -21.0R |

Removed trades, live G1: 224 trades, -78.8R, avg -0.352R, win 38%, red on 18 of 27 days, avg w/o best day -0.415R.
By symbol: SQQQ 62 trades -30.5R, SOXS 73 -25.4R, SPXS 11 -9.5R, BEZ 17 -6.7R, VXX 9 -6.5R, PSQ 10 -3.4R; the few
positive ones (UVXY +2.3R, TZA +3.0R, TWM +2.0R, AAOZ +1.5R) are small.

## 2. Per setup (live G1; full tables in live_G1.csv, live_G1_fam.csv, lab_*.csv)
Avg R / avg R w/o best day, before -> after; best-day share where total > 0.
- **Primary (6 affected, 5 better):** L3-fromopen-FD +13.94R (16 trades removed; avg 0.17 -> 0.27, w/o best day
  -0.01 -> +0.12, best-day share 103% -> 70%: the `1 day` tag stays on but weakens); L3-rsi5hi-FD +2.58R; RW3-FD +2.18R;
  MF2-FD +1.33R; exhaustion_short +1.14R; **worse: RW5-FD -0.90R** (1 trade).
- **L3 family: +30.4R, 7 of 8 setup-accounts better** (fromopen-WB4 T2 +6.72R, rsi5hi T1 +2.91R, rsi5hi-WB5 Live Lab
  +2.06R, lowdist-WB4 T-F +1.52R, lowdist T1 +1.20R); worse: L3-fromopen-FD Testing 1 -0.47R. Family avg w/o best day
  0.06 -> 0.13, best-day share 62% -> 48%.
- **Largest worsenings (all < 3R):** heat_fade_short-FD Graveyard -2.65R, NM-RWR3 Live Lab -2.11R (avg w/o best day
  0.42 -> -0.22, a 7-trade record), GEN-261022-04 Gen -1.73R, NS2-sma50break Graveyard -1.69R, GEN-261023-03 -1.64R,
  NS3-failed-vwap-reclaim Testing E -1.41R, exhaustion_short T1 -1.06R; the other 17 worse are each < 1R.
- **Families worse (4, total -3.1R):** NS2 -1.0R, RW5 -0.9R, NS3V1 -0.8R, RW3S -0.4R. Families better (19): L3 +30.4,
  exhaustion_short +7.7, CWT14 +7.6, GEN +5.3, RW2 +5.1, CWT13 +3.8, CWT09 +3.7, RW3 +3.2, NS3 +3.1, others < 3R.
- **Lab G1-ETBp:** families 22 better / 7 worse; worst setups GEN-261019-10 -16.3R (166 fires; it is +2.6R better live
  in Testing F), GEN-261027-07 -5.8R, L3-fromopen-FD -5.4R (lab only; live +13.9R), RW6-ns2 -4.1R, RW1-FD -3.9R; best
  CWT14-pdh-p10 +19.5R, GEN-261029-06 +10.9R, CWT13 +9.3R, L3-lowdist +9.1R. Lab per-trade effect is small
  (removed fires avg -0.040R) and **lab L3 disagrees with live L3** (live is the more relevant read: the lab has no
  borrow, no caps, no same-symbol lots).

## 3. ETB interaction (U9-ETB from 11-19)
- Signal pairs (setup/symbol/day, run 1): in-class shorts got through ETB 10.4% of the time before 11-19 (160/1,543) and
  7.2% on 11-19 (20/278). Other shorts: 71% -> 87%. **U9-ETB did not open or close the leak**; it changed logging only.
- What gets through is the liquid, usually-borrowable names: SQQQ (through on 18 days, ETB 3), SOXS (16 / 12), PSQ
  (10 / 0). 15 in-class symbols flipped between ETB and borrowable across days, so ETB's protection is accidental.
- Run-2 what-ifs of ETB-skipped in-class shorts: 2,400 rows, **-374R** (-0.156R; -198R ex 11-19) vs -0.024R for other
  ETB-skipped shorts. The guard therefore gives up nothing ETB is saving and keeps protecting if borrow lists change.
  (Indicative only: what-if rows repeat signals and fill optimistically. The earlier +12.6R figure was Primary-only,
  beta-list, through 11-18.)

## 4. Mirror (long setups buying inverse products): not a live leak
- Live: removing them costs -20.5R (587 trades, avg +0.035R, win 62%); 41 better / 56 worse; worst -18.9R
  (GEN-261022-01), -17.9R (GEN-261021-02). By family: CWT14 -23.0R and ST2 -4.3R lose on inverse longs; GEN +31.2R and
  heat_fade_long +11.9R win.
- Lab says the opposite (+2,530R), driven by two families: LD2-tqqq +725R and CWT14 longs +1,540R. Sources disagree;
  a CWT14-only cut would be tailored to one family. **Not proposed.** Note: from 11-20 ULT-22 (Live Lab, ETF long)
  carries 21 inverse ETFs in its universe and the WB4 ETF list feeds ETFDISP; in the lab NM-ETF-late-dip on inverse is
  +17.3R (inverse longs help it), so no action, only a shadow column.

## 5. Decision bar (pre-registered) and playing time
| bar | G1 | G2 | G3 |
|---|---|---|---|
| live net > 0, with and without 11-19 | pass (+78.8 / +55.9) | pass (+73.6 / +50.7) | pass (+48.7 / +25.8) |
| >= 60% of affected not worse | pass (51/75 = 68%) | pass (68%) | pass (63%) |
| no setup worse by > 3R (live) | pass (-2.65) | pass (-2.65) | **fail (-3.12)** |
| lab ETBp net >= 0 both halves | pass (+13.3 / +66.3) | pass (same) | n/a (raw both halves > 0) |
G1 and G2 both pass; they differ only in single-stock/crypto inverse names, which ETB nearly always blocks (+5.2R live
in G1's favour). G1 is the simpler frozen list. Playing time: G1 removes 0.8% of live trades, but takes most of the
activity of three low-rep L3 copies (L3-fromopen-WB4 T2 18 of 24 trades, L3-rsi5hi-WB5 Live Lab 2 of 2, L3-lowdist-WB4
Testing F 3 of 3) plus a few GEN shorts; on stock-only signals these would get few reps.

## 6. Proposal (owner decision; reply code **INV**)
**INV-G1:** short setups skip any symbol on the frozen INVERSE ∪ LONG_VOL list (all accounts), and exposure checks count
such a short as long-market. Route: backlog entry -> forward shadow column `blocked_inverse_short` in
research/forward/compass_gate/forward.csv from 11-20 (journal-only) -> live change outside market hours after >= 10
sessions on the pre-registered bar -> ledger entry + `python -m mcf.research.ledger check`. Mirror: no change, shadow
column only. Reply "INV yes" (backlog + shadow), "INV live-epoch" (also Primary in the Friday epoch window), or "INV no".

Conflicts with standing owner rules (flagged for the conflict check): (1) setup/filter change -> backlog (RESEARCH_RULES
15-17), never during 09:30-16:00 ET; (2) **Primary only in the Friday epoch window (C3-EPOCH)** and with the adversarial
review; BASE1 (frozen 11-18 book) would then differ from Epoch by this guard, so the Epoch-vs-BASE1 read must note it;
(3) **Playing time / low-rep rotation (11-03, 11-04)**: the three L3 WB copies above lose most of their activity; they
need the owner to accept the lower activity, or their rotation time counted from stock-only signals;
(4) remedies rule (11-05): satisfied — targeted at the failure mode in every short setup, 50 setups better / 24 worse
reported in full, no setup worse > 3R live.

Educational only — not financial advice.
