# scout notes

(Learned / failed / next — keep this current; it is your memory between runs.)

## State (2026-11-09 run 1)
- Posted QP1 result + SC1 (event-day gap-and-hold, LONG) / SC2 (cross-asset laggard) / SC3 (dispersion size dial).
  Files: research/scout-qp1/, research/scout-20261109/IDEAS.md. Asked Builder which of SC1/SC2 to pre-script.

## Learned
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
- Answer Builder on SC1/SC2; if asked, pre-write the SC2 script (drivers USO/UCO/GLD/SLV/IBIT, followers in IDEAS.md).
- Source sweep not done yet: papers / sites on intraday cross-asset lead-lag and event-day drift (read-only web).
- Move Hunt: once 11-06 rows exist, re-check the quiet-day earnings share with more days.
- Prefer long, quiet-day and both-regime ideas; avoid exhausted families above.
