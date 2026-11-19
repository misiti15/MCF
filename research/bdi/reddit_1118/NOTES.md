Educational only — not financial advice.

# reddit_1118: Reddit setup scout (2026-11-18)

**Result: 0 posts from the last 1-3 days could be read, 0 ideas added, 0 tested, 0 passed. No DECISION.**
Nothing in config, setups, exits, research/ledger.jsonl, research/backlog.jsonl or docs/live changed. The locked block
(2024-11-01..2025-02-28) was not read. Read-only toward Reddit: GETs only, no account, no posting, voting or messaging;
no user names recorded. 0 configurations scored, so no t-bar applies.

**Rule changes in the window:** none apply (no data was scored).

**Note:** research/consultant_p3/RESULTS.md "Stop doing" lists the Reddit scout itself (0 passes from ~480
ideas/variants). This run was requested anyway with a narrow focus; today's result adds to that record.

## Focus (crunch week)
LONG setups for up/quiet days; missed big-move categories (opening drive 09:35-09:45, non-earnings gap-and-go,
sector-lagger follow, afternoon trend); ways to avoid short squeezes on gap-down fades. Excluded: the consultant
stop-doing list, mechanisms already in research/backlog.jsonl (1,090 lines), and the exact U4/U5/U6 specs that failed
today (research/usage/SUMMARY_1118.md).

## Sources tried
- Reddit RSS (`https://www.reddit.com/r/<sub>/top/.rss?t=day`, UA `mcf-research/0.1`, 5-20 s spacing) for r/Daytrading,
  r/Trading, r/algotrading, r/RealDayTrading, r/quant, r/StockMarket, r/swingtrading: every feed returned 404 (an Atom
  "Not Found" body) or 429; a retry 20 s apart got the same. old.reddit.com RSS redirects to a login page; `.json`
  returned 403. This is a change from reddit_1110, when the same feeds worked.
- Third-party Reddit mirror pages were not fetched (the session's permission layer declined it; not worked around).
- WebSearch (standard), 8 site:reddit.com / reddit queries aimed at the focus areas (gap-and-go first 15 min, opening
  drive, sector-laggard RS, afternoon trend, gap-down fade squeeze, recent r/Daytrading / r/algotrading). **No result
  was dated 2026-11-15..11-18**; hits were 2021-2025 threads on mirrors, blogs, or spam pages.

## Older threads seen (not added; outside the 1-3 day window and already covered by mechanism)
- r/RealDayTrading 2021 "gap and go or gap and gag" (gap to a new high: wait for a compression or pullback in the
  first 30 minutes): covered by the opening-drive / ORB30 / gap-and-go entries in the backlog and U6 M2.
- r/RealDayTrading 2021 "a simple strategy" (go long RS names when SPY breaks its downtrend; exit when RS fades):
  covered by the RS/RW and MH4 group-laggard entries and U4 RS longs.
- r/Daytrading 2024 thread (day trend set by 10:30 on non-news days): no rule; dayclass / U5 cover it.
- Blog rule (not Reddit) for late-day breakouts after 14:00 above prior-day and current-day highs: covered by the
  prior-day-high and PM arena entries (e.g. bdi-rdt-r17-pd-retest, swarm1017 PM entries).

## Next step (if the scout continues)
The RSS route is now closed from this environment. Options for the owner: drop the scout as the consultant advised
(C3-LEAN-style), or allow a Reddit-readable route; otherwise the scout yields nothing.
