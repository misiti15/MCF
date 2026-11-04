# BDI 2026-11-04 (Wednesday): data cache rebuilt, Move Hunt day 5, all-account swing autopsy, GY-BP replay, QR1/QR2 (QDAY), leads L7/L8

*Educational only — not financial advice. Live numbers are **paper** results from one session (costs in: P/L = journal
`pnl_adj`, R = `pnl_adj / $ risk`). Two-year tests use the lab frames rebuilt tonight (research/bdi/1104/DATA.md) and
the 2-year trade lists of every enabled lab setup built from them (bt_all.py). **The locked block 2024-11-01..2025-02-28
is written by the frame builder into its own directory and was never read (asserted absent on every table).**
**8 configurations were tried tonight, all reported below; 0 pass** (bar t ≥ max(1.5, √(2 ln 8)) = 2.04).
No config, setup, exit, ledger or docs/live file was changed.*

Built on, not redone: nightly1104 (close, coverage, Primary WHY = midday give-back, latch / BRAKE-1 / REG2 / FLOW1
shadows, DECISION L3H, backlog +4).

**Day type today: UP.** SPY open-to-close **+0.48%**, above its open at 10:00 (+0.55%); QQQ +1.34% at 10:00, high +1.89%
10:15, close +0.50%; **IWM −0.06%, low −1.01% at 11:27** — a narrow, tech-led morning, then a broad midday rally (breadth
above VWAP 0.40 at 10:05 → 0.70 at 12:35). SPY printed a bad 1-minute high of 775.64 at 10:00 (+1.65%; next bar 768.27);
the Move Hunt's SPY "long #10" row is that print and should be ignored. Every R figure for today is an up-day,
SPY-above-open-at-10:00 figure.

**Rule changes inside the windows quoted here** (research/ledger.jsonl): effective 11-04 — DM-N3 (NS5-FD / ST4-FD /
RW6G1-FD → Graveyard), UNI1 (Testing 2 top-500 pool); 11-03 — RW3S added to Testing 2, SO-1A, MF3-FD / MF5-FD → Graveyard;
11-02 — PDL-1a R2A legs, NS3-FD / RW4-FD → Graveyard; 10-30 — Testing cost filter CF, L3 pair promoted to Primary,
CWT14-pdl-p05 pair → Graveyard; 10-29 — Primary −2R per-setup latch, BAR90; 10-28 — Primary ~$4k size, Generator paused
(resumed later with new seeds). From 11-05 (not in any number here): ROLL1 (Explore 1 / Live Lab low-rep homes).
The live day-type table (§0) spans all of these; two-year results are rule-fixed backtests.

## Today's win
**The 2-year lab is back.** The data gap that stopped every backtest in tonight's nightly loop is closed: 1,226 symbols of
1-minute SIP bars to 11-04, lab frames + context + daily table, head/tail, and — new — **2-year trade lists with exit times for
95 live lab setups (1.17M trades, 446 open sessions)**, all in the paths the repo code expects (DATA.md), so SIZE1 and FLOW1-2Y
can run straight away. Second win: the **Move Hunt capture rate rose to 20% (10 / 50) from 12% on 11-03**. Research win:
QR1 measured that a *wide* SPY opening half hour flags trend days (quiet-close share 20-24% in the top two quintiles vs ~40%
below) — the first ex-ante day-type signal the QDAY search has found, though it does not reach the +15-point bar as a
quiet-day predictor and does not turn counter-index entries positive (QR2).

## DATA: 2-year lab cache rebuilt (research/bdi/1104/DATA.md)
1,226 symbols × 1-minute SIP 2024-09-16..2026-11-04 → `data/cache_hist/1Min` (4.4 GB, 0 failures, 25 min);
lab frames 39.1M rows (open months 2024-10, 2025-03..2026-11) + context + daily → `research/history2y/data` (6.9 GB incl. the
locked directory, never read); head/tail → `research/bdi/cwt/test_b/data/headtail.parquet`; 2-year trade lists for the
96 covered enabled lab setups (95 with trades; of 162 enabled; not covered: 48 hold / holdtr geometries, 8 classic, 5 geom S, 4 heat,
1 symbol list) → `research/history2y/data/bt_lab1104/`. SIZE1 and FLOW1-2Y can reuse all of it (paths and rebuild commands in DATA.md).
Frames now run to 11-04 (old ones ended 10-07). Disk after the build: 16 GB free (cache kept for SIZE1 / FLOW1-2Y).

## 0a. Move Hunt (v1 definition unchanged; moves.csv +100 rows for 11-04; research/bdi/moves/moves_1104_out.txt)
Inputs: SIP 5-minute bars 09-22..11-04 (1,591 symbols), live priors + SIP 1-minute bars, the 5 journals; 1,216 liquid
names, 80,216 decision rows, 975 live trades (474 symbols).

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | 2 / 50 (4%) | +1.99 | 8, −5.43R | blackout 38 (29 on the event day) |
| tradable (blackout removed) | **10 / 50 (20%)**: long 6/25, short 4/25 | **−0.64** | **38, −35.71R** | skipped 12, traded outside the move 12, wrong side only 10, no setup 6 |

**Capture rate 20% vs 12% on 11-03** (10-29 26%, 10-30 6%, 11-02 22%) — up, but the captured R is −0.64 (11-03 +4.13)
and the wrong-side R is the worst of the five days (−35.71R; 11-03 −4.00R). Catches: GY LIQ-orl-sweep / CWT14-orl HON long
(+1.14R), GY heat_fade_short C (+0.85R), T2 RW3S USO short (+1.14R), GY CWT14-failbrk-pdh-p10 RF / FITB shorts (+0.16 / +0.35R),
GY CWT14-pdl-p05 CMS long (+1.14R); Gen's CNP / FE / SUNB longs were in the right direction but stopped (−1.06 / −1.21 / −2.23R).

What was known at the decision point (only data available then):
- **A bank group gapped UP and faded from 09:35:** COF (gap +2.7%, rsi5 98.6, 3.03 ATR down by 10:26), SYF, C, ALLY, HBAN,
  USB, KEY, PNC, PNFP, RF, FITB — 11 of the 25 short movers, all gap +1.6..+3.1%, rsi5 88-100, decision 09:35-09:45.
  The live book was on the **wrong side** of KEY (−4.12R) and HBAN (−2.39R) (CWT14 failed-breakdown / orl longs) and
  the 11 together carry −7.9R of wrong-side trades. Recurring: the 11-03 hunt had banks (KEY, RF, BNS, RY) short at
  10:45. → backlog idea `mh-1104-group-gapup-fade-open` (opening group gap-up fade; needs the 09:35-09:45 open frame,
  not in the 2-year frames which start at 09:50 — queued, not tested tonight).
- **Oil reversed at 10:50** (UCO −11.3%, BNO, USO, PDBC short; SCO long #1): a 10:30-10:50 news-type turn; UCO short
  skipped "not shortable/ETB", SCO long skipped "max positions for this setup".
- **Defensive longs** (utilities AEP, CNP, OGE, FE, CMS; staples HRL, TSN, WMT) from 09:45-10:10 while QQQ led — a rotation
  inside an up tape; AEP skipped on spread-vs-stop, OGE / TSN no setup.
- **Skips worth noting:** halted (VIK, URI long, TDY short), spread > max (CACI, HRI, AVAV), cost filter (FAST), setup
  daily loss limit (CCL), max positions (SCO). 12 of 50 tradable movers were skipped signals — the most of any hunt day.
- **The open again:** 30 of 50 decision points at 09:35-09:45 (10-29 30, 10-30 33, 11-02 36, 11-03 23).
- Precursor test tonight: the group gap-up fade is an open-frame setup (above); the oil / utility moves were single
  events. No recurring precursor was testable on the 09:50+ frames tonight; the QDAY work (§3) took the 2-year slot.

## 0b. Swing autopsy, every account (research/bdi/1104/swings.py → swings_out.txt, timeline_<acct>.csv, 5-min)
Method = 1103 (1-min marked R per lot, zig-zag legs ≥ 25% of the day's R range, each leg split into market (beta × SPY),
setup-day mismatch (sector-ETF residual), bad entries (fill + first 5 min stock-specific), stock-specific remainder incl.
exit fills and costs; parts sum exactly to the leg, asserted). Betas 5-min 09-22..11-03.

**Primary** (54 lots, 38 short / 16 long): peak **+5.69R 12:16**, trough −10.83R 15:54, close −10.75R / −$209.
Legs: 09:50→10:25 +1.92R; 10:25→10:42 −7.66R (SPY +0.28 → +0.51%); 10:42→12:16 **+11.35R**; 12:16→close **−16.44R**.
- 10:42→12:16 +11.35R = market +3.95 + mismatch +6.39 + entries −1.20 + stock +2.22. Top 5: ORCL `L3-gap-slope-fromopen-FD`
  (Gap-Down Recovery Fade) +3.50, UMC `MF2-open-rsimidhi-flowsell-FD` +1.53, RF `ST7-rsi50dn-long-pm-t1s1-FD` +1.05, AAL (ST7-FD)
  +1.02, FLEX `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` +0.94.
- **12:16→close −16.44R = market −1.50 + mismatch −1.91 + bad entries −4.07 + stock-specific −8.97.** Top 5: NRIX
  `L3-gap-slope-rsi5hi-FD` −3.32, PL `MF2-open-rsimidhi-flowsell-FD` −1.45, GEV (RW5-FD) −1.32, GLXY (MF2-FD) −1.25, PDBC
  `RW3-gapdn-rsi5pop-flowsell-short-FD` −1.25 (together −8.59R). 12 entries inside the leg, **all shorts, final avg −0.72R**;
  net beta −21R per +1% SPY at 12:19 (10 shorts open) while QQQ went +0.57 → +1.16% (12:19 → 12:50).
- **What turned it:** at 12:16 the book re-loaded shorts (MF2-FD five lots in the 12:15 poll) into a breadth surge
  (above-VWAP share 0.61 → 0.70) and QQQ's second leg; the stops came 12:21-12:27, then NRIX three times. Not market
  beta (−1.5R) — stock-specific and entry timing. The −2R latch stopped MF2-FD / MF4-FD at 12:35 / 13:16 (saved +2.5R).

**Testing 1** (20 lots, all long; split-tape gate skipped its shorts): close −4.30R / −$37; peak +1.49R 11:00. Largest legs:
11:00→11:14 −3.18R (CWT05-flush oil longs UCO / BNO / USO −2.31R at the 10:50 oil turn = mismatch −1.52 + entries −1.28)
and 15:35→close −3.95R (intraday_momentum DIA / SPY / QQQ / IWM longs −2.86R = market −4.15: SPY +0.62 → +0.41%).

**Testing 2** (139 lots, 65 long / 74 short): one leg 09:50→12:34 **−33.37R** = market −5.94 + mismatch −9.68 + entries −4.67
+ stock −13.08; by setup `CWT14-failbrk-pdl-p10-long` −10.16, `CWT14-failbrk-pdl-p10-lowvol-long` −5.42 (Failed Prior-Day-Low
Break Long, same lots twice: HUBB −1.19 / −1.19), `RW3S-gapdn-flowsell-short-FD` −4.20 (JCI −1.45, ESTC −1.14),
`exhaustion_short-FD` −3.42 (FIVE −1.14). Both sides lost: failbrk longs while IWM fell to −1.01% (11:27) and gap-down
shorts while QQQ ripped. Recovery 12:34→13:18 +8.55R (RW3S / RW1 shorts, CWT13 XOP long), then −7.35R into the close.

**Graveyard** (507 lots): peak +7.19R 09:56, then **09:56→close −67.13R** = market −9.56 + mismatch −11.91 + **bad entries −25.15**
+ stock −20.52; `CWT14-failbrk-orl-p05-long` −23.95 (banks TFC −4.07, HBAN −2.39, FITB −2.19 — longs in the fading bank group),
`RW2-exhaustion-noon-adv150-short-FD` −23.15, `CWT14-failbrk-pdl-p05-long` −10.86, `CWT14-failbrk-pdh-p10-short` −10.63.
Simulated original brackets give −25.8R vs live −59.9R: ~34R of the loss is execution / fills / cap order, not the rules.

**Generator** (255 lots, halted 10:50): one leg −174.97R = market +7.21 + **mismatch −74.38** + entries −26.57 + stock −81.23;
`GEN-261029-08-…-RSI14ge65-AM-SPYgt0p5-hold-short` −47.90, `GEN-261026-05-…-OPEN-BRopgt0p5-hold-short` −44.70,
`GEN-261021-02-…-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long` −31.73: the SPY>0.5 / breadth-gated GEN rules fired en masse at
the open on a day the gate was "on" from 09:35 and the groups moved against them.

**Recurring swing types (merged):** (1) *short book vs a strong-QQQ tape* — 11-03 Primary / T1 (lost while SPY climbed to
+0.51%) and today Primary 12:16→close, T2 / Gen mornings → merged into **swing1104-L7** (with swing1103-L3 / L6);
(2) *failed-breakdown longs on a falling small-cap / sector tape* — T2 and GY today, T2 11-03 (LEN / HD pdl-p10 −1.0..−1.3R
in the 10:39→11:47 leg) → **swing1104-L8** (merges nightly1104's "pdl longs on small-cap-down days").

**Leads pre-registered tonight** (research/bdi/swings/hypotheses.jsonl, written before any 2-year read):
- **swing1104-L7** (short guard, qqq_fo ≥ +0.75% at entry, all 47 short lab setups): **fails.** Class A n 77,766 on 138 days,
  raw −0.017R vs the other shorts −0.067R — excess **+0.031R** (train −0.003 / valid +0.052, t +1.03): shorts entered on a
  strong-QQQ bar are *less* bad than the rest. On up days A −0.060R vs B −0.258R; the problem on up days is shorting at
  all, not the QQQ bar. As a filter it would keep 83% of trades but only 79% of top-decile winners. Forward bar stands.
- **swing1104-L8** (CWT14 failed-breakdown longs, IWM ≤ −0.50% from open at entry, 8 setups): **fails.** Class A n 130,363 on
  229 days raw −0.088R vs B −0.093R, excess +0.004R (t +0.27; train −0.014 / valid +0.014); keeps 77% of trades / 74% of
  top-decile winners (filter-creep bar missed too). By day type the class is a direction bet on the close (up days +0.108R,
  down −0.170R) — not knowable at entry. The whole pool is −0.092R per trade on 2 years.
- Lead count: **9 in the file (7 earlier + L7, L8)**, 0 passing on 2 years.

**Forward tallies of existing leads** (forward.py, 11-04 = first out-of-sample day): L1 no class-A trade (B 8, −0.193R);
L2 no trigger; L3 not qualifying (SPY +0.55%, IWM −0.05% at 10:00); **L6 counter-index n 469 −0.389R vs others −0.198R
(diff −0.191R)** — the up-day sign, as the 2-year table predicted (up days −0.082R excess, quiet +0.305R); latch shadow
(nightly) GY latch cost +43.4R; FLOW1 day 1 −3.90R. Best forward lead so far: none positive after 1 session (L6 has the
most data, n 469, wrong sign on an up day). Note: research/bdi/swings/forward.py rewrites the whole `forward` block of
every hypothesis (it wiped the nightly's latch / FLOW1 / L1-L3 day records tonight; restored by hand from HEAD) —
housekeeping fix queued (make it touch only L1/L2/L3/L6).

## 0. Per-account session review (accounts_out.txt, trades_bdi_out.txt; peak from nightly1104/daily_peak.csv)
| account | P/L after costs | trades | win% vs break-even | avg R | peak → close (give-back cause) | best / worst setup |
|---|---|---|---|---|---|---|
| Primary | **−$208.63** (−10.75R) | 54 | 48% vs 59% | −0.199 | +$463 12:17 → −$209: midday short re-load into QQQ's second leg (§0b) | ST7-rsi50dn-long-pm-t1s1-FD +3.1R / +$118, L3-gap-slope-fromopen-FD +2.7R; MF2-FD −6.5R / −$232, L3-rsi5hi-FD −2.9R / −$199 |
| Testing 1 | −$36.66 (−4.30R) | 20 | 40% vs 56% | −0.215 | +$7 11:01 → −$37: oil turn + 15:35 SPY dip on index momentum longs | ST7Q +2.3R; CWT05-flush −3.3R, NS1-FD −1.7R |
| Testing 2 | −$517.68 (−32.2R) | 139 | 45% vs 60% | −0.232 | +$12 10:09 → −$518: failbrk longs + RW3S shorts both lost in the morning | CWT09-gapdn-vwaploss-g10 +0.9R, RW1-FD +2.2R; CWT14-pdl-p10 −12.8R, -lowvol −8.6R |
| Graveyard | −$771.90 (−59.9R) | 507 | 54% vs 61% | −0.118 | +$49 09:57 → −$772: bad entries (−25R) + bank longs | LIQ-orl-sweep +14.8R, CWT09-gapdn-bounce-g5 +5.1R; CWT14-pdl-p05 −10.7R, -lowvol −8.4R |
| Generator | −$2,454.65 (−175.2R) | 255 | 22% vs 59% | −0.687 | never green; halted 10:50 (account loss limit) | GEN-261022-07 +1.0R; GEN-261021-02 −32.0R, GEN-261029-08 −47.9R |

**Exit what-ifs (all 975 trades, 1-min SIP, costs in; one day = diagnosis, not evidence):** trail +0.5R/0.5R best in
Primary (−3.1R vs −10.7R live) and T2 (−20.2R); stop-and-reverse halves Gen and T2 losses (−93R / −9R); hold-to-close
best in GY (+22.8R). The opposite side 1R/1R made +0.173R per trade (+142R in Gen alone). **Hindsight check:** shorts with SPY
≥ +0.25% from the open at entry (485 trades) lost −0.377R live and the opposite side made +0.280R; with SPY below that line
−0.203R / +0.067R. On 11-03 (quiet) the same flag was the *winning* side (+0.357R) — the flag is a day-type bet, which is
exactly what L6's 2-year table says; not a rule.
**Loss types:** stopped-then-reversed 96 / wrong side after a big swing 92 (Primary: 12 / 10 of 28 losers, −$544 / −$544
by type sum incl. overlaps), never worked 137, small-MFE-then-failed 131, gave back gains 73 (Gen 36, GY 30).
**Give-back (MFE ≥ 0.5R, closed red):** Gen 41 trades −42.3R, GY 51 −54.3R, T2 10 −10.0R, Primary 8 −9.2R, T1 0.
**Same-symbol stacking (≥ 2 sister setups, same side, ≤ 30 min):** T2 20 stacks / 40 lots −12.3R (extra lots −6.1R; KORU
2 lots −$64); GY 63 stacks / 142 lots −14.9R (**SOXS 3 lots −$192**: inverse-semis longs = short semis into QQQ +1.9%; by
underlying the GY book was also short semis via SOXS while long other semis — leveraged/inverse ETFs count against their
underlying); Gen 14 stacks −34.0R (extra lots −18.6R). Primary had no stack.
**Notable skips:** the Move Hunt list above (12 skipped movers); Gen's 799 "halted" skips after 10:50 (what-if −53R saved).

**R by day type (QDAY report; daytype.py; all live sessions 10-06..11-04: 11 quiet, 6 up, 5 down by SPY o-c ±0.25%):**
| account | down | quiet | up | SPY above open @10 | below |
|---|---|---|---|---|---|
| Primary | **+0.269R** (200) | −0.096 (336) | −0.165 (322) | +0.072 (469) | −0.168 (389) |
| Testing 1 | −0.077 (842) | −0.083 (1747) | −0.214 (882) | −0.039 | −0.151 |
| Testing 2 | −0.254 (1126) | −0.065 (2062) | −0.139 (1190) | −0.026 | −0.194 |
| Graveyard | −0.205 | −0.099 | −0.114 | −0.141 | −0.121 |
| Generator | −0.218 | −0.310 | −0.434 | −0.325 | −0.288 |
Live setups positive on **both** up and down days (≥ 10 trades each): 9 — T1 `L3-gap-slope-fromopen-FD` (+0.198 down /
+0.268 quiet / +0.204 up, 222 trades: positive in all three), T1 `MF4-h40-open-flowsell-FD` (+0.356 / +0.345 / +0.100), T2
`RW1-gapdn-bounce-flowsell-short-FD` (+0.298 / +0.116 / +0.312), T1 exhaustion_short, Primary RW5-FD / RW3-FD / MF2-FD (negative on
quiet days), GY CWT09-gapdn-bounce-g5, Gen GEN-261022-07. Small samples (10-38 per cell), several rule changes inside (above).

**Concrete edits (tested or queued, none applied):** (1) Primary midday short re-load → L7 tested tonight (fails: strong-QQQ shorts are not worse than other shorts on 2 years);
(2) CWT14 failbrk longs on a falling small-cap tape → L8 tested tonight (fails: excess +0.004R); (3) GY burst lots → GY-BP replay
(§4) says a lower per-setup cap only trades less of a losing book (no edit); (4) forward.py clobber → housekeeping.

## 1. Every trade (research/bdi/1104/per_trade_1104.csv; patterns.csv +543 loser rows for 11-04)
975 trades with bars (all), 543 losers classified. Per-trade rule values at entry (from-open, VWAP distance, 15-min
return, SPY from-open), MFE / MAE / time to MFE, the 9 exit what-ifs incl. stop-and-reverse and re-entry, the opposite
side, the hindsight flags and the loss type are in per_trade_1104.csv; by-setup sums in by_setup_1104.csv.

## 2. Patterns → testable rules
- Shorts on a strong-QQQ tape (Primary midday, T2 / Gen mornings; 11-03 Primary) → L7 (tested, §0b / §4).
- Failed-breakdown longs on a falling small-cap / sector tape (T2 / GY today, T2 11-03) → L8 (tested).
- Counter-index edge appears only on quiet days, and quiet days are not knowable from "quiet so far" (QD1) → QR1 / QR2:
  can the *opening half hour* tell a range day from a trend day? (tested, §3).
- Opening group gap-up fade (banks today, banks 11-03) → backlog, needs the open frame.

## 3. New tested idea (QDAY): QR1 predictor and QR2 narrow-open counter-index setup
**QR1 — can the 09:30-10:00 SPY range tell a quiet day at 10:00?** (qr1.py, SPY 1-minute, 431 open sessions, 3 configs,
pre-registered bar: quiet-close share ≥ base + 15 points in train AND valid, flag on ≥ 10% of days.)
| config | train flag share / quiet if flagged / base | valid | pass |
|---|---|---|---|
| P1 low OR ratio (bottom tercile) & \|fo10\| ≤ 0.25% | 27% / **44.4%** / 26.9% (+17.6 pts) | 23% / 41.2% / 35.7% (+5.5) | no |
| P2 high OR ratio & \|fo10\| ≤ 0.25% | 11% / 20.0% (−6.9) | 15% / 26.1% (−9.6) | no |
| P3 \|fo10\| ≤ 0.10% & prior day quiet | 10% / 7.7% (−19.2) | 15% / 50.0% (+14.3) | no |
Descriptive (not a test): quiet-close share by OR-ratio quintile 40% / 40% / 41% / **24% / 20%**, mean |o-c| 0.37 → 0.82%.
A wide opening half hour marks a trend day; a narrow one does not mark a quiet day. Today: OR ratio 0.84 (top quintile),
fo10 +0.55% → trend-day flag, and the day closed +0.48% (up).

**QR2 — counter-index entries only on narrow-open days** (qr2.py; pre-registered after QR1's table, before any trade
list was read; 1 config; all 95 lab setups' 2-year trades ≥ 10:05; counter = short with SPY ≥ +0.25% / long with SPY ≤
−0.25% at the entry bar): **fails.** Gated n 137,302 on 251 days, **−0.059R** (t −3.53), excess +0.007R (train −0.071 / valid
−0.053 raw); the wide-open control is the same (−0.058R). Quiet days +0.112R / +0.098R, up −0.125 / −0.073, down −0.095 /
−0.090: the opening range does not separate the counter edge — it is still only on the (hindsight) quiet close.
→ backlog `qr1-1104-opening-range-trend-day-flag` (parked, with the descriptive trend-day flag as a sizing input for SIZE1:
"smaller size on quiet days" can use the inverse — counter entries on wide-open days are not better either, so the flag
is information for sizing, not a filter).

## 4. Swarm (queue order; SIZE1 and FLOW1-2Y left to their own runs) — all configurations, failures included
| # | config | result | pass? |
|---|---|---|---|
| 1 | GY-BP cap 12 (queue item GY-BP) | net +124.5R, but only 1 new setup funded; dropped lots −0.139R vs kept −0.130R | no (pre-registered question fails) |
| 2 | GY-BP cap 18 (sensitivity) | net +34.3R, 0 new setups funded | no |
| 3 | QR1-P1 low OR & flat fo10 | +17.6 / +5.5 pts | no |
| 4 | QR1-P2 high OR & flat fo10 | −6.9 / −9.6 pts | no |
| 5 | QR1-P3 flat fo10 & prior quiet | −19.2 / +14.3 pts | no |
| 6 | QR2 counter-index on narrow-open days | −0.059R, excess +0.007R, t +0.40 | no |
| 7 | swing1104-L7 strong-QQQ short guard | excess +0.031R, t +1.03 (wrong sign) | no |
| 8 | swing1104-L8 IWM-down failbrk-long guard | excess +0.004R, t +0.27 | no |
8 configurations, 0 pass; no holdout was scored (nothing reached it); the locked block was never read.
Queue: SIZE1 and FLOW1-2Y left to their own runs (their data is now in place, DATA.md).

**GY-BP replay (queue item 3, journal replay, Graveyard 10-21..11-04, 11 sessions; gybp.py → gybp_out.txt):** a per-setup cap of
12 instead of 25 would have dropped 850 lots (−118.4R) and funded 53 of 101 buying-power rejects (+6.1R, 26 setup-days, but
only **1** setup that had no live trade that session) — net +124.5R (w/o best session +97.4R, t 4.37). **The pre-registered
question fails:** buying power is not what starves later setups (≤ 59 BP rejects a day, only on 11-02 / 11-03), and the cap
spreads almost nothing. The "saving" is not an edge: **dropped lots averaged −0.139R vs kept −0.130R** — the cap does not
pick worse lots, it just trades fewer lots of a book that averaged −0.132R. Cap 18: net +34.3R (dropped −0.092R vs kept
−0.135R). No decision; GY's playing-time question is answered by the rotation plan (ROLL1), not a lower cap.

## 5. Decisions / suggestions
**No DECISION tonight** (0 of 8 pass). Nightly's DECISION L3H (L3-gap-slope-rsi5hi-FD Primary → Testing 1) stands on its own
evidence; tonight adds: NRIX ×3 was −3.32R of Primary's −16.44R give-back leg (stock-specific).
Near-misses / low-rep suggestions: none from tonight's tests. FYI (live, small samples, rule changes inside): T1-era
`L3-gap-slope-fromopen-FD` (now in Primary since 10-30) is the only live setup positive on down, quiet AND up days
(222 trades; +0.198 / +0.268 / +0.204R) — consistent with QDAY (b); its Primary record since the move is in the nightly
scorecard. Avg R w/o best session for GY-BP: +97.4R of +124.5R (best session 11-03 = 22%), not a setup record.

## Files
research/bdi/1104/: NOTES.md, DATA.md, dl_wrapper.py, headtail_wrapper.py, bt_all.py + setups.csv, accounts.py, swings.py,
trades_bdi.py, daytype.py, gybp.py, qr1.py, qr2.py, leads_bt.py and their *_out.txt / csv; research/bdi/moves/moves.csv
(+100), moves_1104_out.txt; research/bdi/patterns.csv (+543); research/bdi/swings/hypotheses.jsonl (+L7, L8; L6 forward),
forward.csv (+4); research/backlog.jsonl.

*Educational only — not financial advice.*
