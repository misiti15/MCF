# Oversold-turn longs and open-dip longs (BDI, owner request 2026-10-13): pre-declaration

*Educational only - not financial advice. Written 2026-10-13 before any configuration of this study was scored. Results
go in NOTES.md. This file may only gain dated amendments, written before the affected configurations are scored.*

Owner (2026-10-13):
- (A) "Run backtesting on oversold setups turning into upswing."
- (B) "Fully run and backtest huge dips (0.75% or more) at open up until 9:45-9:50 and go long after. Market trends and
  other factors need to support the lack of a further continuous drop."

Builds on `research/bdi/longs1013` (Q2 open flush: 484 configurations, 0 pass; the positive longs were market beta).
What is new here:
- the dip is measured in % as well as in ATR;
- gap classes (gap-and-fade vs open-then-flush);
- market, sector, VIX-proxy, trend and volume-capitulation support filters;
- structural exits (stop under the session low, VWAP or open target);
- a full-session oversold-to-turn family (A);
- **every configuration is scored against random longs at the same minute.**

Seen before writing this plan:
- published notes only: longs1013, reddit1012liq, turns1009 (CASES), stack1009, cwt/test_b;
- the frame schema, `gates.py`, `setup_lab._outcomes_asym`, `heat.heat_frame` and `LabStrategy.generate`.

No result of this study had been computed.

## 0. Data and conventions (both parts)
**Data**
- Open two-year history only. The rule-19 locked block (2024-11-01..2025-02-28) is never loaded, and
  `MCF_HIST_ALLOW_LOCKED` is never set.
  - The 1-minute SIP cache `data/cache_hist/1Min` is read per symbol, and locked-block rows are dropped immediately
    after each read.
  - `lib.load_month` (open months only) supplies the frame columns `rsi`, `rsi5`, `sma20_dist_pct`, `gap`, `atr_d`
    and `adv20`.
  - `lib.daily()` (locked block excluded) supplies the daily trend features.
  - The 1-minute ETF array of `research/bdi/indexlink/data/etf1m.npz` (426 open sessions) supplies SPY, QQQ, the
    sector ETFs and VXX.
  - The sector map is `research/bdi/indexlink/linkage.csv` `sector_etf`. Caveat: this is the highest-correlation
    sector ETF over the open history, a mild look-ahead in the mapping only.
- Population: point-in-time adv20 >= $95M and atr_d > 0 (the min_adv of every live lab setup).
  - Today's universe is applied to the past (survivorship caveat as in rule 19).

**Bars and features**
- 5-minute RTH bars rebuilt from the 1-minute cache with `mcf.data.bars.resample` semantics.
  - Bar-close times run 09:35..16:00.
  - VWAP is computed as in `heat_frame`: cumulative 5-minute typical price x volume.
  - Frame columns are merged on (symbol, date, tod) for 09:50..15:00.
- **R = 0.25 x daily ATR for every exit**, including the structural ones, so all numbers share one unit.

**Entries and fills**
- Entry is at the signal bar's close, the lab convention. One trade per symbol-day per configuration (the first
  qualifying bar).
- A next-bar-open entry is reported for the finalists as a robustness line.

**Exit simulation** (5-minute bars after the entry bar, up to the 15:55 bar)
- Stop first inside a bar. A bar that opens through the stop fills at its open.
- Target fills at the target, as a limit.
- Timed exit at the 15:55 bar close.
- `HTC` holds to the 15:55 close with no stop and no target.

**Costs: `gates` production costs, always in**
- Entry side: (1c + 1 bps) x `gates.tod_cost_mult(entry tod)`. That multiplier is x3.8 before 09:35, x2.1 before
  09:50 and x1.4 before 10:30. **The 09:45 entry pays x2.1 and the 09:50-10:25 entries pay x1.4. The open is
  expensive, and this is charged.**
- Exit side: a target fill (a limit) is free. A stop fill pays 1c + 1 bps + 2c. A timed / HTC exit pays 1c + 1 bps.
- The whole cost is x3 on the extended tier (|gap| >= 20% or price < $5).

**Splits and statistics**
- Splits: train = open sessions <= 2025-12-31; valid = 2026-01-02..2026-10-07; open = both (426 sessions).
- Statistics:
  - day-clustered t (`gates.summary` formula);
  - up / flat / down session split (`lib.regimes()`, the universe's median open-to-close terciles; a same-day outcome
    label, used for reporting only);
  - ex-best-day;
  - busiest-session share;
  - walk-forward (`gates.walk_forward`, finalists only).
- **Same-minute random control (the owner's requirement):** for every trade, the control is the mean production R of
  *every* eligible symbol's long trade with the same exit rule entered at the same date and bar (the structural exits
  are applied to each control symbol's own session low / VWAP / open).
  - **Excess** = trade R - control.
  - The excess is reported with its day-clustered t for every configuration, plus up-day / down-day splits for every
    finalist.

## 1. Part A - oversold, then turning up (lineage `dips1013-ost`)
Oversold state **O** (16), evaluated on the bars before the turn bar:
| family | definition | thresholds |
|---|---|---|
| rsi2 | simple RSI(2) on today's 5-minute closes from 09:35 (`heat._rsi_simple` formula) | <= 5, <= 10 |
| rsi5 | frame `rsi5` | <= 15, <= 25 |
| rsi14 | frame `rsi` | <= 25, <= 30 |
| vwap | (VWAP - close) / atr_d | >= 0.5, >= 1.0 |
| sma20 | (SMA20 - close) / atr_d, with SMA20 = close / (1 + sma20_dist_pct/100), the 5-minute SMA20 | >= 0.5, >= 1.0 |
| bb | close below the 5-minute Bollinger lower band (20 bars, continuous RTH series across sessions) | k = 2.0, 2.5 sd |
| streak | consecutive lower 5-minute closes today | >= 3, >= 5 |
| dfh | (high of day - close) / atr_d | >= 1.0, >= 1.5 |

Lookback **L** (2):
- L1: O is true on bar t-1.
- L3: O is true on any of bars t-3..t-1, within today.

Turn trigger **T** on bar t (5):
- `PBH`: close > the prior bar's high.
- `RSIX`: rsi5 crosses back above 30 (prior < 30, now >= 30).
- `VWR`: close > VWAP and the prior close <= the prior VWAP.
- `EMAR`: close > EMA9 and the prior close <= the prior EMA9. EMA9 is computed on today's 5-minute closes from 09:35,
  with span 9 and no adjustment.
- `HL`: low > min(low of bars t-3..t-1) and close > the prior close.

Filter **F** (3):
- `none`.
- `spynl`: SPY made no new session low on bar t or t-1.
- `pcl`: prior-day close location (prior close - prior low) / (prior high - prior low) >= 0.5.

Window (4), by bar close:
- full 09:50-15:00;
- am 09:50-11:00;
- mid 11:05-13:00;
- pm 13:05-15:00.

Exit (5):
- `t1s1`, `t05s1`, `t1s05`, `HTC`.
- `SW-VWAP`: stop 0.05R below the lowest low of bars t-3..t; target the VWAP at bar t if it is above the entry, else
  hold to 15:55.

Grid and controls:
- **A grid = 16 x 2 x 5 x 3 x 4 x 5 = 9,600.**
- Controls: a random long bar per symbol-day in each window (seed 1013) x 5 exits = 20.
- **Part A N = 9,620.**

## 2. Part B - big dip by 09:45-09:50, then long (lineage `longs1013-flush` continued)
Day constants:
- O = the 09:30 open.
- PC = the prior close, O / (1 + gap/100).
- The dip is measured at the 09:50 bar close (09:45 for entry E945).

Dip **D** (21) = reference x depth:
- Reference: `O` (fromOpen), `PC` (from the prior close), or `B` (both conditions).
- Depth (close below the reference): 0.75%, 1.0%, 1.5% or 2.0%; or 0.5, 0.75 or 1.0 daily ATR.

Gap class **G** (5), by the open's gap vs the prior close:
- `any`.
- `notdn`: gap > -1%, which excludes news gap-downs.
- `flat`: |gap| < 0.5%, open-then-flush.
- `gup`: gap >= +0.5%, gap-up-and-fade.
- `gdn`: gap <= -1%, gap-down-and-keep-falling.

Entry **E** (6):
- `E945`: the 09:45 close (dip measured at 09:45). **Not runnable live: the LabStrategy window starts at 09:50.**
- `E950`: the 09:50 close.
- `E955`: the 09:55 close, unconditionally.
- Triggers, first bar 09:55..10:15 (dip measured at 09:50):
  - `PBH`: close > the prior bar's high.
  - `HL`: the session low is unchanged from two bars ago and close > the prior close.
  - `VR`: close > VWAP and the prior close <= the prior VWAP.

Support filter **F** (16), all measured at the entry bar:
- `none`.
- `spyup`: SPY fromOpen > 0.
- `spynl`: SPY made no new session low on the entry bar or the bar before.
- `spymid`: SPY close > the midpoint of SPY's open and its session low.
- `qqqmid`: the same for QQQ.
- `idio`: SPY fromOpen > the stock's fromOpen / 3, so the index drop is under a third of the stock's.
- `sect`: the sector ETF's fromOpen >= SPY's fromOpen, so the sector is not down more than the market.
- `vix`: VXX's prior close <= its 20-session SMA (calm regime) and VXX fromOpen <= 0 at the entry bar.
- `trend`: the stock's prior daily close > its SMA20 and SMA50. The SMA is NaN when the window crosses the dropped
  block (more than 35 / 80 calendar days).
- `pcl`: prior-day close location >= 0.5.
- `capd`: the day's highest 5-minute volume so far is in 09:35..09:45, and the entry bar's volume <= 50% of it (from
  today's bars only).
- `capr`: the 09:30-09:45 volume >= 2x its mean over the prior 20 open sessions (same window), and the entry bar's
  volume is below the 09:35 bar's.
- Combinations:
  - `C1` spymid & trend;
  - `C2` spymid & pcl;
  - `C3` spymid & capd;
  - `C4` spymid & sect & vix.

Exit **X** (7):
- `t1s1`, `t05s1`, `t1s05`, `HTC`.
- Structural stop at the session low through the entry bar minus 0.05R (the 09:30-09:50 low for the 09:50 entry),
  with one of three targets:
  - `SL-VWAP`: the VWAP at entry if it is above the entry, else none.
  - `SL-OPEN`: the day's open.
  - `SL-HTC`: no target.

Grid and controls:
- **B grid = 21 x 5 x 6 x 16 x 7 = 70,560.**
- Control: a random long bar per symbol-day in 09:45..10:15 x 7 exits = 7. The same-minute excess is computed for
  every configuration.
- **Part B N = 70,567.**

## 3. Counts and bars
- **Study N = 9,620 + 70,567 = 80,187.**
  - Study try-count bar: t >= max(1.5, sqrt(2 ln 80,187)) = 4.75.
  - Lineage bars:
    - Part A, `dips1013-ost`, with turns1009 stage C (80) and stack1009 counted as unrelated: t_required(9,620) = 4.28.
    - Part B, + longs1013-flush lineage 31,454: t_required(102,021) = 4.80.
- Research gate: `gates.verdict` with the lineage N.
- Nothing is scored on the locked block. That is the lead's look.

## 4. Selection, finalists, Testing-1 bar
**Finalists, per part**
- The 10 configurations with the highest train day-clustered t, among those with n_train >= 150 and train exp > 0.
- Plus the best by train t of each entry (B) or turn (A) type, if not already in.
- Every finalist is reported on valid and open, failures included, with:
  - same-minute excess (exp, t), plus excess in up and down sessions;
  - up / flat / down exp;
  - ex-best-day, busiest session, walk-forward share;
  - plateau: the worst open exp among the one-step neighbours in depth/threshold and in the window or entry dimension;
  - the next-bar-open line.

**Testing-1 bar** (reddit1012liq PLAN section 5 (a), plus the owner's 2026-10-13 additions; all must hold):
- n_open >= 150.
- Open exp > 0 after costs, with t_open >= 1.5.
- Train exp > 0 and valid exp > 0.
- Ex-best-day > 0, and the busiest session <= 10% of trades.
- **Same-minute excess > 0 on open, train and valid**, so it is not market beta.
- Plateau > 0.
- **Runnable on the live LabStrategy frame:** entry bar 09:50..15:00, and only frame-computable conditions:
  - frame-computable: close / high / low / volume / tod / atr_d / fromOpen / gap / vwapDistPct / rsi / rsi5 /
    sma20_dist_pct / dist_pdh_atr / dist_pdl_atr;
  - not frame-computable: spy*, qqq*, idio, sect, vix, trend, capr and bb need market or history context the frame
    does not carry, so they are research-only.

Clause (b) of section 5 (the lowered bar, which admits negative expectancy) is **not** used. The owner asked for a
stricter standard.

**Proposals**
- At most 2 configurations per part, best open t first.
- If none passes, none is proposed. A research-only configuration that would pass apart from runnability is reported
  as a hook request; mcf/ is not edited.
- Passing configurations are built under `live/` as LabStrategy modules with a trade-for-trade parity check
  (`live/verify.json`). Their config entries are proposed in NOTES.md, not written.

## Amendments
**A1 (2026-10-13, before any configuration was scored; clarification of section 4).**
- The plateau neighbours are fixed as follows.
- **Part A:** the other threshold of the same oversold family and the other lookback L. The windows are different
  trade sets, not neighbours.
- **Part B:** the one-step depth neighbours inside the same unit (% or ATR), and the adjacent entry:
  - E945 <-> E950 <-> E955;
  - each trigger <-> E955.
- In Part A, frame features (rsi, rsi5, sma20_dist_pct) count only from the 09:50 bar, as in the history frames. The
  live module masks them before 09:50 for parity.
- N is unchanged.
