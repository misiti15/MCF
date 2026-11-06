# BDI 2026-11-05 (Thursday): crash day — Move Hunt day 6, all-account swing autopsy, FB1 "sell the bounce", leads L9 / FB1 shadow

*Educational only — not financial advice. Live numbers are **paper** results from one session (costs in). **$ = Alpaca**
(account equity change on the data branch, last commit before 08:00 ET vs final); journal `pnl_adj` $ shown where it differs.
R = journal `pnl_adj / $ risk`. Two-year tests use the lab cache of research/bdi/1104/DATA.md (frames to 11-04, trade lists
`research/history2y/data/bt_lab1104`). **Locked block 2024-11-01..2025-02-28 never read (asserted absent on every table).**
**6 configurations tried tonight, all reported below; 0 pass** (full bar max(1.5, √(2 ln 6)) = 1.89; Testing bar BAR90 1.70).
No config, setup, exit, ledger or docs/live file changed.*

Built on, not redone: BURST1 (why MF4 / MF2 failed; $ per R; latch), REGX, GATE1, HC1 / COMP15, nightly1105 (close,
coverage, Gen halt-restart bug, latch / REG2 / FLOW1 shadows). The 11-05 curve was rebuilt from journal + SIP 1-min bars
(poll-log snapshots, PR #150, are usable from 11-06).

**Day type: DOWN (crash).** SPY open-to-close **−4.11%** (−1.37% at 10:00 1-min close, −4.22% on the daily table), QQQ −4.92%,
IWM −4.58%; first leg down 09:30 → 10:53 (QQQ −4.4%), bounce to 11:20 (QQQ −3.0%), new lows 13:00-13:30, afternoon bounce
13:02 → 14:48 (SPY −3.89 → −3.15%), lows into the close. Breadth above open 0.20 at 11:00 → 0.06 from 13:00. The deepest-down
morning of the live window. Every figure below is a down-day, SPY-below-open-at-10:00 figure.

**Rule changes inside the windows quoted here** (research/ledger.jsonl): effective 11-05 — **ROLL1** (Explore 1 / Live Lab go
live as low-rep homes: their first session); 11-04 — DM-N3 (NS5-FD / ST4-FD / RW6G1-FD → Graveyard), **UNI1** (Testing 2
top-500 pool); 11-03 — RW3S added to Testing 2, SO-1A, MF3-FD / MF5-FD → Graveyard; 10-30 Testing cost filter; 10-29 Primary
−2R per-setup latch, BAR90; 10-28 Primary ~$4k lot. The live day-type table (§0) spans all of these; 2-year results are rule-fixed.

## Today's win
**Primary: +4.54R on a −4.1% day, carried by the one setup that waits for the bounce** — Gap-Down Pop Fade, Heavy Selling (all day)
`RW3-gapdn-rsi5pop-flowsell-short-FD` 13 trades **+16.49R / +$790** (it sold the 11:20 and 12:00 bounce tops: the 11:22 → 12:07
leg +29.8R). Testing 1 green too (+6.04R / +$57.71; RW7 +14.3R). Research win: the bounce-vs-flush split is **sharp live**
(shorts entered within 0.15 ATR of the session low −0.419R n 134 vs bounce-sold +0.231R n 146, all 7 accounts) — the 2-year
test says it is *not* a general edge (FB1, §3), so it is logged as a forward shadow rather than shipped, and the honest
reading is that today's split is a crash-day property.

## 0a. Move Hunt (v1 definition unchanged; moves.csv +100 rows for 11-05; research/bdi/moves/moves_1105_out.txt)
Inputs rebuilt tonight: priors + SIP 1-min bars for 1,635 universe names (ADV ≥ $60M), 5-min bars 09-22..11-05, 11-05 lab
frames; 1,251 liquid names, 82,544 decision rows, 1,207 live trades (539 symbols), **7 accounts** (Explore 1 / Live Lab added;
the 5-account rate is the same, moves_1105_5acct_out.txt).

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | 1 / 50 (2%) | +0.24 | 4, −5.03R | traded outside the move 18, no setup 18, blackout 8 |
| tradable (blackout removed) | **1 / 50 (2%)**: long 0/25, short 1/25 | **+0.24** | 8, −9.58R | traded outside 21, no setup 21, wrong side 4, skipped 3 |
| single names (|corr to SPY| < 0.85), decision ≥ 09:50 (descriptive cut, moves_alt_out.txt) | 3 / 50 (6%) | −0.03 | 15, −18.87R | no setup 16, traded outside 13, skipped 12, wrong side 6 |

**Capture rate 2% vs 20% on 11-04** (10-29 26%, 10-30 6%, 11-02 22%, 11-03 12%). The v1 list on a one-factor day is the
index: 48 of 50 decision points are **09:35** (before the 09:50 no-entry rule), the extremes 10:51-10:55 — inverse / leveraged
ETPs long, index ETFs and banks short. Only catch: GY `CWT14-failbrk-pdh-p10-short` KBWB (+0.24R).
What was known at the decision point:
- **09:50, the bank group gapped UP against a falling tape:** C, JPM, MS, BNY, WFC, BLK, STT, PNC, HBAN, KEY, AMP gap +0.9..+2.0%,
  already below their open, SPY −1.24% → each fell 1.7-2.7 daily ATR by 10:53. Third day running a bank group led the short
  list (11-03, 11-04). Skips: max positions (WFC, IVZ, XLF, PNC), spread vs stop (BLK, STT), daily loss limit (AMP); the book
  was long JPM / MS (−2.6R). → tested tonight as MH1105-P1 (below): fails.
- **The 10:50-11:05 bounce-turn longs** (FUTU, GFI, BHP, AEM, GDX, META): the live book was on the wrong side of the gold names
  (GFI / AEM / GDX −8.8R, shorts at the low) — the same flush-chase failure as MF4 (§0b).
- Inverse ETPs (VXX, UVXY, SDS, SQQQ…) are the biggest longs on every crash morning; no live setup trades them by design
  (SOXS skipped by the broker).
- **Precursor test (1 config, costs in, Testing bar 1.70):** MH1105-P1 = short at the 09:50 close names with gap ≥ +0.8%,
  below the open, SPY ≤ −0.50% (research/bdi/1105/MH_PLAN.md, pre-registered; mh_p1_out.txt): **n 1,766 on only 9 days, avg
  −0.046R (t −0.34) — fails.** It beats the same day's other 09:50 shorts (+0.183R, t 2.19) and wins on down days (+0.099R) but
  loses on quiet (−0.63R) and up (−0.62R) days; TRAIN +0.173 / VALID −0.184. A crash-morning relative edge, not a setup.

## 0b. Swing autopsy, every account (research/bdi/1105/swings.py → swings_out.txt, timeline_<acct>.csv, 5-min)
Method = 1104 (1-min marked R per lot, zig-zag legs ≥ 25% of the day's R range; each decomposed leg = market (beta × SPY) +
setup-day mismatch (sector-ETF residual) + bad entries (fill + first 5 min) + stock-specific (rest, incl. exits and costs);
parts sum exactly, asserted). Betas 5-min 09-22..11-04.

**Primary** (61 lots, 57 short / 4 long): R peak **+20.67R 13:02**, trough −18.17R 11:22, close **+4.54R / Alpaca −$367.71**
(journal −$419; R and $ disagree because MF4's losers carried ~$121 per R vs RW3's $48 — BURST1).

| leg (ET) | R | $ | SPY | market | mismatch | bad entries | stock | top names (setup) | what turned it |
|---|---|---|---|---|---|---|---|---|---|
| 09:50→10:42 | +1.12 | +85 | −1.11→−2.53% | | | | | 2 trades | |
| **10:42→11:22** | **−19.29** | **−1,730** | −2.53→−2.49% (QQQ low 10:53, +1.4% bounce) | (BURST1) | | | | 11 MF4-FD shorts 11:00-11:10 all stopped 11:10-11:18 (−11.6R) | **MF4 sold the flush at the low** (BURST1) |
| 11:22→12:07 | +29.82 | +1,406 | −2.49→−3.17% | +20.94 | +1.40 | +2.69 | +4.79 | CLSK (MF2) +4.5; APH, QLD, TECL, CSCO (RW3) +10.3 | RW3 / MF2 sold the bounce top (15 shorts, avg +0.47R) |
| 12:07→12:19 | −18.36 | −642 | −3.17→−3.03% | | | | | MF2 0.2%-stop cluster (BURST1) | |
| 12:19→13:02 | +27.39 | +979 | −3.03→−3.89% | +36.00 | −1.94 | −0.24 | −6.44 | IBIT, CLSK, KEYS, MTUM, BWA (MF2) +12.6 | 19 shorts open, net beta −48.9R per +1% SPY |
| **13:02→14:48** | **−27.60** | **−1,459** | −3.89→−3.15% | **−16.01** | −1.47 | −0.97 | −9.15 | **CLSK, IBIT, FBTC, LRCX (MF2) −16.5, CLSK (RW5) −2.3** (together −18.8R) | the afternoon index bounce against 12 open shorts (beta −38.8R/1%): **give-back = market**, plus crypto names bouncing harder |
| 14:48→close | +11.47 | +943 | −3.15→−4.11% | | | | | | new lows into the close |

Primary's day = **two flush-chases (MF4 11:00, MF2 12:05) and one give-back (MF2 crypto stack 13:02-14:48, market −16R)**
against RW3's bounce sales. Peak → close −16.1R. The −2R latch (MF4-FD 11:12, MF2-FD, NS5, L3-rsi5hi) cost 15.25R today
(nightly1105). Bad entries are small on every leg (≤ 2.7R): the losses are *where* in the swing the setups sold, not fills.

**Testing 1** (91 lots, 73 short): +6.04R / Alpaca **+$57.71**; peak +24.83R 13:02 → close (give-back 18.8R). Largest legs
13:02→14:16 −27.98R (market −17.70, mismatch −4.29) and 14:30→14:52 −31.02R (market −22.77): RW7-gapdn-bounce-early-short-FD
(49 trades, +14.3R day) rode the index both ways with ~31 shorts open (beta −38R per +1%). Longs 18 −7.1R (CWT05-flush longs).

**Testing 2** (271 lots, **193 long**): −85.41R / Alpaca **−$978.08**; one leg 09:53→close −86.14R = market −7.59 + mismatch
−16.94 + bad entries −24.65 + stock −36.97. Top setups: RW3S-gapdn-flowsell-short-FD −30.8R (20-short burst 11:00-11:10
−19.2R, 19 stops — the MF4 flush-chase again), CWT13-vwapstretch-z05-long 100 longs −23.9R, CWT14-failbrk-pdl-p10(-lowvol) longs
−27.4R. **Setup-day mismatch** (longs bought into a crash) + selling the flush. UNI1 day 2 (top-500 pool) inside the window.

**Graveyard** (344 lots): −60.47R but Alpaca **+$415.10**. 10:16→10:35 −92.38R = market −49.69 + mismatch −10.22 + entries −3.67
+ stock −28.80 (74 longs open at 10:16, net beta +118.7R per +1%): **CWT14-failbrk-orl long bursts 10:09-10:20** (p05 / p05-lowvol
/ p10 / p10-lowvol, 82 entries, −70.6R); then 10:35→10:55 +45.67R from **CWT09-gapdn-vwaploss-g5-short** (24 shorts at 10:30-10:31,
+28.4R / +$513 for the day, AMDW +10.3R). Latch shadow: GY latch saved 292.2R today (longs).

**Gen** (385 lots): −127.77R; Alpaca **−$156.18** vs journal −$1,100.08 (69 unbooked trades over the 14:49 restart, HK-RECON-GEN —
Alpaca is the number). 09:50→10:56 −63.66R (GEN-261019-05 long burst 09:50-09:58, 29 entries −31.4R; entries −19.4R) and
11:05→close −106.44R (GEN-261022-09 hold-short: **48 shorts 10:55-11:03, all stopped, −58.5R** — the flush-chase at the 10:53 low).

**Explore 1** (36 lots, 33 long) day 1: −15.32R / Alpaca **+$54.92** (two big-$ CWT09 g10 shorts); CWT13-vwapstretch-z075-long
23 longs −10.7R (JPM, ARE, SCHW, PFG: buying VWAP stretches on a crash day), ST8 longs −5.9R. **Live Lab** (19 lots) day 1:
−1.44R / Alpaca **+$154.24**; NM-ETF-late-dip-di-long +1.5R, CWT09 g10 short +1.2R / +$147, CWT05-flush-m075 longs −3.8R.
Both closed clean (nightly1105).

**Cross-account cause (one line):** the morning flush (09:30-10:53) bought by failed-breakdown / VWAP-stretch longs
(GY, T2, Ex1, Gen) and then *sold at its low* by heat/flow shorts (P MF4, T2 RW3S, Gen GEN-261022-09: 79 shorts 10:55-11:10,
−89R), while the bounce-waiting shorts (RW3, RW7, CWT09) made the day's money.

### Leads (research/bdi/swings/hypotheses.jsonl; 15 leads)
- **New, pre-registered 17:33 ET before its 2-year read: `swing1105-L9`** — skip lab long entries at/after 10:00 when SPY ≤ −1.00%
  from its open at 10:00. ONE 2-year backtest (l9_bt_out.txt): **only 2 qualifying open-month days in 2 years** (both rebounded,
  SPY o-c +0.24% mean), class A n 2,801 excess **+0.229R** (wrong sign), t 1.09 — **fails, not powered**; forward shadow (needs
  ≥ 3 qualifying days). Honest note: deep-down mornings are rare, so this lead can only be judged forward.
- **New forward shadow `fb1-flush-chase-shadow`** (FB1-S / FB1-B tags on live shorts; bar in the file).
- **Forward tallies, 11-05** (forward.csv): L1 A n 5 +0.12 vs B −0.10; L2 no trigger; L3 not qualifying; **L6 counter-index
  entries n 639 −0.428R vs others −0.011R** (setup-adjusted excess −0.001); L7 no class A (QQQ never ≥ +0.75%); **L8 class A 174
  −0.666R** (all failbrk longs were class A; no contrast); **gate1-checkpoint-gate day 1 +13.81R** (state DOWN at every
  checkpoint; dropped 60 entries −13.81R, GY +12.6R); **latch1103 day 2** GY +292.2R raw (excess +87.2), Primary −15.25R;
  **flow1** merged +150.3R = the SPY-only control (excess 0, no lift); **burst1-openloss-latch3** in-sample today (forward
  from 11-06); **comp15-w60-early** forward from 11-06. Best lead tonight: gate1-checkpoint-gate (+13.8R day 1, 19 to go).

## 0. Per-account session review (accounts.py → accounts_out.txt / accounts.csv; bursts_out.txt; daytype_out.txt)

| account | Alpaca $ | R | trades | win% vs break-even | avg R | peak → close (journal $) | best setup | worst setup | skips |
|---|---|---|---|---|---|---|---|---|---|
| Primary | **−367.71** | **+4.54** | 61 | 49% vs 46% | +0.074 | +153 (11:06) → −419 | RW3-FD 13 +16.5R +$790 | MF4-FD 15 −10.7R −$1,293 | 298 / 359 (not shortable 170, setup loss limit 80) |
| Testing 1 | +57.71 | +6.04 | 91 | 53% vs 49% | +0.066 | +285 (13:08) → +48 | RW7-FD 49 +14.3R | CWT05-flush-m05-v3-long 16 −6.2R | 94 / 185 (cost filter 31) |
| Testing 2 | −978.08 | −85.41 | 271 | 44% vs 66% | −0.315 | +13 (09:54) → −996 | RW1-FD 8 +4.8R | RW3S-FD 60 −30.8R | 215 / 486 (spread 98) |
| Graveyard | +415.10 | −60.47 | 344 | 47% vs 56% | −0.176 | +323 close high | CWT09-g5-short 24 +28.4R +$513 | CWT14-orl-p05-lowvol-long 27 −22.0R | 1,811 / 2,155 (setup loss limit 1,273) |
| Gen | −156.18 (journal −1,100) | −127.77 | 385 | 40% vs 58% | −0.332 | +378 (11:38) → −1,100 | GEN-261019-10 short 11 +10.6R | GEN-261022-09 hold-short 48 −58.5R | 818 / 1,272 (halted 262) |
| Explore 1 | +54.92 | −15.32 | 36 | 33% vs 56% | −0.426 | +88 (13:01) → +50 | CWT09-g10-lowerhalf-short 2 +1.1R +$145 | CWT13-z075-long 23 −10.7R | 167 / 203 (max positions 67) |
| Live Lab | +154.24 | −1.44 | 19 | 58% vs 63% | −0.076 | +152 close high | NM-ETF-late-dip-di-long 3 +1.5R | CWT05-flush-m075-v3-long 6 −3.8R | 60 / 79 (not shortable 45) |

Avg R w/o best day / one-big-day check: single session — n/a; RW3-FD's +16.5R is 1 day of its record (see nightly1105 for the
full-record figures). Sides: shorts carried every account that made R (P +4.7R, T1 +13.1R, GY shorts +61.7R); longs lost in all 7
(GY −122.2R, T2 −60.4R, Gen −62.1R, Ex1 −17.1R, T1 −7.1R, LL −4.6R, P −0.2R).
**Explore 1 / Live Lab first-day review (ROLL1):** both green in Alpaca $ from CWT09 g10 big-$ shorts, red in R from crash-day
longs (CWT13 z075, CWT05 flush, ST8); skips dominated by max positions (Ex1) and not-shortable (LL); clean close. One session —
no verdict; rotation re-evaluates after ~2 sessions per ROLL1.

**R by day type** (all live sessions in the 7 journals, daytype_out.txt; 6 down / 11 quiet / 6 up days): Primary down **+0.224R**
(261 trades) vs quiet −0.096 / up −0.165; T1 down −0.063 / quiet −0.083 / up −0.214; T2 down −0.266 / quiet −0.065 / up −0.139;
GY −0.198 / −0.099 / −0.114; Gen −0.265 / −0.310 / −0.426. Primary is still a down-day book (short-heavy).

**Edits (tested or queued, none live):** (1) flush-chase / bounce-sold tag → FB1 tested (fails on 2 years), forward shadow;
(2) deep-down-morning long veto → L9 tested (not powered), forward shadow; (3) gap-up-vs-tape 09:50 short → MH1105-P1 tested
(fails). Queue items GATE2 / FLOW1-2Y / SIZE1 remain open (not run tonight).

## 1. Every-trade analysis (trades_bdi.py → per_trade_1105.csv, patterns_1105.csv → patterns.csv +664 rows; bursts.py)
- **Bursts:** 96 setup bursts (≥ 4 same-setup same-side entries in 10 min), 844 entries, −205.8R (avg −0.244R vs −0.204R
  non-burst); **34 bursts with ≥ 75% stops = −300.7R.** Largest: Gen GEN-261022-09 48 shorts 10:55-11:03 −58.5R (48 stops); Gen
  GEN-261019-05 29 longs 09:50-09:58 −31.4R; GY CWT09-g5 24 shorts 10:30-10:31 **+28.4R**; GY CWT14-orl longs 4 bursts 10:09-10:20
  −70.6R; T2 RW3S 20 shorts 11:00-11:10 −19.2R; P MF4-FD 11 shorts 11:00-11:10 −11.6R; T1 RW7 5 shorts 11:30-11:40 +10.6R.
  The bad bursts are the ones *at the extreme of a leg* (10:09-10:20 longs into the first flush, 10:55-11:10 shorts at the low);
  the good ones fired after a bounce (CWT09 10:30 on the VWAP loss after a pop, RW7 11:30).
- **Stacking:** T2 42 lots −22.5R, GY 122 lots −70.0R (sister CWT14 orl / pdl variants on the same symbol), Gen +8.4R.
- **Give-back** (peak → close, journal $): Gen $1,478, T2 $1,010, P $572 (R: +20.7 → +4.5), T1 $238; GY / LL closed at the high.
  Primary's R give-back was market (−16.0R of −27.6R in 13:02→14:48).
- **Loss types** (losers): wrong_side_after_big_swing dominates (P 11 / −$1,329, Gen 108 / −$2,289, T2 70, GY 35); P
  stopped_then_reversed 15 / −$747 (MF4 / MF2 at the lows).
- **Exit what-ifs** (all 1,207 trades, R after costs, per trade): live −0.232, trail −0.102, reent −0.139, t1 −0.152; **opposite
  side +0.085**. Primary: hold +28.5R vs live +4.5R (stops at the lows), trail +7.4R. One session, not a basis for an exit change.
- **Hindsight flag:** entries against SPY ≥ |0.25%| (i.e. longs today) 639 trades −0.428R; their opposite 1R/1R +0.305R.

## 2-3. Patterns → testable rules; NEW tested idea: FB1 "sell the bounce, not the flush" (FB1_PLAN.md, fb1_out.txt)
Pre-registered 17:26 ET before any 2-year read; ONE run, 4 configs, generalising RW3's trait across all lab short families (and the
mirror for longs), on the 2-year lists (95 setups, 1,165,576 trades, 446 sessions), features at the entry bar.

| config | class A share | A excess | day-t | TRAIN / VALID | families helped / harmed | pass |
|---|---|---|---|---|---|---|
| FB1-S short within 0.15 ATR of the LOD (guard) | 13.8% | +0.013R | +1.03 | +0.023 / +0.009 | 11 / 13 | no |
| FB1-I short while QQQ at its low & ≤ −0.5% (guard) | 9.8% | +0.005R | +0.27 | +0.042 / −0.009 | 13 / 11 | no |
| FB1-L long within 0.15 ATR of the HOD (guard) | 14.8% | +0.000R | +0.02 | +0.025 / −0.012 | 9 / 2 | no |
| FB1-B short after a bounce (dist_lod ≥ 0.5, rsi5 ≥ 50) (boost) | 37.7% | +0.003R | +0.17 | +0.018 / −0.003 | 14 / 10 | no |

**FB1 no.** On two years, where a short sits relative to the low is not, by itself, an edge in any family (buckets 0-0.15 / 0.15-0.3
/ 0.3-0.5 / 0.5-1 / >1 ATR: excess +0.013 / +0.011 / −0.007 / −0.014 / +0.012R). What is real is conditional on the day: index-flush
shorts lose on quiet (−0.134R excess) and up days (−0.200R) and win on down days (+0.061R) — i.e. on V-reversal days, which are
not known at entry. Live 11-05 (in-sample, descriptive, fb1_live_out.txt): near-LOD shorts −0.419R (n 134; GEN −1.12, MF4 −0.88,
RW3S −0.53) vs rest +0.098R; bounce-sold +0.231R (n 146; RW3 +1.33, RW7 +1.66, CWT09 +0.54). Salvage: the forward shadow
`fb1-flush-chase-shadow` checks whether the live split repeats on ≥ 3 up and ≥ 3 down sessions before any re-test.
Remedy rule (owner 11-05) reported: no family made materially worse or better by any FB1 config (|family excess| ≤ 0.2R except
tiny-n CWT13 / RW6 / ST4 cells).
QDAY: today was not a quiet day; no new QDAY config tonight.

## 4. Swarm / configs counted
Configs tonight: FB1 ×4, L9 ×1, MH1105-P1 ×1 = **6** (bar 1.89; BAR90 1.70). 0 pass. Not run: queue GATE2, FLOW1-2Y, SIZE1
(open, unchanged). Locked block never read. Backlog +3 parked (`fb1-1105-sell-bounce-not-flush`, `swing1105-L9-deep-down-morning-long-veto`,
`mh-1105-gapup-vs-falling-tape-0950`; research/bdi/1105/add_backlog.py).

## 5. Decision
None. Nothing passed; no setup moves; no DECISION card.

Files: accounts.py, swings.py, trades_bdi.py, bursts.py, daytype.py, forward_l78.py, forward_gate1.py, fb1.py, fb1_live.py, l9_bt.py,
mh_p1.py, moves_alt.py (+ outputs). Scratch inputs: priors / bars / frames under the session scratchpad `mh1105/` (rebuild:
research/ops/coverage1029/fetch.py, research/bdi/moves/fetch5.py, frames_today.py). Educational only — not financial advice.
