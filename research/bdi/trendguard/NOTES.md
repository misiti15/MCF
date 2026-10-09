# BDI trend-guard study: owner trend-trap rules as extra layers on the 23 re-scored setups

*Educational only - not financial advice. Lab results on the 2-year history only; nothing here is a live result.*

**Section 1 (pre-declaration) was written on 2026-10-09 03:51 UTC, before any configuration was scored.**
Results are appended below it in section 2 and are not allowed to change section 1.

Source: owner notes on the 10 worst trades of 2026-10-08 (`research/bdi/daily/2026-10-08/OWNER_NOTES.md`,
`owner_trendtrap_rules.jpg`) and the autopsy (`research/bdi/daily/2026-10-08/AUTOPSY.md`).

## 1. Pre-declaration

### 1.1 Data
- Two-year frames `research/history2y/data/frames` via `research/history2y/lib.py` (open months only). The rule-19 locked
  block 2024-11-01..2025-02-28 is never loaded: `MCF_HIST_ALLOW_LOCKED` is never set, `research/history2y/data/locked` is
  never read. The new indicators come from the 1-minute SIP cache `data/cache_hist/1Min` (the frames' own source);
  every row dated inside the locked block is dropped at load, before any computation.
- Sessions scored: the 426 open sessions of `lib.regimes()` (2024-10-01..2026-10-07 minus the locked block).
- Survivorship caveat as RESCORE.md (today's 1,226 names applied to the past).

### 1.2 Features (live parity: 5-minute bars, value known at the bar's close; tod = bar end, as the frames)
5-minute bars = `mcf.data.bars.resample(1-min, "5min")`, RTH, continuous across sessions (LabStrategy sees 40 prior
5-min bars plus today's; EMA/ADX here use the full prior series, a small warm-up difference noted for ADX).
- **VWAP** session-cumulative typical price x volume (as `mcf.research.heat.heat_frame`). **VWAP SD** volume-weighted:
  `sqrt(cum(v*tp^2)/cum(v) - vwap^2)`; bands `vwap +- k*SD`.
- **EMA9 / EMA21** of close (`ewm(span, adjust=False)`). Rising = `EMA[t] - EMA[t-3] > 0`; falling = `< 0`.
- **CMF(20)** = sum20(((c-l)-(h-c))/(h-l) * v) / sum20(v) (0 when h = l). Rising = `CMF[t] > CMF[t-3]`.
- **OBV** = cumsum(sign(c - c_prev) * v); slope = `OBV[t] - OBV[t-3]`.
- **ADX(14), +DI, -DI**: Wilder (ewm alpha 1/14).
- **RSI**: the frames' `rsi` (MarcoFlow simple RSI(14) on 5-min closes, the RSI the setups use).
- **Prior-day VAH / VAL**: prior session's 1-minute bars; 50 equal-width bins between that session's low and high; each
  1-min bar's volume goes to the bin of its typical price; start at the POC (largest bin) and repeatedly add the larger
  of the next bin above / next bin below (tie: above) until >= 70% of the session volume. VAH = upper edge of the top
  included bin, VAL = lower edge of the bottom one. Only the prior session is used. For the first session after the
  locked block (2025-03-03) the prior session is locked: VAH/VAL are missing and G5 does not block.
- **daily ATR** `atr_d` and R = 0.25 x atr_d: from the frames (bt setups: same formula on the 1-min cache).

### 1.3 Guards (short form as the owner wrote them; longs are the exact mirror). block = skip this bar.
| id | variants | short: block the bar if | long mirror: block if |
|---|---|---|---|
| G1 | k = 1, 2 (2) | close > VWAP and, since the last 5-min close <= VWAP in this session (or the open), some close was > VWAP + k*SD (this bar included) | close < VWAP and since the last close >= VWAP some close < VWAP - k*SD |
| G2 | L = 9, 21, 9-or-21 (3) | close > EMA_L and EMA_L rising (9-or-21: either holds) | close < EMA_L and EMA_L falling |
| G3 | a: CMF; b: CMF or OBV (2) | RSI > 70 and [a: CMF > 0 and CMF rising; b: (CMF > 0 and rising) or OBV slope > 0] | RSI < 30 and [a: CMF < 0 and falling; b: (...) or OBV slope < 0] |
| G4 | ADX > 25 / 30 x DI gap > 5 / 10 (4) | ADX > A and (+DI) - (-DI) > D | ADX > A and (-DI) - (+DI) > D |
| G5 | 1 | close > prior-day VAH | close < prior-day VAL |

A guard is a **layer**: entries = setup mask & window & adv & not blocked, first qualifying bar per symbol-day (exactly
the rescore convention). A blocked signal bar can therefore be followed by a later unblocked one ("wait").
**Pairs**: both guards apply (block = blockA or blockB), every cross-family variant combination of G1-G5:
G1xG2 6, G1xG3 4, G1xG4 8, G1xG5 2, G2xG3 6, G2xG4 12, G2xG5 3, G3xG4 8, G3xG5 2, G4xG5 4 = **55 pairs**. All 55 are
scored and counted (no "pick the two best singles", which would be selection after seeing results).

### 1.4 C: confirmation as an entry delay, N in {3, 6, 12} 5-min bars (3)
For each symbol-day the first raw signal bar s opens a wait over bars s+1 .. s+N (never past tod 15:00). Enter at the
close of the first bar j where all hold:
1. lower high: some bar i in s+1..j had high_i < max(high_s .. high_{i-1}) (long: higher low, low_i > min(low_s..low_{i-1}));
2. trigger on bar j: close_j < VWAP_j or close_j < EMA9_j (long: close above VWAP or EMA9);
3. bearish volume divergence on some bar i in s..j: CMF20_i < 0, or (high_i >= max(high_{i-20..i-1}) and volume_i <
   volume of the bar that made that prior 20-bar high) (long: CMF > 0, or a lower low on lower volume).
If not confirmed by s+N the signal is dropped; the next raw signal after s+N may open a new wait. One trade per
symbol-day. C is not combined with G guards (the menu is: none, single G, C, G-pairs).

### 1.5 Exits (3). Path = later 5-min bars up to the 15:55 bar, stop first inside a bar, flat at the 15:55 bar's close
- **cur**: the setup's own geometry (t1s1 / t05s1 / t1s05, R = 0.25 x atr_d), identical to `setup_lab._outcomes_asym`
  (checked: the simulator must reproduce the frames' `r_<side>_<geom>` on the baseline before anything is scored).
- **E1** momentum-shift: as cur, plus once a bar's favourable extreme has reached +0.5R (bars after entry, that bar
  included), the first such armed bar that closes back across EMA9 (short: close > EMA9; long: close < EMA9) and did not
  hit stop or target exits at that close.
- **E2** structure stop: stop = highest high of the last 6 5-min bars up to and including the entry bar + 0.1 x atr_d
  (long: lowest low - 0.1 x atr_d), distance capped at 1.5R; target price unchanged; size to the same $ risk, i.e. the
  result is measured in units of the new stop distance and costs are divided by it.
- Costs (all exits): production, as `gates.prod_r`: 1c + 1 bps per side, the exit side free on target fills, +2c on stop
  fills.

### 1.6 orb20_a and intraday_momentum (production backtester trades, `bt_trades.parquet`)
Guards are evaluated on the last 5-min bar completed at the trade's entry time and act as a filter only (the engine
emits one signal; there is no later bar to wait for). E1 / E2 / C are re-simulated on 1-minute bars from the recorded
fill with the engine's cost model (`mcf.backtest.engine.Costs`, non-extended tier) and the trade's own stop / target;
for C the entry moves to the confirming 5-min bar's close (+ entry cost) with the same stop and target distances; for
these two setups the confirming bar may end any time before 15:55 (intraday_momentum enters at 15:30, so the lab 15:00
cap would remove every trade by construction). E2 keeps the original stop if the structure stop is on the wrong side
of the fill. (1.6 amended 2026-10-09 before scoring.)
The re-simulation of `cur` is compared with the recorded r_multiple and the difference reported.

### 1.7 Configurations
Per setup: guard sets 1 (none) + 12 (singles: G1 2, G2 3, G3 2, G4 4, G5 1) + 3 (C) + 55 (pairs) = **71**, x 3 exits =
**213**, of which 212 are new (none x cur is the rescore baseline). **23 setups x 212 = 4,876 new configurations.**
At p = 0.05 about 244 would look significant by chance.

Per-lineage try count N (feeds `gates.t_required` and the deflated Sharpe) = the lineage's rescore tries + 212 x
the number of setups of that lineage in this study:
| lineage | setups | rescore tries | added | N |
|---|---|---|---|---|
| exhaustion (exhaustion_short 855,600; RW2 934,522) | 2 | own | 424 | 856,024 / 934,946 |
| heat study | heat_fade_short, heat_fade_long | 19,200 | 424 | 19,624 |
| MarcoFlow primitives | MF1-MF5 | 8,012 | 1,060 | 9,072 |
| owner 10-08 scan | NS1-NS5 | 7,374 | 1,060 | 8,434 |
| rework 82,068 | RW1, RW3, RW5, RW7 | 82,068 | 848 | 82,916 |
| rework 81,430 | RW4, RW6, RW8 | 81,430 | 636 | 82,066 |
| setup screen | orb20_a, intraday_momentum | 15 | 424 | 439 |

### 1.8 Gates and verdict (unchanged `mcf/research/gates.py`, fixed in advance)
exp > 0; day-clustered t >= max(1.5, sqrt(2 ln N)); exp > 0 in up AND down sessions (n >= 30 each); walk-forward
share >= 0.6 (3-month train / 1-month test, locked months excluded). Also reported: deflated Sharpe, ex-best-day,
trades/day, flat sessions. **keep** = all gates pass. A setup's reported "best" configuration is the one with the
highest day-clustered t (descriptive only). A guard that mostly removes up-session trades still has to be > 0 in up
AND down sessions. Nothing is scored on the locked block; a keep candidate goes to the lead for its single scoring.

### 1.9 Anecdote (labelled as such)
The 10 trades the owner flagged (IONQ, ACN, Z, PATH, NOW, LDOS, SHW, NLY, VTRS, BABA) plus GEV (E2's motivating case):
guard values at the live signal bar from `data/cache/bdi1008` 1-min bars (same feature code), and E1 / E2 re-walked on
1-minute bars from the live fill with the live R. One session: a diagnosis, not evidence.
