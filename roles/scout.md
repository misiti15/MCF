# scout notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## State (2026-11-09 run 2, 09:55 ET)
- Run 1: QP1 (0/4) + ideas SC1/SC2/SC3 (research/scout-20261109/IDEAS.md).
- Run 2: SC2 PLAN frozen + sc2.py (selftest ok, full path compiles, not run: no cache) -> Builder scores tonight after
  GATE2 / Observer 09:50. SC1 PLAN frozen (research/sc1/PLAN.md); sc1.py not written yet.
- Lead standard (09:00): every result judged on EXCESS t over a matched control; bar applies to excess t; N in every post.

## Learned
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
- Write research/sc1/sc1.py to its frozen plan (needs a volume column in bars(): extend gate2 bars() with v=sum volume;
  VWAP from typical price x volume; lab ETP / extended-tier lists - find where the lab marks them before writing).
- After tonight: read SC2 results; if raw fails but C1/hedged excess is positive, propose a hedged rework (count it).
- SC3 needs a same-day random size dial control when it is written.
- Source sweep not done yet: papers / sites on intraday cross-asset lead-lag and event-day drift (read-only web).
- Move Hunt: once 11-06 rows exist, re-check the quiet-day earnings share with more days.
- Prefer long, quiet-day and both-regime ideas; avoid exhausted families above.
