# ultimate_1119 ROUND 3 — PRE-REGISTRATION (written 2026-11-19 ~07:30Z, before any round-3 scoring)

*Educational only — not financial advice. Research only: no setup, exit, config or account change. Nothing committed.*

Owner (2026-11-18): the best intraday setups from everything MCF has learned — many trades/session across the universe,
long and short, any market, high avg R per trade AFTER COSTS, entries >= 09:50, flat by 15:50, holds ~5-45 min.
"We have the usage. Do not stop until promising results show that would be expected to beat our current best setups."
"I don't want to force weak setups."

This file fixes the round-3 candidates, rules, grids, configuration count, split, selection rule and bars **before**
anything in round 3 is scored. Changes after the first fit run only as dated lines under "Amendments", counted.
Nothing below was chosen from a CHECK number except where sec. 0.5 says so openly.

## 0. What rounds 1-2 taught and how round 3 uses it
1. **19/19 candidates failed** (round 1 0/10, round 2 0/9; only ULT-12 reached TIER B). Volume is never the problem
   (2-30/session); the edge after costs is.
2. **Triggers beat random; bases lose.** Same-name random controls: +0.03..+0.13R for most triggers in both halves
   (ULT-15 short stack +0.113 fit / +0.132 check; ULT-13 one-bar RSI collapse +0.030 / +0.077; WB4 dip on ETFs +0.107 fit).
   Random entries in every stock base tried lose -0.02..-0.11R, partly BEFORE costs (ULT-15: long up-tape base -0.015
   gross fit). Plain tape/volatility/time bases never reached >= 0 (ULT-15 gate 0/16 cells).
3. **The one out-of-sample edge on this pipeline is the WB4 dip on index/sector equity ETFs** (ULT-12 anchor: fit
   +0.219, check +0.110, w/o best day +0.096, t 2.87, but 0.82/session). Widening to every ETF failed only because of
   single-stock 2x funds (MSTX, SNXX, ...); widening to stocks failed outright (6/6 % configs negative on check).
   Mechanism read: a sharp 15-min dip in a **diversified basket** is mostly liquidity/flow, which reverts; in a single
   name it is often information, which does not. Round 3's D2 work keeps "basket" as the edge-carrying part and raises
   volume through time window, an ATR-scaled trigger and basket-like universes — never through single names at large.
4. **Learned rankers on the whole universe learn "volatile names"** (ULT-11: +0.0004 over random on check) and the
   persistent factors flip sign between fit sub-halves (ULT-19). Round 3's D1 work (a) ranks only among bars where a
   trigger with proven relative edge fires (event-conditioned), and (b) ranks inside the ETF basket universe where the
   base is near zero.
5. **Contamination disclosure (honest).** CHECK (2025-10-01..2026-11-04) has now been read by two rounds. Round-3 design
   choices informed by earlier CHECK numbers: (i) "WB4 list / equity baskets, not single-stock funds" (ULT-12 family
   split on check); (ii) the ULT-13 one-bar collapse as a component (its check plateau was positive); (iii) the ULT-15
   short stack TS1/TS2 (its relative edge was +0.13 on check too). In addition, the WB4 and ST7-FD parameters came
   from Workbench / earlier research whose 2-year data may overlap CHECK (source of the WB4 tune not located; treated
   as check-informed). Consequences, fixed now: every candidate that uses (i)-(iii) or the WB4/ST7 parameters is tagged
   **CHECK-INFORMED** in its report; a CHECK-INFORMED pass is a screening result that needs a forward look (recorded-
   quote replay + live Testing exposure) before anyone calls it "the goal", and the Deploy stage must weigh it so.
   The N penalty below (t floor 3.68) is the statistical part of that discount.
6. **Statistical reality of BEATS (repeated from round 2).** Per-trade SD ~0.84R, design effect ~3.7: a check avg R of
   +0.10 needs ~ (3.68 x 0.84 / 0.10)^2 x 3.7 ~ 3,500 check trades (~12.7/session) to reach t 3.68; +0.15 needs ~5.6/
   session. A low-volume candidate can be TIER A but not "the goal". Stated now so nobody reads a 1.5/session +0.12 as
   a beat later.

## 1. Data, split, locked block (unchanged)
- Signals: lab frames /home/user/MCF/research/history2y/data/frames (5-min decision bars 09:50-15:00 ET bar close,
  1,226 symbols, today's list = survivorship bias, flatters longs). Context: research/history2y/data/context (spy_fo,
  qqq_fo, breadth, breadth_open, qqq_vwap). 1-minute bars: /home/user/MCF/data/cache_hist/1Min (read-only). Daily bars
  research/history2y/data/daily.parquet (date-filtered, see LOCKED).
- **FIT** = 2024-10 + 2025-03-01..2025-09-30 (170 sessions); sub-halves A = 2024-10 + 2025-03..05, B = 2025-06..09.
- **CHECK** = 2025-10-01..2026-11-04 (276 sessions). Scored ONCE per candidate on the frozen fit pick.
- **LOCKED** 2024-11-01..2025-02-28: never read. pyarrow filters on every load, no_locked() asserts on every frame,
  trade list and 1-min load, MCF_HIST_ALLOW_LOCKED refused by every bt.py. ULT-27 needs prior-session 1-min history:
  its look-back for 2025-03 sessions starts 2025-03-03 (it never reaches back into the block; the first 2025-03
  sessions with too few valid look-back days simply produce no signal).
- Frames end at the 15:00 bar: windows are clamped to <= 15:00.

## 2. Round-3 chassis (= round-2 chassis; reuse benchmark/bench.py walk + round-2 bt.py helpers, no new infrastructure)
- **Intake:** price >= $10 at the decision bar; point-in-time ADV20 >= candidate floor; |gap| < 20%; atr_d > 0;
  cost_r <= candidate cap (cost_r = LR8 round-trip cost for a stop exit / u, u = 0.25 x atr_d).
- **Entry** = OPEN of the 1-minute bar starting at the decision-bar close (next tradable print), LR8 entry cost on it.
- **Borrow:** every short pays 1.2 bp of entry notional; shorts only where easy_to_borrow = True (today's flag,
  caveat); **no shorts of leveraged or inverse ETFs ever** (their borrow is expensive and erratic) — ETF short exposure
  is taken by buying the inverse fund. Shorts priced < $20 pay 3 bp (cheap conservative tier).
- **Exits** walked on 1-minute bars as bench.py: stop first, then target; stop gap-through at the worse of open/stop;
  target at the limit, no exit cost; +2c on stops; TX-n = time exit at n min with a 2u catastrophic stop, R per 2u;
  brackets tXsY per u unless a candidate sets another unit. Flat 15:50. No entries after 15:00.
- One lot per symbol per candidate; refire >= 30 min after the exit; max 2 entries per symbol-session; day cap 30
  (first by time, ties ADV20 desc) unless stated.
- **Universal filters:** no short if gap >= +0.5% or RSI5 < 25; no long while SPY is -0.30..-0.75% from its open AND
  spy_r30 < 0 (unless a candidate's own tape rule says otherwise).
- **Forbidden columns:** frames win_*, r_*, *heat* — dropped before features, asserted absent.
- **Universes used in round 3 (frozen in round3/universes.json before any fit scoring, built from names / fund type
  only, no outcomes):**
  - **WB4** = the exact WB4 ETF list (124 names, modules/ULT-12_symbols.json "WB4").
  - **EQB** (equity baskets) = WB4 plus every other lab ETF whose holdings are an equity basket of >= 10 stocks, at any
    leverage, long or inverse (international / country / thematic equity ETFs such as EEM, EFA, EWZ, EWY, FXI, KWEB,
    KORU, VEA, VWO, ARKG). **Excluded:** single-stock funds (MSTX, NVDL, TSLL, CONL, ...), commodity / metal / energy-
    futures funds (GLD, SLV, USO, UCO, BOIL, UNG, AGQ, ...), crypto funds (IBIT, BITX, ETHA, ...), volatility funds
    (VXX, UVXY), bond funds (TLT, TMF, EDV, ...), managed-futures / option-income funds. Rule-based, written before fit.
  - **MEGA** = non-ETF stocks with point-in-time ADV20 >= $1B and price >= $20.
  - **Exposure groups** (ULT-21 only): ETFs mapped by underlying (Nasdaq-100: QQQ/QQQM/QLD/TQQQ/PSQ/QID/SQQQ; S&P 500;
    Russell 2000; Dow; semis; biotech; regional banks; financials; energy; gold miners; homebuilders; ...; others own group).
- **Fit-half-only feature statistics** (z-scores, quantile thresholds, tau) are computed on the training fold only.

## 3. Candidates (8) and pre-declared grids

### ULT-20 EVR — event-conditioned learned ranker, LONG + SHORT, 09:50-15:00 (D1)
Thesis: the swarm should choose among candidate trades that already carry relative edge, not among all bars (ULT-11's
failure). Rows are only bars where at least one library trigger fires; the model learns which context turns a
+0.05-over-random trigger into a positive trade.
- Event library (decision bar, point-in-time): long L1 WB4-A dip (ret3 <= -0.21 x atr_d%, ret12 >= -0.28 x atr_d%,
  di_diff7 >= -5); L2 one-bar RSI collapse (RSI14[prev] >= 50, RSI14 <= 35, buyPressure > 0); L3 RSI5 up-cross 30
  (this or previous bar) with buyPressure > 0; L4 depth (from_open_dATR <= -1.0 or dist_hod_dATR >= 1.5); L5 RSI2 <= 5.
  Short S1 pop (RSI5 in [60, 90), dist_lod_dATR >= 0.5, |sma20_dist| >= 1.5%); S2 roll-over (RSI5[prev] >= 80, RSI5
  falling, upper_wick > 0); S3 from_open_dATR >= +1.0; S4 RSI2 >= 95. Both: E5 sector lag (ULT-17 rule, S 0.15, Lmin
  0.10, in the sector's direction).
- Rows: every (bar, name, side) with >= 1 event of that side; intake per universe below; universal filters; shorts ETB.
- Features (~26): the 11 event flags + side event count; 5 time-block dummies; s x gap; s x from_open_dATR;
  s x vwap_dist_dATR; s x (RSI14 - 50); s x di_diff7; atr_d%; cost_r; log10 ADV20; is_ETF; volumeRatio; s x spy_fo;
  s x spy_r30 (s = +1 long / -1 short). z-scored on the training fold, clipped +-5, NaN -> 0.
- Target: after-cost R of TX-45 (decision close -> 5-min close at tod+45, LR8 both legs + borrow), per 2u,
  winsorised +-4 (training proxy; scoring through the real chassis).
- Models: RG = ridge alpha 1e3; LG = L2 logistic (C 0.01) on 1[target > 0]; GB = HistGradientBoosting(max_depth 2,
  max_iter 100, lr 0.05, min_samples_leaf 2000, l2 1.0, seed 1119).
- Trading: per name the better-scoring side; enter if score > tau_k; <= 3 entries per bar; session cap 2k; TX-45 exit.
  tau_k = training in-sample constant giving k entries/session.
- Walk-forward inside FIT exactly as ULT-11 (folds 2025-05..09, train on all earlier FIT months); "fit" = pooled OOF;
  final model on all FIT frozen (weights / pickle / tau in fitsel.json) before any check feature is built.
- Grid (12): model {RG, LG, GB} x k {4, 10} x universe {L1: ADV >= $100M, cost_r <= 0.05; L2: ADV >= $50M, cost_r
  <= 0.08}. Names 20a..20l (model outer, k middle, universe inner). CHECK-INFORMED (uses L2/S1/S2).
- Expected trades/session: ~3-4 (k 4) / ~7-10 (k 10).

### ULT-21 ETF-RANK — learned ranker inside the equity-basket ETF universe, LONG only (both market directions via inverse funds) (D1)
Thesis: the only universe whose dips revert out of sample is equity-basket ETFs, and its random base is near zero
(ULT-12 random fit -0.000). A small model over short-horizon reversal / trend features, trained on FIT only, may find
more of those trades than the single WB4 rule.
- Universe EQB, ADV20 >= $30M, cost_r <= 0.08, every 5-min bar 10:30-15:00. Long only (inverse funds give short
  exposure; no ETF shorts). One open lot per exposure group.
- Features (~20): ret1, ret3, ret6, ret12 in dATR; di_diff7; RSI2, RSI5, RSI14; vwap_dist_dATR; from_open_dATR;
  dist_hod_dATR, dist_lod_dATR; volumeRatio; atr_d%; cost_r; leverage (1/2/3) and inverse flag; spy_fo; spy_r30;
  5 time-block dummies.
- Target: after-cost R of TX-45 per 2u (training proxy), winsorised +-4. Walk-forward / OOF / freeze as ULT-20.
- Grid (8): model {RG ridge alpha 1e4, GB as ULT-20} x k {2, 4} x exit {t05s1 cap45 (WB4 geometry, u = 0.25 dATR),
  TX-45}. Names 21a..21h (model outer, k middle, exit inner). CHECK-INFORMED (universe choice, sec. 0.5 i).
- Expected trades/session: ~2 / ~4.

### ULT-22 WB4-WIDE — WB4's own trigger, more hours and an ATR-scaled twin, baskets only, LONG (D2)
Thesis: keep the edge-carrying parts (sharp 15-min dip, DI not bearish, falling-hour guard, basket universe, t05s1)
and raise volume one step at a time: longer window, ATR-scaled trigger with a lower ATR floor, EQB instead of WB4 list.
- Trigger P (WB4 exact): ret3 <= -0.75%, di_diff7 >= -5, ret12 >= -1.0%, atr_d% >= 3.6.
  Trigger A (ATR-scaled): ret3 <= -0.21 x atr_d%, ret12 >= -0.28 x atr_d%, di_diff7 >= -5, atr_d% >= 2.4.
  Indicators via mcf.research.arena.indicators.compute (as WB4 / ULT-12).
- Intake: ADV20 >= $95M (WB4's own), cost_r <= 0.08 (A) / 0.10 (P, as ULT-12); universal long filter.
- Exit t05s1 (u = 0.25 dATR) cap 45, flat 15:50; refire 30 min; max 2 per symbol-session.
- Grid (12): universe {W (WB4 list), Q (EQB)} x trigger {P, A} x window {1400-1500, 1230-1500, 1030-1500}.
  Names 22a..22l (universe outer, trigger middle, window inner); 22a = the WB4 anchor (W-P-1400).
  CHECK-INFORMED (sec. 0.5 i + WB4 parameters).
- Expected trades/session (fit counts scale from ULT-12: 1-h window ~1.4 fit / 0.8 check): 1400 ~0.8-1.4;
  1230 ~1.7-3; 1030 ~3-5; trigger A and Q add ~30-60%. Only the 1230 / 1030 rows can be eligible (>= 2/session).

### ULT-23 COLLAPSE-BASKET — ST7's one-bar RSI collapse moved to baskets and mega caps, LONG (D2)
Thesis: ST7-FD's edge sits in the ONE-bar collapse (ULT-13); its 2-year record is check-positive but fit-negative, and
the down-day losses are in single names. The WB4 lesson says a collapse in a diversified basket (or the most liquid,
index-driven mega caps) is more likely flow than news. Test ST7's exact trigger in those universes.
- Rule: RSI14[prev] >= 50 AND RSI14 <= RMAX (one 5-min bar); fromOpen <= -min(1.0%, 0.30 x atr_d%); buyPressure (19-bar)
  > 0; universal long filter; window 10:15-15:00; cost_r <= 0.08.
- Universes: Q = EQB (ADV20 >= $30M); M = MEGA; QM = both.
- Grid (12): universe {Q, M, QM} x RMAX {30, 35} x exit {t1s1 cap45 (ST7's), t05s1 cap45}. Names 23a..23l (universe
  outer, RMAX middle, exit inner). CHECK-INFORMED (sec. 0.5 ii + ST7 parameters).
- Expected trades/session: Q 0.5-1.5, M 1-3, QM 1.5-4.

### ULT-24 CONFL-2 — confluence of gated triggers on gated bases, LONG + SHORT (D3)
Thesis: round 1-2 lesson: first prove the base, then stack triggers that each add value in BOTH fit sub-halves. Round 2
used stock bases that lose before costs; round 3 uses the two cheapest bases with a reason to be near zero: equity-basket
ETFs and mega caps.
- **Bases** (decision bars 10:30-15:00):
  - BQ-L: EQB, ADV20 >= $30M, atr_d% >= 2.0, cost_r <= 0.08, own ret12 >= -0.28 x atr_d% (falling-hour guard). Long.
  - BM-L: MEGA, cost_r <= 0.05, SPY 60-min change > -0.40%, universal long filter. Long.
  - BM-S: MEGA, ETB, cost_r <= 0.05, gap <= +0.5%, SPY since 09:50 <= +0.20% AND spy_r30 <= +0.10%, RSI5 >= 25. Short.
- **Base gate (FIT only, before any trigger is scored):** one random base-eligible bar per base-eligible
  symbol-session (seed 1119), scored through the chassis with TX-45 AND t05s1 cap45; the base opens only if its random
  avg R >= 0 in BOTH fit sub-halves A and B under at least the exit used by the config. 3 evaluations, counted.
- **Triggers:** long TL-A WB4-A dip (as ULT-22 A, without the ATR floor); TL-B one-bar RSI collapse (RSI14[prev] >= 50,
  RSI14 <= 35); TL-C RSI2 <= 5; TL-D capitulation bar (lower wick >= 0.5 x bar range, bar volume >= 2x its 20-bar mean,
  close in the upper half of the bar). Short TS-1 pop (ULT-01: RSI5 in [60, 90), dist_lod_dATR >= 0.5, |sma20_dist|
  >= 1.5%); TS-2 roll-over (ULT-08: RSI5[prev] >= 80, falling, upper_wick > 0); TS-3 from_open_dATR >= +1.0; TS-4
  RSI2 >= 95.
- **Trigger gate (FIT only, after the base gate, before any confluence is scored):** per (open base, trigger), signal
  (trigger true on the bar) minus same-base random avg R (TX-45) must be >= 0 in BOTH fit sub-halves. Failing triggers
  are dropped (reported). 4 triggers x 3 bases = 12 evaluations, counted.
- **Confluence rule:** enter when at least C of the surviving triggers of that side have each been true on the decision
  bar or within the previous W bars (5-min spacing, same session); if fewer than C triggers survive, the base trades nothing.
- Grid (8): W {3 bars, 6 bars} x C {2, 3} x exit {t05s1 cap45, TX-45}. Names 24a..24h (W outer, C middle, exit inner).
  CHECK-INFORMED (TS-1/TS-2, TL-B).
- Expected trades/session: if all bases open, C 2 ~2-6; C 3 ~0.3-1. If the gates close everything (as ULT-15), the
  result is "no candidate", reported.

### ULT-25 ULTRA-CHEAP — the strongest relative-edge triggers only where cost per R is lowest, LONG + SHORT (D4)
Thesis: costs ate 0.04-0.12R per trade. Instead of rescaling R on any name (ULT-16: no help for time exits), trade only
where the cost of one u is tiny (cost_r <= 0.03: high ATR% x high price x top liquidity), so a +0.05-0.10 relative edge
is not eaten. Bracket geometry is varied with a wider unit (m), which is where scaling R can help (target reachable in
45 min, fewer stop-outs on noise).
- Universe: cost_r(u = 0.25 dATR) <= 0.03 at the decision bar AND ADV20 >= $300M AND atr_d% >= 2.0 (stocks and
  unlevered ETFs both sides; leveraged / inverse ETFs long only). Window W.
- Long trigger: one-bar RSI collapse (RSI14[prev] >= 50, RSI14 <= 35, buyPressure > 0) OR WB4-A dip (as ULT-22 A without
  the ATR floor); universal long filter; SPY 60-min change > -0.40%.
- Short trigger: TS-1 pop OR TS-2 roll-over (as ULT-24); gap <= +0.5%; SPY since 09:50 <= +0.20%; ETB; RSI5 >= 25.
- Unit Ru = m x atr_d. Exits: t05s1 = +0.5 Ru / -1 Ru; t1s1 = +1 Ru / -1 Ru; TX-45 with a 2 Ru catastrophic stop (R per 2 Ru).
  Cap 45, flat 15:50. R reported per actual risk and per 0.25-dATR unit.
- Grid (12): m {0.25, 0.50} x exit {t05s1, t1s1, TX-45} x window {1030-1500, 1300-1500}. Names 25a..25l (m outer, exit
  middle, window inner). CHECK-INFORMED (TS-1/TS-2, collapse).
- Expected trades/session: 1030 window ~3-8, 1300 window ~1.5-4 (to be confirmed by the fit counts).

### ULT-26 WITH-GAP TREND — with-the-gap continuation only on a trend tape, LONG + SHORT (D5)
Thesis: ULT-05 (with-gap pullback) gave 13-21 trades/session at ~0R (fit -0.011, check -0.003) and lost on flat tapes;
round 1's own backlog named the targeted remedy: a point-in-time "trend day so far" layer. Trend persistence inside a
day is documented (Gao, Han, Li & Zhou 2018, market intraday momentum); the name trades only in the direction of its own
gap AND the tape.
- Long: gap >= +G; close > VWAP and vwap_dist% <= 0.5 x atr_d% (pullback near VWAP); buyPressure > 0; name's position in
  its own intraday range (close - LOD) / (HOD - LOD) >= 0.6; tape T+: spy_fo >= +T and SPY's position in its own range
  since 09:30 >= 0.7.
- Short: mirror (gap <= -G; close < VWAP within 0.5 x atr_d%; buyPressure < 0; range position <= 0.4; tape T-: spy_fo
  <= -T and SPY range position <= 0.3); ETB; RSI5 >= 25.
- Intake ADV20 >= $50M, cost_r <= 0.08; window 10:30-14:30; no universal SPY long filter needed (T+ implies SPY up).
- Grid (8): G {2%, 3%} x T {0.30%, 0.50%} x exit {t1s1 cap45, TX-45}. Names 26a..26h (G outer, T middle, exit inner).
  Not check-informed.
- Expected trades/session: trend tapes on ~35-50% of sessions; ~2-6 per session averaged over all sessions.

### ULT-27 PERIODICITY — same-clock-interval return persistence across days, LONG + SHORT (D5)
Thesis: a mechanism class never tried in MCF. Heston, Korajczyk & Sadka (2010, J. Finance, "Intraday patterns in the
cross-section of stock returns"): a stock's return in a given half-hour tends to repeat at the same half-hour on later
days (institutional order-splitting / scheduled flows), for weeks. Cross-sectional, both sides, any tape.
- At the 10:00, 11:00, 12:00, 13:00, 14:00 and 15:00 decision bars: for each eligible name, P = mean over the previous
  L open sessions (same clock interval t..t+30 min, 1-min cache, prior sessions only, >= 0.7 L valid days) of the
  interval return / atr_d% of that day. Long the top N by P, short the bottom N (ETB, gap/RSI5 universal short filters;
  an excluded name is replaced by the next eligible one). Exit TX-30 with a 2u catastrophic stop.
- Universe: non-leveraged names (stocks + unlevered ETFs), ADV20 >= $200M, price >= $10, cost_r <= 0.05.
- Day cap 36 for this candidate (6 times x 2N, N <= 3). Grid (6): L {5, 10, 20} x N {2, 3}. Names 27a..27f (L outer).
  Not check-informed. Honest prior: the published gross effect is a few bp per half hour, likely below cost; it is
  included because it is independent of every trigger tried so far and costs little to test.
- Expected trades/session: 24 (N 2) or 36 (N 3).

### Not built (and why)
ORB on stocks in play (orb20_a already 2-year flat, -0.000R, 6.7/session); earnings continuation (no point-in-time
earnings calendar); index-level dip / day-type lanes (random entries on the same days earn the same); market intraday
momentum into the close (entries end at 15:00 and W6 X5 shows late alignment reversing); sector lead-lag as a setup
(ULT-17: the lag closes within a minute — kept only as an event flag in ULT-20); VWAP-band reversion on stocks (CWT13);
limit entries (ULT-16 adverse selection); every failed round-1/2 candidate unchanged.

## 4. Configuration count
| Candidate | configs |
|---|---|
| ULT-20 EVR | 12 |
| ULT-21 ETF-RANK | 8 |
| ULT-22 WB4-WIDE | 12 |
| ULT-23 COLLAPSE-BASKET | 12 |
| ULT-24 CONFL-2 | 8 grid + 3 base gates + 12 trigger gates = 23 |
| ULT-25 ULTRA-CHEAP | 12 |
| ULT-26 WITH-GAP TREND | 8 |
| ULT-27 PERIODICITY | 6 |
| Bias diagnostics (fit pick re-scored with signal-close fill and no borrow fee; one per candidate) | 8 |
| **Round 3 total** | **101** (78 grid + 23 gates/diagnostics) |
| Cumulative before round 3 (round 1 682 + round 2 92 = 774, plus ULT-15's disclosed extras counted at the conservative 779) | 779 |
| **Cumulative N after round 3** | **880** |

sqrt(2 ln 880) = **3.68** -> the BEATS t floor is max(1.5, 3.68) = 3.68 (recomputed with the final N if an amendment
adds configurations). Random-entry controls are reported, not counted (except ULT-24's gates, which decide something).
Walk-forward folds inside ULT-20/21 are part of each named config.

## 5. Selection and scoring order (as round 2)
1. Score every grid config on FIT only (ULT-20/21: walk-forward OOF inside FIT; ULT-24: gates first).
2. Per candidate, fit pick = highest **fit total R minus the best fit day's R** among configs with >= 2.0 trades/session
   on fit (ties: fewer conditions, then first listed). If none reaches 2/session, the best by the same score is carried
   but cannot reach TIER A. Never rank by avg R/trade.
3. Freeze fitsel.json (UTC timestamp, sha256 of bt.py and module) BEFORE any check frame / feature / trade is built.
4. Score the fit pick on CHECK once. That single result decides the tier and the BEATS test.
5. Only then: the full grid on check as a plateau diagnostic (never used to re-select); the bias diagnostic.

## 6. BARS (fixed now)
- **TIER A:** check avg R > 0 AND check avg R w/o best day > 0 AND fit avg R > 0 (ULT-20/21: OOF) AND >= 2.0
  trades/session on check (all 276 sessions in the denominator) AND no look-ahead (code review incl. forbidden columns
  and point-in-time truncation test).
- **BEATS BENCHMARK (the goal):** TIER A AND check avg R > +0.0836 AND check avg R w/o best day > +0.0734 AND check total
  R/session > 0 AND worst check day / trades per traded session >= -2.152 AND day-clustered t of check avg R >=
  max(1.5, sqrt(2 ln N_cumulative)) = **3.68 at N = 880**.
  Day-clustered t = avgR / SE, SE = sqrt( sum over sessions d of ( sum_{i in d} (r_i - avgR) )^2 ) / n_trades.
- A CHECK-INFORMED candidate that meets BEATS is reported as "meets the bar, check-informed" (sec. 0.5).
- Only BEATS candidates are "the goal". TIER A non-beaters may be deployed only if clearly positive (owner: no weak
  setups) — the Deploy stage decides with the skeptic. Everything else: FAIL (TIER B = fit > 0 and check > -0.02 is
  reported as a near miss, never deployed).

## 7. Reported for every candidate (fit and check)
trades, trades/session, win, avg R (actual risk and 0.25-dATR units), avg R w/o best day, best-day share (1-day tag
>= 50%), total R, R/session, worst day, worst day / trades per traded session, day-clustered t, SPY up/flat/down avg R
(end-of-day label, reporting only), **avg R without 2025-04-03..04-09** (fit; check has no such dates), check first/
second half, fit sub-halves A/B, side split, same-name random control and signal-minus-random, median hold, exit mix,
bias diagnostic, CHECK-INFORMED tag, configs tried. Long results carry the survivorship caveat; signal-minus-random is
the survivorship-neutral read.

## 8. Rule-change context (owner 2026-11-02)
Both 2-year halves are scored with one fixed rule set (today's LR8 costs, round-2/3 chassis); no live rule change falls
inside them. Live figures quoted in earlier rounds span the ledger changes listed in RESULTS.md (11-12 LR8 cost model,
10-28 Primary sizing, 10-30 Testing cost filter, 11-17 TSZ1 half-size lots / SPYEXIT, setup moves). WB4 itself went
live 2026-11-17 (Testing E), after the CHECK window.

## 9. Disk / hygiene
~4.7 GB free: no feature files on disk (ridge from accumulated X'X / X'y; GB on an in-memory subsample <= 2M rows);
trade lists in the scratchpad, deleted after scoring; only small json/csv/md under round3/.

## Amendments
(none)

Educational only — not financial advice.
