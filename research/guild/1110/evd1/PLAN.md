# EVD1 — does the earnings surprise agree with the gap, and does that predict the reaction-session move? (Scout plan, FROZEN 2026-11-10 07:40 ET)

*Educational only — not financial advice. DESCRIPTIVE, gross first, 0 configs scored as rules (Lead lead-20261110-0700-1/-3;
Observer D1; Skeptic's calendar audit research/skeptic-20261109/earnings_cal_audit.md written in below). Outcomes are read only
after Builder posts the gap-alignment table. Live trading blacks out earnings names +-4 days: any setup from this would need an
owner exception, stated up front.*

## What is new vs the family
er-react / er-eps-surprise entered at the first open after the report and held 1-20 DAYS (0 candidates; 'beat + price up >= 4%'
+0.09% t 2.05 daily; beat-but-sold-off / miss-but-rallied negative in 10/12 rows). SC1 used a gap+volume PROXY with no surprise
(0 of 12). EVD1 asks the INTRADAY question with the REAL calendar: after 20 minutes of price discovery (09:50), does surprise-gap
agreement predict the rest of the reaction session, beyond what any same-day gapper does?

## Family try-count
er-react / er-ah / er-eps / er-react-prev(-trp) / er-react-runup(-tr) 498 + sat1010 PEAD 60 + SC1 lineage 12 + gap-and-go
(rdt-r04 128, cwt-a8 80, sat1031 4) 212 + cwt-a7 bad-news gap-down 64 + mh-1029 sympathy 8 + cwt-c6 event AVWAP 4 = **N 858 ->
full 3.67, BAR90 3.31** (+ this study's looks below).

## Events (point-in-time; Skeptic traps 1-8)
- earnings_yf.parquet (research-data), open block only (locked-block rows are in a separate file, never loaded; asserted).
- Reaction session: BMO -> the report date; AMC -> the next session; **dmh dropped**; weekend dates -> next session (counted);
  same-symbol events < 45 days apart deduped (first kept); symbols in the lab 1-min cache with adv20 >= $60M.
- Surprise sign: +1 if surprise_pct > +1%, -1 if < -1%, 'inline' bucket if |surprise| <= 1%, 'unknown' if NaN; raw % never used.

## Measurement (reaction session; 1-min SIP cache; locked block dropped at read and asserted)
- gap = 09:30 open / prior close - 1; fo950 = 09:49 close / open - 1.
- Entry at the 09:50 minute's open; outcomes to the 11:29 close (H1130) and the 15:55 close (H1555), in ATR14 units, GROSS;
  ex-market = minus beta60 x SPY's move over the same window.
- **Direction tested:** the gap's sign. Buckets: AGREE (sign surprise = sign gap), DISAGREE, INLINE, UNKNOWN; and |gap| < 2% / 2-5%
  / > 5%; and 'held' (sign fo950 = sign gap) vs 'faded by 09:50'.
- **Controls:** (a) DAY-DEMEANED vs all same-day event names (same direction rule); (b) vs same-minute random NON-event gappers
  (same day, |gap| bucket matched, direction = their own gap sign; 1 random per event, seeded) - the 'any gapper continues' baseline.
- Splits: TRAIN (<= 2025-09-30) / VALID; BMO vs AMC separately; SPY up / down / quiet; day-clustered t; per-day sign counts;
  best-day share.

## Looks (counted): 2 — AGREE-minus-DISAGREE and AGREE-minus-control(b), each at H1130 and H1555 (reported, one family)
Reading: a lead needs AGREE > DISAGREE and AGREE > random gappers in TRAIN and VALID, BMO and AMC, gross and ex-market. Then and
only then a <= 4-config plan at BAR90 3.31 (forward shadow per XA-EPROC: HARM monitor from day 1; confirmation needs 40-60 sessions).
