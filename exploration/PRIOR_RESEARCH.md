# Prior research inventory (as of 2026-11-27 close)

Educational only — not financial advice.

Sources: docs/RESEARCH_RECAP_1125.md, research/wave3..wave6_1127 SUMMARY, inspector_1127, consultants_1126, primshorts_1126, squeeze_1125, neveragain_1125, l3refire/rwout/taileff/stopfloor/cfprimary_1127, longs_1125, owner inbox 11-27, docs/live/decisions.json, research/backlog.jsonl (1,198 rows), research/ledger.jsonl. Fresh numbers in (c) come from `exploration/sandbox/inventory/` (Primary journal and all 10 journals, run 1, LR8 R after costs, read-only).

**Configs tried so far: about 9,363 (tonight's waves 3-6 included).** Lineage bar: t ≥ about 4.3. Nothing has reached it.

## (c) The numbers that matter most

### Primary since Day 1 (10-23 .. 11-27): 25 sessions, 943 trades
| Metric | Value |
|---|---|
| Total R after costs (LR8) | **−147.0R** (−5.88 R/day, day t −1.69) |
| Without best day (11-12, +39.9R) | −186.9R |
| Green days | **8 of 25 (32%)** |
| Green weeks | **1 of 6** (11-16..20, +4.1R, which still had 3 red days) |
| Red days per full week | 3, 3, 4, 3, 3 (average 3.2 of 5) |
| Worst days | 11-25 −42.3, 11-10 −34.8, 11-11 −28.3, 11-06 −26.1, 11-09 −20.0 |
| Journal $ (pnl_adj) | −$4,208. The nightly brief's Alpaca figure is −$14,809, on a different basis. |
| Side | shorts 758 trades −124.6R (−0.164/trade) · longs 185 trades −22.4R (−0.121/trade) |

Weekly R: 10-23 −3.3 · 10-26 wk −10.1 · 11-02 wk −33.9 · 11-09 wk −44.7 · 11-16 wk +4.1 · 11-23 wk −59.2 (4 sessions; 11-26 was a holiday).

### Primary by setup since 10-23 (LR8 R after costs)
| Setup | Status | Sessions / trades | Total R | Avg R | Avg R w/o best day |
|---|---|---|---|---|---|
| L3-gap-slope-fromopen-FD | in Primary | 17 / 215 | −3.1 | −0.014 | −0.209 |
| RW3-gapdn-rsi5pop-flowsell-short-FD | in Primary | 24 / 166 | −7.6 | −0.046 | −0.155 |
| RW5-heat30-...-gapdn-short-FD | in Primary | 25 / 160 | −11.3 | −0.071 | −0.144 |
| NM-ETF-late-dip-di-long | in Primary (AV50 from 11-30) | 9 / 35 | −8.1 | −0.230 | −0.381 |
| MF4-h40-open-flowsell-FD | gone | 13 / 107 | −52.5 | −0.490 | −0.550 |
| MF2-open-rsimidhi-flowsell-FD | gone | 12 / 85 | −37.5 | −0.441 | −0.534 |
| L3-gap-slope-rsi5hi-FD | gone (11-11) | 7 / 22 | −10.3 | −0.469 | −0.513 |
| ST7-rsi50dn-long-pm | gone (11-23) | 14 / 43 | −7.1 | −0.165 | −0.291 |
| Others (CWT14, NS5, NS1, CWT13, NS4, MF1) | gone | — / 110 | −9.6 | — | — |

- The four setups now in Primary made **−30.1R** of the −147R. Departed setups made about −117R. All four are negative without their best day.
- The nightly brief's longer windows show L3 at 19 sessions / 238 trades / −0.046R, RW3 at +0.076R (best day 151% of the total, `1 day`) and RW5 at +0.049R (188%, `1 day`).
- **Bench (2-year minute engine, LIVE-L costs):** the P4 book loses **−3.03 R/day on CHECK** (−2.05 with LATCH-OPEN) and −1.75 / −1.53 on T2. Every short is negative in every window, at about −0.09 to −0.18 R/trade.

### All 10 accounts since 10-23 (identical signals counted once)
| Side | Trades | R | R/trade | Day t | Green days |
|---|---|---|---|---|---|
| Long (all) | 15,154 | −2,430 | −0.160 | −2.74 | 7/25 |
| Short (all) | 13,645 | −2,315 | −0.170 | −1.42 | 9/25 |
| Long (no Graveyard) | 8,695 | −1,408 | −0.162 | −2.74 | 5/25 |
| Short (no Graveyard) | 9,312 | −1,775 | −0.191 | −1.24 | 7/25 |
| Since 11-19, long / short (no Graveyard) | 2,338 / 4,062 | −434 / −1,026 | −0.186 / −0.253 | | |

**Challenge to the goal framing:** shorts are worse, but only modestly. Per trade, both sides lose about 0.16-0.19R, which is the size of the cost wall (about 0.10-0.12R per trade). The problem is "no gross edge after costs", not mainly the side. 33 of 111 long setups (outside the Graveyard) are positive in total. The best are GEN-261020-09 (+76R, 259 trades), GEN-261023-07 (+64R, 139) and GEN-261027-10 (+26R, 176), but on 11-25 the top 3 longs made 90% of all long R (longs_1125).

**Realistic goal metrics (consultants_1126 C, neveragain_1125):** even a +0.5R/lot book (about 5x anything seen live) is red on 11% of days, so "green every day" is not reachable. The bars proposed: red days ≤ 11 a month, worst-5 ≥ −90R, 20-session floor ≥ −40R, no day worse than about −20 to −25R. A positive per-lot edge has to come first; without it, levers only trade less.

### Rule changes inside the 10-23..11-27 window (ledger)
| Date | Change |
|---|---|
| 10-28 | Primary position size ~$4k |
| 10-29 | −2R per-setup latch (counts closed R only) |
| 10-30 | Testing cost filter |
| 11-11 | TEAM-6 lineup |
| 11-12 | LR8 costs, account restructure |
| 11-17 | TSZ1 half lots in testing |
| 11-19 | C3 Epoch 1, U9-TGT |
| 11-20 | Stop rounding, FOOTRACE-EXIT |
| 11-21 | Cost-basis fix |
| 11-23 | ST7 out of Primary, BRAKE-BURST, PSHADOW |
| 11-27 | GYH V1+V3, ROT-B3, GEN seed (outside Primary) |
| **11-30 (next)** | AV50/ETF-STOP50 for NM-ETF in Primary; Friday-review moves |

## (a) Settled: do not repeat

| Theme | What was tested | Conclusion |
|---|---|---|
| **Shorts** | Gap-down trio (L3/RW3/RW5) re-scored at live costs (primshorts); removal of every subset (rwout); cost-zone filters (shortcost); index open-pop shorts; ULT/GEN shorts | Every short is negative on the bench in every window. Removing any one short helps by about the same amount (L3 +0.95, RW3 +0.95, RW5 +0.91 R/day CHECK). Against an exposure-matched size cut, no removal reaches t 2.8 on both splits. In other words, **less short exposure = less loss; no short is "special"**. Inverse-ETF guard is in forward test. |
| **Longs** | 10+ long hunts (0 of 367, etc.), LONGBOOK (live longs added to Primary, 0/8), UPDAY (16 long up-day setups, 0/16), OPENDRIVE early entry | No long passes after single-stock costs. The longs move against the short book (corr −0.07 to −0.30) but give back on down and quiet days. |
| **Costs** | LIVE-L model (32,131 live trades); stop floors in bp; cost filter CF-15 on Primary (0/2); spread caps (SPRD) | Costs are the wall: about 0.10-0.12R per trade, versus gross edges of 0 to +0.05R. Tight stops (<50 bp) lose −0.3 to −0.5R/trade, mostly through cost. A bp floor and the cost filter = "trade less", no better than random on both splits. LIVE-L under-charges stops of fewer than 6 spreads by 0.09R. |
| **Regime / steering** | ~4,100 regime/gate configs; REGSTEER, TAPE (7/7 fail), breadth gate (0/6), DAYTYPE (0/24), PMDIR, compass-as-trade (COMPASSIDX), GAPNEWS direction | Direction is a coin flip (09:50 movers: 4.9x chance to find, 49% direction; afternoon SPY: no model beats always-long). Steering a negative-intercept book only trades less. Volume is predictable (Hunch 67.7%). |
| **Hedges** | HEDGE-B SPY beta hedge; IDXHEDGE one-shot sleeve (0/12); SQZ long hedge; PAIRS (0/28) | Cost is fixed by an index hedge, but the tail is not: worst days are single-stock squeezes the index does not follow. Pairs: costs 3-10x the gross. |
| **Stops / exits** | ~22,000 giveback configs; 489 exit rules; stoplab; STOPFLOOR (0/18) | Holding beats cutting. Per-setup stop choice is noise. Keep −2R and current widths. Only exit pass ever: RW3/RW5 1.25x target (+0.044R, t 2.58), never started. |
| **Tail / risk levers** | neveragain G1-G4, squeeze B8/B12/B16/SV/SO, TAILEFF (0/6), −12R hard stop, stacking caps, L3REFIRE (0/7, FIRST1 lead) | Nothing beats an exposure-matched cut on both splits. LATCH-OPEN is pure insurance (E = 1.00 on CHECK). S8 is the most tail-efficient (7x a size cut) but fails the floor and day-count bars. Stacking caps cost the trio 13-21R. |
| **Sizing** | Size tiers (SZ-PROOF), size-up tests | Lost 33-47R on the test half; declined. Half lots in testing adopted. |
| **Index ideas** | Index open-dip family (IDXDIP 40 configs, family t 0.11); QQQOPEN 85 configs; DAYTYPE as SPY trades; MEREB1 | The family is flat. IDX3 is INCONCLUSIVE (t 2.20, falls to 1.24 under stress). IDX6 and IWM45 run as forward shadows. Shorts fail. |
| **Discovery** | Generator, guild (0/174), swarms, outside ideas (Reddit, podcasts, paper momentum 0/24), GEN siblings 0/56, ARENASTARS (G05/G07/G37 one-day) | Live arena "stars" are one-day records. Gross GEN edge (+0.09..0.12R) is eaten by about 0.11R cost at R = 0.25 ATR. |
| **Crypto** | crypto_r1-r3, MH4 peer laggards | Intraday followers lose after costs. A daily trend overlay cut drawdown (CRYPTO-SCOPE card open). |
| **Process** | Promotion standard, rotation, workbench tunes, inspector audit | Last week's rank does not predict next week's. 60/60 in-sample tunes lost. Cards often drop report caveats; two "day t" definitions exist; half-day calendar bugs (Hunch, Compass, IDXFWD) fixed or flagged. |

## (b) Left open

### Owner decisions pending (docs/live/decisions.json, 16 open)
| Card | Ask | Key evidence |
|---|---|---|
| **LATCH-OPEN** | −2R latch counts open R too (Friday epoch only) | 11-25 replay −37.4 → −8.3R; live worst-5 −28.2 → −17.0; bench days ≤ −20R cut ~75%. Insurance, not edge (t 1.77). |
| **L3-OUT** | L3 to On Deck / probation / keep | Bench +0.77 / +0.36 R/day (LO, t 3.4 / 3.7). Not specific to L3 (rwout). Skips the probation step. |
| **HS-SCALE** | SHOCK-V only | As built it blocks entries only and never fires before the −20R halt. No flatten or bug guards exist yet. |
| **B8-SHADOW** | Log the net-beta cap B8 as a shadow | Worst-5 −47% / −22%. Beats a random block on the tail; fails the constant-cut test on T2. Fires 185 of 252 days. |
| **PRIM-ADD3** | Add none of the 4 candidates | All 4 turned negative since 11-24. Recommendation: no. |
| ODP2 + ODB3 x7 | On Deck admissions (GEN longs/shorts) | All `1 day` records. ODP2 is open more than 3 nights. |
| T1X2 | Close On Deck's phantom 12 SOXX shares | Mismatch since 11-25. |
| CRYPTO-SCOPE | Daily crypto trend overlay in scope? | Drawdown 59% → 10-34% (CHECK). |
| COMPASS-HALF | Half-day compass handling | New 11-27. |

### Forward tests running (scored later; none due before Monday)
| Test | Status | Bar / due |
|---|---|---|
| Regime switches GAP-U / IDX3-P / SPYO-P (shadow) | 11 sessions: Primary cumulative GAP-U **+42.7R**, IDX3-P +19.4R, SPYO-P +0.4R. GAP-U would have switched off all 15 lots on 11-27 (+5.65R). | 15-20 sessions, ~12-10 |
| SPREADFLOOR shadow (F6/F8 skip, < 6 / < 8 spreads) | Merged on the default branch; logs from 11-30. Live lead: 100th pct vs random, 101/120 setups better, best day 18-19%. | 20 and 40 sessions |
| L3 leash K11/K12 | 11 of 20 sessions; dK11 −15.5R, dK12 −28.0R (hurting) | ~12-09 |
| NM-ETF frozen Primary test + AV50 | AV50 live from 11-30 | 25 sessions, by 12-31 |
| Compass gate (watch-only) | needs 25 marks | ~mid-Dec |
| Inverse-short guard | watch-only | ~12-04 |
| BRAKE-1 shadow | +4.31R since 11-02 | rolling |
| MEREBFWD (month-end SPY long) | first scored day **Mon 11-30** | n ≥ 12, t ≥ 2 |
| IDXFWD (IDX6 QQQ −1.5% → TQQQ; IWM45) | defects fixed in a8b92f9c57 | forward |
| Epoch 1 vs BASE1 twin | 6 paired sessions, +1.53 R/day (SE 1.60) | rolling to 12-18 |

### Research leads not yet closed
1. **Exposure is the honest lever.** RWOUT: removing all three shorts passes all 7 bars against random (worst-5 −25.7 → −3.6, red days per month 12.7 → 3.8 on CHECK, LO). The gain is the size of the exposure cut, so it is not a stock-picking edge, but it is what moves red days today. The book needs a positive-edge replacement, not more filters.
2. **L3 repeat lots with LATCH-OPEN on:** repeats are worse than first lots (CHECK −0.126 vs −0.100; T2 −0.161 vs −0.097). This interaction is untested (L3REFIRE salvage).
3. **Spread-aware costs:** add a spread term to LIVE-L. Tight-in-spread stops are under-charged by 0.09R, which flatters every tight-stop backtest.
4. **Half-day rule** (nightly-1127-halfday-hold-to-close): on 11-27, 53% of lots ended at the 12:55 flatten for −65.7R. Lab test: 3 configs. Next half day is 12-24.
5. **RW3/RW5 1.25x target:** passed (t 2.58, 6/6 weeks), never started.
6. **S8 insurance:** removes 1-3% of exposure and cuts worst-5 by 23% on CHECK, at no cost on a profitable book. Fails only the floor and day-count bars.
7. **Long candidates with real live size** (GEN-261020-09, -261023-07, -261027-10). The live records are carried by 11-25, and LONGBOOK says they do not help Primary on the bench. Only a forward test can settle them.
8. **Index residue:** IDX3 (n 57, +0.42R, t 2.20; stress t 1.24); IDX6 (n 16, +1.15R, t 3.29, 3 trades after 2022); IWM 0.75% at 09:45 (n 144, +0.24R, t 2.00). All are uncorrelated with Primary (corr 0.01-0.05). They are small diversifiers, not a fix.
9. **Inspector reproducibility gaps:** the LATCH-OPEN / HS-SCALE scripts were only in the scratchpad (since committed under neveragain_1125 / hsscale_1125). Keep one "day t" definition (footrace day_t).

## Bottom line
- Seven weeks of research converge on one picture: **the book has no gross edge after costs.** About 0.10-0.12R per trade goes to costs, against gross edges of about 0, on both sides.
- Every lever that has improved red days so far works by **trading less**: L3-OUT, RWOUT, LATCH-OPEN, B8, the cost filter.
- The realistic path to green weeks has three parts:
  - (1) cut the losing exposure now (insurance plus fewer or smaller short lots);
  - (2) protect the tail (LATCH-OPEN, S8 or B8, a real flatten);
  - (3) grow a positive-edge sleeve from forward-tested candidates (regime-switch shadows, spread-floor skips, index residue, the few long setups with size).
- Tonight's tracks should not re-run anything in table (a).

Educational only — not financial advice.
