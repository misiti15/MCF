**End of week in the books! (11-16 to 11-20)**

**What this is:**

- An automated day-trading system built and run with Claude (AI), on paper money (no real money yet).
- It tests hundreds of "setups" (a setup = one rule for when to buy or sell a stock and when to get out) in 10 practice accounts. The best graduate to the main account, **Primary**.

**Primary is the scoreboard (image 1):**

- **+4.1R / +$756** this week on 193 trades; 2 of 5 days green.
- Mon did the heavy lifting: **+25.3R / +$1,475**, 82% of trades won.
- **Since Day 1 (10-23): +$313** (Alpaca, our paper broker), but **-87.8R** (corrected 11-22 to one cost basis; first shown as -66.0R); 7 of 21 days green. R and $ differ because some setups carry more $ per R. (11-05/11-06 broker glitch excluded.)
- **Fri, honest version:** Late-Day ETF Dip Buy bought 12 ETFs within minutes; all 12 stopped out: **-12.6R**. Primary still closed **+3.00R**, because our shorts won **20 of 20**.
- **On Deck** (next in line for Primary): -45.4R / -$425.
- **Testing (all A–F): -228R / -$405** on 3,563 trades. Not a verdict: their job is to sniff out what doesn't work, fast.

**This week's story: data rules everything — we just needed more numbers.**

- **Outsider pressure test:** a fresh-eyes review threw 36 hard questions at the system. Takeaways: Primary is the only scoreboard, and every future change gets weighed heavily.
- **Random-entry test:** 165 setups (27,383 live trades) vs random entries on the same stock, same day, same stop. **32 of 165 beat random** (luck alone gives ~8). Our three Primary shorts are in the 32.
- **Where Primary's money comes from:** the gap-down shorts (Gap-Down Recovery Fade, Gap-Down Pop Fade x2: short a stock that gapped down and bounced). **+77.1R** on 550 trades since 10-06 (through 11-20); everything else that's run in Primary: **-207.5R**. *(Corrected 11-22: same cost basis for every trade after the QA cost fix; earlier versions showed +73.4R / -161R and +88.8R / -173R.)*
- ***Honest: that +77.1R leans on two big days.***
- **"What works" protected list:** 32 things that work (spread filter, clean booking, 15:55 close-out, the three shorts...). They change only with evidence. Not a freeze.

**What changes Monday:**

- **2 new testing setups** from a from-scratch textbook experiment: an opening-range breakout (BEG-ORB) and a gap-and-go (BEG-GNG).
- **12:30 copies:** testing copies of the three shorts that stop new trades at 12:30 (most of their money comes before 1 pm). Originals unchanged.
- **Burst brake:** a setup can open at most 30 trades in 10 minutes (one setup fired 100 trades Fri, -99R).
- **Retire rule:** 20+ sessions, 150+ trades, still losing without its best day and red over its last 10 sessions → retired. Never Primary.
- **12 retired** and **12 left the testing arenas** for the Graveyard.

**The Graveyard:**

- Home for weak setups. They keep trading every day, so the data keeps coming, but we're not exploring them right now.
- The weakest are now retired: switched off, never deleted from the record.

**More numbers (images 2-3) — reps matter:**

- **6,719 live trades** this week (6,248 week before); **29,585** since 10-06.
- Setups trading per day in Testing A–F: **~21 → ~64**.
- Testing trades: **939 → 3,563**.
- **182 different setups** traded this week. More reps = fairer, faster verdicts for every setup.

**Our rules in one line each:**

- **R:** results in units of what we risked; +1R = made what we risked.
- **-2R stop per setup:** in Primary, a setup down 2R in a day sits out the rest of it.
- **-20R account stop:** Primary down 20R = no new trades that day.
- **Costs always in:** every number is after trading costs.
- **Paper before real money.**
- **Promotion = a move:** a setup moving up leaves its old account; weak ones move down.
- **The Graveyard never deletes.**
- **Protected list:** what works changes only with evidence.
- **Burst brake:** no runaway pile of trades in a few minutes.

**Rule changes:** half-size testing lots 11-17 ($ not comparable); Primary down to 5 setups 11-19; stop-rounding fix + 9 new testing setups 11-20; Monday's changes from 11-23.

As always, thanks so much for the support and input!

Fun stuff!

Educational only — not financial advice.
