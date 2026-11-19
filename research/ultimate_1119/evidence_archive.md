# Ultimate setup (overnight 11-19): evidence from the research archive

*Educational only — not financial advice.* This is a read of MCF's research archive only. I ran no new backtests and scored nothing (**configurations tried here: 0**). Every number below is quoted from the file named next to it, with costs in as that file states. The locked block 2024-11-01..2025-02-28 was not read. Read it as a list of parts to try and parts to avoid. It is not a list of proven parts: almost nothing in the archive clears its own try-count bar.

**Rule-change context for the quoted live figures (10-06..11-18, research/ledger.jsonl):**
- 10-20 twin block
- 10-22/23 testing latch off
- 10-27 slots 160 → 77
- 10-28 Primary ~$4k sizing
- 10-29 −2R per-setup latch + BAR90
- 11-05 ROLL1
- 11-11 TEAM-6
- 11-12 LR1-LR8 (after-cost R, live cost model); before this date, 62% of trades carry zero cost
- 11-16 ROT1 and WB window bands
- 11-17 TSZ1 half size, SPYEXIT, promotion hold
- 11-18 GY-BENCH, SRCV1
- From 11-19, C3 Epoch 1

Live R figures that straddle 11-12 mix two cost bases (WAVE1 DQ-P3). The 2-year figures follow today's rules and are not affected.

---

## 0. Six facts any design must respect

1. **The per-trade edge is close to zero after costs, and costs set the floor.** At R = 0.25 × daily ATR, a random entry in any 09:50-15:00 window loses −0.05 to −0.14R per trade at t1s1. The figure is −0.07R even for a 25-minute hold into the close. Sources: primitives/METRIC_MAP.md baselines; bdi/1118 EODREV1 (all-name baseline −0.073R). The median R is ~0.76% of price, and one hedge leg costs ~0.03R (SPY) to ~0.05R (sector) (swarm1010/w2_neutral). So **any trigger must beat about +0.08-0.10R gross over random before it nets anything.** A setup with tight stops and short holds fails on costs: swing1022 retest stops cost ~0.55R per trade, and the HF half-R setups average −0.13 to −0.16R.
2. **High frequency multiplies the edge. It does not create one** (bdi/hf1027). The 13 setups that trade 20+ times a session are 0 of 13 positive (−0.127R, −635R). Spearman(trades/session, |total R|) is +0.78. The three profitable HF setups all turn negative without their best day. A relative-value trigger fires 60-650 times a session and loses to costs every time (w2_neutral, 0/324). The owner's "high volume" has to come from **many independent, cost-cleared triggers across many names**, not from loosening one trigger.
3. **Most short "edges" are a market-direction bet.** On 2 years (history2y/rescore.csv), almost every short family makes about −0.25R on up sessions and +0.15 to +0.27R on down sessions:
   - RW1: −0.258 up / +0.257 down
   - RW3: −0.294 / +0.192
   - MF3: −0.290 / +0.148
   - heat_fade_short: −0.199 / +0.154

   Longs show the mirror image (NS5: +0.10 up / −0.20 down). With a SPY or sector hedge, the up/down gap shrinks from 0.24R to 0.02-0.04R, and **the stock-specific remainder is negative** (w2_neutral). Primary's red days are short squeezes on SPY-up days: shorts lose −0.32 to −0.49R per trade when SPY moves against them after entry (crunch/w7_primaryday). For "any market condition", the design has to neutralise or switch on direction. It cannot just pick a side.
4. **Live winners are not 2-year winners.** The best live setup, L3-gap-slope-fromopen-FD (+90R over 378 live trades, +0.19R without its best day), is **−0.048R on 2 years (4,885 trades)**. It makes +272R on bear days and −1,020R on the rest (bdi/regime1022; workbench/L3-fromopen RESULTS). RW3 and RW5 are one-day live records (best day 89% and 104% of total R) and −0.04 / −0.01R on 2 years. Of 114 live setups with ≥ 30 trades, 0 reach the try-count t (W6 X2). Treat 6 weeks of live R as a diagnosis, not as evidence.
5. **Selection noise dominates tuning.** Evidence:
   - Fit-gain vs check-gain Spearman is −0.26 overall and −0.37 for gates. The 17 chosen tunes went from +63.6R on fit to −45.3R on check (crunch/w5).
   - Condition effects keep their sign between halves only 56% of the time and shrink to 0.23x (crunch/w4).
   - Choosing a time-of-day bucket loses ~85% of its in-sample edge out of sample (bdi/timeofday).
   - Ranking by avg R per trade overfits: PBO 0.74, against 0.24 for ranking by total R (W6 X1).
   - Green-day-optimised books went from 92% green on fit to 31% on check (P3 P1).

   Conclusion: pre-register a few mechanism-led configurations, rank by total R or a shrunk avg (n/(n+150)·avg + 150/(n+150)·(−0.10), from C3-BAR2), and require a plateau.
6. **Noise model for sizing tests** (crunch/w5 A4):
   - per-trade SD 0.84R
   - same-day ICC 0.22
   - design effect 3.7 (5.0 at more than 10 trades/day)
   - detecting +0.05R takes 1,000+ unpaired sessions, or 255-320 paired trades

   Day-clustered t is mandatory.

---

## 1. Components with the strongest and most persistent evidence (ranked)

Tiers:
- **A** = persists across halves, splits or sources, or passed a pre-registered bar.
- **B** = consistent sign in 2+ sources, below the bar.
- **C** = a single source or post hoc; worth one pre-registered try.

### 1a. Market-direction alignment (the largest single factor) — Tier A as a *factor*, not yet as a gate
- **Trade with the tape, not against it.** Evidence:
  - Early (< 10:00) trades against SPY's move since the prior close: −0.321 check / −0.189 fit (n 1,395), against +0.009 / −0.272 for aligned trades. Skipping them: +376.5R, t 2.51, 32 setups better / 13 worse, best-day share 0.20 (W6 Q1/Q4). Below the 2.67 bar.
  - Shorts with SPY moving against them after entry lose −0.32 to −0.49R per trade, and win +0.24 / +0.37R with SPY (W7).
  - The 2-year up/down split in fact 3 above.
- **Caveat that persists:** the *gate* versions mostly fail. SPY-at-10:00 and VWAP-distance gates have zero setup-level persistence (W4 stability, spy10 −0.06). Day-type switches do not keep their sign (P3 P2; 0 of 67 setups positive on gap-up days in both halves). Direction tilts add ~0 (bdi/direction1020, 0/76). At 10:00-11:00 the rest of the day is only 49-52% predictable in VALID.
- **What does survive as a part:** the **SPY-since-09:50 skip on short fades.** It was kept in the Workbench combos for RW3 (skip SPY > +0.20%), RW5 (+0.20/0.30%), RW1 (+0.20%), RW7 (+0.10% plus SPY last 30 min ≤ +0.20%) and ST7 (long side mirror, skip SPY > +0.10%) (PARTS_CATALOGUE). This is a *within-day, point-in-time* tape filter, not a day-type forecast. It has not been validated out of sample (W5 warns on per-setup picks). It is the best-supported way to stop up-day squeezes.
- **Design implication:** make the side **conditional on the live tape at entry** (short fades only while SPY since 09:50 ≤ ~+0.1-0.2%; long dips only while SPY is not making new lows / has not fallen > 1% in the last hour), **or** hedge with an index leg. The hedge leg costs ~0.03R and showed the stock-specific part to be negative for existing lists, so use it only if the stock leg's residual is positive.

### 1b. Gap relation (trade *with* a big gap, fade only a recovering gap-down) — Tier A/B
- Gap is one of the three conditions that **persist best** across halves (W4 persistence: tod 0.49, **gap 0.44**, **fromOpen 0.39**, atr_pct 0.36).
- Trading **with** a ≥ 2% gap: −0.058 fit / **+0.008** check over 4,362 trades. No gap: −0.123 / −0.149. **Fading** the gap: −0.157 / −0.187. In Primary, with-gap is +0.065 / +0.120 and fade is **−0.376 / −0.596** (W6 P1, post hoc).
- Gap mechanisms: −0.008R per trade against −0.140R for the rest, and 7 of 20 robust against 4 of 115 (P3 C3-MECH).
- MF-family shorts fading a ≥ 2% gap-up: −0.558R (127 trades), negative in every gap bucket; skipping them gives +70.9R, t 2.14, 9 setups better / 1 worse (W6 MF).
- Gap-down + recovery-from-open short (L3: gap ≤ −2.66%, fromOpen > +3.46%, SMA20 slope up) is the only setup positive in **both** live and replay. It is negative on 2 years outside bear days, and its live edge carried forward (+0.18 → +0.32R).
- **Part to use:** gap ≤ −2.5% to −3% names as the short universe for rallies into resistance; gap ≥ +2% names never shorted by a fade; gap-and-go *with* the gap on earnings reaction days (1e).

### 1c. Distance from open / from the day's low or high, in ATRs — Tier B
- fromOpen persists (0.39). L3-lowdist (distance from the low of day > 0.78 → 0.82 daily ATR) passed WB, and the 75-min hold transfers to it.
- GEN-261026-03: close vs prior close ≤ −1.3 daily ATR passed WB1.
- Measuring a move in **daily-ATR units** (ret3_atr, from_pc_atr, dist_lod_atr) beats raw % (GEN-261023-09 WB2: "pop measured in daily ATRs, not % ").
- **Part to use:** extension triggers expressed in daily ATR: an overbought short when the price is ≥ X ATR above the open / VWAP after a gap-down, and an oversold long when it is ≥ X ATR below the open with the tape stabilising.

### 1d. Time of day — Tier B for broad blocks, Tier F for narrow windows
- Persists best of all conditions (0.49). But narrow per-setup windows are ~85% selection (bdi/timeofday), and 30-min cells flip (winning_periods: heat_fade_long 12:00 +0.49R train → −0.30R valid).
- **Broad blocks with support:**
  - 10:30-13:00 carries the current five's edge (+58.2R). Entries ≥ 13:00 are −18.0R over 103 trades (W7, descriptive).
  - Window **end 13:00** passed WB for L3-fromopen, RW1 and RW7 (the leak is the window end).
  - Window **start 10:15-10:30** passed for RW3, RW5 and CWT14. RW6G1's start 11:00 passed.
  - Opening entries (09:35-09:45) all lose after costs at 1x, and every one at 2-3x opening spreads (bdi/timeofday §3).
  - The morning low most often sits right at 09:50 (trend from the first 20 min continues). No 10:00-11:00 window holds the low more than chance (morning_low_1116).
  - Late turns at **10:55-11:25** were the only positive index cells: SPY +15 bps at +90 min, t 3.1, both halves t ≥ 2.1. As SPXL that is +0.27R (n 37), below the 3.76 bar and post hoc.
  - Late-day ETF dips (14:00-15:00) are positive on 2 years (1g).
  - Live vs 2 years **disagree** on 14:00+ for L3 (2y +0.142R best, live −0.25R).
- **Part to use:** entries 10:15-13:00 as the core window, plus a separate 14:00-15:00 dip-buy lane. Never pick narrow windows per setup. Respect the owner's 09:50 floor. The 40-bar warm-up parity defect means the SMA50 is NaN live until 10:20 (bdi/timeofday), so do not rely on SMA50 before 10:25.

### 1e. Earnings reaction day (gap-and-go) — Tier B/C, highest per-trade number in the archive
- EARN-GO: +0.346R per trade, n 121, t 3.63, +0.241 without its best day, best-day share 35%. **The earlier half is only +0.045R**, and it is +0.145R without 11-05 and 11-09 (P3 P6).
- 58% of top moves are in earnings-blackout names (P6). bdi/earnings: after-hours reaction continuation, +0.68% net per trade, t 2.77, n 890, fails only the try-count bar (3.34).
- Conflict: BLKOUT (report-day BMO −0.064R, t −3.57). RT-EARN asks for a 2-year earnings-season test first.
- **Part to use:** a *with-the-gap* continuation on earnings reaction days, entries ≥ 09:50. It needs the blackout exception and a 2-year test. It is the strongest "big move" source by far.

### 1f. Down-day / bear-tape short fades of gap-down rallies — Tier B (regime specialist)
- L3-fromopen +272R on bear days over 2 years; the RW family is +0.19 to +0.27R on down sessions (rescore). NS3 failed-VWAP-reclaim is +0.24R down (2y +0.056R, unseen +0.096, WF 0.71). Big Loser VWAP Reclaim Fade is +375R on bear days.
- The loss is all on up and flat days. **The best at-entry regime call (SPY ≥ +0.5% from the open at 11:00) is right 70-82% of the time when it fires, but cannot gate well enough** (regime1022).
- **Part to use:** short fades switched on by an intraday tape state (SPY since 09:50 ≤ 0, or SPY below its open at entry). Score them as a regime specialist with a long counterpart for the other tape.

### 1g. Late-day volatile-ETF dip buy with directional strength — Tier B (only long positive on 2 years)
- NM-ETF-late-dip-di-long: 14:00-15:00, 15-min dip ≤ −0.80%, +DI(7) ≥ −DI(7), daily ATR ≥ 3.6%, ETF list, t05s1. Results: 2y **+0.117R** (65.6R), replay +0.330R, live +0.311R over 21 trades (+0.281R without best day, 22% share). It is positive across live, replay and 2 years.
- WB4 (dip ≤ −0.75, DI ≥ −5, **falling-hour guard ret12 ≥ −1.0%**, refire on): 2y +0.130R, 1.92 trades/session, total R +65%, on a plateau (every one-step neighbour passes, 17 of 113 configs).
- Caveats: April 2025 rebound clusters are the profit (a cluster cap cut total R 65.6 → 36-43). Adding more tickers dilutes it (universe widening fails every time).
- **Part to use:** a "dip-in-a-strong-tape" trigger plus a falling-hour guard; the leveraged-ETF list; t05s1 geometry. It is a real but low-frequency lane.

### 1h. Stops — Tier A (keep it simple)
- **Per-trade stop width: keep k = 1.0 × the setup's 1R (0.25 × daily ATR).** Tighter (0.75/0.9) is worse for 98 and 90 of 117 setups. Wider looks better only through size; the stop effect itself is +0.003R (stoplab B). The L3 k = 1.5 lead failed without its best day.
- The 1R in daily-ATR units with an **ATR floor** helps where cost per R is high: daily ATR ≥ 1.6%, 1R ≥ 0.40% of price (kept for RW3 and RW1); CWT14 stop 1.0 → 1.5 × 1R kept in WB5; CWT14-pdl stop 0.25 → 0.45 ATR kept.
- **The cost-to-R prefilter persists as a part:** stop-exit cost / 1R ≤ 0.05-0.15 (kept for L3-rsi5hi, RW5, CWT14). Execution filters as a whole saved ~1,300R, and spread filters ~4,100R net of spread (P7). **Never drop the spread or cost filters.**

### 1i. Exits — Tier A for "don't exit earlier", Tier B for "75-min time cap" and LATCH-CLOSE
- **Earlier exits hurt.** Target 0.75x −0.030R (5/5 worse), break-even after +0.5R −0.027R, 60-min stop if MFE < 0.25R −0.025R (5/5 worse), all on gap-down short fades (crunch/w5, 1,549 paired trades).
  - exits/EXIT_STUDY (489 configs): keep the current exits on all five; stalled-trade time stops cut the late drift.
  - stoplab C: time stops lose on winning setups (13 better / 37 worse); break-even after +0.5R hurts.
  - winning_periods: 11 of 12 time stops negative; the median time to MFE is 52-56 min (19 min for heat_fade_short).
  - Profit locks and giveback stops all lower P/L (winning_periods, P2 W3; red days never went green first).
- **Wider targets mostly fail too** (hf1027: coil 0.5 → 1R worse, t −2.4 to −4.1; exhaustion 1.25-2R carried by one day).
  - So **t1s1 (or t05s1 for dip buys) at R = 0.25 ATR is the robust default.**
  - The exception under test is WB2-NEXT: target 1.25x and trail after +1R on the gap-down family.
- **Max hold 75 min** (the lot is closed 75 min after entry) passed on L3-fromopen (replay +0.173R) and **transferred to L3-lowdist**. It did not transfer to the 0.5R-target sibling L3-rsi5hi.
  - This matches the owner's 5-45 min sketch: most of the move resolves inside ~75 min (heat_fade_short median target 26 min).
  - A fixed clock cap is OK. A conditional "exit if not working" is not.
- **LATCH-CLOSE** (when a setup's −2R daily latch fires, close its open lots at the next 5-min close): **PASSED a pre-registered 2-year test.**
  - TRAIN +3,241R (t 6.33), VALID +1,684R (t 3.89, +1,557R without best day), 7 of 9 families better (bdi/1111).
  - LATE is +169.5R but t 0.98. It is in forward shadow.
  - This is the only exit/risk part in the archive that passed its bar.
- **L15 EOD-loser short cover** (at 15:30, close shorts in names ≤ −2% from the open): VALID +534.7R (t 1.42), 8/0 families, LATE +80.9R; TRAIN −200R. A near miss, in shadow from 11-19. Its mirror has no effect.
- **Flat by 15:55** (system default); a time exit of 15:00 passed for L3-fromopen and RW3.

### 1j. Risk / caps — Tier A for the −2R per-setup latch plateau
- Daily stop −1.25 to −2.01R is one flat plateau; looser is worse; per-setup levels fail 0/111 (stoplab A).
- Keep −2R plus LATCH-CLOSE.
- Gap-down shorts with the latch off: +47R, t 2.14. Thin (4 days, 58% from 10-22), shadow only.

### 1k. Universe / intake — Tier B
- **Price < $20 is a cost drag on 2 years** in several shorts (CWT09 −0.846R; skipping keeps 80% of trades and 99% of the top decile). Live does not confirm it. **ADV ≥ $100-150M** helped GEN-261027-01, MF2 and RW6G1.
- Easy-to-borrow only: 56-60% of L3 shorts are ETB-blocked live (P3), so the backtest **must** use an ETB universe or it overstates frequency.
- Top-10 by 09:30-09:49 rvol plus price ≥ $20 passed for orb20_a.
- The earnings blackout removes 58% of top moves (1e).
- Widening the universe dilutes the edge (NM-ETF FREQ, "more tickers dilute").

### 1l. Entry-quality sensors that passed the Workbench (per-setup; Tier C, W5 warns these are mostly noise)
- Signal-bar close below the day open plus a 5-min close above VWAP on the bounce (CWT09)
- RSI(14) band narrowed 55-65 → 55-60 (RW1)
- RSI(5) cap ≤ 90 and SMA20-slope cap ≤ 1.0 (L3-rsi5hi: do not short the steepest, most extreme bars)
- Reclaim-bar volume ≥ 0.45 × the 20-bar average (NM-RWN5)
- ADX(7) ≥ 44 (GEN-261023-09)
- Reclaim close ≥ VWAP + 0.5 SD (RW6G1)
- Breadth-rise skip (GEN-261027-01)

Use them only as **pre-registered mechanism classes** (W5 A2: pooling a fixed class cuts the damage by two thirds). Do not tune them per setup.

### 1m. Index lanes (SPXL/TQQQ) — Tier C
- Big first-hour drop day, long a 3x index ETF with an ATR stop: +0.06 to +0.26R in both halves. But **random entries on the same days earn the same**: the day type carries it, the trigger adds nothing (drop_rebound_1116).
- Index dip-bounce triggers do not beat random times on dip days, and 0 of 104 are positive in down sessions (longs1020).
- Late morning-low turn at 11:20: see 1d.
- Low frequency; better treated as a day-type overlay than as a setup.

### 1n. Daily-horizon anomalies (outside intraday scope, for context)
- Connors RSI(3) < 5 above SMA200: +65-78 bps net, t 5.07 (w3_daily).
- 5-day loser reversal: +164-245 bps.

Both are multi-day holds and partly market drift. They are **not intraday**. They show only that mean reversion of 5-day losers is the one reversal effect that clears costs, when holds are long enough to dwarf costs.

---

## 2. Proven NOT to work (the design should avoid these)

| Component | Evidence | Source |
|---|---|---|
| High trade count from one loose trigger | 0/13 of 20+/session setups positive; RV triggers 0/324 | bdi/hf1027, swarm1010/w2 |
| Tight stops / short holds where cost > ~0.1R | retest stops cost ~0.55R; HF half-R −0.13..−0.16R; tighter k worse for 98/117 | swing1022, hf1027, stoplab B |
| Fading opening gaps (esp. gap-ups ≥ 2%) | fade −0.157/−0.187 vs with-gap +0.008; Primary fade −0.376/−0.596; MF gap-up fades −0.558 | W6 P1/MF |
| Opening-period entries (09:35-09:45) | all 30 configs negative at 1x, −0.09..−0.33R at 2-3x | bdi/timeofday |
| Narrow per-setup time windows | ~85% selection, out of sample +0.015R | bdi/timeofday, winning_periods |
| Day-type switches / SPY-at-10:00 gates / direction tilts / compass gates | 0/67 setups positive on gap-up days in both halves; spy10 persistence −0.06; 0/76 tilt policies | P3 P2, W4, direction1020, regime1022 |
| Per-setup bespoke condition filters from short samples | 0/31 pass; 8 made their setup worse (−58.2R); excess +31.8R vs +550R promised | crunch/w4 |
| Earlier exits on fades (0.75x target, BE +0.5R, MFE time stop) | −0.025..−0.030R, 14/15 pairs worse | crunch/w5 |
| Profit locks, give-back stops, equity-curve gating, conditional time stops | all lower R; red days never green first | winning_periods, P2 W3/W5/W6, stoplab C |
| Wider targets (beyond 1R) as a blanket change | coil t −2.4..−4.1; exhaustion one-day | hf1027, EXIT_STUDY |
| Volatility-managed sizing, tier weighting, daily trade caps, cross-setup caps | X6 Sharpe fell both halves; check −33..−47R; caps cost L3 −2.8..−31.6R | W6, P8, W7 |
| Burst / cluster caps and pacing | ≈ 0 vs own average (t −0.16..−0.34); clusters are the profit days | bdi/burst1, NM-ETF cluster cap |
| Hedged / relative-value single-name trades | stock-specific remainder negative; 0/530 | swarm1010/w2 |
| Confirmation triggers on index dips (VWAP reclaim, higher low, rec20) | no better than random time on the same days | longs1020, drop_rebound_1116 |
| Buying the 10:25 morning low | turn returns ≈ same-minute null; 10:25 window below null | morning_low_1116 |
| End-of-day reversal *entry* (losers at 15:30) | −0.041R, t −5.24 (reversal real, +0.031R vs baseline, eaten by costs) | bdi/1118 EODREV1 |
| Late-day SPY-momentum alignment (≥ 15:00) | reverse held (aligned −0.219) | W6 X5 |
| Squeeze filter, gap-fade-by-liquidity | failed | W6 |
| Undirected generator output | GEN 89 setups −776R live; Guild 0/78; Reddit 0/26; Top-5 Part B 0/378 | P3 |
| CWT12/CWT14 variants and top-5 execution tunes | 10,807 trades −1,418R; ~12.4M configs, 0 live winners | P3 |
| Automatic −FD (full-day) copies | −294R over 14 pairs | P3 P4 |
| Treating replay / 2-year "meets parent" as a pass; 30-trade live records | rank corr ~0; next-30 Spearman 0.03; early kill backfired 10/10 | P3 P5, W5 A3 |
| Latency / limit-entry / streaming projects | latency ~0; passive fills pick the −0.22R trades | P7 |

---

## 3. What this implies for the "ultimate setup" (design brief from the archive)

1. **Volume must come from a family of independent, cost-cleared triggers across ~1,200-3,000 ETB names, long and short**, each with R = 0.25 × daily ATR (with an ATR floor ≥ ~1.6% so that cost per R ≤ 0.10-0.15), not from one loosened trigger. A target like "5-15 trades a session at ≥ +0.08R net" is realistic. "50+ a session" has never been positive.
2. **Direction-aware by construction.** Short only in a non-rising tape (SPY since 09:50 ≤ ~+0.1-0.2% at entry, plus SPY last 30 min not up > 0.2%); long dips only when the falling-hour guard holds (ret12 ≥ −1%) and the index is not breaking lower. Each side should be a regime specialist, and the pair together covers "any market condition". The point-in-time tape filter is the part that worked; forecasting the day type is the part that failed.
3. **Signal content that persists:**
   - gap (sign and size, ≥ 2-3%)
   - distance from open / LOD / prior close in daily ATRs
   - broad time block (10:15-13:00 core; 14:00-15:00 dip lane)
   - earnings reaction day

   Fade only *recoveries of gap-downs* (L3 mechanism) and extended moves in ATR units. Never fade gap-ups ≥ 2%. Trade *with* big gaps.
4. **Exits:**
   - fixed bracket t1s1 (t05s1 for dip buys)
   - a hard clock cap of ~60-75 min (fits the owner's 5-45 min, with room for MFE at 52-56 min)
   - flat 15:50-15:55
   - LATCH-CLOSE at the −2R per-setup latch
   - L15 (cover shorts in ≥ −2% losers at 15:30) as an option

   No break-even, no early time stop, no giveback lock, no tighter stop.
5. **Validation protocol:**
   - 2-year TRAIN (to 2025-12) / VALID (2026) plus the live-quote replay; costs in (LR8: 1c + 1 bp per side, +2c on stops, time-of-day/extended multipliers)
   - ETB universe; positive in up AND down sessions *and* in both halves
   - avg R without best day > 0, best-day share < 50%; not carried by April 2025 (report ex-April 2025)
   - plateau on one-step neighbours; day-clustered t against max(1.5, √(2 ln N)) with N counted over the lineage
   - beat a same-day random-entry control (the drop-rebound lesson)
   - rank finalists by total R or shrunk avg, not raw avg R
6. **Expect a near miss.** Across ~1.3M+ configurations in the archive (swarm1017 1,054,906; P3 153,401; primitives 12,030; Wave 1 2,287 ...), **nothing intraday has cleared its try-count bar on 2 years except LATCH-CLOSE, an exit/risk rule.** So the honest goal for tonight is several *pre-registered, mechanism-led* candidates that are positive in both halves and both tape types, sent to Testing as candidates, not as proven edges.

### Candidate archetypes grounded in the evidence (for the swarm to build and score)
1. **Gap-down recovery fade, tape-gated:** L3 mechanism (gap ≤ −2.66%, fromOpen ≥ +3.5% or ≥ X ATR, SMA20 slope up, RSI(5) ≤ 90 cap), entries 10:15-13:00, skip while SPY since 09:50 > +0.15%, t1s1, 75-min cap. Evidence: 1b, 1c, 1d, 1f, 1i.
2. **Gap-down pop fade (RW3/RW5 class) with SPY-since-09:50 ≤ +0.20%, start 10:15, ATR floor 1.6%, cost/R ≤ 0.15.** Evidence: WB3 combos. On 2 years the parents are negative overall but +0.19 to +0.27R on down sessions.
3. **Late-day volatile-ETF dip buy WB4** (falling-hour guard, refire), 14:00-15:00, t05s1. This is the only long positive on 2 years. Evidence: 1g.
4. **Earnings reaction-day continuation (EARN-GO)**, with the gap, ≥ 09:50, ATR-based stop, 60-75 min cap. Highest per-trade figure; needs the blackout exception and a 2-year earnings-season test. Evidence: 1e.
5. **With-the-gap continuation (non-earnings) for ≥ 2% gaps**, long on gap-ups / short on gap-downs, 10:15-13:00, entered on the first pullback that holds VWAP. Evidence: W6 P1 (with-gap +0.008 check, Primary +0.12). The weakest edge, but it has the right sign in both halves, so it is a good base layer for the tape gate.
6. **Failed-VWAP-reclaim short (NS3/RW4) + SMA100 layer, down-tape gated.** Evidence: 2y +0.056R, unseen +0.096, WF 0.71; swarm1010 w1 passers +0.139R (t 2.53, below 4.22); +0.24R on down sessions.
7. **Late morning turn long (10:55-11:25 reclaim after a new 09:50+ low)** on liquid names / 3x index, +90-min exit. Evidence: morning_low_1116 (t 3.1 on SPY, both halves t ≥ 2.1, post hoc).
8. **Oversold-in-ATR long mirror of #1:** gap-up name sold ≥ X ATR below its open, slope turning up, long only while the tape holds (ST7 SPY gate mirror). It completes the "any market" pair. Only weak evidence (ST4/NS5 up-day positives), so treat it as exploratory.

Exit and risk set for all eight: t1s1 (t05s1 for dip buys), 75-min cap, flat 15:55, −2R latch + LATCH-CLOSE, spread/cost filters on, ETB universe, earnings blackout except #4.

---

## 4. Sources read
- research/crunch/WAVE1.md and w1-w8 RESULTS
- research/consultant_p2/RESULTS.md, research/consultant_p3/RESULTS.md
- research/bdi/top20/CONDITIONS.md
- research/bdi/{hf1027, htf1028, timeofday, direction1020, regime1022, longs1020, swing1022, burst1, filters1017, earnings, gates1021, 1111, 1117, 1118}/NOTES.md
- research/workbench/PARTS_CATALOGUE.md (evidence log, all rows); workbench L3-fromopen and NM-ETF blueprints/RESULTS, NM-ETF FREQ
- research/exits/EXIT_STUDY.md
- research/stoplab/NOTES.md
- research/swarm1010/w1-w4 NOTES
- research/swarm1017/SUMMARY.md
- research/primitives/primitives/{NOTES, METRIC_MAP}.md, primitives/holdout/results.json, primitives/winning_periods/NOTES.md
- research/drop_rebound_1116/NOTES.md, research/morning_low_1116/NOTES.md
- research/history2y/rescore.csv
- research/l3_bespoke_1117/BESPOKE_RULES.md
- research/generator (registry and runs, structure only)

Educational only — not financial advice.
