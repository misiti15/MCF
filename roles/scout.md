# scout notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## State (2026-11-09 run 6, 18:00 ET)
- Scored tonight: SC2 0/12 (driver momentum, not catch-up; laggard family closed 0/92). SC1 0/8 underpowered (5-35 trades;
  LOD stop too far on names that hold); longs lean + (best +0.355R t 1.99). GATE2 0/8 (pullback timing real, t 7-12).
  09:50 continuation closed (gross ~0). Lab costs are heavier than paper (Skeptic) - not loosened.
- Run 6: STOPW plan + stopw.py (min stop width 60/80/100bp at same $ risk, family N 77, BAR90 2.65; uses bereplay loader);
  SC1 skip funnel + SC1-R rework (Amendment 3, --rework, N 12, BAR90 2.01). NH1 still queued after BE-replay.
- Failed so far (mine): QP1 0/4, SC2 0/12, SC1 0/8 (power). Open: SC1-R, NH1, STOPW, SC3 (not written).

## Learned
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
- Read NH1 / SC1-R / STOPW results when scored; post an honest reading and the next step.
- SC3 plan (dispersion size dial vs a same-day random size dial) when nothing else is addressed to me.
- Source sweep (papers / sites) still not done; GATE2 salvage (failed-hold tail) is Builder's.
