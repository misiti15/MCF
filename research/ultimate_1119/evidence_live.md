Educational only — not financial advice.

# Ultimate setup — live evidence miner (consultant, 2026-11-19 overnight)

**Source.** Every closed *paper* (real broker fill) trade in the ten account journals on the `mcf-data*` branches as of 2026-11-18 close (primary, testing, testing2, testingd/e/f, graveyard, explore1, livelab, gen). Not what-if, not shadow. 27,052 trades → **26,944 after dedupe** (WB copies and the same setup in two accounts on the same symbol/minute counted once). 2026-10-06 .. 2026-11-18, 32 sessions, 219 setups. `data/journal.db` in the repo is empty, so the branch journals were used.

**Cost basis.** R after costs on ONE basis: `mcf.costs.with_cost_r` (LR8 re-costing of pre-11-12 rows, DQ-P3). Mean cost 0.060R/trade before 11-12, 0.044R after.

**Point-in-time features.** For each trade, 1-minute SIP bars (Alpaca, split-adjusted) for that day, using only bars that had closed at the live `signal_time`, plus daily bars from earlier sessions: gap %, gap/ATR, distance from open/VWAP/prior close in ATR(14), RSI(5) on 5-min closes, RSI(5) 1-min, cumulative and 15-min relative volume (vs the 20-day average), ATR%, price, 20-day ADV, distance to SMA20, 5-day return, position in the day's range, 15/30-min momentum, SPY from open/gap/30-min/VWAP, ETF flag (by name in universe.csv). Hold time and exit reason are outcomes and are shown only to describe what happened.

**Halves.** H1 = 10-06..10-27 (8,831 trades), H2 = 10-28..11-18 (18,113). "w/o best" = avg R with the best session dropped.

**Number of configurations looked at: ~230** (26 single-attribute tables, ~170 buckets; 31 hand-picked cells; ~30 drill-down cuts). All of it is post hoc on one 32-session record. Wave 1 measured a shrink of about 0.23x for condition effects between halves, so **every number below is an upper bound**. Divide the edges by about 3-4 before planning on them.

**Rule changes inside the window** (ledger): 10-12 Testing full-day versions; 10-13/14 per-lot stacking and refire; 10-15/10-20/10-21 promotions and demotions, plus the Graveyard account; 10-20 twin cap and −2R per-setup loss limit; 10-28 Primary sizing ~$4k; 10-29 −2R latch + BAR90; 11-05 ROLL1 (Explore 1 / Live Lab); 11-11 TEAM-6; **11-12 LR1/LR3/LR7 + LR8 cost model + Testing D/E/F start (also the biggest single session in the record)**; 11-16 ROT1; 11-17 TSZ1 half size + 15 WB copies; 11-18 GY-BENCH. Sizing changes do not affect R. The 11-12 session is called out wherever it carries a result.

---

## 1. The baseline is negative everywhere

All live trades: **−0.150R/trade** (H1 −0.156, H2 −0.147), win rate 52%. Every account is negative. Only **10 of 139 setups with ≥ 20 trades** have positive avg R without their best day, and only 6 are positive in both halves. Longs average −0.160 and shorts −0.137. **No single attribute bucket for longs is positive in both halves.**

## 2. Attributes that separate good from bad trades and keep their sign in both halves

| Attribute | Good side | Bad side | Persistence |
|---|---|---|---|
| **Stop width (cost structure)** | stop ≥ 150 bps: −0.077 (cost 0.027R) · top octile ≥ 243 bps: −0.042 | stop < 60 bps: **−0.259** (cost 0.113R); stop < 0.22 ATR: −0.287 | monotone, both halves; strongest and most mechanical finding |
| **ATR%** | ≥ 7.8%: −0.072; ≥ 5%: −0.090 | < 2.3%: **−0.221** (day-t −5.3) | monotone, both halves |
| **Time of day (all)** | 11:00-11:30 −0.066; **14:30-15:00 −0.007** (H2 +0.019) | 09:50-10:30: −0.207 (both halves ≤ −0.15) | persists (agrees with Wave 1) |
| **Shorts: gap** | gap −3..−1.5%: **+0.084** (H1 +0.163, H2 +0.040); −6..−3%: −0.006 | **gap-up ≥ +0.5%: −0.274** (H1 −0.260, H2 −0.281, day-t −3.3, 75 setups) | both halves; dropping gap-up shorts improves 14 of 20 short families |
| **Shorts: trend (SMA20 / 5-day)** | below SMA20 by > 5%: −0.05; 5-day return < −2.6%: −0.04 to −0.09 | near SMA20 (±1.5%): −0.284 | both halves |
| **Shorts: RSI(5)** | 75-85: −0.023 (H2 +0.026) | **< 15: −0.530**; < 25: −0.353 (shorting an already oversold name) | both halves for < 25 |
| **Longs: SPY state** | SPY up ≥ +0.3%: −0.11 | SPY −0.3..−0.75% from open: **−0.304** (both halves) | both halves |
| **Longs: RSI(5)** | 50-65: −0.127 | < 15: −0.235/−0.276 (buying the knife) | both halves |
| **15-min relative volume** | low (< 0.7x): −0.12 | top sextile (> 1.36x): −0.193 | both halves; chasing volume bursts loses |
| **Position in range vs side** | entering away from the extreme | long near day high / short near day low: −0.20 | H2 only (H1 opposite): **not robust** |
| VWAP / open distance, 30-min momentum, price, ADV, ETF flag | small differences (≤ 0.08R), signs flip between halves | — | **not robust; do not build on these** |

The stop-width finding matters most for the design. A large part of the losses is mechanical: the LR8 costs (4 bps on stops, 1 bp on entry and market exits, fees) are fixed per share, so tight stops in low-ATR names turn them into 0.10-0.14R per trade. Raw R is also worse in that bucket (−0.17 vs −0.02). **The ultimate setup should keep stop ≥ ~120-150 bps and ATR% ≥ ~3%.**

## 3. The one cross-setup "live edge" pocket: fade the gap-down bounce, late morning

**Cell A, defined on live attributes: short, gap ≤ −1.5%, RSI(5, 5-min) ≥ 60, entry ≥ 11:00 ET**

| | n | setups | avg R | w/o best day | best-day share | H1 | H2 | without 11-12 | day-t |
|---|---|---|---|---|---|---|---|---|---|
| Cell A (≥ 11:00) | 1,647 | 53 | **+0.137** | +0.052 | 69% | +0.071 | +0.174 | +0.052 | 1.0 |
| A, 11:00-13:00 | 1,103 | 35 | +0.231 | **+0.125** | 59% | +0.098 | +0.321 | +0.125 | 1.3 |
| A, 11:00-13:00, RSI < 90 | 1,031 | 35 | +0.264 | +0.163 | 54% | +0.165 | +0.324 | +0.163 | 1.45 |
| Same rule **before 11:00** | 525 | 41 | **−0.203** | −0.262 | — | −0.323 | −0.125 | | −1.0 |
| Same setups, trades **outside** cell A | 7,168 | 53 | −0.148 | | | | | | |

- **Broad, not one setup.** 68% of the 31 setups with ≥ 10 trades in the cell are positive in it. Without the L3/RW3/RW5 families the cell is still +0.100 (n 1,148). The mean of per-setup averages is +0.09. Contributors include L3-fromopen +0.267 (185), heat_fade_short-FD +0.217 (129), RW6-ns2-up3 +0.189 (108), NS2-FD +0.142 (135), RW3 +0.509 (49), L3-lowdist +0.252 (71), RW7 +0.088 (111). The same setups outside the cell average −0.148, so **the edge belongs to the condition, not to the setups.**
- **Works in both SPY directions.** SPY ≤ −0.3% from open: +0.170. SPY ≥ +0.3%: +0.218. Flat SPY (−0.3..+0.3): about 0.
- **Time of day is the sharp knob:** 11:00-12:00 +0.274, 12:00-13:00 +0.129, 13:00-14:00 −0.111, 14:00-15:00 +0.024. Shorts are negative before 11:00 in every version tried.
- **Caveats.** The 11-12 session (LR8 / Testing D-F start day) carries 155R of the cell's 226R. Daily t is only 1.0-1.45. Weeks: 6 of 7 positive (week 42 −78R). Green days: 55%. RSI ≥ 90 is negative (−0.29, n 100). The 11-13 and RSI < 90 cuts were found by looking, so expect them to shrink toward the plain ≥ 11:00 cell. Planning number: **+0.03 to +0.05R/trade, about 30-50 trades/day across the book.**
- Exits in the cell: target +0.85 (670), stop −1.10 (341), flatten +0.05 (633; median hold of flattened trades 225 min). The t1s1-style geometry with an EOD flatten works here. The owner's 5-45 min hold is the *target* hit time (median 33 min across all target exits).

**Mirror longs do not work:** gap-up names dipping (gap ≥ +1.5%, RSI ≤ 40, ≥ 11:00) −0.133; gap-down dip-buys −0.010; uptrend dips −0.09 (H1 +0.10, H2 −0.16). **The live record shows no long edge.** Late-day longs (≥ 14:30) are the least bad (−0.017, w/o best −0.091).

## 4. Families and setups with positive avg R w/o best day (≥ 20 trades)

| Setup | n | avg | w/o best | best share | H1 / H2 | Why it works (attributes) |
|---|---|---|---|---|---|---|
| L3-gap-slope-fromopen-FD | 397 | +0.204 | **+0.156** | 39% | +0.115 / +0.294 | short; gap ≤ −2.66%, SMA20 rising, up > 3.46% from open = the gap-down bounce fade (cell A core). Best of all: both halves, low best-day share |
| NM-ETF-late-dip-di-long | 30 | +0.248 | +0.235 | 18% | +0.40 / +0.22 | only long with a clean record; ETF, late-day dip; small n |
| GEN-261026-03 NewLOD lunch short | 25 | +0.423 | +0.259 | 56% | +0.62 / +0.27 | lunch-window short at a new low of day; small n |
| CWT09-gapdn-vwaploss-g10-short | 24 | +0.218 | +0.141 | 49% | small n | gap-down, below VWAP, short |
| L3-gap-slope-lowdist-FD | 109 | +0.231 | +0.091 | 72% | +0.04 / +0.38 | L3 family; one-big-day dependent |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 199 | +0.139 | +0.025 | **85% (1 day)** | +0.41 / **−0.05** | gap-down RSI pop short; edge only ≥ 11:00 (in cell A +0.51); before 11:00 it gives it back |
| RW5-heat30-...-gapdn-short-FD | 206 | +0.110 | +0.022 | **83% (1 day)** | +0.34 / **−0.08** | same pattern as RW3 |
| GEN-261027-08 ORBfailDn lunch short | 78 | +0.094 | +0.008 | 93% | 6 days only | lunch-window short |
| L3-gap-slope-rsi5hi-FD | 158 | +0.089 | +0.007 | 94% | +0.10 / +0.08 | L3; one-day record |
| ST7-rsi50dn-long-pm-t1s1-FD | 50 | +0.081 | +0.002 | 98% | | one-day record |

Family totals: L3 +119R (685 tr, w/o best +0.101, both halves +). RW3 +26R and RW5 +26R are one-day records that are negative in H2. RW7 is about 0 (−0.008, 831 tr). Everything else is negative. The largest drains are CWT14 (−1,529R over 9,739 tr: failed-breakout longs on tight stops), GEN (−931R), CWT12 (−225R), heat_fade_short (−216R overall but **+0.217 inside cell A**), heat_fade_long (−167R) and the MF family (−320R; MF2/MF4/MF5 gap-up shorts −0.36 to −0.72).

**Why the winners work, in common terms:** all are **shorts on gap-down names that have bounced** (RSI pop, up from the open, rising short-term slope), mostly entered **after the first hour**, with wide stops (high-ATR names). That is the same thing Wave 1 found persists: gap, distance from open and time of day.

## 5. Implications for the ultimate setup (for the Mechanic / backtest stage)

1. **Core candidate U1: gap-down bounce fade.** Short; gap ≤ −1.5%; RSI(5, 5-min) 60-90, *or* up ≥ ~0.3 ATR from the open; entry 11:00-13:00 (test 11:00-15:00 as a variant); stop ≥ 120 bps and ATR% ≥ 3%; t1s1-type target with an EOD flatten 15:50. Many names qualify: ~30-50 live trades/day across the book. It works on SPY-up and SPY-down days, not on flat ones.
2. **Universal filters (remedies, not tied to one setup):** no shorts on gap-up ≥ +0.5% names (−0.27R, 75 setups, both halves); no shorts with RSI(5) < 25; no longs while SPY is −0.3..−0.75% from open; no entries before ~10:30 unless a setup has its own evidence; minimum stop width / ATR% so costs stay ≤ ~0.04R.
3. **Long side:** the live record offers nothing robust. Long candidates must come from the 2-year history work, and the planning prior should be near zero. Late-day (≥ 14:30) and ETF late-dip longs are the only leads.
4. **Hold time:** most target exits arrive within 20-45 min, which matches the owner's sketch. The EOD flatten exits are slightly positive (+0.046 overall, +0.05 in cell A). Earlier forced exits are *not* supported (W5: earlier exits hurt gap-down fades).
5. **Honesty bar:** the cell A day-t is 1.0-1.45, far below the C3-BAR2 / Wave 1 bars (2.5-3.9), and the record depends on the 11-12 session. It must be confirmed on the 2-year history (open part, costs in, locked block untouched) before it is treated as an edge.

Files (scripts + tables, all small): `research/ultimate_1119/evidence_live_files/` — `load.py` (journals → LR8 R), `feat.py` (point-in-time features from SIP bars), `an.py`/`an2.py` (tables), `tables.txt`, `cells.csv`, `setups.csv`.

Educational only — not financial advice.
