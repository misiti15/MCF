Educational only — not financial advice.

# reddit_1106: Reddit setup scout (2026-11-06)

**Result: 2 ideas kept, 1 tested, 0 pass.** 8 configurations were declared in PLAN.md before scoring. Full bar for
N = 8 is 2.04, Testing bar (BAR90) 1.84; the best t was −0.25, so **the locked block (2024-11-01..2025-02-28) was not
scored and there is no DECISION.** No config, setup, exit, ledger or docs/live file was changed. Read-only toward
Reddit (RSS GETs only, no account, no posting, voting or messaging; no user names recorded).

**Rule changes in the window:** none apply. This is a two-year backtest on the research cost model (gates.py: 1c +
1 bp per side, time-of-day entry multiplier, +2c stops), not a live record; the live changes in research/ledger.jsonl
(GX1 10-27, Primary size 10-28, −2R stop 10-29, CF 10-30, UNI1 11-04, ROLL1 11-05) do not touch it; nothing new 11-06.
Data: the 2-year cache rebuilt 11-04 (research/bdi/1104/DATA.md); 485 symbols, 342 sessions (same frame as reddit_1105).

## Sources
- Reddit RSS (`/r/<sub>/top/.rss?t=day`, UA `mcf-research/0.1`, 10-25 s spacing, retries for HTTP 429). Got top-day
  for all nine: r/Daytrading, r/Trading, r/algotrading, r/ai_trading, r/RealDayTrading, r/quant, r/StockMarket,
  r/swingtrading, r/daytrade (active intraday sub, as 11-05). Also read `/new/` for r/Daytrading and r/daytrade, and
  top-week for r/Daytrading, r/RealDayTrading, r/algotrading (top-day was thin). Comment feeds read: 1xpp3mz, 1xozdah,
  1xp2b5y, 1xpl1wq, 1xpfcka, 1xpgdee. WebSearch not needed.
- **215 unique posts; 155 dated 2026-11-05..11-06 (141 on 11-06)** — Daytrading 47, Trading 25, ai_trading 25,
  swingtrading 20, StockMarket 19, algotrading 8, daytrade 6, quant 4, RealDayTrading 1. Older top-week posts already
  covered by reddit_1103..1105 (1xou3un, 1xo3sdz, 1xnsgqq, 1xomh9r etc.) not re-scored.

## Filter (what was dropped)
Day after the crash (jobs print, rebound then fade): most posts were psychology, tilt, prop firms, brokers, P/L,
AI-bot promotion, gold / futures / crypto / options, crash news. Dropped with a reason:
- r/Daytrading 1xozdah (relative strength / weakness): a filter, not an entry; covered by ex30-XS2-leader-redtape-long,
  reddit-1030-rs-spydip-orh-long, reddit-1029-rdt-volconfirm-bounce. A comment's RSP-vs-SPY market-type read is a
  breadth filter (no rule given).
- r/Daytrading 1xpfcka (+ comments: closed 1-hour candle as the direction filter for 5-minute breakouts): generic
  MTF alignment; covered by the trend-filter variants (trend-pullback, cwt-b-b7, bdi-rdt-r09).
- r/Daytrading 1xp2b5y (tests of anchored VWAP / EMA / value-area references "repeat"): no rule; covered by
  cwt-c-c6-event-avwap, bdi-vid-volume-profile, bdi-art-volume-profile.
- r/Trading 1xpgdee (QQQ 45-minute strategy, 41 trades, options): options, few trades, rule not posted.
- r/StockMarket 1xp9g3p (rebound after the crash fades by midday, rallies into the close): one-day narrative; the
  next-day-after-crash bet was dropped on 11-05 (too few events).
- r/Trading 1xp6kwa (float runners), r/Daytrading 1xpirqs (MNQ / GC entries), 1xprki1, 1xpokh5 (forex sessions),
  r/ai_trading 1xpkhv5 (SEC late-filer short, quarterly), r/algotrading 1xppwoi (regime question), r/daytrade
  watchlists / images: not intraday US-equity rules or no rule.

## Ideas (research/backlog.jsonl, tags reddit + scout)
| id | source | status |
|---|---|---|
| reddit-1106-lowvol-pullbackday-15m-ema20-volbounce-long | [r/Daytrading 1xpp3mz](https://www.reddit.com/r/Daytrading/comments/1xpp3mz/dal_day_trade_recap_a_020r_trade_that_never/) | parked (8 configs) |
| reddit-1106-dataday-wait-or-settle | [r/StockMarket 1xpl1wq](https://www.reddit.com/r/StockMarket/comments/1xpl1wq/jobs_print_beat_hard_and_nasdaq_futures_bounced/) (post + comment) | idea (needs a release calendar; ~15 NFP days = low power) |

## A — low-volume pullback day, then a volume-confirmed 15-minute EMA20 bounce, LONG (`a_tests.py`, `a_out.txt`, `a_results.csv`)
Poster's DAL long on a weak SPY day: high-volume up day, pullback day on ~70% of that volume above the daily EMA20;
intraday a green 15-minute candle off the rising 15-minute EMA20 on ~2x the prior red candle's volume; structural stop.
`ctx` = the daily context on/off; `v` = volume ratio; target m x R. Random control = 3 same-symbol-day long entries
(10:05..14:45), same $ R and target.

| config | n | /session | avg R | t | train / valid | excess vs random (t) | w/o best day | SPY up / down / quiet | WF | stopped | med R % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ctx on, v 1.5, 1.5R | 266 | 0.78 | −0.260 | −3.50 | −0.338 / −0.174 | −0.293 (−3.9) | −0.283 | −0.175 / −0.379 / −0.278 | 24% | 55% | 0.35 |
| ctx on, v 1.5, 2R | 266 | 0.78 | −0.257 | −3.16 | −0.301 / −0.208 | −0.315 (−3.7) | −0.282 | −0.177 / −0.397 / −0.250 | 12% | 58% | 0.35 |
| ctx on, v 2.0, 1.5R | 107 | 0.31 | −0.104 | −0.89 | −0.180 / −0.024 | −0.082 (−0.7) | −0.134 | −0.023 / −0.174 / −0.182 | 35% | 48% | 0.39 |
| ctx on, v 2.0, 2R | 107 | 0.31 | −0.033 | −0.25 | −0.044 / −0.022 | −0.125 (−1.0) | −0.071 | +0.072 / −0.164 / −0.099 | 41% | 49% | 0.39 |
| ctx off, v 1.5, 1.5R | 8,709 | 25.46 | −0.135 | −6.34 | −0.118 / −0.149 | −0.111 (−6.5) | −0.140 | +0.006 / −0.273 / −0.199 | 12% | 52% | 0.37 |
| ctx off, v 1.5, 2R | 8,709 | 25.46 | −0.151 | −6.47 | −0.123 / −0.175 | −0.139 (−7.9) | −0.156 | +0.022 / −0.316 / −0.235 | 6% | 55% | 0.37 |
| ctx off, v 2.0, 1.5R | 3,588 | 10.49 | −0.126 | −4.49 | −0.112 / −0.138 | −0.142 (−5.4) | −0.134 | −0.009 / −0.211 / −0.208 | 18% | 50% | 0.39 |
| ctx off, v 2.0, 2R | 3,588 | 10.49 | −0.136 | −4.58 | −0.109 / −0.159 | −0.134 (−5.2) | −0.143 | +0.028 / −0.269 / −0.240 | 18% | 53% | 0.39 |

(SPY day type: SPY open-to-close > +0.25% up, < −0.25% down, else quiet. Best-day share is not defined: every total R
is negative. Universe-median regime gate fails on all 8. WF = share of 17 open months > 0.)

- **Fails.** Every config is negative in TRAIN and VALID and below same-day random entries.
- **Not a quiet-day or a down-day idea:** at best break-even on SPY-up days, −0.20..−0.24R on quiet days and
  −0.16..−0.40R on down days — the poster's "weak SPY" backdrop is where it loses most.
- **Why:** the structural stop under one 15-minute candle is tight (median 0.35-0.39% of price, stopped 48-58%), so
  the per-side costs take a large share of R; the volume surge off the EMA does not add timing value vs random.
- The daily low-volume-pullback context is the only part that looks less bad (v 2.0: ctx on −0.03..−0.10R vs off
  −0.13..−0.14R), on 107 trades (t −0.25..−0.89) — noise at this n. Salvage path, if anyone picks it up: the daily
  context alone as a filter on an existing long family with a wider stop (not tested; would be a new pre-declared run).

## Files
- `PLAN.md` (pre-declared grid), `a_tests.py` (run from any directory; reads /home/user/MCF data), `a_out.txt`,
  `a_results.csv`.
