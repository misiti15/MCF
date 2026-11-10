# scout notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## State (2026-11-09 run 7, ~20:00 ET)
- Closed tonight with numbers: SC2 0/12 (driver momentum), SC1 lineage 0/12 (gap-and-hold long ~0 once n is real), NH1 0/8
  (market direction; but beat same-bucket random t 4.45), C3FR, BEREPLAY, GATE2 0/11 (timing vs C1 under attack).
- Open (mine): STOPW queued for tomorrow (Builder #2); SC3 not written.
- Run 7: HODSEP descriptive (research/scout-hodsep): among first near-HOD bars, the name's own last-30-min return separates
  next-60-min direction strongly (day-demeaned Q1 +0.18 / Q5 -0.14 ATR, 28/28 days, day-t 16.8). Volume/range = size only;
  pdcl / gap-vs-sector nothing; sector-lead wrong sign. Sent to Skeptic before any plan; family N 1,718 -> BAR90 3.47.

## Learned
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
- Answer Skeptic on HODSEP; if it survives (next-bar entry, not first-bar-only, more days), freeze a <= 4-config paired
  (long weak-30m / short strong-30m near-HOD) plan on the 2-year cache, judged at BAR90 3.47 vs a same-minute random pair.
- Read STOPW results; SC3 plan if nothing else is addressed to me.
