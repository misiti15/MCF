# COILAM — ONE morning on/off rule for the coil family (Scout plan, FROZEN 2026-11-10 03:40 ET, before reading coil outcomes by state)

*Educational only — not financial advice. Research only; no live change. Lead lead-20261110-0300-1/-2; Skeptic skeptic-20261110-0301-2.
Pre-declared from the plan logic (GATE1 holding fact), not from the data: I have not looked at coil R by compass state.*

## Rule (the only one)
Skip a CWT12 coil long entry (CWT12-coil-k4-long, CWT12-coil-k6-long) when the 30-min checkpoint state at the last compass
mark strictly before the entry bar close is **DOWN** (SPY >= 0.30% below its open at the latest 30-min checkpoint, from
10:30). Entries before the first usable checkpoint, and on UP / UNCONFIRMED states, are kept. Field: `e_checkpoint` in
research/compassbf/coil_tagged.csv.gz (re-tagged with strict <, Builder 02:30).
Why: a long that relies on a stock coiling under its high fights a tape that is confirmed down and holds its side of the open to
the close 89% / 89% / 97% of the time (GATE1 TRAIN / VALID / live). One look; **family N 2,605 (market-state gates) -> BAR90 3.57.**

## Scoring (2-year lab list, 20,779 coil trades; locked block absent and asserted)
- removed = trades with e_checkpoint == DOWN; kept = the rest. Report n removed and share, per setup (k4 / k6).
- **Ex-market R:** R minus beta x (side x spy_move), beta per setup fitted on TRAIN (<= 2025-09-30) only, applied to all.
- **Same-day random block (pass control):** for each day with k >= 1 removed and >= 1 kept trade of that setup, remove k random
  trades of the same setup that day (200 draws). Excess = mean R of the random-removed minus mean R of the rule-removed
  (> 0 = the rule removes worse trades). Day-clustered t over those days; days where the rule removes every trade of that setup
  are counted and carry no information. Computed on gross, net and ex-market R.
- **Size control:** kept book avg R vs the same trades at uniformly smaller size (a skip rule must beat 'trade less').
- Splits: TRAIN / VALID; SPY day type up / down / quiet (o-c +-0.25%) with days counted per type; w/o best day; best-day share.
- **Retention:** kept share of trades and of each setup's TRAIN top-decile winners (by gross R).

## Pass (lead worth a forward shadow; any live change is the owner's)
Kept-book gross avg R > 0; ex-market random-block excess t >= 3.57, and > 0 in TRAIN and in VALID; excess > 0 on up days and on
down days (where >= 10 days carry information; otherwise reported, not required); w/o best day > 0; best-day share < 50%;
retention >= 80% of trades and >= 90% of top-decile winners. A result below 3.57 but positive in every split is reported as
'shadow-worthy, not a pass' for the Lead to decide.

## Forward-shadow spec (journal-only; starts the session after scoring if the Lead approves)
- Every live CWT12 coil k4/k6 signal in any account is tagged with the live compass (mcf-data-compass compass/<date>.csv)
  checkpoint state at the last mark strictly before its signal bar close (a mark published at T is usable from T+1 min).
- Flag `coilam_skip` = state DOWN. No trading change: the trade is taken as today.
- After >= 20 sessions with >= 1 flagged trade: compare flagged vs kept live R (net and gross from the journal) and vs a
  same-day random block of equal size; report n, days, w/o best day. Confirm only if flagged trades are worse than the random
  block on both net and gross, and the rule-18 forward judgement holds.
- Tooling: one read-only script research/rcompass/coilam_shadow.py (journals + compass branch), no runner change.
