# Owner questionnaire: weekend swarm 2026-10-17

*Educational only — not financial advice.* This page holds every decision the swarm needs from you. ★ marks the
recommended answer. Evidence: `research/swarm1017/SUMMARY.md`, `final/READINESS.md`, `final/PROPOSED_CONFIG.md`.
Every config change is applied after the close and recorded in the ledger.

## A. Funding

**Q1. Real funds on Tuesday 2026-10-20?**
- ★ A) No. Stay on paper. Nothing has a demonstrated edge after costs, in history or live.
- B) A capped "plumbing pilot" with real money to measure real fills. This is expected to lose.
- C) Fund as originally planned.

**Q2. Only if Q1 = B:**
- (a) Pilot capital: ____ $. Hard daily dollar stop: ____ $.
- (b) Account: ★ a new, separate Alpaca live account / the existing account.
- (c) Setups: ★ the watch-list only (RW3-FD, RW5-FD, MF2-FD) / the whole Primary account.
- (d) Arm the watchdog (`MCF_WATCHDOG_MODE=act`): ★ yes / no.

## B. Setups

**Q3. Add the 5 tagged near-misses to Testing 1 as forward observation? These are paper only and are not
candidates (PROPOSED_CONFIG §2).**
- ★ A) Yes, all 5, tagged `near-miss`. Judge them on ≥ 20 sessions and ≥ 60 trades.
- B) Only #1 (AM gap-down capitulation) and #4 (CWT09 g10 VWAP-loss).
- C) None.

**Q4. Move these 11 Testing 1 setups to the Graveyard after 10-20? Moving is not deleting. All are negative on 2y
history and on the live week, and their reworks failed:** RW6-ns2-FD, NS2-FD, heat_fade_long-FD, ST1-FD,
exhaustion_short-FD, L3-fromopen-FD, L3-lowdist-FD, MF1-FD, RW2-FD, heat_fade_short-FD, ST2-FD.
- ★ A) Yes, all 11.
- B) Yes, except: ____.
- C) No, keep all of them in Testing 1.

**Q5. Former-primary setups NS2, heat_fade_long and heat_fade_short in Testing 1 (rule 20, 10-session clock):**
- ★ A) Prompt me at session 10 with the scorecard, and move them to the Graveyard if they are still below the bar.
- B) Move them now (this waives the 10-session clock).
- C) Keep them indefinitely.

**Q6. Primary demotions to Testing 1: MF1, MF3 and MF5 are negative on 2y history after an exhaustive rework.**
- ★ A) Demote all three after the 10-19 session. Decide MF4 in its scheduled 10-19 review.
- B) Demote MF1 only.
- C) Keep them all in Primary.

**Q7. What does the Graveyard (Testing 2 after 10-20) do with its setups, including the current CWT setups?**
- ★ A) Keep paper-trading them so retirement prompts have data, with lower caps.
- B) Signals journaled only (shadow), no orders.
- C) Disable them; they come back only on my word.

## C. Code and research (housekeeping ships after tests pass; studies are pre-declared)

**Q8. Build the missing live features: spy_fo, qqq_fo and breadth columns in the lab frame; a symbols allow-list;
t05s05 and no-target/trailing geometries. About 10 near-misses cannot be forward-tested without them.**
- ★ A) Yes.
- B) Only spy_fo and qqq_fo.
- C) No.

**Q9. Spend locked-block looks on near-misses? A pass would still not clear their try-count bars.**
- ★ A) No. Keep the locked block clean for a version that clears the history bars.
- B) Spend look 1 on up to 3 of them: RST1, ETF-late-dip-adx, AM gap-down capitulation.

**Q10. Run a pre-declared 2-year study of a decision-time "skip trades against the index" filter, with up/down
regime splits? It was the biggest lever in the live week, but it is regime-dependent.**
- ★ A) Yes.
- B) No.

**Q11. Exit studies on 1-minute paths: breakeven at +0.5R for the MF setups, a 1R trail for the CWT12/14 longs, and
a 0.5R stop by regime?**
- ★ A) Yes, all three.
- B) Only the MF breakeven.
- C) None.

**Q12. Add gate tooling: day-equal-weighted t, best-day-removed t, top-3-day share and a per-session cap.**
- ★ A) Yes, as housekeeping. It makes the gates stricter only.
- B) No.

**Q13. Commit and test the new `mcf/research/arena/` package, the "training arena" you asked for?**
- ★ A) Yes, with tests.
- B) Keep it as research scratch.

## D. Goals and direction

**Q14. The "160 quality setups" target. The weekend found 0 quality setups in 1.05M configurations.**
- ★ A) Replace the count target with "only setups that pass the gates". Keep intraday as a forward test and put the
  main research into longer holding periods (research/longhold).
- B) Count tagged Testing-grade near-misses toward the target. They are not quality, and the label would say so.
- C) Keep 160 as the target for the intraday search.

**Q15. Items to settle before any real-funded account (yes / no / later for each):**
- (a) ★ Yes: book a CPA review covering short-term income, wash sales, 475(f), the reserve, IRA limits and PTP
  credits.
- (b) ★ Yes: add a backup data feed.
- (c) ★ Yes: the daily loss limit includes open P/L, and is tightened from 20R to ____R.
- (d) ★ Yes: review the residual-lot rule (0.25).
- (e) ★ Yes: finalize the 30% profit skim.
- (f) ★ Yes: use a separate live account and keys.
- (g) ★ Yes: zero unexplained journal-to-broker P/L gap.
