# ultimate_1119 — PRE-REGISTRATION (written 2026-11-19 before any candidate scoring)

*Educational only — not financial advice. Research only: no setup, exit, config or account change. Nothing committed here.*

Owner request (2026-11-18): build from the ground up the "ultimate" intraday setup(s) — many trades per session across
the universe, long AND short, any market condition, high avg R after costs, entries >= 09:50, flat by 15:50-15:55,
holds ~5-45 min. Owner, same night: **"I don't want to force weak setups."** Only TIER A below is ever deployed.

This file fixes the candidates, their rules, their grids, the total configuration count, the fit/check split, the
selection rule and the deploy bar **before** anything is scored. Nothing in it may be changed after the first fit run
except to add a line under "Amendments" (dated, with the reason), and any amendment's extra configurations are counted.

## 0. Evidence used (read-only; no scoring)
- research/ultimate_1119/evidence_live.md (26,944 live real-fill trades, 230 post-hoc configs)
- research/ultimate_1119/evidence_archive.md (archive synthesis, 0 configs)
- research/ultimate_1119/evidence_movehunt_long.md (104 configs, fit half only)
- research/ultimate_1119/evidence_movehunt_short.md (240 configs, fit half only)
- research/ultimate_1119/benchmark/BENCHMARK.md (current best setups on the same pipeline; 1 config)
- research/crunch/WAVE1.md: 0/31 bespoke rules pass; tunes picked on fit fail on check; only time of day, gap and
  distance-from-open keep their sign between halves; ranking by avg R/trade overfits more than ranking by total R.

Components used (only those that held in both halves / several sources):
1. Cost / volatility intake (cost_r <= 0.10, ATR% floor, price >= $10) — monotone in every source.
2. Broad time blocks (no entries before 10:15-10:30 except where stated; 11:00-13:00 fade core; 14:00-15:20 lane).
3. Gap relation (never fade gap-ups; gap-down names are the short-fade universe; trade WITH 2%+ gaps).
4. Distance from open / high / low in daily-ATR units.
5. Point-in-time SPY tape (SPY since 09:50, SPY 30-min return) — skip shorts into a rising tape, longs into a
   falling hour, except the explicit "flush" long which buys a falling 30 min (S4 evidence).
6. Range room for fades: time exits / wider stops beat the tight stop on extended names.
7. House exits: t1s1 (t05s1 for dip buys), flat by 15:50, max hold <= 45 min.
8. Avoid lists: RSI5 < 25 shorts, gap-up shorts, near-SMA20 shorts, 15-min rvol bursts, longs while SPY is -0.3..-0.75%
   from the open (except the S4 flush definition), opening entries, narrow per-setup windows, day-type forecasts.

## 1. Data, split, locked block
- Signals: lab frames research/history2y/data/frames (5-min decision bars 09:50-15:00 ET bar close, 1,226 symbols,
  survivorship bias — today's symbol list; flatters longs, noted in every report). Exits walked on 1-minute bars
  (data/cache_hist/1Min) exactly as research/ultimate_1119/benchmark/bench.py (stop first, then target; gap-through
  at the worse of open/stop; flat 15:50 for candidates).
- **FIT** = all open sessions before 2024-11-01 (2024-10) plus 2025-03-01..2025-09-30.
- **CHECK** = 2025-10-01..latest cache session (2026-11-04 at time of writing). Scored once per candidate (sec. 5).
- **LOCKED** 2024-11-01..2025-02-28: never read or scored. pyarrow filters exclude it; every frame, trade list and
  1-minute load asserts no date in the block; MCF_HIST_ALLOW_LOCKED is never set.
- Costs: LR8 research basis (mcf.research.gates; same as the benchmark): entry 1c + 1 bp x time-of-day multiplier;
  exit 1c + 1 bp except target limit fills; +2c on stops; x3 extended tier. Borrow fees not modelled (intraday;
  caveat). ETB flag is today's universe.csv (caveat).

## 2. Common chassis (every candidate unless its spec says otherwise)
- **Intake U:** price >= $10 at the decision bar; point-in-time ADV20 >= $20M (frames `adv20`, prior sessions);
  |gap| < 20%; atr_d known; R = 0.25 x atr_d (prior-day daily ATR); **cost_r <= 0.10** (LR8 round-trip estimate at
  the decision bar / R). ETFs allowed unless stated.
- **Point-in-time features only:** everything from 5-min bars closed at the decision bar plus daily bars of earlier
  sessions. ATR-unit distances: from_open_atr = (close - open_0930)/atr_d; off_hod_atr = frames dist_hod_atr;
  lod_atr = dist_lod_atr. SPY: spy_s950 = SPY close / SPY 09:50 bar close - 1; spy_r30 = SPY close / SPY close 6 bars
  earlier - 1; spy_s930 = SPY close / SPY 09:30 open - 1; spy_r60 = 12-bar return. All at the same bar close.
- **Entry:** at the decision 5-min bar close (market, entry cost applied). One open lot per symbol per candidate.
- **Refire:** after an exit, the same symbol may refire for the same candidate only after 30 min; max 2 entries per
  symbol per session per candidate.
- **Day cap:** at most 30 entries per candidate per session (first by time; ties by ADV20 desc). Purpose: limit
  crash-day dominance (the 2025-04-03..04-09 week). The uncapped version of each fit-selected config is reported as a
  diagnostic and counted (10 extra configs), never used for selection or the bar.
- **Flat:** every lot closed by 15:50 at the latest (time exit or flatten, whichever first). No entries after 15:20.
- **Stops / targets:** 1R stop = 0.25 x atr_d unless the config says "TX" (time exit with a catastrophic 2R stop).
  t1s1 = +1R limit / -1R stop; t05s1 = +0.5R / -1R. "cap N" = max hold N minutes.

## 3. Candidates (10) and pre-declared grids

### ULT-01 gap-down pop fade short ("Cell A core") — SHORT, midday
Thesis: gap-down names that bounce into overbought between 11:00 and 13:00 roll back over; the condition carries the
edge across 53 live setups (+0.231 live at 11:00-13:00, +0.125 w/o best day, both halves), L3-fromopen was the best
live setup, and K6/K11 on the fit half kept their sign. Before 11:00 the same rule loses.
Rule: U; gap <= -1.5%; RSI5 (5-min) >= RSI_MIN and < 90; lod_atr >= 0.5 (a real pop: close at least 0.5 daily ATR
above the low of day); spy_s950 <= +0.15%; sma20_dist_pct not within +-1.5%; window W.
Grid (8): W {1100-1300, 1100-1500} x RSI_MIN {60, 70} x exit {t1s1 cap45, TX45}.
Names: 01a W13-R60-T, 01b W13-R60-X, 01c W13-R70-T, 01d W13-R70-X, 01e W15-R60-T, 01f W15-R60-X, 01g W15-R70-T, 01h W15-R70-X.

### ULT-02 tape-flush washout long ("S4") — LONG, mid/late morning to afternoon, falling tape
Thesis: when SPY drops >0.3% in 30 min, names already washed out snap back with the tape (S4 ex-April +0.189R, every
ex-April month positive, +0.15R over a same-moment control). Timed exit beats the bracket.
Rule: U with cost_r <= 0.10; (from_open_atr <= -D1 OR off_hod_atr >= D2); spy_r30 < SPY_T; window 1030-1500.
Grid (12): SPY_T {-0.30%, -0.50%} x depth {A: D1 1.0 / D2 1.5, B: D1 1.5 / D2 2.0} x exit {TX30, TX45, t1s1 cap45}.
Names: 02a..02l in that order (SPY_T outer, depth middle, exit inner).

### ULT-03 RSI-collapse dip buy, broadened ("ST7 chassis") — LONG, all day
Thesis: ST7 (RSI14 crosses below 50, RSI14 <= 30, down > 1% from open, 19-bar buy pressure > 0) is the best check-half
setup in the benchmark (+0.084, 3.1/session) and the only long the live record and 2 years agree on besides NM-ETF.
Broadening the intake with the cost filter instead of ADV >= $95M should raise volume; the falling-hour guard
removes the "longs into a falling SPY" losers.
Rule: U; RSI14 crosses below 50 within the last 3 bars and RSI14 <= RSI_MAX; fromOpen <= -1.0%; buyPressure > 0;
NOT (spy_s930 between -0.75% and -0.30% AND spy_r30 < 0); window 1015-1500.
Grid (8): RSI_MAX {30, 35} x ADV floor {$20M, $95M} x exit {t1s1 cap45, TX45}.
Names: 03a..03h (RSI_MAX outer, ADV middle, exit inner).

### ULT-04 down-tape pop fade short — SHORT, regime specialist (down sessions)
Thesis: short fades earn +0.15..+0.27R on down sessions and lose on up sessions; the point-in-time version of "down
session" (SPY already below its open) plus a weak name (below SMA20) and an overbought pop is the in-day part that
held. No gap-ups, no oversold shorts.
Rule: U; spy_s930 <= SPY_T and spy_r30 <= 0; gap <= +0.5%; sma20_dist_pct <= -1.5%; RSI5 >= RSI_MIN and < 90;
window 1030-1430.
Grid (12): SPY_T {-0.30%, -0.50%} x RSI_MIN {70, 80} x exit {t1s1 cap45, TX30, TX45}.
Names: 04a..04l (SPY_T outer, RSI middle, exit inner).

### ULT-05 with-the-gap continuation — LONG and SHORT, morning to early afternoon
Thesis: gap is the second most persistent condition; trading WITH a 2%+ gap beats fading it in both halves. Enter on a
pullback that holds the gap side of VWAP, with the tape not against the trade.
Rule: U; long if gap >= G and close > VWAP and vwapDistPct <= 0.5 x atrPct (near VWAP) and buyPressure > 0 and
spy_s950 >= -0.15%; short mirror (gap <= -G, close < VWAP, within 0.5 x atrPct, buyPressure < 0, spy_s950 <= +0.15%);
RSI5 not < 25 for shorts; window W.
Grid (8): G {2%, 3%} x W {1015-1300, 1015-1400} x exit {t1s1 cap45, TX45}. Both sides always together; side split
reported as a diagnostic.
Names: 05a..05h (G outer, W middle, exit inner).

### ULT-06 late morning-turn long — LONG, 10:30-12:00
Thesis: a new post-09:50 low followed by a reclaim around 11:00 is the "morning turn" (SPY +15 bps at +90 min,
t 3.1, both halves t >= 2.1); applied per name with the tape turning too.
Rule: U; the name printed a new low of day after 09:50 within the last 6 bars; now lod_atr >= RCL (reclaimed off
that low); fromOpen < 0; rsiSlope > 0; SPY close above its own lowest 5-min close since 09:50 by >= 0.10%; window W.
Grid (8): W {1050-1130, 1030-1200} x RCL {0.3, 0.5} x exit {TX30, TX45}.
Names: 06a..06h (W outer, RCL middle, exit inner).

### ULT-07 afternoon volatile dip buy ("NM-ETF WB4 chassis, broadened") — LONG, 14:00-15:15
Thesis: the late-day volatile dip buy is the only long positive live, on replay and on 2 years (+0.130R, plateau);
broadening from the ETF list to all high-ATR names under the cost filter raises volume. Falling-hour guard kept.
Rule: U; atrPct >= A_MIN; from_open_atr <= -DROP; buyPressure > 0 and RSI5 crossed up through 30 in the last 2 bars;
spy_r60 > -0.40%; window 1400-1515.
Grid (8): A_MIN {3, 4} x DROP {1.0, 1.5} x exit {t05s1 cap45, TX45}.
Names: 07a..07h (A_MIN outer, DROP middle, exit inner).

### ULT-08 afternoon overbought roll-over short — SHORT, 14:00-15:20
Thesis: 14:30-15:00 is the least-bad live block (-0.007) and the owner's "overbought name rolling over". Extension
precursors raise swing rates but also adverse moves, so: no gap-ups, require the roll-over to have started (RSI5
slope down, upper wick), tape not rising, short time exit.
Rule: U; gap <= +0.5%; from_open_atr >= RUN; RSI5 on the previous bar >= RSI_MIN and RSI5 now lower (rsiSlope < 0);
upper_wick > 0; spy_r30 <= 0; window 1400-1520.
Grid (8): RUN {1.5, 2.0} x RSI_MIN {80, 85} x exit {TX20, TX30}.
Names: 08a..08h (RUN outer, RSI middle, exit inner).

### ULT-09 failed-VWAP-reclaim short on a weak tape — SHORT, 10:30-15:30
Thesis: archive archetype 6 (failed VWAP reclaim with the SMA trend layer, down tapes). Weak names (below SMA20,
below open) that poke back above VWAP and fail are shorted only while SPY is not rising.
Rule: U; gap <= +0.5%; fromOpen < 0; sma20_dist_pct <= -1.5%; the name closed above VWAP on one of the previous 3
bars and now closes below VWAP; RSI5 >= 40; spy_s950 <= S_T; window W.
Grid (8): S_T {-0.20%, 0.00%} x W {1030-1400, 1030-1520} x exit {t1s1 cap45, TX45}.
Names: 09a..09h (S_T outer, W middle, exit inner).

### ULT-10 regime-switch book (composite) — LONG and SHORT, all day
Thesis: no single mechanism works in every market; a point-in-time SPY state switch routes each 5-min bar to the
mechanism that fits the tape, so the book trades on up, flat and down sessions.
Rule at each decision bar, using spy_s930 and spy_r30 only:
- spy_r30 < -T (flush) -> ULT-02 rule; else spy_s930 <= -T -> ULT-04 and ULT-09 rules;
- spy_s930 >= +T -> ULT-03, ULT-05 (long side) and ULT-07 rules;
- otherwise (flat) -> ULT-01, ULT-06 and ULT-08 rules.
Day cap 30 for the whole book; one lot per symbol across the book.
Grid (4): T {0.30%, 0.50%} x component configs {first-listed config of each component (a), fit-selected config of
each component (b)}. (b) depends only on fit results, so it stays pre-registered.
Names: 10a T30-first, 10b T30-fitsel, 10c T50-first, 10d T50-fitsel.

### Not built (and why)
- Earnings reaction-day continuation (EARN-GO): no point-in-time earnings calendar in the 2-year cache; a gap/volume
  proxy would just be ULT-05. Left for a round with an earnings source.
- Fading gap-ups, opening entries, relative-value / hedged trades, day-type gates, generator output, CWT variants,
  tight stops: proven not to work (evidence_archive.md).

## 4. Configuration count
| Candidate | configs |
|---|---|
| ULT-01 | 8 |
| ULT-02 | 12 |
| ULT-03 | 8 |
| ULT-04 | 12 |
| ULT-05 | 8 |
| ULT-06 | 8 |
| ULT-07 | 8 |
| ULT-08 | 8 |
| ULT-09 | 8 |
| ULT-10 | 4 |
| Uncapped diagnostics (1 per candidate) | 10 |
| **Total** | **94** |
Plus random-entry controls (one per candidate: same symbol-sessions and decision times as the fit-selected config's
signals, random bar within the window, same side and exit) — reported, not counted as candidates. Prior evidence
work in this folder: 574 configs (live 230, movehunt long 104, short 240) — reported alongside.

## 5. Selection and scoring order
1. Score all 84 grid configs on **FIT only**.
2. Per candidate, the **fit-selected config** = highest fit total R among configs with >= 2 trades/session on fit
   (ties: fewer conditions / first listed). If none reaches 2/session, the highest fit total R config is still
   carried and can at best be TIER B. Ranking is by total R, never by avg R/trade.
3. Freeze the fit-selected configs (write fitsel.json with a timestamp) **before** loading any check data.
4. Score the fit-selected config of each candidate on **CHECK once**. That single number decides the tier.
5. Only after step 4: score the full grids on check as a plateau diagnostic (reported, never used to re-select).

## 6. DEPLOY BAR (pre-registered)
- **TIER A** (deployable to a testing arena; deployment itself follows the normal rules and owner approval):
  check avg R after costs > 0 AND check avg R without best day > 0 AND fit avg R > 0 AND >= 2.0 trades/session on
  check (all check sessions in the denominator) AND no look-ahead (code review of the feature build).
- **TIER B** (near miss, next round only, NEVER deployed): fit avg R > 0 AND check avg R > -0.02.
- Everything else: FAIL, reported with its numbers.
- **Benchmark (headline goal, does not change the tier):** a TIER A candidate "beats the current best" if its check
  R/session > +0.262 AND check avg R w/o best day > +0.073 (ST7-FD on the same pipeline, the best benchmark setup;
  NM-ETF-late-dip +0.049 R/session, +0.039 w/o best day, is second).

## 7. Reported for every candidate (fit and check)
trades, trades/session, win rate, avg R, avg R w/o best day, best-day share (1-day tag at >= 50%), total R,
R/session, worst day, SPY up/flat/down avg R (SPY 09:30->15:59 +-0.30%, end-of-day label used ONLY for reporting),
avg R without 2025-04-03..04-09 (fit), check first-half / second-half avg R, random-control avg R, side split
(ULT-05, ULT-10), median hold, configs tried. Rule changes inside any live window are noted per CLAUDE.md.
Underestimate rather than overestimate: where a modelling choice is open, the costlier one is used.

## Amendments
(none)
