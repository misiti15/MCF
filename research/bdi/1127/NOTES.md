# BDI daily 2026-11-27 (Friday, HALF DAY: close 13:00 ET, flatten 12:55): CAPTURE / COVERAGE

*Educational only — not financial advice. Live figures are **paper** results; the lab covers 2 years (22 open months
2024-10..2026-11). **Configurations tried tonight by BDI: 1** (DIPV-1127 A). The locked block 2024-11-01..2025-02-28 was
not read. Scratch under scratchpad/s1127 (journals copied there and deleted after). Tonight's research waves are cited,
not redone: research/wave3_1127/SUMMARY.md (8 studies, 224 configs, nothing passed; QQQOPEN IDX3 INCONCLUSIVE), wave 4
(idxdip / daytype / pairs / gapnews / pmdir: all FAIL per their REPORT.md) and L3REFIRE-1127 (pre-registered, running).*

**Rule changes in the window (ledger).** Effective 11-27: GYH V1+V3, the GEN seed and ROT-B3 (testing / Generator /
Graveyard only; nothing in Primary since 11-23). Next: **11-30 AV50 / ETF-STOP50** (Primary `NM-ETF-late-dip-di-long`
burst stop) and the 11-27 Friday review moves (1 Generator → Graveyard, 3 Graveyard retirements). Earlier inside the
10-06..11-26 day-type window: 10-28 Primary sizing, 10-29 −2R latch, 11-12 LR8 costs, 11-16 ROT1, 11-17 TSZ1, 11-19 C3
Epoch 1, 11-20 stop rounding / FOOTRACE-EXIT, 11-21 cost-basis fix, 11-23 ST7 out of Primary, BRAKE-BURST, PSHADOW.
Per-day averages below mix these.

**Market: a morning dip, then a grind up.** SPY −0.56% from its open at 09:50, low −0.73% at 10:05, back at its open by
10:40, +0.49% at the 12:59 bar (daily bar open→close +0.34%: an **up** day by the ±0.25% rule); QQQ +0.99% (low −1.09%
10:05), IWM +0.65%. Half day: 3.5 hours of tape, flatten at 12:55.

## 0a Move Hunt (research/bdi/moves/moves_1127_out.txt; moves.csv +100 rows; precursors_1127_k05_out.txt)
Half-day copy `research/bdi/1127/moves_hd.py` = moves.py with decision points 09:35..12:25 and the forward window capped at
the 13:00 close (bars after 13:00 are extended-hours prints, ignored); all 10 accounts (672 trades on 393 symbols), 1,287
liquid names, top 25 per side.

| Set | 11-27 | 11-25 (last session) |
|---|---|---|
| All movers | **1/50 = 2%, +0.96R** | 2/50 = 4%, +0.07R |
| Tradable (blackout removed) | **1/50 = 2%, +0.96R** | 2/50 = 4%, +0.07R |

- **Catch:** Sprouts Farmers Market `SFM` short (Testing A `GEN-261026-04-ORBfailDn-…-holdtr-short`, +0.96R). Long side 0 of 25.
- **What was known at the decision point:** **48 of 50 movers were decided 09:35–09:45**, before the owner's ≥ 09:50 entry
  rule, while SPY sat near its low (median SPY −0.74% for the long movers). Long movers were names down from their open at
  that point (median fromOpen −0.23%) that rallied with the index (VRTX 1.69 ATR, IP, MO, CHKP, MTCH, CHTR, LYFT, ZBRA,
  PANW); short movers were early pops that faded (SNDQ, GGG, AXSM, the bitcoin ETPs GBTC / IBIT / FBTC / BITO). Only
  3 of 50 (TGTX 10:05, EBAY 10:25, LVS 11:30) were decidable inside the trading window — today's ceiling was low.
- **Miss reasons (all set):** no setup signalled 21, traded outside the move 11, blackout 8 (none on the event day),
  skipped 7 (burst brake 5: Generator Podcast: Breadth Thrust, Strong Large Caps
  `GEN-POD1022-01-thrasher-breadth-thrust-stocks-holdtr-long` fired on 157 names at
  10:40, near the END of these moves; its 30 taken lots lost −8.52R, so the brake did not cost R today), not
  shortable / ETB 2 (SNDQ, MSTZ), wrong side 2. Wrong-direction trades 6, −5.82R.
- **K6 context (research/bdi/1127/k6_today.py → k6_today_out.txt; MOVEHUNT_1127 frozen coefficients, per-day z-scores,
  movers = top 2% by |12:59 close − 09:50 price| / ATR):** capture@20 **4/34 (10.0× chance)**, @50 5/34 (5.0×), @100
  6/34 (3.0×) — the "which names" half works on a fresh day. Direction: continuation 30% on the top 20, **0 of 5** movers in
  the top 50 continued (VRTX, HPQ, TGTX, MO, PKG all reversed up). 11 of the 50 Move Hunt names were in K6's top 50; none
  was traded the right way. That reversal is what DIPV-1127 tested (step 3); it fails.
- **Precursor scan (K 0.5 ATR, one day, hindsight labels):** long moves came from the first decision frames (tod q1 lift
  3.4×), in-play names (vol_exp q5 2.5×), gap-down / no-gap names (gap q1–q3 1.4–1.5× vs q4–q5 0.2–0.3×); short moves from
  in-play, high-rvol early pops (vol_exp q5 2.2×, rvol q5 2.5×, gap q1 2.4×). Same shape as 11-25 (dip-morning reversals).

## 0b Swing autopsy: Primary (research/bdi/1127/swings.py → swings_out.txt, timeline_p.csv; method unchanged)
Half-day copy (1-min index 09:30–12:59); AHCO / AVBP (ADV < $60M, outside the fetch) added from a separate SIP pull.
- **Close:** **−5.65R after costs**, Alpaca −$204 (nightly), 15 shorts (3 wins). Realised peak +1.54R (11:11).
  **Mark (1-min, no costs while open): peak +2.62R at 11:26, trough −6.23R at 12:35.**

| Leg | R | Market | Setup-day mismatch | Bad entries | Stock-specific |
|---|---|---|---|---|---|
| 10:30 → 10:49 | −2.68 | −0.63 | −0.00 | −0.16 | −1.89 |
| 10:49 → 11:26 (peak) | +4.26 | +0.10 | +0.41 | +0.40 | +3.35 |
| **11:26 → 12:35 (the swing)** | **−8.85** | −1.07 | −1.05 | −0.24 | **−6.48** |
| 12:35 → 12:59 | +0.58 | +0.32 | −0.21 | +0.11 | +0.36 |

- **Timeline (5-min):** 11:29 open +0.61R, realised +1.54R, 6 shorts / 0 longs, beta −4.0R per +1% SPY, SPY +0.02%;
  11:49 −0.16R (PANW lots 2–3 in, 7 shorts, −5.6R/%); 12:04 −2.51R; 12:19 −2.59R after the 3 PANW stops (12:15–12:16,
  L3 −2R latch); 12:34 −3.45R (SPY +0.25%); flat at 12:55.
- **Top 5 names in the swing (−7.79R):** Palo Alto Networks `PANW` (Gap-Down Recovery Fade `L3-gap-slope-fromopen-FD`)
  −3.37R; AdaptHealth `AHCO` (same setup) −1.97R; US Foods `USFD` (Gap-Down Pop Fade, Heavy Selling
  `RW3-gapdn-rsi5pop-flowsell-short-FD`) −0.94R; ArriVent BioPharma `AVBP` (L3) −0.90R; Leidos `LDOS` (Gap-Down Pop Fade
  `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`) −0.62R. By setup: L3 −6.23R, RW3 −2.00R, RW5 −0.62R.
- **Cause:** **stock-specific, in a same-name restack** — 73% of the swing (−6.48R of −8.85R); market only −1.07R (the book
  was small: −4.7R per +1% SPY). PANW: three L3 lots 11:25 / 11:35 / 11:46 in one name, stopped together. AHCO: three
  lots on a 9¢ stop (120 bp), so single-cent ticks moved its mark ±1.97R in three successive legs; costs took 0.12R a lot.
- **What turned it:** at 12:35 → 12:48 AHCO / AVBP / PG ticked back (+3.05R on the mark); nothing structural — the L3 latch
  stopped new L3 entries (latch what-if +0.69R, nightly 6c) and the flatten ended it.
- **Lead:** **none new.** The swing type is merged into one accumulating hypothesis `swing-same-name-restack`
  (hypotheses.jsonl; 11-23 PLMR / UNH, 11-24 PTLO, 11-27 PANW). Its pre-registered test is already running:
  **L3REFIRE-1127** (7 configs, L3 only; pass bar paired day t ≥ 3.0 on CHECK and ≥ 2.0 on T2, effect reported per
  setup). The tight-cent part is STOPFLOOR-1127 (FAIL as a skip rule); its spread-floor recorder now logs every live entry
  (SPREADFLOOR-1127, log-only, test fixed at >= 20 sessions). No duplicate backtest run.
- **Forward tallies (fwd_swings.py = forward.py with all 10 accounts; l19_live.py half-day copy):** L1 no class-A NS5
  long (1 class-B +0.13R); L2 no trigger; L3 not qualifying (SPY −0.80%, IWM −0.39% at 10:00); **L6** counter-index entries
  n 142 **+0.230R** vs others n 530 −0.252R (+0.481, against L6's sign; running 14 sessions −0.290R, t −1.68); L15 n/a (no
  15:30 on a half day); L19 no trigger (5 family symbols stopped). L13 LATCH-CLOSE not re-tallied.
- **Lead count:** 34 rows in hypotheses.jsonl (17 swing L-leads + accumulating types), 0 L-leads added. Best forward lead
  still **L13** (LATCH-CLOSE; +302.7R over 7 sessions to 11-20, `1 day` 69%).

## 0 Per-account lines (11-27; research/bdi/1127/acct.py → acct_out.txt)
R = journal R after costs; $ = Alpaca day P/L (nightly). Peak = realised running peak (exit order). Day-type columns = avg
R per traded session 10-06..11-26 by SPY open→close (up / quiet / down; sessions). Today is an **up** day.

| Account | $ | Trades | Avg R | Total R (L / S) | Peak (time) | Best setup | Worst setup | Up / Quiet / Down per day |
|---|---|---|---|---|---|---|---|---|
| Primary | −$204 | 15 | −0.377 | −5.65 (0 / −5.65) | +1.54 (11:11) | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD +1.17 (3) | L3-gap-slope-fromopen-FD −5.39 (7) | −11.94 (12) / −4.70 (12) / +4.74 (13) |
| On Deck | +$17 | 18 | −0.260 | −4.68 (−0.82 / −3.86) | −1.07 (11:06) | NS5-sma50-flush-oversold-long +0.13 (1) | RW1-gapdn-bounce-flowsell-short-FD −3.29 (8) | −51.67 / −15.74 / −10.58 |
| Testing A | −$724 | 133 | −0.275 | −36.64 (−7.86 / −28.78) | +0.78 (11:35) | GEN-261026-04-ORBfailDn-…-holdtr-short +0.96 (1) | NS3V1-am-widestop-short −24.14 (85) | −31.37 / −15.21 / −31.77 |
| Testing B | +$48 | 19 | −0.004 | −0.08 (+1.15 / −1.22) | +2.07 (10:39) | LD3-st2-idxturn-t05s1-long +2.79 (7) | BEG-GNG-gap-and-go-long −2.27 (2) | −28.39 / +2.40 / +3.19 |
| Testing C | −$177 | 36 | −0.431 | −15.51 (+1.71 / −17.22) | +0.60 (10:36) | LD6-spy-dip020atr-breadthturn-spxl-holdtr-long +0.92 (1) | ST5-pdbrkup-short-mid-t05s1-FD −11.85 (20) | −29.85 / −1.17 / −19.38 |
| Testing D | +$66 | 29 | +0.129 | +3.74 (+3.74 / 0) | +4.69 (12:54) | CWT14-failbrk-orl-p10-long-WB5 +3.25 (27) | GEN-261027-10-…-holdtr-long +0.49 (2) | −0.79 / — / −3.37 |
| Testing E | −$49 | 157 | −0.059 | −9.20 (+8.58 / −17.78) | +1.38 (11:23) | ULT-05-withgap-cont-long +7.77 (119) | NS3-failed-vwap-reclaim-short −18.25 (33) | −34.12 / — / −1.64 |
| Testing F | +$1 | 37 | −0.153 | −5.65 (+1.78 / −7.43) | +4.22 (11:32) | LD5-st2-breadthup-t05s1-long +2.61 (5) | RW7-gapdn-bounce-early-short-FD −3.18 (15) | −105.70 / — / +1.25 |
| Gen | −$58 | 46 | −0.335 | −15.41 (−13.75 / −1.66) | −1.09 (11:03) | GEN-261125-04-…-hold-long −0.17 (1) | GEN-POD1022-01-thrasher-breadth-thrust-stocks-holdtr-long −8.52 (30) | −25.22 / −24.40 / −28.85 |
| Graveyard | −$36 | 182 | −0.065 | −11.82 (+19.73 / −31.55) | +5.62 (11:34) | CWT14-failbrk-orl-p05-long +18.59 (97) | heat_fade_short-FD −28.49 (30) | −41.01 / −25.12 / −84.03 |

- Non-Graveyard: 490 trades across 53 setups; Graveyard 182. All R is half-day R (flatten 12:55); 355 of 672 lots ended
  at the flatten (nightly), so most numbers are truncated holds.
- **COVERAGE gap:** Primary's up-day average is now −11.94R over 12 sessions (incl. 11-25); today added a small one.
- **Today's win:** the 09:50 big-mover ranker held up on a fresh day — K6's 09:50 top 20 contained 4 of the day's 34 big
  movers (10× chance), the "which names" half of the Move Hunt problem working out of sample; and DIPV-1127 answered the
  direction question for dip mornings with a control in one config (no). In the book, longs made +14.3R across accounts
  while shorts lost −115.2R (nightly); Testing D's Failed Opening-Range-Low Break Long WB5
  `CWT14-failbrk-orl-p10-long-WB5` +3.25R (27) and Testing E's With-the-Gap Continuation, Long `ULT-05-withgap-cont-long`
  +7.77R (119) led.

## 1 Patterns (research/bdi/patterns.csv +262 loser rows; research/bdi/1127/patterns.py → patterns_out.txt)
Accounts Primary, On Deck, Testing A–F (444 trades). Classifier unchanged (the 12:55 flatten counts as the flatten exit).
- **Late hold −56.4R (162 lots)** leads (A −31.6R: Big Loser VWAP Reclaim Fade, Morning, Wide Stop `NS3V1-am-widestop-short`), then never worked −30.6R (52), small-MFE
  then failed −22.9R (26), gave back gains −7.8R (18). The half-day flatten cut holds short (nightly
  `nightly-1127-halfday-hold-to-close` covers it).
- Primary: late hold −2.2R, never worked −2.2R, small-MFE −2.2R, gave back −1.0R.
- **Stacking:** lot 2+ 63 trades −0.206R vs lot 1 381 trades −0.159R (11-25: −0.706 vs −0.545). Primary's PANW 3 lots
  −3.34R is the day's clearest case (L3REFIRE-1127).
- Exposure: short-market positions 239 −0.349R vs long-market 205 +0.048R. Inverse / leveraged ETPs small (±1R each).

## 2 Recurring patterns → rules
- Dip-morning reversals (11-25, 11-27): long movers are early losers that turn with the index. Tested tonight as DIPV
  (fail): the turn is index-wide; in-play early losers do worse than other down names. Index-level remedy remains IDX3
  (QQQOPEN INCONCLUSIVE, no size change).
- Same-name restack: one hypothesis (`swing-same-name-restack`), tested by L3REFIRE-1127; a remedy, if it passes, is
  targeted (L3 only) and reported per setup.

## 3–4 Tested idea: DIPV-1127 Dip-Morning In-Play Reversal Long (CAPTURE + COVERAGE) — FAIL (configs 1; dipv_lab.py)
Pre-declared: SPY ≤ −0.40% from its open at 09:50 → the in-play top 20 (equal-weight ranks of range so far, |gap| / ATR,
volume ratio; adv20 ≥ $95M, ≥ $5) that are down from their open; buy the 09:50 close, stop = day low so far − 0.10 ATR
(floor 0.10 ATR), hold to 15:55; LR8 costs; control = every liquid down-from-open name at the same bar. Mechanism tag:
day type known at 09:50; falsified if no better than the control.
- 16 trigger sessions (below the 20-day bar). **A n 205 −0.236R after costs** (gross −0.104R), day t −0.78, w/o best day
  −0.458R, fit −0.745 / check +0.512, up closes +1.411 / down −0.890R, 2/10 positive months, 75% stopped. Control n 9,337
  −0.016R (up closes +1.149R). **A minus control −0.186R per trigger day (t −2.06).** 2 of 11 checks pass → FAIL.
- Lesson: on dip mornings the names that rebound are not predictable by in-play rank; in-play early losers keep falling
  more often. The rebound is the index (IDX3 lane). Backlog `bdi1127-dipv-dipmorning-inplay-reversal-long`, parked.

## 5 Decision
None. Nothing passed; no Testing suggestion.

## Weekly KPI (BDI, week 11-23..11-27; 4 sessions, Thu closed)

| Ideas tested | Passed research | Passed live |
|---|---|---|
| 6 (L18, IGR1, GAPDEF-1124, L19, VRL-1125, DIPV-1127; 16 configs) | 0 | 0 |

Educational only — not financial advice.
