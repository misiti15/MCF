# Completeness critic (cycle 3)

Educational only — not financial advice. Written 2026-11-28 ~02:30 ET. I read every file in exploration/ and checked config and research files on the default branch (read-only). **New configurations scored: 0** (the count stays at about 9,656). Rule changes in the 10-23..11-27 window are as listed at the top of DECISIONS.md.

## Gaps found

1. **The Monday combo was never replayed on the Monday roster.** LATCH-OPEN's numbers (11-25 −40 → −8R; bench days ≤ −20R 33 → 8; CHECK −3.03 → −2.05 R/day) all come from the old 4-setup book with L3 in it. D1 Q5 says outright that the 3-setup roster was "not re-replayed". So MONDAY_PLAN's "Both: a day below −20R becomes rare (about 3 a year)" and "+1 to +6 R/wk" are not checked.
2. **LATCH-OPEN's forward test has no control.** Its pass bar (PROPOSALS #1) asks for "skipped lots average ≤ 0R", and in a book losing −0.156R per lot that is close to automatic. The shorts reviewer flagged this same flaw for ARENA-LATCH-F. The session's own review rule (D7.4a: show every red-day lever next to an exposure-matched size cut) is not applied to its top proposal.
3. **L3-OUT's pass bar is mostly mechanical.** Day sd ≤ 10R is already 9.1 in-sample once L3's lots are removed. There is no random-removal control of the same size, even though rwout says removing any short helps by about the same amount.
4. **ARENA-LATCH-F already failed its own control in-sample.** Against a random cut of the same size on the same account-days, the latch sat at the 0th / 14th / 41st percentile (shorts_autopsy reviewer, row L). D5 does not say this. The scoring script is also still unwritten (D5).
5. **The B8 shadow logs a different rule from the one that passed.** The bench used a 60-day shrunk beta (research/squeeze_1125/REPORT.md, caveats). The shadow uses beta 1.0 for every symbol (D3). PRIOR_RESEARCH also records that B8 already **fails the constant-cut test on T2**, and with LATCH-OPEN on, B8 added nothing on 11-25 (squeeze REPORT). D3 does not state either point.
6. **The L3 tail guard is in the wrong account.** L3 moves to On Deck (−391R on 11-25, no per-setup stop), but D5 latches Testing F. Fixed in D2 Q4.
7. **One assumption has no source.** D1 says the owner missed the Friday step because "you wanted to ask questions first". Nothing in the files records that.
8. **An obvious angle was missed: free paired evidence already running.** RW3-WB4 (Live Lab), RW5-WB4 (Testing D), L3-WB4 (Testing A) and the RQa-1230 copies have traded the same signals as their Primary parents since 11-17 / 11-23. The WB4 copies skip entries while SPY is up more than 0.20% from 09:50; the RQa copies make no entries after 12:30. No track paired parent against copy, although dev_tactics shows paired reads need about 3x fewer sessions.
9. **The opportunity side was never studied.** All seven tracks looked at losses or filters. None measured capture rate against the day's real movers (the charter's Move Hunt), and that is the only route the files name to a positive edge.
10. **Small fixes made in DECISIONS.md:**
    - The 11-17 giveback/SPY exits applied to the WB4 copies only (rw_target, ledger 2026-11-16-wb-*).
    - The "all accounts, deduped" label in shorts_autopsy is consistent. The exact-name RW3/RW5 run only in Primary (config/account_testing.yaml: "runs in Primary only from 2026-10-21").

## Next research steps (ranked)

1. **Replay the Monday combo on the bench:** RW3 + RW5 + NM-ETF, with and without LATCH-OPEN (and the −3R variant), against an exposure-matched size cut, on CHECK and T2. This puts real numbers on D1 Q5 and on the −20R-day claim (configs: about 4).
2. **Pair each parent with its WB4 / RQa copy** on residual R, using same-day day-clustered t and LIVE-L-consistent costs, from 11-17 / 11-23. It costs nothing and it tests an SPY-up skip and a 12:30 cut-off on live fills.
3. **Add controls before Monday's forward tests start.** LATCH-OPEN: skipped lots compared with a same-day random skip of equal size. L3-OUT: Primary compared with a random 37% lot cut. ARENA-LATCH-F: write the scorer first, and pre-state the in-sample 0th-percentile result so the read is tail-only.
4. **B8 parity.** Ship the shrunk-beta JSON before the shadow starts, or bench-score the beta-1.0 version. Write down what could still promote B8, given the T2 constant-cut fail.
5. **Capture-rate study.** For the day's top movers both ways (top 1% by move after 10:00), record what share any setup entered, when, and the R after entry. Pre-register it on CHECK and T2.

## Q&A on the three provisional taps

**LATCH-OPEN (tapped *friday*)**
- *"I said Friday. Why Monday?"* → Monday already starts epoch 3 (AV50), and waiting a week carries about a 20% chance of a −20R day (D1). The premise that the owner wanted to ask questions first is unsourced (gap 7).
- *"With L3 gone, what does it still save?"* → **Not quantified.** D1 Q5 answers qualitatively (RW baskets on 11-10 and 11-11 of 35-39 lots, about −24R each). See step 1.
- *"Why not just trade 20% smaller?"* → On CHECK it equals a size cut (E = 1.00, D1 Q4). Its edge is timing: on 11-25 it gives −8R, where a 20% cut would give about −32R (arithmetic on −40.1R).
- *"How will I know it worked?"* → PROPOSALS #1, but that bar has no control (gap 2).

**L3-OUT (tapped *out*)**
- *"I already said out?"* → Only the date is open: Monday (overrides probation) or 12-04 (D2).
- *"What do I lose?"* → The windfalls of 11-12 (+31R) and 11-16 (+16.4R). Total R barely moves (−30.1 → −27.0R) and day sd falls 15.8 → 9.1 (roster_options_out.txt).
- *"One-big-day check?"* → Primary −0.209R per lot without its best day. All accounts +0.086R per lot, 81% of it from 10-20 (D2 Q1).
- *"Is it safe in On Deck?"* → No per-setup stop there, and it would be the 8th L3 copy (D2 Q4). No guard covers On Deck (gap 6).

**B8-SHADOW (tapped *shadow*)**
- *"Does it change trades?"* → No. It is a journal tag in Primary, On Deck and Testing A (D3).
- *"Is it the rule that passed?"* → **No:** beta 1.0, not the shrunk 60-day beta (gap 5). Not answered in D3.
- *"What would make it live?"* → D3: beat an exposure-matched cut and a size-matched random block on CHECK and T2, plus 20 sessions of tags. It already fails T2's constant cut (PRIOR_RESEARCH). Not stated in D3.
- *"When?"* → After 20 Primary sessions, about 12-29 if it starts Monday (D3, PROPOSALS #5).

Educational only — not financial advice.
