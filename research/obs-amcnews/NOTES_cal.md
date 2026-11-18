# FAMC calendar nightly log (Observer)

## 2026-11-13 night (catch-up; no guild posts 11-12 07:50 .. 11-13 23:10 ET)
- 11-12 built: snapshot by the 08:57 ET pre-open job, 111 names listed, 738 evening items -> 8 AMC flags:
  AMAT ARWR CBRS HTFL KOD NKTR NU QXO (reaction 11-13).
- 11-13 UNBUILDABLE by the frozen rule: mcf-data earnings/2026-11-13.json was committed by 'job 09:53 done 2026-11-13'
  (no pre-open job wrote it). Not built, not patched. Reaction session 11-16 has no FAMC calendar row.
- Health (gap ratio) fell: 6 of 13 flags > 2x normal (11-11: 1/3, 11-12: 3/8). health_base.py base rate on 292 KNOWN AMC
  events (Yahoo, 08-03..10-30, lab names): 74.3% > 2x (median 4.58x); random non-event days 21.3%. A mixture reading of
  6/13 gives precision ~0.47, with a CI covering ~0..1 at n 13. P(>= 7 of 13 below 2x | all true AMC) = see out (~0.03).
- Direct read (headline audit, outcome-free): all 11 flags of 11-11/11-12 carry a genuine earnings release in the
  16:00-19:59 window (e.g. AMAT 'Q4 Adj EPS $4.16', FNV 'Reports Q3 2026 Financial Results', KOD 'Q3 EPS misses').
  So precision is intact; small opening reactions (FNV, ENS, AMAT, KOD, QXO) drive the low ratios.
- Lesson: the open-gap ratio is a weak health instrument (1 in 4 true AMC names opens < 2x). Replace it with the headline
  audit (count of flags whose evening item is a results release) and keep the ratio as context only.
Educational only — not financial advice.

## Snapshot coverage (11-14 ~19:50 ET; for Skeptic's 'unscorable count beside K')
earnings/<D>.json on mcf-data, 10-20..11-13 (fetch --depth=5000 like the builder; a shallow fetch shows only 'EOD report' and
looks like 0 of 19 - my first pass made that mistake): 15 of 19 sessions pass the frozen rule (one commit, pre-open job).
All 4 failures are 'late job' days: the first job started after 09:30 (10-20 09:33, 10-23 10:47, 10-26 10:39, 11-13 09:53),
i.e. no pre-open job ran. Since 10-27: 14 of 15. The owner's start guards (08:40 / 09:05 / 09:35 ET, from 11-16) should cut these.
Second loss source: my own build missing the same night (11-12, during the guild pause) -> unscorable even with a good snapshot.
Expected coverage going forward ~90%: the 40-60 session e-process horizon stretches by ~10%.

## Headline audit = primary health line (11-14 ~21:55 ET; headline_audit.py -> famc_headline_audit.csv)
Outcome-free, never writes the calendar. Strict RESULTS pattern (Q-EPS/Sales lines, 'Reports ... Results', 'Financial Results',
guidance 'Sees Q/FY'). All 13 calendar rows so far (11-10: 2/2, 11-11: 3/3, 11-12: 8/8) carry a results release that evening.
Discrimination check on other single-symbol evening items: non-earnings items match 3/277 (11-11) and 3/340 (11-12), ~1%;
earnings-ish items 76-83% (the pattern is stricter than the builder's EARN filter). Nightly: run after build_famc_cal.py.
Precision only; recall needs a late calendar.

## 2026-11-16 (built 23:41 ET, same night)
Snapshot by the 08:44 ET pre-open job (27 names listed; passes the frozen rule). 299 evening items -> 1 AMC flag: INFQ
(reaction 11-17). Headline audit 1/1 ('Infleqtion Reports Q3 2026 Financial Results'). FAMC session 11-17 scorable.

## 2026-11-17 (built 21:41 ET, same night)
Snapshot by the 08:45 ET pre-open job (32 names; passes). 267 evening items -> 1 AMC flag: NVDA (reaction 11-18). Headline audit 1/1
('NVIDIA Reports Financial Results for Third Quarter Fiscal 2027'). Gap-ratio context: 11-16's INFQ opened < 2x normal (ratio is weak; audit 1/1).
