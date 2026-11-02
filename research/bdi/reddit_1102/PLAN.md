# reddit_1102 pre-declared test plan (written before any scoring)

*Educational only — not financial advice.*

Common rules (docs/RESEARCH_RULES.md): costs in (1c + 1 bp per side; entry side x time-of-day multiplier, **3.8x for a
09:35 entry** (conservative: the TOD_COST band before 10:30 at its widest), exit side free on a target limit, +2c on stop
fills); locked block 2024-11-01..2025-02-28 never read (opening frame built without it, 1-minute rows dropped at load
before any computation, daily table rows dropped at load); old holdouts 2026-04..06 and >= 2026-09-16 dropped before
scoring (as saturday1031); earnings blackout (+-4 trading days, `GD._blackout`) removed; one trade per symbol-day;
day-clustered t; regime split `gates.session_regimes` (up / down must both be > 0); WF = share of months > 0 (>= 54%);
split TRAIN <= 2025-08-31 / VALID after; avg R without the best day + best-day share reported.
**N = 20 configurations for the batch -> full bar sqrt(2 ln 20) = 2.45, BAR90 = 2.20.** No post-hoc configs. The locked
block is scored only if a config clears every open-history gate.

## A — opening-candle range expansion, trade its direction (r/Daytrading 1xle3nm, 2026-11-01; posted on US100 CFD)
Data: research/bdi/timeofday/data/open (5-minute lab rows 09:35..10:30 from the 1-minute SIP cache).
- First candle = the 09:30-09:35 bar (tod 935 row): open = close / (1 + fromOpen/100), range = high - low.
- "Unusually large range vs its preceding ATR" -> rr = range / median(first-candle range over the symbol's prior 20
  sessions in the frame, >= 10 needed; point in time, today excluded).
- Signal rr >= k; side = candle direction (long: close > open; short: close < open).
- Entry 09:35 close. Stop = opposite extreme of the candle -/+ 1c. Exit 10:30 close (frame ends 10:30; the post says
  10:35), unless a later 5-minute low (long) / high (short) reaches the stop. R = |entry - stop|; skip R < 0.05% of price.
- Grid: universe {stocks adv20 >= $95M (ETFs kept, as the lab), QQQ alone (the poster's instrument)} x side {long, short}
  x k {1.5, 2.0, 3.0} = **12 configs**.
- Random control (same minute): every eligible symbol-day of the same universe, same side, entered at the 09:35 close
  with the stop one first-candle range away, same exit. Excess = trade R minus the same-date baseline mean.

## B — 1-minute VWAP bounce in the 15-minute trend, top-volume mega caps, 09:45-11:30 (r/Trading 1xjucpo, 2026-10-30)
Variant of reddit-1029-rdt-volconfirm-bounce (failed: 5-min, all names, 10:00-15:00); new here: 1-minute bars, the
day's 6 highest-volume mega caps only, the morning window and a 15-minute trend filter.
Data: data/cache_hist/1Min (locked rows dropped at load).
- Candidate list per day: the 30 non-ETF names (mcf.longhold.signals.etf_set) with the highest prior-day adv20; of
  those, the 6 with the highest 09:30-09:44 dollar volume today (known at 09:45).
- VWAP: session VWAP of 1-minute typical price from 09:30.
- 15-min trend (long): the last completed 15-minute bar close > EMA20 of 15-minute closes (prior sessions included) and
  > VWAP; short = mirror.
- Bounce bar (long), bar close 09:45..11:29: low <= VWAP x 1.0005, close > VWAP, close > open, prior bar close > VWAP,
  volume >= V x mean volume of the 10 prior 1-minute bars. Short = mirror.
- Entry bar close; stop = bar low - 1c (long) / high + 1c (short); skip R < 0.05% of price.
- Exits: t2r (target 2R limit, else out at 11:30 close) or h1130 (stop only, out at 11:30 close). Stop checked on later
  1-minute lows / highs (stop first if a bar touches both).
- Grid: side {long, short} x V {1.0, 1.5} x exit {t2r, h1130} = **8 configs**.
- Random control: for each trade, 5 random entry minutes in 09:45..11:29 on the same symbol-day, same side, same $ stop
  distance, same exit; excess = trade R minus the mean of its 5 controls.
