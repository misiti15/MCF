Educational only — not financial advice.

# pdl1030 / why: why the Failed Prior-Day-Low Break Longs fire so often and where their losses come from

Scope: description only. **0 configurations scored.** Every slice below is a descriptive cut of the parent trades, not a
candidate rule, so lineage N is unchanged by this note. Data: open two-year frames, **TRAIN+VALID only**
(2024-10, 2025-03..12, 2026-01..03, 2026-07..09-15; 348 sessions). HOLD months were not loaded. 2026-09 rows after 09-15
were dropped at load. The locked block was never loaded. Kernel `S6.b3_any`, simulator top5_1028 `sim`, costs in, same as swarm15.
Live = paper journals (j1030 copy, run_id 1, R = pnl_adj / $ risk).
Files: `feat.py` (per-trade features -> `tr_*.parquet`, `sd_*.parquet`), `anat.py` -> `anat_out.txt`, `anat2.py` -> `anat2_out.txt`,
`live.py` -> `live_out.txt`. Caveat: the backtest hold-time lines in anat_out.txt are wrong (the `xtod` column is the entry bar),
so use the live hold times instead.

## Parity (passes)
p05 n 53,326, -0.0677 (swarm15 -0.0677). p05-lowvol n 35,238, -0.0950 (-0.0950). p10 n 29,836, -0.0880 (-0.0880).
Diff 0.0000 on all three. p10-lowvol is not in swarm15: n 16,031, -0.0968.
Trades/session: p05 153.2, p05lv 101.3, p10 85.7, p10lv 46.1.
Exposure floor for variants: >= 76.6/session (50% of p05) or >= 25/session.

## 1) Why they fire so often
- The universe is large: 885 liquid names per session (adv20 >= 95M).
- PDL sits close to the open. Median open is only 0.42 ATR above PDL, and 15% of names open below it. Median prior close is
  0.38 ATR above PDL. A normal session range is about 1 ATR, so a PDL touch is routine.
- 42.5% of liquid symbol-days trade 0.05 ATR under PDL by 15:00. 60% of those first breaks happen by 09:45, which is the
  opening auction and the gap.
- 41% of break days close back above PDL within 3 bars inside 09:50-15:00. That gives 17.3% of all liquid symbol-days,
  about 153 signals per session for p05. Signal days average 1.7 reclaim cycles, so price chops around the level.
- Breaks follow the tape. Break rate is 52% on SPY gap-down days vs 35% on gap-up days, and 47% on SPY down sessions vs 38% on up sessions.
  By open position: opened below PDL 99%, 0-0.25 ATR above 68%, 0.5-1 ATR above 17%.
- Conclusion: the signal is close to "a liquid name sat near yesterday's low at the open." It is a market-wide event, not
  something specific to the stock.

## 2) Where the losses come from (p05; p10 in anat_out.txt is the same, slightly worse)
- **No edge before costs.** Gross avg R is about +0.020 for p05 and +0.001 for p10. Round-trip cost averages 0.088R (median 0.063R).
  Regressing on SPY's move during the trade gives a market-neutral net intercept of -0.074R (gross +0.014) for p05, and
  -0.102 (gross -0.013) for p10. Beta is about 0.84-0.98R per 1% SPY move.
- **Market direction during the trade explains nearly all the variance** (not known at entry):
  - SPY falls more than 0.3% during the trade: -0.73R. SPY rises 0.1-0.3%: +0.14R.
  - SPY down sessions: -0.124R (p05) and -0.172 (p10). SPY up sessions: -0.009 and -0.002.
  - Down sessions carry 94% (p05) and 99% (p10) of the total loss.
  - Session-R quintiles by SPY: -0.159 / -0.095 / -0.060 / -0.031 / +0.030.
- **Market context known at entry separates only weakly:**
  - SPY above VWAP -0.054 vs below -0.080. QQQ above VWAP -0.054 vs below -0.081.
  - Breadth > 0.7: -0.037. Breadth 0.3-0.4: -0.089.
  - SPY gap <= -0.5%: -0.023 (p10 -0.009). This is the best market slice. When the whole market gaps down,
    names that fall under PDL tend to snap back.
- **Cost per R is the biggest known-at-entry gradient:**
  - Cost <= 3% of R: -0.019. 3-5%: -0.018. 5-8%: -0.041. 8-12%: -0.061. > 12%: -0.210 (18% of trades).
  - The > 12% bucket is cheap, low-ATR names: median $36, ATR 1.8%. The <= 5% bucket: median $192, ATR 4.0%.
  - Gross R is flat across cost buckets (+0.00..+0.04), so the cheap names lose purely to costs.
- **Time of day:** flat in the backtest (-0.051..-0.084). Live, 09:50-10:00 entries lose most (397 trades, -0.221R), and
  13:00-15:00 entries are slightly positive (171 trades, about +0.06). Live samples are small and this is the session open.
- **Break depth, reclaim strength, gap-under vs drift:**
  - Break depth and how far the reclaim bar closes above PDL show no useful gradient (-0.05..-0.075). Exception: reclaim > 0.2 ATR
    (-0.031, 4/session).
  - Gap-under (opened below PDL) -0.061 vs intraday drift -0.070.
  - Stock gap <= -3%: -0.010, but only 5.6/session.
- **Relative strength:** a U-shape, best at the extremes.
  - Stock > 0.5% above its VWAP: -0.026 (18/session).
  - Stock beats SPY from open by > 0.5%: -0.046.
  - Mild laggards (-0.5..0% vs SPY) are worst: -0.084.
- **MFE / MAE:**
  - 13% of trades never reach +0.1R (-1.10R), and 10% stall at 0.1-0.25R (-1.03R). Together they lose about 13,000R.
  - Winners do not run. The target is 0.5R and the average win is +0.26R on p05 (scale-out to break-even) and +0.45 on p10.
    p05's 0.25R scale-out turns 34% of trades into roughly +0.03R moved-stop exits.
  - On p10, 14% of trades reach 0.25-0.5R MFE and still lose (about -0.95R).
  - Stops are 21% (p05) / 32% (p10) of trades and average -1.14R after slippage.
  - Live: stops average -1.131R, median 35 min to the stop, 46% within 30 min. Winners take a median 20 min.
    The live target sits at only a median 0.46R from the fill, p10 0.20R (the fill price slips past the signal price).
- **Re-break of the day's low (not known at entry):**
  - 51% of p05 trades see the day's low broken again later: -0.269R. When the low holds: +0.142R.
  - 22% of trades see it broken before their exit.
  - The losers are the "failed failure": the level breaks again, usually with the market.

## 3) Five angles to keep the exposure and lift avg R (ranked; descriptive evidence only, none scored)
1. **Cost-aware risk unit: a wider stop at the same $ plus a cost floor, combined.**
   - Cost <= 5% R slice: -0.018R at 54/session. With SPY above VWAP as well: -0.007 at 26/session.
   - The combination with swarm15 S3 is untested. S3 alone gives -0.021, and x3 R cuts cost/R by 3x.
   - It keeps >= 25/session. This is the largest lever that is known at entry.
2. **Market-neutral version: pair the long with a beta-sized SPY/QQQ short.** The loss is beta; slope is ~0.84-0.98R per 1% SPY.
   - The market-neutral gross intercept is only +0.014 for p05, so this removes the variance and the down-day disaster but not the cost drag.
   - It is worth testing only together with angle 1. It keeps 100% of the exposure.
3. **Tape gate on SPY gap down (<= -0.5%) or breadth > 0.7, with a side flip on the losing tape.**
   - SPY gap <= -0.5%: -0.023 (p10 -0.009). With cost <= 5%: +0.005 / +0.016.
   - Down sessions are -0.12..-0.17. A short-side twin on the re-break, keyed to SPY below VWAP with breadth < 0.5
     (34-66/session), would keep the signal count.
4. **Structure exit when the day low re-breaks, or a short flip when price loses PDL again.**
   - Re-break trades: -0.27R (p05) / -0.45R (p10), 51% / 48% of trades. Hold trades: +0.14 / +0.24.
   - Re-breaking PDL is an observable event, so a stop-and-reverse keeps the exposure.
5. **Relative-strength extremes and avoiding the open bar.**
   - Stock > 0.5% above its VWAP: -0.026. RS vs SPY > +0.5%: -0.046.
   - Live 09:50-10:00 entries: -0.22R.
   - These gains are small (0.02-0.04R) and are a secondary layer only.

Not promising: break depth, reclaim distance, gap-under vs drift, and fine time-of-day cuts. All are flat within ~0.02R.

## When each condition is known
- Known at entry, from the signal-bar close or earlier: cost/R, price, ATR, gap, SPY gap, SPY/QQQ fromOpen and VWAP,
  breadth, RS, stock VWAP, break depth, reclaim, first-break time.
- Not known at entry (outcome descriptors only): SPY session direction, SPY move during the trade, MFE/MAE, and the later re-break.

Not done: I did not promote L3-gap-slope-rsi5hi-FD. That is outside this agent's step: no config/ or repo writes were
allowed here, and per CLAUDE.md a setup move needs the assignments regeneration and must happen outside 09:30-16:00 ET.

Educational only — not financial advice.
