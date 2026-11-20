Educational only — not financial advice

# Beginner experiment 2026-11-20: 10 intraday setups and separate session rules

I wrote this as a fresh beginner. I did not open MCF research, the backlog or the existing setup
modules. I read README.md (to learn the data format and the setup list) and mcf/strategies/base.py
(the Signal and DayContext interface). Because README lists setup names, a few of the ideas below share a
name or source with existing MCF setups (ORB, noise band, intraday momentum, gap-and-go, gap fade, VWAP
reversion). That overlap is expected: these are the first things a beginner learns. The rules below were
written from public sources only, so any later comparison with the existing versions is a real test.

## Global conventions (MCF rules plus beginner defaults)
- Bars: 1-minute RTH. Signal on the close of a bar, fill at the next bar's open (or a stop order where stated).
  Costs are included by the engine.
- Entries 09:50 ET or later. Every position is flat by 15:55 ET (`exit_by=15:55`).
- Base universe U0: US common stocks and ETFs, price >= $5, 20-day average dollar volume >= $20M.
- Shorts: easy-to-borrow names only. Never short inverse, leveraged-inverse or volatility funds (SQQQ,
  SH, SPXU, UVXY, VXX, SVXY, etc.).
- 1R = |entry - stop|. "ATR" = daily ATR(14) as of the prior close (`ctx.atr`). "RVOL20" = 09:30-09:49
  volume / average for the same window over 14 days; `rank_rvol20` = rank in the day's universe.
- "Gap" = today's open / prev_close - 1. "VWAP" = session VWAP from 09:30.
- OR15 = 09:30-09:44 high/low. R20 = 09:30-09:49 high/low.

## (A) Setups

### B01 ORB-15 on stocks in play (long and short)
- Universe: U0 + price >= $10, RVOL20 >= 2.0 and rank_rvol20 <= 20, ATR >= $0.50.
- Window: entries 09:50-11:30.
- Trigger: long on a buy-stop at OR15 high + $0.01 if the 09:30-09:44 candle closed above its open; short on a
  sell-stop at OR15 low - $0.01 if the candle closed below its open (doji candle = no trade). Order valid until 11:30.
- Stop: 0.10 x ATR from entry (the paper's stop), and never beyond the far side of OR15.
- Exit: target 2R; otherwise hold to 15:55. Breakeven stop at +1R.
- Max hold: until 15:55. One trade per symbol.
- Why: limiting ORB to high-relative-volume "stocks in play" kept a profit after costs in a 2016-2023 test
  (Zarattini, Barbon & Aziz 2024, "A Profitable Day Trading Strategy for the U.S. Equity Market"; replicated on QuantConnect).

### B02 VWAP first pullback in a trend (long and short)
- Universe: U0 + price >= $10, rank_rvol20 <= 50.
- Setup: long if price at 09:50 is >= +2.0% from prev_close and every 1-minute close from 09:35-09:49 is above
  VWAP. Short is the mirror case: <= -2.0%, closes below VWAP.
- Window: entries 09:50-13:00.
- Trigger: the first pullback after 09:50 whose bar low comes within 0.10% of VWAP (long) while that bar
  closes back above VWAP. Enter at the next bar's open. Short is the mirror case.
- Stop: pullback bar low - $0.02 (long) / high + $0.02 (short), with distance at least 0.15 x ATR.
- Exit: target 2R, or the day's high/low so far if that is closer (min 1.5R, otherwise skip).
  Time stop: exit after 60 min if +0.5R was never reached.
- Max hold: 120 min.
- Why: the first test of VWAP in a trending stock is the textbook continuation entry, with VWAP acting as the
  institutional benchmark (Aziz, "How to Day Trade for a Living"; practitioner source, weak evidence).

### B03 Gap-and-go continuation (long only)
- Universe: U0 + price $5-$200, gap >= +3.0%, RVOL20 >= 3.0.
- Window: entries 09:50-11:00.
- Trigger: buy-stop at R20 high + $0.01, only if the last close before the trigger is above VWAP. The order
  is valid 09:50-11:00.
- Stop: max(R20 low, VWAP at signal) - $0.02, with distance kept within 0.4%-3% of price (otherwise skip).
- Exit: target 2R; trail 1R behind the best price after +1R.
- Max hold: until 12:00 (`exit_by=12:00`).
- Why: big gaps on heavy volume carry news-driven demand into the morning (momentum-trader classic, e.g. Aziz;
  Zarattini et al. find relative volume is the key filter). Practitioner evidence.

### B04 Quiet gap fade toward prior close (long and short)
- Universe: U0 + 20-day ADV >= $50M, price >= $15, |gap| between 1.5% and 6%, and NO unusual volume
  (rank_rvol20 > 100 and RVOL20 < 1.5), so the gap is likely not news.
- Window: entries 09:50-12:00.
- Trigger (gap up -> short): a 1-minute close below R20 low with price below VWAP. Gap down -> long: a close
  above R20 high with price above VWAP. ETB only for shorts.
- Stop: the other side of R20 + $0.02, capped at 0.35 x ATR from entry.
- Exit: target = prev_close (the gap fill); if that is < 1.2R away, skip the trade. Otherwise exit at 15:55.
- Max hold: until 15:55.
- Why: overnight gains tend to reverse during the day (Lou, Polk & Skouras "A Tug of War"; Miwa 2019 via
  Quantpedia; Vainio 2011-2024 US thesis). The no-news filter avoids information gaps, which do not reverse.

### B05 Market intraday momentum, last 25 minutes (long and short)
- Universe: SPY, QQQ, IWM, DIA (index ETFs only; never inverse ETFs).
- Window: one entry at 15:30 (signal on the 15:29 bar close).
- Trigger: r1 = price at 10:00 / prev_close - 1. Long at 15:30 if r1 >= +0.25% and the 15:29 close > VWAP;
  short if r1 <= -0.25% and the 15:29 close < VWAP.
- Stop: 0.15 x ATR from entry.
- Exit: 15:55 (time exit), no target.
- Max hold: 25 min.
- Why: the first half-hour return predicts the last half-hour return in SPY and ten other liquid ETFs (Gao, Han, Li
  & Zhou 2018, JFE). The effect is stronger on high-volatility and high-volume days.

### B06 Noise-area breakout on index ETFs (long and short)
- Universe: SPY, QQQ.
- Bounds: upper = open x (1 + m_t), lower = open x (1 - m_t). Here m_t is the 14-day average |close/open - 1| at
  the same minute (`ctx.avg_move[t]`). If the gap is positive, the upper bound is anchored at max(open, prev_close);
  if negative, the lower bound is anchored at min(open, prev_close).
- Window: check only at 10:00, 10:30, ..., 15:00 (half-hour marks).
- Trigger: at a check time, long if close > max(upper, VWAP); short if close < min(lower, VWAP). One position at a time.
- Stop: trailing. Long: exit on a check-time close < max(upper, VWAP). Short: mirror. Hard stop at 0.25 x ATR.
- Exit: 15:55 if the trailing stop has not been hit.
- Max hold: until 15:55.
- Why: moves beyond the usual intraday "noise" in SPY show supply/demand imbalance that tends to continue
  (Zarattini, Aziz & Barbon 2024, "Beat the Market"; 4th place, Quantpedia Awards 2025).

### B07 End-of-day reversal of intraday extremes (long and short)
- Universe: U0 + price >= $10, ADV >= $30M, stocks only (no ETFs).
- Window: one entry at 15:25 (signal on the 15:24 bar close).
- Trigger: r = close at 15:24 / prev_close - 1, ranked across the universe. Long the 10 lowest r with r <= -3% that
  are not at the day's low in the last 5 minutes (close > day low + 0.1 x ATR). Short the 10 highest r with
  r >= +3% that are not at the day's high (ETB only).
- Stop: 0.20 x ATR from entry.
- Exit: 15:55.
- Max hold: 30 min.
- Why: a stock's return early in the day negatively predicts its return in the last half hour (Soebhag, Baltussen
  & Da, "End-of-Day Reversal", 2nd place Quantpedia Awards 2025). The paper reports the effect gross of costs, so
  a cost check is essential.

### B08 Stretched-from-VWAP snap-back (long and short)
- Universe: U0 + price >= $20, ADV >= $100M (large caps), rank_rvol20 > 30 (no headline names).
- Window: entries 10:00-14:30.
- Setup: |close - VWAP| >= 0.8 x ATR and 5-minute RSI(14) > 80 (short) or < 20 (long).
- Trigger: a reversal bar. Short when a 1-minute close is below the prior bar's low; long when a close is above the
  prior bar's high.
- Stop: the day's extreme since the setup + 0.05 x ATR.
- Exit: target = VWAP at entry time (min 1.0R, otherwise skip). Time stop: 45 min.
- Max hold: 45 min.
- Why: large intraday moves in liquid stocks show significant price reversal 10-60 minutes later (arXiv
  cond-mat/0406696). Short-term reversal is concentrated in intraday returns (Miwa 2019).

### B09 Midday range -> high/low-of-day break (long and short)
- Universe: U0 + price >= $10, rank_rvol20 <= 30.
- Setup (long): the day's return is >= +3% at 11:30, and over a window of >= 30 consecutive minutes inside
  11:30-14:30 the range (high - low) stays <= 0.35 x ATR with every close above VWAP. Short is the mirror case:
  <= -3%, closes below VWAP.
- Trigger: buy-stop at high of day + $0.01 (short: sell-stop at low of day - $0.01), valid until 15:00.
- Stop: consolidation low - $0.02 (short: its high + $0.02).
- Exit: target 2R; otherwise 15:55.
- Max hold: until 15:55.
- Why: strong stocks that rest above VWAP at midday and then break the day's high tend to trend into the close.
  Practitioner (Aziz; Minervini-style "tight range"), plus the afternoon momentum in Gao et al. Weak evidence.

### B10 Narrow-range day -> first-30-minute breakout (long and short)
- Universe: U0 + price >= $10, ADV >= $30M.
- Setup: yesterday's range (prev_high - prev_low) <= 0.6 x ATR (compression; the proxy for Crabel's NR7/inside day,
  computable from DayContext).
- Window: entries 10:00-12:30.
- Trigger: buy-stop at the 09:30-09:59 high + $0.01; sell-stop at its low - $0.01 (OCO, first fill wins;
  ETB for shorts). Skip if the 30-minute range is > 0.8 x ATR.
- Stop: midpoint of the 09:30-09:59 range.
- Exit: target 2R; otherwise 15:55.
- Max hold: until 15:55.
- Why: volatility contraction tends to be followed by expansion, and opening-range breakouts after narrow-range days
  are a classic short-term pattern (Crabel, "Day Trading with Short Term Price Patterns and Opening Range Breakout",
  1990). Practitioner evidence; not verified this session.

Side mix: B03 is long only. The other nine trade both sides.

## (B) Session rules (apply to every setup; test each one separately, on and off)

- S1 Daily loss stop: once an account's realized P&L for the day is <= -3R, no new entries for the rest of the day.
  Open trades keep their stops.
- S2 Trade caps: at most 6 new entries per account per day and at most 2 per symbol per day. After a stop-out, no
  re-entry in the same symbol by the same setup that day.
- S3 Time window: no entries before 09:50 or after 15:30. B05/B07 enter only in their fixed 15:25-15:30 slots.
  Everything is flat by 15:55.
- S4 Exposure: at most 4 open positions per account, and at most 3 in the same direction. 1R = 0.5% of account
  equity, the same for every trade.
- S5 Streak control: after 3 losing trades in a row, pause new entries for 30 minutes. Once the day's realized P&L
  is >= +4R, halve the risk on new trades (1R = 0.25%).
- S6 Event blackout: on scheduled macro days, no new entries 08:30-10:15 on CPI/NFP days, 09:55-10:10 on ISM
  days, and 13:45-14:30 on FOMC days. Setups that fire inside a blackout are skipped, not delayed.
- S7 Trade with the tape (momentum setups B01, B02, B03, B06, B09, B10 only): longs only while SPY's last close is
  above SPY VWAP, shorts only while it is below. The reversal setups (B04, B07, B08) and B05 are exempt.
- S8 Sanity filter: skip any trade whose stop distance is < 0.25% or > 3% of price, or whose last 5 one-minute
  bars average < $150k traded (a proxy for the spread).

## Test plan sketch
Score each setup with costs in, over the full history, then on a locked holdout (scored once). Report trades, win
rate, avg R, PF, avg R without the best day and that day's share of total R. Test each session rule against the
baseline with no session rules, and report its effect per setup (how many improve, how many get worse), not only
the total. Report the number of configurations tried.

## Sources
- Zarattini, Barbon, Aziz (2024), A Profitable Day Trading Strategy for the U.S. Equity Market: https://ideas.repec.org/p/chf/rpseri/rp2498.html ; QuantConnect replication https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/
- Zarattini, Aziz, Barbon (2024), Beat the Market (SPY noise area): https://ideas.repec.org/p/chf/rpseri/rp2497.html
- Gao, Han, Li, Zhou (2018), Market Intraday Momentum, JFE 129: https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414 ; https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/
- Soebhag, Baltussen, Da, End-of-Day Reversal: https://www3.nd.edu/~zda/EOD.pdf
- Miwa, Short-Term Return Reversals and Intraday Transactions: https://quantpedia.com/short-term-return-reversals-and-intraday-transactions/
- Lou, Polk, Skouras, A Tug of War: https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
- Vainio, overnight-intraday reversal thesis (Turku): https://www.utupub.fi/bitstreams/88057d2a-1ee8-4c05-9592-c535a21b502c/download
- Short-term reaction after extreme price changes (arXiv): https://arxiv.org/pdf/cond-mat/0406696
- Practitioner: Aziz, How to Day Trade for a Living; Crabel (1990), Day Trading with Short Term Price Patterns and Opening Range Breakout (not fetched this session).
