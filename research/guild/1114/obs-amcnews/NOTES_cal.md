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
