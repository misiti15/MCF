**Day 6.5: a weekend look under the hood**

No trading today, so here are some basic facts about where the system stands, what runs behind the scenes, and where it is headed.

**End of week (10/26 to 10/30) in one look:**

- **Primary:** 125 trades, 3 of 5 days green, -5.2R / -$135 after costs for the week. The 3 green days added +$367; one short-heavy day (10/29) took most of it back.
- **Top-10 setups** (the leaderboard's best 10 across all accounts): **+12.4R** for the week.
- Two strong setups were promoted to Primary on Friday, and two weak ones were moved to the Graveyard.

**Top 10s vs Primary:**

- The top-10 group finished the week at +12.4R while Primary finished at -5.2R (picture 1).
- That gap is the point of the ladder: setups earn their way up. 4 of today's top 5 on the leaderboard now run in Primary, and the weekly review keeps moving Primary toward that group, 1 to 3 moves a week at most.

**Position size was adjusted earlier this week:**

- **Before (to 10/27):** each position was capped at about $1,900. The typical trade risked only about $15, roughly 0.02% of the account, even though the risk rule allows up to 0.25% (about $239). It was built that way on purpose: dozens of setups could fire at once and the account had to have room for all of them.
- **Now (from 10/28):** Primary runs fewer, better setups, so each position is about $4,000 and the typical trade risks about $30. Still well under the 0.25% limit, and every daily loss limit stayed the same.

**Automatic start: glitched twice, now watched:**

- The system starts itself every morning from a schedule. Twice that schedule did not fire.
- **10/26:** nobody caught it, and the accounts started at 10:39, missing the first hour. That day I added a **watchdog** that checks every hour that all 5 accounts are running and restarts any that are not.
- **10/30:** the 8:35 start never fired again. The watchdog caught it and started everything at 8:50, before the open. No session lost, all 5 accounts traded the full day.

**Rules and filters you don't see (about 25):**

- **Before a signal:** liquid stocks only, minimum price, no stocks within 4 trading days of earnings (about 1,490 names were excluded on 10/29), no partnerships that trigger tax withholding, each setup's own time window, decisions on clean 5-minute bars.
- **Before an order:** borrow check for shorts, halt check, spread under 0.30% and under 25% of the stop, fresh and sane quotes, one position per stock (no opposite sides, sister setups can't double up), short-sale rule gate, size capped by liquidity, max 30 positions per setup and 77 per account.
- **During the day:** a -2R daily stop per setup, a -20R daily stop for the account, an outage plan (pause new trades after 5 min of bad data, protect stops at 15, exit at 30), everything flat by 3:55 PM, and the watchdog.
- **Result so far:** of 17,425 signals, 9,294 (53%) were stopped before reaching the market (picture 2).

**Basic facts:**

- About 18,000 lines of system code, 8,500 lines of tests (463 automated tests) and roughly 196,000 lines of research scripts, built in about 4 weeks.
- 134 approved rule changes, each logged and re-checked.
- 110 hand-built setups plus 93 machine-generated ones live on paper.
- Backtests use 2 years of 1-minute prices for 3,000+ US stocks and ETFs, with all costs in, plus a 4-month block kept locked as a final exam.
- About 27,600 setups and variations have been rejected by backtests and never made it to live testing. 370 ideas in the research list have failed outright. Every try is counted, which raises the bar for the next one.

**5 reasons I'm optimistic:**

1. The top-10 setups made +12.4R this week. The leaderboard is finding setups that work.
2. Primary was green 3 of 5 days this week.
3. The safeguards earn their keep: the twin cap saved 57.2R this week and the Graveyard's loss limit saved 188.6R.
4. The watchdog turned a missed start into a non-event, and every account closed flat every day.
5. The research filter is doing its job: thousands of ideas rejected on paper before risking a dollar.

**What's next:**

- Hit the milestones (3 green days in a row, 8 of the last 10) before any real money, then start small: $5,000, no leverage.
- Keep building Primary from proven setups only.
- Catch more of the day's big moves. Many start in the first 15 minutes, before most setups are allowed to trade.
- More LONG setups.

Paper money. Educational only - not financial advice.
