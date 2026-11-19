# ultimate_1119 ROUND 2 — PRE-REGISTRATION (written 2026-11-19 before any round-2 scoring)

*Educational only — not financial advice. Research only: no setup, exit, config or account change. Nothing committed.*

Owner (2026-11-18): build the best intraday setups from everything MCF has learned — many trades/session across the
universe, long and short, any market, high avg R per trade AFTER COSTS, entries >= 09:50, flat by 15:50, holds ~5-45 min.
"We have the usage. Do not stop until promising results show that would be expected to beat our current best setups."
"I don't want to force weak setups."

This file fixes the round-2 candidates, rules, grids, configuration count, split, selection rule and bars **before**
anything in round 2 is scored. Changes after the first fit run only as dated lines under "Amendments", counted.

## 0. What round 1 taught (research/ultimate_1119/RESULTS.md) and how round 2 uses it
1. **0/10 passed; every check avg R was -0.003..-0.157.** Volume was easy (6-21/session); the edge was not.
2. **Triggers beat random, bases lose.** Same-name random-entry controls: ULT-01 +0.060 fit / +0.066 check, ULT-03
   +0.058 / +0.060, ULT-07 +0.074 / +0.020, ULT-08 ~+0.21 / +0.03; ULT-02 beat same-moment random names (+0.116 check).
   But random entries in those bases run -0.05..-0.11R (mostly cost, ~0.075-0.12R per trade at R = 0.25 dATR), so a
   +0.06 trigger only shrinks the loss. -> D3 (confluence on a base that is >= 0 on its own) and D4 (cost geometry).
3. **Fit totals were carried by one crash-rebound day** (2025-04-04/04-07/04-09). -> round-2 fit selection ranks by
   fit total R **without the best fit day** (sec. 5), decided now, before scoring.
4. **The two benchmark positives are not alike.** NM-ETF-late-dip is positive in BOTH halves (fit +0.269, check +0.052,
   ~1/session). ST7-FD is fit **-0.132** / check +0.084; round 1 showed ST7's one-bar RSI collapse is the edge-carrying
   event (ULT-03's 3-bar window diluted it x7-10) and that its fit losses sit on SPY-down days (-0.45 fit). Round 1
   broadened ULT-07 with a different trigger (RSI5 turn), not WB4's own trigger — that, not the universe, failed.
   Common core of NM-ETF / ST7 / L3: **a sharp short-horizon counter-move while the longer-horizon flow is intact**.
   -> D2 candidates keep the trigger exactly and change one thing at a time.
5. **Statistical reality of the BEATS bar.** With per-trade SD ~0.84R and design effect ~3.7 (crunch/w5), a check avg R
   of +0.084 needs about 36.5^2 x 3.7 ~ 4,900 check trades (~18/session over 276 sessions) to reach t = 3.65. So
   only high-volume candidates (ULT-11, -17, -18, -19 at k >= 20, maybe -14) can be "the goal"; low-volume ones can at
   best be TIER A. This is stated now so nobody reads a low-volume +0.10 as a beat later.

## 1. Data, split, locked block (unchanged from round 1)
- Signals: lab frames research/history2y/data/frames (5-min decision bars 09:50-15:00 ET bar close, 1,226 symbols,
  today's list = survivorship bias, flatters longs). Context: research/history2y/data/context (spy_fo, qqq_fo,
  breadth, breadth_open, qqq_vwap). Sector ETFs from data/cache_hist/1Min (XL*, SMH, XBI, KRE, GDX, XOP, ITB, IBIT,
  ARKK, IWM, QQQ, SPY). Daily bars research/history2y/data/daily.parquet (filtered, see LOCKED).
- **FIT** = 2024-10 + 2025-03-01..2025-09-30 (170 sessions). Sub-halves for sign checks: A = 2024-10 + 2025-03..05,
  B = 2025-06..09.
- **CHECK** = 2025-10-01..2026-11-04 (276 sessions, last cache day). Scored ONCE per candidate on the frozen fit pick.
- **LOCKED** 2024-11-01..2025-02-28: never read. pyarrow filters on every frame / 1-min / daily load; no_locked()
  asserts on every frame, trade list and 1-min load; MCF_HIST_ALLOW_LOCKED never set (bt scripts refuse it).
  daily.parquet holds locked rows: it is read only with a date filter excluding the block.
- Frames end at the 15:00 bar: every window is clamped to <= 15:00 (live LabStrategy clamps the same way).

## 2. Round-2 chassis (every candidate unless its spec says otherwise)
Reuses benchmark/bench.py (month_job-style signal stage, walk1_job 1-minute exit walk, cost_r) through one thin shared
helper research/ultimate_1119/round2/r2common.py; no new infrastructure.
- **Intake U2:** price >= $10 at the decision bar; point-in-time ADV20 >= candidate floor (default $50M); |gap| < 20%;
  atr_d > 0; cost_r <= candidate cap, where cost_r = LR8 round-trip cost at the decision bar for a stop exit / u,
  u = 0.25 x atr_d (prior-day daily ATR).
- **Entry fix (bias "fills at signal close"):** entry price = OPEN of the 1-minute bar that starts at the decision bar
  close (the next tradable print), not the 5-min close. LR8 entry cost on that price. Diagnostic (counted, sec. 4):
  the fit pick re-scored with the old signal-close fill and no borrow fee, to show the size of both biases.
- **Borrow fee (bias "no borrow fee"):** every short pays 1.2 bp of entry notional (~3%/yr for one day; conservative
  for an intraday ETB short) in addition to LR8; shorts only in names with easy_to_borrow = True in data/universe.csv
  (today's flag — not point-in-time; caveat).
- **R unit = actual risk.** tXsY brackets use u (0.25 dATR) unless a candidate sets another unit. TX-n = time exit at
  n minutes with a catastrophic stop at 2u; R per 2u (as round 1). Every report also shows R in 0.25-dATR units.
- One lot per symbol per candidate; refire >= 30 min after the exit; max 2 entries per symbol-session; day cap 30
  (first by time, ties ADV20 desc) unless a candidate states its own cap. No entries after 15:00. Flat 15:50.
- Exits walked on 1-minute bars as bench.py (stop first, then target; stop gap-through at the worse of open/stop;
  target at the limit, no exit cost; flat 15:50).
- Costs: LR8 research basis (entry 1c + 1 bp x TOD mult; exit 1c + 1 bp except target fills; +2c stops; x3 extended
  tier) + borrow fee above. Underestimate rather than overestimate.
- **Universal filters** (round-1 evidence, both halves, many setups): no short if gap >= +0.5% or RSI5 < 25; no long
  while SPY is -0.30..-0.75% from its open AND spy_r30 < 0 (except where a candidate states a tape rule of its own).
- **Forbidden columns** (look-ahead): frames win_* and r_* (outcome columns), and the composite *Heat / heat columns
  (provenance unclear). Each bt.py asserts none of them is read by a signal or feature.
- Sector map (ULT-11, -17, -18): for each name-session, sector ETF = argmax Pearson correlation of daily close-to-close
  returns over the prior <= 60 open (non-locked) sessions, min 20, among {SPY, QQQ, IWM, XLK, XLF, XLE, XLV, XLI, XLY,
  XLP, XLU, XLB, XLRE, XLC, SMH, XBI, KRE, GDX, XOP, ITB, IBIT, ARKK}; beta = OLS beta over the same window, clipped
  [0.3, 3]. Strictly prior sessions -> point-in-time. ETFs themselves are not traded in ULT-17/-18.

## 3. Candidates (9) and pre-declared grids

### ULT-11 LR-RANK — learned ranker, wide features, LONG + SHORT, 09:50-15:00 (D1)
Thesis: the swarm finds the factors. Round 1 shows weak (+0.06) but real conditional information in many hand
triggers; a regularised model trained only on FIT can pool many weak point-in-time signals and rank every 5-min bar,
trading only the top of the distribution, at high volume.
- Universe: U2, ADV20 >= $50M, cost_r <= 0.08. Every 5-min decision bar 09:50-15:00, both sides.
- Training target (FIT only): after-cost R of a time exit h min later (entry decision close, exit the 5-min close at
  tod + h, frames + headtail tail rows; LR8 market both legs, + borrow for shorts), in u units, winsorised at +-4.
  Training proxy only; all scoring is through the real chassis (next-minute-open entry, 1-min walk).
- Features (~36, all at the decision bar close): minutes since 09:30 + 5 time-block dummies (0950-1029, 1030-1129,
  1130-1259, 1300-1359, 1400-1500); gap %, gap / atr_d%; fromOpen, vwapDist, dist_hod/lod/pdh/pdl in dATR; RSI14, RSI5,
  RSI2 (computed from frame closes within the symbol-day), rsiSlope; ret1/ret3/ret6/ret12 in dATR; volumeRatio,
  buyPressure, flow3, upper_wick, lower_wick; sma20/sma50 dist %, sma20 slope %; atr_d %; log10 ADV20; cost_r; spy_fo,
  spy_r30 (6-bar change), qqq_fo, qqq_vwap, breadth, breadth - breadth_open; sector ETF fo and r30 (sector map),
  name fromOpen% - beta x sector fo%, sector-missing flag. z-scored with training-fold mean/sd, clipped +-5, NaN -> 0.
- Models (separate per side): R3 = ridge alpha 1e3; R5 = ridge alpha 1e5 (exact, from X'X / X'y accumulated month by
  month — no feature file on disk); GB = sklearn HistGradientBoostingRegressor(max_depth 3, max_iter 200, lr 0.05,
  min_samples_leaf 5000, l2 1.0, no early stopping) on a fixed 2M-row random subsample of the training fold (seed 1119).
- Trading rule (causal): at each bar take the better side per name; enter if pred > tau; at most 3 entries per bar
  (highest pred first); session cap 2k; one lot per symbol, refire 30 min, max 2/symbol-session; exit TX-h (same h).
  tau = the training-period in-sample prediction quantile that gives on average k entries/session (fixed constant).
- Walk-forward INSIDE FIT: folds 2025-05, 06, 07, 08, 09; each fold trains on all FIT months before it. Fold
  trades are scored through the real chassis. "Fit" figures for this candidate (selection AND the TIER A fit test) =
  pooled out-of-fold (OOF) results; in-sample all-FIT figures are reported too. Final model = retrained on all FIT,
  tau from all-FIT in-sample predictions; weights, scaler, tau (and the GBM pickle) frozen in fitsel.json / beside it
  before any check feature is built.
- Grid (12): model {R3, R5, GB} x h {30, 45} x k {8, 20}. Names 11a..11l (model outer, h middle, k inner).
- Expected trades/session: ~8 or ~20 (check may drift; capped at 2k).

### ULT-19 LR-LITE — shrunk linear score on the persistent factors, LONG + SHORT (D1, low-dimensional twin)
Thesis: WAVE1 found only time of day, gap and distance-from-open keep their sign between halves; a 12-feature ridge
on those (plus cost/vol and the tape), with a sign-stability filter, should overfit far less than ULT-11.
- Features (side-signed, s = +1 long / -1 short): 5 time-block dummies; s x gap; s x fromOpen_dATR; s x vwapDist_dATR;
  atr_d %; cost_r; s x spy_fo; s x spy_r30; s x (RSI5 - 50); s x (RSI14 - 50); one model, side as a signed design.
- Ridge alpha 1e5 on FIT; **stability filter**: a coefficient whose sign differs between fit sub-halves A and B is set
  to 0. Target, trading rule, walk-forward, OOF-as-fit, freezing: as ULT-11 with h = 45.
- Grid (6): k {5, 10, 20} x universe {UA: ADV >= $50M, cost_r <= 0.10; UB: ADV >= $200M, cost_r <= 0.06}.
  Names 19a..19f (k outer).
- Expected trades/session: 5 / 10 / 20.

### ULT-12 ETF-DIP-X — NM-ETF WB4's own trigger, new universes/times, LONG (D2)
Thesis: NM-ETF is the only setup positive in both 2-year halves. Keep WB4's trigger exactly (round-1 lesson: the
trigger swap failed, not the universe) and extend only universe / window, one step at a time.
- Trigger (WB4): ret3 <= -0.75% (15-min return of 5-min closes) AND di_diff7 >= -5 AND ret12 >= -1.0% (falling-hour
  guard, the name's own 60-min return) AND atr_d_pct >= 3.6. Indicators via mcf.research.arena.indicators.compute.
  ATR-scaled variant: ret3 <= -0.21 x atr_d_pct and ret12 >= -0.28 x atr_d_pct (= WB4 at atr_d_pct 3.6).
- Exit t05s1 (u = 0.25 dATR), max hold 45 min, flat 15:50; refire 30 min; cost_r <= 0.10.
- Universes: E = every ETF/ETN in the 1,226 list (universe.csv name/fund match, plus the WB4 list) with ADV >= $50M;
  S200 = non-ETF stocks ADV >= $200M; S100 = non-ETF stocks ADV >= $100M.
- Grid (12): universe {E, S200, S100} x drop {pct, atr} x window {1400-1500, 1300-1500}. Names 12a..12l
  (universe outer, drop middle, window inner). Anchor diagnostic (counted): exact WB4 ETF list, 1400-1500, pct.
- Expected trades/session: E 1.5-3, S200 2-5, S100 4-8 (1300 windows ~1.7x).

### ULT-13 ST7-SHARP — ST7's one-bar RSI collapse + a down-tape guard, LONG (D2)
Thesis: ST7-FD is the best check-half benchmark; its edge sits in the ONE-bar collapse (RSI14 >= 50 -> <= 30 in one
5-min bar); its fit-half failure sits on SPY-down days. A point-in-time tape guard is the targeted remedy for that
failure mode; ADV is relaxed to $50M for volume (ULT-03 showed ADV $20M vs $95M did not hurt).
- Rule: RSI14[prev] >= 50 AND RSI14 <= RMAX; fromOpen <= -1.0%; buyPressure (19-bar) > 0; ADV >= $50M; cost_r <= 0.10;
  window 09:50-15:00. Guard G1: skip if spy_fo <= -0.30% AND spy_r30 <= 0 (SPY down from the open and still falling);
  G0 = no guard (universal long filter still applies).
- Grid (8): RMAX {30, 35} x guard {G0, G1} x exit {t1s1 cap45, TX45}. Names 13a..13h.
- Expected trades/session: 1-4. Honest prior: ST7 lost on fit; this can only be TIER A if the guard fixes fit.

### ULT-14 SNAP — sharp counter-move against an intact trend, LONG + SHORT (D2, the NM-ETF/ST7/L3 common core)
Thesis: all three positive families buy (sell) a sharp 15-min move against a still-intact longer-horizon flow, in
volatile names, with a quick half-R / 1R target. Build that core directly, two-sided, ATR-scaled.
- Long: ret3 <= -D x atr_d (15-min drop in daily-ATR units) AND di_diff7 >= 0 AND buyPressure > 0 AND atr_d% >= 3.0
  AND SPY 60-min return > -0.40%.
- Short: ret3 >= +D x atr_d AND di_diff7 <= 0 AND buyPressure < 0 AND gap <= +0.5% AND RSI5 < 90 AND
  SPY since 09:50 <= +0.20% (the Workbench short-fade skip) AND ETB.
- U2 with ADV >= $50M, cost_r <= 0.08.
- Grid (8): window {1400-1500, 1100-1500} x D {0.20, 0.30} x exit {t05s1 cap45, t1s1 cap45}. Both sides always;
  side split reported. Names 14a..14h.
- Expected trades/session: 3-12.

### ULT-15 CONFLUENCE — 2+ round-1 triggers that beat random in both halves, on a base that is >= 0 by itself (D3)
Thesis: round 1's lesson: a good trigger on a losing base only shrinks the loss. First prove the base, then stack
triggers that each added value in both halves.
- **Base gate (FIT only, before any trigger is scored):** one random eligible bar per eligible symbol-session (seed
  1119), scored through the chassis with the config's exit; the base passes only if its random avg R >= 0 in BOTH fit
  sub-halves A and B. A side whose base fails is dropped from that config (reported); if both fail, the config scores
  nothing. 4 base evaluations (2 sides x 2 liquidity levels), counted.
- Base BL (long): atr_d% >= 3.0; 10:30-15:00; spy_fo >= 0 AND spy_r30 >= 0 (with the tape).
  Base BS (short): ETB; gap <= -1.0%; 11:00-15:00; spy_fo <= 0 AND spy_r30 <= 0.
  Liquidity L1: ADV >= $200M (long) / $100M (short), cost_r <= 0.05; L2: ADV >= $50M, cost_r <= 0.08.
- Long triggers: TL1 RSI14 crossed below 50 in the last 3 bars AND RSI14 <= 30 (ULT-03); TL2 RSI5 crossed up through 30
  on this or the previous bar AND buyPressure > 0 (ULT-07 timing); TL3 from_open_dATR <= -1.0 OR off_hod_dATR >= 1.5
  (ULT-02 depth A).
  Short triggers: TS1 RSI5 in [60, 90) AND lod_dATR >= 0.5 AND sma20_dist not within +-1.5% (ULT-01); TS2 RSI5[prev]
  >= 80 AND rsiSlope < 0 AND upper_wick > 0 (ULT-08); TS3 from_open_dATR >= +1.0 (L3 recovery / ULT-08 run).
  A trigger counts if true on the decision bar or one of the 2 bars before it. Honest note: the long triggers all
  measure "oversold", so they are correlated, not independent; confluence still filters.
- Grid (8): C {2-of-3, 3-of-3} x exit {TX30, TX45} x liquidity {L1, L2}. Names 15a..15h.
- Expected trades/session: 2-6 (if both bases pass).

### ULT-16 COST-GEO — wider R, liquid names, limit entry, on ULT-01 + ULT-03 triggers (D4)
Thesis: costs ate 0.075-0.12R per trade at u = 0.25 dATR. Note (pre-registered): for pure time exits, scaling R does
not change the edge/cost ratio; it helps only through bracket geometry (a bigger target that the 45-min move can still
reach) and lower cost per R in liquid names. Limit entries save the entry cost but suffer adverse selection
(archive P7: passive fills pick the -0.22R trades) — measured, not assumed.
- Book = ULT-01 trigger (SHORT: gap <= -1.5%, RSI5 in [60, 90), lod_dATR >= 0.5, spy since 09:50 <= +0.15%, sma20 not
  within +-1.5%, 11:00-15:00) + ULT-03 trigger (LONG: RSI14 crossed below 50 in last 3 bars and <= 30, fromOpen <= -1%,
  buyPressure > 0, not (spy_fo in -0.75..-0.30% and spy_r30 < 0), 10:15-15:00). Universe ADV >= $150M (stocks + ETFs
  incl. leveraged), cost_r <= 0.10.
- Unit Ru = m x atr_d; bracket +1 Ru / -1 Ru, max hold 45 min, flat 15:50.
- Entry MKT = next-minute open (chassis). Entry LMT = limit 0.1u better than the decision close, valid 10 min, filled
  only if a 1-min bar trades THROUGH the limit by >= $0.01, fill at the limit, entry cost 0 (as LR8 limit fills);
  unfilled = no trade (fill rate reported).
- Grid (8): m {0.5, 1.0} x entry {MKT, LMT} x vol floor {none, atr_d% >= 2.5}. Names 16a..16h. Side split reported.
- Expected trades/session: 3-8 (LMT fewer).

### ULT-17 SECTOR-LAG — sector-ETF lead-lag catch-up, LONG + SHORT (D5)
Thesis: ETFs/large caps lead; a name whose sector made a sharp 15-min move it has not yet followed tends to catch up.
Independent of every round-1 trigger; cross-sectional; high volume; both sides; works in any tape (it needs sector
moves, not a direction).
- At decision bar t (10:15-15:00): sret3 = sector ETF 15-min return (5-min closes from 1-min cache); require
  |sret3| >= S x sector atr_d% (prior-day sector daily ATR %); lag L = sgn(sret3) x (beta x sret3 - nret3) / atr_d% of
  the name >= Lmin; trade the name in the sector's direction. Non-ETF names only; U2 with ADV >= $50M, cost_r <= 0.08;
  universal filters; sector missing -> no signal.
- Grid (8): S {0.15, 0.25} x Lmin {0.10, 0.20} x exit {TX30, TX45}. Names 17a..17h.
- Expected trades/session: 5-20.

### ULT-18 XS-MOMREV — cross-sectional momentum / reversal at fixed times, LONG + SHORT (D5)
Thesis: distance from open is one of the three persistent conditions; whether it continues or reverts over 45 min
inside the day is open, so both directions are pre-registered (the choice is a fit selection, counted). Fixed times
make it a market-neutral-ish book every session, in any tape, at high volume.
- At the 11:00, 13:00 and 14:00 decision bars: universe non-ETF, ADV >= $200M, price >= $10, cost_r <= 0.06; shorts
  ETB; universal filters (an excluded name is replaced by the next eligible one).
- Sort key K1 = fromOpen in dATR; K2 = sector-relative: (fromOpen% - beta x sector fo%) / atr_d%.
- MOM = long the top N, short the bottom N; REV = long the bottom N, short the top N. Exit TX45. Day cap 6N.
- Grid (8): K {K1, K2} x direction {MOM, REV} x N {5, 10}. Names 18a..18h.
- Expected trades/session: 30 (N 5) or 60 (N 10).

### Not built (and why)
VWAP-band mean reversion (CWT13 failed, -0.08 2y; VWAP-sd lifts ~0 in Move Hunt); earnings continuation (no PIT
earnings calendar in the cache); index-ETF day-type lanes (random entries on the same days earn the same); opening
entries; gap-up fades; anything round 1 failed unchanged.

## 4. Configuration count
| Candidate | configs |
|---|---|
| ULT-11 | 12 |
| ULT-12 | 12 (+1 anchor diagnostic) |
| ULT-13 | 8 |
| ULT-14 | 8 |
| ULT-15 | 8 (+4 base gates) |
| ULT-16 | 8 |
| ULT-17 | 8 |
| ULT-18 | 8 |
| ULT-19 | 6 |
| Bias diagnostics (signal-close fill + no borrow, one per candidate's fit pick) | 9 |
| **Round 2 total** | **92** (78 grid + 14 gates/diagnostics) |
| Round 1 whole job (RESULTS.md, incl. ULT-10's 3 unused diagnostics; 574 evidence + 104 candidates + 1 benchmark + 3) | 682 |
| **Cumulative N after round 2** | **774** |
sqrt(2 ln 774) = **3.65** -> the BEATS t-stat floor is max(1.5, 3.65) = 3.65 (recomputed with the final N if any
amendment adds configurations). Random-entry controls are reported, not counted (except ULT-15's base gates, which
decide something). Walk-forward folds inside ULT-11/19 are part of each named config, not extra configs.

## 5. Selection and scoring order
1. Score every grid config on FIT only (ULT-11/19: walk-forward OOF inside FIT).
2. Per candidate, the fit pick = highest **fit total R minus the best fit day's R** among configs with >= 2.0
   trades/session on fit (ties: fewer conditions, then first listed). If none reaches 2/session, the best by the same
   score is carried but cannot reach TIER A. Never rank by avg R/trade.
3. Freeze fitsel.json (timestamp, sha256 of bt.py and module) BEFORE any check frame / feature / trade is built.
4. Score the fit pick on CHECK once. That single result decides the tier and the BEATS test.
5. Only then: the full grid on check as a plateau diagnostic (reported, never used to re-select); the bias diagnostic.

## 6. BARS (fixed now)
- **TIER A:** check avg R > 0 AND check avg R w/o best day > 0 AND fit avg R > 0 (ULT-11/19: OOF) AND >= 2.0
  trades/session on check (all 276 sessions in the denominator) AND no look-ahead (code review incl. forbidden
  columns).
- **BEATS BENCHMARK (the goal):** TIER A AND check avg R > +0.0836 AND check avg R w/o best day > +0.0734 AND check total
  R/session > 0 AND worst check day / trades per traded session >= -2.152 AND day-clustered t of check avg R >=
  max(1.5, sqrt(2 ln N_cumulative)) = 3.65 at N = 774.
  Day-clustered t = avgR / SE, SE = sqrt( sum over sessions d of ( sum_{i in d} (r_i - avgR) )^2 ) / n_trades.
- Only BEATS candidates are "the goal". TIER A non-beaters may be deployed only if clearly positive (owner: no weak
  setups) — the Deploy stage decides with the skeptic. Everything else: FAIL, reported with its numbers.

## 7. Reported for every candidate (fit and check)
trades, trades/session, win, avg R (actual-risk units and 0.25-dATR units), avg R w/o best day, best-day share
(1-day tag >= 50%), total R, R/session, worst day, worst day / trades per traded session, day-clustered t, SPY up/flat/
down avg R (end-of-day label, reporting only), fit avg R without 2025-04-03..04-09, check first/second half, side
split, same-name random-entry control and signal-minus-random, median hold, LMT fill rate (ULT-16), bias diagnostic
(signal-close fill / no borrow), configs tried. Long results carry the survivorship caveat; the signal-minus-random
figure is the survivorship-neutral read.

## 8. Rule-change context (owner 2026-11-02)
The 2-year halves are scored with one fixed rule set (today's); no live rule change falls inside them. Live-record
figures quoted from round 1 / evidence_live.md span the ledger changes listed in RESULTS.md (notably 11-12 LR8 cost
model, 10-28 Primary sizing, 10-30 Testing cost filter, 11-17 TSZ1 half-size lots and SPYEXIT).

## 9. Disk / hygiene
~4.7 GB free: no feature files on disk (ridge from accumulated X'X/X'y; GBM on a 2M-row in-memory subsample);
trade lists in the scratchpad, deleted after scoring; only small json/csv/md under round2/.

## Amendments
(none)

Educational only — not financial advice.
