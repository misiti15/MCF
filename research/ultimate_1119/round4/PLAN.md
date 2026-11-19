# ultimate_1119 ROUND 4 — PRE-REGISTRATION (written 2026-11-19 ~08:45Z, before any round-4 scoring)

*Educational only — not financial advice. Research only: no setup, exit, config or account change. Nothing committed.*

Owner (2026-11-18): the best intraday setups from everything MCF has learned. That means many trades per session across
the universe, long and short, any market, and high avg R per trade AFTER COSTS. Entries from 09:50, flat by 15:50,
holds of about 5-45 min. Owner's words: "We have the usage. Do not stop until promising results show that would be
expected to beat our current best setups." And: "I don't want to force weak setups."

This file fixes the round-4 candidates, rules, grids, configuration count, split, selection rule and bars **before**
anything in round 4 is scored. Any change after the first fit run goes in only as a dated line under "Amendments", and
it is counted. No value below was chosen from a CHECK number, except where sec. 0.6 says so openly.

## 0. What rounds 1-3 taught and how round 4 uses it
1. **27 of 27 candidates fall short of the goal.** One is TIER A only on paper (ULT-20: +0.0075, t 0.55, below random
   trigger bars; not deployable). Four are TIER B (12, 20-weak, 22, 23). Volume is never the problem. The edge after
   costs is.
2. **Every price-pattern trigger on single stocks sits on a base that loses.** The base loses -0.02..-0.11R, partly
   before costs, and the trigger only shrinks the loss. Bases that pass a random-entry gate: 0 of 19 tried (ULT-15,
   ULT-24).
3. **The out-of-sample edges are narrow and specific.**
   - The WB4 dip on index/sector ETFs at 14:00-15:00 holds out of sample (+0.110 check, t 2.87), but trades only
     ~0.8/session.
   - ST7's one-bar RSI collapse on mega caps is positive in both halves (+0.326 fit / +0.139 check), but trades
     0.1-0.3/session.
   - Every broadening (hours, universe, ATR-scaled trigger, rankers) brings the result back to ~0.
4. **Mechanism read (round 3, kept): flow reverts, information does not.**
   - A sharp dip in a diversified basket or a mega cap is mostly liquidity or flow, and it reverts.
   - In a single name it is often information, and it does not revert.
   - Rounds 1-3 kept trading single-name price patterns *without knowing whether there was information behind them*.
5. **Round 4's main new ingredient is a point-in-time earnings calendar.** It was never used in rounds 1-3.
   - Source: `earnings_yf.parquet` from branch `origin/research-data` (commit c81186d9), copied to
     `round4/data/earnings_yf.parquet`, sha256 b80cdc46…e0dc. It holds 42,085 rows: symbol, report date,
     report hour / session (bmo / amc / dmh), EPS estimate, reported EPS and surprise %.
   - The `_lockedblock` sibling file is **never read**.
   - In the 1,193-name lab list the FIT half has 2,540 timed events, about **15 reaction-day names per session**
     (counted from dates only, no outcomes looked at).
   - This lets round 4 separate the **information** day (earnings reaction day = known news) from **no-news** moves.
     The literature predicts the two behave in opposite ways: news drifts, no-news reverts (Chan 2003, JFE;
     the PEAD literature).
   - The archive's strongest per-trade figure is earnings reaction-day continuation: EARN-GO +0.346R, n 121, t 3.63,
     but its earlier half is +0.045. The bdi/earnings daily study adds three points:
     - at the daily horizon, OPEN entries are flat;
     - after-hours drops continue (+0.68%, t 2.77);
     - "negative reactions on already-weak names bounce".
     The intraday 09:50+ question has never been tested on 2 years.
6. **Contamination disclosure (honest).** CHECK (2025-10-01..2026-11-04) has been read by three rounds.
   - **ULT-32 is CHECK-INFORMED.** It reuses the WB4 and ST7/ULT-23 parameters whose check numbers were seen.
   - **The earnings candidates (28, 29, 30, 31, 33, 35) are PARTLY CHECK-INFORMED.** No earnings intraday result was
     ever scored on this pipeline. But two of the idea sources overlap CHECK: EARN-GO's live record (Oct-Nov 2026) and
     the bdi/earnings daily valid2 split (2025-03..2026-10).
   - **ULT-34 is not check-informed.**
   - A CHECK-INFORMED pass is a screening result. It needs a forward look (recorded-quote replay + live Testing
     exposure) before anyone calls it "the goal".
7. **Statistical reality of BEATS.** Per-trade SD is ~0.84R and the design effect ~3.7.
   - At t 3.71, a check avg R of +0.10 needs ~3,600 check trades (~13.0/session). +0.15 needs ~5.8/session, and
     +0.25 needs ~2.1/session.
   - Earnings events cluster in ~40% of sessions, so their design effect may be higher still.
   - A low-volume candidate can be TIER A but not "the goal".
8. **Owner rule conflict, stated up front.** `config/default.yaml: earnings_blackout_days: 4` (owner 2026-10-07)
   blocks any trade within 4 trading days of earnings. Every earnings candidate trades *inside* that window by
   design.
   - **Even a BEATS result could not be deployed without an explicit owner exception.** The Deploy stage must ask;
     it must not assume.
   - ULT-34 and ULT-32 respect the blackout. ULT-34 by construction. ULT-32 applies it as an intake filter.

## 1. Data, split, locked block (unchanged)
- **Data:**
  - Signals: lab frames /home/user/MCF/research/history2y/data/frames (5-min decision bars 09:50-15:00 ET bar close,
    1,226 symbols; today's list = survivorship bias, which flatters longs).
  - Context: research/history2y/data/context (spy_fo, qqq_fo, breadth, qqq_vwap).
  - 1-minute bars: /home/user/MCF/data/cache_hist/1Min (read-only).
  - Daily bars: research/history2y/data/daily.parquet (date-filtered).
- **FIT** = 2024-10 + 2025-03-01..2025-09-30 (170 sessions). Sub-halves: A = 2024-10 + 2025-03..05 and
  B = 2025-06..09. Each sub-half holds earnings seasons: A has Oct-24, Apr/May-25; B has Jul/Aug-25.
- **CHECK** = 2025-10-01..2026-11-04 (276 sessions, the cache's last day). Scored ONCE per candidate, on the frozen
  fit pick.
- **LOCKED** 2024-11-01..2025-02-28: never read.
  - pyarrow filters on every load, `no_locked()` asserts on every frame, trade list, daily and 1-minute load, and on
    the earnings event table. MCF_HIST_ALLOW_LOCKED is refused.
  - Look-backs never reach into the block. ULT-34 needs closes for d-1 and d-2. ULT-30 needs RD-1. A 2025-03 session
    whose look-back would touch 2025-02 is dropped, not filled. The first usable ULT-34 session in March is 2025-03-05.
  - An earnings event whose reaction day, or any look-back day it uses, lies in the block is dropped.
- Frames end at the 15:00 bar, so windows are clamped to <= 15:00.

## 2. Round-4 chassis (= round-3 chassis; reuse benchmark/bench.py walk and the round-3 bt.py helpers)
- **Intake:** price >= $10 at the decision bar; point-in-time ADV20 >= the candidate floor; |gap| < 20%; atr_d > 0;
  cost_r <= the candidate cap. cost_r = LR8 round-trip cost for a stop exit / u, with u = 0.25 x atr_d unless a
  candidate sets m.
- **Entry** = OPEN of the 1-minute bar starting at the decision-bar close (the next tradable print), with LR8 entry
  cost. ULT-33's LMT configs are the only exception (sec. 3).
- **Earnings-day cost surcharge (bias fix, new):** on a reaction-day bar before 10:30, entry and exit costs are
  x1.5. Spreads are wider in the first hour of a news day.
- **Borrow fee (bias fix, raised for news days).**
  - Every short pays 1.2 bp of entry notional, or 3 bp if priced < $20.
  - A short in an earnings window (RD-1..RD+1) pays **5 bp** (8 bp if priced < $20).
  - Shorts only where easy_to_borrow = True (today's flag; caveat).
  - Never short leveraged or inverse ETFs.
- **Exits** walked on 1-minute bars as bench.py.
  - Stop first, then target. A stop gap-through fills at the worse of open and stop. A target fills at the limit
    with no exit cost. Stops pay +2c.
  - TX-45 = time exit at 45 min with a 2u catastrophic stop, R per 2u. Brackets tXsY are per u. Cap 45 min.
    Flat 15:50. No entries after 15:00.
- **Lots and caps:** one lot per symbol per candidate. Refire >= 30 min after the exit. Max 2 entries per
  symbol-session. Day cap 30 (first by time, ties by ADV20 desc) unless stated.
- **Universal filters:**
  - No short if gap >= +0.5% or RSI5 < 25.
  - No long while SPY is -0.30..-0.75% from its open AND spy_r30 < 0.
- **Forbidden columns:** frames win_*, r_*, *heat*. They are dropped before features and asserted absent.
- **Earnings event table (shared helper `round4/earn.py`, built once and reused by 28-31, 33-35).**
  - Reaction day RD = report date for `bmo`, or the next trading session for `amc`. `dmh` / `unknown` are excluded.
  - Repeats of a symbol within 10 sessions keep the first.
  - The table carries surprise_pct, clipped at +-100 (NaN = missing).
  - RD+1 = the next session after RD. "Earnings window" = RD-5..RD+1 (ULT-34's exclusion).
  - Point-in-time: report dates and sessions are scheduled weeks ahead, and the surprise is public before the RD open.
    Caveat: the table was fetched after the fact, so rare date revisions are not modelled.
  - Live implementability needs a report-hour source. The live mcf/data/earnings.py Nasdaq feed often lacks the hour;
    yfinance has it. This is noted for the Deploy stage.
- **Controls (reported, not counted):**
  - A same-name, same-session random bar with the same side and exit, giving signal minus random.
  - For the earnings candidates, a **non-earnings twin**: the same rule on gap names with no earnings in RD-5..RD+1.
    It shows whether "news" is what carries the result.

## 3. Candidates (8) and pre-declared grids
Expected trades/session are averaged over ALL sessions in the half. Earnings names are ~0 per session outside the
seasons.

### ULT-28 EARN-GO — earnings reaction-day continuation with the gap, LONG + SHORT (D5)
Thesis: the reaction day is the one day a single-name move is known to carry information. Information moves drift
(PEAD). The archive's EARN-GO is the highest per-trade figure. Enter only while the gap is holding, after 09:50.
- **Universe:** RD names, ADV20 >= $30M, price >= $10, cost_r <= 0.08, |gap| >= G, |gap| < 20%. Side s = sign(gap).
- **Window:** 09:50-12:30 (archive core block; information is absorbed early).
- **HOLD trigger:** the first bar >= 09:50 on which all three hold:
  - close is on the s side of VWAP;
  - s x fromOpen >= 0 (the gap is not being given back);
  - RSI5 <= 85 (long) or >= 25 (short).
- **PUSH trigger:** the HOLD conditions plus a new session extreme in direction s on this bar. That is
  dist_hod_atr <= 0.02 (long) or dist_lod_atr <= 0.02 (short), with the previous bar not at the extreme.
- **Surprise S:** "agree" requires sign(surprise_pct) = s (missing = excluded); "any" ignores it.
- **Exit:** t1s1 (u = 0.25 dATR) cap 45, or TX-45.
- **Grid (12):**
  - 28a-28h = G {3%, 5%} x entry {HOLD, PUSH} x S {agree, any}, all with t1s1. Order: G outer, entry, S inner.
  - 28i-28l = G {3%, 5%} x entry {HOLD, PUSH}, S any, TX-45.
- **Expected trades/session:** G3 ~3-6; G5 ~2-4; "agree" ~0.6x of that.
- **Tags:** PARTLY CHECK-INFORMED (sec. 0.6). Owner blackout conflict (sec. 0.8).

### ULT-29 EARN-CONFL — gated confluence on an earnings reaction-day base, LONG + SHORT (D3)
Thesis: round 1-3 lesson. First prove the base, then stack triggers that each beat random in BOTH fit sub-halves.
The reaction-day with-gap base is the first base with a reason to be >= 0 by itself, because it carries information.
- **Bases** (decision bars 10:00-13:00):
  - EB-L: RD names with gap >= +2%, ADV20 >= $30M, cost_r <= 0.08, universal long filter. Long.
  - EB-S: RD names with gap <= -2%, the same intake, ETB, RSI5 >= 25. Short.
- **Base gate (FIT only, before any trigger is scored).**
  - Draw one random base-eligible bar per symbol-session (seed 1119) and score it through the chassis under both
    TX-45 and t1s1.
  - The base opens for a config only if its random avg R >= 0 in BOTH sub-halves A and B under that config's exit.
  - 2 bases x 2 exits = 4 evaluations, counted.
- **Triggers** (long; short mirrored):
  - T1 VWAP-hold pullback: bar low within 0.15 x atr_d of VWAP and close > VWAP.
  - T2 new session high since 09:30 (dist_hod_atr <= 0.02, previous bar not).
  - T3 RSI5 reset: RSI5[prev] <= 40, RSI5 > 40, and close > VWAP.
  - T4 with-direction volume bar: volumeRatio >= 2 and close > previous close.
- **Trigger gate (FIT only, after the base gate).** Per open base and trigger, signal minus same-base random avg R
  (TX-45) must be >= 0 in both sub-halves. 4 x 2 = 8 evaluations, counted. Triggers that fail are dropped and
  reported.
- **Confluence:** enter when at least C of the surviving triggers of that side have each been true within the last W
  bars, counting the decision bar. If fewer than C triggers survive, that base trades nothing.
- **Grid (8):** W {1, 3} x C {2, 3} x exit {t1s1 cap45, TX-45}. Names 29a..29h, in the order W, C, exit.
- **Expected trades/session:** C2 ~1.5-4, C3 ~0.5-1.5. If the base gate fails, the result is "no candidate"
  (as ULT-24), reported with an ungated diagnostic.
- **Tags:** PARTLY CHECK-INFORMED. Blackout conflict.

### ULT-30 EARN-DAY2 — day-after-earnings continuation, LONG + SHORT (D5)
Thesis: PEAD is strongest in the first days. On RD+1 the reaction is fully known before the open (point-in-time), and
the day-2 tape decides whether it keeps going.
- **Event:** session RD+1 for every RD event. REACT = close(RD) / close(RD-1) - 1 minus SPY's same move, from daily
  bars dated <= RD. Require |REACT| >= T. Side s = sign(REACT).
- **Intake:** ADV20 >= $30M, cost_r <= 0.08. Window 09:50-12:30.
- **Rule** (first qualifying bar):
  - s x gap >= -0.5% (no reversal gap);
  - close on the s side of VWAP;
  - s x fromOpen >= 0;
  - RSI5 <= 85 (long) or >= 25 (short);
  - universal filters.
- **Grid (8):** T {4%, 8%} x side {both, long-only} x exit {t1s1 cap45, TX-45}. Names 30a..30h, in the order T, side,
  exit.
  - Long-only is pre-declared because of the daily evidence that shorts after negative reactions fail.
- **Expected trades/session:** both sides ~2-4 at T4; long-only ~1-2.
- **Tags:** PARTLY CHECK-INFORMED. Blackout conflict.

### ULT-31 EARN-AWARE RANK — learned ranker with information-state features, LONG + SHORT (D1)
Thesis: rankers failed because, on price features alone, they learn "volatile names" or "SPY is rising" (ULT-11, 19,
20, 21). This ranker gets features that measure *information state* (earnings window, surprise, report session) and
sign-stability selection against ULT-19's sign flips. It runs both on the whole liquid universe and on the
earnings-window rows only. This is the "swarm finds the factors" route with a new factor family.
- **Rows:** every (5-min decision bar 10:00-15:00, name, side). Two universes:
  - ALL: ADV20 >= $100M, cost_r <= 0.05, price >= $10.
  - EVT: names on RD or RD+1, ADV20 >= $30M, cost_r <= 0.08.
  - Universal filters apply. Shorts must be ETB and not leveraged or inverse funds.
- **Features (~34), s = +1 long / -1 short:**
  - ULT-20 base set: 5 time-block dummies; s x gap; s x from_open_dATR; s x vwap_dist_dATR; s x (RSI14 - 50);
    s x (RSI5 - 50); RSI2 <= 5 and >= 95 flags x s; s x di_diff7; atr_d%; cost_r; log10 ADV20; is_ETF;
    volumeRatio; s x spy_fo; s x spy_r30; s x qqq_fo; s x sector-ETF fromOpen (ULT-11 sector map).
  - Earnings features: e_RD, e_RD1, e_pre (report within the next 1-3 sessions), e_bmo;
    s x sign(surprise) x (e_RD or e_RD1); s x clip(surprise, +-30) / 30 x (e_RD or e_RD1); s x gap x e_RD;
    s x REACT x e_RD1.
  - Scaling: z-scored on the training fold, clipped +-5, NaN -> 0.
- **Target:** after-cost TX-45 R per 2u (LR8 both legs, surcharge and borrow included), winsorised +-4. This is a
  training proxy; scoring goes through the real chassis.
- **Models:**
  - RS = ridge, alpha 1e3, with **sign-stability selection**. Inside each training fold, refit on leave-one-month-out
    subsets. Keep only features whose coefficient sign agrees in >= 80% of the refits, then refit on the kept set.
  - GB = HistGradientBoosting(max_depth 2, max_iter 100, lr 0.05, min_samples_leaf 2000 [ALL] / 300 [EVT], l2 1.0,
    seed 1119).
- **Trading:**
  - Per name, take the better-scoring side and enter if score > tau_k.
  - At most 3 entries per bar; session cap 2k; TX-45 exit.
  - tau_k = the training in-sample constant giving k entries/session. For EVT this is computed over earnings-season
    sessions, so off-season sessions trade little.
- **Walk-forward inside FIT:** folds 2025-05..09, each trained on all earlier FIT months (as ULT-11 and ULT-20).
  "Fit" = pooled OOF. The final model is trained on all of FIT and frozen (weights / pickle / tau in fitsel.json)
  before any check feature is built.
- **Grid (8):** universe {ALL, EVT} x model {RS, GB} x k {3, 8}. Names 31a..31h, in the order universe, model, k.
- **Expected trades/session:** ~3 or ~8 (ALL); EVT ~1.5-3 or ~3-6 averaged over all sessions.
- **Tags:** PARTLY CHECK-INFORMED (EVT rows, earnings features). Blackout conflict (EVT, and ALL wherever earnings
  rows are picked).

### ULT-32 FLOW-DIP — dissection of ST7-FD and NM-ETF, plus a union sibling of their edge-carrying parts, LONG (D2)
**Part 1: dissection (FIT only; diagnostics, counted, never used to select).** Each ablation is scored on FIT through
the round-4 chassis.
- **ST7-FD (12 ablations):**
  - drop one layer at a time: cross-below-50, RSI14 <= 30, fromOpen <= -1%, buyPressure > 0 (4);
  - hour blocks 09:50-11:00 / 11:00-13:30 / 13:30-15:00 (3);
  - ADV tiers $95-300M / $300M-1B / >= $1B (3);
  - exits t05s1 / TX-45 (2).
- **NM-ETF WB4 (11 ablations):**
  - drop one layer at a time: dip, DI, falling-hour guard, ATR floor (4);
  - hour blocks 10:30-12:30 / 12:30-14:00 / 14:00-15:00 (3);
  - universe: WB4 list vs other basket ETFs; leveraged vs unleveraged (2);
  - exits t1s1 / TX-45 (2).
- Benchmark check-trade splits along the same cuts are produced **only after** ULT-32's single check score, as
  description.
- Known before dissection, from published numbers:
  - ST7-FD is fit -0.132 / check +0.084, so its sign is not stable.
  - NM-ETF is fit +0.269 / check +0.052.
  - The parts that held in BOTH halves are (a) the basket universe at 14:00-15:00 for the WB4 dip and (b) the
    one-bar collapse on mega caps (ULT-23 M).
**Part 2: sibling = union of those two parts plus one volume step that keeps the "flow" property (index-weight
names only).**
- **Leg E (NM-ETF WB4, exact):** WB4 list (124), ADV20 >= $95M, cost_r <= 0.10, 14:00-15:00.
  Trigger: ret3 <= -0.75%, di_diff7 >= -5, ret12 >= -1.0%, atr_d% >= 3.6. Exit t05s1 cap45.
- **Leg M (ST7 collapse on large caps):** non-fund stocks with point-in-time ADV20 >= A and price >= $20,
  cost_r <= 0.08, 10:15-15:00.
  Trigger: RSI14[prev] >= 50 and RSI14 <= RMAX in one bar; fromOpen <= -min(1.0%, 0.30 x atr_d%);
  buyPressure(19) > 0; universal long filter. Exit t1s1 cap45.
- **Leg D (WB4-A dip on the same large caps, 14:00-15:00 only):** ret3 <= -0.21 x atr_d%, ret12 >= -0.28 x atr_d%,
  di_diff7 >= -5. Exit t05s1 cap45.
- **Book rules:** the earnings blackout (RD-4..RD+4) applies to legs M and D as an intake filter, as live. One lot
  per symbol across legs. Day cap 30.
- **Grid (8):** A {$1B, $500M} x RMAX {30, 35} x leg D {off, on}. Names 32a..32h, in the order A, RMAX, D.
- **Expected trades/session:** 1.0-1.5 (32a) to 2-3.5 (32h). Only the larger cells can be eligible.
- **Tags:** CHECK-INFORMED (WB4 / ST7 / ULT-23 parameters and universes).

### ULT-33 EARN-GEO — cost geometry on reaction-day moves: wider R, 2:1 target, limit entry, LONG + SHORT (D4)
Thesis: rescaling R did not help on ordinary bars (ULT-16, ULT-25), because the edge there is a fixed few bp. On a
reaction day the move is 2-4 daily ATRs, so the opportunity scales with R while costs do not. This is the one place
where wider R and a 2:1 target should pay.
- **Event set (fixed):** RD names, |gap| >= 3%, with-gap side, HOLD trigger as ULT-28, S any, window 09:50-12:30,
  ADV20 >= $100M (the high-liquidity tier), cost_r(m) <= 0.08.
- **Unit:** Ru = m x atr_d.
- **Exits:** t1s1 = +1 Ru / -1 Ru; t2s1 = +2 Ru / -1 Ru. Cap 45, flat 15:50. R is reported per actual risk and per
  0.25-dATR unit.
- **Entry:**
  - MKT = next-minute open.
  - LMT = limit at VWAP + s x 0.05 x atr_d, valid 15 min. Filled when a 1-minute bar trades through the limit, at
    the limit, with LR8 entry cost still charged. Unfilled = no trade, and the fill rate is reported.
- **Grid (12):** m {0.25, 0.5, 1.0} x exit {t1s1, t2s1} x entry {MKT, LMT}. Names 33a..33l, in the order m, exit,
  entry.
- **Expected trades/session:** MKT ~2-4; LMT ~1-2.5.
- **Tags:** PARTLY CHECK-INFORMED. Blackout conflict.

### ULT-34 NO-NEWS REVERSAL — day-2 fade of an extreme prior-day move with no earnings, LONG + SHORT (D5)
Thesis: the mirror of the earnings candidates. A large one-day move with no scheduled news is more likely a liquidity
shock, and those revert (Chan 2003). It respects the owner blackout by construction. It covers both tapes because
the side comes from the name's own move, not from SPY.
- **Event at session d:** r1 = close(d-1) / close(d-2) - 1, from daily bars dated < d. Require
  |r1| >= K x atr_d% (atr_d as known at d). Require no earnings event for the symbol in d-5..d+1 (scheduled dates
  only). Side s = -sign(r1).
- **Intake:** ADV20 >= $50M, cost_r <= 0.08, |gap| < 20%. Window 10:00-13:00.
- **Rule** (first qualifying bar, refire as chassis):
  - s x gap <= +0.5 x |r1| (today has not already fully reverted at the open);
  - close on the s side of VWAP;
  - confirm F: "V" = VWAP side only; "VO" = VWAP side AND s x fromOpen >= 0;
  - universal filters.
  - Shorts must be ETB and pay borrow. No shorts of leveraged or inverse funds. Leveraged or inverse ETFs are
    excluded from events.
- **Grid (8):** K {2.0, 3.0} x F {V, VO} x exit {t1s1 cap45, TX-45}. Names 34a..34h, in the order K, F, exit.
- **Expected trades/session:** K2 ~4-10; K3 ~1.5-4.
- **Tags:** NOT check-informed.

### ULT-35 EARN-FAIL — failed earnings gap: trade the reclaim against the gap, LONG + SHORT (D5)
Thesis: when a reaction-day gap fails (price back through VWAP and the open), the market has rejected the news
reading. Trapped gap traders unwind. Daily evidence that fits this: "negative reactions on weak names bounce";
gap-up-then-fade *long* is +0.30% at H5, a caution for the short side, which is reported separately. This is
mutually exclusive with ULT-28 on any bar (holding vs failing).
- **Universe:** RD names, ADV20 >= $30M, cost_r <= 0.08, |gap| >= G. Window 10:15-13:30.
- **Long (gap-down reclaim):** close > VWAP AND fromOpen >= D x atr_d, on the first such bar (previous bar not).
- **Short (gap-up failure):** close < VWAP AND fromOpen <= -D x atr_d, first such bar; ETB; RSI5 >= 25;
  earnings-window borrow.
- **Grid (8):** G {3%, 6%} x D {0, 0.5} x exit {t1s1 cap45, TX-45}. Names 35a..35h, in the order G, D, exit.
- **Expected trades/session:** ~1-3 (G3), ~0.5-1.5 (G6).
- **Tags:** PARTLY CHECK-INFORMED. Blackout conflict.

### Not built (and why)
- Plain with-gap continuation without news (ULT-05 / ULT-26 failed). It appears only as the non-earnings twin control.
- Index-level 3x-ETF lanes: random entries on the same days earn the same.
- Sector lead-lag (ULT-17: the lag closes within a minute).
- XS momentum / reversal at fixed times (ULT-18) and periodicity (ULT-27).
- Limit entries on ordinary bars (ULT-16).
- WB4 at wider hours or wider universes (ULT-12, ULT-22).
- Any ranker over price features alone (ULT-11, 19, 20, 21).
- Every failed round-1-3 candidate unchanged.

## 4. Configuration count
| Candidate | configs |
|---|---|
| ULT-28 EARN-GO | 12 |
| ULT-29 EARN-CONFL | 8 grid + 4 base gates + 8 trigger gates = 20 |
| ULT-30 EARN-DAY2 | 8 |
| ULT-31 EARN-AWARE RANK | 8 |
| ULT-32 FLOW-DIP | 8 grid + 23 dissection ablations = 31 |
| ULT-33 EARN-GEO | 12 |
| ULT-34 NO-NEWS REVERSAL | 8 |
| ULT-35 EARN-FAIL | 8 |
| Bias diagnostics (fit pick re-scored with signal-close fill, no borrow, no surcharge; one per candidate) | 8 |
| **Round 4 total** | **115** (72 grid + 43 gates / ablations / diagnostics) |
| Cumulative before round 4 (round 1 682 + round 2 incl. ULT-15 extras = 779, + round 3 101 + ULT-24's 1 extra) | 881 |
| **Cumulative N after round 4** | **996** |

sqrt(2 ln 996) = **3.716**, so the BEATS t floor is max(1.5, 3.716) = **3.72**. It is recomputed with the final N if
an amendment adds configurations.
- Random-entry controls and non-earnings twins are reported, not counted. ULT-29's gates are counted, because they
  decide something.
- Walk-forward folds inside ULT-31 are part of each named config.

## 5. Selection and scoring order (as rounds 2-3)
1. Score every grid config on FIT only. ULT-31 uses walk-forward OOF inside FIT. ULT-29 runs its gates first.
   ULT-32's dissection may run at any time on FIT; it never selects.
2. Per candidate, the fit pick is the highest **fit total R minus the best fit day's R** among configs with >= 2.0
   trades/session on fit. Ties go to fewer conditions, then the first listed.
   - If no config reaches 2/session, the best by the same score is carried, but it cannot reach TIER A.
   - Never rank by avg R per trade.
3. Freeze fitsel.json (UTC timestamp, sha256 of bt.py, the module and round4/earn.py) BEFORE any check frame,
   feature, event row or trade is built.
4. Score the fit pick on CHECK once. That single result decides the tier and the BEATS test.
5. Only then run the full grid on check as a plateau diagnostic (never used to re-select), the bias diagnostic, the
   non-earnings twin and ULT-32's check-side dissection splits.

## 6. BARS (fixed now)
- **TIER A:** all of the following.
  - check avg R > 0;
  - check avg R w/o best day > 0;
  - fit avg R > 0 (ULT-31: OOF);
  - >= 2.0 trades/session on check, with all 276 sessions in the denominator;
  - no look-ahead: code review including forbidden columns, a point-in-time truncation test, and an earnings-table
    test that features at RD use no field dated after the bar.
- **BEATS BENCHMARK (the goal):** TIER A plus all of the following.
  - check avg R > +0.0836;
  - check avg R w/o best day > +0.0734;
  - check total R/session > 0;
  - worst check day / trades per traded session >= -2.152;
  - day-clustered t of check avg R >= max(1.5, sqrt(2 ln N_cumulative)) = **3.72 at N = 996**.
    Day-clustered t = avgR / SE, with SE = sqrt( sum over sessions d of ( sum_{i in d} (r_i - avgR) )^2 ) / n_trades.
- A CHECK-INFORMED or PARTLY CHECK-INFORMED candidate that meets BEATS is reported as "meets the bar,
  (partly) check-informed" (sec. 0.6).
- Every earnings candidate additionally carries "**needs owner blackout exception**" (sec. 0.8). The Deploy stage
  cannot deploy it without that.
- Only BEATS candidates are "the goal". TIER A non-beaters may be deployed only if clearly positive (owner: no weak
  setups); the Deploy stage decides with the skeptic. Everything else is FAIL. TIER B (fit > 0 and check > -0.02)
  is reported as a near miss and never deployed.

## 7. Reported for every candidate (fit and check)
- **Volume and result:** trades, trades/session, win, avg R (actual risk and 0.25-dATR units), avg R w/o best day,
  best-day share (1-day tag at >= 50%), total R, R/session, worst day, worst day / trades per traded session,
  day-clustered t.
- **Splits:**
  - SPY up/flat/down avg R (end-of-day label, reporting only);
  - **avg R without 2025-04-03..04-09** (fit; check has no such dates);
  - check first and second half;
  - fit sub-halves A/B;
  - side split;
  - earnings-season vs off-season sessions (earnings candidates).
- **Controls and diagnostics:** same-name random control and signal minus random; non-earnings twin (earnings
  candidates); median hold; exit mix; bias diagnostic.
- **Tags and counts:** CHECK-INFORMED / blackout tags; configs tried.
- Long results carry the survivorship caveat. Signal minus random is the survivorship-neutral read.

## 8. Rule-change context (owner 2026-11-02)
- Both 2-year halves are scored with one fixed rule set (today's LR8 costs and the round-2/3/4 chassis), so no live
  rule change falls inside them.
- The live earnings blackout (4 days, owner 2026-10-07) has been in force through the whole live record. That is why
  no live setup has an earnings-day track record to compare with; EARN-GO's figure comes from research, not from
  live accounts.
- Live figures quoted in earlier rounds span the ledger changes listed in RESULTS.md:
  - 11-12 LR8 cost model;
  - 10-28 Primary sizing;
  - 10-30 Testing cost filter;
  - 11-17 TSZ1 half-size lots / SPYEXIT;
  - setup moves.
- WB4 went live 2026-11-17 (Testing E), after the CHECK window.

## 9. Disk / hygiene
- ~4.7 GB free. No feature files on disk: ridge runs from accumulated X'X / X'y, and GB on an in-memory subsample of
  <= 2M rows (ALL) or all rows (EVT).
- Trade lists go in the scratchpad and are deleted after scoring. Only small json / csv.gz / md files go under
  round4/.
- The earnings table (470 KB) lives in round4/data/.

## Amendments
(none)

Educational only — not financial advice.
