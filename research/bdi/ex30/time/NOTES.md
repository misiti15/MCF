Educational only — not financial advice

# ex30 / time — time and calendar structure: results (2026-11-03)

Pre-declared in PLAN.md (committed 80baddd2c before any scoring). **15 configurations scored** (5 primaries, 10
neighbours); nothing else was scored. **0 of 15 pass the light lane gate; 0 of 5 delivered setups pass.** Every
config is negative after costs on TRAIN and on VALID. Locked block 2024-11-01..2025-02-28 never loaded. Costs in
(gates.lab_trades production + time-of-day entry). TRAIN = 234 sessions (2024-10, 2025-03..12), VALID = 114 sessions
(2026-01..03, 2026-07-01..09-15). Backtest only — no live or paper result exists for any of these. Files: `score.py`
(harness), `report.py`, `gen_modules.py` (writes the modules), `results.csv` (every config), `parity.csv`, `modules/`.

## Data constraints stated before scoring

- Entries are bar closes 09:50-15:00 (LabStrategy), so "power hour" = entries 14:30-15:00 held to the 15:55 flat.
- SPY's prior-day *direction* is not available to a lab module live; only `spy_prng` (SPY prior range / ATR). The
  "session after a big / small index day" idea is therefore range-based (TM2 uses a narrow prior SPY day).
- No exchange holiday calendar is available to a module; turn of month uses calendar day of month (known at the open).
- The modules read the date from `date` (history) or the frame's DatetimeIndex (live).

## Failures first

1. **Both QUIET-day setups lose on quiet days.** TM1 (lunch stalled-high fade, SPY within +-0.25% at entry) is -0.11R
   (TRAIN, n 775) / -0.05R (VALID, n 442) on quiet days; it only makes money on days that end DOWN (+0.11 / +0.03R)
   — a short that is a hidden down-day bet. TM2 (quiet-tape range-floor fade) is -0.07 / -0.12R on quiet days,
   +0.07 / +0.07R on up days, -0.42 / -0.23R on down days: a flat tape at noon is not a quiet day by the close, and
   a long at the floor of the range is a direction bet again. TM2 also fires 43 trades/session (cap 25).
   Being "quiet at the bar" (spy_fo) does not deliver the quiet-day edge the live book lacks.
2. **TM3 (gap-up drifted to the low, power-hour short) is the worst**: -0.17 / -0.09R, below the random entry in both
   splits (-0.24R t -1.65 / -0.08R t -2.23). Gap-up names at the low at 14:30 bounce into the close more than they
   capitulate. All three neighbours agree (-0.07..-0.21R).
3. **TM4 (10:00 reversal long) breaks out of sample.** TRAIN -0.019R (n 940, passes the avg-R part, +0.05R vs random)
   but VALID -0.217R (n 624, t -3.7, -0.18R vs random, t -2.95). Monday-only neighbour: +0.03 / -0.26R at < 1.5
   trades/session (its TRAIN best-day share is meaningless: total R ~ +6R).
4. **TM5 (turn-of-month VWAP pullback long)** -0.055 / -0.051R at 20.4 trades/session. The calendar matters a little:
   the complement (days 4-27, same rule) is -0.071 / -0.091R, so turn-of-month is +0.016 / +0.040R better, but both
   are below the -0.02 line, and it is still an up-day bet (+0.03 / +0.09 up, -0.13 / -0.15 down, -0.09 / -0.18 quiet).

## The 5 setups (delivered as modules; all gate_pass = false)

| setup | TRAIN avgR (n, t) | VALID avgR (n, t) | trades/session | vs random T / V | up / down / quiet R TRAIN | up / down / quiet R VALID | w/o best day T / V | parity |
|---|---|---|---|---|---|---|---|---|
| TM1-lunch-stalled-high-fade-quiet-short | -0.089 (1,319, -3.37) | -0.028 (892, -0.90) | 6.4 | -0.025 / +0.024 | -0.22 / +0.11 / -0.11 | -0.05 / +0.03 / -0.05 | -0.099 / -0.035 | 524/524 |
| TM2-quiet-tape-range-floor-fade-long | -0.094 (8,343, -3.51) | -0.121 (6,727, -4.71) | 43.3 | +0.018 / -0.003 | +0.07 / -0.42 / -0.07 | +0.07 / -0.23 / -0.12 | -0.100 / -0.128 | 9,787/9,787 |
| TM3-gapup-drift-powerhour-short | -0.174 (2,183, -1.70) | -0.093 (1,274, -1.56) | 9.9 | -0.241 / -0.079 | -0.27 / -0.17 / -0.14 | -0.13 / -0.09 / -0.07 | -0.211 / -0.139 | 1,343/1,343 |
| TM4-ten-oclock-reversal-long | -0.019 (940, -0.24) | -0.217 (624, -3.69) | 4.5 | +0.052 / -0.177 | +0.04 / -0.14 / +0.08 | -0.26 / -0.30 / -0.09 | -0.077 / -0.240 | 137/137 |
| TM5-turn-of-month-vwap-pullback-long | -0.055 (4,573, -1.31) | -0.051 (2,519, -1.10) | 20.4 | +0.035 / -0.002 | +0.03 / -0.13 / -0.09 | +0.09 / -0.15 / -0.18 | -0.085 / -0.076 | 3,095/3,095 |

Day type = SPY open-to-close (end of day, not known at entry): up >= +0.25%, down <= -0.25%, else quiet. Parity = bar-
by-bar mask match module vs harness on 2026-09 inside window and ADV 95M (independent implementations: numpy segment
lags in score.py, pandas groupby in the modules). Live-shape check also passed: on 400 random symbol-days the modules
give the same mask on a single-symbol frame indexed by timestamps, without symbol/date columns and with three extra
pre-09:50 bars (as the live frame has) — 2,000 checks, 0 mismatches.

Neighbours (results.csv): TM1 mv 1.0 -0.080 / -0.032R, dh 0.25 -0.086 / -0.021R (VALID nearly at the line, TRAIN not);
TM2 prng off -0.097 / -0.122R, spy 0.30 -0.091 / -0.109R; TM3 gap 2.0 -0.21 / -0.09R, mv -0.50 -0.17 / -0.07R;
TM4 mv -1.0 -0.022 / -0.156R, Monday only +0.028 / -0.263R (0.99 trades/session); TM5 days 27-4 -0.065 / -0.028R,
days 4-27 (calendar control) -0.071 / -0.091R.

Gate per setup: TM1 fail (TRAIN avg R); TM2 fail (avg R both, 43 trades/session); TM3 fail (avg R both); TM4 fail
(VALID avg R); TM5 fail (avg R both).

## Reading for the owner

- If any of these goes to an exploratory account anyway (live is the main verdict), the least bad are **TM1** (VALID
  -0.03R, 6 trades/session, a short that earns on down days) and **TM5** (-0.05 / -0.05R; the only one where the
  calendar ingredient itself showed a positive difference vs its complement). TM4's VALID collapse and TM3's
  below-random record argue against them. TM2 needs a throttle before it is runnable at all.
- The quiet-day problem is not solved by gating on spy_fo at the bar: both quiet designs lose on days that close
  quiet. A real quiet-day setup probably needs a pre-open predictor of a quiet day (spy_prng alone did not help:
  TM2 with and without it are the same) or symmetric two-sided range trading, which a one-side lab module cannot do
  in one setup.

Rule-change context: none of these setups ran live; no ledger change applies to these backtest numbers (fixed
lab_trades cost model, R = 0.25 x ATR, no per-setup stop, no sizing). Live R in a Testing-style account would also carry
the ledger's 10-27 GX1 lab clock and the 10-30 Testing cost filter.

Educational only — not financial advice.
