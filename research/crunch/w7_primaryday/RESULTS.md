Educational only — not financial advice

# W7-primaryday — what makes Primary's days red, and do structural entry rules fix it? (crunch 2026-11-18)

Research only: no config, runtime, setup or branch change; nothing here is a decision. Plan pre-registered and pushed before scoring (`PLAN.md`, commit 22756a148; Addendum A written before H13 was scored).

**Data.** Primary journal (`mcf-data`), live run 1, 10-06..11-18 (11-18 complete: last flatten 15:55). R = pnl_adj / (|entry − stop| × shares), after costs (LR8 from 11-12). SPY 5-min and daily bars of the 670 traded names from Alpaca SIP (GET only). Locked block not read. Windows: **FIT** 10-23..11-05 (10 sessions), **CHECK** 11-06..11-18 (9), **EARLY** 10-06..10-22 (13, older lineup — for the current five it holds only RW3/RW5 on 10-20..10-22, so it is thin).

**Configurations: 26** (12 rules × 2 books = 24, plus H13 × 2). Bar t ≥ max(1.5, √(2 ln 26)) = **2.55**. **Nothing passed.**

**Rule changes inside the window (research/ledger.jsonl):** 10-26 ST7 promoted, CWT13 in/out; 10-28 rotations (CWT14-lowvol, NS4, MF2 base out) and Primary size ~$4k (slots 77, per-setup 30); 10-29 −2R per-setup latch (Primary); 10-30 L3-rsi5hi promoted, L3-fromopen re-promoted; 11-11 TEAM-6 lineup (NM-ETF in; MF2-FD/MF4-FD/L3-rsi5hi/others out over 11-11..11-16); 11-12 LR3 (halt/latch count after-cost R, halt counts open marks) and LR8 costs; 11-16 TEAM-6 open-ended; 11-19 (after window) C3-NS5 → Primary runs the five setups below. R is per unit of risk, so sizing changes do not distort it; the latch changes which trades exist (the simulation re-applies it, see Method).

## 1. Decomposition — why the red days were red (19 sessions, 10-23..11-18)

| Book | Trades | Total R | Avg R | W/o best day | Best-day share | Green days | Median day | Worst | Avg realised peak on red days |
|---|---|---|---|---|---|---|---|---|---|
| As traded (all lineups) | 773 | −52.7 | −0.068 | −92.6 | 43% (11-12) | 6/19 (32%) | −2.52 | −31.2 (11-10) | +1.9R (4 of 13 red days ever ≥ +3R) |
| Current five (L3-fromopen, NM-ETF, RW3, RW5, ST7) | 449 | +43.7 | +0.097 | +4.1 | 36% (11-12) | 8/19 (42%) | −0.52 | −26.7 (11-11) | +0.9R (1 of 11 ever ≥ +3R) |

What the data say (descriptive, not rules):

1. **Red days are lost by setups that are already gone.** Of the −145.7R on as-traded red days, −85.6R came from setups no longer in Primary (MF2-FD −36.8R, MF4-FD −38.5R, L3-rsi5hi −7.1R, CWT13 −4.4R ...). The lineup moves of 11-11..11-19 already removed the largest red-day source.
2. **It is a short book.** Longs are ~0 on both red and green days (−0.1R / +0.2R in total). Every red day is short-side R (as traded −145.6R of −145.7R).
3. **Red days are not giveback days.** Red days peaked at +1.9R realised on average (current five +0.9R) and went red from the start; green days peaked at +15.9R and kept +15.5R. This is why giveback locks failed before (Part 2 W3) and should stay closed.
4. **Squeeze is the loss mechanism, on up days.** Shorts lost −0.49 / −0.48 / −0.32R per trade when SPY moved against them (> +0.3%, +0.1..0.3%, flat) after entry, and won +0.24 / +0.37R when SPY moved with them. RW3+RW5: −25.0R on the 12 SPY-up sessions, +19.4R on the 7 SPY-down sessions; L3-fromopen is positive on both (+37.3R / +7.9R). Day R vs SPY open-to-close: corr −0.24 (as traded), −0.31 (current five). This is a day-type effect (Part 3 P2: day-type switches don't keep their sign); the RW3/RW5 SPY-exit Workbench copies (WB4, Testing D / Live Lab, 11-17) are the setup-level test already running.
5. **Time of day.** Current five, entries ≥ 13:00: 103 trades, −18.0R (red days −26.0R, green days +8.0R); 10:30–13:00 carries the edge (+58.2R); before 10:30 +3.5R. L3-fromopen ≥ 13:00 −5.6R on 18 Primary trades and −15.3R on 29 trades in other accounts — but the L3-AM 13:00 cutoff already FAILED on the 2-year (research/l3_bespoke_1117), so this is listed, not proposed.
6. **Clusters, stacking, repeat losers are not where the red days come from.** Lots entered in 5-min clusters of ≥ 5 lost −0.45R/trade on red days but won +0.35R on green days (net −13.7R on 224 lots); singles/pairs were worse (−57.2R on 373). Stacked lots (another Primary lot open on the symbol): −2.7R net on 152 lots. Entries after a loss on the same symbol: 21 lots, −6.1R. All small or two-sided.

## 2. Structural rules tested (pre-registered, point-in-time, entries removed only)

Method: entries walked in time order per session; a removed lot never opens (so it does not count toward later caps); the −2R per-setup latch (Primary from 10-29) is re-applied so that a rule which makes a setup's realised R hit −2R earlier blocks its later lots (baseline reproduces the journal exactly: 0 trades dropped). Freed slots are **not** refilled — skipped-signal outcomes are not used; caps that block lots would in reality let some other signals in. Paired t on per-session difference (rule − baseline), FIT+CHECK.

Rules: **SYM1** no new entry on a symbol after any Primary loss on it that day; **STACK1** one open Primary lot per symbol across setups; **CLU3 / CLU5** max 3 / 5 new entries per 5-min decision bar; **CORR2** no new lot when ≥ 2 same-side lots are open in names with trailing-40-session daily-return corr ≥ 0.60 (closes to the prior session); **SECT3** ≤ 3 same-side open lots per sector (sector_map.json; covers only 32% of traded names); **TOD-FH** ≤ 6 entries before 10:30; **FLAT25** skip entries while |SPY from open| < 0.25% (hypothesis from the descriptive step — FIT/CHECK not clean, only EARLY is); **+L3x** = same rule with L3-fromopen exempt (the protect rule).

### Current five (the book Primary runs from 11-19)

| Rule | Lots removed | dR | FIT | CHECK | EARLY | t | dR w/o best day | Green % | Median day | Worst day | ≤-10R days | Better/worse | Per setup (R) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SYM1 | 14 | +0.1 | -3.1 | +3.2 | -5.5 | 0.02 | -3.1 | 42→47 | -0.52→-0.20 | -26.7→-26.7 | 2→2 | 1/1 | RW5 -0.9; L3-fromopen +1.0 |
| STACK1 | 93 | -10.1 | +0.3 | -10.4 | -8.6 | -0.60 | -16.7 | 42→53 | -0.52→+0.05 | -26.7→-20.1 | 2→2 | 2/1 | L3-fromopen -15.0; RW5 +0.2; RW3 +4.8 |
| CLU3 | 62 | -39.2 | -10.4 | -28.8 | -24.7 | -1.60 | -41.2 | 42→42 | -0.52→-0.52 | -26.7→-26.7 | 2→2 | 0/4 | L3-fromopen -20.6; RW3 -8.8; RW5 -5.2; ST7 -4.6 |
| CLU5 | 31 | -19.1 | +0.0 | -19.1 | -17.4 | -1.02 | -20.2 | 42→42 | -0.52→-0.52 | -26.7→-26.7 | 2→2 | 0/4 | L3-fromopen -14.7; RW5 -2.2; RW3 -1.1; ST7 -1.1 |
| CORR2 | 121 | -47.2 | -15.1 | -32.2 | -27.6 | -1.47 | -53.5 | 42→42 | -0.52→-0.59 | -26.7→-20.5 | 2→2 | 0/5 | L3-fromopen -31.6; RW3 -11.5; RW5 -2.6; ST7 -1.4; NM -0.1 |
| SECT3 | 24 | -17.1 | -3.9 | -13.3 | -12.6 | -1.47 | -17.1 | 42→42 | -0.52→-0.52 | -26.7→-26.7 | 2→2 | 0/3 | L3-fromopen -13.7; RW3 -3.1; RW5 -0.4 |
| TOD-FH | 5 | -2.7 | +0.0 | -2.7 | +0.0 | -1.00 | -2.7 | 42→42 | -0.52→-0.52 | -26.7→-26.7 | 2→2 | 1/1 | L3-fromopen -2.8; RW3 +0.2 |
| FLAT25 | 110 | +35.9 | +6.8 | +29.1 | -36.7 | 1.76 | +17.0 | 42→58 | -0.52→+0.55 | -26.7→-22.4 | 2→1 | 4/1 | NM -0.4; ST7 +1.4; L3-fromopen +8.7; RW3 +12.8; RW5 +13.3 |
| STACK1+L3x | 29 | +4.9 | +1.0 | +3.9 | -12.2 | 0.67 | +0.7 | 42→47 | -0.52→-0.52 | -26.7→-22.5 | 2→2 | 2/0 | RW5 +0.2; RW3 +4.8 |
| CLU5+L3x | 15 | -4.4 | +0.0 | -4.4 | -17.4 | -1.02 | -5.5 | 42→42 | -0.52→-0.52 | -26.7→-26.7 | 2→2 | 0/3 | RW5 -2.2; RW3 -1.1; ST7 -1.1 |
| CORR2+L3x | 65 | -17.8 | -15.1 | -2.8 | -27.6 | -1.15 | -24.1 | 42→42 | -0.52→-0.59 | -26.7→-20.5 | 2→2 | 0/4 | RW3 -12.7; RW5 -3.6; ST7 -1.4; NM -0.1 |
| SECT3+L3x | 5 | -3.5 | -3.9 | +0.4 | -12.6 | -0.88 | -4.1 | 42→42 | -0.52→-0.52 | -26.7→-26.7 | 2→2 | 0/2 | RW3 -3.1; RW5 -0.4 |

### As traded (all lineups)

| Rule | Lots removed | dR | FIT | CHECK | EARLY | t | dR w/o best day | Green % | Median day | Worst day | ≤-10R days | Better/worse | Per setup (R) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SYM1 | 21 | +6.1 | +1.7 | +4.4 | -2.8 | 0.95 | +1.7 | 32→37 | -2.52→-2.52 | -31.2→-31.2 | 6→6 | 4/2 | RW5 -0.9; MF4 -0.4; L3-fromopen +1.0; MF2 +1.1; NS5 +1.1; L3-rsi5hi +4.2 |
| STACK1 | 147 | +5.9 | +2.0 | +3.9 | -16.0 | 0.27 | -2.5 | 32→32 | -2.52→-1.89 | -31.2→-23.3 | 6→5 | 4/4 | L3-fromopen -14.7; RW5 -2.5; NS5 -0.9; NM -0.2; L3-rsi5hi +1.8; RW3 +5.8; MF4 +7.0; MF2 +9.6 |
| CLU3 | 156 | -0.7 | -8.2 | +7.5 | -8.5 | -0.02 | -27.8 | 32→32 | -2.52→-3.37 | -31.2→-28.7 | 6→4 | 4/6 | L3-fromopen -20.5; RW5 -8.6; RW3 -8.4; ST7 -4.6; NS5 -0.5; L3-rsi5hi -0.4; NS1 +0.1; CWT14 +6.3; MF4 +17.9; MF2 +18.1 |
| CLU5 | 79 | +1.0 | -6.4 | +7.4 | -9.6 | 0.03 | -21.5 | 32→26 | -2.52→-2.46 | -31.2→-31.4 | 6→5 | 5/4 | L3-fromopen -15.4; RW5 -3.1; ST7 -2.3; RW3 -1.1; NS5 +0.1; NS1 +0.6; CWT14 +4.2; MF2 +8.7; MF4 +9.3 |
| CORR2 | 225 | +1.1 | -5.2 | +6.2 | -33.9 | 0.02 | -22.3 | 32→32 | -2.52→-2.52 | -31.2→-24.7 | 6→3 | 3/7 | L3-fromopen -32.7; RW3 -11.5; RW5 -2.7; ST7 -1.4; NS5 -1.2; CWT14 -0.7; NM -0.5; L3-rsi5hi +1.2; MF4 +25.2; MF2 +25.3 |
| SECT3 | 55 | -9.6 | -6.2 | -3.5 | -8.4 | -0.57 | -20.0 | 32→26 | -2.52→-2.52 | -31.2→-32.1 | 6→6 | 2/4 | L3-fromopen -15.0; RW3 -3.1; L3-rsi5hi -0.4; RW5 -0.4; MF4 +3.2; MF2 +6.1 |
| TOD-FH | 36 | +2.9 | +4.7 | -1.9 | +35.0 | 0.33 | -2.7 | 32→32 | -2.52→-2.52 | -31.2→-35.1 | 6→5 | 3/3 | L3-fromopen -2.6; MF2 -2.4; L3-rsi5hi -0.4; RW3 +0.2; CWT14 +3.3; MF4 +4.8 |
| FLAT25 | 226 | +56.3 | +13.8 | +42.4 | -21.5 | 1.63 | +23.9 | 32→37 | -2.52→-0.46 | -31.2→-24.2 | 6→4 | 9/4 | NS5 -3.4; CWT14 -1.6; NS1 -0.9; NM -0.4; NS4 +1.0; MF1 +1.3; ST7 +1.4; L3-rsi5hi +3.9; MF2 +6.7; L3-fromopen +8.7; RW3 +12.8; RW5 +13.3; MF4 +13.4 |
| STACK1+L3x | 82 | +20.6 | +2.7 | +17.9 | -19.7 | 1.32 | +10.5 | 32→32 | -2.52→-2.46 | -31.2→-22.4 | 6→4 | 4/3 | RW5 -2.5; NS5 -0.9; NM -0.2; L3-rsi5hi +1.8; RW3 +5.8; MF4 +7.0; MF2 +9.6 |
| CLU5+L3x | 62 | +16.4 | -6.4 | +22.8 | -9.6 | 0.66 | -6.1 | 32→26 | -2.52→-2.46 | -31.2→-30.7 | 6→5 | 5/3 | RW5 -3.1; ST7 -2.3; RW3 -1.1; NS5 +0.1; NS1 +0.6; CWT14 +4.2; MF2 +8.7; MF4 +9.3 |
| CORR2+L3x | 175 | +31.8 | -4.1 | +36.0 | -33.9 | 1.05 | +8.5 | 32→32 | -2.52→-2.52 | -31.2→-22.7 | 6→3 | 3/6 | RW3 -12.7; RW5 -3.7; ST7 -1.4; NS5 -1.2; CWT14 -0.7; NM -0.5; L3-rsi5hi +1.2; MF2 +25.2; MF4 +25.5 |
| SECT3+L3x | 39 | +8.6 | -5.1 | +13.7 | -11.7 | 0.68 | -1.8 | 32→26 | -2.52→-2.52 | -31.2→-28.3 | 6→5 | 2/3 | RW3 -3.1; L3-rsi5hi -0.4; RW5 -0.4; MF4 +3.2; MF2 +9.2 |

### H13 (Addendum A): RW3/RW5 entries ≥ 13:00 worse? — FAIL

Primary's 13:00-hour RW3/RW5 loss (−14.5R) does not replicate elsewhere: in other accounts RW3/RW5 (all variants) ≥ 13:00 averaged +0.316R (19 trades) vs +0.235R (73) before; exact -FD names +0.292 vs +0.289R; paired diff t 1.26 the wrong way. The whole RW family (2,568 trades) shows no afternoon effect (−0.075 vs −0.080R, t 0.45). Not a setup lead.

## 3. Verdicts (honest)

- **Every cap / de-dup / correlation / sector / first-hour rule costs Gap-Down Recovery Fade (L3-fromopen) R** (−2.8 to −31.6R): its edge comes in clustered, correlated, stacked entries on its big days (11-12 +31.0R, 11-16 +16.4R). They fail on the current five (dR −2.7 to −47.2R) and are noise on the as-traded book (t ≤ 0.33, gains come only from removing MF2/MF4 lots that are already out of Primary). **FAIL — add to the stop list.**
- **With L3 exempt**, only **STACK1+L3x** is positive: +4.9R on the current five (FIT +1.0, CHECK +3.9; RW3 +4.8R, RW5 +0.2R, 2 better / 0 worse; green 42 → 47%, worst day −26.7 → −22.5R) but t 0.67, the gain without its best day is +0.7R, and EARLY is −12.2R (it would have cut the +65.8R 10-22 RW3/RW5 burst). The same trade-off that sank the RW3/RW5 open-lot caps in Part 2. **FAIL; at most a journal-only shadow tag.**
- **SYM1** (symbol loss limit) is ~0 (+0.1R current five; 14 lots); a no-cost hygiene rule but no R. **FAIL (no effect).**
- **FLAT25** (skip entries while SPY is within ±0.25% of its open) is the largest number found: current five +35.9R (FIT +6.8, CHECK +29.1; RW3 +12.8, RW5 +13.3, L3-fromopen +8.7, ST7 +1.4, NM-ETF −0.4: 4 better / 1 worse), green 42 → 58%, median −0.52 → +0.55R, ≤ −10R days 2 → 1; as traded +56.3R, t 1.63. But it was found by looking at the same window, t 1.76 < 2.55, and the only clean data (EARLY) say **−36.7R (current five, 3 sessions, the 10-22 burst) / −21.6R (as traded, 13 sessions)**. **FAIL as a rule.** The honest next step is a fresh-data test, not a live change (proposal W7-FLAT below).
- **Positive R every day is not reachable with entry-side structure on this book.** The current five's red days are RW3/RW5 shorts squeezed on SPY-up sessions; their green days need the same clustered shorts. A structural rule that removes the squeeze also removes the payday. What moved the median day is the lineup (as traded −2.52R → current five −0.52R), which is already done (TEAM-6 + C3-NS5).

## 4. Effect on each setup (current five; dR over FIT+CHECK)

| Setup | Base R | Rules that help it | Rules that hurt it |
|---|---|---|---|
| L3-gap-slope-fromopen-FD | +45.2 | FLAT25 +8.7, SYM1 +1.0 | CORR2 −31.6, CLU3 −20.6, STACK1 −15.0, CLU5 −14.7, SECT3 −13.7, TOD-FH −2.8 |
| RW3-gapdn-rsi5pop-flowsell-short-FD | −1.3 | FLAT25 +12.8, STACK1(+L3x) +4.8, TOD-FH +0.2 | CORR2 −11.5, CLU3 −8.8, SECT3 −3.1, CLU5 −1.1 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | −4.3 | FLAT25 +13.3, STACK1 +0.2 | CLU3 −5.2, CORR2 −2.6, CLU5 −2.2, SYM1 −0.9 |
| ST7-rsi50dn-long-pm-t1s1-FD | +2.0 | FLAT25 +1.4 | CLU3 −4.6, CORR2 −1.4, CLU5 −1.1 |
| NM-ETF-late-dip-di-long | +2.0 | — | FLAT25 −0.4, CORR2 −0.1 |

## Caveats

19 sessions (fit/check halves of 10 and 9; one day ≈ 5 points of green %). EARLY for the current five is three sessions. Removed lots are not replaced by skipped signals (caps understate what a live cap would substitute in). Correlations use daily closes only. SECT3 maps 32% of names. The −20R account halt is not re-simulated (rules only remove lots, so it could only fire later or not at all). Scratch data deleted after the run; scripts in `src/` (they read the journal from the state branch and Alpaca bars; keys from the environment, never printed).
