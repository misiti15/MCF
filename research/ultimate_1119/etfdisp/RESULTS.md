Educational only — not financial advice

# ETFDISP: ETF late dip after high-dispersion days. Built for live, scored the normal way (2026-11-19)

Owner decision 2026-11-19 ~07:50 ET: "Added to testing as a new setup for live sessions. We have the slots available
currently." This is a build. The scores below are reported honestly, but they do not decide deployment: the owner
does. Nothing is committed here; the Deploy stage commits, and only after the 16:00 ET close. Earliest effective
session: **2026-11-20**.

Files:
- plan: `etfdisp/PLAN.md` (sha256 in PLAN.sha256; written 13:28Z, before any score);
- scoring: `etfdisp/score.py` and `etfdisp/stats.py`;
- every number: `etfdisp/results.json`;
- module: `research/ultimate_1119/modules/ETFDISP-late-dip-hidisp-long.py`;
- tests: `tests/test_etfdisp.py` (12 tests).

## In plain words
- **What it trades.** It is the late-afternoon ETF dip from WB4 (leg E of ULT-32, unchanged). It trades only on days
  after a session where stocks moved far apart from each other ("high dispersion"). The dispersion reading uses only
  yesterday's daily closes, so it is known before the open.
- **Threshold.** The cut-off is 2.6438%, the median of the three round-6 cut-offs. That rule was written down before
  scoring and has not been tuned.
- **Live wiring.** The live system now records each name's prior-day return in its pre-open data. It works out the
  dispersion once per session, and the setup reads it as a new opt-in context column, `disp_prev`. Live, the replay
  and the backtester all use the same function. If the value is missing, the setup does not trade.
- **Results, normal filter way (costs in, testing-account rules, 45-minute time exit as it will run live):**

  | Test | Avg R | Trades |
  |---|---|---|
  | 2024-25 fit | +0.250 | 202 |
  | 2025-26 check | +0.125 | 181 |
  | 2-year combined | +0.191 | 383 |
  | 2023-24 | +0.142 | 44 |

  It meets every pre-registered top-10 standard and is not "really bad". Treat this as a low bar: the top-10 medians
  are negative.
- **Caveats to read before the numbers:**
  1. **The gate has seen all three windows.** Each round-6 cut-off was picked on two of them. These are in-sample
     results; only live sessions are a fair test.
  2. **The fit result is mostly April 2025.** 175 of the 202 fit trades fall in that month, and one day (2025-04-10)
     gives 57% of the fit R. The check window is spread out (best day 17% of its R). 2023-24 has only 44 trades, and
     47% of that R comes from 2023-03-14.
  3. **In 2025-26 the gate removes trades that made money.** Leg E's check trades on low-dispersion days averaged
     +0.046R, so the gated setup earns less total R than ungated leg E (73.0R vs 88.1R over 2 years). It earns more
     per trade. The gate pays off only in a 2023-24-type market, where the trades it removes averaged −0.081R.
  4. **It duplicates live trades.** Every symbol-session it trades on T1 is also traded by the live WB4 copy
     (Testing E), and 73% by the Primary parent NM-ETF-late-dip. Under the job's ">= 70% overlap" duplicate rule this
     would be skipped. The owner's decision (1) overrides that rule, but the placement must avoid stacking the same
     ETF dips (see Deployment notes).

## The setup (frozen)
- **Leg E of ULT-32, unchanged:** `modules/ULT-32.py` is byte-identical to `round5/frozen/book_module__ULT-32.py`.
  The ETF list is identical to WB4's 124 names.
- **Entry rules:**
  - WB4 ETF list, ADV20 >= $95M;
  - bar close 14:00-15:00;
  - 15-minute return <= −0.75%;
  - +DI(7) − −DI(7) >= −5;
  - 60-minute return >= −1.0%;
  - daily ATR >= 3.597% of price;
  - cost_r <= 0.10;
  - price >= $10 and |gap| < 20%;
  - skip while SPY is −0.30..−0.75% from its open and falling over 30 minutes;
  - at most 2 per symbol-session, the 2nd at least 6 bars after the 1st.
- **Exit:** +0.5R target, −1R stop (R = 0.25 × daily ATR), 45-minute time exit.
- **Gate:** `disp_prev >= 2.6438`. `disp_prev` is the standard deviation (ddof 1, in %) of the prior session's
  close-to-close returns, each clipped to ±50%, over the names with ADV20 >= $95M through that session. It is NaN,
  so no trade, when fewer than 100 names qualify.
- **Parity with round 6.** `disp_prev` recomputed with the live function matches round6/gates.py `disp` on all 664
  shared dates (max difference 5e-6).
- **Universe parity.** 1,203 of the live universe's 1,204 names with ADV >= $95M (data/universe.csv) are in the
  history2y list. The live universe's 1% ATR floor changes the level by +0.4% (gate open share 53.4% → 53.7% on
  2025-26). So the live value and the backtest value describe the same thing.

## Live build (engine changes, all opt-in; no other setup changes)
| File | Change |
|---|---|
| `mcf/data/priors.py` | `Prior.prev_ret` (default NaN): the prior session's close-to-close return, from the daily bars the pre-open prep already fetches |
| `mcf/strategies/lab_context.py` | new opt-in daily market column `disp_prev` (by name only; `context: true` unchanged). `cross_dispersion`, `market_daily`, `market_daily_cols`. Carried in `index_priors["__market__"]` |
| `mcf/strategies/setups.py` | `LabStrategy.market_daily_cols` |
| `mcf/execution/runner.py` | computes `disp_prev` once per session from the universe priors (`_load_index_priors`); value shown in `health["market_daily"]` |
| `mcf/backtest/engine.py` | the same column from each symbol's daily history (prior-session return, prior ADV20) |

The replay fast path and shadow use `runner.index_priors`, so they inherit the value. Replay priors pickled before
this change have no `prev_ret`, which reads as NaN: the setup does not trade in those replays (fail safe).

**Tests.** `tests/test_etfdisp.py` has 12 tests:
- the column is opt-in;
- the dispersion definition, including the < 100 names and missing `prev_ret` cases;
- `_daily_part` records `prev_ret`;
- the runner computes the value once per session;
- the backtester supplies the value from the prior session;
- the module under the live `LabStrategy` fires on a fixture ETF dip only when `disp_prev >= 2.6438`. Cases 3.0 and
  2.6438 fire; 2.64, NaN and missing do not. The signal is decided at the 14:35 bar close with a 45-minute time stop;
- non-list symbols are refused;
- the exact YAML block below builds through `build_strategies`.

The full suite passes: 819 passed, 1 skipped (before the YAML test was added; that file now has 12 passing tests).

YAML block for the destination testing account (the Deploy stage picks the account):
```yaml
  ETFDISP-late-dip-hidisp-long:
    # NEW setup, owner 2026-11-19 ~07:50 ET "Added to testing as a new setup for live sessions"; effective session 2026-11-20.
    # Leg E of ULT-32 (= WB4 ETF late dip + ULT-32 intake) only after high prior-day cross-sectional dispersion
    # (disp_prev >= 2.6438, frozen). research/ultimate_1119/etfdisp/RESULTS.md. Derived from NM-ETF-late-dip-di-long / WB4.
    enabled: true
    type: lab
    module: research/ultimate_1119/modules/ETFDISP-late-dip-hidisp-long.py
    symbols: module
    min_adv: 95000000
    window: [1400, 1500]
    geom: t05s1
    context: [spy_fo, disp_prev]
    refire: true
    refire_cooldown: 0
    time_stop_min: 45
    time_stop_min_r: 99
    scale_out_r: null
    tags: [ultimate_1119, etf, "parent:NM-ETF-late-dip-di-long"]
```

## Scores, the normal filter way
Engine: `top10/bench10.py`, unchanged.
- **Signals:** the live mask on the lab frames (T1) or on frames built from cache_fresh (T2). Window 14:00-15:00,
  min_adv on ADV20, refire chain with cooldown 0 (the module thins).
- **Exits:** 1-minute walk from the decision-bar close, stop first, target traded through by $0.01.
- **Costs:** LR8.
- **Book:** testing-arena rules (cap 100, 0.15R cost filter, <= 3 lots per symbol, price >= $5).
- **Exit variants:** "cap45" is the setup as it will run (45-minute time exit). "nocap" is the bench10 walk as is.
- **Sessions:** T1 fit 170, check 276, combined 446 (2024-10 + 2025-03..2026-11-04); T2 427
  (2023-01-03..2024-09-13).

### ETFDISP (cap45, as it will run)
| Test | Trades (/session) | Traded sessions | Win | Avg R | Avg R w/o best day | Best-day share | Total R (/session) | Worst day | Day-t | SPY up / flat / down avg R |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 fit | 202 (1.19) | 21 | 78% | **+0.250** | +0.169 | 57% **1 day** (2025-04-10) | +50.4 (+0.297) | −1.15 | 3.84 | +0.186 / +0.389 / +0.292 |
| T1 check | 181 (0.66) | 81 | 61% | **+0.125** | +0.108 | 17% | +22.6 (+0.082) | −2.27 | 2.95 | +0.104 / +0.098 / +0.162 |
| T1 combined | 383 (0.86) | 102 | 70% | **+0.191** | +0.143 | 40% | +73.0 (+0.164) | −2.27 | 4.00 | +0.154 / +0.112 / +0.243 |
| T2 | 44 (0.10) | 20 | 68% | **+0.142** | +0.087 | 47% (2023-03-14) | +6.2 (+0.015) | −0.76 | 1.70 | +0.245 / +0.159 / +0.053 |

nocap view, same rows:

| Test | Trades | Avg R | Avg R w/o best day | Day-t |
|---|---|---|---|---|
| T1 fit | 202 | +0.271 | +0.212 | 5.04 |
| T1 check | 181 | +0.152 | +0.137 | 3.26 |
| T1 combined | 383 | +0.215 | +0.177 | 5.10 |
| T2 | 44 | +0.189 | +0.124 | 1.81 |

The 45-minute cap costs about 0.025R/trade here. It binds on the check half (median hold 45 min). It is kept because
it is the frozen rule; it is not tuned here.

### Against the top-10 standard (top10/PLAN.md, fixed before any variant was scored)
| Condition | Threshold | ETFDISP (cap45) | Met |
|---|---|---|---|
| T1 combined avg R | >= −0.0383 | +0.191 | yes |
| T1 check avg R | >= −0.0464 | +0.125 | yes |
| T1 combined w/o best day | >= −0.0674 | +0.143 | yes |
| T1 check w/o best day | >= −0.0781 | +0.108 | yes |
| T1 combined total R/session | >= −0.4862 | +0.164 | yes |
| T1 check total R/session | >= −0.5218 | +0.082 | yes |
| T2 avg R | >= −0.1048 | +0.142 | yes |
| >= 20 trades on T1 check and on T2 | | 181 / 44 | yes |
| REALLY BAD | | no (T1 combined t +4.0; positive in all three) | not bad |

**Tier A: meets** (7 of 7 conditions plus the data floor). Because the top-10 medians are negative, the comparison
with the best of the top 10 is more telling:

| | ETFDISP (cap45) | Best of the top 10 |
|---|---|---|
| T1 combined avg R | +0.191 | +0.140 (NM-ETF-late-dip) |
| T1 combined w/o best day | +0.143 | +0.105 (NM-ETF) |
| T1 check avg R | +0.125 | +0.071 (NM-RWN4) |
| T2 avg R | +0.142 | +0.034 (RW6) |
| T1 combined total R/session | +0.164 | +0.154 (NM-ETF) |
| T2 total R/session | +0.015 | +0.048 (RW6) |

ETFDISP trails on T2 total R per session, because it trades only 0.10 times per session there.

### Reference rows: same engine, same book, cap45 (not candidates; shown so the gate's effect is visible)
| | T1 fit avg R (n) | T1 check | T1 combined | T2 |
|---|---|---|---|---|
| Leg E ungated | +0.218 (289) | +0.107 (235) | +0.168 (524); total +88.1R | −0.042 (251); w/o best −0.071 |
| WB4 (live Testing E rules) | +0.158 (385) | +0.068 (321) | +0.117 (706) | −0.066 (338) |
| **ETFDISP** | **+0.250 (202)** | **+0.125 (181)** | **+0.191 (383); total +73.0R** | **+0.142 (44)** |

What the gate does to leg E on the same rows (remedy rule: effect where it acts):

| Window | Kept: n / avg R | Removed: n / avg R | Unknown dispersion |
|---|---|---|---|
| T1 fit | 202 / +0.250 | 81 / +0.140 | 6 (first sessions after the locked gap: not bridged, no trade) |
| T1 check | 181 / +0.125 | 54 / +0.046 | 0 |
| T2 | 44 / +0.142 | 207 / −0.081 | 0 |

The gate improves avg R in all three windows. It costs total R in 2025-26 (it removes trades that made money) and
turns 2023-24 from negative to positive. One family (leg E) is affected. Gate open share:

| Window | Sessions open | Median `disp_prev` |
|---|---|---|
| T1 fit | 52 of 170 (31%) | 2.37 |
| T1 check | 178 of 276 (64%) | 2.85 |
| T2 | 47 of 427 (11%) | 1.99 |

So live volume depends on the regime. At today's dispersion level it is about 0.66 trades per session.

Monthly (cap45, trades / avg R), T1:
- 2025-03 14 / +0.185; **2025-04 175 / +0.267**;
- 2025-05..09 12 trades in all;
- 2025-10 8 / +0.280; 2025-11 5 / +0.166; 2025-12 4 / +0.205;
- 2026-01 12 / +0.382; 2026-02 27 / +0.255; 2026-03 23 / +0.154; 2026-04 7 / −0.203;
- 2026-05 16 / +0.065; 2026-06 32 / +0.020; 2026-07 19 / +0.137; 2026-08 10 / −0.139;
- 2026-10 14 / +0.067; 2026-11 3 / +0.253.

The edge is thinner in mid-2026 (+0.02..+0.14 with two negative months).

### T2 coverage
cache_fresh has 1-minute bars for 100 of the 124 ETFs; 24 have none (`t2_status.json` in the work dir). T1 also has
1-minute bars for 100 of 124. Of these, 14 ETFs traded on T2 and 68 on T1.

### T3: recorded-quote replay. Not scorable; live proxy shown instead
- **Replay.** The only replay session is 2026-11-18. Its `disp_prev` needs the full universe's 11-17 daily returns,
  and no file in the workspace holds them: the replay priors were pickled before `prev_ret` existed, and history2y
  ends 2026-11-04. By design the replay gives NaN and no trades, so T3 is not scored. Bars were not re-downloaded.
- **Live proxy, 2026-10-06..11-04.** These are the Primary/Live Lab/Testing 2 parent's live trades on dates with a
  known `disp_prev`:
  - gate open: 6 trades on 4 days, +0.194R;
  - gate closed: 4 trades on 1 day, +0.328R;
  - 11-05..11-18 (20 parent trades, +0.248R; WB4's 3 live trades, +0.078R): unknown.

  This is far too small to judge anything. The live window includes these rule changes (research/ledger.jsonl):
  - Primary sizing 10-28;
  - Testing 1/2 0.15R cost filter 10-30;
  - NM-ETF moved Live Lab → Primary 11-11;
  - the LR8 live cost model 11-12 (live R is on the LR8 basis);
  - Testing half-size lots and the WB4 copy 11-17.

## Biases (most favour the setup; true figures are likely at or below these)
- In-sample gate (all three windows were used to set the cut-offs).
- T1 lab universe and the T2 symbol list are today's names (survivorship).
- The backtest has no spread, quote cross-check or U9 skips. Live sizing and account slot limits are not modelled
  beyond the per-setup book.
- April 2025 dominates the fit half.

## Configurations counted
- 1 (this frozen setup).
- The ungated leg E and WB4 rows are references only and are not counted.
- The threshold rule was fixed in advance and there was no search.
- Job cumulative **N ≈ 1,883 (up to 1,885 if the two reference rows are counted)**.

## Deployment notes (for the Deploy stage; the owner decides)
- **Account.** Put it in a testing account that holds neither WB4 (Testing E) nor the NM-ETF parent (Primary). On
  every symbol-session ETFDISP trades, WB4 also trades in T1, so the same ETF dip would be taken in two accounts.
- **Label.** "debatable / derived from NM-ETF-late-dip-di-long (WB4)" is not needed: it meets Tier A. Label it
  "owner decision 2026-11-19 (1); meets the top-10 standard; in-sample gate".
- **Paperwork in the same after-close commit:**
  - a `research/ledger.jsonl` entry (effective 2026-11-20; includes the engine change: new opt-in `disp_prev`
    column, `Prior.prev_ret`);
  - regenerated `docs/live/assignments.json`;
  - the setup-freeze check passing.
- **One-big-day check.** Avg R w/o best day is +0.143 on T1 combined (best-day share 40%) and +0.169 on T1 fit, where
  the share is 57%: **1 day** tag in the fit half (2025-04-10).

Educational only — not financial advice.
