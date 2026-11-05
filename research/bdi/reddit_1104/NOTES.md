Educational only — not financial advice.

# reddit_1104: Reddit setup scout (2026-11-04)

**Result: 1 idea kept, tested, 0 pass.** 6 configurations were declared in PLAN.md before scoring. BAR90 for N = 6 is
1.70 (full bar 1.89); the best t was −5.09, so **the locked block (2024-11-01..2025-02-28) was not scored and there is
no DECISION.** No config, setup, exit, ledger or docs/live file was changed. Read-only toward Reddit (RSS GETs only, no
account, no posting, voting or messaging; no user names recorded).

**Rule changes in the window:** none apply. These are two-year backtests on the research cost model (gates.py: 1c +
1 bp per side, time-of-day entry multiplier, +2c stops), not live records; the live sizing / stop / filter changes in
research/ledger.jsonl (GX1 10-27, Primary size 10-28, −2R stop 10-29, CF 10-30, UNI1 11-04) do not touch them.
Data: the 2-year cache rebuilt tonight (research/bdi/1104/DATA.md); the daily table now has more symbol-days in the
same open months than the one reddit_1103 used (86,000 vs 74,239 top-250 symbol-days, 344 sessions both), so counts
are not comparable one-to-one with 11-03.

## Sources
- Reddit RSS (`/r/<sub>/top/.rss?t=day|week`, `/new/.rss`, UA `mcf-research/0.1`, 8-15 s spacing). Got: r/Daytrading
  (top day, new), r/Trading (top day), r/algotrading (top day / week, new), r/quant (top day / week), r/StockMarket
  (top day), r/daytrade (top day; active intraday sub, mostly link / image posts), and on the retry r/ai_trading,
  r/RealDayTrading and r/swingtrading (top week; top day was HTTP 429). Comment feeds read: 1xnpo24, 1xnjsf0,
  1xnt98d, 1xncjp2 (1xngvtd stayed 429). WebSearch not needed (RSS answered).
- **210 unique posts; 141 dated 2026-11-02..11-04 (95 on 11-04)** — Daytrading 41, Trading 25, algotrading 20,
  StockMarket 14, ai_trading 13, swingtrading 12, quant 10, RealDayTrading 3, daytrade 3. 11-02 / 11-03 posts were in
  reddit_1103's window and are not re-scored (1xn5ohs, 1xmes0o, 1xljdal named there).

## Filter (what was dropped)
Post-midterm day: most posts were psychology, prop firms, brokers, P/L, forex / gold / NQ / crypto, AI-platform
promotion, election / earnings news. Dropped with a reason:
- r/Trading 1xnjsf0 (event day: sit out the first 30 min, cut size; a comment: trade a break of the first-hour range
  only after one full 15-minute bar holds inside it): covered by wi-ib-narrow-extension and the time-window grids;
  the "15-min close back inside the pre-open range" variant needs premarket bars (not in the lab frames).
- r/swingtrading 1xnt98d (what makes a consolidation clean: tightening range, higher lows, volume dry-up, resistance
  tested): no rule in the post; covered by wi-intraday-vcp, cwt-b-b4-coil-flag-breakout, cwt-c-c2-tight-base.
- r/Daytrading 1xnm4xn (3 Bar Play, +29.4R then −29.4R): the poster's own test shows no edge vs random; covered by
  reddit-1029-3barplay (parked).
- r/Daytrading 1xncjp2 (no indicators; comments: PDH / PDL / premarket levels, a fixed clock): vague or options.
- r/algotrading 1xlyqdy (65 pre-registered tests, 0 passes): forex / futures; matches RESEARCH_RULES already.
- r/RealDayTrading 1xn5p8m, 1xnsgqq (relative strength): covered by bdi-reddit-rdt-rrs-fullday.
- r/Trading 1xnpb1s (AMD post-earnings vs SOXX / NVDA), r/Daytrading 1xo33p4 (volume profile levels, a question),
  1xnq4hv (screenshot), 1xngvtd (EURUSD EMA scalping), r/algotrading 1xngx81 (XAUUSD), r/daytrade 1xnmjah (screenshot).
- r/algotrading 1xn814m: public log of this project's own paper accounts; not a source.

## Idea (research/backlog.jsonl, tags reddit + scout)
| id | source | status |
|---|---|---|
| reddit-1104-session-room-pullback-long | [r/Daytrading 1xnpo24](https://www.reddit.com/r/Daytrading/comments/1xnpo24/your_target_looks_good_does_the_session_have_room/) (= r/Trading 1xo1lmv) | parked (6 configs) |

## A — morning-rally pullback long with a "session room" target check (`a_session_room.py`, `a_out.txt`, `a_results.csv`)
5-minute bars from the 1-minute SIP cache; locked block and old holdouts dropped at load; top-250 non-ETF names by
prior-day adv20, blackout removed (485 symbols, 86,000 symbol-days, 344 sessions). Long only; rally >= 0.5 ATR14
from the open, pullback >= 1/3 of it and still above the open, bar closes above the prior bar's high (10:00..13:30);
next-bar-open entry, stop 1c below the pullback low, R >= 0.10% of price, target m x R, out 15:55. Room filter keeps a
trade only if target <= LOD so far + k x ATR14. Random control = 3 same-symbol-day entries, same $ stop and m x R.

| config | n | /session | avg R | t | train / valid | excess vs random (t) | w/o best day | SPY up / down / quiet | WF | stopped | target hit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| room none, 1.5R | 17,133 | 49.8 | −0.118 | −5.77 | −0.114 / −0.121 | −0.060 (−3.51) | −0.125 | +0.063 / −0.288 / −0.213 | 6% | 56% | 35% |
| room none, 2R | 17,133 | 49.8 | −0.122 | −5.09 | −0.114 / −0.128 | −0.063 (−3.31) | −0.131 | +0.106 / −0.341 / −0.238 | 6% | 60% | 27% |
| room k1.0, 1.5R | 10,994 | 32.0 | −0.141 | −6.30 | −0.141 / −0.142 | −0.035 (−1.92) | −0.149 | +0.039 / −0.299 / −0.245 | 6% | 58% | 37% |
| room k1.0, 2R | 9,196 | 26.7 | −0.160 | −6.04 | −0.159 / −0.160 | −0.029 (−1.42) | −0.169 | +0.076 / −0.381 / −0.287 | 6% | 64% | 29% |
| room k1.25, 1.5R | 14,324 | 41.6 | −0.134 | −6.27 | −0.133 / −0.134 | −0.051 (−2.91) | −0.141 | +0.052 / −0.297 / −0.242 | 6% | 57% | 36% |
| room k1.25, 2R | 13,104 | 38.1 | −0.139 | −5.48 | −0.136 / −0.142 | −0.042 (−2.17) | −0.149 | +0.089 / −0.340 / −0.273 | 12% | 62% | 28% |

(SPY day type: SPY open-to-close > +0.25% up, < −0.25% down, else quiet; n up / down / quiet 3,842-7,142 /
2,377-4,594 / 2,977-5,397. Best-day share is not defined: every total R is negative. Universe-median regime gate:
up +0.06..+0.12, down −0.30..−0.40 — fails everywhere. Median stop 0.39-0.50% of price.)

Room-filter diagnostic (trades the filter keeps vs drops, from the `none` set, paired by day):

| target | k | kept n / avg R | dropped n / avg R | diff (t) |
|---|---|---|---|---|
| 1.5R | 1.0 | 10,994 / −0.141 | 6,139 / −0.077 | −0.045 (−1.71) |
| 1.5R | 1.25 | 14,324 / −0.134 | 2,809 / −0.040 | −0.062 (−1.86) |
| 2R | 1.0 | 9,196 / −0.160 | 7,937 / −0.079 | −0.050 (−1.88) |
| 2R | 1.25 | 13,104 / −0.139 | 4,029 / −0.067 | −0.051 (−1.61) |

- **Fails.** Every config loses in TRAIN and VALID, in down and in quiet SPY days; only SPY-up days are positive
  (+0.04..+0.11R) — the same up-day-only pattern as reddit_1103 A. It also loses to random entries on the same
  symbol-day (excess −0.03..−0.06R), so the pullback-reclaim trigger has no timing value.
- **The room check is backwards on this proxy:** the trades whose target sits *beyond* LOD + k x ATR14 (the ones the
  poster would skip) lose less than the ones inside it. A stock that has already made a large range keeps moving
  (momentum / trend day) more often than it mean-reverts to its ATR. The poster's own range model (similar historical
  sessions) is unpublished, so this tests the ADR / ATR version the comment thread describes, not their tool.
- QDAY focus: quiet SPY days are the second-worst bucket (−0.21..−0.29R), so this is not a range-day long.
- Not re-tested with a day-direction gate (would be a new, post-hoc config).

## Files
- `PLAN.md` (pre-declared grid), `a_session_room.py` (run from any directory; reads /home/user/MCF data), `a_out.txt`,
  `a_results.csv`.
