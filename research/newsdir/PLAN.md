# NEWSDIR — does the polarity of overnight / pre-open company news predict the rest-of-day move? (Scout, FROZEN 2026-11-10 19:20 ET, before any outcome)

*Educational only — not financial advice. Fresh DIRECTION source (Lead lead-20261110-1900-4). Descriptive pilot, one look,
kill line. The guild has only used news PROXIES (gap / volume 'catalyst' setups); never headline text.*

## Family
News-proxy setups: cwt-a-a8 catalyst gap-and-go 80 + cwt-a-a7 bad-news gap-down 64 = 144; text-based news ideas
(bdi-1008-material-news-filter, news-catalyst, orb-news-guard) 0 configs. **N = 144 + 1 -> BAR90 2.84.**

## Pilot sample (reuses the OPTFLOW pilot's stock data)
- Names: the 60 OPTFLOW names (top adv20, single stocks). Sessions 2026-08-04 .. 2026-11-06 (open window).
- News: Alpaca news API (Benzinga), items published between the prior session's 16:00 and **09:45 ET** of day D, where the name is
  the item's ONLY symbol (multi-symbol stories dropped - Observer / Skeptic lesson).
- **Earnings excluded:** items whose headline matches earnings / EPS / quarter / Q1-Q4 / results / revenue / guidance / reports.
- **Polarity (fixed lexicon, case-insensitive, headline only):**
  UP = upgrade | upgraded | outperform | overweight | buy rating | raises price target | price target raised | approval | approved |
  wins | awarded | contract | partnership | record | buyback | repurchase | beats | expands | launches | acquired by | to be acquired
  DOWN = downgrade | downgraded | underperform | underweight | sell rating | cuts price target | price target cut | lowers price
  target | recall | lawsuit | sued | probe | investigation | subpoena | offering | dilution | delay | delays | halts | resigns |
  misses | warns | layoffs | fine | fined | rejects | rejected | short report
  Day score = (#UP - #DOWN) over the name's qualifying items; sign = polarity; 0 / no items = no signal.
- **Outcome:** stock 09:50 one-minute open -> 15:55 close, ATR14 units, gross; ex-market minus beta1 x SPY over the same
  window; day-demeaned across the 60 names.
- **The one look:** mean of polarity x day-demeaned ex-market outcome over signed name-days, day-clustered t; and the same
  split by AGREE (polarity = gap sign) vs DISAGREE, against the gap-sign baseline (gap sign x outcome on the same name-days).
- **Kill line:** polarity-signed mean <= 0, or day-t < 2, or not above the gap-sign baseline on the same name-days -> close.

Amendment 1 (19:30 ET, before any news or outcome was fetched): 'upgrades' and 'downgrades' added to the lexicon (Benzinga's
usual headline form; the word-boundary match missed them in the selftest).

## Pilot result (2026-11-10 ~19:45 ET) — CLOSED by the kill line
3,777 name-days (60 names, 63 sessions); 5,447 single-symbol, non-earnings headlines; 472 name-days with a polarity signal (UP 337
/ DOWN 135). THE LOOK: polarity-signed, day-demeaned ex-market 09:50->15:55 **+0.032 ATR, day-t 1.18 (34/62 days)**; gap-sign baseline
on the same name-days +0.028 (t 1.07) -> fails day-t >= 2 and barely beats the gap. AGREE +0.032 (t 0.88), DISAGREE +0.005 (t 0.13);
DOWN-only +0.065 (t 1.34, n 135). Reading: by 09:50 the headline's direction is already in the gap; a crude lexicon adds ~0.004 ATR.
