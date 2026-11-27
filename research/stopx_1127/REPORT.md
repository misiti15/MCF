Educational only — not financial advice
# STOPX-1127: close-confirmed stops for Primary's 4 setups (inspector 1127 idea #2; research only, nothing changed)
Pre-registered: PREREG.md (sha256 836cd2ea…5892, committed d4883e3885 before any score). Configs: 3 (C1, C2, C3; Step 0 is measurement). Lineage ≈ 8,891 (regsteer_1126) + this week's later studies + 3; bar t ≥ 3.4 per ideas.json (4.26 at N ≈ 8,900). Locked block never read (asserted in every loader). Engine: regsteer_1126 bench10 lots for Primary's 4 re-walked on 1-min OHLC (sx_walk.py); book = primshorts booksim, Primary rules + LATCH-OPEN; LIVE-L costs on shorts, LR8 on NM-ETF. Parity: BASE reproduces every lot's exit minute (100%) and avg R exactly (CHECK −0.0728, T2 −0.0954); BASE book CHECK −2.04 / T2 −1.53 R/session = primshorts (−2.05 / −1.53).
**Verdict: FAIL — all 3 configs fail on CHECK and T2. Keep the intrabar stop.**
## Step 0: live stop slippage (11,471 cleaned stop exits, 10 journals, 10-14..11-25; sx_live.py → step0.json)
- Fill beyond the stop: mean **5.1 bp** (median 3.2, p90 13.4) = 0.045R; vs the inspector's 4 bp that is +1 bp (−0.002R/trade net). LR8's research stop-exit charge (1c + 1 bp + 2c ≈ 8.6 bp, 0.081R) covers it with room, except $100+ names (5.5 bp vs 2.6 bp charged, +0.023R short).
- Gap-down shorts 7.3 bp (0.046R); L3-fromopen 9.7 bp (123 stops), RW3 3.0, RW5 4.3, NM-ETF 3.4 (12). 11% of stops filled through a gap.
- The idea's appeal: 44% of live stop exits had their exit-minute close back on the right side of the stop. The bench shows it does not last beyond that minute.
## Step 1: paired dR/trade on the BASE book's lots (CHECK 6,605 / T2 4,421 lots), day-clustered t
| Config | CHECK dR (t) | T2 dR (t) | Setups better C / T2 | Book dR/session C / T2 | Worst-5 C / T2 (BASE −128.4 / −72.4) |
|---|---|---|---|---|---|
| C1 1-min close confirm | −0.0035 (−1.2) | −0.0035 (−1.0) | 1/4, 0/4 | −0.04 / −0.04 | −127.5 / −78.8 (9% deeper) |
| C2 C1 + 2x catastrophe | −0.0036 (−1.2) | −0.0035 (−1.0) | 1/4, 0/4 | −0.05 / −0.04 | −127.5 / −78.8 |
| C3 5-min close + 2x cat. | −0.0031 (−0.6) | +0.0027 (+0.4) | 2/4, 2/4 | −0.12 / +0.08 | −137.4 / −80.9 (7-12% deeper) |
- Per setup C1 CHECK / T2: L3 −0.006 / −0.001 · RW3 −0.005 / −0.005 · RW5 +0.001 / −0.002 · NM-ETF −0.009 (t −3.1) / −0.016. C3: L3 −0.007 / +0.021, NM-ETF −0.029 / −0.015, RW3/RW5 ≈ 0. None worse than −0.03R (the one criterion all meet). FIT (info only) is the one positive window: C1 +0.010 (t 2.0).
- Mechanism: C1 rescues only 6.4% of the 18,165 BASE stop-outs, and the confirmed exits fill at 1.085R from entry vs 1.005R for a touch stop (0.08R extra adverse move, ~2x live touch slippage); the two cancel. The 2x catastrophe stop almost never fires (27 / 73 / 483 hits in C1 / C2 / C3).
- Sensitivity, market-order costs instead of stop costs: all configs within ±0.005R (|t| ≤ 0.7) on both splits; still no edge.
## Goal metrics (book, Primary rules + LO): R/session · w/o best day · red days/21 · 20-session floor
CHECK: BASE −2.04 · −2.18 · 12.7 · −162 | C1 −2.09 · −2.22 · 13.1 · −168 | C2 −2.09 · −2.22 · 13.1 · −168 | C3 −2.17 · −2.31 · 12.9 · −179.
T2: BASE −1.53 · −1.57 · 12.4 · −87 | C1 −1.58 · −1.61 · 12.4 · −87 | C2 −1.58 · −1.61 · 12.4 · −87 | C3 −1.46 · −1.49 · 12.3 · −89.
Every arm is negative, so no best-day share applies (no positive total); C3's T2 book gain has a best-day share of 37%. BASE with LO off: CHECK −3.03, T2 −1.75.
## Caveats and rule-change context
- Bench windows use one fixed rule set. The live Step 0 window spans ledger changes 10-28 sizing, 10-29 −2R latch, 11-11 TEAM-6, 11-12 LR8/LR3, 11-17 TSZ1, 11-19 Epoch 1, 11-20 stop rounding (bears on stop fills), 11-21 cost-basis fix, 11-23 burst brake / ST7 out. 11-26 stops not in Step 0 (no exit bars yet).
- Read for the owner: stop execution is not where R leaks (live slippage ≈ 1 bp over the quote and inside LR8's charge); the edge per lot is the lever. No DECISION draft. Scripts: sx_walk.py, sx_score.py, sx_live.py; outputs step0.json, step1.json.
