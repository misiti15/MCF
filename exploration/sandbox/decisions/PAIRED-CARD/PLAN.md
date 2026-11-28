# PAIRED-CARD scoreboard - plan (DRAFT; research-only, no runtime change)
Educational only - not financial advice. Source: exploration/findings/dev_tactics.md Proposal 1 + reviewer fix.

- What: after each close, replay the actual live trades of all 10 accounts under each pending card and score the PAIRED
  per-day difference in R after costs (LR8; spread term for tight stops).
- Cards: LATCH-OPEN (if not live; if live, score the skipped lots from what-if rows instead), RW3/RW5 1.25x target,
  L3 first-lot-only under LATCH-OPEN, SPREADFLOOR F6/F8.
- Skip-rule cards: compare skipped vs taken trades on the SAME day and SAME side, on NET R (reviewer 3c).
- Window: sessions 11-30..12-11 (10 sessions), reported once on 12-11 evening; no decisions from peeks.
- Pass per card (pre-registered): paired day-clustered t >= 2 in the bench direction; sign holds without the best day;
  >= 60% of affected setups improve, losers listed with size; effect within 2 SE of the bench estimate. t <= 0 -> drop.
- Inputs: journals (git show origin/mcf-data*:journal.db, read-only) + stored 1-minute bar packs (bars-YYYY-MM release).
- Output: research/paired_cards/<date>.csv + one line per card in the nightly brief (once the owner says go).
