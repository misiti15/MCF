# scout notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## State (2026-11-10 run 13, ~07:45 ET)
- Day-2 P1 = D1 (Observer): the real historical earnings calendar (research-data earnings_yf.parquet, 7,381 events). I own it.
  EVD1 plan + evd1.py frozen (family N 858 -> BAR90 3.31; Skeptic's 8 calendar traps built in). Waiting for Builder's
  gap-alignment table, then Builder runs evd1.py (cache + pyarrow live there). Alignment passed (AMC next session 5.7x);
  Builder running EVD1. Run 14: source sweep -> research/evd1/SOURCES.md; reading rule registered before output (negative =
  fade; lead only if consistent in every split and below the random-gapper control).
- Closed (mine): QP1, SC2, SC1, NH1, STOPW, HODSEP, RCOMPASS-1, COILAM, SIZEBKT. FLOW1-2Y closed (Builder).
- XA-EPROC: a 20-session shadow is a HARM floor, not confirmation (power 0-19%); confirmation needs 40-60 sessions or an
  EDGE alarm. XA-PBO: print beside avg R; ~0.5 = selection uninformative.

## Learned
- Register how a result's SIGN will be read before the output lands when the outside prior points the other way
  (EVD1: literature favours an intraday fade on earnings days, our test measures continuation).
- Predicted size (rvol, range) at 5-60 min is noise amplitude: brackets get whipsawed MORE on high-size names.
  Don't route size predictors into entries; at most into per-name sizing / stop width (and beat 'trade smaller').
- Any day label ('held', 'flipped', 'quiet') must be known at the entry time; 'no flip all day' peeks past the entry.
  Compare post-event trades with 'not-yet-event at entry', never with 'event never happened'.
- Let another role score a plan I froze when I have not looked: keeps the look honest and the count at one.
- TEMPLATE RULE: every look-back slice goes through a guard (`win(arr, lo, hi)` asserting lo >= 0); numpy wraps
  negative indices to the end of the day = silent look-ahead. HODSEP v1 looked like t 16.8 because of it. Assert the first
  candidate bar >= the longest look-back, and enter at the next bar's open so feature and outcome share no price.
- 'Too strong' is a bug signal: send it to Skeptic before planning (it worked).
- A big-excursion label (max high >= X ATR) rewards volatility features; always check a directional, day-demeaned
  forward return too before calling a feature a selector.
- Alpaca multi-symbol bars: 100 symbols/request, ~1,240 symbols x 33 sessions of 5-min bars ~ 15 min (includes extended
  hours - filter to RTH). Slices like a[b-5:b+1] break at b < 5 (negative index) - guard window starts.
- Before freezing a plan, walk its skip funnel on paper: SC1's own LOD stop + 0.6-ATR cap removed >95% of the very
  trades the rule was built for (names that HOLD their gap are extended above the LOD). Count skips by reason in every script.
- Followers beating same-minute random names is not catch-up: Skeptic's C3 (laggard minus already-moved follower) and the
  driver-hedged R are the right controls for any lead-lag idea.
- Cross-sectional controls over ~500 names x 430 days x 50 bars blow memory if pooled per bar; do signals first, then a
  second streaming pass that trades controls only at the needed (date, bar) keys.
- Write selftest expectations from the rule, not intuition: three times today the code was right and my fixture was wrong
  (z crossing a bar early, Wilder RSI decay ~35, gap-through fill at the open).
- No lab ETP list exists: universe.csv name regex works (202 of 1,225; watch word boundaries - 'Maplebear' hit Bear;
  Sprott 'Physical Gold/Silver Trust' needed adding). Family try-counts: grep backlog configs_tried; ex30 families share one
  count across their 5 setups (e.g. peer family 15), COMBO1's 15 already includes its 9-config first pass.
- Pre-writing for Builder: copy gate2.py conventions (bars(), cost formula, G.summary, dtype, wf months, bar90 row);
  add a --selftest on synthetic bars so logic is checked without the cache. Write test expectations carefully (a partial
  driver move can cross z a bar early - that is correct behaviour).
- Backlog (950 rows) + pod1022 (452 ideas) cover almost every classic family: VWAP, gap, RSI, ORB, SPY gates, PDH/PDL,
  fades, calendar/TOM/OPEX pin, TLT, SSR (rule 201), round numbers, RS vs SPY, lunch/quiet-tape (ex30). Grep both
  (research/backlog.jsonl and research/bdi/pod1022/NOTES.md, research/bdi/ex30/CATALOG.md) before proposing anything.
- Not yet covered (as of 11-09): cross-asset commodity/crypto -> equity lead-lag; intraday event-day (earnings) entries
  (blocked by no historical calendar + live blackout).
- Quiet day at 10:00 is not predictable from tape: QD1 8 + QR1 3 + QP1 4 = 15 configs, best +10..+12 pts vs +15 bar.
  Sector dispersion predicts day SIZE (both splits). Most stable weak flag: SPY crosses open >= 2x by 09:55.
- Quiet-day big movers are ~90% earnings names (2 days, descriptive).
- Data: no bar cache in a fresh container. Alpaca market-data GET works with env keys (urllib, feed=sip); 13 ETFs x 2y
  5-min took ~2 min. No pyarrow -> save CSV. Run scripts with `python3 -I` and use __file__ for output paths.
- Guild worktree: `git fetch origin mcf-guild && git worktree add ../guild origin/mcf-guild`, then
  `git checkout -B mcf-guild origin/mcf-guild` inside it.

## Failed
- QP1: 4 non-SPY quiet predictors, 0 pass (dispersion, VXX, crossings, combo).

## Next
- Read EVD1 output after the alignment table: agree vs disagree vs random gapper, BMO/AMC, TRAIN/VALID, gross + ex-market.
  Lead only if all agree; then a <= 4-config plan (owner exception for the blackout stated up front).
- Source sweep (read-only) for intraday direction evidence around earnings (e.g. opening-auction imbalance, analyst revisions).
