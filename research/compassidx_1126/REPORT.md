Educational only — not financial advice
# COMPASSIDX-1126: trade SPY itself in the W60 compass direction (overlay / hedge). Research only; nothing changed
Pre-registered: PREREG.md (sha256 98d9397c…7a5c), frozen and committed after Step 0 on FIT, before any CHECK / T2 / live score. The owner's 11-26 request lifts the rule-26 guard. Configs: **2 counted** (CI-1, CI-2; CI-3 skipped because on FIT 10:15–11:30 is no better than the whole window). CI-2 is reported in 4 book contexts. N ≈ 8,900, bar t ≥ 4.26 (3.46 and 2.0 shown too). Locked block never read; asserted in every loader.
**Verdict: FAIL on every bar. Do not build it. No DECISION draft.** The compass tells you where the day stands at confirmation, not where SPY goes after it.
## Step 0: SPY from first confirmation to 15:55, signed by the confirmed side (info only)
| Split | Days | Mean bp | Median bp | Hit | t | Months > 0 |
|---|---|---|---|---|---|---|
| FIT (seen) | 169 | +13.1 | +6.2 | 53.3% | 1.91 | 5/8 (Mar–Apr 2025 = +36 / +65; May–Sep ≈ 0) |
| CHECK | 268 | −0.5 | +2.1 | 51.5% | −0.15 | 6/14 |
| T2 | 427 | −0.7 | −1.7 | 48.0% | −0.26 | 11/21 |
| Live 10-23..11-25 | 24 | +10.4 | −9.2 | 41.7% | 0.50 | — |
- By confirmation time, CHECK / T2 (bp): 10:00 +0.9 / −5.4 · 10:15–10:30 +1.2 / +19.1 (n 43, t 2.2) · 10:45–11:30 −2.5 / +2.9 · 11:45–13:00 −4.3 / −9.7. So the 70.4% "right side at the close" rate is the move already made by ~10:00. From confirmation on, the drift is zero. The FIT drift was the 2025 tariff spring.
## CI-1: standalone 1R/day SPY trade (session-extreme stop, cap 0.6%, floor 0.15%; exit at 15:55, the stop, or the first opposite confirmation; LIVE-L costs)
| Split | Trades | Mean R | t | Gross R | R at 1 bp cost | Months > 0 | P1 random: mean / p95 | P2 prior-day side: mean, paired t |
|---|---|---|---|---|---|---|---|---|
| FIT | 168 | −0.210 | −2.08 | +0.023 | −0.014 | 2/8 | −0.379 / −0.221 | −0.489, 1.95 |
| CHECK | 263 | **−0.252** | −3.67 | −0.029 | −0.062 | 3/14 | −0.313 / −0.181 (fails) | −0.321, 0.54 (fails) |
| T2 | 422 | **−0.240** | −3.36 | +0.002 | −0.037 | 3/21 | −0.276 / −0.159 (fails) | −0.372, 1.42 (fails) |
| Live | 24 | +0.006 | 0.02 | +0.198 | — | 1/2 | +0.094 | +0.472, −0.83 |
- Pooled CHECK+T2 t = −4.77. Stops hit 40–50% of trades, median stop 32–34 bp, and LIVE-L costs about 0.22R/trade. Even gross, or at a 1 bp cost, the result is ≈ 0. The best-day-share bar does not apply: totals are negative. Goal metrics (per session), CHECK / T2: red days 12.7 / 14.2 per 21; worst-5 −7.0 / −7.1R; 20-session floor −14.2 / −16.9R; avg w/o best day −0.26 / −0.26R.
## CI-2: compass-signed hedge on the Primary book (h = side × |net beta| only when the compass opposes the book, flat at most; 4.4 bp/side)
| Context | CHECK book → +hedge (R/day) | worst-5 | T2 book → +hedge | worst-5 | Hedge R/day CHECK / T2 (t) | Pass (≥ 20% both) |
|---|---|---|---|---|---|---|
| a live rules | −3.03 → −3.63 | −178.1 → −177.8 | −1.75 → −2.39 | −122.0 → −115.5 | −0.61 (−2.5) / −0.64 (−5.1) | no |
| b L3-OUT | −2.08 → −2.51 | −148.1 → −139.3 | −1.36 → −1.90 | −104.8 → −100.7 | −0.43 / −0.54 | no |
| c LATCH-OPEN | −2.05 → −2.52 | −128.4 → −123.3 | −1.56 → −2.07 | −79.1 → −79.4 | −0.47 / −0.52 | no |
| d L3-OUT + LATCH-OPEN | −1.26 → −1.62 | −98.1 → −92.2 | −1.18 → −1.63 | −62.9 → −63.5 | −0.36 / −0.45 | no |
- The book baselines match primshorts_1126 (a −3.03 / −1.75; b −2.08 / −1.36). Costs are 0.42–0.88R/day; the hedge is ≈ +0.28 / −0.04R/day gross. Worst-5 improves ≤ 6% (bar 20%). Red days go up 1–1.7 per 21 sessions. Context a's 20-session floor: −239 → −243 (CHECK) and −124 → −122 (T2). Per-setup R is unchanged: the hedge is a separate leg.
- Caveats and rule-change context: Bench rules are fixed; costs are LIVE-L for SPY as asked, although SPY's real cost is nearer 1 bp (A's estimate). Even at 1 bp CI-1 is ≈ 0, and CI-2 would be about breakeven, not a tail cut. CI-2's open marks use an approximate LIVE-L market cost. The live window (CI-1 only; 24 sessions, compute() backfill marks + Alpaca SIP) spans the ledger changes of 10-28 sizing, 10-29 −2R latch, 11-11 TEAM-6, 11-12 LR8/LR3, 11-17 TSZ1, 11-19 Epoch 1, 11-20 stop rounding, 11-21 cost basis, and 11-23 burst brake / ST7 out. None of them touch SPY or the compass.
- Read for the owner: the compass is a good **display** of the day's side, not a forward signal, for setups (REGSTEER) or for the index (here). The hedge question is beta, not direction: A's HEDGE-B (an always-on beta offset at ~1 bp) is the open test. Scripts: ci_lib.py, step0.py, ci1_score.py, ci2_build.py, ci2_score.py.
