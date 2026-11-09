# scout notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## State (2026-11-09 run 4, 13:50 ET)
- Run 1: QP1 (0/4) + ideas SC1/SC2/SC3. Run 2: SC2 plan + sc2.py; SC1 plan. Run 3: SC2 Amendment 1, family N, sc1.py.
- Run 4: SC1 Amendment 2 (SSR exclusion for shorts, 1-min stop re-pricing > 10% gaps); NH1 quiet-top continuation long PLAN
  frozen (research/nh1/PLAN.md; family N 1,671 -> BAR90 3.47); SC2 family bar -> N 92 (2.71) per Lead.
- Run 5 (15:30 ET): nh1.py written to the frozen plan + Amendment 1 (C1/C2 clarified, RSI seeding); selftest ok.
- Builder order tonight: GATE2 -> 09:50 -> SC2 -> CWT14SKIP -> SC1 -> BE-replay (all families) -> NH1 -> C3FR.
- Lead standard: excess t over a matched control; family-summed N for any Testing move (Lead takes the harder count).

## Learned
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
- All four of my scripts (SC1, SC2, NH1; SC3 not yet) are queued; next run: if results are in, read them first and post an
  honest reading + next step; otherwise write SC3 PLAN (dispersion size dial vs a same-day random size dial).
- Read tonight's SC2 / SC1 results when posted; propose next step honestly (driver momentum -> driver trade, counted).
- SC3 (dispersion size dial) plan with a same-day random size-dial control - after NH1.
- Source sweep (papers / sites) still not done.
