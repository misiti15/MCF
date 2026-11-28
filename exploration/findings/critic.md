# Completeness critic (cycle 3)

Educational only — not financial advice. 2026-11-28 ~02:30 ET. All of exploration/ read; default-branch config/research checked read-only. **Configs scored: 0** (count stays about 9,656). Rule changes in the window: top of DECISIONS.md.

## Gaps found

1. **The Monday combo was never replayed on the Monday roster.** LATCH-OPEN's figures (11-25 −40 → −8R; bench ≤ −20R days 33 → 8) come from the 4-setup book with L3; D1 Q5 admits the 3-setup roster was "not re-replayed". So MONDAY_PLAN's "about 3 days below −20R a year" and "+1 to +6 R/wk" are unchecked.
2. **LATCH-OPEN's forward test has no control.** Its bar (PROPOSALS #1) "skipped lots average ≤ 0R" is near-automatic in a −0.156R/lot book. The session's own rule D7.4a (exposure-matched cut beside every red-day lever) is not applied to its top proposal.
3. **L3-OUT's pass bar is mostly mechanical.** Day sd ≤ 10R is already 9.1 in-sample once L3's lots are removed. No same-size random-removal control, though rwout says any short's removal helps equally.
4. **ARENA-LATCH-F already failed its own control in-sample.** Against a random cut of the same size on the same account-days, the latch sat at the 0th / 14th / 41st percentile (shorts_autopsy reviewer, row L). D5 omits this, and its scorer is unwritten.
5. **The B8 shadow logs a different rule from the one that passed.** The bench used a 60-day shrunk beta (research/squeeze_1125/REPORT.md, caveats). The shadow uses beta 1.0 for every symbol (D3). B8 also already **fails the constant-cut test on T2** (PRIOR_RESEARCH) and added nothing on 11-25 once LATCH-OPEN was on (squeeze REPORT). D3 states neither.
6. **The L3 tail guard is in the wrong account.** L3 moves to On Deck (−391R on 11-25, no per-setup stop), but D5 latches Testing F. Fixed in D2 Q4.
7. **One assumption has no source.** D1 says the owner missed the Friday step because "you wanted to ask questions first". No file records it.
8. **An obvious angle was missed: free paired evidence already running.** RW3-WB4 (Live Lab), RW5-WB4 (Testing D), L3-WB4 (Testing A) and the RQa-1230 copies have traded the same signals as their Primary parents since 11-17 / 11-23. (WB4: skip while SPY > +0.20% from 09:50; RQa: no entries after 12:30). No track paired parent vs copy, though paired reads need about 3x fewer sessions (dev_tactics).
9. **The opportunity side was never studied.** All seven tracks studied losses or filters; none measured capture rate on the day's real movers (charter Move Hunt), the route to a positive edge.
10. **Fixed in DECISIONS.md:** 11-17 giveback/SPY exits were WB4-copies only (rw_target); the shorts_autopsy "all accounts" label is consistent (exact-name RW3/RW5 run in Primary only, config/account_testing.yaml).

## Next research steps (ranked)

1. **Replay the Monday combo on the bench:** RW3 + RW5 + NM-ETF, with and without LATCH-OPEN (and the −3R variant), against an exposure-matched size cut, on CHECK and T2. Answers D1 Q5 and the −20R-day claim (about 4 configs).
2. **Pair each parent with its WB4 / RQa copy** on residual R, using same-day day-clustered t and LIVE-L-consistent costs, from 11-17 / 11-23. Free; tests an SPY-up skip and a 12:30 cut-off on live fills.
3. **Add controls before Monday's forward tests start.** LATCH-OPEN: skipped lots compared with a same-day random skip of equal size. L3-OUT: Primary compared with a random 37% lot cut. ARENA-LATCH-F: write the scorer first, and pre-state the in-sample 0th-percentile result so the read is tail-only.
4. **B8 parity.** Ship the shrunk-beta JSON before the shadow starts, or bench-score the beta-1.0 version. State what could still promote it.
5. **Capture-rate study.** For the day's top movers both ways (top 1% by move after 10:00), record what share any setup entered, when, and the R after entry. Pre-register it on CHECK and T2.

## Q&A on the three provisional taps

**LATCH-OPEN (tapped *friday*)**
- *"I said Friday. Why Monday?"* → Monday already starts epoch 3 (AV50); a week's wait carries about a 20% chance of a −20R day (D1).
- *"With L3 gone, what does it still save?"* → **Not quantified**; D1 Q5 is qualitative (RW baskets 11-10/11-11, about −24R each). Step 1.
- *"Why not just trade 20% smaller?"* → On CHECK it equals a size cut (E = 1.00, D1 Q4); its edge is timing: 11-25 −8R vs about −32R for a 20% cut.
- *"How will I know it worked?"* → PROPOSALS #1, but that bar has no control (gap 2).

**L3-OUT (tapped *out*)**
- *"I already said out?"* → Only the date is open: Monday (override) or 12-04 (D2).
- *"What do I lose?"* → The windfalls of 11-12 (+31R) and 11-16 (+16.4R). Total R −30.1 → −27.0R; day sd 15.8 → 9.1 (roster_options_out.txt).
- *"One-big-day check?"* → Primary −0.209R per lot without its best day. All accounts +0.086R per lot, 81% of it from 10-20 (D2 Q1).
- *"Is it safe in On Deck?"* → No per-setup stop there, and it would be the 8th L3 copy (D2 Q4). No guard covers On Deck (gap 6).

**B8-SHADOW (tapped *shadow*)**
- *"Does it change trades?"* → No; journal tag in Primary, On Deck, Testing A (D3).
- *"Is it the rule that passed?"* → **No:** beta 1.0, not the shrunk 60-day beta (gap 5). Not answered in D3.
- *"What would make it live?"* → D3: beat exposure-matched and random-block cuts on CHECK and T2 plus 20 sessions of tags; it already fails T2's constant cut (PRIOR_RESEARCH), unstated in D3.
- *"When?"* → 20 Primary sessions, about 12-29 (D3).

Educational only — not financial advice.
