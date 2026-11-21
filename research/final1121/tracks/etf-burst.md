Educational only — not financial advice.

# ETF-BURST: a burst-safe NM-ETF-late-dip-di-long (research only; no live change)

**Scope.** The owner has not yet answered ETF-BURST. This study looks for a targeted rule that keeps NM-ETF's good same-bar bursts and cuts bad ones like 11-20 (12 lots, -12.57R in Primary). A general stacking cap is not proposed; it is shown only as a reference.
- **Method.** bench10 "normal way":
  - LR8 costs.
  - Primary book: cap 30, 3 lots per symbol, -2R latch.
  - 1-minute exits.
  - Trades are the cached bench10 NM-ETF trades (top10w).
  - FIT = 2024-10 + 2025-03..09 (170 sessions).
  - T2 = 2023-01..2024-09 (427 sessions), used as a second development period.
  - CHECK = 2025-10-01..2026-11-04, scored once, for the finalists only.
  - The locked block 2024-11..2025-02 was never read (pyarrow filter and assert).
- **Configurations tried: 21** (15 C-family + 6 V-family). WB2 bar = max(1.5, sqrt(2 ln 21)) = 2.47.
- **Rule-change context.** NM-ETF moved Live Lab → Primary on 11-11 (TEAM-6). The LR8 live cost basis applies from 11-12. WB1 (Testing B) and WB4 (Testing E) copies started 11-17 and 11-18, with half-size testing lots from 11-17. ULT-22 joined Live Lab around 11-20. The Primary -2R latch has been in force since 10-29. The backtest applies today's rules throughout.

## 1. What the 2-year "burst pocket" really is
Booked Primary-rule lots in burst bars (4 or more signals in one bar):

| period | burst lots | burst R | of which April 2025 | burst R excluding April 2025 |
|---|---|---|---|---|
| FIT | 144 | +41.3 | 133 lots, +41.3R, 10 days | **+0.05R** (11 lots) |
| CHECK | 63 | **-0.81** | – | -0.81R (10 days) |
| T2 2023-24 | 47 | **-2.70** | – | -2.70R (8 days) |

- The "+0.48R on 66 trades for 8+-lot bursts" figure is the April-2025 tariff-crash week (2025-04-07..04-11). Outside it, bursts are about 0R.
- Split by index state (C1 = the burst bets against SPY's VWAP side):
  - CHECK: against-index bursts -12.7R (38 lots, 7 days); with-index bursts +11.9R.
  - T2: the reverse (+3.2 / -5.9).
  - FIT: against-index +18.4R.
- **The sign is unstable**, so an index-state switch cannot be trusted. At the 11-20 14:10 bar:
  - SPY was -1.93% from its open and -0.85% below VWAP;
  - it sat at 4% of its day range;
  - Compass read DOWN-confirmed.
  
  2025-04-08 looked the same (SPY -3.5% from open, -2.1% below VWAP, at 6% of its range) and made +5.3R.

## 2. Grid (declared before scoring; FIT and T2 dR vs base)
Base: FIT +57.78R (226 lots, t 4.35, avg R w/o best day +0.200, w/o top-2 days +0.175). T2 -9.17R. CHECK +10.71R (262 lots, t 0.82).

| cfg | FIT dR | FIT days better / worse | T2 dR | T2 days better / worse |
|---|---|---|---|---|
| C0A1 / A2 / A3 (general cap, reference) | -28.4 / -35.8 / -40.8 | 1/8, 3/9, 4/8 | -3.0 / +0.9 / +3.7 | |
| C1A1 (owner spec) | -12.8 | 1/4 | -2.5 | 1/3 |
| C1A2 / C1A3 | -16.1 / -15.9 | | -3.3 / -3.2 | |
| C2A1 / A2 / A3 | -11.9 / -15.6 / -19.5 | | -1.1 / -1.5 / -1.8 | |
| C3A1 / A2 / A3 | -2.7 / -4.7 / -7.3 | | -2.8 / -3.7 / -6.5 | |
| C4A1 / A2 / A3 | -3.9 / -4.3 / -1.7 | | -2.8 / -4.1 / -5.1 | |
| V25A1 / **V25A3** | -3.0 / **+3.8** | 0/2, **2/0** | -1.1 / **+11.6** | 1/1, **3/1** |
| V30A1 / **V30A3** | -1.0 / **+3.6** | 0/1, **1/0** | +0.3 / **+14.5** | 1/0, **3/0** |
| V35A1 / A3 | 0 / 0 | | +0.3 / +14.5 | |

**Finalists.**
- V25A3 and V30A3 are the only configurations positive on both FIT and T2.
- C1A1 was also scored on CHECK as the owner's suggested rule, for information.

## 3. CHECK (scored once)

| cfg | lots | avg R | total R | dR | days better / worse | w/o best day | w/o top-2 days | best-day share | worst day | day-clustered t | random-null p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 262 | +0.041 | +10.71 | – | – | +0.028 | +0.018 | 0.35 | -6.06 | 0.82 | – |
| **V30A3** | 252 | +0.078 | +19.57 | **+8.87** | 1/0 | +0.066 | +0.055 | 0.19 | -5.04 | 1.74 | 0.075 (1 bar) |
| V25A3 | 233 | +0.071 | +16.62 | +5.91 | 2/3 | +0.058 | +0.047 | 0.21 | -5.04 | 1.54 | 0.197 |
| C1A1 | 250 | +0.071 | +17.83 | +7.12 | 4/2 | +0.059 | +0.050 | 0.21 | -3.99 | 1.74 | – |

- Matched random-trim null on the development years (FIT+T2): V30A3 +18.1R vs a null mean of -5.5R (p < 0.002); V25A3 p = 0.003.
- **V30A3 events:** 2023-02-07, 2024-01-31, 2024-04-17, 2025-04-04 and 2026-06-17. All 5 improved, +27R in total.

## 4. Live replay 10-19..11-20 (journal LR8 cost-R; all NM-ETF-family setups)
Only 11-20 had burst bars (4 or more lots): Primary 14:10 (9 lots), WB4 14:10 (11) and 14:15 (4), ULT-22 14:10 (11).

| cfg | Primary | WB4 (Testing E) | ULT-22 (Live Lab) | setup-days better / worse |
|---|---|---|---|---|
| C1A1 / C2A1 / C4A1 | +5.18 (9 lots → 4) | +10.50 | +5.87 | 3 / 0 |
| C1A3 / C2A3 / C4A3 | +9.41 | +15.76 | +10.11 | 3 / 0 |
| C3A1 | 0 | +3.14 | 0 | 1 / 0 |
| V25 / V30 / V35 | 0 | 0 | 0 | 0 / 0 |

- The 14:15 gold-miner bar in Primary (GDXJ, NUGT, SILJ: -3.17R) has 3 lots, so no burst rule touches it.
- The latch is not re-run: on 11-20 it blocked 5 inverse-ETF lots worth +2.04R before costs, which are not added back here.

## 5. Verdict and next step
- **No rule meets all goals.** The rules that would have saved 11-20 (C1, C2, C4) cut the April-2025 crash bursts that make up the 2-year record: FIT -12 to -20R. The rule that holds up over 2 years (V30A3) does not see 11-20.
- **V30A3 is a near-miss.** It skips a burst whose index itself flushed at least 0.30 ATR against it in the last 15 minutes: an index breakdown in a calm regime, not an ETF-specific dip.
  - Evidence is thin: 5 events in 3.5 years, 1 of them in CHECK.
  - Its threshold was picked after seeing the development burst table.
  - Suggested as a forward shadow tally or backlog item. It could only run as a WB copy (PROT-29), not as a change to the Primary parent.
- **For the ETF-BURST decision.**
  - The burst pocket is one crash week; outside it, bursts are about 0R.
  - So a lot limit costs little in normal regimes. It costs a lot only in a crash-bounce week (-28 to -41R in FIT for a general cap).
  - The owner's VWAP group cap (C1A1) nets -8.2R over FIT+T2+CHECK, +21.6R on 11-20 live.
  - This is a variance-versus-crash-upside trade-off. The data does not show a free targeted fix.

## 6. Caveats
- During an early diagnostic I printed CHECK burst rows before declaring the grid (disclosed contamination). The C-family conditions came from the brief and the mechanism; the V threshold came from the FIT+T2 table.
- WB1, WB4 and ULT-22 were not backtested; they appear only in the live replay.
- The T2 universe is 469 symbols.
- In A1, "first lot per group" is chosen alphabetically, not in live signal order.

## Files
All under /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/etf-burst/:
- `base.py`, `idx.py`, `spyd.py`, `grid.py`, `check.py`: the backtest
- `replay.py`, `livetab.py`, `livefeat.py`, `live_pull.py`: the live replay
- `grid_fit_t2.csv`, `replay.csv`: results

## Robustness

null