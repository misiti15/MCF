# swing1022: "15m swing level: break-and-retest / 3rd rejection to the next POI" (Reddit, owner request 2026-10-22). Results

*Educational only - not financial advice. Everything here is a backtest on the open two-year history with costs in.
Nothing is paper or live. `PLAN.md` was committed (abfbb314) before any scoring. The locked block
2024-11-01..2025-02-28 was never read (row-filtered loads; the extended-hours fetch for SPXL/TQQQ, like reddit1021's
for SPY/QQQ, never requested it). No holdout was scored.*

## Verdict (plain English)
**No validity found after costs.** The rules as posted almost never fire on SPY/QQQ: in 444 sessions, 15 break-and-retest
trades (-0.32R each) and 3 third-rejection trades. With a simpler target so it trades more (fixed 2R, 150 trades), it
loses -0.11R per trade (train -0.09 / valid -0.14) and is only +0.08R before costs. On ~1,200 liquid stocks it loses
-0.45R per trade as posted (4,229 trades; +0.10R before costs, but the tight retest stops make costs ~0.55R per trade)
and is exactly random with a fixed 2R target (-0.25R vs random -0.25R, 57k trades). The author's own "very little
edge" is about right: there is a hint of it before costs, and none after.

**Setups added to testing accounts: 0.** Nothing passes the Testing bar (0 of 192) and nothing meets the owner's
near-miss merit rule of 2026-10-22 (0 of 192: positive after costs in train AND valid, beats random in both,
>= 30 train / >= 20 valid trades, no day > 25% of total R). The ideas went to the backlog as failed
(`backlog_proposals.jsonl`, research/backlog.jsonl).

**Configurations: 192** (`counts.json`): SPY+QQQ 66 (58 pre-declared + 8 stage 2), SPXL+TQQQ 62 (58 + 4),
stocks 64 (56 + 8). The plan's "26 one-knob variants per type" was an addition slip: the listed knobs are 27, and
all 27 were scored as listed. Study bar max(1.5, sqrt(2 ln 192)) = **3.24**; lineage bar with reddit1021 (375) =
**3.44**; with reddit1012liq too (8,093) = **4.24**. About 10 false positives are expected at p = 0.05.
**Best open-history day-clustered t among rows with >= 30 trades: 0.08.**

## Failures first
- **0 Testing-bar passes, 0 owner-merit near-misses.** The one formal "near-miss" (fails only n_train) is SPY/QQQ
  third rejection + prior-day H/L levels: 4 trades in two years. It is noise, and it is not added.
- **No row with >= 30 trades is positive on both train and valid.** 7 rows are positive on both, and all of them have
  2-29 trades. 131 of 192 rows lose on the full history.
- **As posted, the rules almost never trigger on SPY/QQQ**:
  - break-and-retest: 15 trades in 444 sessions (0.03/day), 20% winners, -0.32R (train -0.79 n10 / valid +0.61 n5).
  - third rejection: 3 trades (1 train, 2 valid).
  - Why: with every 15m swing point of 5 sessions, prior-day and premarket H/L and round numbers counted as POIs, the
    *next* POI is closer than 2R 90% of the time, so the strict "next POI must be >= 2R" rule skips most retests.
    Three rejections of the same swing level before 11:30 are rare (full day: 4 trades).
- **Target variants that trade more do not help.** SPY/QQQ break-and-retest, 150 trades (0.34/day):
  - fixed 2R: -0.114R (train -0.092 / valid -0.144), 37% winners, gross +0.078.
  - fixed 1.5R / 3R: -0.13 / -0.19.
  - first POI >= 2R away: -0.125 (train -0.091 / valid -0.173).
  - Random same-minute entries with the same exit: -0.18. Excess +0.065R, t ~0.5: not distinguishable from random.
- **Stocks (1,198 names, adv20 >= $95M on the day): every one of 64 rows loses on both splits** (-0.16 to -1.84R per
  trade, t -2 to -71).
  - Break-and-retest as posted: n 4,229 (9.5/day), 28% winners, -0.448R (train -0.498 / valid -0.389), gross +0.101,
    costs 0.55R per trade. Random same-minute: -0.537 (excess +0.089).
  - Fixed 2R: n 57,350, -0.254R vs random -0.252R: **zero edge before costs** (gross -0.002).
  - Third rejection: n 411, -0.428R (gross +0.059).
- **The resting-limit entry at the level is the worst variant everywhere** (SPY/QQQ -0.84R, SPXL/TQQQ -0.98R, stocks
  -1.06R). The fills select the breaks that fail (adverse selection), the same as the fib-limit finding in reddit1021.
- **SPXL/TQQQ (better cost per unit of risk) do not change the answer.** As posted: 8 trades. First POI >= 2R:
  n 140, -0.007R (train -0.106 / valid +0.160), costs 0.15R per trade vs 0.20 on SPY/QQQ.
- **Filters do not rescue it.** CHoCH-only / BOS-only, fresh levels only, volume > 1.0x / 1.5x the 20-bar average, SPY
  with/against VWAP or its open, long-only / short-only, swing N 1/3, retest tolerance 0/0.25 ATR, retest window
  2/8 candles, stop buffer 0/0.25 ATR, full day to 15:00 are all negative or tiny-n on SPY/QQQ, and negative on both
  splits for stocks (`results.csv`).
- **Extended-hours swings (premarket/after-hours, SPY/QQQ)** raise SPY/QQQ break-and-retest to +0.10R, but on 29
  trades (train +0.005 n13 / valid +0.18 n16, t 0.27). Live cannot see them anyway: the lab frame holds today's bars only.
- **Data limits.** We test ETFs and stocks, not ES/NQ futures. Futures have lower costs per unit of risk and a real
  overnight session. Stocks have no extended-hours bars here. The universe is today's list applied to the past
  (survivorship).

## Results (avg R per trade after costs; n; win %) - key rows
| group | rule | trades (per day) | win % | avg R | train | valid | random | before costs |
|---|---|---|---|---|---|---|---|---|
| SPY+QQQ | break-retest, as posted (next POI >= 2R) | 15 (0.03) | 20 | -0.321 | -0.787 (10) | +0.612 (5) | -0.427 | +0.034 |
| SPY+QQQ | 3rd rejection, as posted | 3 (0.01) | 67 | +0.885 | -1.378 (1) | +2.017 (2) | -0.578 | +1.207 |
| SPY+QQQ | break-retest, fixed 2R | 150 (0.34) | 37 | -0.114 | -0.092 (88) | -0.144 (62) | -0.178 | +0.078 |
| SPY+QQQ | break-retest, first POI >= 2R | 150 (0.34) | 32 | -0.125 | -0.091 (88) | -0.173 (62) | -0.213 | +0.079 |
| SPY+QQQ | 3rd rejection, first POI >= 2R | 24 (0.05) | 33 | +0.066 | -0.087 (15) | +0.321 (9) | -0.181 | +0.270 |
| SPY+QQQ | break-retest, limit at the level | 128 (0.29) | 20 | -0.843 | -1.149 (76) | -0.397 (52) | -0.712 | -0.105 |
| SPY+QQQ | break-retest + round-number levels | 76 (0.17) | 25 | -0.250 | -0.792 (37) | +0.265 (39) | -0.308 | +0.039 |
| SPY+QQQ | break-retest, extended-hours swings | 29 (0.07) | 34 | +0.103 | +0.005 (13) | +0.183 (16) | -0.205 | +0.329 |
| SPXL+TQQQ | break-retest, as posted | 8 (0.02) | 38 | -0.172 | -0.630 (4) | +0.287 (4) | -0.538 | +0.144 |
| SPXL+TQQQ | break-retest, first POI >= 2R | 140 (0.32) | 34 | -0.007 | -0.106 (88) | +0.160 (52) | -0.152 | +0.146 |
| stocks | break-retest, as posted | 4,229 (9.5) | 28 | -0.448 | -0.498 | -0.389 | -0.537 | +0.101 |
| stocks | break-retest, fixed 2R | 57,350 (129) | 35 | -0.254 | -0.286 | -0.221 | -0.252 | -0.002 |
| stocks | 3rd rejection, as posted | 411 (0.9) | 29 | -0.428 | -0.403 | -0.457 | -0.446 | +0.059 |

Full table: `results.csv` (192 rows). Columns: train / valid / all, random control, excess, gross, cost, trades per
day, up / flat / down sessions, walk-forward month share, ex-best-day, max day share, Testing-bar failures, owner
merit flag. Per ticker: `results_{idx,lev}_per_ticker_*.csv`. Finalist rows: `finalists.csv`.

## Add / no-add, per candidate (owner rule 2026-10-22)
- No row passes the Testing bar, so nothing is added under (a).
- No row meets (b) "near-miss with merit". The closest rows by trade count:
  - SPXL/TQQQ first-POI-2R: train -0.106, so it is positive in one period only.
  - SPY/QQQ 3rd rejection first-POI-2R: train -0.087, n 15 / 9.
  - SPY/QQQ extended-hours swings: n 13 / 16; it also needs data the live frame lacks.
  - Stocks, short-only third rejection, stop buffer 0.25 ATR (stage 2): train +0.26 (48) but valid -0.48 (23).
- **Not added; reason: positive in one period at most, or tiny samples.** No lab module was written, and no config,
  ledger, assignments or OPEN_ITEMS change was made.

## Method notes
- **Data, split and costs:** see PLAN.md. TRAIN = 245 sessions (2024-09-16..10-31, 2025-03-03..12-31); VALID = 199
  (2026-01-02..10-16).
- **15m bars** use the 09:30 anchor.
- **Swings** are fractal pivots (strict; N = 2) on the continuous regular-hours 15m series. The extended-hours knob
  uses 04:00-20:00 15m bars.
- **The level pair** is the last swing high and the last swing low confirmed before 09:30, within 5 sessions.
- **POIs** are all swings of those 5 sessions, today's confirmed 15m swings, prior-day H/L, premarket H/L (ETFs) and
  round numbers. The step is the smallest of 0.05..100 that is >= 0.5% of the prior close: $5 on SPY/QQQ.
- **Break and retest:** the break is a 15m close through the level (the first candle is excluded). The retest
  candle (within 4 candles) touches within 0.1 ATR15 and closes back on the break side. Entry at its close; stop past
  the farther of level / wick + 0.1 ATR15.
- **Third rejection:** the third 15m candle that wicks through and closes back, with no close beyond the level in
  between. Entry at its close; stop past its wick + 0.1 ATR15.
- **Exits:** a target limit at the POI (no exit cost), stop-first in every 1-minute bar, flat 15:55. Production
  costs; x3 on the extended tier.
- **Random control:** a market entry at the same fill minute on other sessions of the same split (ETFs 60, stocks
  20 of the same symbol), same side, same R/price and target multiple, flat 15:55.
- **One trade per level per day.** A level is used up by its first break, whether the break was traded or not.
- **Scripts** (`scripts/`): `prep.py` (15m bars, pivots, levels), `sw_engine.py` (numba signals, fills, controls),
  `run.py` (configurations, stage 2, summaries), `report.py` (bars, finalists, counts). They reuse reddit1021's
  loaders (`common.py`) and its read-only extended-hours fetch.

## Reddit reply (draft, plain words)
> I ran your rules on ~2 years of 1-minute data (444 trading days), on SPY/QQQ (and SPXL/TQQQ) as
> stand-ins for ES/NQ, plus ~1,200 liquid stocks. "Result" = profit or loss per trade in units of the risk you took,
> after commissions/slippage.
>
> SPY+QQQ, 15-min swing high/low, 10:00-11:30 entries:
> ```
> version                               trades  win%  result/trade
> break & retest, your rules              15    20%     -0.32
> 3rd rejection, your rules                3    67%     +0.89 (too few)
> break & retest, fixed 2:1 target       150    37%     -0.11
> break & retest, first POI >= 2:1       150    32%     -0.13
> 3rd rejection, first POI >= 2:1         24    33%     +0.07
> limit order sitting at the level       128    20%     -0.84
> SPXL/TQQQ, first POI >= 2:1            140    34%     -0.01
> stocks, your rules                   4,229    28%     -0.45
> ```
> The honest bit: you said "very little edge", and that's what I found. Before costs it's slightly positive
> (+0.03 to +0.10 per trade), but the retest stops are tight, so costs eat it, and it's close to random entries
> with the same exit. What helped a little: aim for the first level at least 2:1 away instead of skipping the
> trade; use premarket swings; and don't rest a limit at the level (those fills are mostly the breaks that fail).
> Taken strictly, "next POI must be 2:1" skips ~90% of retests (levels are dense). Limits: ETFs/stocks, not
> futures (lower costs, real overnight). Not advice.

Educational only - not financial advice.
