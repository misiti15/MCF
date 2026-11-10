Educational only — not financial advice.

# reddit_1110: Reddit setup scout (2026-11-10)

**Result: 1 idea kept, 1 tested, 0 pass.** 8 configurations were declared in PLAN.md before scoring. Full bar for
N = 8 is max(1.5, sqrt(2 ln 8)) = 2.04, Testing bar (BAR90) 1.84; the best t was +0.26, so **the locked block
(2024-11-01..2025-02-28) was not scored and there is no DECISION.** No config, setup, exit, ledger or docs/live file was
changed. Read-only toward Reddit (RSS GETs only, no account, no posting, voting or messaging; no user names recorded).

**Rule changes in the window:** none apply. Two-year backtest on the research cost model (gates.py: 1c + 1 bp per side,
time-of-day entry multiplier, +2c stops), not a live record; the live changes in research/ledger.jsonl (GX1 10-27,
Primary size 10-28, −2R stop 10-29, CF 10-30, UNI1 11-04, ROLL1 11-05, EXPO1109 11-09/11-10) do not touch it. Data: the
2-year cache rebuilt 11-04 (research/bdi/1104/DATA.md); 485 symbols, 342 sessions (same frame as reddit_1105..1109).

## Sources
- Reddit RSS (UA `mcf-research/0.1`, 8-25 s spacing; two feeds returned empty on the first try and were re-fetched):
  top-day for r/Daytrading, r/Trading, r/algotrading, r/ai_trading, r/RealDayTrading, r/quant, r/StockMarket,
  r/swingtrading, r/daytrade; `/new/` for r/Daytrading, r/algotrading, r/RealDayTrading, r/Trading, r/swingtrading.
  r/daytrading_strategies tried (0 entries). WebSearch (standard, 2 queries) returned only months-old third-party
  mirrors, nothing usable. No new intraday subreddit found.
- **346 unique posts; 227 dated 2026-11-09..11-10** (11-09 posts before ~23:30 ET were covered by reddit_1109) —
  Daytrading 100, Trading 50, algotrading 50, RealDayTrading 50, swingtrading 50, ai_trading 27, StockMarket 13,
  daytrade 3, quant 3 (all dates).
- Thin day for rules: CPI day + NVDA news; most posts were psychology, brokers/prop firms, tool promos, futures/forex/
  gold/crypto, AI-bot crypto experiments.

## Filter (what was dropped)
- r/Daytrading [1xss0rx](https://www.reddit.com/r/Daytrading/comments/1xss0rx/whats_one_trading_rule_you_wish_you_followed_sooner/)
  (never trade the first 5 minutes): already in effect (config `no_entry_before: "09:50"`).
- r/Daytrading [1xs8zab](https://www.reddit.com/r/Daytrading/comments/1xs8zab/i_backtested_a_textbook_strategy_ema_921_rsi_macd/)
  (EMA 9/21 cross + RSI 50-70 + MACD > 0 + above SMA200, 1-hour): covered by bdi-rdt-r10-ema-cross, wi-ema-cross,
  bdi-art-indicator-grid (all parked); also BTC/NVDA/SPY only.
- r/Daytrading [1xszib3](https://www.reddit.com/r/Daytrading/comments/1xszib3/low_float_small_cap_regime_change/), first
  half (low-float breakouts "stuffed"): covered by CWT14 failed-breakout reversal; low floats are outside the top-250
  universe. The second half was kept (below).
- r/Daytrading [1xsyc1d](https://www.reddit.com/r/Daytrading/comments/1xsyc1d/) ("when is price most likely not to go
  sideways"): no rule; overlaps the dayclass / QR1 day-type flags. r/Daytrading 1xs5u3m (bias: wait for the first
  30 minutes): no rule; ORB30 / QR1 cover it.
- r/algotrading [1xsdm1o](https://www.reddit.com/r/algotrading/comments/1xsdm1o/flexible_bars/) (move-based bars instead
  of fixed-time bars): bar construction, daily horizon, no setup.
- r/Trading 1xrtjzf (NVDA lagging the tech bounce): no rule; MH4 group-laggard covers it. r/RealDayTrading 1xsedxy /
  1xsagkk (one-year journeys; ORB in volatile mornings, relative strength): no new rule.
- r/ai_trading 1xstaf5 (a tester's written research rules: pre-register, count every try, measured costs, random-entry
  control, single holdout touch): not a setup, but it matches docs/RESEARCH_RULES.md point for point.
- r/Daytrading 1xseyvm (London reversal, forex), 1xsgpgd (gold-futures IFVG), 1xsz2yl (futures microscalping),
  1xspr63 (TradingView indicator promo), r/swingtrading 1xsvhud (weekly cup base), 1xsq6f2 (option-buyer forecast).

## Idea (research/backlog.jsonl, tags reddit + scout + qday)
| id | source | status |
|---|---|---|
| reddit-1110-grind-no-pullback-continuation | [r/Daytrading 1xszib3](https://www.reddit.com/r/Daytrading/comments/1xszib3/low_float_small_cap_regime_change/) | parked (8 configs) |

The post gives an observation, not a rule ("a few stocks just grinded upward with no real pullback or setup"); the rule
in PLAN.md is MCF's mechanical reading: enter on the smoothness itself instead of waiting for a pullback. It is LONG-led
and stock-relative, so it was a candidate for the QDAY focus.

## Results (`g_tests.py`, `g_out.txt`, `g_results.csv`)
Random control = 3 same-symbol-day entries 10:00..14:30, same side, same $ R, exit at the close.

| config | n | /session | avg R | t | train / valid | excess vs random (t) | w/o best day | SPY up / down / quiet | WF | stopped | med R % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| long 11:00 ER 0.30 | 780 | 2.28 | +0.022 | 0.26 | +0.054 / +0.003 | −0.086 (−1.4) | −0.008 (best day 133%, `1 day`) | +0.262 / −0.446 / −0.096 | 59% | 48% | 0.81 |
| long 11:00 ER 0.45 | 763 | 2.23 | +0.017 | 0.20 | +0.044 / −0.000 | −0.086 (−1.4) | −0.014 (best day 182%, `1 day`) | +0.251 / −0.465 / −0.081 | 53% | 48% | 0.81 |
| long 12:30 ER 0.30 | 873 | 2.55 | −0.201 | −2.61 | −0.273 / −0.154 | −0.799 (−14.5)* | −0.231 | −0.064 / −0.675 / −0.254 | 24% | 60% | 0.55 |
| long 12:30 ER 0.45 | 582 | 1.70 | −0.177 | −1.97 | −0.290 / −0.103 | −0.844 (−13.0)* | −0.214 | −0.073 / −0.610 / −0.232 | 35% | 57% | 0.59 |
| short 11:00 ER 0.30 | 991 | 2.90 | −0.159 | −2.14 | −0.154 / −0.163 | −0.229 (−4.5) | −0.184 | −0.487 / −0.075 / −0.165 | 41% | 54% | 0.93 |
| short 11:00 ER 0.45 | 967 | 2.83 | −0.154 | −2.11 | −0.154 / −0.153 | −0.224 (−4.4) | −0.173 | −0.472 / −0.067 / −0.185 | 41% | 54% | 0.94 |
| short 12:30 ER 0.30 | 1,156 | 3.38 | −0.133 | −1.11 | −0.006 / −0.212 | −0.802 (−8.7)* | −0.181 | −0.481 / −0.025 / −0.305 | 47% | 60% | 0.72 |
| short 12:30 ER 0.45 | 686 | 2.01 | −0.144 | −1.25 | −0.047 / −0.206 | −0.899 (−9.7)* | −0.191 | −0.435 / −0.058 / −0.273 | 47% | 58% | 0.81 |

(17 open months each. Regime gate fails on all 8. *The random window starts at 10:00, so for the 12:30 checks (and
partly 11:00) it includes entries made before the trend formed, which are profitable by construction; the excess
column overstates the gap. Raw t fails without it.)

- **G fails.** The 11:00 long is the only config near zero (+0.02R, positive in TRAIN, flat in VALID) but it rests on a
  single day (without it −0.01R) and is a bet on the tape: +0.25R on SPY-up days, −0.45R on down days, −0.09R on quiet
  days. So it is not a QDAY idea. Shorts mirror it (win only on SPY-down days). By 12:30 the smooth movers have used
  their room: longs −0.18..−0.20R with 57-60% stopped.
- The path-efficiency threshold barely changes the 11:00 sample (the no-retrace rule already implies a high ER).
- Salvage path (not run; a new pre-declared test needed): the 11:00 long only on compass-UP days, which overlaps the
  dayclass gate ideas — same conclusion as reddit_1109 A.

## Files
- `PLAN.md` (pre-declared grid), `g_tests.py` (run from any directory; reads /home/user/MCF data), `g_out.txt`,
  `g_results.csv`.
